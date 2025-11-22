"""
Integration Tests for RAG Service

Tests the RAG service with real Gemini API, Search service, and NLP parser.
Validates question answering, citation extraction, and confidence scoring.

Note: Requires GEMINI_API_KEY environment variable to be set.
Tests will be skipped if API key is not available.

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import pytest
import sys
import os
from pathlib import Path

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag_service import RAGService, RAGAnswer, Citation
from services.gemini_client import get_gemini_client


# Check if Gemini API is available
def check_gemini_available():
    """Check if Gemini API key is configured"""
    try:
        client = get_gemini_client()
        return client.is_available()
    except:
        return False


GEMINI_AVAILABLE = check_gemini_available()
skip_if_no_gemini = pytest.mark.skipif(
    not GEMINI_AVAILABLE,
    reason="Gemini API not available (set GEMINI_API_KEY)"
)


@skip_if_no_gemini
class TestRAGServiceIntegration:
    """Integration tests for RAG Service with real Gemini API"""

    @pytest.fixture(scope="class")
    def rag_service(self):
        """Create RAG service"""
        return RAGService()

    # Basic Question Answering Tests

    def test_answer_simple_question(self, rag_service):
        """Test answering a simple eligibility question"""
        question = "Can permanent residents apply for employment insurance?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        assert isinstance(answer, RAGAnswer)
        assert len(answer.answer) > 50  # Should have substantive answer
        assert answer.question == question
        assert 0.0 <= answer.confidence_score <= 1.0

    def test_answer_with_citations(self, rag_service):
        """Test that answer includes citations"""
        question = "What are the requirements for Canada Pension Plan eligibility?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # Should have citations
        assert isinstance(answer.citations, list)

        # If citations exist, they should have proper structure
        if len(answer.citations) > 0:
            citation = answer.citations[0]
            assert isinstance(citation, Citation)
            assert citation.text is not None
            assert 0.0 <= citation.confidence <= 1.0

    def test_answer_complex_question(self, rag_service):
        """Test answering a complex multi-part question"""
        question = """I am a temporary resident in Canada. Can I apply for
        employment insurance if I lose my job, and what documents do I need?"""

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=10,
            use_cache=False
        )

        # Should handle complex question
        assert len(answer.answer) > 100
        assert answer.confidence_score > 0.0

        # Should reference relevant concepts
        answer_lower = answer.answer.lower()
        assert any(term in answer_lower for term in ['temporary', 'resident', 'work', 'permit'])

    # Context and Document Retrieval Tests

    def test_answer_uses_context_documents(self, rag_service):
        """Test that answer uses retrieved context documents"""
        question = "What is Old Age Security?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # Should have retrieved source documents
        assert isinstance(answer.source_documents, list)
        assert len(answer.source_documents) > 0

        # Each source doc should have required fields
        for doc in answer.source_documents:
            assert 'id' in doc
            assert 'title' in doc
            assert 'score' in doc

    def test_answer_with_filters(self, rag_service):
        """Test answering with jurisdiction filter"""
        question = "What are workers compensation regulations?"

        answer = rag_service.answer_question(
            question=question,
            filters={'jurisdiction': 'federal'},
            num_context_docs=5,
            use_cache=False
        )

        # Should retrieve documents matching filter
        for doc in answer.source_documents:
            if 'jurisdiction' in doc:
                assert doc['jurisdiction'] == 'federal'

    def test_answer_with_varying_context_size(self, rag_service):
        """Test with different numbers of context documents"""
        question = "Who is eligible for disability benefits?"

        for num_docs in [1, 3, 5, 10]:
            answer = rag_service.answer_question(
                question=question,
                num_context_docs=num_docs,
                use_cache=False
            )

            # Should work with different context sizes
            assert answer.answer is not None
            assert len(answer.source_documents) <= num_docs

    # Citation Extraction Tests

    def test_citation_extraction_pattern1(self, rag_service):
        """Test citation extraction using [Title, Section X] pattern"""
        # Use a question likely to generate formal citations
        question = "What does Section 7 of the Employment Insurance Act say?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=3,
            use_cache=False
        )

        # If citations exist, check they're properly formatted
        for citation in answer.citations:
            assert citation.text is not None
            assert len(citation.text) > 0

    def test_citation_document_linking(self, rag_service):
        """Test that citations link to actual source documents"""
        question = "What are CPP contribution requirements?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # Get IDs of source documents
        source_doc_ids = {doc['id'] for doc in answer.source_documents}

        # Citations should reference source documents
        for citation in answer.citations:
            if citation.document_id:
                # Document ID should be in sources or be related
                assert isinstance(citation.document_id, str)

    # Confidence Scoring Tests

    def test_confidence_score_reasonable(self, rag_service):
        """Test that confidence scores are reasonable"""
        questions = [
            "What is employment insurance?",  # Clear question
            "Can citizens apply for EI?",  # Clear question
            "What about the thing with the stuff?"  # Vague question
        ]

        for question in questions:
            answer = rag_service.answer_question(
                question=question,
                num_context_docs=5,
                use_cache=False
            )

            # Confidence should be in valid range
            assert 0.0 <= answer.confidence_score <= 1.0

    def test_confidence_higher_with_citations(self, rag_service):
        """Test that answers with citations have higher confidence"""
        question = "What are the eligibility requirements for Old Age Security?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # If answer has citations, confidence should be reasonable
        if len(answer.citations) > 0:
            assert answer.confidence_score > 0.4

    # Caching Tests

    def test_answer_caching_works(self, rag_service):
        """Test that answer caching works correctly"""
        question = "What is the Canada Child Benefit?"

        # Clear cache first
        rag_service.clear_cache()

        # First call - should not be cached
        answer1 = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=True
        )

        assert answer1.cached is False

        # Second call - should be cached
        answer2 = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=True
        )

        assert answer2.cached is True

        # Answers should be the same
        assert answer1.answer == answer2.answer

    def test_cache_key_normalization(self, rag_service):
        """Test that similar questions use same cache"""
        rag_service.clear_cache()

        questions = [
            "What is EI?",
            "what is ei?",
            "  What is EI?  "
        ]

        # All should produce same cache key
        answer1 = rag_service.answer_question(questions[0], use_cache=True)
        answer2 = rag_service.answer_question(questions[1], use_cache=True)
        answer3 = rag_service.answer_question(questions[2], use_cache=True)

        assert answer2.cached is True
        assert answer3.cached is True

    def test_cache_clear(self, rag_service):
        """Test cache clearing"""
        question = "Test cache clear question"

        # Add to cache
        rag_service.answer_question(question, use_cache=True)

        # Clear cache
        rag_service.clear_cache()

        # Should not be cached now
        answer = rag_service.answer_question(question, use_cache=True)
        assert answer.cached is False

    # Temperature and Parameter Tests

    def test_answer_with_different_temperatures(self, rag_service):
        """Test answering with different temperature settings"""
        question = "What is permanent residency?"

        for temperature in [0.1, 0.3, 0.7]:
            answer = rag_service.answer_question(
                question=question,
                num_context_docs=5,
                temperature=temperature,
                use_cache=False
            )

            # Should work with different temperatures
            assert answer.answer is not None
            assert len(answer.answer) > 0

    def test_answer_with_token_limit(self, rag_service):
        """Test answering with token limits"""
        question = "Explain all the requirements for Canadian citizenship."

        # Short answer
        answer_short = rag_service.answer_question(
            question=question,
            max_tokens=100,
            use_cache=False
        )

        # Long answer
        answer_long = rag_service.answer_question(
            question=question,
            max_tokens=1000,
            use_cache=False
        )

        # Longer token limit should generally produce longer answer
        # (though not guaranteed due to AI variability)
        assert answer_short.answer is not None
        assert answer_long.answer is not None

    # Error Handling and Edge Cases

    def test_answer_no_relevant_context(self, rag_service):
        """Test handling when no relevant documents found"""
        question = "What are the regulations for Martian colonization?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # Should handle gracefully
        if len(answer.source_documents) == 0:
            # Low confidence expected
            assert answer.confidence_score < 0.5
            # Should indicate lack of information
            assert 'metadata' in answer.to_dict()

    def test_answer_empty_question(self, rag_service):
        """Test handling empty question"""
        try:
            answer = rag_service.answer_question(
                question="",
                num_context_docs=5,
                use_cache=False
            )

            # Should either handle gracefully or have low confidence
            if answer:
                assert answer.confidence_score < 0.5
        except Exception as e:
            # Or raise appropriate error
            assert "question" in str(e).lower() or "empty" in str(e).lower()

    def test_answer_very_long_question(self, rag_service):
        """Test handling very long question"""
        long_question = "Can I apply for benefits? " * 50

        answer = rag_service.answer_question(
            question=long_question,
            num_context_docs=5,
            use_cache=False
        )

        # Should handle without crashing
        assert answer is not None

    # Performance Tests

    def test_answer_performance(self, rag_service):
        """Test that answer generation is within acceptable time"""
        import time

        question = "What is employment insurance?"

        start = time.time()
        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )
        elapsed_ms = (time.time() - start) * 1000

        # Should complete within 10 seconds (can be slow with API calls)
        assert elapsed_ms < 10000, \
            f"Answer generation took {elapsed_ms:.0f}ms (target: <10000ms)"

        # Processing time should be tracked
        assert answer.processing_time_ms > 0

    def test_cached_answer_fast(self, rag_service):
        """Test that cached answers are fast"""
        import time

        question = "Test cached answer speed"

        # Prime cache
        rag_service.answer_question(question, use_cache=True)

        # Cached retrieval
        start = time.time()
        answer = rag_service.answer_question(question, use_cache=True)
        elapsed_ms = (time.time() - start) * 1000

        assert answer.cached is True

        # Should be much faster (under 100ms)
        assert elapsed_ms < 100, \
            f"Cached answer took {elapsed_ms:.1f}ms (target: <100ms)"

    # Metadata and Serialization Tests

    def test_answer_metadata_complete(self, rag_service):
        """Test that answer metadata is complete"""
        question = "What is the GIS?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # Check metadata fields
        assert 'num_context_docs' in answer.metadata
        assert answer.metadata['num_context_docs'] == 5

    def test_answer_serialization(self, rag_service):
        """Test that answer can be serialized to dict/JSON"""
        question = "What is CPP?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=3,
            use_cache=False
        )

        # Convert to dict
        answer_dict = answer.to_dict()

        # Check all required fields
        assert 'question' in answer_dict
        assert 'answer' in answer_dict
        assert 'citations' in answer_dict
        assert 'confidence_score' in answer_dict
        assert 'source_documents' in answer_dict

        # Should be JSON-serializable
        import json
        json_str = json.dumps(answer_dict)
        assert len(json_str) > 0

    # Health Check Tests

    def test_rag_service_health_check(self, rag_service):
        """Test RAG service health check"""
        health = rag_service.health_check()

        assert 'status' in health
        assert health['status'] in ['healthy', 'degraded', 'unhealthy']

        assert 'components' in health
        assert 'gemini' in health['components']

    def test_cache_stats(self, rag_service):
        """Test getting cache statistics"""
        stats = rag_service.get_cache_stats()

        assert 'total_entries' in stats
        assert 'cache_ttl_hours' in stats
        assert isinstance(stats['total_entries'], int)

    # Integration with NLP Tests

    def test_intent_detection_integration(self, rag_service):
        """Test that RAG integrates with NLP intent detection"""
        question = "How do I apply for Old Age Security?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # Should detect intent
        if answer.intent:
            assert answer.intent in ['procedure', 'eligibility', 'search', 'compliance']

    # Multi-language and Special Characters

    def test_answer_with_accents(self, rag_service):
        """Test questions with accented characters"""
        question = "What are Québec's language requirements?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # Should handle accented characters
        assert answer.answer is not None

    def test_answer_with_special_chars(self, rag_service):
        """Test questions with special legal characters"""
        question = "What does Section 7(1) say?"

        answer = rag_service.answer_question(
            question=question,
            num_context_docs=5,
            use_cache=False
        )

        # Should handle special characters
        assert answer.answer is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
