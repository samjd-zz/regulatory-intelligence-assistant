"""
Query Parser Service - Natural Language Query Understanding for Legal Questions

This module provides query parsing and intent classification for regulatory questions,
including:
- Intent classification (search, compliance, interpretation)
- Entity extraction from queries
- Query normalization and understanding
- Context extraction
- Confidence scoring

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# Handle both relative and absolute imports
try:
    from .legal_nlp import LegalEntityExtractor, ExtractedEntity, EntityType
except ImportError:
    from legal_nlp import LegalEntityExtractor, ExtractedEntity, EntityType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Types of user intents for regulatory queries"""
    SEARCH = "search"  # Finding relevant regulations
    COMPLIANCE = "compliance"  # Checking if something meets requirements
    INTERPRETATION = "interpretation"  # Understanding what a regulation means
    ELIGIBILITY = "eligibility"  # Checking if someone qualifies for something
    PROCEDURE = "procedure"  # How to do something
    DEFINITION = "definition"  # What does a term mean
    COMPARISON = "comparison"  # Comparing regulations or options
    STATISTICS = "statistics"  # Asking about counts, totals, numbers, statistics
    GRAPH_RELATIONSHIP = "graph_relationship"  # Relationship/citation queries
    UNKNOWN = "unknown"  # Cannot determine intent


@dataclass
class ParsedQuery:
    """
    Represents a parsed user query with extracted information.
    """
    original_query: str  # Original user query
    normalized_query: str  # Cleaned/normalized query
    intent: QueryIntent  # Classified intent
    intent_confidence: float  # Confidence in intent classification
    entities: List[ExtractedEntity]  # Extracted entities
    keywords: List[str]  # Important keywords
    question_type: Optional[str] = None  # Type of question (who, what, when, where, why, how)
    filters: Dict[str, any] = field(default_factory=dict)  # Extracted filters (jurisdiction, date, etc.)
    context: Optional[str] = None  # Additional context
    metadata: Dict = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "original_query": self.original_query,
            "normalized_query": self.normalized_query,
            "intent": self.intent.value,
            "intent_confidence": self.intent_confidence,
            "entities": [e.to_dict() for e in self.entities],
            "keywords": self.keywords,
            "question_type": self.question_type,
            "filters": self.filters,
            "context": self.context,
            "metadata": self.metadata
        }

    def get_entities_by_type(self, entity_type: EntityType) -> List[ExtractedEntity]:
        """Get all entities of a specific type"""
        return [e for e in self.entities if e.entity_type == entity_type]


class LegalQueryParser:
    """
    Parse and understand natural language queries about regulations.

    This class combines pattern matching, entity extraction, and classification
    to understand user queries and extract structured information.
    """

    # Intent classification patterns
    INTENT_PATTERNS = {
        QueryIntent.GRAPH_RELATIONSHIP: [
            r'\b(has section|contains section|section)\b',
            r'\b(part of|belongs to|included in)\b',
            r'\b(references?|cites?|cited by|referenced by|mentions?|mentioned by|refers? to)\b',
            r'\b(relevant for|relevant to|pertains to)\b',
            r'\b(applies to|applicable to)\b',
            r'\b(implements?|enforces?)\b',
            r'\b(amends?|amended by|modifies?|modified by)\b',
            r'\b(what (laws|regulations|acts|sections|amendments) (reference|cite|amend|implement|mention|enforce|modify|apply|relate|contain|belong|implement|pertain|enforce|modify))\b',
            r'\b(relationship[s]? between|how is.*related to)\b',
        ],
        QueryIntent.SEARCH: [
            r'\b(find|search|look for|locate|show me|list)\b',
            r'\b(what are|which|where can i find)\b',
            r'\b(regulations? about|rules? about|laws? about)\b',
        ],
        QueryIntent.COMPLIANCE: [
            r'\b(comply|compliance|compliant|meet requirements?|satisfy)\b',
            r'\b(am i allowed|can i|is it legal|is it permitted)\b',
            r'\b(do i need to|must i|required to|have to)\b',
            r'\b(check|verify|validate|confirm)\b.*\b(application|form|submission)\b',
        ],
        QueryIntent.INTERPRETATION: [
            r'\b(what does.*mean|meaning of|interpret|explain|clarify)\b',
            r'\b(how to understand|how should i read)\b',
            r'\b(what is meant by)\b',
        ],
        QueryIntent.ELIGIBILITY: [
            r'\b(eligible|eligibility|qualify|qualifies)\b',
            r'\b(can.*apply|may.*apply|able to apply)\b',
            r'\b(am i eligible|who is eligible|who can)\b',
            r'\b(do i qualify|does.*qualify)\b',
        ],
        QueryIntent.PROCEDURE: [
            r'\b(how do i|how to|how can i|what are the steps)\b',
            r'\b(process for|procedure for|way to)\b',
            r'\b(apply for|submit|file|register)\b',
        ],
        QueryIntent.DEFINITION: [
            r'\b(what is|what are|define|definition of)\b',
            r'\b(who is considered|what counts as)\b',
        ],
        QueryIntent.COMPARISON: [
            r'\b(compare|comparison|difference between|versus|vs)\b',
            r'\b(which is better|which should i|or)\b',
            r'\b(what\'s the difference)\b',
        ],
        QueryIntent.STATISTICS: [
            r'\b(how many|how much|count|total|number of|amount of)\b',
            r'\b(statistics|stats|metrics|data about)\b',
            r'\b(quantity|volume|size)\b.*\b(database|system|collection)\b',
            r'\b(access to|have|contain|includes?)\b.*\b(how many|count|total|number)\b',
            r'\b(total number|total count|total amount)\b',
            r'\bwhat\s+(is|are)\s+the\s+total\b',
        ],
    }

    # Question type patterns
    QUESTION_PATTERNS = {
        "who": r'\b(who)\b',
        "what": r'\b(what)\b',
        "when": r'\b(when)\b',
        "where": r'\b(where)\b',
        "why": r'\b(why)\b',
        "how": r'\b(how)\b',
        "which": r'\b(which)\b',
    }

    # Stop words to remove during keyword extraction
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'i', 'you', 'they', 'we', 'my', 'your',
        'can', 'could', 'should', 'would', 'may', 'might', 'must', 'do', 'does'
    }

    def __init__(self, use_spacy: bool = False):
        """
        Initialize the query parser.

        Args:
            use_spacy: Whether to use spaCy for NLP tasks
        """
        self.entity_extractor = LegalEntityExtractor(use_spacy=use_spacy)
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for faster matching"""
        self.compiled_intent_patterns = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            self.compiled_intent_patterns[intent] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]

        self.compiled_question_patterns = {
            q_type: re.compile(pattern, re.IGNORECASE)
            for q_type, pattern in self.QUESTION_PATTERNS.items()
        }

    def parse_query(self, query: str) -> ParsedQuery:
        """
        Parse a natural language query and extract structured information.

        Args:
            query: The user's query text

        Returns:
            ParsedQuery object with extracted information
        """
        if not query or not query.strip():
            return ParsedQuery(
                original_query=query,
                normalized_query="",
                intent=QueryIntent.UNKNOWN,
                intent_confidence=0.0,
                entities=[],
                keywords=[]
            )

        # Normalize query
        normalized = self._normalize_query(query)

        # Classify intent
        intent, intent_confidence = self._classify_intent(normalized)

        # Extract entities
        entities = self.entity_extractor.extract_entities(normalized)

        # Extract keywords
        keywords = self._extract_keywords(normalized, entities)

        # Detect question type
        question_type = self._detect_question_type(normalized)

        # Extract filters
        filters = self._extract_filters(entities)

        # Build parsed query
        parsed_query = ParsedQuery(
            original_query=query,
            normalized_query=normalized,
            intent=intent,
            intent_confidence=intent_confidence,
            entities=entities,
            keywords=keywords,
            question_type=question_type,
            filters=filters,
            metadata={
                "entity_count": len(entities),
                "entity_summary": self.entity_extractor.get_entity_summary(entities)
            }
        )

        return parsed_query

    def _normalize_query(self, query: str) -> str:
        """
        Normalize a query by cleaning and standardizing text.

        Args:
            query: The original query

        Returns:
            Normalized query text
        """
        # Remove extra whitespace
        normalized = ' '.join(query.split())

        # Remove question mark at end (we'll detect questions another way)
        normalized = normalized.rstrip('?')

        # Lowercase for consistency (but keep original for entity extraction)
        return normalized.strip()

    def _classify_intent(self, query: str) -> Tuple[QueryIntent, float]:
        """
        Classify the intent of a query.

        Args:
            query: The normalized query text

        Returns:
            Tuple of (intent, confidence_score)
        """
        intent_scores = {}

        # Score each intent based on pattern matches
        for intent, patterns in self.compiled_intent_patterns.items():
            score = 0
            for pattern in patterns:
                if pattern.search(query):
                    score += 1

            if score > 0:
                # Normalize score (max 1.0)
                intent_scores[intent] = min(score / len(patterns), 1.0)

        # If no patterns matched, try to infer from question words
        if not intent_scores:
            return self._infer_intent_from_structure(query)

        # PRIORITY RULE: STATISTICS takes precedence over DEFINITION
        # When both match (e.g., "What is the total number of..."), choose STATISTICS
        if (QueryIntent.STATISTICS in intent_scores and 
            QueryIntent.DEFINITION in intent_scores):
            # If both matched, prefer STATISTICS
            best_intent = QueryIntent.STATISTICS
            confidence = intent_scores[QueryIntent.STATISTICS]
        else:
            # Get intent with highest score
            best_intent = max(intent_scores, key=intent_scores.get)
            confidence = intent_scores[best_intent]

        # Boost confidence if multiple strong signals
        if confidence > 0.5:
            confidence = min(confidence * 1.2, 0.95)

        return best_intent, confidence

    def _infer_intent_from_structure(self, query: str) -> Tuple[QueryIntent, float]:
        """
        Infer intent from query structure when patterns don't match.

        Args:
            query: The normalized query text

        Returns:
            Tuple of (intent, confidence_score)
        """
        query_lower = query.lower()

        # Eligibility patterns
        if "can" in query_lower and "apply" in query_lower:
            return QueryIntent.ELIGIBILITY, 0.7

        # Definition patterns
        if query_lower.startswith("what is") or query_lower.startswith("what are"):
            return QueryIntent.DEFINITION, 0.7

        # Procedure patterns
        if query_lower.startswith("how"):
            return QueryIntent.PROCEDURE, 0.7

        # Search patterns
        if query_lower.startswith("where") or query_lower.startswith("which"):
            return QueryIntent.SEARCH, 0.6

        # Default to unknown with low confidence
        return QueryIntent.UNKNOWN, 0.3

    def _detect_question_type(self, query: str) -> Optional[str]:
        """
        Detect the type of question (who, what, when, where, why, how).

        Args:
            query: The normalized query text

        Returns:
            Question type or None
        """
        for q_type, pattern in self.compiled_question_patterns.items():
            if pattern.search(query):
                return q_type
        return None

    def _extract_keywords(self, query: str, entities: List[ExtractedEntity]) -> List[str]:
        """
        Extract important keywords from query, excluding stop words and entities.

        Args:
            query: The normalized query text
            entities: Extracted entities

        Returns:
            List of keywords
        """
        # Remove entity text from query to avoid duplication
        entity_texts = {e.text.lower() for e in entities}

        # Tokenize
        words = re.findall(r'\b\w+\b', query.lower())

        # Filter out stop words and entity text
        keywords = [
            word for word in words
            if word not in self.STOP_WORDS
            and word not in entity_texts
            and len(word) > 2  # Ignore very short words
        ]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords

    def _extract_filters(self, entities: List[ExtractedEntity]) -> Dict[str, any]:
        """
        Extract structured filters from entities.

        Args:
            entities: Extracted entities

        Returns:
            Dictionary of filters
        """
        filters = {}

        # Extract jurisdiction filters
        jurisdictions = [
            e.normalized for e in entities
            if e.entity_type == EntityType.JURISDICTION
        ]
        if jurisdictions:
            filters["jurisdiction"] = jurisdictions[0]  # Use first jurisdiction

        # Extract program filters
        programs = [
            e.normalized for e in entities
            if e.entity_type == EntityType.PROGRAM
        ]
        if programs:
            filters["program"] = programs

        # Extract person type filters
        person_types = [
            e.normalized for e in entities
            if e.entity_type == EntityType.PERSON_TYPE
        ]
        if person_types:
            filters["person_type"] = person_types

        # Extract date filters
        dates = [
            e.text for e in entities
            if e.entity_type == EntityType.DATE
        ]
        if dates:
            filters["date"] = dates

        return filters

    def batch_parse_queries(self, queries: List[str]) -> List[ParsedQuery]:
        """
        Parse multiple queries in batch.

        Args:
            queries: List of query strings

        Returns:
            List of ParsedQuery objects
        """
        return [self.parse_query(query) for query in queries]

    def get_intent_distribution(self, parsed_queries: List[ParsedQuery]) -> Dict[str, int]:
        """
        Get distribution of intents across multiple queries.

        Args:
            parsed_queries: List of parsed queries

        Returns:
            Dictionary mapping intent to count
        """
        distribution = {}
        for pq in parsed_queries:
            intent = pq.intent.value
            distribution[intent] = distribution.get(intent, 0) + 1
        return distribution


class QueryExpander:
    """
    Expand queries with synonyms and related terms for better search recall.
    """

    def __init__(self):
        """Initialize the query expander"""
        self.entity_extractor = LegalEntityExtractor(use_spacy=False)

    def expand_query(self, query: str) -> List[str]:
        """
        Expand a query with synonyms and related terms.

        Args:
            query: The original query

        Returns:
            List of expanded query variations
        """
        expanded_queries = [query]  # Include original

        # Extract entities
        entities = self.entity_extractor.extract_entities(query)

        # For each entity, create variations with synonyms
        for entity in entities:
            if entity.entity_type in [EntityType.PERSON_TYPE, EntityType.PROGRAM,
                                     EntityType.JURISDICTION, EntityType.REQUIREMENT]:
                # Get synonyms from terminology
                synonyms = self._get_synonyms(entity.normalized, entity.entity_type)

                # Create query variations
                for synonym in synonyms:
                    if synonym.lower() != entity.text.lower():
                        expanded = query.replace(entity.text, synonym)
                        if expanded not in expanded_queries:
                            expanded_queries.append(expanded)

        return expanded_queries[:5]  # Limit to 5 variations

    def _get_synonyms(self, canonical: str, entity_type: EntityType) -> List[str]:
        """Get synonyms for a canonical term"""
        try:
            from .legal_nlp import LegalTerminology
        except ImportError:
            from legal_nlp import LegalTerminology

        if entity_type == EntityType.PERSON_TYPE:
            term_dict = LegalTerminology.PERSON_TYPES
        elif entity_type == EntityType.PROGRAM:
            term_dict = LegalTerminology.PROGRAMS
        elif entity_type == EntityType.JURISDICTION:
            term_dict = LegalTerminology.JURISDICTIONS
        elif entity_type == EntityType.REQUIREMENT:
            term_dict = LegalTerminology.REQUIREMENTS
        else:
            return []

        return term_dict.get(canonical, [])


# Convenience function
def parse_legal_query(query: str, use_spacy: bool = False) -> ParsedQuery:
    """
    Quick function to parse a legal query.

    Args:
        query: The user's query text
        use_spacy: Whether to use spaCy for NLP

    Returns:
        ParsedQuery object

    Example:
        >>> parsed = parse_legal_query("Can a temporary resident apply for employment insurance?")
        >>> print(f"Intent: {parsed.intent}, Confidence: {parsed.intent_confidence}")
        >>> print(f"Entities: {[e.text for e in parsed.entities]}")
    """
    parser = LegalQueryParser(use_spacy=use_spacy)
    return parser.parse_query(query)


if __name__ == "__main__":
    # Test the query parser
    test_queries = [
        "Can a temporary resident apply for employment insurance?",
        "What are the eligibility requirements for Canada Pension Plan?",
        "How do I apply for old age security benefits?",
        "What does 'permanent resident' mean in the Immigration Act?",
        "Find all regulations about employment insurance for Ontario.",
        "Is my application compliant with the requirements?",
        "Compare EI and CPP benefits for seniors.",
        "What is the procedure for obtaining a work permit?",
    ]

    parser = LegalQueryParser(use_spacy=False)
    expander = QueryExpander()

    print("=" * 80)
    print("Query Parser Service - Intent Classification and Entity Extraction Test")
    print("=" * 80)

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test Case {i}: {query}")
        print("-" * 80)

        # Parse query
        parsed = parser.parse_query(query)

        # Display results
        print(f"Intent: {parsed.intent.value} (confidence: {parsed.intent_confidence:.2f})")
        print(f"Question Type: {parsed.question_type or 'N/A'}")
        print(f"Normalized: {parsed.normalized_query}")

        if parsed.entities:
            print(f"\nEntities ({len(parsed.entities)}):")
            for entity in parsed.entities:
                print(f"  - [{entity.entity_type.value}] {entity.text} → {entity.normalized}")

        if parsed.keywords:
            print(f"\nKeywords: {', '.join(parsed.keywords)}")

        if parsed.filters:
            print(f"\nFilters: {parsed.filters}")

        # Show query expansion
        expanded = expander.expand_query(query)
        if len(expanded) > 1:
            print(f"\nQuery Expansions:")
            for j, exp_query in enumerate(expanded[1:], 1):  # Skip original
                print(f"  {j}. {exp_query}")

    print("\n" + "=" * 80)
    print("Test complete!")

    # Test batch parsing
    print("\n" + "=" * 80)
    print("Intent Distribution Across All Queries:")
    print("-" * 80)
    all_parsed = parser.batch_parse_queries(test_queries)
    distribution = parser.get_intent_distribution(all_parsed)
    for intent, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        print(f"  {intent}: {count}")
