"""
Statistics Service - Direct Database Queries for Counts and Statistics

This service provides accurate statistics by querying PostgreSQL directly,
bypassing RAG which is limited by context window size.

Use this for:
- "How many regulations..."
- "Total number of..."
- "Count of..."
- Other statistical queries

Author: Developer 2 (AI/ML Engineer)
Created: 2025-12-03
"""

import logging
from typing import Dict, Any, Optional, List
from sqlalchemy import func, distinct, and_, or_
from sqlalchemy.orm import Session
from datetime import datetime

from database import SessionLocal
from models.models import Regulation, Section, Amendment

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatisticsService:
    """
    Service for querying database statistics directly.
    
    Provides accurate counts and statistics by querying PostgreSQL,
    avoiding RAG's context window limitations.
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize statistics service.
        
        Args:
            db_session: Optional database session (creates new if not provided)
        """
        self.db_session = db_session
    
    def _get_session(self) -> Session:
        """Get database session"""
        if self.db_session:
            return self.db_session
        return SessionLocal()
    
    def _close_session(self, session: Session):
        """Close session if it was created internally"""
        if not self.db_session:
            session.close()
    
    def get_total_documents(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get total count of searchable documents (regulations + sections).
        
        Args:
            filters: Optional filters (jurisdiction, language, status, etc.)
            
        Returns:
            Dictionary with count and metadata
        """
        session = self._get_session()
        
        try:
            # Count regulations from regulations table (the CORRECT table!)
            reg_query = session.query(func.count(Regulation.id))
            
            # Count sections from sections table (these are searchable too!)
            section_query = session.query(func.count(Section.id))
            
            # Apply filters if provided
            if filters:
                if 'jurisdiction' in filters:
                    jurisdiction = filters['jurisdiction']
                    reg_query = reg_query.filter(
                        Regulation.jurisdiction == jurisdiction
                    )
                    # For sections, need to join with regulations to filter by jurisdiction
                    section_query = section_query.join(Regulation).filter(
                        Regulation.jurisdiction == jurisdiction
                    )
                
                if 'language' in filters:
                    language = filters['language']
                    reg_query = reg_query.filter(
                        Regulation.language == language
                    )
                    # For sections, join with regulations to filter by language
                    section_query = section_query.join(Regulation).filter(
                        Regulation.language == language
                    )
                
                if 'status' in filters:
                    status = filters['status']
                    reg_query = reg_query.filter(
                        Regulation.status == filters['status']
                    )
                    # Sections don't have status, filter by parent regulation
                    section_query = section_query.join(Regulation).filter(
                        Regulation.status == status
                    )
            
            # Execute queries
            reg_count = reg_query.scalar() or 0
            section_count = section_query.scalar() or 0
            
            # Total searchable documents = regulations + sections
            # (Each regulation and each section is indexed as a separate searchable document)
            total_searchable = reg_count + section_count
            
            return {
                "total_searchable_documents": total_searchable,
                "total_regulations": reg_count,
                "total_sections": section_count,
                "filters_applied": filters or {},
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return {
                "total_searchable_documents": 0,
                "total_regulations": 0,
                "total_sections": 0,
                "error": str(e),
                "filters_applied": filters or {}
            }
        finally:
            self._close_session(session)
    
    def get_documents_by_jurisdiction(self) -> Dict[str, int]:
        """
        Get regulation counts grouped by jurisdiction.
        
        Returns:
            Dictionary mapping jurisdiction to count
        """
        session = self._get_session()
        
        try:
            # Query regulations grouped by jurisdiction
            results = session.query(
                Regulation.jurisdiction,
                func.count(Regulation.id)
            ).group_by(Regulation.jurisdiction).all()
            
            return {
                jurisdiction: count
                for jurisdiction, count in results
            }
            
        except Exception as e:
            logger.error(f"Error getting jurisdiction counts: {e}")
            return {}
        finally:
            self._close_session(session)
    
    def get_documents_by_type(self) -> Dict[str, int]:
        """
        Get regulation counts by type (all are regulations in the current data).
        
        Returns:
            Dictionary mapping document type to count
        """
        session = self._get_session()
        
        try:
            # All items in regulations table are regulations
            total = session.query(func.count(Regulation.id)).scalar() or 0
            
            return {
                "regulation": total
            }
            
        except Exception as e:
            logger.error(f"Error getting document type counts: {e}")
            return {}
        finally:
            self._close_session(session)
    
    def get_regulations_by_language(self) -> Dict[str, int]:
        """
        Get regulation counts grouped by language.
        
        Returns:
            Dictionary mapping language to count
        """
        session = self._get_session()
        
        try:
            # Query regulations grouped by language
            results = session.query(
                Regulation.language,
                func.count(Regulation.id)
            ).group_by(Regulation.language).all()
            
            return {
                language: count
                for language, count in results
            }
            
        except Exception as e:
            logger.error(f"Error getting language counts: {e}")
            return {}
        finally:
            self._close_session(session)
    
    def get_sections_count(
        self,
        regulation_id: Optional[str] = None
    ) -> int:
        """
        Get total count of sections.
        
        Args:
            regulation_id: Optional regulation ID to filter by
            
        Returns:
            Total count of sections
        """
        session = self._get_session()
        
        try:
            query = session.query(func.count(Section.id))
            
            if regulation_id:
                query = query.filter(Section.regulation_id == regulation_id)
            
            return query.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting sections count: {e}")
            return 0
        finally:
            self._close_session(session)
    
    def get_amendments_count(
        self,
        regulation_id: Optional[str] = None
    ) -> int:
        """
        Get total count of amendments.
        
        Args:
            regulation_id: Optional regulation ID to filter by
            
        Returns:
            Total count of amendments
        """
        session = self._get_session()
        
        try:
            query = session.query(func.count(Amendment.id))
            
            if regulation_id:
                query = query.filter(Amendment.regulation_id == regulation_id)
            
            return query.scalar() or 0
            
        except Exception as e:
            logger.error(f"Error getting amendments count: {e}")
            return 0
        finally:
            self._close_session(session)
    
    def get_database_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics summary.
        
        Returns:
            Dictionary with all statistics
        """
        session = self._get_session()
        
        try:
            # Get all counts
            total_stats = self.get_total_documents()
            
            return {
                "summary": {
                    "total_searchable_documents": total_stats.get("total_searchable_documents", 0),
                    "total_regulations": total_stats.get("total_regulations", 0),
                    "total_sections": total_stats.get("total_sections", 0),
                    "total_amendments": self.get_amendments_count(),
                },
                "by_jurisdiction": self.get_documents_by_jurisdiction(),
                "by_type": self.get_documents_by_type(),
                "by_language": self.get_regulations_by_language(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting database summary: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            self._close_session(session)
    
    def format_statistics_answer(
        self,
        question: str,
        statistics: Dict[str, Any]
    ) -> str:
        """
        Format statistics into a natural language answer.
        
        Args:
            question: Original question
            statistics: Statistics dictionary
            
        Returns:
            Formatted answer string
        """
        question_lower = question.lower()
        
        # Detect what kind of count question this is
        if "total" in question_lower or "how many" in question_lower:
            total_searchable = statistics.get("total_searchable_documents", 0)
            total_regs = statistics.get("total_regulations", 0)
            total_sections = statistics.get("total_sections", 0)
            
            # Build comprehensive answer
            answer_parts = []
            
            if total_searchable > 0:
                answer_parts.append(
                    f"The knowledge base contains **{total_searchable:,} searchable documents** indexed for retrieval"
                )
            
            # Breakdown
            breakdown_parts = []
            if total_regs > 0:
                breakdown_parts.append(f"**{total_regs:,} regulations** (Acts, Regulations, and legal instruments)")
            
            if total_sections > 0:
                breakdown_parts.append(f"**{total_sections:,} sections** (individual provisions within regulations)")
            
            if breakdown_parts:
                answer_parts.append("This includes:")
                answer = ". ".join(answer_parts) + ":\n\n" + "\n".join(f"- {part}" for part in breakdown_parts)
            else:
                answer = ". ".join(answer_parts) + "."
            
            # Add breakdown if available
            if "by_jurisdiction" in statistics:
                jurisdictions = statistics["by_jurisdiction"]
                if jurisdictions:
                    answer += "\n\n**By Jurisdiction:**\n"
                    for jurisdiction, count in sorted(
                        jurisdictions.items(),
                        key=lambda x: x[1],
                        reverse=True
                    ):
                        answer += f"- {jurisdiction}: {count:,} regulations\n"
            
            if "by_language" in statistics:
                languages = statistics["by_language"]
                if languages:
                    answer += "\n\n**By Language:**\n"
                    for language, count in sorted(
                        languages.items(),
                        key=lambda x: x[1],
                        reverse=True
                    ):
                        lang_name = "English" if language == "en" else "French" if language == "fr" else language
                        answer += f"- {lang_name}: {count:,} regulations\n"
            
            # Add filters info if applied
            filters_applied = statistics.get("filters_applied", {})
            if filters_applied:
                answer += f"\n\n*Note: These counts reflect the filters applied: {filters_applied}*"
            
            return answer.strip()
        
        # Default response
        return (
            f"The knowledge base contains {statistics.get('total_searchable_documents', 0):,} searchable documents "
            f"from {statistics.get('total_regulations', 0):,} regulations."
        )


if __name__ == "__main__":
    # Test the statistics service
    print("=" * 80)
    print("Statistics Service - Test")
    print("=" * 80)
    
    service = StatisticsService()
    
    # Test 1: Total documents
    print("\n1. Total Searchable Documents:")
    total = service.get_total_documents()
    print(f"   Total Searchable: {total['total_searchable_documents']:,}")
    print(f"   Regulations: {total['total_regulations']:,}")
    print(f"   Sections: {total['total_sections']:,}")
    
    # Test 2: By jurisdiction
    print("\n2. Documents by Jurisdiction:")
    by_jurisdiction = service.get_documents_by_jurisdiction()
    for jurisdiction, count in sorted(
        by_jurisdiction.items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"   {jurisdiction}: {count:,}")
    
    # Test 3: By language
    print("\n3. Documents by Language:")
    by_language = service.get_documents_by_language()
    for language, count in by_language.items():
        print(f"   {language}: {count:,}")
    
    # Test 4: Database Summary:
    print("\n4. Database Summary:")
    summary = service.get_database_summary()
    print(f"   Total Searchable Documents: {summary['summary']['total_searchable_documents']:,}")
    print(f"   Total Regulations: {summary['summary']['total_regulations']:,}")
    print(f"   Total Sections: {summary['summary']['total_sections']:,}")
    print(f"   Total Amendments: {summary['summary']['total_amendments']:,}")
    
    # Test 5: Format answer
    print("\n5. Formatted Answer:")
    question = "How many Canadian federal acts are in the database?"
    answer = service.format_statistics_answer(question, summary)
    print(f"   Question: {question}")
    print(f"   Answer:\n{answer}")
    
    print("\n" + "=" * 80)
    print("Test complete!")
