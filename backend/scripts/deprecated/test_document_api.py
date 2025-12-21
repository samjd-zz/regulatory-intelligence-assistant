#!/usr/bin/env python3
"""
Test script for the Document Parser and Ingestion system.

This script creates sample documents and tests all API endpoints.
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


def create_sample_text_document(filename: str, content: str) -> Path:
    """Create a sample text file for testing."""
    filepath = Path(f"/tmp/{filename}")
    filepath.write_text(content)
    return filepath


def test_upload_document():
    """Test document upload endpoint."""
    print("\n" + "="*60)
    print("TEST: Upload Document")
    print("="*60)
    
    # Create a sample regulation text
    sample_text = """
EMPLOYMENT INSURANCE ACT

S.C. 1996, c. 23

PART I - UNEMPLOYMENT BENEFITS

Section 1 - Definitions

In this Act:

"benefit period" means the period determined in accordance with section 10;
"benefits" means benefits payable under this Part;
"claimant" means a person who has made an initial claim for benefits;

Section 2 - Purpose

The purpose of this Act is to provide:
(a) income support to unemployed workers;
(b) employment assistance programs;
(c) support for families with children.

Section 3 - Establishment of Account

(1) There shall be established in the accounts of Canada an account to be known as the Employment Insurance Account.

(2) The Account shall be credited with all amounts received under this Act.

Section 4 - Administration

The Commission shall administer this Act.

PART II - ELIGIBILITY

Section 5 - General Requirements

To qualify for benefits, a person must:
(a) have paid premiums;
(b) have sufficient hours of work; and
(c) be available for work.

Section 6 - Hours Requirement

(1) A claimant must have at least 420 hours of insurable employment.

(2) In regions of high unemployment, the requirement in subsection (1) may be reduced.

Section 7 - Benefit Period

(1) A benefit period begins on the Sunday of the week in which the interruption of earnings occurs.

(2) Subject to section 10, a benefit period lasts for 52 weeks.

Section 8 - Waiting Period

(1) A one-week waiting period is required before benefits are payable.

(2) The waiting period begins with the first week for which benefits would otherwise be payable.

Section 9 - Disqualifications

A claimant is disqualified from receiving benefits if the claimant:
(a) lost employment by reason of misconduct;
(b) voluntarily left employment without just cause; or
(c) refused suitable employment.

See Section 10 for the duration of benefit periods.
See Section 5 for general requirements.
As defined in Section 1, "claimant" means a person who has made an initial claim.
Pursuant to Section 4, the Commission administers this Act.
"""
    
    filepath = create_sample_text_document("employment_insurance_act.txt", sample_text)
    
    try:
        url = f"{BASE_URL}/documents/upload"
        
        with open(filepath, "rb") as f:
            files = {"file": f}
            data = {
                "document_type": "legislation",
                "jurisdiction": "federal",
                "authority": "Parliament of Canada",
                "document_number": "S.C. 1996, c. 23",
                "effective_date": "1996-06-30"
            }
            
            response = requests.post(url, files=files, data=data)
            response.raise_for_status()
            
            result = response.json()
            print("✅ Document uploaded successfully!")
            print(f"Document ID: {result['id']}")
            print(f"Title: {result['title']}")
            print(f"Sections: {result['total_sections']}")
            print(f"Cross-references: {result['total_cross_references']}")
            
            return result['id']
            
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None
    finally:
        # Cleanup
        if filepath.exists():
            filepath.unlink()


def test_get_document(document_id: str):
    """Test get document endpoint."""
    print("\n" + "="*60)
    print("TEST: Get Document Details")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/documents/{document_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        doc = response.json()
        print("✅ Document retrieved!")
        print(f"Title: {doc['title']}")
        print(f"Type: {doc['document_type']}")
        print(f"Jurisdiction: {doc['jurisdiction']}")
        print(f"Status: {doc['status']}")
        print(f"Processed: {doc['is_processed']}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")


def test_get_sections(document_id: str):
    """Test get document sections endpoint."""
    print("\n" + "="*60)
    print("TEST: Get Document Sections")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/documents/{document_id}/sections"
        response = requests.get(url)
        response.raise_for_status()
        
        sections = response.json()
        print(f"✅ Retrieved {len(sections)} sections!")
        
        print("\nFirst 5 sections:")
        for section in sections[:5]:
            indent = "  " * section['level']
            print(f"{indent}- {section['section_number']}: {section['section_title'][:50]}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")


def test_get_cross_references(document_id: str):
    """Test get cross-references endpoint."""
    print("\n" + "="*60)
    print("TEST: Get Cross-References")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/documents/{document_id}/cross-references"
        response = requests.get(url)
        response.raise_for_status()
        
        refs = response.json()
        print(f"✅ Retrieved {len(refs)} cross-references!")
        
        print("\nSample cross-references:")
        for ref in refs[:5]:
            print(f"  - {ref['source_location']} → {ref['target_location']}")
            print(f"    Type: {ref['reference_type']}")
            print(f"    Citation: {ref['citation_text'][:60]}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")


def test_search_documents():
    """Test document search endpoint."""
    print("\n" + "="*60)
    print("TEST: Search Documents")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/documents/search"
        payload = {
            "query": "employment insurance",
            "document_type": "legislation",
            "jurisdiction": "federal"
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        results = response.json()
        print(f"✅ Found {len(results)} documents!")
        
        for doc in results:
            print(f"  - {doc['title']} ({doc['document_number']})")
        
    except Exception as e:
        print(f"❌ Failed: {e}")


def test_list_documents():
    """Test list documents endpoint."""
    print("\n" + "="*60)
    print("TEST: List Documents")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/documents"
        params = {
            "document_type": "legislation",
            "skip": 0,
            "limit": 10
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        docs = response.json()
        print(f"✅ Listed {len(docs)} documents!")
        
        for doc in docs:
            print(f"  - {doc['title']}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")


def test_statistics():
    """Test statistics endpoint."""
    print("\n" + "="*60)
    print("TEST: Get Statistics")
    print("="*60)
    
    try:
        url = f"{BASE_URL}/documents/statistics/summary"
        response = requests.get(url)
        response.raise_for_status()
        
        stats = response.json()
        print("✅ Statistics retrieved!")
        print(f"Total documents: {stats['total_documents']}")
        print(f"Total sections: {stats['total_sections']}")
        print(f"\nBy type: {json.dumps(stats['by_type'], indent=2)}")
        print(f"By jurisdiction: {json.dumps(stats['by_jurisdiction'], indent=2)}")
        print(f"By status: {json.dumps(stats['by_status'], indent=2)}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")


def test_health_check():
    """Test if API is running."""
    print("\n" + "="*60)
    print("TEST: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        print("✅ API is running!")
    except Exception as e:
        print(f"❌ API is not accessible: {e}")
        print("\nMake sure to start the API server:")
        print("  cd backend")
        print("  uvicorn main:app --reload --port 8000")
        sys.exit(1)


def main():
    """Run all tests."""
    print("\n" + "#"*60)
    print("# Document Parser & Ingestion System - Test Suite")
    print("#"*60)
    
    # Check if API is running
    test_health_check()
    
    # Run tests
    document_id = test_upload_document()
    
    if document_id:
        test_get_document(document_id)
        test_get_sections(document_id)
        test_get_cross_references(document_id)
        test_search_documents()
        test_list_documents()
        test_statistics()
    
    print("\n" + "#"*60)
    print("# Test Suite Complete!")
    print("#"*60)
    print("\nNext steps:")
    print("1. Check the API docs: http://localhost:8000/docs")
    print("2. View uploaded documents in the database")
    print("3. Try uploading PDF/HTML/XML files")
    print("4. Explore cross-references and search functionality")


if __name__ == "__main__":
    main()
