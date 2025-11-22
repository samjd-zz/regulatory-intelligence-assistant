"""
Regulatory Document Batch Processing

Specialized batch processing utilities for regulatory intelligence tasks:
- Bulk document ingestion and indexing
- Batch search operations
- Bulk RAG queries
- Compliance checks for multiple forms

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging
from datetime import datetime

from utils.batch_processor import BatchProcessor, AsyncBatchProcessor, BatchResult
from services.search_service import SearchService
from services.rag_service import RAGService
from services.legal_nlp import LegalEntityExtractor
from services.query_parser import LegalQueryParser

logger = logging.getLogger(__name__)


# === Document Batch Processing ===

@dataclass
class DocumentBatchItem:
    """Single document for batch processing"""
    title: str
    content: str
    jurisdiction: str
    document_type: str = "regulation"
    authority: Optional[str] = None
    effective_date: Optional[str] = None
    citation: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class DocumentIndexResult:
    """Result of indexing a document"""
    document_id: str
    title: str
    indexed: bool
    error: Optional[str] = None
    indexed_at: str = ""


class DocumentBatchProcessor:
    """Batch processor for regulatory documents"""

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        max_workers: int = 5,
        rate_limit_per_second: float = 10.0
    ):
        """
        Initialize document batch processor

        Args:
            search_service: SearchService instance
            max_workers: Maximum parallel workers
            rate_limit_per_second: Rate limit for indexing
        """
        self.search_service = search_service or SearchService()
        self.processor = BatchProcessor[DocumentBatchItem, DocumentIndexResult](
            max_workers=max_workers,
            rate_limit_per_second=rate_limit_per_second,
            retry_attempts=3
        )

    def _index_document(self, item: DocumentBatchItem) -> DocumentIndexResult:
        """Index a single document"""
        try:
            import hashlib

            # Generate document ID
            hash_input = f"{item.title}:{item.content}"
            doc_id = hashlib.md5(hash_input.encode()).hexdigest()[:16]

            # Prepare document
            doc = {
                "id": doc_id,
                "title": item.title,
                "content": item.content,
                "jurisdiction": item.jurisdiction,
                "document_type": item.document_type,
                "authority": item.authority,
                "effective_date": item.effective_date,
                "citation": item.citation,
                "indexed_at": datetime.now().isoformat()
            }

            # Add custom metadata
            if item.metadata:
                doc.update(item.metadata)

            # Index in Elasticsearch
            result = self.search_service.index_document(doc)

            return DocumentIndexResult(
                document_id=doc_id,
                title=item.title,
                indexed=True,
                indexed_at=datetime.now().isoformat()
            )

        except Exception as e:
            logger.error(f"Failed to index document '{item.title}': {e}")
            return DocumentIndexResult(
                document_id="",
                title=item.title,
                indexed=False,
                error=str(e)
            )

    def process_document_batch(
        self,
        documents: List[DocumentBatchItem],
        job_id: Optional[str] = None
    ) -> BatchResult[DocumentIndexResult]:
        """
        Process a batch of documents for indexing

        Args:
            documents: List of documents to index
            job_id: Optional job ID for tracking

        Returns:
            BatchResult with indexing results
        """
        return self.processor.process_batch(
            documents,
            self._index_document,
            job_id=job_id
        )

    def get_progress(self, job_id: str):
        """Get progress for a batch job"""
        return self.processor.get_progress(job_id)


# === Search Batch Processing ===

@dataclass
class SearchBatchItem:
    """Single search query for batch processing"""
    query: str
    filters: Optional[Dict[str, Any]] = None
    size: int = 10
    search_type: str = "hybrid"  # keyword, vector, hybrid


@dataclass
class SearchBatchResult:
    """Result of a batch search"""
    query: str
    hits: List[Dict[str, Any]]
    total: int
    execution_time_ms: float = 0.0
    error: Optional[str] = None


class SearchBatchProcessor:
    """Batch processor for search operations"""

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        max_workers: int = 10
    ):
        """
        Initialize search batch processor

        Args:
            search_service: SearchService instance
            max_workers: Maximum concurrent searches
        """
        self.search_service = search_service or SearchService()
        self.processor = BatchProcessor[SearchBatchItem, SearchBatchResult](
            max_workers=max_workers,
            use_processes=False  # I/O bound
        )

    def _execute_search(self, item: SearchBatchItem) -> SearchBatchResult:
        """Execute a single search"""
        import time

        try:
            start = time.time()

            # Execute search based on type
            if item.search_type == "keyword":
                result = self.search_service.keyword_search(
                    query=item.query,
                    filters=item.filters or {},
                    size=item.size
                )
            elif item.search_type == "vector":
                result = self.search_service.vector_search(
                    query=item.query,
                    filters=item.filters or {},
                    size=item.size
                )
            else:  # hybrid
                result = self.search_service.hybrid_search(
                    query=item.query,
                    filters=item.filters or {},
                    size=item.size
                )

            execution_time = (time.time() - start) * 1000

            return SearchBatchResult(
                query=item.query,
                hits=result['hits'],
                total=result['total'],
                execution_time_ms=execution_time
            )

        except Exception as e:
            logger.error(f"Search failed for query '{item.query}': {e}")
            return SearchBatchResult(
                query=item.query,
                hits=[],
                total=0,
                error=str(e)
            )

    def process_search_batch(
        self,
        queries: List[SearchBatchItem],
        job_id: Optional[str] = None
    ) -> BatchResult[SearchBatchResult]:
        """
        Process a batch of search queries

        Args:
            queries: List of search queries
            job_id: Optional job ID for tracking

        Returns:
            BatchResult with search results
        """
        return self.processor.process_batch(
            queries,
            self._execute_search,
            job_id=job_id
        )


# === RAG Batch Processing ===

@dataclass
class RAGBatchItem:
    """Single question for batch RAG processing"""
    question: str
    num_context_docs: int = 5
    use_cache: bool = True


@dataclass
class RAGBatchResult:
    """Result of a batch RAG query"""
    question: str
    answer: str
    confidence_score: float
    citations: List[Dict[str, Any]]
    execution_time_ms: float = 0.0
    from_cache: bool = False
    error: Optional[str] = None


class RAGBatchProcessor:
    """Batch processor for RAG question answering"""

    def __init__(
        self,
        rag_service: Optional[RAGService] = None,
        max_workers: int = 3  # Lower for API rate limits
    ):
        """
        Initialize RAG batch processor

        Args:
            rag_service: RAGService instance
            max_workers: Maximum concurrent RAG queries
        """
        self.rag_service = rag_service or RAGService()
        self.processor = BatchProcessor[RAGBatchItem, RAGBatchResult](
            max_workers=max_workers,
            rate_limit_per_second=2.0,  # Conservative for API limits
            retry_attempts=2
        )

    def _answer_question(self, item: RAGBatchItem) -> RAGBatchResult:
        """Answer a single question"""
        import time

        try:
            start = time.time()

            result = self.rag_service.answer_question(
                question=item.question,
                num_context_docs=item.num_context_docs,
                use_cache=item.use_cache
            )

            execution_time = (time.time() - start) * 1000

            return RAGBatchResult(
                question=item.question,
                answer=result['answer'],
                confidence_score=result['confidence_score'],
                citations=result['citations'],
                execution_time_ms=execution_time,
                from_cache=result.get('from_cache', False)
            )

        except Exception as e:
            logger.error(f"RAG failed for question '{item.question}': {e}")
            return RAGBatchResult(
                question=item.question,
                answer="",
                confidence_score=0.0,
                citations=[],
                error=str(e)
            )

    def process_rag_batch(
        self,
        questions: List[RAGBatchItem],
        job_id: Optional[str] = None
    ) -> BatchResult[RAGBatchResult]:
        """
        Process a batch of RAG questions

        Args:
            questions: List of questions
            job_id: Optional job ID for tracking

        Returns:
            BatchResult with answers
        """
        return self.processor.process_batch(
            questions,
            self._answer_question,
            job_id=job_id
        )


# === NLP Batch Processing ===

@dataclass
class NLPBatchItem:
    """Single text for batch NLP processing"""
    text: str
    extract_entities: bool = True
    parse_query: bool = True


@dataclass
class NLPBatchResult:
    """Result of batch NLP processing"""
    text: str
    entities: Optional[Dict[str, List[str]]] = None
    parsed_query: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class NLPBatchProcessor:
    """Batch processor for NLP operations"""

    def __init__(
        self,
        max_workers: int = 10
    ):
        """
        Initialize NLP batch processor

        Args:
            max_workers: Maximum concurrent NLP operations
        """
        self.entity_extractor = LegalEntityExtractor()
        self.query_parser = LegalQueryParser()
        self.processor = BatchProcessor[NLPBatchItem, NLPBatchResult](
            max_workers=max_workers,
            use_processes=True  # CPU-bound for NLP
        )

    def _process_text(self, item: NLPBatchItem) -> NLPBatchResult:
        """Process a single text"""
        try:
            result = NLPBatchResult(text=item.text)

            # Extract entities
            if item.extract_entities:
                entities = self.entity_extractor.extract_entities(item.text)
                result.entities = entities

            # Parse query
            if item.parse_query:
                parsed = self.query_parser.parse_query(item.text)
                result.parsed_query = parsed

            return result

        except Exception as e:
            logger.error(f"NLP processing failed for text '{item.text[:50]}': {e}")
            return NLPBatchResult(
                text=item.text,
                error=str(e)
            )

    def process_nlp_batch(
        self,
        texts: List[NLPBatchItem],
        job_id: Optional[str] = None
    ) -> BatchResult[NLPBatchResult]:
        """
        Process a batch of texts

        Args:
            texts: List of texts to process
            job_id: Optional job ID for tracking

        Returns:
            BatchResult with NLP results
        """
        return self.processor.process_batch(
            texts,
            self._process_text,
            job_id=job_id
        )


# === Unified Batch API ===

class RegulatoryBatchAPI:
    """
    Unified API for all batch operations

    Provides a single interface for batch document processing,
    search, RAG, and NLP operations.
    """

    def __init__(self):
        """Initialize batch API"""
        self.document_processor = DocumentBatchProcessor()
        self.search_processor = SearchBatchProcessor()
        self.rag_processor = RAGBatchProcessor()
        self.nlp_processor = NLPBatchProcessor()

    def batch_index_documents(
        self,
        documents: List[DocumentBatchItem],
        job_id: Optional[str] = None
    ) -> BatchResult[DocumentIndexResult]:
        """Batch index documents"""
        return self.document_processor.process_document_batch(documents, job_id)

    def batch_search(
        self,
        queries: List[SearchBatchItem],
        job_id: Optional[str] = None
    ) -> BatchResult[SearchBatchResult]:
        """Batch search"""
        return self.search_processor.process_search_batch(queries, job_id)

    def batch_answer_questions(
        self,
        questions: List[RAGBatchItem],
        job_id: Optional[str] = None
    ) -> BatchResult[RAGBatchResult]:
        """Batch RAG question answering"""
        return self.rag_processor.process_rag_batch(questions, job_id)

    def batch_nlp_processing(
        self,
        texts: List[NLPBatchItem],
        job_id: Optional[str] = None
    ) -> BatchResult[NLPBatchResult]:
        """Batch NLP processing"""
        return self.nlp_processor.process_nlp_batch(texts, job_id)

    def get_job_progress(self, job_id: str, job_type: str = "document"):
        """
        Get progress for any batch job

        Args:
            job_id: Job identifier
            job_type: Type of job (document, search, rag, nlp)
        """
        if job_type == "document":
            return self.document_processor.get_progress(job_id)
        elif job_type == "search":
            return self.search_processor.processor.get_progress(job_id)
        elif job_type == "rag":
            return self.rag_processor.processor.get_progress(job_id)
        elif job_type == "nlp":
            return self.nlp_processor.processor.get_progress(job_id)
        return None


# === Example Usage ===

if __name__ == "__main__":
    # Example: Batch document indexing
    batch_api = RegulatoryBatchAPI()

    documents = [
        DocumentBatchItem(
            title="Employment Insurance Act - Section 7",
            content="Benefits are payable to persons who have lost employment...",
            jurisdiction="federal",
            document_type="act",
            authority="Parliament of Canada"
        ),
        DocumentBatchItem(
            title="Canada Pension Plan Act - Section 44",
            content="Retirement pension shall be paid to a contributor...",
            jurisdiction="federal",
            document_type="act"
        )
    ]

    result = batch_api.batch_index_documents(documents)
    print(f"Indexed {result.success_count}/{result.total_items} documents")
    print(f"Success rate: {result.success_rate:.1f}%")

    # Example: Batch search
    searches = [
        SearchBatchItem(query="employment insurance eligibility", search_type="hybrid"),
        SearchBatchItem(query="pension benefits", search_type="keyword")
    ]

    search_result = batch_api.batch_search(searches)
    print(f"Executed {search_result.success_count} searches")

    # Example: Batch RAG
    questions = [
        RAGBatchItem(question="What is the Canada Pension Plan?"),
        RAGBatchItem(question="Who is eligible for employment insurance?")
    ]

    rag_result = batch_api.batch_answer_questions(questions)
    print(f"Answered {rag_result.success_count} questions")
