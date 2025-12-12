"""
Legal Term Synonym Dictionary for Query Expansion

This module provides synonym mappings for legal terms, programs, and concepts
to improve search recall. Used in Tier 2 of the multi-tier RAG search to
expand queries when initial searches fail.

Features:
- Bilingual synonyms (English/French)
- Program name variations (EI, CPP, OAS, etc.)
- Legal terminology alternatives
- Action verbs and their synonyms

Author: Developer 2 (AI/ML Engineer)
Created: 2025-12-12
"""

from typing import Dict, List, Set
import re


# =============================================================================
# PROGRAM SYNONYMS
# =============================================================================

PROGRAM_SYNONYMS = {
    # Employment Insurance
    'employment insurance': ['ei', 'unemployment insurance', 'unemployment benefits', 
                            'assurance-emploi', 'ae', 'chomage'],
    'ei': ['employment insurance', 'unemployment insurance', 'assurance-emploi'],
    
    # Canada Pension Plan
    'canada pension plan': ['cpp', 'canadian pension', 'pension plan', 
                           'régime de pensions du canada', 'rpc'],
    'cpp': ['canada pension plan', 'canadian pension', 'régime de pensions du canada'],
    
    # Old Age Security
    'old age security': ['oas', 'seniors pension', 'elderly pension', 
                        'sécurité de la vieillesse', 'sv'],
    'oas': ['old age security', 'seniors pension', 'sécurité de la vieillesse'],
    
    # Guaranteed Income Supplement
    'guaranteed income supplement': ['gis', 'income supplement', 'supplement de revenu garanti', 'srg'],
    'gis': ['guaranteed income supplement', 'income supplement', 'supplement de revenu garanti'],
    
    # Social Insurance Number
    'social insurance number': ['sin', 'insurance number', 'numéro d\'assurance sociale', 'nas'],
    'sin': ['social insurance number', 'numéro d\'assurance sociale'],
}


# =============================================================================
# LEGAL TERMINOLOGY
# =============================================================================

LEGAL_TERM_SYNONYMS = {
    # Benefits and entitlements
    'benefit': ['payment', 'assistance', 'support', 'entitlement', 'allowance', 
               'prestation', 'aide'],
    'benefits': ['payments', 'assistance', 'support', 'entitlements', 'allowances'],
    'payment': ['benefit', 'disbursement', 'compensation', 'paiement'],
    
    # Eligibility
    'eligible': ['qualify', 'entitled', 'admissible', 'qualified', 'admissible'],
    'eligibility': ['qualification', 'entitlement', 'admissibility', 'admissibilité'],
    'qualify': ['eligible', 'entitled', 'meet requirements', 'admissible'],
    
    # Regulations and laws
    'regulation': ['act', 'law', 'statute', 'legislation', 'règlement', 'loi'],
    'act': ['regulation', 'law', 'statute', 'legislation', 'loi'],
    'law': ['regulation', 'act', 'statute', 'legislation', 'loi'],
    'statute': ['regulation', 'act', 'law', 'legislation', 'loi'],
    'legislation': ['regulation', 'act', 'law', 'statute', 'législation'],
    
    # Requirements
    'requirement': ['prerequisite', 'condition', 'criterion', 'exigence'],
    'requirements': ['prerequisites', 'conditions', 'criteria', 'exigences'],
    'condition': ['requirement', 'prerequisite', 'stipulation', 'condition'],
    
    # Applications
    'apply': ['申请', 'demander', 'submit application', 'file', 'faire une demande'],
    'application': ['request', 'claim', 'submission', 'demande'],
    'claim': ['file claim', 'submit claim', 'application', 'réclamation'],
    
    # Work and employment
    'work': ['employment', 'job', 'occupation', 'travail'],
    'employment': ['work', 'job', 'occupation', 'emploi'],
    'worker': ['employee', 'employed person', 'travailleur'],
    'employee': ['worker', 'employed person', 'employé'],
    'employer': ['company', 'business', 'organization', 'employeur'],
}


# =============================================================================
# PERSON TYPE SYNONYMS
# =============================================================================

PERSON_TYPE_SYNONYMS = {
    # Seniors
    'senior': ['elderly', 'retiree', 'pensioner', 'older adult', 'aîné', 'personne âgée'],
    'elderly': ['senior', 'retiree', 'pensioner', 'older adult', 'âgé'],
    'retiree': ['senior', 'pensioner', 'retired person', 'retraité'],
    
    # Workers
    'worker': ['employee', 'employed person', 'staff', 'travailleur'],
    'employee': ['worker', 'staff member', 'employé'],
    
    # Residents
    'resident': ['inhabitant', 'domiciled person', 'résident'],
    'permanent resident': ['pr', 'landed immigrant', 'résident permanent'],
    'temporary resident': ['temporary worker', 'foreign worker', 'résident temporaire'],
    
    # Citizens
    'citizen': ['canadian citizen', 'national', 'citoyen'],
    'canadian': ['citizen', 'canadian citizen', 'canadien'],
    
    # Families
    'family': ['household', 'dependents', 'relatives', 'famille'],
    'spouse': ['partner', 'husband', 'wife', 'conjoint'],
    'child': ['dependent', 'minor', 'offspring', 'enfant'],
}


# =============================================================================
# ACTION VERB SYNONYMS
# =============================================================================

ACTION_SYNONYMS = {
    # Applying
    'apply': ['申请', 'demander', 'submit', 'file', 'request', 'faire une demande'],
    'submit': ['apply', 'file', 'send', 'soumettre'],
    'file': ['submit', 'lodge', 'apply', 'déposer'],
    
    # Receiving
    'receive': ['get', 'obtain', 'collect', 'recevoir'],
    'get': ['receive', 'obtain', 'acquire', 'obtenir'],
    
    # Qualifying
    'qualify': ['be eligible', 'meet requirements', 'be entitled', 'être admissible'],
    'entitled': ['eligible', 'qualified', 'have right to', 'avoir droit'],
}


# =============================================================================
# QUERY EXPANSION FUNCTIONS
# =============================================================================

def expand_query_with_synonyms(query: str, max_expansions: int = 3) -> str:
    """
    Expand a query with synonyms to improve search recall.
    
    This function:
    1. Identifies key terms in the query
    2. Adds top synonyms for each term
    3. Returns expanded query without over-expanding
    
    Args:
        query: Original search query
        max_expansions: Maximum number of synonyms per term (default: 3)
    
    Returns:
        Expanded query string
    """
    # Normalize query
    query_lower = query.lower()
    query_words = query_lower.split()
    
    # Collect all synonym dictionaries
    all_synonyms = {
        **PROGRAM_SYNONYMS,
        **LEGAL_TERM_SYNONYMS,
        **PERSON_TYPE_SYNONYMS,
        **ACTION_SYNONYMS
    }
    
    # Find matching terms and their synonyms
    expanded_terms = []
    expanded_terms.append(query)  # Keep original query
    
    for term, synonyms in all_synonyms.items():
        # Check if term appears in query
        if term in query_lower:
            # Add top synonyms (limit to avoid over-expansion)
            for synonym in synonyms[:max_expansions]:
                if synonym not in query_lower:  # Don't duplicate
                    expanded_terms.append(synonym)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_terms = []
    for term in expanded_terms:
        if term.lower() not in seen:
            seen.add(term.lower())
            unique_terms.append(term)
    
    # Join with OR (for some search engines) or space (for others)
    # Using space for Elasticsearch compatibility
    expanded_query = ' '.join(unique_terms[:10])  # Limit total terms
    
    return expanded_query


def get_synonyms_for_term(term: str) -> List[str]:
    """
    Get all synonyms for a specific term.
    
    Args:
        term: Term to find synonyms for
    
    Returns:
        List of synonyms (empty if no synonyms found)
    """
    term_lower = term.lower()
    
    # Collect all synonym dictionaries
    all_synonyms = {
        **PROGRAM_SYNONYMS,
        **LEGAL_TERM_SYNONYMS,
        **PERSON_TYPE_SYNONYMS,
        **ACTION_SYNONYMS
    }
    
    return all_synonyms.get(term_lower, [])


def detect_program_from_query(query: str) -> List[str]:
    """
    Detect which government programs are mentioned in a query.
    
    This function aligns with program_mappings.py and returns the exact
    program IDs used throughout the system.
    
    Args:
        query: User query
    
    Returns:
        List of detected program identifiers matching program_mappings.py
    """
    query_lower = query.lower()
    detected_programs = []
    
    # Check for EI/Employment Insurance
    if any(term in query_lower for term in ['ei', 'employment insurance', 'unemployment', 'assurance-emploi', 'chomage', 'job loss']):
        detected_programs.append('employment_insurance')
    
    # Check for CPP (Canada Pension Plan)
    if any(term in query_lower for term in ['cpp', 'canada pension plan', 'canadian pension', 'régime de pensions', 'retirement pension', 'disability pension']):
        detected_programs.append('canada_pension_plan')
    
    # Check for OAS (Old Age Security)
    if any(term in query_lower for term in ['oas', 'old age security', 'seniors pension', 'sécurité de la vieillesse']):
        detected_programs.append('old_age_security')
    
    # Check for Immigration
    if any(term in query_lower for term in ['immigration', 'refugee', 'permanent resident', 'temporary resident', 'visa', 'work permit', 'study permit', 'citizenship']):
        detected_programs.append('immigration')
    
    # Check for Taxation
    if any(term in query_lower for term in ['income tax', 'tax', 'taxation', 'tax credit', 'tax deduction', 'gst', 'hst', 'excise']):
        detected_programs.append('taxation')
    
    # Check for Health Care
    if any(term in query_lower for term in ['health care', 'healthcare', 'medical', 'hospital', 'health insurance', 'medicare']):
        detected_programs.append('health_care')
    
    # Check for Labour Standards
    if any(term in query_lower for term in ['labour', 'labor', 'employment standards', 'workplace safety', 'minimum wage', 'working hours', 'overtime']):
        detected_programs.append('labour_standards')
    
    # Check for Consumer Protection
    if any(term in query_lower for term in ['consumer protection', 'competition act', 'consumer rights', 'price fixing']):
        detected_programs.append('consumer_protection')
    
    # Check for Environmental
    if any(term in query_lower for term in ['environmental', 'pollution', 'emissions', 'environmental assessment', 'species at risk']):
        detected_programs.append('environmental')
    
    # Check for Criminal Law
    if any(term in query_lower for term in ['criminal code', 'criminal law', 'offence', 'prosecution', 'sentencing']):
        detected_programs.append('criminal_law')
    
    return detected_programs


def normalize_legal_term(term: str) -> str:
    """
    Normalize a legal term to its canonical form.
    
    Maps various term variations to the exact program IDs used in program_mappings.py
    
    Args:
        term: Term to normalize
    
    Returns:
        Canonical form of the term (matching program_mappings.py)
    """
    term_lower = term.lower()
    
    # Program name normalization (must match program_mappings.py exactly)
    if term_lower in ['ei', 'unemployment insurance', 'assurance-emploi', 'unemployment']:
        return 'employment_insurance'
    elif term_lower in ['cpp', 'canadian pension', 'régime de pensions du canada', 'pension plan']:
        return 'canada_pension_plan'
    elif term_lower in ['oas', 'seniors pension', 'sécurité de la vieillesse', 'elderly pension']:
        return 'old_age_security'
    elif term_lower in ['immigration', 'refugee', 'citizenship']:
        return 'immigration'
    elif term_lower in ['tax', 'taxation', 'income tax']:
        return 'taxation'
    elif term_lower in ['health care', 'healthcare', 'medical', 'medicare']:
        return 'health_care'
    elif term_lower in ['labour', 'labor', 'employment standards']:
        return 'labour_standards'
    elif term_lower in ['consumer', 'consumer protection']:
        return 'consumer_protection'
    elif term_lower in ['environmental', 'environment']:
        return 'environmental'
    elif term_lower in ['criminal', 'criminal law', 'criminal code']:
        return 'criminal_law'
    
    # Return original if no normalization applies
    return term


# =============================================================================
# BILINGUAL TERM MAPPING
# =============================================================================

ENGLISH_TO_FRENCH = {
    'employment insurance': 'assurance-emploi',
    'canada pension plan': 'régime de pensions du canada',
    'old age security': 'sécurité de la vieillesse',
    'guaranteed income supplement': 'supplément de revenu garanti',
    'social insurance number': 'numéro d\'assurance sociale',
    'benefit': 'prestation',
    'benefits': 'prestations',
    'eligibility': 'admissibilité',
    'eligible': 'admissible',
    'requirement': 'exigence',
    'requirements': 'exigences',
    'application': 'demande',
    'apply': 'faire une demande',
    'worker': 'travailleur',
    'employee': 'employé',
    'employer': 'employeur',
    'senior': 'aîné',
    'elderly': 'personne âgée',
    'citizen': 'citoyen',
    'resident': 'résident',
    'family': 'famille',
    'spouse': 'conjoint',
    'child': 'enfant',
}

FRENCH_TO_ENGLISH = {v: k for k, v in ENGLISH_TO_FRENCH.items()}


def translate_term(term: str, to_language: str = 'fr') -> str:
    """
    Translate a legal term between English and French.
    
    Args:
        term: Term to translate
        to_language: Target language ('en' or 'fr')
    
    Returns:
        Translated term (or original if no translation found)
    """
    term_lower = term.lower()
    
    if to_language == 'fr':
        return ENGLISH_TO_FRENCH.get(term_lower, term)
    else:
        return FRENCH_TO_ENGLISH.get(term_lower, term)


# =============================================================================
# TEST CODE
# =============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Legal Synonyms Dictionary - Test")
    print("=" * 80)
    
    # Test query expansion
    print("\n1. Query Expansion Test:")
    test_queries = [
        "employment insurance eligibility",
        "Can seniors apply for OAS?",
        "What are the requirements for CPP?",
        "temporary resident work permit"
    ]
    
    for query in test_queries:
        expanded = expand_query_with_synonyms(query, max_expansions=2)
        print(f"\n   Original: {query}")
        print(f"   Expanded: {expanded[:100]}...")
    
    # Test synonym lookup
    print("\n\n2. Synonym Lookup Test:")
    test_terms = ['benefit', 'eligible', 'worker', 'senior']
    
    for term in test_terms:
        synonyms = get_synonyms_for_term(term)
        print(f"\n   '{term}' → {synonyms[:5]}")
    
    # Test program detection
    print("\n\n3. Program Detection Test:")
    test_queries = [
        "How do I apply for EI?",
        "Canada Pension Plan benefits",
        "OAS and GIS eligibility"
    ]
    
    for query in test_queries:
        programs = detect_program_from_query(query)
        print(f"\n   Query: {query}")
        print(f"   Programs: {programs}")
    
    # Test bilingual translation
    print("\n\n4. Translation Test:")
    test_terms = ['employment insurance', 'benefit', 'eligibility']
    
    for term in test_terms:
        french = translate_term(term, 'fr')
        print(f"\n   EN: {term} → FR: {french}")
    
    print("\n" + "=" * 80)
    print("Test complete!")
