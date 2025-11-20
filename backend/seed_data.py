"""
Seed database with sample regulatory data for testing.
Run this script to populate the database with initial data.
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models.models import (
    User, Regulation, Section, Citation, Amendment,
    QueryHistory, WorkflowSession, WorkflowStep,
    AlertSubscription, Alert
)
from datetime import datetime, date
import uuid


def seed_users(db: Session):
    """Create sample users."""
    users = [
        User(
            email="admin@gov.example.com",
            role="admin",
            department="Treasury Board",
            preferences={"language": "en", "notifications": True}
        ),
        User(
            email="caseworker@gov.example.com",
            role="employee",
            department="Employment and Social Development",
            preferences={"language": "en", "theme": "light"}
        ),
        User(
            email="citizen@example.com",
            role="citizen",
            preferences={"language": "en"}
        ),
    ]
    
    for user in users:
        db.add(user)
    
    db.commit()
    print(f"✓ Created {len(users)} users")
    return users


def seed_regulations(db: Session):
    """Create sample regulations."""
    regulations = [
        Regulation(
            title="Employment Insurance Act",
            jurisdiction="federal",
            authority="Parliament of Canada",
            effective_date=date(1996, 6, 30),
            status="active",
            full_text="An Act respecting employment insurance in Canada...",
            content_hash="abc123...",
            extra_metadata={
                "act_number": "S.C. 1996, c. 23",
                "last_amended": "2024-01-15"
            }
        ),
        Regulation(
            title="Canada Pension Plan",
            jurisdiction="federal",
            authority="Parliament of Canada",
            effective_date=date(1965, 4, 3),
            status="active",
            full_text="An Act to establish the Canada Pension Plan...",
            content_hash="def456...",
            extra_metadata={
                "act_number": "R.S.C. 1985, c. C-8",
                "last_amended": "2023-12-01"
            }
        ),
        Regulation(
            title="Old Age Security Act",
            jurisdiction="federal",
            authority="Parliament of Canada",
            effective_date=date(1952, 7, 1),
            status="active",
            full_text="An Act respecting old age security...",
            content_hash="ghi789...",
            extra_metadata={
                "act_number": "R.S.C. 1985, c. O-9",
                "last_amended": "2024-03-01"
            }
        ),
    ]
    
    for regulation in regulations:
        db.add(regulation)
    
    db.commit()
    print(f"✓ Created {len(regulations)} regulations")
    return regulations


def seed_sections(db: Session, regulations: list):
    """Create sample sections."""
    sections = []
    
    # Employment Insurance Act sections
    ei_sections = [
        Section(
            regulation_id=regulations[0].id,
            section_number="7(1)",
            title="Eligibility for benefits",
            content="Subject to this Part, benefits are payable to an insured person who qualifies to receive them.",
            extra_metadata={"category": "eligibility"}
        ),
        Section(
            regulation_id=regulations[0].id,
            section_number="7(2)",
            title="Qualification requirements",
            content="An insured person qualifies if the person has accumulated the required number of hours of insurable employment.",
            extra_metadata={"category": "eligibility"}
        ),
    ]
    
    # CPP sections
    cpp_sections = [
        Section(
            regulation_id=regulations[1].id,
            section_number="44(1)",
            title="Amount of retirement pension",
            content="A retirement pension shall be paid to every person who has reached 60 years of age...",
            extra_metadata={"category": "benefits"}
        ),
    ]
    
    sections.extend(ei_sections)
    sections.extend(cpp_sections)
    
    for section in sections:
        db.add(section)
    
    db.commit()
    print(f"✓ Created {len(sections)} sections")
    return sections


def seed_citations(db: Session, sections: list):
    """Create sample cross-references."""
    if len(sections) >= 2:
        citation = Citation(
            section_id=sections[0].id,
            cited_section_id=sections[1].id,
            citation_text="See also Section 7(2)"
        )
        db.add(citation)
        db.commit()
        print("✓ Created 1 citation")


def seed_amendments(db: Session, regulations: list):
    """Create sample amendments."""
    amendment = Amendment(
        regulation_id=regulations[0].id,
        amendment_type="modified",
        effective_date=date(2024, 1, 15),
        description="Updated eligibility requirements for temporary foreign workers",
        extra_metadata={"bill_number": "C-47", "royal_assent": "2024-01-10"}
    )
    db.add(amendment)
    db.commit()
    print("✓ Created 1 amendment")


def seed_query_history(db: Session, users: list):
    """Create sample query history."""
    queries = [
        QueryHistory(
            user_id=users[1].id,
            query="Can a temporary resident apply for employment insurance?",
            entities={"person_type": ["temporary_resident"], "program": ["employment_insurance"]},
            intent="search",
            results=[{"regulation_id": str(uuid.uuid4()), "relevance": 0.95}],
            rating=5
        ),
        QueryHistory(
            user_id=users[2].id,
            query="How do I apply for Canada Pension Plan?",
            entities={"program": ["cpp"], "action": ["apply"]},
            intent="compliance",
            results=[{"regulation_id": str(uuid.uuid4()), "relevance": 0.89}],
            rating=4
        ),
    ]
    
    for query in queries:
        db.add(query)
    
    db.commit()
    print(f"✓ Created {len(queries)} query history entries")


def seed_workflows(db: Session, users: list):
    """Create sample workflow sessions."""
    workflow = WorkflowSession(
        user_id=users[1].id,
        workflow_type="ei_application",
        state={"step": 1, "data": {"applicant_name": "John Doe"}},
        status="active",
        extra_metadata={"application_id": "EI-2024-001"}
    )
    db.add(workflow)
    db.commit()
    
    # Add workflow steps
    steps = [
        WorkflowStep(
            session_id=workflow.id,
            step_number=1,
            action="personal_information",
            input_data={"name": "John Doe", "sin": "123-456-789"},
            validation_result={"valid": True},
            completed_at=datetime.utcnow()
        ),
    ]
    
    for step in steps:
        db.add(step)
    
    db.commit()
    print(f"✓ Created 1 workflow with {len(steps)} steps")


def seed_alerts(db: Session, users: list, regulations: list):
    """Create sample alert subscriptions and alerts."""
    subscription = AlertSubscription(
        user_id=users[1].id,
        jurisdiction="federal",
        topics=["employment_insurance", "cpp"],
        frequency="daily",
        active=True
    )
    db.add(subscription)
    db.commit()
    
    alert = Alert(
        subscription_id=subscription.id,
        change_type="amended",
        regulation_id=regulations[0].id,
        summary="Employment Insurance Act amended to update eligibility for temporary workers",
        read=False,
        extra_metadata={"amendment_id": str(uuid.uuid4())}
    )
    db.add(alert)
    db.commit()
    print("✓ Created 1 alert subscription and 1 alert")


def clear_database(db: Session):
    """Clear all data from database (for testing)."""
    print("Clearing existing data...")
    
    # Delete in reverse order of dependencies
    db.query(Alert).delete()
    db.query(AlertSubscription).delete()
    db.query(WorkflowStep).delete()
    db.query(WorkflowSession).delete()
    db.query(QueryHistory).delete()
    db.query(Amendment).delete()
    db.query(Citation).delete()
    db.query(Section).delete()
    db.query(Regulation).delete()
    db.query(User).delete()
    
    db.commit()
    print("✓ Database cleared")


def main():
    """Main seeding function."""
    print("\n" + "="*50)
    print("Seeding Regulatory Intelligence Database")
    print("="*50 + "\n")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Clear existing data (comment out if you want to keep existing data)
        clear_database(db)
        
        # Seed data in order of dependencies
        users = seed_users(db)
        regulations = seed_regulations(db)
        sections = seed_sections(db, regulations)
        seed_citations(db, sections)
        seed_amendments(db, regulations)
        seed_query_history(db, users)
        seed_workflows(db, users)
        seed_alerts(db, users, regulations)
        
        print("\n" + "="*50)
        print("✓ Database seeding completed successfully!")
        print("="*50 + "\n")
        
    except Exception as e:
        print(f"\n✗ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
