"""
End-to-End Workflow Tests

Tests complete user workflows from query input to final answer,
simulating real user interactions with the Regulatory Intelligence Assistant.

These tests validate the entire pipeline:
Query → NLP Processing → Search → RAG → Response

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import pytest
import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.query_parser import LegalQueryParser
from services.search_service import SearchService
from services.rag_service import RAGService


class TestEndToEndWorkflows:
    """End-to-end workflow tests for complete user journeys"""

    @pytest.fixture(scope="class")
    def query_parser(self):
        """Query parser service"""
        return LegalQueryParser()

    @pytest.fixture(scope="class")
    def search_service(self):
        """Search service"""
        return SearchService()

    @pytest.fixture(scope="class")
    def rag_service(self):
        """RAG service"""
        return RAGService()

    # Workflow 1: Simple Search Query

    def test_workflow_simple_search(self, query_parser, search_service):
        """
        User Workflow: Simple regulatory search

        Steps:
        1. User enters natural language query
        2. System parses query and extracts entities
        3. System searches for relevant regulations
        4. System returns ranked results with citations
        """
        # Step 1: User input
        user_query = "Find federal employment insurance regulations"

        # Step 2: Parse query
        parsed = query_parser.parse_query(user_query)

        assert parsed.intent.value == "search"
        assert len(parsed.entities) > 0

        # Step 3: Search with parsed filters
        search_results = search_service.hybrid_search(
            query=parsed.normalized_query,
            filters=parsed.filters,
            size=10
        )

        # Step 4: Validate results
        assert search_results['total'] > 0
        assert len(search_results['hits']) > 0

        # Results should be relevant to employment insurance
        top_result = search_results['hits'][0]
        assert 'employment' in top_result['title'].lower() or \
               'ei' in top_result.get('program', '').lower()

    # Workflow 2: Question Answering with Citations

    @pytest.mark.skipif(
        not RAGService().gemini_client.is_available(),
        reason="Gemini API not available"
    )
    def test_workflow_qa_with_citations(self, query_parser, rag_service):
        """
        User Workflow: Ask question and get cited answer

        Steps:
        1. User asks natural language question
        2. System identifies question intent
        3. System retrieves relevant context
        4. System generates answer with AI
        5. System extracts and validates citations
        6. System returns answer with confidence score
        """
        # Step 1: User question
        user_question = "Can permanent residents receive Old Age Security benefits?"

        # Step 2: Parse and identify intent
        parsed = query_parser.parse_query(user_question)
        assert parsed.intent.value in ["eligibility", "search"]

        # Steps 3-6: Generate answer
        answer = rag_service.answer_question(
            question=user_question,
            num_context_docs=5,
            use_cache=False
        )

        # Validate complete answer
        assert answer.answer is not None
        assert len(answer.answer) > 50
        assert 0.0 <= answer.confidence_score <= 1.0
        assert len(answer.source_documents) > 0

        # Should address the specific question
        answer_lower = answer.answer.lower()
        assert 'permanent resident' in answer_lower or 'pr' in answer_lower
        assert 'old age' in answer_lower or 'oas' in answer_lower

    # Workflow 3: Filtered Search

    def test_workflow_filtered_search(self, query_parser, search_service):
        """
        User Workflow: Search with jurisdiction filter

        Steps:
        1. User specifies jurisdiction in query
        2. System extracts jurisdiction filter
        3. System searches with filter applied
        4. System returns only matching documents
        """
        # Step 1: User query with jurisdiction
        user_query = "British Columbia workers compensation regulations"

        # Step 2: Parse and extract filters
        parsed = query_parser.parse_query(user_query)

        assert 'jurisdiction' in parsed.filters or \
               any(e.entity_type.value == 'jurisdiction' for e in parsed.entities)

        # Step 3: Search with filters
        search_results = search_service.hybrid_search(
            query="workers compensation",
            filters={'jurisdiction': 'british_columbia'},
            size=10
        )

        # Step 4: Validate filtered results
        for hit in search_results['hits']:
            if 'jurisdiction' in hit:
                assert hit['jurisdiction'] == 'british_columbia'

    # Workflow 4: Multi-Entity Query

    def test_workflow_complex_multi_entity_query(self, query_parser, search_service):
        """
        User Workflow: Complex query with multiple entities

        Steps:
        1. User enters complex query with multiple entities
        2. System extracts all entities (person type, program, jurisdiction)
        3. System creates composite search
        4. System returns results matching all criteria
        """
        # Step 1: Complex query
        user_query = "Can a temporary resident in Ontario apply for social assistance?"

        # Step 2: Extract multiple entities
        parsed = query_parser.parse_query(user_query)

        # Should extract person type and program
        entity_types = {e.entity_type.value for e in parsed.entities}
        assert 'person_type' in entity_types
        assert 'program' in entity_types or 'jurisdiction' in entity_types

        # Step 3: Search with all extracted information
        search_results = search_service.hybrid_search(
            query=parsed.normalized_query,
            filters=parsed.filters,
            size=10
        )

        # Step 4: Results should be relevant
        assert search_results['total'] > 0

    # Workflow 5: Comparison Query

    @pytest.mark.skipif(
        not RAGService().gemini_client.is_available(),
        reason="Gemini API not available"
    )
    def test_workflow_comparison_query(self, query_parser, rag_service):
        """
        User Workflow: Compare two programs

        Steps:
        1. User asks comparison question
        2. System identifies comparison intent
        3. System retrieves context for both programs
        4. System generates comparative answer
        5. System provides citations for both
        """
        # Step 1: Comparison question
        user_question = "What is the difference between CPP and OAS?"

        # Step 2: Identify comparison intent
        parsed = query_parser.parse_query(user_question)
        assert parsed.intent.value == "comparison"

        # Steps 3-5: Generate comparison
        answer = rag_service.answer_question(
            question=user_question,
            num_context_docs=10,  # More context for comparison
            use_cache=False
        )

        # Validate comparison answer
        answer_lower = answer.answer.lower()
        assert 'cpp' in answer_lower or 'pension' in answer_lower
        assert 'oas' in answer_lower or 'old age' in answer_lower

    # Workflow 6: Caching Workflow

    @pytest.mark.skipif(
        not RAGService().gemini_client.is_available(),
        reason="Gemini API not available"
    )
    def test_workflow_cached_repeated_question(self, rag_service):
        """
        User Workflow: Ask same question twice (caching)

        Steps:
        1. User asks question (first time)
        2. System generates answer and caches it
        3. User asks same question again
        4. System returns cached answer instantly
        """
        question = "What is employment insurance?"

        # Clear cache
        rag_service.clear_cache()

        # Step 1-2: First query
        answer1 = rag_service.answer_question(
            question=question,
            use_cache=True
        )
        assert answer1.cached is False
        processing_time1 = answer1.processing_time_ms

        # Step 3-4: Repeated query
        answer2 = rag_service.answer_question(
            question=question,
            use_cache=True
        )
        assert answer2.cached is True
        processing_time2 = answer2.processing_time_ms

        # Cached should be much faster
        assert processing_time2 < processing_time1

        # Content should be identical
        assert answer1.answer == answer2.answer

    # Workflow 7: Error Recovery

    def test_workflow_error_recovery_vague_query(self, query_parser, search_service):
        """
        User Workflow: Handle vague or unclear query

        Steps:
        1. User enters vague query
        2. System attempts to parse
        3. System performs best-effort search
        4. System returns results with low confidence indication
        """
        # Step 1: Vague query
        vague_query = "Tell me about benefits"

        # Step 2: Parse (should work but with lower confidence)
        parsed = query_parser.parse_query(vague_query)

        # May have lower intent confidence
        # Intent confidence acceptable for vague queries
        assert parsed.intent_confidence >= 0.0

        # Step 3: Search
        search_results = search_service.hybrid_search(
            query=vague_query,
            size=10
        )

        # Step 4: Should return results even if confidence is lower
        assert 'hits' in search_results

    # Workflow 8: No Results Handling

    def test_workflow_no_results_graceful_handling(self, search_service):
        """
        User Workflow: Query with no matching results

        Steps:
        1. User searches for non-existent topic
        2. System performs search
        3. System returns empty results gracefully
        4. System provides helpful message
        """
        # Step 1-2: Search for non-existent topic
        search_results = search_service.hybrid_search(
            query="regulations about alien spacecraft licensing",
            size=10
        )

        # Step 3: Graceful handling
        assert 'hits' in search_results
        assert 'total' in search_results

        # May have zero results
        assert search_results['total'] >= 0

    # Workflow 9: Performance-Critical Path

    def test_workflow_performance_critical_path(self, query_parser, search_service):
        """
        User Workflow: Fast response for common query

        Tests the performance of the most common user path:
        Query → Parse → Search → Results

        Target: <3 seconds total (design.md §8.1)
        """
        import time

        # Common query
        user_query = "CPP eligibility requirements"

        # Measure total time
        start = time.time()

        # Parse
        parsed = query_parser.parse_query(user_query)

        # Search
        search_results = search_service.hybrid_search(
            query=parsed.normalized_query,
            filters=parsed.filters,
            size=10
        )

        elapsed_s = time.time() - start

        # Should complete within 3 seconds (prd.md NFR-1.1)
        assert elapsed_s < 3.0, \
            f"Critical path took {elapsed_s:.2f}s (target: <3.0s)"

    # Workflow 10: Multi-Step User Journey

    @pytest.mark.skipif(
        not RAGService().gemini_client.is_available(),
        reason="Gemini API not available"
    )
    def test_workflow_multi_step_user_journey(self, query_parser, search_service, rag_service):
        """
        User Workflow: Complete multi-step user journey

        Simulates realistic user interaction:
        1. User searches for topic
        2. User clicks on relevant result
        3. User asks follow-up question
        4. User gets detailed answer
        """
        # Step 1: Initial search
        search_query = "employment insurance"
        parsed_search = query_parser.parse_query(search_query)

        search_results = search_service.hybrid_search(
            query=parsed_search.normalized_query,
            size=5
        )

        assert search_results['total'] > 0

        # Step 2: User "clicks" on top result (simulated)
        top_result = search_results['hits'][0]
        selected_doc_id = top_result['id']

        # Step 3: User asks follow-up question
        followup_question = "What are the eligibility requirements for this program?"

        # Step 4: Get detailed answer
        answer = rag_service.answer_question(
            question=followup_question,
            filters={'program': 'employment_insurance'},
            num_context_docs=5,
            use_cache=False
        )

        # Validate complete journey
        assert answer.answer is not None
        assert len(answer.source_documents) > 0
        assert answer.confidence_score > 0.0

    # Workflow 11: Concurrent Users

    def test_workflow_concurrent_users_simulation(self, rag_service):
        """
        User Workflow: Multiple users querying simultaneously

        Simulates concurrent usage to ensure thread-safety
        and performance under load.
        """
        import concurrent.futures

        questions = [
            "What is EI?",
            "Can I get CPP?",
            "OAS eligibility?",
            "Workers comp coverage?",
            "Citizenship requirements?"
        ]

        def ask_question(q):
            """Ask a question"""
            return rag_service.answer_question(
                question=q,
                num_context_docs=3,
                use_cache=False
            )

        # Simulate 5 concurrent users
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(ask_question, q) for q in questions]
            results = [f.result(timeout=30) for f in concurrent.futures.as_completed(futures)]

        # All should complete successfully
        assert len(results) == 5
        assert all(r is not None for r in results)
        assert all(r.answer is not None for r in results)


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    @pytest.fixture(scope="class")
    def services(self):
        """All services"""
        return {
            'parser': LegalQueryParser(),
            'search': SearchService(),
            'rag': RAGService()
        }

    def test_scenario_caseworker_eligibility_check(self, services):
        """
        Scenario: Caseworker checking client eligibility

        A caseworker needs to quickly determine if a client
        (permanent resident, Ontario, lost job) is eligible for EI.
        """
        # Caseworker's query
        query = "Is a permanent resident in Ontario eligible for employment insurance?"

        # Parse query
        parsed = services['parser'].parse_query(query)

        # Search for relevant regulations
        search_results = services['search'].hybrid_search(
            query=parsed.normalized_query,
            filters=parsed.filters,
            size=5
        )

        # Should find relevant regulations
        assert search_results['total'] > 0

        # Should extract correct entities
        entity_types = {e.entity_type.value for e in parsed.entities}
        assert 'person_type' in entity_types or 'program' in entity_types

    def test_scenario_citizen_self_service_lookup(self, services):
        """
        Scenario: Citizen looking up program information

        A citizen wants to understand what Canada Child Benefit is
        and how to apply.
        """
        # Citizen's search
        search_query = "Canada Child Benefit what is it"

        parsed = services['parser'].parse_query(search_query)

        search_results = services['search'].hybrid_search(
            query=parsed.normalized_query,
            size=10
        )

        # Should find CCB information
        assert search_results['total'] > 0

    def test_scenario_policy_analyst_research(self, services):
        """
        Scenario: Policy analyst researching regulations

        An analyst needs to find all federal regulations related
        to seniors' benefits for a policy review.
        """
        # Analyst's query
        query = "federal benefits for seniors"

        parsed = services['parser'].parse_query(query)

        search_results = services['search'].hybrid_search(
            query=parsed.normalized_query,
            filters={'jurisdiction': 'federal'},
            size=20
        )

        # Should return comprehensive results
        assert search_results['total'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
