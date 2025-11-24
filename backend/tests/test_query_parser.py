"""
Tests for query_parser service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from services.query_parser import (
    QueryIntent, ParsedQuery, LegalQueryParser, QueryExpander,
    parse_legal_query
)
from services.legal_nlp import ExtractedEntity, EntityType


class TestQueryIntent:
    """Tests for QueryIntent enum."""
    
    def test_query_intent_values(self):
        """Test QueryIntent enum values."""
        assert QueryIntent.SEARCH.value == "search"
        assert QueryIntent.COMPLIANCE.value == "compliance"
        assert QueryIntent.INTERPRETATION.value == "interpretation"
        assert QueryIntent.ELIGIBILITY.value == "eligibility"
        assert QueryIntent.PROCEDURE.value == "procedure"
        assert QueryIntent.DEFINITION.value == "definition"
        assert QueryIntent.COMPARISON.value == "comparison"
        assert QueryIntent.UNKNOWN.value == "unknown"
    
    def test_query_intent_membership(self):
        """Test QueryIntent enum membership."""
        intents = list(QueryIntent)
        assert len(intents) == 8
        assert QueryIntent.SEARCH in intents
        assert QueryIntent.UNKNOWN in intents


class TestParsedQuery:
    """Tests for ParsedQuery dataclass."""
    
    @pytest.fixture
    def sample_entity(self):
        """Create sample extracted entity."""
        return ExtractedEntity(
            text="temporary resident",
            entity_type=EntityType.PERSON_TYPE,
            normalized="temporary_resident",
            confidence=0.95,
            start_pos=6,
            end_pos=24
        )
    
    @pytest.fixture
    def parsed_query(self, sample_entity):
        """Create sample ParsedQuery."""
        return ParsedQuery(
            original_query="Can a temporary resident apply?",
            normalized_query="can a temporary resident apply",
            intent=QueryIntent.ELIGIBILITY,
            intent_confidence=0.85,
            entities=[sample_entity],
            keywords=["apply"],
            question_type="can",
            filters={"person_type": ["temporary_resident"]},
            context="Eligibility question",
            metadata={"entity_count": 1}
        )
    
    def test_parsed_query_creation(self, parsed_query):
        """Test ParsedQuery creation."""
        assert parsed_query.original_query == "Can a temporary resident apply?"
        assert parsed_query.normalized_query == "can a temporary resident apply"
        assert parsed_query.intent == QueryIntent.ELIGIBILITY
        assert parsed_query.intent_confidence == 0.85
        assert len(parsed_query.entities) == 1
        assert parsed_query.keywords == ["apply"]
    
    def test_to_dict(self, parsed_query):
        """Test conversion to dictionary."""
        result = parsed_query.to_dict()
        
        assert isinstance(result, dict)
        assert result["original_query"] == "Can a temporary resident apply?"
        assert result["intent"] == "eligibility"
        assert result["intent_confidence"] == 0.85
        assert isinstance(result["entities"], list)
        assert len(result["entities"]) == 1
        assert result["keywords"] == ["apply"]
        assert result["filters"] == {"person_type": ["temporary_resident"]}
    
    def test_get_entities_by_type(self, parsed_query, sample_entity):
        """Test filtering entities by type."""
        # Add another entity of different type
        location_entity = ExtractedEntity(
            text="Ontario",
            entity_type=EntityType.JURISDICTION,
            normalized="ontario",
            confidence=0.9,
            start_pos=0,
            end_pos=7
        )
        parsed_query.entities.append(location_entity)
        
        person_entities = parsed_query.get_entities_by_type(EntityType.PERSON_TYPE)
        assert len(person_entities) == 1
        assert person_entities[0].text == "temporary resident"
        
        location_entities = parsed_query.get_entities_by_type(EntityType.JURISDICTION)
        assert len(location_entities) == 1
        assert location_entities[0].text == "Ontario"
    
    def test_get_entities_by_type_empty(self, parsed_query):
        """Test getting entities when none of that type exist."""
        date_entities = parsed_query.get_entities_by_type(EntityType.DATE)
        assert date_entities == []


class TestLegalQueryParser:
    """Tests for LegalQueryParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create LegalQueryParser instance."""
        return LegalQueryParser(use_spacy=False)
    
    def test_parser_initialization(self, parser):
        """Test parser initialization."""
        assert parser.entity_extractor is not None
        assert hasattr(parser, 'compiled_intent_patterns')
        assert hasattr(parser, 'compiled_question_patterns')
    
    def test_normalize_query(self, parser):
        """Test query normalization."""
        query = "  What   is  EI?  "
        normalized = parser._normalize_query(query)
        
        assert normalized == "What is EI"
        assert not normalized.endswith("?")
        assert "  " not in normalized
    
    def test_normalize_query_empty(self, parser):
        """Test normalizing empty query."""
        assert parser._normalize_query("") == ""
        assert parser._normalize_query("   ") == ""
    
    def test_classify_intent_search(self, parser):
        """Test classifying search intent."""
        queries = [
            "find regulations about privacy",
            "search for employment insurance rules",
            "what are the laws about taxes"
        ]
        
        for query in queries:
            intent, confidence = parser._classify_intent(query)
            assert intent == QueryIntent.SEARCH
            assert confidence > 0
    
    def test_classify_intent_compliance(self, parser):
        """Test classifying compliance intent."""
        queries = [
            "am i compliant with privacy regulations",
            "is this application compliant",
            "check if application meets requirements"
        ]
        
        for query in queries:
            intent, confidence = parser._classify_intent(query)
            assert intent == QueryIntent.COMPLIANCE
            assert confidence > 0
    
    def test_classify_intent_eligibility(self, parser):
        """Test classifying eligibility intent."""
        queries = [
            "am i eligible for EI benefits",
            "who qualifies for CPP",
            "do i qualify for benefits"
        ]
        
        for query in queries:
            intent, confidence = parser._classify_intent(query)
            assert intent == QueryIntent.ELIGIBILITY
            assert confidence > 0
    
    def test_classify_intent_procedure(self, parser):
        """Test classifying procedure intent."""
        queries = [
            "how do i apply for EI",
            "what are the steps to register",
            "how to submit an application"
        ]
        
        for query in queries:
            intent, confidence = parser._classify_intent(query)
            assert intent == QueryIntent.PROCEDURE
            assert confidence > 0
    
    def test_classify_intent_definition(self, parser):
        """Test classifying definition intent."""
        queries = [
            "what is employment insurance",
            "what are temporary residents",
            "define permanent resident"
        ]
        
        for query in queries:
            intent, confidence = parser._classify_intent(query)
            assert intent == QueryIntent.DEFINITION
            assert confidence > 0
    
    def test_infer_intent_from_structure(self, parser):
        """Test inferring intent from query structure."""
        # Test eligibility inference
        intent, conf = parser._infer_intent_from_structure("can I apply for benefits")
        assert intent == QueryIntent.ELIGIBILITY
        
        # Test definition inference
        intent, conf = parser._infer_intent_from_structure("what is EI")
        assert intent == QueryIntent.DEFINITION
        
        # Test procedure inference
        intent, conf = parser._infer_intent_from_structure("how to apply")
        assert intent == QueryIntent.PROCEDURE
        
        # Test unknown inference
        intent, conf = parser._infer_intent_from_structure("random text")
        assert intent == QueryIntent.UNKNOWN
        assert conf < 0.5
    
    def test_detect_question_type(self, parser):
        """Test detecting question types."""
        assert parser._detect_question_type("who is eligible") == "who"
        assert parser._detect_question_type("what is EI") == "what"
        assert parser._detect_question_type("when can I apply") == "when"
        assert parser._detect_question_type("where do I submit") == "where"
        assert parser._detect_question_type("why is this required") == "why"
        assert parser._detect_question_type("how do I apply") == "how"
        assert parser._detect_question_type("which option is better") == "which"
        assert parser._detect_question_type("this is not a question") is None
    
    def test_extract_keywords(self, parser):
        """Test keyword extraction."""
        query = "find employment insurance regulations for temporary residents"
        entities = [
            ExtractedEntity(
                text="employment insurance",
                entity_type=EntityType.PROGRAM,
                normalized="employment_insurance",
                confidence=0.9,
                start_pos=5,
                end_pos=26
            ),
            ExtractedEntity(
                text="temporary residents",
                entity_type=EntityType.PERSON_TYPE,
                normalized="temporary_resident",
                confidence=0.9,
                start_pos=43,
                end_pos=62
            )
        ]
        
        keywords = parser._extract_keywords(query, entities)
        
        # Should exclude stop words like "for"
        assert "for" not in keywords
        # Important keywords should be included
        assert "regulations" in keywords
        # Keywords list should not be empty
        assert len(keywords) > 0
        # Entity normalized forms should not be in keywords
        assert "employment_insurance" not in keywords
        assert "temporary_resident" not in keywords
    
    def test_extract_keywords_deduplication(self, parser):
        """Test keyword deduplication."""
        query = "apply apply for benefits benefits"
        keywords = parser._extract_keywords(query, [])
        
        # Should remove duplicates
        assert keywords.count("apply") == 1
        assert keywords.count("benefits") == 1
    
    def test_extract_filters(self, parser):
        """Test extracting filters from entities."""
        entities = [
            ExtractedEntity(
                text="Ontario",
                entity_type=EntityType.JURISDICTION,
                normalized="ontario",
                confidence=0.9,
                start_pos=0,
                end_pos=7
            ),
            ExtractedEntity(
                text="EI",
                entity_type=EntityType.PROGRAM,
                normalized="employment_insurance",
                confidence=0.95,
                start_pos=8,
                end_pos=10
            ),
            ExtractedEntity(
                text="temporary resident",
                entity_type=EntityType.PERSON_TYPE,
                normalized="temporary_resident",
                confidence=0.9,
                start_pos=11,
                end_pos=29
            )
        ]
        
        filters = parser._extract_filters(entities)
        
        assert filters["jurisdiction"] == "ontario"
        assert "employment_insurance" in filters["program"]
        assert "temporary_resident" in filters["person_type"]
    
    def test_extract_filters_empty(self, parser):
        """Test extracting filters with no entities."""
        filters = parser._extract_filters([])
        assert filters == {}
    
    def test_parse_query_complete(self, parser):
        """Test complete query parsing."""
        query = "Can a temporary resident apply for employment insurance in Ontario?"
        
        parsed = parser.parse_query(query)
        
        assert parsed.original_query == query
        assert parsed.normalized_query
        assert parsed.intent in QueryIntent
        assert 0 <= parsed.intent_confidence <= 1.0
        assert isinstance(parsed.entities, list)
        assert isinstance(parsed.keywords, list)
        assert isinstance(parsed.filters, dict)
        assert isinstance(parsed.metadata, dict)
    
    def test_parse_query_empty(self, parser):
        """Test parsing empty query."""
        parsed = parser.parse_query("")
        
        assert parsed.original_query == ""
        assert parsed.normalized_query == ""
        assert parsed.intent == QueryIntent.UNKNOWN
        assert parsed.intent_confidence == 0.0
        assert parsed.entities == []
        assert parsed.keywords == []
    
    def test_parse_query_whitespace(self, parser):
        """Test parsing whitespace-only query."""
        parsed = parser.parse_query("   ")
        
        assert parsed.intent == QueryIntent.UNKNOWN
        assert parsed.intent_confidence == 0.0
    
    def test_batch_parse_queries(self, parser):
        """Test batch parsing of multiple queries."""
        queries = [
            "What is EI?",
            "How do I apply for CPP?",
            "Am I eligible for old age security?"
        ]
        
        results = parser.batch_parse_queries(queries)
        
        assert len(results) == 3
        assert all(isinstance(r, ParsedQuery) for r in results)
        assert results[0].original_query == queries[0]
        assert results[1].original_query == queries[1]
        assert results[2].original_query == queries[2]
    
    def test_get_intent_distribution(self, parser):
        """Test getting intent distribution across queries."""
        parsed_queries = [
            ParsedQuery("q1", "q1", QueryIntent.SEARCH, 0.9, [], []),
            ParsedQuery("q2", "q2", QueryIntent.SEARCH, 0.8, [], []),
            ParsedQuery("q3", "q3", QueryIntent.ELIGIBILITY, 0.85, [], []),
            ParsedQuery("q4", "q4", QueryIntent.COMPLIANCE, 0.7, [], []),
        ]
        
        distribution = parser.get_intent_distribution(parsed_queries)
        
        assert distribution["search"] == 2
        assert distribution["eligibility"] == 1
        assert distribution["compliance"] == 1


class TestQueryExpander:
    """Tests for QueryExpander class."""
    
    @pytest.fixture
    def expander(self):
        """Create QueryExpander instance."""
        return QueryExpander()
    
    def test_expander_initialization(self, expander):
        """Test expander initialization."""
        assert expander.entity_extractor is not None
    
    @patch.object(QueryExpander, '_get_synonyms')
    def test_expand_query(self, mock_get_synonyms, expander):
        """Test query expansion."""
        # Mock synonyms
        mock_get_synonyms.return_value = ["foreign worker", "non-citizen"]
        
        # Mock entity extraction
        mock_entity = ExtractedEntity(
            text="temporary resident",
            entity_type=EntityType.PERSON_TYPE,
            normalized="temporary_resident",
            confidence=0.9,
            start_pos=6,
            end_pos=24
        )
        
        with patch.object(expander.entity_extractor, 'extract_entities', return_value=[mock_entity]):
            query = "Can a temporary resident apply?"
            expanded = expander.expand_query(query)
            
            assert isinstance(expanded, list)
            assert query in expanded  # Original included
            assert len(expanded) <= 5  # Max 5 variations
    
    def test_expand_query_no_entities(self, expander):
        """Test expansion with no entities found."""
        with patch.object(expander.entity_extractor, 'extract_entities', return_value=[]):
            query = "simple query"
            expanded = expander.expand_query(query)
            
            # Should still include original
            assert len(expanded) == 1
            assert expanded[0] == query
    
    def test_get_synonyms_person_type(self, expander):
        """Test getting synonyms for person types."""
        # The method accesses LegalTerminology directly, so we test actual behavior
        synonyms = expander._get_synonyms("temporary_resident", EntityType.PERSON_TYPE)
        
        # Should return a list (may be empty or with synonyms)
        assert isinstance(synonyms, list)
    
    def test_get_synonyms_unknown_type(self, expander):
        """Test getting synonyms for unknown entity type."""
        synonyms = expander._get_synonyms("something", EntityType.DATE)
        assert synonyms == []


class TestParseLegalQueryFunction:
    """Tests for convenience function."""
    
    def test_parse_legal_query_basic(self):
        """Test parsing a legal query with convenience function."""
        query = "What is employment insurance?"
        
        result = parse_legal_query(query)
        
        assert isinstance(result, ParsedQuery)
        assert result.original_query == query
        assert result.intent in QueryIntent
    
    def test_parse_legal_query_with_spacy(self):
        """Test parsing with spaCy option."""
        query = "What is EI?"
        
        # Should not raise error even if spaCy not available
        result = parse_legal_query(query, use_spacy=False)
        
        assert isinstance(result, ParsedQuery)
    
    def test_parse_legal_query_empty(self):
        """Test parsing empty query."""
        result = parse_legal_query("")
        
        assert result.intent == QueryIntent.UNKNOWN
        assert result.intent_confidence == 0.0


class TestIntentPatternMatching:
    """Tests for intent pattern matching."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return LegalQueryParser(use_spacy=False)
    
    def test_search_patterns(self, parser):
        """Test search intent patterns."""
        test_cases = [
            "find regulations about privacy",
            "search for tax laws",
            "show me all rules about employment",
            "where can i find immigration policies"
        ]
        
        for query in test_cases:
            intent, _ = parser._classify_intent(query)
            assert intent == QueryIntent.SEARCH, f"Failed for: {query}"
    
    def test_compliance_patterns(self, parser):
        """Test compliance intent patterns."""
        test_cases = [
            "is my application compliant",
            "must i comply with regulations",
            "verify my submission meets requirements",
            "check if this is compliant"
        ]
        
        for query in test_cases:
            intent, _ = parser._classify_intent(query)
            assert intent == QueryIntent.COMPLIANCE, f"Failed for: {query}"
    
    def test_interpretation_patterns(self, parser):
        """Test interpretation intent patterns."""
        test_cases = [
            "what does section 5 mean",
            "explain the privacy act",
            "clarify this regulation",
            "how to understand clause 3"
        ]
        
        for query in test_cases:
            intent, _ = parser._classify_intent(query)
            assert intent == QueryIntent.INTERPRETATION, f"Failed for: {query}"
    
    def test_comparison_patterns(self, parser):
        """Test comparison intent patterns."""
        test_cases = [
            "compare EI and CPP",
            "what's the difference between permanent and temporary resident",
            "EI versus CPP benefits",
            "comparison of federal and provincial programs"
        ]
        
        for query in test_cases:
            intent, _ = parser._classify_intent(query)
            assert intent == QueryIntent.COMPARISON, f"Failed for: {query}"


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return LegalQueryParser(use_spacy=False)
    
    def test_very_long_query(self, parser):
        """Test handling very long query."""
        query = "Can a temporary resident who has been living in Canada for more than five years and has been working full-time with valid work permits apply for employment insurance benefits in the province of Ontario if they lose their job due to company restructuring?" * 5
        
        # Should not crash
        parsed = parser.parse_query(query)
        assert isinstance(parsed, ParsedQuery)
    
    def test_special_characters(self, parser):
        """Test query with special characters."""
        query = "What is EI? (Employment Insurance) - Benefits & Eligibility!"
        
        parsed = parser.parse_query(query)
        assert isinstance(parsed, ParsedQuery)
        assert parsed.normalized_query  # Should be normalized
    
    def test_unicode_characters(self, parser):
        """Test query with unicode characters."""
        query = "Qu'est-ce que l'assurance-emploi? Montréal, Québec"
        
        # Should not crash
        parsed = parser.parse_query(query)
        assert isinstance(parsed, ParsedQuery)
    
    def test_numbers_in_query(self, parser):
        """Test query with numbers."""
        query = "What are the requirements under Section 42 of Act 123?"
        
        parsed = parser.parse_query(query)
        assert isinstance(parsed, ParsedQuery)
    
    def test_multiple_question_marks(self, parser):
        """Test query with multiple question marks."""
        query = "What is EI??? How do I apply???"
        
        parsed = parser.parse_query(query)
        # Should normalize by removing trailing question marks
        # Note: The implementation only strips trailing '?', not internal ones
        assert not parsed.normalized_query.endswith("?")
    
    def test_all_stop_words(self, parser):
        """Test query composed entirely of stop words."""
        query = "is it the a of and by"
        
        parsed = parser.parse_query(query)
        # Keywords should be empty or very short
        assert len(parsed.keywords) <= 1
    
    def test_query_with_only_entities(self, parser):
        """Test query that's only entity names."""
        query = "Ontario Canada EI CPP"
        
        parsed = parser.parse_query(query)
        # Should still parse without crashing
        assert isinstance(parsed, ParsedQuery)
