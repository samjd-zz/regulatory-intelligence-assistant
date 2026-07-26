#!/usr/bin/env python3
"""
Intelligent data initialization script for first-time setup.

Provides users with options to seed:
1. Canadian laws only
2. Regulations only
3. Both (full dataset)

With optional limit for faster testing/development.
"""
import sys
import os
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from database import SessionLocal, engine
from ingestion.data_pipeline import DataIngestionPipeline
from services.graph_service import GraphService
from services.search_service import SearchService


def check_existing_data(db_session) -> dict:
    """Check if data already exists in the database."""
    stats = {
        'regulations': 0,
        'sections': 0,
        'neo4j_nodes': 0
    }
    
    try:
        # Check PostgreSQL - use regulations and sections tables (not documents)
        # The 'regulations' table stores ingested Canadian laws/regulations
        # The 'documents' table is for user-uploaded documents
        result = db_session.execute(text("SELECT COUNT(*) FROM regulations"))
        stats['regulations'] = result.scalar()
        
        result = db_session.execute(text("SELECT COUNT(*) FROM sections"))
        stats['sections'] = result.scalar()
        
        # Check Neo4j
        graph_service = GraphService()
        graph_stats = graph_service.get_statistics()
        stats['neo4j_nodes'] = graph_stats.get('node_count', 0)
        
    except Exception as e:
        print(f"Warning: Could not check existing data: {e}")
    
    return stats


def prompt_user_choice(existing_stats: dict) -> tuple:
    """
    Prompt user for what data to load.
    
    Returns:
        (data_type, limit) where data_type is 'laws', 'regulations', or 'both'
    """
    if existing_stats['regulations'] > 100:
        print(f"\n⚠️  Existing data detected:")
        print(f"   - {existing_stats['regulations']:,} regulations")
        print(f"   - {existing_stats['sections']:,} sections")
        print(f"   - {existing_stats['neo4j_nodes']:,} Neo4j nodes")
        print("\nData appears to be already loaded.")
        
        response = input("\nWould you like to re-ingest data anyway? (yes/no) [no]: ").strip().lower()
        if response not in ['yes', 'y']:
            print("Skipping data ingestion.")
            return None, None
    
    print("\n" + "="*60)
    print("🚀 Regulatory Intelligence Assistant - Data Initialization")
    print("="*60)
    print("\nWhat data would you like to load?")
    print("\n1. Canadian Laws (Acts/Lois) - ~800 documents")
    print("   Examples: Employment Insurance Act, Canada Pension Plan")
    print("\n2. Regulations - ~4,240 documents")
    print("   Examples: Employment Insurance Regulations")
    print("\n3. Both Laws and Regulations (Full Dataset) - ~5,040 documents")
    print("   Includes all Canadian federal legislation")
    print("\n0. Skip data loading (for manual ingestion later)")
    
    while True:
        choice = input("\nEnter your choice (0-3) [3]: ").strip() or "3"
        
        if choice == "0":
            return None, None
        elif choice == "1":
            data_type = "laws"
            break
        elif choice == "2":
            data_type = "regulations"
            break
        elif choice == "3":
            data_type = "both"
            break
        else:
            print("Invalid choice. Please enter 0, 1, 2, or 3.")
    
    # Ask for limit
    print(f"\n📊 Selected: {data_type}")
    print("\nHow many documents would you like to load?")
    print("  - Enter a number (e.g., 10, 50, 100) for testing")
    print("  - Press Enter for ALL documents (recommended for production)")
    
    limit_input = input("\nLimit [ALL]: ").strip()
    
    if limit_input:
        try:
            limit = int(limit_input)
            print(f"\n✓ Will load {limit} documents")
        except ValueError:
            print("Invalid number. Loading ALL documents.")
            limit = None
    else:
        limit = None
        print("\n✓ Will load ALL documents")
    
    return data_type, limit


def download_data_if_needed(data_type: str, limit: Optional[int] = None) -> bool:
    """
    Download data files if they don't exist.
    
    Args:
        data_type: 'laws', 'regulations', or 'both'
        limit: Optional limit on number of documents to download
        
    Returns:
        True if data is available, False otherwise
    """
    data_dir = Path("data/regulations/canadian_laws")
    xml_files = list(data_dir.glob("**/*.xml"))
    
    if xml_files and len(xml_files) >= (limit or 10):
        print(f"\n✓ Found {len(xml_files)} XML files - skipping download")
        return True
    
    print(f"\n⚠️  No data files found in {data_dir}")
    print("\nWould you like to download data now?")
    print("This will use the Canadian Laws downloader (laws-lois.justice.gc.ca)")
    
    response = input("\nDownload now? (yes/no) [yes]: ").strip().lower() or "yes"
    
    if response not in ['yes', 'y']:
        print("\nTo download manually later, run:")
        print("  python ingestion/download_canadian_laws.py")
        print("  or")
        print("  bash scripts/download_bulk_regulations.sh")
        return False
    
    # Import and run downloader
    try:
        print("\n📥 Downloading Canadian laws...")
        from ingestion.download_canadian_laws import main as download_main
        download_main()
        
        # Check if files were downloaded
        xml_files = list(data_dir.glob("**/*.xml"))
        if xml_files:
            print(f"\n✓ Successfully downloaded {len(xml_files)} files")
            return True
        else:
            print("\n⚠️  Download completed but no files found")
            return False
            
    except Exception as e:
        print(f"\n❌ Download failed: {e}")
        print("\nPlease download manually:")
        print("  python ingestion/download_canadian_laws.py")
        return False


def run_ingestion(data_type: str, limit: Optional[int] = None):
    """
    Run the data ingestion pipeline.
    
    Args:
        data_type: 'laws', 'regulations', or 'both'
        limit: Optional limit on number of documents to process
    """
    print("\n" + "="*60)
    print("📥 Starting Data Ingestion")
    print("="*60)
    
    db = SessionLocal()
    try:
        # Check if data files exist, offer to download if not
        if not download_data_if_needed(data_type, limit):
            return False
        
        # Initialize services
        graph_service = GraphService()
        search_service = SearchService()
        
        # Initialize pipeline
        pipeline = DataIngestionPipeline(
            db_session=db,
            graph_service=graph_service,
            search_service=search_service
        )
        
        # Determine source directory based on data type
        data_dir = Path("data/regulations/canadian_laws")
        
        # Get XML files
        xml_files = list(data_dir.glob("**/*.xml"))
        
        # Filter by type if needed
        if data_type == "laws":
            # Acts typically contain "Act" or "Loi" in filename
            xml_files = [f for f in xml_files if any(x in f.stem for x in ['Act', 'Loi'])]
        elif data_type == "regulations":
            # Regulations typically contain "Regulations" or "Règlement"
            xml_files = [f for f in xml_files if any(x in f.stem for x in ['Regulation', 'Règlement'])]
        
        # Apply limit if specified
        if limit:
            xml_files = xml_files[:limit]
        
        print(f"\n📄 Found {len(xml_files)} XML files to process")
        
        if len(xml_files) == 0:
            print(f"\n⚠️  No files match criteria for '{data_type}'")
            return False
        
        # Confirm before proceeding with large datasets
        if len(xml_files) > 50 and not limit:
            response = input(f"\nThis will process {len(xml_files)} files. Continue? (yes/no) [yes]: ").strip().lower()
            if response in ['no', 'n']:
                print("Cancelled.")
                return False
        
        print("\n⏳ Processing files... (this may take several minutes)")
        
        # Process files directly since we've already filtered them
        import asyncio
        
        async def process_files():
            """Process the filtered XML files."""
            for i, xml_file in enumerate(xml_files, 1):
                print(f"[{i}/{len(xml_files)}] Processing {xml_file.name}...")
                try:
                    await pipeline.ingest_xml_file(str(xml_file))
                    pipeline.stats['successful'] += 1
                except Exception as e:
                    print(f"  ✗ Failed: {e}")
                    pipeline.stats['failed'] += 1
                
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(xml_files)} files processed")
        
        # Update total files stat and run processing
        pipeline.stats['total_files'] = len(xml_files)
        asyncio.run(process_files())
        
        # Commit final changes
        try:
            db.commit()
        except Exception as e:
            print(f"Warning: Final commit failed: {e}")
            db.rollback()
        
        # Print statistics
        print("\n" + "="*60)
        print("✅ Ingestion Complete!")
        print("="*60)
        print(f"\n📊 Statistics:")
        print(f"   - Documents created: {pipeline.stats['regulations_created']:,}")
        print(f"   - Sections created: {pipeline.stats['sections_created']:,}")
        print(f"   - Neo4j nodes: {pipeline.stats['graph_nodes_created']:,}")
        print(f"   - Neo4j relationships: {pipeline.stats['graph_relationships_created']:,}")
        print(f"   - Elasticsearch documents: {pipeline.stats['elasticsearch_indexed']:,}")
        print(f"   - Success rate: {pipeline.stats['successful']}/{pipeline.stats['total_files']} files")
        
        if pipeline.stats['failed'] > 0:
            print(f"\n⚠️  {pipeline.stats['failed']} files failed to process")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Initialize regulatory database with Canadian laws and regulations"
    )
    parser.add_argument(
        '--type',
        choices=['laws', 'regulations', 'both'],
        help='Type of data to load (bypasses interactive prompt)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of documents to process'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-ingestion even if data exists'
    )
    parser.add_argument(
        '--non-interactive',
        action='store_true',
        help='Run without prompts (use with --type)'
    )
    
    args = parser.parse_args()
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Check existing data
        if not args.force:
            existing_stats = check_existing_data(db)
        else:
            existing_stats = {'regulations': 0, 'sections': 0, 'neo4j_nodes': 0}
        
        # Determine what to load
        if args.non_interactive:
            if not args.type:
                print("Error: --type required when using --non-interactive")
                sys.exit(1)
            data_type = args.type
            limit = args.limit
        elif args.type:
            # Type specified, but still confirm if data exists
            data_type = args.type
            limit = args.limit
            if existing_stats['regulations'] > 100 and not args.force:
                print(f"\n⚠️  Existing data detected ({existing_stats['regulations']:,} regulations)")
                response = input("Continue anyway? (yes/no) [no]: ").strip().lower()
                if response not in ['yes', 'y']:
                    print("Cancelled.")
                    sys.exit(0)
        else:
            # Interactive mode
            data_type, limit = prompt_user_choice(existing_stats)
        
        if data_type is None:
            print("\nNo data to load. Exiting.")
            sys.exit(0)
        
        # Run ingestion
        success = run_ingestion(data_type, limit)
        
        if success:
            print("\n✅ Database initialization complete!")
            print("\nYou can now access:")
            print("  - Frontend: http://localhost:5173")
            print("  - API: http://localhost:8000/docs")
            print("  - Neo4j: http://localhost:7474")
            sys.exit(0)
        else:
            print("\n❌ Initialization failed")
            sys.exit(1)
            
    finally:
        db.close()


if __name__ == "__main__":
    main()
