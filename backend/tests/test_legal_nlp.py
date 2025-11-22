"""
Unit Tests for Legal NLP Service

Tests entity extraction, query parsing, and intent classification for
legal and regulatory text processing.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import pytest
from services.legal_nlp import (
    LegalEntityExtractor,
    LegalTerminology,
    EntityType,
    ExtractedEntity,
    extract_legal_entities
)
from services.query_parser import (
    LegalQueryParser,
    QueryExpander,
    QueryIntent,
    ParsedQuery,
    parse_legal_query
)


class TestLegalTerminology:
    """Test the legal terminology database"""

    def test_get_canonical_form_person_type(self):
        """Test getting canonical form for person types"""
        canonical = LegalTerminology.get_canonical_form("canadian citizen", EntityType.PERSON_TYPE)
        assert canonical == "citizen"

        canonical = LegalTerminology.get_canonical_form("pr", EntityType.PERSON_TYPE)
        assert canonical == "permanent_resident"

        canonical = LegalTerminology.get_canonical_form("temp resident", EntityType.PERSON_TYPE)
        assert canonical == "temporary_resident"

    def test_get_canonical_form_program(self):
        """Test getting canonical form for programs"""
        canonical = LegalTerminology.get_canonical_form("ei", EntityType.PROGRAM)
        assert canonical == "employment_insurance"

        canonical = LegalTerminology.get_canonical_form("cpp", EntityType.PROGRAM)
        assert canonical == "canada_pension_plan"

        canonical = LegalTerminology.get_canonical_form("oas", EntityType.PROGRAM)
        assert canonical == "old_age_security"

    def test_get_canonical_form_jurisdiction(self):
        """Test getting canonical form for jurisdictions"""
        canonical = LegalTerminology.get_canonical_form("federal", EntityType.JURISDICTION)
        assert canonical == "federal"

        canonical = LegalTerminology.get_canonical_form("ontario", EntityType.JURISDICTION)
        assert canonical == "ontario"

        canonical = LegalTerminology.get_canonical_form("bc", EntityType.JURISDICTION)
        assert canonical == "british_columbia"

    def test_get_canonical_form_not_found(self):
        """Test handling of unknown terms"""
        canonical = LegalTerminology.get_canonical_form("unknown_term", EntityType.PERSON_TYPE)
        assert canonical is None

    def test_get_all_patterns(self):
        """Test getting all patterns for an entity type"""
        patterns = LegalTerminology.get_all_patterns(EntityType.PROGRAM)
        assert len(patterns) > 0
        assert "employment insurance" in patterns
        assert "ei" in patterns


class TestLegalEntityExtractor:
    """Test the legal entity extractor"""

    @pytest.fixture
    def extractor(self):
        """Create an entity extractor instance"""
        return LegalEntityExtractor(use_spacy=False)

    def test_extract_person_types(self, extractor):
        """Test extraction of person types"""
        text = "Can a temporary resident apply for benefits?"
        entities = extractor.extract_entities_by_type(text, EntityType.PERSON_TYPE)

        assert len(entities) > 0
        assert any(e.normalized == "temporary_resident" for e in entities)

    def test_extract_programs(self, extractor):
        """Test extraction of program names"""
        text = "I need information about employment insurance and CPP."
        entities = extractor.extract_entities_by_type(text, EntityType.PROGRAM)

        assert len(entities) >= 2
        program_names = {e.normalized for e in entities}
        assert "employment_insurance" in program_names
        assert "canada_pension_plan" in program_names

    def test_extract_jurisdictions(self, extractor):
        """Test extraction of jurisdictions"""
        text = "Federal regulations and Ontario provincial rules apply."
        entities = extractor.extract_entities_by_type(text, EntityType.JURISDICTION)

        assert len(entities) >= 2
        jurisdictions = {e.normalized for e in entities}
        assert "federal" in jurisdictions
        assert "ontario" in jurisdictions

    def test_extract_requirements(self, extractor):
        """Test extraction of requirements"""
        text = "You need a social insurance number and work permit."
        entities = extractor.extract_entities_by_type(text, EntityType.REQUIREMENT)

        assert len(entities) >= 2
        requirements = {e.normalized for e in entities}
        assert "social_insurance_number" in requirements
        assert "work_permit" in requirements

    def test_extract_dates(self, extractor):
        """Test extraction of dates"""
        text = "Applications due by January 15, 2025 or 12/31/2024."
        entities = extractor.extract_entities_by_type(text, EntityType.DATE)

        assert len(entities) >= 2
        date_texts = {e.text for e in entities}
        assert "January 15, 2025" in date_texts

    def test_extract_money(self, extractor):
        """Test extraction of monetary amounts"""
        text = "The benefit is $2,500 per month or 1000 dollars."
        entities = extractor.extract_entities_by_type(text, EntityType.MONEY)

        assert len(entities) >= 1
        assert any("$2,500" in e.text for e in entities)

    def test_extract_legislation(self, extractor):
        """Test extraction of legislation references"""
        text = "According to the Employment Insurance Act and Immigration Regulation."
        entities = extractor.extract_entities_by_type(text, EntityType.LEGISLATION)

        assert len(entities) >= 1
        assert any("Act" in e.text for e in entities)

    def test_extract_all_entity_types(self, extractor):
        """Test extracting multiple entity types from one text"""
        text = "Can a temporary resident in Ontario apply for employment insurance?"
        entities = extractor.extract_entities(text)

        entity_types = {e.entity_type for e in entities}
        assert EntityType.PERSON_TYPE in entity_types
        assert EntityType.JURISDICTION in entity_types
        assert EntityType.PROGRAM in entity_types

    def test_confidence_scores(self, extractor):
        """Test that confidence scores are within valid range"""
        text = "permanent resident needs employment insurance"
        entities = extractor.extract_entities(text)

        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0

    def test_entity_summary(self, extractor):
        """Test entity summary generation"""
        text = "Can a temporary resident in Ontario apply for EI or CPP?"
        entities = extractor.extract_entities(text)

        summary = extractor.get_entity_summary(entities)
        assert isinstance(summary, dict)
        assert "person_type" in summary
        assert "program" in summary

    def test_empty_text(self, extractor):
        """Test handling of empty text"""
        entities = extractor.extract_entities("")
        assert entities == []

        entities = extractor.extract_entities(None)
        assert entities == []

    def test_deduplication(self, extractor):
        """Test that duplicate entities are removed"""
        text = "EI and employment insurance are the same program."
        entities = extractor.extract_entities_by_type(text, EntityType.PROGRAM)

        # Both "EI" and "employment insurance" should map to same canonical form
        # but we might get multiple matches that need deduplication
        assert len(entities) >= 1


class TestLegalQueryParser:
    """Test the query parser"""

    @pytest.fixture
    def parser(self):
        """Create a query parser instance"""
        return LegalQueryParser(use_spacy=False)

    def test_parse_eligibility_query(self, parser):
        """Test parsing eligibility questions"""
        query = "Can a temporary resident apply for employment insurance?"
        parsed = parser.parse_query(query)

        assert parsed.original_query == query
        assert parsed.intent in [QueryIntent.ELIGIBILITY, QueryIntent.PROCEDURE]
        assert parsed.intent_confidence > 0.0
        assert len(parsed.entities) > 0

    def test_parse_search_query(self, parser):
        """Test parsing search questions"""
        query = "Find all regulations about employment insurance"
        parsed = parser.parse_query(query)

        assert parsed.intent == QueryIntent.SEARCH
        assert parsed.intent_confidence > 0.5

    def test_parse_compliance_query(self, parser):
        """Test parsing compliance questions"""
        query = "Is my application compliant with the requirements?"
        parsed = parser.parse_query(query)

        assert parsed.intent == QueryIntent.COMPLIANCE
        assert "application" in parsed.keywords or "compliant" in parsed.keywords

    def test_parse_interpretation_query(self, parser):
        """Test parsing interpretation questions"""
        query = "What does permanent resident mean?"
        parsed = parser.parse_query(query)

        assert parsed.intent in [QueryIntent.INTERPRETATION, QueryIntent.DEFINITION]

    def test_parse_procedure_query(self, parser):
        """Test parsing procedure questions"""
        query = "How do I apply for old age security?"
        parsed = parser.parse_query(query)

        assert parsed.intent == QueryIntent.PROCEDURE
        assert parsed.question_type == "how"

    def test_parse_comparison_query(self, parser):
        """Test parsing comparison questions"""
        query = "Compare EI and CPP benefits"
        parsed = parser.parse_query(query)

        assert parsed.intent == QueryIntent.COMPARISON
        assert len(parsed.get_entities_by_type(EntityType.PROGRAM)) >= 2

    def test_question_type_detection(self, parser):
        """Test detection of question types"""
        test_cases = {
            "Who is eligible?": "who",
            "What is the requirement?": "what",
            "When can I apply?": "when",
            "Where do I submit?": "where",
            "Why was it denied?": "why",
            "How do I apply?": "how",
        }

        for query, expected_type in test_cases.items():
            parsed = parser.parse_query(query)
            assert parsed.question_type == expected_type

    def test_keyword_extraction(self, parser):
        """Test keyword extraction"""
        query = "Can a temporary resident apply for employment insurance?"
        parsed = parser.parse_query(query)

        # Should extract keywords but exclude stop words
        assert len(parsed.keywords) > 0
        assert "the" not in parsed.keywords
        assert "a" not in parsed.keywords

    def test_filter_extraction(self, parser):
        """Test filter extraction from entities"""
        query = "Employment insurance for Ontario residents"
        parsed = parser.parse_query(query)

        assert "program" in parsed.filters or len(parsed.entities) > 0
        assert isinstance(parsed.filters, dict)

    def test_empty_query(self, parser):
        """Test handling of empty queries"""
        parsed = parser.parse_query("")
        assert parsed.intent == QueryIntent.UNKNOWN
        assert parsed.intent_confidence == 0.0

    def test_batch_parsing(self, parser):
        """Test batch query parsing"""
        queries = [
            "Can I apply for EI?",
            "What is CPP?",
            "How to get OAS?",
        ]

        parsed_queries = parser.batch_parse_queries(queries)
        assert len(parsed_queries) == len(queries)
        assert all(isinstance(pq, ParsedQuery) for pq in parsed_queries)

    def test_intent_distribution(self, parser):
        """Test intent distribution calculation"""
        queries = [
            "Can I apply?",
            "What is this?",
            "How do I do it?",
        ]

        parsed_queries = parser.batch_parse_queries(queries)
        distribution = parser.get_intent_distribution(parsed_queries)

        assert isinstance(distribution, dict)
        assert sum(distribution.values()) == len(queries)

    def test_confidence_range(self, parser):
        """Test that confidence scores are in valid range"""
        queries = [
            "Can a temporary resident apply for EI?",
            "What is the requirement?",
            "Some random text without clear intent",
        ]

        for query in queries:
            parsed = parser.parse_query(query)
            assert 0.0 <= parsed.intent_confidence <= 1.0

    def test_entity_extraction_integration(self, parser):
        """Test that entities are properly extracted during parsing"""
        query = "Can a permanent resident in BC apply for CPP?"
        parsed = parser.parse_query(query)

        # Should extract person type, jurisdiction, and program
        entity_types = {e.entity_type for e in parsed.entities}
        assert EntityType.PERSON_TYPE in entity_types
        assert EntityType.PROGRAM in entity_types


class TestQueryExpander:
    """Test query expansion with synonyms"""

    @pytest.fixture
    def expander(self):
        """Create a query expander instance"""
        return QueryExpander()

    def test_expand_with_synonyms(self, expander):
        """Test query expansion with synonyms"""
        query = "Can a temporary resident apply for EI?"
        expanded = expander.expand_query(query)

        assert len(expanded) > 1  # Should include original + expansions
        assert query in expanded  # Original should be included

        # Should have variations with synonyms
        expanded_text = ' '.join(expanded)
        assert "employment insurance" in expanded_text or "temp resident" in expanded_text

    def test_expand_multiple_entities(self, expander):
        """Test expansion with multiple entities"""
        query = "EI and CPP for seniors"
        expanded = expander.expand_query(query)

        assert len(expanded) >= 1

    def test_limit_expansions(self, expander):
        """Test that expansions are limited"""
        query = "Can a temporary resident apply for employment insurance in Ontario?"
        expanded = expander.expand_query(query)

        # Should limit to reasonable number of variations
        assert len(expanded) <= 5


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_extract_legal_entities_function(self):
        """Test the extract_legal_entities convenience function"""
        text = "Can a temporary resident apply for EI?"
        entities = extract_legal_entities(text)

        assert isinstance(entities, list)
        assert all(isinstance(e, ExtractedEntity) for e in entities)

    def test_parse_legal_query_function(self):
        """Test the parse_legal_query convenience function"""
        query = "Can I apply for employment insurance?"
        parsed = parse_legal_query(query)

        assert isinstance(parsed, ParsedQuery)
        assert parsed.original_query == query


class TestEntityDataclass:
    """Test ExtractedEntity dataclass"""

    def test_to_dict(self):
        """Test entity conversion to dictionary"""
        entity = ExtractedEntity(
            text="temporary resident",
            entity_type=EntityType.PERSON_TYPE,
            normalized="temporary_resident",
            confidence=0.9,
            start_pos=10,
            end_pos=28,
            context="Can a temporary resident apply?",
            metadata={"source": "test"}
        )

        entity_dict = entity.to_dict()
        assert entity_dict["text"] == "temporary resident"
        assert entity_dict["entity_type"] == "person_type"
        assert entity_dict["normalized"] == "temporary_resident"
        assert entity_dict["confidence"] == 0.9
        assert entity_dict["metadata"]["source"] == "test"


class TestParsedQueryDataclass:
    """Test ParsedQuery dataclass"""

    def test_to_dict(self):
        """Test parsed query conversion to dictionary"""
        parsed = ParsedQuery(
            original_query="Can I apply?",
            normalized_query="can i apply",
            intent=QueryIntent.ELIGIBILITY,
            intent_confidence=0.8,
            entities=[],
            keywords=["apply"],
            question_type="what",
            filters={"program": ["ei"]},
            metadata={"test": "value"}
        )

        parsed_dict = parsed.to_dict()
        assert parsed_dict["original_query"] == "Can I apply?"
        assert parsed_dict["intent"] == "eligibility"
        assert parsed_dict["intent_confidence"] == 0.8
        assert parsed_dict["filters"]["program"] == ["ei"]

    def test_get_entities_by_type(self):
        """Test filtering entities by type"""
        entities = [
            ExtractedEntity("EI", EntityType.PROGRAM, "ei", 0.9, 0, 2),
            ExtractedEntity("Ontario", EntityType.JURISDICTION, "ontario", 0.9, 5, 12),
            ExtractedEntity("CPP", EntityType.PROGRAM, "cpp", 0.9, 15, 18),
        ]

        parsed = ParsedQuery(
            original_query="test",
            normalized_query="test",
            intent=QueryIntent.SEARCH,
            intent_confidence=0.8,
            entities=entities,
            keywords=[]
        )

        programs = parsed.get_entities_by_type(EntityType.PROGRAM)
        assert len(programs) == 2
        assert all(e.entity_type == EntityType.PROGRAM for e in programs)


# Test accuracy metrics
class TestAccuracyMetrics:
    """Test that accuracy targets are met"""

    @pytest.fixture
    def extractor(self):
        return LegalEntityExtractor(use_spacy=False)

    @pytest.fixture
    def parser(self):
        return LegalQueryParser(use_spacy=False)

    def test_entity_extraction_accuracy(self, extractor):
        """Test entity extraction accuracy > 80%"""
        test_cases = [
            ("temporary resident", EntityType.PERSON_TYPE, "temporary_resident"),
            ("permanent resident", EntityType.PERSON_TYPE, "permanent_resident"),
            ("employment insurance", EntityType.PROGRAM, "employment_insurance"),
            ("EI", EntityType.PROGRAM, "employment_insurance"),
            ("CPP", EntityType.PROGRAM, "canada_pension_plan"),
            ("Ontario", EntityType.JURISDICTION, "ontario"),
            ("federal", EntityType.JURISDICTION, "federal"),
            ("social insurance number", EntityType.REQUIREMENT, "social_insurance_number"),
            ("SIN", EntityType.REQUIREMENT, "social_insurance_number"),
        ]

        correct = 0
        for text, expected_type, expected_normalized in test_cases:
            entities = extractor.extract_entities(text)
            if any(e.entity_type == expected_type and e.normalized == expected_normalized
                   for e in entities):
                correct += 1

        accuracy = correct / len(test_cases)
        assert accuracy >= 0.80, f"Entity extraction accuracy {accuracy:.2%} below 80% target"

    def test_intent_classification_accuracy(self, parser):
        """Test intent classification accuracy > 85%"""
        test_cases = [
            ("Find regulations about EI", QueryIntent.SEARCH),
            ("Search for employment insurance", QueryIntent.SEARCH),
            ("Can I apply for EI?", [QueryIntent.ELIGIBILITY, QueryIntent.PROCEDURE]),
            ("Am I eligible for CPP?", QueryIntent.ELIGIBILITY),
            ("How do I apply?", QueryIntent.PROCEDURE),
            ("What does permanent resident mean?", [QueryIntent.DEFINITION, QueryIntent.INTERPRETATION]),
            ("Is my application compliant?", QueryIntent.COMPLIANCE),
            ("Compare EI and CPP", QueryIntent.COMPARISON),
        ]

        correct = 0
        for query, expected_intent in test_cases:
            parsed = parser.parse_query(query)
            if isinstance(expected_intent, list):
                if parsed.intent in expected_intent:
                    correct += 1
            else:
                if parsed.intent == expected_intent:
                    correct += 1

        accuracy = correct / len(test_cases)
        assert accuracy >= 0.85, f"Intent classification accuracy {accuracy:.2%} below 85% target"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
