"""
Query Suggestion System

Intelligent query suggestions and autocomplete for regulatory searches:
- Auto-complete based on common legal queries
- Popular searches and trending topics
- Query history-based suggestions
- Typo correction and fuzzy matching
- Personalized suggestions (when user data available)
- Query templates for common scenarios

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import re
import logging
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


# === Query Suggestion Entry ===

@dataclass
class QuerySuggestion:
    """A single query suggestion"""
    text: str
    score: float
    category: str = "general"  # general, popular, history, template
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'text': self.text,
            'score': round(self.score, 3),
            'category': self.category,
            'metadata': self.metadata
        }


# === Query Templates ===

QUERY_TEMPLATES = {
    'eligibility': [
        "Who is eligible for {program}?",
        "Can {person_type} apply for {program}?",
        "What are the eligibility requirements for {program}?",
        "Am I eligible for {program}?",
    ],
    'application': [
        "How do I apply for {program}?",
        "What documents are needed for {program}?",
        "Where can I submit {program} application?",
        "How long does {program} application take?",
    ],
    'benefits': [
        "What benefits does {program} provide?",
        "How much is {program} benefit?",
        "When do I receive {program} payments?",
        "How long can I receive {program}?",
    ],
    'requirements': [
        "What are the requirements for {program}?",
        "What documentation is required for {program}?",
        "Do I need {requirement} for {program}?",
    ],
    'process': [
        "What is the {program} process?",
        "How does {program} work?",
        "What are the steps for {program}?",
    ],
    'status': [
        "How do I check my {program} status?",
        "When will my {program} be processed?",
        "How do I track my {program} application?",
    ],
}

# Common program names
COMMON_PROGRAMS = [
    "Employment Insurance",
    "Canada Pension Plan",
    "Old Age Security",
    "Canada Child Benefit",
    "Guaranteed Income Supplement",
    "Disability Tax Credit",
    "Working Holiday Visa",
    "Study Permit",
    "Work Permit",
]

# Common person types
COMMON_PERSON_TYPES = [
    "permanent residents",
    "temporary residents",
    "international students",
    "foreign workers",
    "refugees",
    "Canadian citizens",
    "temporary foreign workers",
]

# Popular regulatory queries (pre-defined)
POPULAR_QUERIES = [
    "employment insurance eligibility requirements",
    "how to apply for canada pension plan",
    "permanent resident work permit",
    "international student work hours",
    "temporary resident visa extension",
    "employment insurance maternity benefits",
    "canada child benefit calculation",
    "old age security payment dates",
    "guaranteed income supplement eligibility",
    "disability tax credit application",
    "working holiday visa requirements",
    "study permit extension process",
    "work permit application for spouse",
    "refugee protection claim process",
    "citizenship application requirements",
]


# === Typo Correction ===

class TypoCorrector:
    """Simple typo correction using edit distance"""

    def __init__(self, dictionary: List[str]):
        """
        Initialize with dictionary of valid terms

        Args:
            dictionary: List of correctly spelled terms
        """
        self.dictionary = set(term.lower() for term in dictionary)

    def correct(self, word: str, threshold: float = 0.8) -> Optional[str]:
        """
        Correct typo if similar word exists

        Args:
            word: Potentially misspelled word
            threshold: Minimum similarity (0-1)

        Returns:
            Corrected word or None
        """
        word_lower = word.lower()

        # Check if already correct
        if word_lower in self.dictionary:
            return word

        # Find most similar word
        best_match = None
        best_score = 0.0

        for dict_word in self.dictionary:
            similarity = SequenceMatcher(None, word_lower, dict_word).ratio()

            if similarity > best_score and similarity >= threshold:
                best_score = similarity
                best_match = dict_word

        return best_match


# === Query Analyzer ===

class QueryAnalyzer:
    """Analyze queries to extract patterns and entities"""

    @staticmethod
    def extract_programs(query: str) -> List[str]:
        """Extract program names from query"""
        query_lower = query.lower()
        found_programs = []

        for program in COMMON_PROGRAMS:
            if program.lower() in query_lower:
                found_programs.append(program)

        return found_programs

    @staticmethod
    def extract_person_types(query: str) -> List[str]:
        """Extract person types from query"""
        query_lower = query.lower()
        found_types = []

        for person_type in COMMON_PERSON_TYPES:
            if person_type.lower() in query_lower:
                found_types.append(person_type)

        return found_types

    @staticmethod
    def classify_intent(query: str) -> str:
        """Classify query intent based on keywords"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['eligible', 'eligibility', 'qualify', 'can i']):
            return 'eligibility'
        elif any(word in query_lower for word in ['apply', 'application', 'submit', 'register']):
            return 'application'
        elif any(word in query_lower for word in ['benefit', 'payment', 'amount', 'how much']):
            return 'benefits'
        elif any(word in query_lower for word in ['require', 'need', 'document', 'must']):
            return 'requirements'
        elif any(word in query_lower for word in ['process', 'how', 'step', 'procedure']):
            return 'process'
        elif any(word in query_lower for word in ['status', 'check', 'track', 'when']):
            return 'status'
        else:
            return 'general'


# === Query Suggestion Engine ===

class QuerySuggestionEngine:
    """
    Main query suggestion engine

    Combines multiple suggestion sources:
    - Auto-complete from prefix matching
    - Popular queries
    - Query history
    - Template-based suggestions
    - Typo correction
    """

    def __init__(self, enable_typo_correction: bool = True):
        """Initialize suggestion engine"""
        self.enable_typo_correction = enable_typo_correction

        # Query history (in production, load from database)
        self.query_history: List[Tuple[str, datetime]] = []
        self.query_counts: Counter = Counter()

        # Build typo corrector dictionary
        dictionary = (
            COMMON_PROGRAMS +
            COMMON_PERSON_TYPES +
            POPULAR_QUERIES +
            ['employment', 'insurance', 'pension', 'benefit', 'application', 'eligibility']
        )
        self.typo_corrector = TypoCorrector(dictionary)

        logger.info("Query suggestion engine initialized")

    def record_query(self, query: str):
        """
        Record a query in history

        Args:
            query: User query to record
        """
        self.query_history.append((query, datetime.now()))
        self.query_counts[query.lower()] += 1

        # Keep only last 1000 queries in memory
        if len(self.query_history) > 1000:
            self.query_history = self.query_history[-1000:]

    def _score_suggestion(
        self,
        suggestion: str,
        prefix: str,
        category: str,
        popularity: int = 0
    ) -> float:
        """
        Calculate relevance score for suggestion

        Args:
            suggestion: Suggestion text
            prefix: User's input prefix
            category: Suggestion category
            popularity: Number of times used

        Returns:
            Score between 0-1
        """
        score = 0.0

        # Prefix match score (0-0.5)
        suggestion_lower = suggestion.lower()
        prefix_lower = prefix.lower()

        if suggestion_lower.startswith(prefix_lower):
            # Exact prefix match
            score += 0.5
        elif prefix_lower in suggestion_lower:
            # Contains prefix
            score += 0.3
        else:
            # Fuzzy match
            similarity = SequenceMatcher(None, prefix_lower, suggestion_lower).ratio()
            score += similarity * 0.2

        # Category bonus (0-0.2)
        category_weights = {
            'popular': 0.2,
            'history': 0.15,
            'template': 0.1,
            'general': 0.05
        }
        score += category_weights.get(category, 0)

        # Popularity bonus (0-0.3)
        if popularity > 0:
            # Log scale for popularity
            import math
            popularity_score = min(0.3, math.log(popularity + 1) / 10)
            score += popularity_score

        return min(1.0, score)

    def _get_prefix_matches(self, prefix: str, max_results: int = 10) -> List[QuerySuggestion]:
        """Get suggestions matching prefix"""
        suggestions = []

        # Match from popular queries
        for query in POPULAR_QUERIES:
            if query.lower().startswith(prefix.lower()) or prefix.lower() in query.lower():
                score = self._score_suggestion(query, prefix, 'popular', popularity=100)
                suggestions.append(QuerySuggestion(
                    text=query,
                    score=score,
                    category='popular'
                ))

        # Match from query history
        for query, timestamp in self.query_history[-100:]:
            if query.lower().startswith(prefix.lower()) or prefix.lower() in query.lower():
                popularity = self.query_counts[query.lower()]
                score = self._score_suggestion(query, prefix, 'history', popularity=popularity)
                suggestions.append(QuerySuggestion(
                    text=query,
                    score=score,
                    category='history',
                    metadata={'last_used': timestamp.isoformat()}
                ))

        # Sort by score and deduplicate
        suggestions.sort(key=lambda x: x.score, reverse=True)

        seen = set()
        unique_suggestions = []
        for sugg in suggestions:
            if sugg.text.lower() not in seen:
                seen.add(sugg.text.lower())
                unique_suggestions.append(sugg)

        return unique_suggestions[:max_results]

    def _get_template_suggestions(self, query: str, max_results: int = 5) -> List[QuerySuggestion]:
        """Generate template-based suggestions"""
        suggestions = []

        # Analyze query
        programs = QueryAnalyzer.extract_programs(query)
        person_types = QueryAnalyzer.extract_person_types(query)
        intent = QueryAnalyzer.classify_intent(query)

        # Get templates for intent
        templates = QUERY_TEMPLATES.get(intent, [])

        for template in templates[:max_results]:
            # Fill template with detected entities
            filled_template = template

            if '{program}' in template and programs:
                filled_template = template.format(program=programs[0])
            elif '{person_type}' in template and person_types:
                filled_template = template.format(person_type=person_types[0])
            elif '{requirement}' in template:
                filled_template = template.replace('{requirement}', 'a work permit')
            else:
                # Skip unfilled templates
                continue

            score = self._score_suggestion(filled_template, query, 'template')
            suggestions.append(QuerySuggestion(
                text=filled_template,
                score=score,
                category='template',
                metadata={'intent': intent}
            ))

        return suggestions

    def _correct_typos(self, query: str) -> Optional[str]:
        """Attempt to correct typos in query"""
        if not self.enable_typo_correction:
            return None

        words = query.split()
        corrected_words = []
        has_correction = False

        for word in words:
            corrected = self.typo_corrector.correct(word)
            if corrected and corrected != word.lower():
                corrected_words.append(corrected)
                has_correction = True
            else:
                corrected_words.append(word)

        if has_correction:
            return ' '.join(corrected_words)

        return None

    def get_suggestions(
        self,
        query: str,
        max_results: int = 10,
        include_templates: bool = True
    ) -> List[QuerySuggestion]:
        """
        Get query suggestions

        Args:
            query: User's partial or complete query
            max_results: Maximum number of suggestions
            include_templates: Include template-based suggestions

        Returns:
            List of QuerySuggestion objects
        """
        if not query or len(query) < 2:
            # Return popular queries for empty/short input
            return [
                QuerySuggestion(text=q, score=1.0, category='popular')
                for q in POPULAR_QUERIES[:max_results]
            ]

        suggestions = []

        # Get prefix matches
        prefix_matches = self._get_prefix_matches(query, max_results=max_results)
        suggestions.extend(prefix_matches)

        # Get template suggestions
        if include_templates:
            template_suggestions = self._get_template_suggestions(query, max_results=5)
            suggestions.extend(template_suggestions)

        # Check for typos and suggest correction
        corrected = self._correct_typos(query)
        if corrected:
            suggestions.insert(0, QuerySuggestion(
                text=corrected,
                score=0.95,
                category='correction',
                metadata={'original': query}
            ))

        # Sort by score and limit
        suggestions.sort(key=lambda x: x.score, reverse=True)

        # Deduplicate
        seen = set()
        unique_suggestions = []
        for sugg in suggestions:
            if sugg.text.lower() not in seen:
                seen.add(sugg.text.lower())
                unique_suggestions.append(sugg)

        return unique_suggestions[:max_results]

    def get_trending_queries(self, hours: int = 24, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get trending queries from recent history

        Args:
            hours: Look back this many hours
            top_n: Return top N queries

        Returns:
            List of trending queries with counts
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Count recent queries
        recent_counts: Counter = Counter()

        for query, timestamp in self.query_history:
            if timestamp >= cutoff_time:
                recent_counts[query.lower()] += 1

        # Get top queries
        trending = [
            {
                'query': query,
                'count': count,
                'category': 'trending'
            }
            for query, count in recent_counts.most_common(top_n)
        ]

        return trending

    def get_popular_by_category(self, category: str, top_n: int = 10) -> List[str]:
        """
        Get popular queries by category/intent

        Args:
            category: Category/intent name
            top_n: Number of results

        Returns:
            List of queries
        """
        # Filter queries by intent
        categorized_queries = []

        for query, _ in self.query_history:
            intent = QueryAnalyzer.classify_intent(query)
            if intent == category:
                categorized_queries.append(query)

        # Count and return top
        counts = Counter(categorized_queries)
        return [q for q, _ in counts.most_common(top_n)]


# === Global Engine Instance ===

_suggestion_engine: Optional[QuerySuggestionEngine] = None


def get_suggestion_engine() -> QuerySuggestionEngine:
    """Get or create global suggestion engine"""
    global _suggestion_engine

    if _suggestion_engine is None:
        _suggestion_engine = QuerySuggestionEngine()

    return _suggestion_engine


# === Example Usage ===

if __name__ == "__main__":
    # Initialize engine
    engine = QuerySuggestionEngine()

    # Simulate some query history
    test_queries = [
        "employment insurance eligibility",
        "employment insurance application",
        "canada pension plan benefits",
        "permanent resident work permit",
        "international student visa",
    ]

    for query in test_queries:
        engine.record_query(query)

    # Test suggestions
    print("Suggestions for 'employ':")
    suggestions = engine.get_suggestions("employ", max_results=5)
    for sugg in suggestions:
        print(f"  - {sugg.text} (score: {sugg.score:.3f}, category: {sugg.category})")

    print("\nSuggestions for 'can permanent residents':")
    suggestions = engine.get_suggestions("can permanent residents", max_results=5)
    for sugg in suggestions:
        print(f"  - {sugg.text} (score: {sugg.score:.3f}, category: {sugg.category})")

    print("\nTrending queries:")
    trending = engine.get_trending_queries(hours=24, top_n=5)
    for item in trending:
        print(f"  - {item['query']} ({item['count']} searches)")

    print("\nQuery suggestion system ready!")
