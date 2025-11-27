"""
Pytest Configuration and Shared Fixtures

Provides shared fixtures and configuration for all test modules.
Handles test data seeding for Elasticsearch and database setup.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-27
"""

import pytest
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load test environment variables
env_path = Path(__file__).parent.parent / '.env.test'
if env_path.exists():
    load_dotenv(env_path, override=True)
    print(f"\n✓ Loaded test environment from {env_path}")
else:
    print(f"\n⚠ Test environment file not found: {env_path}")
    print("  Using default environment variables")

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.search_service import SearchService
from services.gemini_client import get_gemini_client
from database import SessionLocal, engine
from models.models import Base


# ============================================================================
# Service Availability Checks
# ============================================================================

def check_elasticsearch_available():
    """Check if Elasticsearch is running"""
    try:
        service = SearchService()
        result = service.es.ping()
        return result
    except Exception as e:
        print(f"\n⚠ Elasticsearch check failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_gemini_available():
    """Check if Gemini API key is configured"""
    try:
        client = get_gemini_client()
        return client.is_available()
    except:
        return False


# Global availability flags
ES_AVAILABLE = check_elasticsearch_available()
GEMINI_AVAILABLE = check_gemini_available()

# Export skip markers
skip_if_no_es = pytest.mark.skipif(
    not ES_AVAILABLE,
    reason="Elasticsearch not available"
)

skip_if_no_gemini = pytest.mark.skipif(
    not GEMINI_AVAILABLE,
    reason="Gemini API not available (set GEMINI_API_KEY)"
)


# ============================================================================
# Test Data
# ============================================================================

SAMPLE_REGULATIONS = [
    {
        "id": "test-ei-act",
        "title": "Employment Insurance Act - Section 7",
        "content": """The Employment Insurance Act provides temporary financial assistance to unemployed 
        Canadians who have lost their job through no fault of their own, while they look for work or 
        upgrade their skills. To qualify, you must have worked a certain number of insurable hours in 
        the last 52 weeks or since your last claim. You must be able and available for work and 
        actively seeking employment. Permanent residents and citizens are eligible if they meet the 
        hour requirements and are authorized to work in Canada. Benefits are payable to persons who 
        have lost employment and are available for work.""",
        "citation": "S.C. 1996, c. 23, s. 7",
        "section_number": "7",
        "jurisdiction": "federal",
        "program": "employment_insurance",
        "effective_date": "1996-06-30",
        "doc_type": "act",
        "department": "Employment and Social Development Canada"
    },
    {
        "id": "test-cpp-act",
        "title": "Canada Pension Plan - Eligibility and Contributions",
        "content": """The Canada Pension Plan (CPP) provides retirement, disability, and survivor benefits 
        to contributors and their families. To qualify for CPP retirement benefits, you must be at least 
        60 years old and have made at least one valid contribution to the CPP. Contributions are mandatory 
        for all employed and self-employed Canadians aged 18 to 70 who earn more than the minimum exemption 
        ($3,500). The standard age to start receiving CPP is 65, but you can start as early as 60 (with 
        reduced benefits) or delay until 70 (with increased benefits). Contributors must have contributed 
        to the plan during their working years.""",
        "citation": "R.S.C. 1985, c. C-8, s. 44",
        "section_number": "44",
        "jurisdiction": "federal",
        "program": "canada_pension_plan",
        "effective_date": "1966-01-01",
        "doc_type": "act",
        "department": "Employment and Social Development Canada"
    },
    {
        "id": "test-oas-act",
        "title": "Old Age Security Act - Eligibility Requirements",
        "content": """Old Age Security (OAS) is Canada's largest pension program. It provides monthly payments 
        to seniors aged 65 and older who meet Canadian residence requirements. To receive the full OAS pension, 
        you must have resided in Canada for at least 40 years after turning 18. If you have lived in Canada 
        for at least 10 years after age 18, you may qualify for a partial pension. Both Canadian citizens and 
        permanent residents are eligible. Temporary residents do not qualify for OAS. The Guaranteed Income 
        Supplement (GIS) provides additional income to low-income OAS recipients. Applicants must be at least 
        65 years old and must have lived in Canada for at least 10 years after age 18.""",
        "citation": "R.S.C. 1985, c. O-9, s. 3",
        "section_number": "3",
        "jurisdiction": "federal",
        "program": "old_age_security",
        "effective_date": "1952-01-01",
        "doc_type": "act",
        "department": "Employment and Social Development Canada"
    },
    {
        "id": "test-citizenship-act",
        "title": "Citizenship Act - Requirements",
        "content": """The Citizenship Act sets out the requirements and procedures for Canadian citizenship. 
        To become a Canadian citizen, applicants must be permanent residents, have lived in Canada for at 
        least 3 out of the last 5 years, file income taxes if required, pass a citizenship test, and 
        prove language skills in English or French. Applicants aged 18-54 must demonstrate adequate 
        knowledge of Canada and responsibilities of citizenship. Processing times typically range from 
        12 to 24 months. Dual citizenship is allowed in Canada.""",
        "citation": "R.S.C. 1985, c. C-29",
        "section_number": "5",
        "jurisdiction": "federal",
        "program": "citizenship",
        "effective_date": "1977-02-15",
        "doc_type": "act",
        "department": "Immigration, Refugees and Citizenship Canada"
    },
    {
        "id": "test-ccb-policy",
        "title": "Canada Child Benefit - Eligibility and Payment",
        "content": """The Canada Child Benefit (CCB) is a tax-free monthly payment made to eligible families 
        to help with the cost of raising children under 18. To qualify, you must live with the child, be 
        primarily responsible for the child's care and upbringing, be a resident of Canada for tax purposes, 
        and be a Canadian citizen, permanent resident, protected person, or temporary resident who has lived 
        in Canada for the previous 18 months. The benefit is income-tested and paid to the primary caregiver, 
        usually the mother. Maximum benefit is $7,787 per year per child under 6 and $6,570 per child aged 6-17.""",
        "citation": "Income Tax Act, s. 122.6",
        "section_number": "122.6",
        "jurisdiction": "federal",
        "program": "canada_child_benefit",
        "effective_date": "2016-07-01",
        "doc_type": "policy",
        "department": "Canada Revenue Agency"
    },
    {
        "id": "test-bc-worksafe",
        "title": "Workers Compensation Act - British Columbia",
        "content": """WorkSafeBC provides coverage for workers injured on the job in British Columbia. 
        The Workers Compensation Act requires all employers in BC to register and pay premiums for workplace 
        injury insurance. Workers who suffer work-related injuries or illnesses are entitled to wage-loss 
        benefits, medical care, and rehabilitation services. Coverage is mandatory for most industries. 
        Claims must be reported within one year of the injury. Benefits include temporary wage replacement 
        at 90% of net earnings, permanent disability awards, and vocational rehabilitation.""",
        "citation": "RSBC 2019, c. 1",
        "section_number": "1",
        "jurisdiction": "british_columbia",
        "program": "workers_compensation",
        "effective_date": "2019-01-01",
        "doc_type": "act",
        "department": "WorkSafeBC"
    },
    {
        "id": "test-on-tenant-act",
        "title": "Residential Tenancies Act - Ontario",
        "content": """The Residential Tenancies Act governs rental housing in Ontario. It sets out rights 
        and responsibilities of landlords and tenants, including rules about rent increases, maintenance, 
        evictions, and dispute resolution. Landlords can only increase rent once every 12 months and must 
        give 90 days notice. The increase is capped at the provincial guideline (2.5% for 2024). Tenants 
        have the right to live in a property that is in good repair and meets health and safety standards. 
        Disputes are resolved by the Landlord and Tenant Board.""",
        "citation": "S.O. 2006, c. 17",
        "section_number": "1",
        "jurisdiction": "ontario",
        "program": "housing",
        "effective_date": "2006-01-31",
        "doc_type": "act",
        "department": "Ministry of Municipal Affairs and Housing"
    },
    {
        "id": "test-disability-benefits",
        "title": "Canada Pension Plan Disability Benefits",
        "content": """CPP Disability benefits provide financial assistance to people who have contributed 
        to the CPP and can no longer work regularly due to a disability. To qualify, you must be under 
        65, have made sufficient CPP contributions, and have a severe and prolonged disability that 
        prevents you from working at any job regularly. Medical evidence must show the disability is 
        both severe (prevents you from regularly working at any job) and prolonged (long-term or likely 
        to result in death). The benefit amount depends on your contributions to CPP.""",
        "citation": "R.S.C. 1985, c. C-8, s. 42",
        "section_number": "42",
        "jurisdiction": "federal",
        "program": "cpp_disability",
        "effective_date": "1966-01-01",
        "doc_type": "act",
        "department": "Employment and Social Development Canada"
    }
]


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_elasticsearch():
    """
    Session-level fixture to seed Elasticsearch with test data.
    Runs once before all tests, cleans up after all tests complete.
    """
    if not ES_AVAILABLE:
        yield
        return
    
    search_service = SearchService()
    
    # Create index if it doesn't exist
    try:
        search_service.create_index()
    except:
        pass  # Index may already exist
    
    # Index sample documents
    indexed_count = 0
    for doc in SAMPLE_REGULATIONS:
        try:
            result = search_service.index_document(doc)
            if result.get('result') in ['created', 'updated']:
                indexed_count += 1
        except Exception as e:
            print(f"Warning: Failed to index {doc['id']}: {e}")
    
    # Wait for indexing to complete
    try:
        search_service.es_client.indices.refresh(index=search_service.index_name)
        print(f"\n✓ Elasticsearch test data seeded: {indexed_count} documents")
    except Exception as e:
        print(f"\n⚠ Elasticsearch refresh failed: {e}")
    
    yield search_service
    
    # Cleanup is optional - you can comment this out to inspect test data
    # try:
    #     for doc in SAMPLE_REGULATIONS:
    #         search_service.es_client.delete(
    #             index=search_service.index_name,
    #             id=doc['id'],
    #             ignore=[404]
    #         )
    # except:
    #     pass


@pytest.fixture(scope="function")
def search_service():
    """Provide search service instance for tests"""
    return SearchService()


@pytest.fixture(scope="function")
def sample_documents():
    """Provide sample regulatory documents for tests"""
    return SAMPLE_REGULATIONS.copy()


@pytest.fixture(scope="session")
def db_session():
    """
    Provide a database session for tests.
    Creates tables if needed, provides session, rolls back after test.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = SessionLocal()
    
    yield session
    
    # Rollback and close
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def clean_db_session():
    """
    Provide a clean database session that rolls back after each test.
    Use this for tests that modify the database.
    """
    session = SessionLocal()
    
    yield session
    
    session.rollback()
    session.close()


# ============================================================================
# Utility Functions for Tests
# ============================================================================

def seed_test_data_to_elasticsearch(documents=None):
    """
    Manually seed test data to Elasticsearch.
    Use this in tests that need fresh data.
    
    Args:
        documents: List of documents to index (defaults to SAMPLE_REGULATIONS)
    
    Returns:
        SearchService instance
    """
    if documents is None:
        documents = SAMPLE_REGULATIONS
    
    search_service = SearchService()
    
    for doc in documents:
        try:
            search_service.index_document(doc)
        except Exception as e:
            print(f"Warning: Failed to index {doc['id']}: {e}")
    
    # Refresh to make documents searchable
    try:
        search_service.es_client.indices.refresh(index=search_service.index_name)
    except:
        pass
    
    return search_service


def clear_test_data_from_elasticsearch():
    """
    Clear all test documents from Elasticsearch.
    Use this to reset Elasticsearch state between tests.
    """
    search_service = SearchService()
    
    for doc in SAMPLE_REGULATIONS:
        try:
            search_service.es_client.delete(
                index=search_service.index_name,
                id=doc['id'],
                ignore=[404]
            )
        except:
            pass
    
    try:
        search_service.es_client.indices.refresh(index=search_service.index_name)
    except:
        pass


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """
    Pytest configuration hook.
    Runs before test collection.
    """
    # Register custom markers
    config.addinivalue_line(
        "markers", "asyncio: mark test as asyncio test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_db: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "requires_neo4j: mark test as requiring Neo4j"
    )
    
    # Print service availability
    print("\n" + "="*70)
    print("TEST ENVIRONMENT STATUS")
    print("="*70)
    print(f"Elasticsearch Available: {'✓' if ES_AVAILABLE else '✗'}")
    print(f"Gemini API Available: {'✓' if GEMINI_AVAILABLE else '✗'}")
    print("="*70 + "\n")


def pytest_collection_modifyitems(config, items):
    """
    Pytest hook to modify test collection.
    Automatically skip tests based on service availability.
    """
    # Skip tests that require services that aren't available
    for item in items:
        if "integration_search" in str(item.fspath) and not ES_AVAILABLE:
            item.add_marker(skip_if_no_es)
        
        if "integration_rag" in str(item.fspath) and not GEMINI_AVAILABLE:
            item.add_marker(skip_if_no_gemini)
        
        if "e2e_workflows" in str(item.fspath):
            if not ES_AVAILABLE:
                item.add_marker(skip_if_no_es)
            # Some E2E tests also require Gemini
            if "qa" in item.name.lower() or "comparison" in item.name.lower():
                if not GEMINI_AVAILABLE:
                    item.add_marker(skip_if_no_gemini)
