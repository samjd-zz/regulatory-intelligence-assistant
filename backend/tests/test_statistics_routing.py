"""
Test Statistics Query Routing

This test verifies that statistics/count questions are routed to direct
database queries instead of RAG, providing accurate answers.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-12-03
"""

import pytest
from services.rag_service import RAGService
from services.query_parser import LegalQueryParser, QueryIntent
from services.statistics_service import StatisticsService


class TestStatisticsRouting:
    """Test statistics query routing feature"""
    
    def test_query_parser_detects_statistics_intent(self):
        """Test that query parser detects STATISTICS intent for count questions"""
        parser = LegalQueryParser(use_spacy=False)
        
        # Test various count questions
        test_questions = [
            "How many Canadian federal acts are in the database?",
            "What is the total number of regulations?",
            "Count the documents in the system",
            "How many employment insurance regulations exist?",
            "What's the total count of laws?",
            "Number of documents by jurisdiction",
        ]
        
        for question in test_questions:
            parsed = parser.parse_query(question)
            assert parsed.intent == QueryIntent.STATISTICS, (
                f"Expected STATISTICS intent for: {question}, "
                f"but got: {parsed.intent}"
            )
    
    def test_rag_service_routes_to_database(self):
        """Test that RAG service routes statistics questions to database"""
        rag = RAGService()
        
        question = "How many documents are in the database?"
        
        # Answer the question
        answer = rag.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )
        
        # Verify it was answered by database query
        assert answer.intent == "statistics"
        assert answer.metadata.get("method") == "database_query"
        assert answer.metadata.get("bypassed_rag") == True
        assert answer.confidence_score >= 0.9  # High confidence for DB queries
        
        # Verify answer contains numeric information
        assert any(char.isdigit() for char in answer.answer), (
            "Statistics answer should contain numbers"
        )
    
    def test_statistics_service_returns_accurate_counts(self):
        """Test that statistics service returns database counts"""
        stats_service = StatisticsService()
        
        # Get total documents
        total = stats_service.get_total_documents()
        
        assert "total_searchable_documents" in total
        assert "total_regulations" in total
        assert isinstance(total["total_searchable_documents"], int)
        assert isinstance(total["total_regulations"], int)
        assert total["total_searchable_documents"] >= 0
        assert total["total_regulations"] >= 0
    
    def test_statistics_with_filters(self):
        """Test statistics with filters applied"""
        stats_service = StatisticsService()
        
        # Test with jurisdiction filter
        filtered = stats_service.get_total_documents(
            filters={"jurisdiction": "federal"}
        )
        
        assert "total_searchable_documents" in filtered
        assert "filters_applied" in filtered
        assert filtered["filters_applied"]["jurisdiction"] == "federal"
    
    def test_formatted_statistics_answer(self):
        """Test that statistics answers are formatted properly"""
        stats_service = StatisticsService()
        
        question = "How many regulations are in the database?"
        stats = stats_service.get_database_summary()
        
        answer = stats_service.format_statistics_answer(question, stats)
        
        # Answer should be a string with content
        assert isinstance(answer, str)
        assert len(answer) > 0
        
        # Should contain numbers
        assert any(char.isdigit() for char in answer)
        
        # Should mention documents or regulations
        assert any(word in answer.lower() for word in [
            "document", "regulation", "act"
        ])
    
    def test_non_statistics_questions_use_rag(self):
        """Test that non-statistics questions still use RAG"""
        parser = LegalQueryParser(use_spacy=False)
        
        # These should NOT be statistics questions
        non_stats_questions = [
            "Can a temporary resident apply for employment insurance?",
            "What is the eligibility criteria for CPP?",
            "Explain the rules for foreign workers",
        ]
        
        for question in non_stats_questions:
            parsed = parser.parse_query(question)
            assert parsed.intent != QueryIntent.STATISTICS, (
                f"Question should not be STATISTICS: {question}"
            )
    
    def test_edge_cases(self):
        """Test edge cases for statistics routing"""
        parser = LegalQueryParser(use_spacy=False)
        
        # Question with "how many" but not really asking for count
        question = "How many days do I have to apply for EI?"
        parsed = parser.parse_query(question)
        
        # This should probably not route to statistics
        # (depends on detection patterns - this is a content question, not a count)
        assert parsed.intent != QueryIntent.STATISTICS, (
            "Question about 'how many days' should not be STATISTICS intent"
        )


if __name__ == "__main__":
    # Run tests
    print("=" * 80)
    print("Testing Statistics Query Routing")
    print("=" * 80)
    
    test = TestStatisticsRouting()
    
    print("\n1. Testing Query Parser Intent Detection...")
    try:
        test.test_query_parser_detects_statistics_intent()
        print("   ✓ PASSED: Query parser correctly detects STATISTICS intent")
    except AssertionError as e:
        print(f"   ✗ FAILED: {e}")
    
    print("\n2. Testing RAG Service Routing...")
    try:
        test.test_rag_service_routes_to_database()
        print("   ✓ PASSED: RAG service routes statistics to database")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    
    print("\n3. Testing Statistics Service Accuracy...")
    try:
        test.test_statistics_service_returns_accurate_counts()
        print("   ✓ PASSED: Statistics service returns accurate counts")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    
    print("\n4. Testing Filtered Statistics...")
    try:
        test.test_statistics_with_filters()
        print("   ✓ PASSED: Statistics work with filters")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    
    print("\n5. Testing Formatted Answers...")
    try:
        test.test_formatted_statistics_answer()
        print("   ✓ PASSED: Statistics answers are formatted correctly")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    
    print("\n6. Testing Non-Statistics Questions...")
    try:
        test.test_non_statistics_questions_use_rag()
        print("   ✓ PASSED: Non-statistics questions still use RAG")
    except Exception as e:
        print(f"   ✗ FAILED: {e}")
    
    print("\n" + "=" * 80)
    print("Test Suite Complete!")
    print("=" * 80)
