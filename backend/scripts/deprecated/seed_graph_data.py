"""
Seed Neo4j knowledge graph with comprehensive regulatory data.
This script creates 10-20 regulations with relationships.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.graph_service import get_graph_service
from datetime import date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_comprehensive_regulatory_data():
    """Create a comprehensive set of 15+ regulations with relationships."""
    logger.info("Creating comprehensive regulatory data...")
    
    service = get_graph_service()
    created_items = {
        'legislation': [],
        'regulations': [],
        'sections': [],
        'programs': [],
        'situations': []
    }
    
    # ========================================
    # 1. EMPLOYMENT & LABOR LEGISLATION
    # ========================================
    
    ei_act = service.create_legislation(
        title="Employment Insurance Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1996, 6, 30),
        status="active",
        full_text="An Act respecting employment insurance in Canada",
        act_number="S.C. 1996, c. 23",
        metadata={"category": "employment", "last_amended": "2024-01-15"}
    )
    created_items['legislation'].append(ei_act)
    logger.info(f"✓ Created: {ei_act['title']}")
    
    # EI Sections
    ei_sections = [
        service.create_section(
            section_number="7(1)",
            title="Eligibility for benefits",
            content="Subject to this Part, benefits are payable to an insured person who qualifies to receive them.",
            level=0,
            metadata={"category": "eligibility"}
        ),
        service.create_section(
            section_number="7(2)",
            title="Qualification requirements",
            content="An insured person qualifies if the person has accumulated the required number of hours of insurable employment.",
            level=0,
            metadata={"category": "eligibility"}
        ),
        service.create_section(
            section_number="12",
            title="Benefit period",
            content="The benefit period of a claimant begins on the Sunday of the week in which the interruption of earnings occurs.",
            level=0,
            metadata={"category": "benefits"}
        ),
    ]
    
    for i, section in enumerate(ei_sections):
        service.link_section_to_legislation(section['id'], ei_act['id'], order=i)
        created_items['sections'].append(section)
    
    # ========================================
    # 2. PENSION & RETIREMENT
    # ========================================
    
    cpp_act = service.create_legislation(
        title="Canada Pension Plan",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1965, 4, 3),
        status="active",
        full_text="An Act to establish the Canada Pension Plan",
        act_number="R.S.C. 1985, c. C-8",
        metadata={"category": "pension", "last_amended": "2023-12-01"}
    )
    created_items['legislation'].append(cpp_act)
    logger.info(f"✓ Created: {cpp_act['title']}")
    
    cpp_sections = [
        service.create_section(
            section_number="44(1)",
            title="Retirement pension eligibility",
            content="A retirement pension shall be paid to every person who has reached 60 years of age and has made contributions.",
            level=0
        ),
        service.create_section(
            section_number="44(2)",
            title="Amount of pension",
            content="The amount of the retirement pension is calculated based on contributions and earnings.",
            level=0
        ),
    ]
    
    for i, section in enumerate(cpp_sections):
        service.link_section_to_legislation(section['id'], cpp_act['id'], order=i)
        created_items['sections'].append(section)
    
    oas_act = service.create_legislation(
        title="Old Age Security Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1952, 7, 1),
        status="active",
        full_text="An Act respecting old age security",
        act_number="R.S.C. 1985, c. O-9",
        metadata={"category": "pension", "last_amended": "2024-03-01"}
    )
    created_items['legislation'].append(oas_act)
    logger.info(f"✓ Created: {oas_act['title']}")
    
    oas_section = service.create_section(
        section_number="3(1)",
        title="Eligibility for old age security pension",
        content="A full monthly pension may be paid to every person who has attained 65 years of age and is a Canadian citizen or legal resident.",
        level=0
    )
    service.link_section_to_legislation(oas_section['id'], oas_act['id'], order=0)
    created_items['sections'].append(oas_section)
    
    # ========================================
    # 3. IMMIGRATION & CITIZENSHIP
    # ========================================
    
    irpa = service.create_legislation(
        title="Immigration and Refugee Protection Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(2002, 6, 28),
        status="active",
        act_number="S.C. 2001, c. 27",
        metadata={"category": "immigration", "last_amended": "2023-06-22"}
    )
    created_items['legislation'].append(irpa)
    logger.info(f"✓ Created: {irpa['title']}")
    
    irpa_sections = [
        service.create_section(
            section_number="11(1)",
            title="Application for visa",
            content="A foreign national must apply for a visa before entering Canada.",
            level=0
        ),
        service.create_section(
            section_number="20(1)",
            title="Obligation - visa",
            content="Every foreign national must hold a visa before entering Canada unless they are exempted.",
            level=0
        ),
    ]
    
    for i, section in enumerate(irpa_sections):
        service.link_section_to_legislation(section['id'], irpa['id'], order=i)
        created_items['sections'].append(section)
    
    citizenship_act = service.create_legislation(
        title="Citizenship Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1977, 2, 15),
        status="active",
        act_number="R.S.C. 1985, c. C-29",
        metadata={"category": "immigration", "last_amended": "2024-04-01"}
    )
    created_items['legislation'].append(citizenship_act)
    logger.info(f"✓ Created: {citizenship_act['title']}")
    
    # ========================================
    # 4. HEALTH & SOCIAL SERVICES
    # ========================================
    
    canada_health_act = service.create_legislation(
        title="Canada Health Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1984, 4, 1),
        status="active",
        act_number="R.S.C. 1985, c. C-6",
        metadata={"category": "health", "last_amended": "2023-09-15"}
    )
    created_items['legislation'].append(canada_health_act)
    logger.info(f"✓ Created: {canada_health_act['title']}")
    
    # ========================================
    # 5. LABOR & EMPLOYMENT STANDARDS
    # ========================================
    
    labour_code = service.create_legislation(
        title="Canada Labour Code",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1971, 3, 1),
        status="active",
        act_number="R.S.C. 1985, c. L-2",
        metadata={"category": "employment", "last_amended": "2024-02-20"}
    )
    created_items['legislation'].append(labour_code)
    logger.info(f"✓ Created: {labour_code['title']}")
    
    employment_equity_act = service.create_legislation(
        title="Employment Equity Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1995, 10, 24),
        status="active",
        act_number="S.C. 1995, c. 44",
        metadata={"category": "employment", "last_amended": "2023-11-10"}
    )
    created_items['legislation'].append(employment_equity_act)
    logger.info(f"✓ Created: {employment_equity_act['title']}")
    
    # ========================================
    # 6. HUMAN RIGHTS & ACCESSIBILITY
    # ========================================
    
    human_rights_act = service.create_legislation(
        title="Canadian Human Rights Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1977, 3, 1),
        status="active",
        act_number="R.S.C. 1985, c. H-6",
        metadata={"category": "rights", "last_amended": "2024-01-05"}
    )
    created_items['legislation'].append(human_rights_act)
    logger.info(f"✓ Created: {human_rights_act['title']}")
    
    accessibility_act = service.create_legislation(
        title="Accessible Canada Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(2019, 7, 11),
        status="active",
        act_number="S.C. 2019, c. 10",
        metadata={"category": "accessibility", "last_amended": "2023-08-15"}
    )
    created_items['legislation'].append(accessibility_act)
    logger.info(f"✓ Created: {accessibility_act['title']}")
    
    # ========================================
    # 7. STUDENT ASSISTANCE & EDUCATION
    # ========================================
    
    student_loans_act = service.create_legislation(
        title="Canada Student Loans Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1964, 7, 30),
        status="active",
        act_number="R.S.C. 1985, c. S-23",
        metadata={"category": "education", "last_amended": "2023-07-01"}
    )
    created_items['legislation'].append(student_loans_act)
    logger.info(f"✓ Created: {student_loans_act['title']}")
    
    # ========================================
    # 8. FAMILY BENEFITS
    # ========================================
    
    ccb_legislation = service.create_legislation(
        title="Canada Child Benefit Legislation",
        jurisdiction="federal",
        authority="Canada Revenue Agency",
        effective_date=date(2016, 7, 1),
        status="active",
        act_number="Income Tax Act provisions",
        metadata={"category": "family_benefits", "last_amended": "2024-01-01"}
    )
    created_items['legislation'].append(ccb_legislation)
    logger.info(f"✓ Created: {ccb_legislation['title']}")
    
    # ========================================
    # 9. DISABILITY BENEFITS
    # ========================================
    
    cpp_disability = service.create_legislation(
        title="CPP Disability Benefits Provisions",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1997, 1, 1),
        status="active",
        act_number="Part of CPP",
        metadata={"category": "disability", "last_amended": "2023-10-15"}
    )
    created_items['legislation'].append(cpp_disability)
    logger.info(f"✓ Created: {cpp_disability['title']}")
    
    # ========================================
    # 10. PRIVACY & DATA PROTECTION
    # ========================================
    
    privacy_act = service.create_legislation(
        title="Privacy Act",
        jurisdiction="federal",
        authority="Parliament of Canada",
        effective_date=date(1983, 7, 1),
        status="active",
        act_number="R.S.C. 1985, c. P-21",
        metadata={"category": "privacy", "last_amended": "2023-12-10"}
    )
    created_items['legislation'].append(privacy_act)
    logger.info(f"✓ Created: {privacy_act['title']}")
    
    # ========================================
    # CREATE REGULATIONS
    # ========================================
    
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
    created_items['regulations'].append(ei_reg)
    logger.info(f"✓ Created regulation: {ei_reg['title']}")
    
    irpa_reg = service.create_regulation(
        title="Immigration and Refugee Protection Regulations",
        authority="Governor in Council",
        effective_date=date(2002, 6, 28),
        status="active",
        metadata={"regulation_number": "SOR/2002-227"}
    )
    service.link_regulation_to_legislation(
        irpa_reg['id'],
        irpa['id'],
        description="Implements IRPA provisions"
    )
    created_items['regulations'].append(irpa_reg)
    logger.info(f"✓ Created regulation: {irpa_reg['title']}")
    
    # ========================================
    # CREATE PROGRAMS
    # ========================================
    
    programs = [
        {
            "name": "Employment Insurance Regular Benefits",
            "department": "Employment and Social Development Canada",
            "description": "Provides temporary financial assistance to unemployed Canadians",
            "eligibility_criteria": [
                "Lost job through no fault of own",
                "Available and able to work",
                "Actively seeking employment",
                "Worked required insurable hours"
            ],
            "regulation_id": ei_reg['id']
        },
        {
            "name": "Canada Pension Plan Retirement",
            "department": "Service Canada",
            "description": "Monthly retirement income for contributors",
            "eligibility_criteria": [
                "Contributed to CPP",
                "At least 60 years old",
                "Made valid application"
            ],
            "regulation_id": None
        },
        {
            "name": "Old Age Security",
            "department": "Service Canada",
            "description": "Monthly payment for seniors 65+",
            "eligibility_criteria": [
                "65 years or older",
                "Canadian citizen or legal resident",
                "Resided in Canada for required years"
            ],
            "regulation_id": None
        },
        {
            "name": "Canada Child Benefit",
            "department": "Canada Revenue Agency",
            "description": "Tax-free monthly payment to eligible families",
            "eligibility_criteria": [
                "Have children under 18",
                "Primary caregiver",
                "Canadian resident",
                "Filed tax return"
            ],
            "regulation_id": None
        },
        {
            "name": "CPP Disability Benefits",
            "department": "Service Canada",
            "description": "Benefits for contributors unable to work",
            "eligibility_criteria": [
                "Severe and prolonged disability",
                "Contributed to CPP",
                "Under 65 years old"
            ],
            "regulation_id": None
        },
    ]
    
    for prog_data in programs:
        reg_id = prog_data.pop('regulation_id', None)
        program = service.create_program(**prog_data)
        created_items['programs'].append(program)
        logger.info(f"✓ Created program: {program['name']}")
        
        if reg_id:
            service.link_regulation_to_program(
                reg_id,
                program['id'],
                description=f"{prog_data['name']} requirements"
            )
    
    # ========================================
    # CREATE SITUATIONS
    # ========================================
    
    situations = [
        {
            "description": "Temporary foreign worker seeking employment benefits",
            "tags": ["temporary_worker", "employment_insurance", "work_permit"],
            "sections": [ei_sections[0]['id'], ei_sections[1]['id']],
            "relevance": 0.95
        },
        {
            "description": "Planning for retirement at age 60",
            "tags": ["retirement", "pension", "seniors"],
            "sections": [cpp_sections[0]['id'], oas_section['id']],
            "relevance": 0.90
        },
        {
            "description": "Applying for permanent residence",
            "tags": ["immigration", "permanent_residence", "pr_application"],
            "sections": [irpa_sections[0]['id'], irpa_sections[1]['id']],
            "relevance": 0.92
        },
        {
            "description": "Parent applying for child benefits",
            "tags": ["family", "children", "benefits"],
            "sections": [],
            "relevance": 0.88
        },
        {
            "description": "Person with disability seeking support",
            "tags": ["disability", "support", "benefits"],
            "sections": [],
            "relevance": 0.93
        },
    ]
    
    for sit_data in situations:
        section_ids = sit_data.pop('sections', [])
        relevance = sit_data.pop('relevance', 0.85)
        
        situation = service.create_situation(
            description=sit_data['description'],
            tags=sit_data['tags']
        )
        created_items['situations'].append(situation)
        logger.info(f"✓ Created situation: {situation['description']}")
        
        for section_id in section_ids:
            service.link_section_to_situation(
                section_id,
                situation['id'],
                relevance_score=relevance,
                description=f"Relevant for {sit_data['description']}"
            )
    
    # ========================================
    # CREATE CROSS-REFERENCES
    # ========================================
    
    if len(ei_sections) >= 2:
        service.create_section_reference(
            ei_sections[0]['id'],
            ei_sections[1]['id'],
            citation_text="See Section 7(2) for qualification details",
            context="Eligibility determination"
        )
        logger.info("✓ Created section cross-references")
    
    return created_items


def main():
    """Main seeding function."""
    print("\n" + "="*60)
    print("Neo4j Knowledge Graph - Comprehensive Data Seeding")
    print("="*60 + "\n")
    
    try:
        # Get graph service and ensure fulltext indexes
        service = get_graph_service()
        print("🔍 Ensuring fulltext indexes are created...")
        service._ensure_fulltext_indexes()
        print("✅ Fulltext indexes ensured")
        
        # Create comprehensive data
        created = create_comprehensive_regulatory_data()
        
        # Get overview
        overview = service.get_graph_overview()
        
        print("\n" + "="*60)
        print("Graph Statistics")
        print("="*60)
        print(f"\nLegislation created: {len(created['legislation'])}")
        print(f"Regulations created: {len(created['regulations'])}")
        print(f"Sections created: {len(created['sections'])}")
        print(f"Programs created: {len(created['programs'])}")
        print(f"Situations created: {len(created['situations'])}")
        
        print("\n" + "-"*60)
        print("Total Nodes by Type:")
        for label, count in overview['nodes'].items():
            print(f"  {label}: {count}")
        
        print("\nTotal Relationships by Type:")
        for rel_type, count in overview['relationships'].items():
            print(f"  {rel_type}: {count}")
        
        print("\n" + "="*60)
        print("✓ Comprehensive data seeding completed successfully!")
        print("="*60)
        print("\nNext steps:")
        print("1. View graph in Neo4j Browser: http://localhost:7474")
        print("2. Login with: neo4j / password123")
        print("3. Run: MATCH (n) RETURN n LIMIT 50")
        print("\n")
        
    except Exception as e:
        logger.error(f"\n✗ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
