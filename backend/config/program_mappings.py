"""
Program and Jurisdiction Detection Mappings

This module provides keyword-based detection of government programs
and jurisdictions from regulatory document titles and content.
"""

from typing import Dict, List, Optional, Set
import re


# Federal programs mapped to their keywords
FEDERAL_PROGRAMS = {
    'employment_insurance': {
        'keywords': [
            'employment insurance',
            'ei benefits',
            'ei act',
            'ei regulations',
            'unemployment',
            'job loss',
            'ei premium',
            'ei contribution'
        ],
        'patterns': [
            r'\bemployment\s+insurance\b',
            r'\b\s*e\s*\.?\s*i\s*\.?\s*\b',
            r'\bunemployment\s+benefits?\b'
        ]
    },
    'canada_pension_plan': {
        'keywords': [
            'canada pension plan',
            'cpp',
            'retirement pension',
            'disability pension',
            'survivor pension',
            'cpp contribution'
        ],
        'patterns': [
            r'\bcanada\s+pension\s+plan\b',
            r'\bc\s*\.?\s*p\s*\.?\s*p\s*\.?\b',
            r'\bpension\s+plan\b'
        ]
    },
    'old_age_security': {
        'keywords': [
            'old age security',
            'oas',
            'guaranteed income supplement',
            'gis',
            'allowance for the survivor'
        ],
        'patterns': [
            r'\bold\s+age\s+security\b',
            r'\bo\s*\.?\s*a\s*\.?\s*s\s*\.?\b',
            r'\bguaranteed\s+income\s+supplement\b'
        ]
    },
    'immigration': {
        'keywords': [
            'immigration',
            'refugee',
            'permanent resident',
            'temporary resident',
            'visa',
            'work permit',
            'study permit',
            'citizenship',
            'naturalization'
        ],
        'patterns': [
            r'\bimmigration\b',
            r'\brefugee\b',
            r'\bpermanent\s+resident',
            r'\btemporary\s+resident',
            r'\bcitizenship\b'
        ]
    },
    'taxation': {
        'keywords': [
            'income tax',
            'tax act',
            'taxation',
            'tax credit',
            'tax deduction',
            'gst',
            'hst',
            'excise tax'
        ],
        'patterns': [
            r'\bincome\s+tax\b',
            r'\btax\s+act\b',
            r'\btaxation\b',
            r'\b[gh]st\b'
        ]
    },
    'health_care': {
        'keywords': [
            'health care',
            'medical services',
            'hospital',
            'health insurance',
            'drug benefits',
            'medicare'
        ],
        'patterns': [
            r'\bhealth\s+care\b',
            r'\bmedical\s+services\b',
            r'\bmedicare\b'
        ]
    },
    'labour_standards': {
        'keywords': [
            'labour code',
            'labor code',
            'employment standards',
            'workplace safety',
            'minimum wage',
            'working hours',
            'overtime'
        ],
        'patterns': [
            r'\blabou?r\s+code\b',
            r'\bemployment\s+standards\b',
            r'\bworkplace\s+safety\b'
        ]
    },
    'consumer_protection': {
        'keywords': [
            'consumer protection',
            'competition act',
            'price fixing',
            'consumer rights'
        ],
        'patterns': [
            r'\bconsumer\s+protection\b',
            r'\bcompetition\s+act\b'
        ]
    },
    'environmental': {
        'keywords': [
            'environmental protection',
            'pollution',
            'emissions',
            'environmental assessment',
            'species at risk'
        ],
        'patterns': [
            r'\benvironmental\b',
            r'\bpollution\b',
            r'\bemissions\b'
        ]
    },
    'criminal_law': {
        'keywords': [
            'criminal code',
            'criminal law',
            'offence',
            'prosecution',
            'sentencing'
        ],
        'patterns': [
            r'\bcriminal\s+code\b',
            r'\bcriminal\s+law\b'
        ]
    }
}


# Jurisdiction detection
JURISDICTION_KEYWORDS = {
    'federal': [
        'canada',
        'federal',
        'parliament of canada',
        'governor in council',
        'minister of',
        'statute of canada',
        's.c.',
        'r.s.c.'
    ],
    'provincial': [
        'ontario',
        'quebec',
        'british columbia',
        'alberta',
        'manitoba',
        'saskatchewan',
        'nova scotia',
        'new brunswick',
        'prince edward island',
        'newfoundland',
        'labrador',
        'provincial',
        'legislature'
    ],
    'municipal': [
        'municipal',
        'city',
        'town',
        'borough',
        'municipality',
        'by-law',
        'bylaw'
    ]
}


class ProgramDetector:
    """Detects government programs and jurisdictions from document metadata."""
    
    def __init__(self):
        """Initialize the detector with compiled patterns."""
        self.program_patterns = {}
        
        # Compile regex patterns for efficiency
        for program, config in FEDERAL_PROGRAMS.items():
            self.program_patterns[program] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in config['patterns']
            ]
    
    def detect_programs(self, title: str, content: str = "", max_programs: int = 3) -> List[str]:
        """
        Detect applicable government programs from document text.
        
        Args:
            title: Document title
            content: Document content (optional, first 1000 chars used)
            max_programs: Maximum number of programs to return
            
        Returns:
            List of detected program IDs
        """
        # Combine title and beginning of content for detection
        search_text = f"{title} {content[:1000]}".lower()
        
        detected = []
        scores = {}
        
        for program, config in FEDERAL_PROGRAMS.items():
            score = 0
            
            # Check keywords
            for keyword in config['keywords']:
                if keyword.lower() in search_text:
                    score += 1
            
            # Check regex patterns (higher weight)
            for pattern in self.program_patterns[program]:
                if pattern.search(search_text):
                    score += 3
            
            if score > 0:
                scores[program] = score
        
        # Sort by score and return top programs
        sorted_programs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        detected = [program for program, score in sorted_programs[:max_programs]]
        
        return detected
    
    def detect_jurisdiction(self, title: str, content: str = "", authority: str = "") -> str:
        """
        Detect jurisdiction from document metadata.
        
        Args:
            title: Document title
            content: Document content (optional)
            authority: Authority/citation field
            
        Returns:
            Jurisdiction: 'federal', 'provincial', or 'municipal'
        """
        # Combine all text for detection
        search_text = f"{title} {content[:500]} {authority}".lower()
        
        # Check for each jurisdiction
        jurisdiction_scores = {}
        
        for jurisdiction, keywords in JURISDICTION_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword.lower() in search_text)
            if score > 0:
                jurisdiction_scores[jurisdiction] = score
        
        # Default to federal if unclear
        if not jurisdiction_scores:
            return 'federal'
        
        # Return jurisdiction with highest score
        return max(jurisdiction_scores, key=jurisdiction_scores.get)


# Singleton instance
_detector = None


def get_program_detector() -> ProgramDetector:
    """Get or create singleton program detector."""
    global _detector
    if _detector is None:
        _detector = ProgramDetector()
    return _detector


if __name__ == "__main__":
    # Test the detector
    detector = ProgramDetector()
    
    test_cases = [
        {
            'title': 'Employment Insurance Act',
            'content': 'Regulations governing employment insurance benefits...',
            'expected_programs': ['employment_insurance'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Canada Pension Plan Regulations',
            'content': 'Rules for CPP contributions and retirement benefits',
            'expected_programs': ['canada_pension_plan'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Immigration and Refugee Protection Act',
            'content': 'Governs immigration to Canada and refugee claims',
            'expected_programs': ['immigration'],
            'expected_jurisdiction': 'federal'
        },
        {
            'title': 'Income Tax Act',
            'content': 'Federal taxation of individuals and corporations',
            'expected_programs': ['taxation'],
            'expected_jurisdiction': 'federal'
        }
    ]
    
    print("Testing Program Detector")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['title']}")
        
        programs = detector.detect_programs(test['title'], test['content'])
        jurisdiction = detector.detect_jurisdiction(test['title'], test['content'])
        
        print(f"  Detected programs: {programs}")
        print(f"  Expected: {test['expected_programs']}")
        print(f"  Match: {'✓' if programs == test['expected_programs'] else '✗'}")
        
        print(f"  Detected jurisdiction: {jurisdiction}")
        print(f"  Expected: {test['expected_jurisdiction']}")
        print(f"  Match: {'✓' if jurisdiction == test['expected_jurisdiction'] else '✗'}")
    
    print("\n" + "=" * 60)
    print("Testing complete!")
