#!/usr/bin/env python3
"""
Test script for program detection in ingestion pipeline.
This script tests the program detector without needing actual XML files.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.program_mappings import ProgramDetector

def test_program_detection():
    """Test the program detector with various regulation titles."""
    
    detector = ProgramDetector()
    
    test_cases = [
        {
            'title': 'Employment Insurance Act',
            'content': 'Regulations governing employment insurance benefits and contributions for workers who lose their jobs.',
            'expected_programs': ['employment_insurance'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Canada Pension Plan Regulations',
            'content': 'Rules for CPP contributions, retirement benefits, and disability pensions.',
            'expected_programs': ['canada_pension_plan'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Immigration and Refugee Protection Act',
            'content': 'This Act governs immigration to Canada, including permanent residence, temporary residence, work permits, and refugee protection.',
            'expected_programs': ['immigration'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Income Tax Act',
            'content': 'Federal taxation of individuals and corporations, including tax credits, deductions, and rates.',
            'expected_programs': ['taxation'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Old Age Security Act',
            'content': 'Provisions for old age security pensions, guaranteed income supplement (GIS), and allowances for seniors.',
            'expected_programs': ['old_age_security'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Canada Labour Code',
            'content': 'Federal labour standards including minimum wage, working hours, overtime, and workplace safety.',
            'expected_programs': ['labour_standards'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Competition Act',
            'content': 'Consumer protection and competition law, regulating price fixing, mergers, and consumer rights.',
            'expected_programs': ['consumer_protection'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Canadian Environmental Protection Act',
            'content': 'Environmental protection, pollution control, and emissions regulations.',
            'expected_programs': ['environmental'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Criminal Code of Canada',
            'content': 'Federal criminal law including offences, prosecution, and sentencing guidelines.',
            'expected_programs': ['criminal_law'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Canada Health Act',
            'content': 'Federal health care legislation governing medicare, medical services, and hospital insurance.',
            'expected_programs': ['health_care'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Temporary Foreign Worker Program Regulations',
            'content': 'Regulations for temporary foreign workers, work permits, and employment authorization in Canada.',
            'expected_programs': ['immigration'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Employment Insurance (Fishing) Regulations',
            'content': 'Special EI provisions for fishing industry workers and seasonal employment.',
            'expected_programs': ['employment_insurance'],
            'expected_jurisdiction': 'federal'
        }
    ]
    
    print("=" * 80)
    print("PROGRAM DETECTION TEST SUITE")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"Test {i}: {test['title']}")
        print("-" * 80)
        
        # Detect programs
        detected_programs = detector.detect_programs(
            title=test['title'],
            content=test['content']
        )
        
        # Detect jurisdiction
        detected_jurisdiction = detector.detect_jurisdiction(
            title=test['title'],
            content=test['content']
        )
        
        # Check programs
        programs_match = set(detected_programs) == set(test['expected_programs'])
        programs_status = "✓ PASS" if programs_match else "✗ FAIL"
        
        # Check jurisdiction
        jurisdiction_match = detected_jurisdiction == test['expected_jurisdiction']
        jurisdiction_status = "✓ PASS" if jurisdiction_match else "✗ FAIL"
        
        print(f"  Content: {test['content'][:80]}...")
        print(f"  Detected Programs: {detected_programs}")
        print(f"  Expected Programs: {test['expected_programs']}")
        print(f"  Programs Test: {programs_status}")
        print(f"  Detected Jurisdiction: {detected_jurisdiction}")
        print(f"  Expected Jurisdiction: {test['expected_jurisdiction']}")
        print(f"  Jurisdiction Test: {jurisdiction_status}")
        
        if programs_match and jurisdiction_match:
            passed += 1
            print(f"  Overall: ✓ PASS")
        else:
            failed += 1
            print(f"  Overall: ✗ FAIL")
        
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("=" * 80)
    
    return passed, failed


def test_edge_cases():
    """Test edge cases and multiple program detection."""
    
    detector = ProgramDetector()
    
    print("\n" + "=" * 80)
    print("EDGE CASES AND MULTI-PROGRAM DETECTION")
    print("=" * 80)
    print()
    
    edge_cases = [
        {
            'title': 'Social Security Tribunal Regulations',
            'content': 'Regulations governing appeals related to Employment Insurance, Canada Pension Plan, and Old Age Security decisions.',
            'description': 'Multiple programs in one regulation'
        },
        {
            'title': 'Provincial Health Services Act',
            'content': 'Ontario provincial health care services and hospital regulations.',
            'description': 'Provincial jurisdiction'
        },
        {
            'title': 'City of Toronto Municipal Code',
            'content': 'Municipal by-laws governing local services and regulations.',
            'description': 'Municipal jurisdiction'
        },
        {
            'title': 'Generic Regulation XYZ',
            'content': 'Some generic content without specific keywords.',
            'description': 'No clear program match'
        }
    ]
    
    for i, test in enumerate(edge_cases, 1):
        print(f"Edge Case {i}: {test['description']}")
        print(f"  Title: {test['title']}")
        print(f"  Content: {test['content'][:60]}...")
        
        programs = detector.detect_programs(test['title'], test['content'])
        jurisdiction = detector.detect_jurisdiction(test['title'], test['content'])
        
        print(f"  Detected Programs: {programs if programs else 'None'}")
        print(f"  Detected Jurisdiction: {jurisdiction}")
        print()
    
    print("=" * 80)


if __name__ == '__main__':
    passed, failed = test_program_detection()
    test_edge_cases()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)
