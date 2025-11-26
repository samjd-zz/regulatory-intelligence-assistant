"""
Initialize Neo4j knowledge graph with schema and sample data.
Run this script to set up the graph database.
"""
import sys
import os
from pathlib import Path

# Add backend directory to Python path
# In Docker: /app/scripts -> /app
# Locally: /path/to/backend/scripts -> /path/to/backend
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.neo4j_client import get_neo4j_client
from services.graph_service import get_graph_service
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_schema():
    """Initialize Neo4j schema with constraints and indexes."""
    logger.info("Initializing Neo4j schema...")
    
    client = get_neo4j_client()
    
    # Read Cypher script
    script_path = Path(__file__).parent / 'init_graph.cypher'
    with open(script_path, 'r') as f:
        cypher_script = f.read()
    
    # Execute each statement separately
    statements = [s.strip() for s in cypher_script.split(';') if s.strip() and not s.strip().startswith('//')]
    
    for statement in statements:
        if statement and not statement.startswith('CALL db.'):  # Skip verification queries
            try:
                client.execute_write(statement)
                logger.info(f"Executed: {statement[:50]}...")
            except Exception as e:
                logger.warning(f"Statement may have failed (might already exist): {e}")
    
    logger.info("✓ Schema initialization complete")


def create_sample_data():
    """Create sample regulatory data in the knowledge graph."""
    logger.info("\nPopulating sample data...")
    
    service = get_graph_service()
    
    # 1. Employment Insurance Act
    ei_act = service.create_legislation(
        title="Employment Insurance Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1996, 6, 30),
        status="active",
        full_text="An Act respecting employment insurance in Canada",
        act_number="S.C. 1996, c. 23",
        metadata={"last_amended": "2024-01-15"}
    )
    logger.info(f"✓ Created: {ei_act['title']}")
    
    # EI Act sections
    ei_section1 = service.create_section(
        section_number="7(1)",
        title="Eligibility for benefits",
        content="Subject to this Part, benefits are payable to an insured person who qualifies to receive them.",
        level=0
    )
    service.link_section_to_legislation(ei_section1['id'], ei_act['id'], order=0)
    
    ei_section2 = service.create_section(
        section_number="7(2)",
        title="Qualification requirements",
        content="An insured person qualifies if the person has accumulated the required number of hours of insurable employment.",
        level=0
    )
    service.link_section_to_legislation(ei_section2['id'], ei_act['id'], order=1)
    
    # 2. Canada Pension Plan
    cpp_act = service.create_legislation(
        title="Canada Pension Plan",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1965, 4, 3),
        status="active",
        full_text="An Act to establish the Canada Pension Plan",
        act_number="R.S.C. 1985, c. C-8",
        metadata={"last_amended": "2023-12-01"}
    )
    logger.info(f"✓ Created: {cpp_act['title']}")
    
    cpp_section = service.create_section(
        section_number="44(1)",
        title="Amount of retirement pension",
        content="A retirement pension shall be paid to every person who has reached 60 years of age and has made contributions for not less than one year.",
        level=0
    )
    service.link_section_to_legislation(cpp_section['id'], cpp_act['id'], order=0)
    
    # 3. Old Age Security Act
    oas_act = service.create_legislation(
        title="Old Age Security Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1952, 7, 1),
        status="active",
        full_text="An Act respecting old age security",
        act_number="R.S.C. 1985, c. O-9",
        metadata={"last_amended": "2024-03-01"}
    )
    logger.info(f"✓ Created: {oas_act['title']}")
    
    oas_section = service.create_section(
        section_number="3(1)",
        title="Eligibility for old age security pension",
        content="Subject to this Act, a full monthly pension may be paid to every person who has attained sixty-five years of age and is a Canadian citizen or legal resident.",
        level=0
    )
    service.link_section_to_legislation(oas_section['id'], oas_act['id'], order=0)
    
    # 4. Immigration and Refugee Protection Act
    irpa = service.create_legislation(
        title="Immigration and Refugee Protection Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(2002, 6, 28),
        status="active",
        act_number="S.C. 2001, c. 27",
        metadata={"last_amended": "2023-06-22"}
    )
    logger.info(f"✓ Created: {irpa['title']}")
    
    # 5. Create Regulations
    ei_reg = service.create_regulation(
        title="Employment Insurance Regulations",
        authority="Governor in Council",
        effective_date=date(1996, 7, 30),
        status="active",
        metadata={"regulation_number": "SOR/96-332"}
    )
    service.link_regulation_to_legislation(
        ei_reg['id'],
        ei_act['id'],
        description="Implements EI Act provisions"
    )
    logger.info(f"✓ Created: {ei_reg['title']}")
    
    # 6. Create Programs
    ei_program = service.create_program(
        name="Employment Insurance Benefits",
        department="Employment and Social Development Canada",
        description="Provides temporary financial assistance to unemployed Canadians",
        eligibility_criteria=[
            "Lost job through no fault of own",
            "Available and able to work",
            "Actively seeking employment",
            "Worked required insurable hours"
        ]
    )
    service.link_regulation_to_program(
        ei_reg['id'],
        ei_program['id'],
        description="EI program requirements"
    )
    logger.info(f"✓ Created program: {ei_program['name']}")
    
    cpp_program = service.create_program(
        name="Canada Pension Plan Retirement Pension",
        department="Service Canada",
        description="Provides monthly retirement income for contributors",
        eligibility_criteria=[
            "Contributed to CPP",
            "At least 60 years old",
            "Made valid CPP application"
        ]
    )
    logger.info(f"✓ Created program: {cpp_program['name']}")
    
    oas_program = service.create_program(
        name="Old Age Security Pension",
        department="Service Canada",
        description="Monthly payment for seniors 65 and older",
        eligibility_criteria=[
            "65 years or older",
            "Canadian citizen or legal resident",
            "Resided in Canada for required years"
        ]
    )
    logger.info(f"✓ Created program: {oas_program['name']}")
    
    # 7. Create Situations
    temp_worker_situation = service.create_situation(
        description="Temporary foreign worker seeking employment benefits",
        tags=["temporary_worker", "employment_insurance", "work_permit"]
    )
    service.link_section_to_situation(
        ei_section1['id'],
        temp_worker_situation['id'],
        relevance_score=0.95,
        description="Eligibility requirements for temporary workers"
    )
    logger.info(f"✓ Created situation: {temp_worker_situation['description']}")
    
    retirement_situation = service.create_situation(
        description="Planning for retirement benefits",
        tags=["retirement", "pension", "seniors"]
    )
    service.link_section_to_situation(
        cpp_section['id'],
        retirement_situation['id'],
        relevance_score=0.9,
        description="CPP retirement eligibility"
    )
    service.link_section_to_situation(
        oas_section['id'],
        retirement_situation['id'],
        relevance_score=0.92,
        description="OAS pension eligibility"
    )
    logger.info(f"✓ Created situation: {retirement_situation['description']}")
    
    # 8. Create cross-references
    service.create_section_reference(
        ei_section1['id'],
        ei_section2['id'],
        citation_text="See Section 7(2) for qualification details",
        context="Eligibility determination"
    )
    logger.info("✓ Created cross-references")
    
    # 9. Get graph overview
    logger.info("\n" + "="*50)
    logger.info("Graph Overview:")
    logger.info("="*50)
    
    overview = service.get_graph_overview()
    logger.info("\nNodes:")
    for label, count in overview['nodes'].items():
        logger.info(f"  {label}: {count}")
    
    logger.info("\nRelationships:")
    for rel_type, count in overview['relationships'].items():
        logger.info(f"  {rel_type}: {count}")
    
    logger.info("\n" + "="*50)
    logger.info("✓ Sample data population complete!")
    logger.info("="*50)


def main():
    """Main initialization function."""
    print("\n" + "="*60)
    print("Neo4j Knowledge Graph Initialization")
    print("="*60 + "\n")
    
    try:
        # Step 1: Initialize schema
        init_schema()
        
        # Step 2: Create sample data
        create_sample_data()
        
        print("\n" + "="*60)
        print("✓ Neo4j initialization completed successfully!")
        print("="*60)
        print("\nYou can now:")
        print("1. View the graph in Neo4j Browser: http://localhost:7474")
        print("2. Run queries using the graph service")
        print("3. Test the health check: curl http://localhost:8000/health/neo4j")
        print("\n")
        
    except Exception as e:
        logger.error(f"\n✗ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
