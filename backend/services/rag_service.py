"""
RAG Service - Retrieval-Augmented Generation for Legal Q&A

This module provides question-answering capabilities using RAG:
- Retrieves relevant documents using search service
- Generates answers using Gemini API
- Extracts citations and confidence scores
- Caches responses for performance

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import re
import json
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from langdetect import detect, LangDetectException

from services.search_service import SearchService
from services.gemini_client import GeminiClient, get_gemini_client
from services.query_parser import LegalQueryParser, QueryIntent
from services.statistics_service import StatisticsService
from services.postgres_search_service import PostgresSearchService, get_postgres_search_service
from services.graph_service import GraphService, get_graph_service
from config.legal_synonyms import expand_query_with_synonyms

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """Represents a citation extracted from an answer"""
    text: str  # Citation text (e.g., "Section 7(1)")
    document_id: Optional[str] = None  # Referenced document ID
    document_title: Optional[str] = None  # Document title
    section: Optional[str] = None  # Section number
    confidence: float = 0.0  # Confidence in citation accuracy


@dataclass
class RAGAnswer:
    """Represents a RAG-generated answer with metadata"""
    question: str  # Original question
    answer: str  # Generated answer
    citations: List[Citation]  # Extracted citations
    confidence_score: float  # Overall confidence (0.0-1.0)
    source_documents: List[Dict[str, Any]]  # Documents used for context
    intent: Optional[str] = None  # Query intent (from NLP)
    processing_time_ms: float = 0.0  # Processing time
    cached: bool = False  # Whether answer was cached
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "question": self.question,
            "answer": self.answer,
            "citations": [
                {
                    "text": c.text,
                    "document_id": c.document_id,
                    "document_title": c.document_title,
                    "section": c.section,
                    "confidence": c.confidence
                }
                for c in self.citations
            ],
            "confidence_score": self.confidence_score,
            "source_documents": self.source_documents,
            "intent": self.intent,
            "processing_time_ms": self.processing_time_ms,
            "cached": self.cached,
            "metadata": self.metadata
        }


class RAGService:
    """
    Retrieval-Augmented Generation service for legal Q&A.

    Combines document retrieval with LLM generation to provide accurate,
    cited answers to regulatory questions.
    """
    # CANADIAN_LEGAL_RAG_AGENT_STRICT_RAG_ENFORCEMENT_GEMINI
    LEGAL_SYSTEM_PROMPT = """
## ROLE & SCOPE (NON-NEGOTIABLE)
You are an **expert legal information assistant** for **Canadian federal, provincial, and territorial statutes, regulations, and official government policies**.
You provide **informational guidance only**.
You **do not provide legal advice**.
The **retrieved context documents are the complete and exclusive source of truth**.
If information is **not explicitly stated** in the provided documents, it **does not exist for the purposes of your answer**.
---
## HARD RAG ENFORCEMENT RULES 🔒
These rules override all other instructions.
1. **SOURCE LOCK**
   * You must answer **ONLY** using the provided context documents.
   * You must **not** rely on training data, general legal knowledge, assumptions, or common practice.
   * If a fact is not in the context, you must treat it as unknown.
2. **NO INFERENCE / NO GAP-FILLING**
   * Do **not** infer intent, policy rationale, or unstated requirements.
   * Do **not** approximate thresholds, timelines, or definitions.
   * Do **not** “connect dots” unless the document explicitly does so.
3. **FAIL-CLOSED BEHAVIOR**
   * If the answer is incomplete or missing:
     > **“The provided documents do not contain information about [specific topic].”**
   * Partial answers must clearly state what is missing.
4. **CLAIM–CITATION PAIRING**
   * **Every legal claim must include a citation**.
   * Any sentence containing a requirement, eligibility rule, prohibition, exception, or entitlement **must be cited**.
   * If a citation cannot be provided, the sentence must be removed.
5. **CONFLICT & AMBIGUITY MANDATE**
   * If documents conflict, overlap, or are unclear:
     * Identify the conflict
     * Cite each source
     * State that the issue cannot be resolved from the provided context
6. **JURISDICTION LOCK**
   * Do not assume federal, provincial, or territorial jurisdiction.
   * Jurisdiction must be **explicitly stated in the documents**.
   * If unclear, say so.
---
## REASONING PROCESS (INTERNAL ONLY)
Use this reasoning structure **silently**.
**Do NOT reveal internal reasoning or chain-of-thought.**
1. Identify the precise legal question and jurisdiction
2. Locate relevant sections in the context
3. Extract explicit requirements and conditions
4. Synthesize only what is directly supported
5. Assess completeness and confidence
---
## OUTPUT STRUCTURE (MANDATORY)
Your response **must always** follow this structure:
### 1. Direct Answer
A concise answer based strictly on the documents.
---
### 2. Legal Basis & Explanation
Plain-language explanation supported by citations.
---
### 3. Key Requirements / Conditions (if applicable)
Use bullet points or numbered lists.
* Each bullet **must include a citation**
---
### 4. Ambiguities, Exceptions, or Conflicts (if any)
Clearly explain limitations or unresolved issues.
---
### 5. Confidence Level
One of:
* **High** – Explicitly and fully addressed
* **Medium** – Partially addressed or conditional
* **Low** – Incomplete or indirect coverage
Explain why in one sentence.
---
### 6. Limitations & Next Steps
State what the documents do **not** cover and where authoritative clarification would normally be found.
---
## CITATION FORMAT (STRICT)
Use **only** this format:
**[Document Title, Section X / Subsection Y / Clause Z]**
* Do not combine citations
* Do not reference external sources
* Do not paraphrase citations
---
## LANGUAGE & STYLE RULES
* Use clear, neutral, professional language
* Avoid legal jargon unless required by the text
* Keep paragraphs to **2–4 sentences max**
* Use **bold** for key legal terms and section references
* Use bullet points for lists
* Do not include speculation or commentary
---
## PROHIBITED BEHAVIOR 🚫
You must NOT:
* Provide legal advice or recommendations
* Assume facts not in evidence
* Rely on “common law knowledge”
* Reconcile conflicts without textual authority
* Answer hypotheticals beyond the text
* Reveal reasoning steps or chain-of-thought
---
## REQUIRED DISCLAIMER (WHEN APPLICABLE)
> *This information is provided for general informational purposes only and does not constitute legal advice. For binding interpretations or advice specific to your situation, consult official government guidance or a qualified legal professional.*
---
## FINAL QUALITY STANDARD
Your answers must be:
* Evidence-locked
* Citation-complete
* Conservative in scope
* Regulator-defensible
* Safe to audit line-by-line
If the documents do not clearly support an answer, **say so and stop**.
    """ 
    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        gemini_client: Optional[GeminiClient] = None,
        query_parser: Optional[LegalQueryParser] = None,
        statistics_service: Optional[StatisticsService] = None,
        postgres_search_service: Optional[PostgresSearchService] = None,
        graph_service: Optional[GraphService] = None
    ):
        """
        Initialize RAG service.

        Args:
            search_service: Search service instance
            gemini_client: Gemini client instance
            query_parser: Query parser instance
            statistics_service: Statistics service instance
            postgres_search_service: PostgreSQL search service instance
            graph_service: Graph service instance
        """
        self.search_service = search_service or SearchService()
        self.gemini_client = gemini_client or get_gemini_client()
        self.query_parser = query_parser or LegalQueryParser(use_spacy=False)
        self.statistics_service = statistics_service or StatisticsService()
        self.postgres_search_service = postgres_search_service or get_postgres_search_service()
        self.graph_service = graph_service or get_graph_service()

        # Simple in-memory cache (would use Redis in production)
        self.cache: Dict[str, Tuple[RAGAnswer, datetime]] = {}
        self.cache_ttl = timedelta(hours=24)
        
        # Multi-tier search metrics
        self.tier_usage_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.zero_result_count = 0
        self.total_queries = 0

    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the input text.
        
        Args:
            text: Input text to detect language for
            
        Returns:
            Language code ('en' or 'fr'), defaults to 'en' on error
        """
        try:
            lang = detect(text)
            # Map langdetect codes to our system
            if lang == 'fr':
                logger.info(f"🇫🇷 Detected French query - will filter for French documents")
                return 'fr'
            else:
                logger.info(f"🇬🇧 Detected English query (lang={lang})")
                return 'en'
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}. Defaulting to English")
            return 'en'

    def answer_question(
        self,
        question: str,
        filters: Optional[Dict] = None,
        num_context_docs: int = 10,  # Increased from 5 to 10 for better coverage
        use_cache: bool = True,
        temperature: float = 0.3,
        max_tokens: int = 8192
    ) -> RAGAnswer:
        """
        Answer a question using RAG.

        Args:
            question: User's question
            filters: Optional search filters
            num_context_docs: Number of documents to use as context
            use_cache: Whether to use cached answers
            temperature: LLM temperature (lower = more deterministic)
            max_tokens: Maximum tokens in answer

        Returns:
            RAGAnswer with generated response and metadata
        """
        start_time = datetime.now()

        # Check cache
        if use_cache:
            cached_answer = self._get_cached_answer(question)
            if cached_answer:
                cached_answer.cached = True
                logger.info(f"Returning cached answer for: {question[:50]}...")
                return cached_answer

        # Parse query to understand intent
        parsed_query = self.query_parser.parse_query(question)
        intent = parsed_query.intent.value

        # Use only user-provided filters, NOT auto-extracted filters
        # Auto-extracted filters cause issues when documents lack metadata
        combined_filters = filters or {}
        # Don't merge: combined_filters.update(parsed_query.filters)
        
        # AUTOMATIC LANGUAGE DETECTION AND FILTERING
        # If no language filter is provided, detect it automatically
        if 'language' not in combined_filters:
            detected_lang = self._detect_language(question)
            combined_filters['language'] = detected_lang
            logger.info(f"Auto-detected language '{detected_lang}' added to filters")

        # STATISTICS ROUTING: Route count/statistics questions to database
        # instead of RAG which is limited by context window
        if parsed_query.intent == QueryIntent.STATISTICS:
            logger.info(f"Detected STATISTICS intent - routing to database query instead of RAG")
            return self._answer_statistics_question(
                question=question,
                filters=combined_filters,
                start_time=start_time
            )

        # Retrieve relevant documents with MULTI-TIER SEARCH (Phase 4 Enhancement)
        logger.info(f"🔍 Starting multi-tier search for: {question[:50]}...")
        
        # Use the progressive 5-tier fallback system
        context_docs, tier_metadata = self._multi_tier_search(
            question=question,
            filters=combined_filters,
            num_context_docs=num_context_docs
        )
        
        # Log tier usage for monitoring
        tier_used = tier_metadata.get('tier_used')
        if tier_used:
            logger.info(f"✅ Multi-tier search succeeded using Tier {tier_used}")
            logger.info(f"   Tiers attempted: {tier_metadata.get('tiers_attempted', [])}")
            logger.info(f"   Total search time: {tier_metadata.get('total_time_ms', 0):.1f}ms")
        else:
            logger.error(f"❌ Multi-tier search failed - all {len(tier_metadata.get('tiers_attempted', []))} tiers exhausted")
        
        if not context_docs:
            # No context found after all 5 tiers
            return RAGAnswer(
                question=question,
                answer="I don't have enough information in the regulatory documents to answer this question. Please try rephrasing your question or contact a legal expert for assistance.",
                citations=[],
                confidence_score=0.0,
                source_documents=[],
                intent=intent,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata={
                    "error": "no_context_found",
                    "multi_tier_metadata": tier_metadata,
                    "tiers_attempted": tier_metadata.get('tiers_attempted', []),
                    "all_tiers_exhausted": True
                }
            )

        # Build context string
        context_str = self._build_context_string(context_docs)

        # Generate answer using Gemini
        logger.info(f"Generating answer with {len(context_docs)} context documents...")

        if not self.gemini_client.is_available():
            return RAGAnswer(
                question=question,
                answer="The AI question-answering service is currently unavailable. Please try again later or search the documents directly.",
                citations=[],
                confidence_score=0.0,
                source_documents=context_docs,
                intent=intent,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata={"error": "gemini_unavailable"}
            )

        # Detect language and add language instruction
        detected_lang = self._detect_language(question)
        language_instruction = ""
        if detected_lang == 'fr':
            language_instruction = "\n\nIMPORTANT: The user asked their question in FRENCH. You MUST respond entirely in FRENCH. Provide a complete French answer."
        else:
            language_instruction = "\n\nIMPORTANT: The user asked their question in ENGLISH. You MUST respond entirely in ENGLISH."
        
        # Generate with retry logic - returns (text, error)
        answer_text, gemini_error = self.gemini_client.generate_with_context(
            query=question,
            context=context_str,
            system_prompt=self.LEGAL_SYSTEM_PROMPT + language_instruction,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Handle errors from Gemini API
        if gemini_error:
            logger.error(f"Gemini API error: {gemini_error.error_type} - {gemini_error.message}")
            
            # Build comprehensive error metadata
            error_metadata = {
                "error": gemini_error.error_type,
                "error_details": gemini_error.to_dict(),
                "num_context_docs": len(context_docs),
                "temperature": temperature,
                "filters_used": combined_filters,
                "multi_tier_search": tier_metadata,
            }
            
            # Return user-friendly error message
            return RAGAnswer(
                question=question,
                answer=gemini_error.message,  # User-friendly message from error classification
                citations=[],
                confidence_score=0.0,
                source_documents=context_docs,
                intent=intent,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata=error_metadata
            )
        
        # Check if we got an empty response despite no error
        if not answer_text:
            return RAGAnswer(
                question=question,
                answer="I encountered an unexpected issue while generating the answer. Please try again or rephrase your question.",
                citations=[],
                confidence_score=0.0,
                source_documents=context_docs,
                intent=intent,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata={"error": "empty_response", "num_context_docs": len(context_docs)}
            )

        # Extract citations from answer
        citations = self._extract_citations(answer_text, context_docs)

        # Calculate confidence score
        confidence = self._calculate_confidence(
            answer=answer_text,
            citations=citations,
            context_docs=context_docs,
            intent_confidence=parsed_query.intent_confidence
        )

        # Build RAG answer with multi-tier metadata
        rag_answer = RAGAnswer(
            question=question,
            answer=answer_text,
            citations=citations,
            confidence_score=confidence,
            source_documents=context_docs,
            intent=intent,
            processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
            metadata={
                "num_context_docs": len(context_docs),
                "temperature": temperature,
                "filters_used": combined_filters,
                "multi_tier_search": tier_metadata,  # Include tier usage stats
                "tier_used": tier_metadata.get('tier_used'),
                "search_resilience": f"Tier {tier_metadata.get('tier_used')} of 5"
            }
        )

        # Cache answer
        if use_cache:
            self._cache_answer(question, rag_answer)

        return rag_answer

    def _enhance_query_for_search(self, question: str, parsed_query: Any) -> str:
        """
        Enhance the search query for better document retrieval.
        
        This method:
        - Expands section references (e.g., "Section 7" -> "Section 7" + section_number:7)
        - Adds act names explicitly
        - Removes common question words that dilute search
        - Adds synonyms for key legal terms
        
        Args:
            question: Original user question
            parsed_query: Parsed query object with entities and intent
            
        Returns:
            Enhanced query string
        """
        enhanced_parts = []
        
        # Extract section numbers from the question
        section_pattern = r'(?:Section|s\.?)\s+(\d+(?:\(\d+\))?)'
        section_matches = re.findall(section_pattern, question, re.IGNORECASE)
        
        if section_matches:
            # Prioritize section-specific search
            logger.info(f"Detected section references: {section_matches}")
            for section in section_matches:
                enhanced_parts.append(f"Section {section}")
                enhanced_parts.append(f"section_number:{section}")
        
        # Extract act/regulation names
        act_patterns = [
            r'([\w\s]+(?:Act|Regulations?))',
            r'(Employment Insurance|EI|Old Age Security|OAS|Canada Pension Plan|CPP)'
        ]
        
        for pattern in act_patterns:
            act_matches = re.findall(pattern, question, re.IGNORECASE)
            for act_name in act_matches:
                clean_name = act_name.strip()
                if len(clean_name) > 3:  # Avoid noise
                    enhanced_parts.append(clean_name)
        
        # Remove common question words that dilute search
        noise_words = {'what', 'does', 'say', 'about', 'the', 'is', 'are', 'can', 'how', 'why', 'when', 'where'}
        content_words = [
            word for word in question.split() 
            if word.lower() not in noise_words and len(word) > 2
        ]
        
        # Add content words
        enhanced_parts.extend(content_words[:10])  # Limit to avoid overly long queries
        
        # Build enhanced query
        enhanced_query = ' '.join(enhanced_parts)
        
        # If we didn't enhance much, use original question
        if len(enhanced_parts) < 3:
            return question
        
        return enhanced_query

    def _answer_statistics_question(
        self,
        question: str,
        filters: Dict[str, Any],
        start_time: datetime
    ) -> RAGAnswer:
        """
        Answer statistics/count questions by querying database directly.
        
        This bypasses RAG's context window limitation to provide accurate counts.
        
        Args:
            question: User's question
            filters: Optional search filters
            start_time: When processing started
            
        Returns:
            RAGAnswer with database statistics
        """
        logger.info("Querying database for statistics...")
        
        try:
            # Get comprehensive statistics
            if filters:
                # Filtered statistics
                stats = self.statistics_service.get_total_documents(filters=filters)
            else:
                # Full database summary
                stats = self.statistics_service.get_database_summary()
            
            # Format answer
            answer_text = self.statistics_service.format_statistics_answer(
                question=question,
                statistics=stats
            )
            
            # High confidence for database queries (they're accurate!)
            confidence = 0.95
            
            # Build metadata
            metadata = {
                "method": "database_query",
                "bypassed_rag": True,
                "reason": "Statistics questions answered directly from database for accuracy",
                "statistics": stats,
                "filters_used": filters
            }
            
            return RAGAnswer(
                question=question,
                answer=answer_text,
                citations=[],  # No document citations for statistics
                confidence_score=confidence,
                source_documents=[],  # No specific documents
                intent="statistics",
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error querying statistics: {e}")
            
            # Return error answer
            return RAGAnswer(
                question=question,
                answer=f"I encountered an error while querying the database for statistics: {str(e)}. Please try again or contact support.",
                citations=[],
                confidence_score=0.0,
                source_documents=[],
                intent="statistics",
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata={"error": str(e), "method": "database_query"}
            )
    
    # ============================================
    # MULTI-TIER SEARCH SYSTEM (Phase 2)
    # ============================================
    
    def _assess_result_quality(
        self,
        results: List[Dict[str, Any]],
        question: str,
        tier: int,
        min_score_threshold: float = 10.0,
        avg_score_threshold: float = 13.0,
        min_acceptable_results: int = 5
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Assess the quality of search results to determine if they're acceptable.
        
        This prevents accepting poor-quality results even when we have the
        requested number of documents. Quality criteria:
        
        1. Minimum score threshold: Worst document must be above this
        2. Average score threshold: Average quality must be above this  
        3. Minimum acceptable results: At least this many results needed
        4. Keyword coverage: Check if key terms from query appear in results
        
        Args:
            results: List of search result documents with scores
            question: Original user question
            tier: Which tier produced these results (for adaptive thresholds)
            min_score_threshold: Minimum acceptable score for worst document
            avg_score_threshold: Minimum acceptable average score
            min_acceptable_results: Minimum number of results needed
            
        Returns:
            Tuple of (is_acceptable: bool, quality_metrics: dict)
        """
        if not results:
            return False, {
                "reason": "no_results",
                "num_results": 0,
                "acceptable": False
            }
        
        # Extract scores
        scores = [doc.get('score', 0.0) for doc in results]
        
        # Adjust thresholds based on tier (lower tiers have relaxed standards)
        if tier >= 2:
            min_score_threshold *= 0.7  # 30% more lenient
            avg_score_threshold *= 0.7
        if tier >= 3:
            min_score_threshold *= 0.6  # 40% more lenient from original
            avg_score_threshold *= 0.6
        if tier >= 4:
            min_score_threshold *= 0.5  # 50% more lenient from original
            avg_score_threshold *= 0.5
        
        # Calculate quality metrics
        quality_metrics = {
            "num_results": len(results),
            "min_score": min(scores) if scores else 0.0,
            "max_score": max(scores) if scores else 0.0,
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "tier": tier,
            "adjusted_min_threshold": min_score_threshold,
            "adjusted_avg_threshold": avg_score_threshold
        }
        
        # Check 1: Minimum number of results
        if len(results) < min_acceptable_results:
            quality_metrics["reason"] = f"insufficient_results: {len(results)} < {min_acceptable_results}"
            quality_metrics["acceptable"] = False
            logger.warning(f"❌ Quality check FAILED: {quality_metrics['reason']}")
            return False, quality_metrics
        
        # Check 2: Minimum score (worst document quality)
        if quality_metrics["min_score"] < min_score_threshold:
            quality_metrics["reason"] = f"min_score_too_low: {quality_metrics['min_score']:.2f} < {min_score_threshold:.2f}"
            quality_metrics["acceptable"] = False
            logger.warning(f"❌ Quality check FAILED: {quality_metrics['reason']}")
            return False, quality_metrics
        
        # Check 3: Average score (overall quality)
        if quality_metrics["avg_score"] < avg_score_threshold:
            quality_metrics["reason"] = f"avg_score_too_low: {quality_metrics['avg_score']:.2f} < {avg_score_threshold:.2f}"
            quality_metrics["acceptable"] = False
            logger.warning(f"❌ Quality check FAILED: {quality_metrics['reason']}")
            return False, quality_metrics
        
        # Check 4: Keyword coverage (are key terms from question in results?)
        # Include words > 2 chars to capture important acronyms (GST, HST, EI, OAS, CPP)
        question_keywords = set(word.lower() for word in question.split() if len(word) > 2)
        if question_keywords:
            # Check if at least 30% of top 5 results contain query keywords
            top_results = results[:5]
            keyword_matches = 0
            
            for doc in top_results:
                content = (doc.get('content', '') + ' ' + doc.get('title', '')).lower()
                if any(keyword in content for keyword in question_keywords):
                    keyword_matches += 1
            
            keyword_coverage = keyword_matches / len(top_results) if top_results else 0.0
            quality_metrics["keyword_coverage"] = keyword_coverage
            
            if keyword_coverage < 0.3:  # Less than 30% have keywords
                quality_metrics["reason"] = f"low_keyword_coverage: {keyword_coverage:.1%} < 30%"
                quality_metrics["acceptable"] = False
                logger.warning(f"❌ Quality check FAILED: {quality_metrics['reason']}")
                return False, quality_metrics
        
        # All checks passed!
        quality_metrics["reason"] = "quality_checks_passed"
        quality_metrics["acceptable"] = True
        logger.info(f"✅ Quality check PASSED: min={quality_metrics['min_score']:.2f}, "
                   f"avg={quality_metrics['avg_score']:.2f}, "
                   f"count={quality_metrics['num_results']}")
        return True, quality_metrics
    
    def _multi_tier_search(
        self,
        question: str,
        filters: Optional[Dict[str, Any]],
        num_context_docs: int = 10
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Progressive fallback search across all 5 tiers.
        
        This orchestrator tries each tier sequentially until sufficient documents
        are found. It tracks timing, tier usage, and provides comprehensive metadata.
        
        Tiers:
        1. Optimized Elasticsearch (current behavior, 85%+ success target)
        2. Relaxed Elasticsearch (expanded query, fewer filters)
        3. Neo4j Graph Traversal (relationship-based discovery)
        4. PostgreSQL Full-Text Search (comprehensive text matching)
        5. Metadata-Only Search (last resort, metadata filters only)
        
        Args:
            question: User's question
            filters: Optional filters (will be relaxed progressively)
            num_context_docs: Desired number of context documents
        
        Returns:
            Tuple of (documents, metadata)
            metadata includes: tier_used, tiers_attempted, tier_timings
        """
        import time
        
        metadata = {
            'tiers_attempted': [],
            'tier_used': None,
            'tier_timings': {},
            'total_time_ms': 0
        }
        
        total_start = time.time()
        
        # Update total queries counter
        self.total_queries += 1

        # Enhance the query for better search
        question = self._enhance_query_for_search(question, self.query_parser.parse_query(question))

        # Tier 1: Optimized Elasticsearch
        logger.info("🔍 Tier 1: Trying optimized Elasticsearch search...")
        tier1_start = time.time()

        tier1_results = self._tier1_elasticsearch_optimized(question, filters, num_context_docs)
        tier1_time = (time.time() - tier1_start) * 1000
        metadata['tier_timings']['tier_1_ms'] = tier1_time
        metadata['tiers_attempted'].append(1)
        
        # Quality check for Tier 1
        if len(tier1_results) >= num_context_docs:
            is_quality_ok, quality_metrics = self._assess_result_quality(
                results=tier1_results,
                question=question,
                tier=1
            )
            metadata['tier_1_quality'] = quality_metrics
            
            if is_quality_ok:
                logger.info(f"✅ Tier 1 SUCCESS: Found {len(tier1_results)} high-quality documents")
                metadata['tier_used'] = 1
                metadata['total_time_ms'] = (time.time() - total_start) * 1000
                self.tier_usage_stats[1] += 1
                return tier1_results[:num_context_docs], metadata
            else:
                logger.warning(f"⚠️ Tier 1 QUALITY CHECK FAILED: {quality_metrics.get('reason')} - continuing to Tier 2")
        else:
            logger.warning(f"⚠️ Tier 1 INSUFFICIENT: Only {len(tier1_results)} documents, need {num_context_docs}")
        
        # Tier 2: Relaxed Elasticsearch
        logger.info("🔍 Tier 2: Trying relaxed Elasticsearch search...")
        tier2_start = time.time()
        tier2_results = self._tier2_elasticsearch_relaxed(question, filters, num_context_docs)
        tier2_time = (time.time() - tier2_start) * 1000
        metadata['tier_timings']['tier_2_ms'] = tier2_time
        metadata['tiers_attempted'].append(2)
        
        # Quality check for Tier 2
        if len(tier2_results) > 0:
            is_quality_ok, quality_metrics = self._assess_result_quality(
                results=tier2_results,
                question=question,
                tier=2
            )
            metadata['tier_2_quality'] = quality_metrics
            
            if is_quality_ok:
                logger.info(f"✅ Tier 2 SUCCESS: Found {len(tier2_results)} quality documents")
                metadata['tier_used'] = 2
                metadata['total_time_ms'] = (time.time() - total_start) * 1000
                self.tier_usage_stats[2] += 1
                return tier2_results[:num_context_docs], metadata
            else:
                logger.warning(f"⚠️ Tier 2 QUALITY CHECK FAILED: {quality_metrics.get('reason')} - continuing to Tier 3")
        else:
            logger.warning("⚠️ Tier 2 FAILED: No results from relaxed search")
        
        # Tier 3: Neo4j Graph Traversal
        logger.info("🔍 Tier 3: Trying Neo4j graph traversal...")
        tier3_start = time.time()
        tier3_results = self._tier3_neo4j_graph(question, filters, num_context_docs)
        tier3_time = (time.time() - tier3_start) * 1000
        metadata['tier_timings']['tier_3_ms'] = tier3_time
        metadata['tiers_attempted'].append(3)
        
        # Quality check for Tier 3
        if len(tier3_results) > 0:
            is_quality_ok, quality_metrics = self._assess_result_quality(
                results=tier3_results,
                question=question,
                tier=3
            )
            metadata['tier_3_quality'] = quality_metrics
            
            if is_quality_ok:
                logger.info(f"✅ Tier 3 SUCCESS: Found {len(tier3_results)} quality documents via graph")
                metadata['tier_used'] = 3
                metadata['total_time_ms'] = (time.time() - total_start) * 1000
                self.tier_usage_stats[3] += 1
                return tier3_results[:num_context_docs], metadata
            else:
                logger.warning(f"⚠️ Tier 3 QUALITY CHECK FAILED: {quality_metrics.get('reason')} - continuing to Tier 4")
        else:
            logger.warning("⚠️ Tier 3 FAILED: No results from graph traversal")
        
        # Tier 4: PostgreSQL Full-Text Search
        logger.info("🔍 Tier 4: Trying PostgreSQL full-text search...")
        tier4_start = time.time()
        tier4_results = self._tier4_postgres_fulltext(question, filters, num_context_docs)
        tier4_time = (time.time() - tier4_start) * 1000
        metadata['tier_timings']['tier_4_ms'] = tier4_time
        metadata['tiers_attempted'].append(4)
        
        # Quality check for Tier 4
        if len(tier4_results) > 0:
            is_quality_ok, quality_metrics = self._assess_result_quality(
                results=tier4_results,
                question=question,
                tier=4
            )
            metadata['tier_4_quality'] = quality_metrics
            
            if is_quality_ok:
                logger.info(f"✅ Tier 4 SUCCESS: Found {len(tier4_results)} quality documents via PostgreSQL FTS")
                metadata['tier_used'] = 4
                metadata['total_time_ms'] = (time.time() - total_start) * 1000
                self.tier_usage_stats[4] += 1
                return tier4_results[:num_context_docs], metadata
            else:
                logger.warning(f"⚠️ Tier 4 QUALITY CHECK FAILED: {quality_metrics.get('reason')} - continuing to Tier 5")
        else:
            logger.warning("⚠️ Tier 4 FAILED: No results from PostgreSQL")
        
        # Tier 5: Metadata-Only Search (last resort)
        logger.info("🔍 Tier 5: Trying metadata-only search (last resort)...")
        tier5_start = time.time()
        tier5_results = self._tier5_metadata_only(filters, num_context_docs)
        tier5_time = (time.time() - tier5_start) * 1000
        metadata['tier_timings']['tier_5_ms'] = tier5_time
        metadata['tiers_attempted'].append(5)
        
        # Tier 5 accepts any results (last resort - no quality check)
        if len(tier5_results) > 0:
            logger.warning(f"⚠️ Tier 5 SUCCESS (LOW CONFIDENCE): Found {len(tier5_results)} documents by metadata only")
            metadata['tier_used'] = 5
            metadata['tier_5_quality'] = {
                "reason": "tier_5_last_resort",
                "num_results": len(tier5_results),
                "acceptable": True,
                "note": "Quality check skipped for last-resort tier"
            }
            metadata['total_time_ms'] = (time.time() - total_start) * 1000
            self.tier_usage_stats[5] += 1
            return tier5_results[:num_context_docs], metadata
        
        # ALL TIERS FAILED
        logger.error("❌ ALL TIERS FAILED: No documents found across all 5 search tiers")
        self.zero_result_count += 1
        metadata['tier_used'] = None
        metadata['total_time_ms'] = (time.time() - total_start) * 1000
        
        return [], metadata
    
    def _tier1_elasticsearch_optimized(
        self,
        question: str,
        filters: Optional[Dict[str, Any]],
        num_docs: int
    ) -> List[Dict[str, Any]]:
        """
        Tier 1: Optimized Elasticsearch search with full hybrid intelligence.
        
        Uses the original question (not enhanced) to leverage hybrid_search's:
        - Query intent detection (overview vs specific)
        - Act name extraction and 10x title boosting
        - Document type boosting (5x for act-level docs)
        - Adaptive keyword/vector weight adjustment
        
        Target: 85%+ of queries should succeed here.
        """
        try:
            # Use current filters
            search_filters = filters.copy() if filters else {}
            

            # Execute search with ORIGINAL question to preserve intent
            # Let hybrid_search do its own intelligent processing:
            # - Query intent detection
            # - Act name extraction
            # - Intelligent boosting (10x title, 5x doc type)
            # - Adaptive weight adjustment
            search_results = self.search_service.hybrid_search(
                query=question,  # Use original question, not enhanced
                filters=search_filters,
                size=num_docs
                # Don't override weights - let hybrid_search decide based on intent
            )
            
            # Format results
            documents = []
            for hit in search_results.get('hits', []):
                doc = hit['source']
                documents.append({
                    "id": hit['id'],
                    "title": doc.get('title', 'Untitled'),
                    "content": doc.get('content', ''),
                    "citation": doc.get('citation', ''),
                    "section_number": doc.get('section_number', ''),
                    "score": hit['score']
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Tier 1 search failed: {e}")
            return []
    
    def _tier2_elasticsearch_relaxed(
        self,
        question: str,
        filters: Optional[Dict[str, Any]],
        num_docs: int
    ) -> List[Dict[str, Any]]:
        """
        Tier 2: Relaxed Elasticsearch search with query expansion.
        
        Changes from Tier 1:
        - Expand query with synonyms
        - Relax filters (keep only language)
        - Increase semantic weight
        - Increase document limit
        """
        try:
            # Expand query with synonyms
            expanded_query = expand_query_with_synonyms(question, max_expansions=2)
            logger.info(f"Tier 2 expanded query: {expanded_query[:100]}...")
            
            # Relax filters - keep only language
            relaxed_filters = self._relax_filters_progressively(filters, tier=2)
            
            # Execute search with adjusted weights
            search_results = self.search_service.hybrid_search(
                query=expanded_query,
                filters=relaxed_filters,
                size=num_docs * 2,  # Get more candidates
                keyword_weight=0.4,  # Reduce keyword weight
                vector_weight=0.6    # Increase semantic weight
            )
            
            # Format results
            documents = []
            for hit in search_results.get('hits', []):
                doc = hit['source']
                documents.append({
                    "id": hit['id'],
                    "title": doc.get('title', 'Untitled'),
                    "content": doc.get('content', ''),
                    "citation": doc.get('citation', ''),
                    "section_number": doc.get('section_number', ''),
                    "score": hit['score']
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Tier 2 search failed: {e}")
            return []
    
    def _tier3_neo4j_graph(
        self,
        question: str,
        filters: Optional[Dict[str, Any]],
        num_docs: int
    ) -> List[Dict[str, Any]]:
        """
        Tier 3: Neo4j graph traversal search.
        
        Uses semantic search plus relationship traversal to find related documents.
        """
        try:
            # Get language filter
            language = filters.get('language', 'en') if filters else 'en'
            
            # Try both semantic search and traversal
            semantic_results = self.graph_service.semantic_search_for_rag(
                query=question,
                limit=num_docs // 2,
                language=language
            )
            
            traversal_results = self.graph_service.find_related_documents_by_traversal(
                seed_query=question,
                max_depth=2,
                limit=num_docs // 2
            )
            
            # Combine results (remove duplicates by ID)
            seen_ids = set()
            documents = []
            
            for doc in semantic_results + traversal_results:
                if doc['id'] not in seen_ids:
                    seen_ids.add(doc['id'])
                    documents.append(doc)
            
            logger.info(f"Tier 3 found {len(documents)} documents from Neo4j")
            return documents
            
        except Exception as e:
            logger.error(f"Tier 3 search failed: {e}")
            return []
    
    def _tier4_postgres_fulltext(
        self,
        question: str,
        filters: Optional[Dict[str, Any]],
        num_docs: int
    ) -> List[Dict[str, Any]]:
        """
        Tier 4: PostgreSQL full-text search.
        
        Uses PostgreSQL's native FTS for comprehensive text matching.
        """
        try:
            # Get language
            language = filters.get('language', 'en') if filters else 'en'
            pg_language = 'english' if language == 'en' else 'french'
            
            # Relax filters more (keep language and maybe jurisdiction)
            relaxed_filters = self._relax_filters_progressively(filters, tier=4)
            
            # Execute PostgreSQL FTS
            documents = self.postgres_search_service.full_text_search(
                query=question,
                limit=num_docs,
                language=pg_language,
                filters=relaxed_filters
            )
            
            logger.info(f"Tier 4 found {len(documents)} documents from PostgreSQL")
            return documents
            
        except Exception as e:
            logger.error(f"Tier 4 search failed: {e}")
            return []
    
    def _tier5_metadata_only(
        self,
        filters: Optional[Dict[str, Any]],
        num_docs: int
    ) -> List[Dict[str, Any]]:
        """
        Tier 5: Metadata-only search (last resort).
        
        Returns documents matching metadata filters only.
        Low confidence - used when all text-based searches fail.
        """
        try:
            if not filters:
                logger.warning("Tier 5: No filters provided, cannot perform metadata-only search")
                return []
            
            # Use all available filters
            documents = self.postgres_search_service.metadata_only_search(
                filters=filters,
                limit=num_docs
            )
            
            logger.warning(f"Tier 5 found {len(documents)} documents by metadata only (LOW CONFIDENCE)")
            return documents
            
        except Exception as e:
            logger.error(f"Tier 5 search failed: {e}")
            return []
    
    def _relax_filters_progressively(
        self,
        filters: Optional[Dict[str, Any]],
        tier: int
    ) -> Dict[str, Any]:
        """
        Progressively relax filters based on tier.
        
        Filter relaxation strategy:
        - Tier 1: All filters (original behavior)
        - Tier 2: Remove program, person_type (keep language, jurisdiction)
        - Tier 3: Keep only language
        - Tier 4+: Keep language and maybe jurisdiction
        
        This progressive relaxation helps improve recall when initial searches
        fail due to overly restrictive filters.
        
        Args:
            filters: Original filters
            tier: Current tier (1-5)
        
        Returns:
            Relaxed filters dictionary
        """
        if not filters:
            logger.debug(f"Tier {tier}: No filters to relax")
            return {}
        
        original_filters = filters.copy()
        relaxed = filters.copy()
        
        if tier == 1:
            # Tier 1: Use all filters
            logger.debug(f"Tier {tier}: Using all {len(relaxed)} filters: {list(relaxed.keys())}")
            return relaxed
        
        elif tier == 2:
            # Tier 2: Remove program, person_type
            removed = []
            if 'programs' in relaxed:
                relaxed.pop('programs')
                removed.append('programs')
            if 'person_type' in relaxed:
                relaxed.pop('person_type')
                removed.append('person_type')
            
            logger.info(f"Tier {tier} Filter Relaxation: Removed {removed}, kept {list(relaxed.keys())}")
            return relaxed
        
        elif tier == 3:
            # Tier 3: Keep only language
            result = {'language': relaxed.get('language')} if 'language' in relaxed else {}
            removed_count = len(original_filters) - len(result)
            logger.info(f"Tier {tier} Filter Relaxation: Kept only 'language', removed {removed_count} filters")
            return result
        
        elif tier >= 4:
            # Tier 4+: Keep language and maybe jurisdiction
            result = {}
            kept = []
            
            if 'language' in relaxed:
                result['language'] = relaxed['language']
                kept.append('language')
            if 'jurisdiction' in relaxed:
                result['jurisdiction'] = relaxed['jurisdiction']
                kept.append('jurisdiction')
            
            removed_count = len(original_filters) - len(result)
            logger.info(f"Tier {tier} Filter Relaxation: Kept {kept}, removed {removed_count} filters")
            return result
        
        return relaxed
    
    def get_tier_usage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about multi-tier search usage.
        
        Returns:
            Dictionary with tier usage statistics
        """
        if self.total_queries == 0:
            return {
                'total_queries': 0,
                'tier_usage': {},
                'zero_result_rate': 0.0,
                'message': 'No queries processed yet'
            }
        
        return {
            'total_queries': self.total_queries,
            'tier_usage': {
                'tier_1': {
                    'count': self.tier_usage_stats[1],
                    'percentage': (self.tier_usage_stats[1] / self.total_queries) * 100
                },
                'tier_2': {
                    'count': self.tier_usage_stats[2],
                    'percentage': (self.tier_usage_stats[2] / self.total_queries) * 100
                },
                'tier_3': {
                    'count': self.tier_usage_stats[3],
                    'percentage': (self.tier_usage_stats[3] / self.total_queries) * 100
                },
                'tier_4': {
                    'count': self.tier_usage_stats[4],
                    'percentage': (self.tier_usage_stats[4] / self.total_queries) * 100
                },
                'tier_5': {
                    'count': self.tier_usage_stats[5],
                    'percentage': (self.tier_usage_stats[5] / self.total_queries) * 100
                }
            },
            'zero_result_count': self.zero_result_count,
            'zero_result_rate': (self.zero_result_count / self.total_queries) * 100
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _build_context_string(self, docs: List[Dict[str, Any]]) -> str:
        """
        Build a context string from retrieved documents.
        
        Args:
            docs: List of document dictionaries with title, content, etc.
        
        Returns:
            Formatted context string for LLM
        """
        if not docs:
            return ""
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            title = doc.get('title', 'Untitled Document')
            content = doc.get('content', '')
            citation = doc.get('citation', '')
            section = doc.get('section_number', '')
            
            # Build document section
            doc_section = f"Document {i}: {title}\n"
            
            if section:
                doc_section += f"Section: {section}\n"
            
            if citation:
                doc_section += f"Citation: {citation}\n"
            
            doc_section += f"Content:\n{content}\n"
            
            context_parts.append(doc_section)
        
        # Join with separators
        return "\n---\n\n".join(context_parts)
    
    def _extract_citations(
        self,
        answer: str,
        context_docs: List[Dict[str, Any]]
    ) -> List[Citation]:
        """
        Extract citations from generated answer.
        
        Looks for patterns like:
        - [Document Title, Section X]
        - Section X(Y)
        - Section X
        
        Args:
            answer: Generated answer text
            context_docs: Context documents used for generation
        
        Returns:
            List of Citation objects
        """
        citations = []
        
        # Pattern 1: [Document Title, Section X]
        pattern1 = r'\[([^\]]+),\s*Section\s+([^\]]+)\]'
        for match in re.finditer(pattern1, answer):
            doc_title = match.group(1).strip()
            section = match.group(2).strip()
            
            # Find matching document
            matching_doc = None
            for doc in context_docs:
                if doc_title.lower() in doc.get('title', '').lower():
                    matching_doc = doc
                    break
            
            citation = Citation(
                text=match.group(0),
                document_id=matching_doc['id'] if matching_doc else None,
                document_title=doc_title,
                section=section,
                confidence=0.9 if matching_doc else 0.5
            )
            citations.append(citation)
        
        # Pattern 2: Section X or Section X(Y)
        pattern2 = r'Section\s+(\d+(?:\(\d+\))?)'
        for match in re.finditer(pattern2, answer):
            section = match.group(1).strip()
            
            # Find matching document by section
            matching_doc = None
            for doc in context_docs:
                doc_section = doc.get('section_number', '')
                if doc_section and section.startswith(doc_section):
                    matching_doc = doc
                    break
            
            citation = Citation(
                text=match.group(0),
                document_id=matching_doc['id'] if matching_doc else None,
                document_title=matching_doc.get('title') if matching_doc else None,
                section=section,
                confidence=0.8 if matching_doc else 0.4
            )
            citations.append(citation)
        
        # Remove duplicates
        unique_citations = []
        seen_texts = set()
        for citation in citations:
            if citation.text not in seen_texts:
                seen_texts.add(citation.text)
                unique_citations.append(citation)
        
        return unique_citations
    
    def _calculate_confidence(
        self,
        answer: str,
        citations: List[Citation],
        context_docs: List[Dict[str, Any]],
        intent_confidence: float = 0.8
    ) -> float:
        """
        Calculate confidence score for the answer.
        
        Factors:
        - Number and quality of citations
        - Context document scores
        - Presence of uncertainty phrases
        - Intent confidence from NLP
        - Answer completeness
        
        Args:
            answer: Generated answer text
            citations: Extracted citations
            context_docs: Context documents used
            intent_confidence: Confidence from query intent classification
        
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence from intent
        confidence = intent_confidence
        
        # Citation factor (0.0 - 0.3)
        if citations:
            # Average citation confidence
            avg_citation_conf = sum(c.confidence for c in citations) / len(citations)
            # Number of citations (capped at 5)
            citation_count = min(len(citations), 5) / 5.0
            citation_factor = (avg_citation_conf * 0.7 + citation_count * 0.3) * 0.3
            confidence += citation_factor
        else:
            # Penalty for no citations
            confidence -= 0.15
        
        # Context quality factor (0.0 - 0.2)
        if context_docs:
            # Average document score (assuming scores around 1.0-2.0)
            avg_score = sum(doc.get('score', 0.5) for doc in context_docs) / len(context_docs)
            context_factor = min(avg_score / 2.0, 1.0) * 0.2
            confidence += context_factor
        
        # Uncertainty penalty (-0.0 to -0.3)
        uncertainty_phrases = [
            'not sure', 'uncertain', 'unclear', 'might be', 'possibly',
            'perhaps', 'may be', 'could be', 'I think', 'likely',
            'do not contain', 'does not contain', 'not available',
            'cannot find', 'unable to'
        ]
        
        answer_lower = answer.lower()
        uncertainty_count = sum(1 for phrase in uncertainty_phrases if phrase in answer_lower)
        if uncertainty_count > 0:
            # Each uncertainty phrase reduces confidence
            uncertainty_penalty = min(uncertainty_count * 0.1, 0.3)
            confidence -= uncertainty_penalty
        
        # Answer length factor (-0.1 for very short answers)
        if len(answer) < 100:
            confidence -= 0.1
        
        # Clamp between 0.0 and 1.0
        confidence = max(0.0, min(1.0, confidence))
        
        return round(confidence, 2)
    
    def _get_cache_key(self, question: str) -> str:
        """
        Generate normalized cache key from question.
        
        Normalizes by:
        - Converting to lowercase
        - Stripping whitespace
        - Hashing for consistent key
        
        Args:
            question: User's question
        
        Returns:
            Cache key (hash)
        """
        # Normalize question
        normalized = question.lower().strip()
        
        # Generate hash
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def _get_cached_answer(self, question: str) -> Optional[RAGAnswer]:
        """
        Retrieve cached answer if available and not expired.
        
        Args:
            question: User's question
        
        Returns:
            RAGAnswer if cached and valid, None otherwise
        """
        cache_key = self._get_cache_key(question)
        
        if cache_key not in self.cache:
            return None
        
        answer, timestamp = self.cache[cache_key]
        
        # Check if expired
        if datetime.now() - timestamp > self.cache_ttl:
            # Remove expired entry
            del self.cache[cache_key]
            return None
        
        return answer
    
    def _cache_answer(self, question: str, answer: RAGAnswer) -> None:
        """
        Cache an answer for future use.
        
        Args:
            question: User's question
            answer: RAGAnswer to cache
        """
        cache_key = self._get_cache_key(question)
        self.cache[cache_key] = (answer, datetime.now())
        
        # Simple cache size management (keep last 1000 entries)
        if len(self.cache) > 1000:
            # Remove oldest entry
            oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
    
    def clear_cache(self) -> None:
        """Clear all cached answers."""
        self.cache.clear()
        logger.info("RAG answer cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'total_entries': len(self.cache),
            'cache_ttl_hours': self.cache_ttl.total_seconds() / 3600,
            'max_size': 1000
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on RAG service components.
        
        Returns:
            Health status dictionary
        """
        health = {
            'status': 'healthy',
            'components': {}
        }
        
        # Check search service
        try:
            # Simple check - search service should be available
            health['components']['search'] = {
                'status': 'healthy',
                'available': True
            }
        except Exception as e:
            health['components']['search'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'degraded'
        
        # Check Gemini
        try:
            gemini_health = self.gemini_client.health_check()
            health['components']['gemini'] = gemini_health
            
            if not self.gemini_client.is_available():
                health['status'] = 'degraded'
        except Exception as e:
            health['components']['gemini'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'degraded'
        
        # Check NLP
        try:
            health['components']['nlp'] = {
                'status': 'healthy',
                'available': True
            }
        except Exception as e:
            health['components']['nlp'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health['status'] = 'degraded'
        
        # Cache stats
        health['cache'] = self.get_cache_stats()
        
        # Multi-tier search stats
        health['multi_tier_stats'] = self.get_tier_usage_stats()
        
        return health
