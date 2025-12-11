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

    # System prompt for legal Q&A with few-shot examples
    LEGAL_SYSTEM_PROMPT = """You are an expert assistant helping users understand Canadian government regulations, laws, and policies.

Your role is to:
1. Answer questions accurately based ONLY on the provided context documents
2. Cite specific sections, clauses, or regulations when making claims
3. Be clear when information is not available in the context
4. Explain complex legal concepts in plain language
5. Flag ambiguities or conflicting regulations
6. Provide confidence levels for your answers

Guidelines:
- ALWAYS cite your sources using the document titles and sections provided
- If you're not certain, say so and explain why
- If the context doesn't contain the answer, say "The provided documents do not contain information about [topic]"
- Use clear, accessible language while maintaining legal accuracy
- Format citations as: "[Document Title, Section X]"
- ALWAYS provide a complete answer - never return empty or null responses

IMPORTANT OUTPUT FORMATTING RULES:
1. Structure your answers with clear paragraphs separated by blank lines
2. Use bullet points (with - or •) for listing multiple items or requirements
3. Use numbered lists (1., 2., 3.) for sequential steps or ordered information
4. Bold key terms or section references for emphasis (use **term** format)
5. Start with a clear, direct answer to the question
6. Follow with supporting details and citations
7. End with a note about limitations or additional resources if needed
8. Keep paragraphs concise (2-4 sentences max)

EXAMPLE 1:
Question: "What are the eligibility requirements for Employment Insurance?"
Good Answer: "According to the **Employment Insurance Act**, to qualify for EI benefits, you must meet these key requirements:

**Core Eligibility Criteria:**
- **Loss of employment**: You must have lost your job through no fault of your own [Employment Insurance Act, Section 7]
- **Insurable hours**: You need sufficient insurable hours of employment in the qualifying period [Employment Insurance Regulations, Section 7(2)]
- **Work availability**: You must be available for work and actively seeking employment [Employment Insurance Act, Section 18]
- **Valid documentation**: You must have a valid Social Insurance Number

**Required Hours:**
The specific number of hours required varies by economic region, typically ranging from 420 to 700 hours in the last 52 weeks [Employment Insurance Act, Section 7(2)]. The exact requirement depends on the unemployment rate in your area.

**Note:** These are the basic eligibility requirements. Special rules may apply for specific situations such as maternity/parental benefits, sickness benefits, or compassionate care benefits."

EXAMPLE 2:
Question: "Can permanent residents apply for Old Age Security?"
Good Answer: "**Yes**, permanent residents can apply for Old Age Security (OAS) if they meet the residency and age requirements.

**Eligibility Requirements for Permanent Residents:**
1. **Age**: You must be at least 65 years old [Old Age Security Act, Section 3]
2. **Residency**: You must have resided in Canada for at least 10 years after turning 18 [Old Age Security Act, Section 3(1)]
3. **Legal status**: You must be a Canadian citizen or legal resident at the time of application

**Pension Amounts:**
- **Full pension**: Requires 40 years of residence in Canada after age 18
- **Partial pension**: Available for those with 10-39 years of Canadian residence [Old Age Security Act, Section 3(2)]
- The pension amount is prorated based on your years of residence

**Important:** Time spent in Canada as a temporary resident (e.g., on a work or study permit) does not count toward the 10-year requirement unless it was authorized by an immigration officer."

EXAMPLE 3 (when information is incomplete):
Question: "What is the maximum benefit amount?"
Good Answer: "The context documents reference benefit calculations but **do not provide specific dollar amounts** for the maximum benefit.

**What I Found:**
- The regulations mention benefit rate calculations in [Canada Pension Plan Regulations, Section 45]
- The formula references earnings and contribution periods
- However, the specific maximum dollar amounts are not included in these excerpts

**To Get Current Amounts:**
For the most up-to-date maximum benefit amounts, I recommend:
1. Visit the official Service Canada website
2. Call Service Canada at 1-800-622-6232
3. Consult with a Service Canada office in person

**Note:** Benefit amounts are adjusted annually based on the Consumer Price Index, so current rates may differ from what's in the base legislation."

Remember: You are providing informational guidance, not legal advice. Users should consult official sources or legal professionals for binding interpretations."""

    def __init__(
        self,
        search_service: Optional[SearchService] = None,
        gemini_client: Optional[GeminiClient] = None,
        query_parser: Optional[LegalQueryParser] = None,
        statistics_service: Optional[StatisticsService] = None
    ):
        """
        Initialize RAG service.

        Args:
            search_service: Search service instance
            gemini_client: Gemini client instance
            query_parser: Query parser instance
            statistics_service: Statistics service instance
        """
        self.search_service = search_service or SearchService()
        self.gemini_client = gemini_client or get_gemini_client()
        self.query_parser = query_parser or LegalQueryParser(use_spacy=False)
        self.statistics_service = statistics_service or StatisticsService()

        # Simple in-memory cache (would use Redis in production)
        self.cache: Dict[str, Tuple[RAGAnswer, datetime]] = {}
        self.cache_ttl = timedelta(hours=24)

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

        # Retrieve relevant documents with enhanced query
        enhanced_query = self._enhance_query_for_search(question, parsed_query)
        logger.info(f"Searching for context: {question[:50]}...")
        logger.info(f"Enhanced query: {enhanced_query}")
        
        search_results = self.search_service.hybrid_search(
            query=enhanced_query,
            filters=combined_filters,
            size=num_context_docs,
            keyword_weight=0.6,  # Increased for better exact matching
            vector_weight=0.4    # Reduced to prioritize keyword matches
        )

        if not search_results['hits']:
            # No context found
            return RAGAnswer(
                question=question,
                answer="I don't have enough information in the regulatory documents to answer this question. Please try rephrasing your question or contact a legal expert for assistance.",
                citations=[],
                confidence_score=0.0,
                source_documents=[],
                intent=intent,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata={"error": "no_context_found"}
            )

        # Build context from search results
        context_docs = []
        for hit in search_results['hits']:
            doc = hit['source']
            context_docs.append({
                "id": hit['id'],
                "title": doc.get('title', 'Untitled'),
                "content": doc.get('content', ''),
                "citation": doc.get('citation', ''),
                "section_number": doc.get('section_number', ''),
                "score": hit['score']
            })

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
        
        answer_text = self.gemini_client.generate_with_context(
            query=question,
            context=context_str,
            system_prompt=self.LEGAL_SYSTEM_PROMPT + language_instruction,
            temperature=temperature,
            max_tokens=max_tokens
        )

        if not answer_text:
            return RAGAnswer(
                question=question,
                answer="I encountered an error while generating the answer. Please try again or rephrase your question.",
                citations=[],
                confidence_score=0.0,
                source_documents=context_docs,
                intent=intent,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000,
                metadata={"error": "generation_failed"}
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

        # Build RAG answer
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
                "filters_used": combined_filters
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
    
    def _build_context_string(self, context_docs: List[Dict[str, Any]]) -> str:
        """
        Build context string from documents with intelligent truncation.
        
        Limits content length to prevent input token overflow while maintaining
        the most relevant information for each document.
        """
        context_parts = []
        MAX_CONTENT_LENGTH = 1500  # ~375 tokens per doc, allows 5 docs + system prompt + answer

        for i, doc in enumerate(context_docs, 1):
            doc_str = f"Document {i}: {doc['title']}\n"

            if doc.get('citation'):
                doc_str += f"Citation: {doc['citation']}\n"

            if doc.get('section_number'):
                doc_str += f"Section: {doc['section_number']}\n"

            # Truncate content if too long
            content = doc['content']
            if len(content) > MAX_CONTENT_LENGTH:
                content = content[:MAX_CONTENT_LENGTH] + "... [truncated]"
                logger.debug(f"Truncated document {i} content from {len(doc['content'])} to {MAX_CONTENT_LENGTH} chars")

            doc_str += f"Content: {content}\n"

            context_parts.append(doc_str)

        total_length = sum(len(part) for part in context_parts)
        logger.info(f"Built context with {len(context_parts)} documents, {total_length:,} total characters (~{total_length//4:,} tokens)")

        return "\n---\n".join(context_parts)

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
        - Act Name, s. X
        """
        citations = []

        # Pattern 1: [Document Title, Section X]
        pattern1 = r'\[([^\]]+),\s*(?:Section|s\.?)\s*(\d+(?:\(\d+\))?)\]'
        matches1 = re.finditer(pattern1, answer, re.IGNORECASE)

        for match in matches1:
            doc_title = match.group(1).strip()
            section = match.group(2).strip()

            # Find matching document
            doc_id = None
            for doc in context_docs:
                if doc_title.lower() in doc['title'].lower():
                    doc_id = doc['id']
                    break

            citations.append(Citation(
                text=match.group(0),
                document_id=doc_id,
                document_title=doc_title,
                section=section,
                confidence=0.9 if doc_id else 0.5
            ))

        # Pattern 2: Section X mentions
        pattern2 = r'(?:Section|s\.?)\s+(\d+(?:\(\d+\))?)'
        matches2 = re.finditer(pattern2, answer, re.IGNORECASE)

        for match in matches2:
            section = match.group(1).strip()

            # Try to find document with this section
            doc_id = None
            doc_title = None

            for doc in context_docs:
                if doc.get('section_number') == section:
                    doc_id = doc['id']
                    doc_title = doc['title']
                    break

            # Avoid duplicates
            if not any(c.section == section for c in citations):
                citations.append(Citation(
                    text=match.group(0),
                    document_id=doc_id,
                    document_title=doc_title,
                    section=section,
                    confidence=0.7 if doc_id else 0.4
                ))

        return citations

    def _calculate_confidence(
        self,
        answer: str,
        citations: List[Citation],
        context_docs: List[Dict[str, Any]],
        intent_confidence: float
    ) -> float:
        """
        Calculate confidence score for the answer.

        Factors:
        - Number of citations (more = higher confidence)
        - Citation quality (linked to documents = higher)
        - Answer length appropriateness
        - Context quality (search scores)
        - Intent classification confidence
        """
        scores = []

        # 1. Citation factor (0-1)
        if len(citations) > 0:
            avg_citation_conf = sum(c.confidence for c in citations) / len(citations)
            citation_score = min(0.3 + (len(citations) * 0.15), 1.0)  # Max at ~4 citations
            citation_score *= avg_citation_conf  # Weighted by citation quality
        else:
            citation_score = 0.2  # Low confidence if no citations

        scores.append(citation_score)

        # 2. Answer quality factor (0-1)
        answer_length = len(answer.split())

        if answer_length < 10:
            # Very short answer - probably uncertain
            quality_score = 0.3
        elif answer_length > 500:
            # Very long answer - might be verbose/uncertain
            quality_score = 0.6
        else:
            # Reasonable length
            quality_score = 0.8

        # Check for uncertainty phrases
        uncertainty_phrases = [
            "i don't know",
            "i'm not sure",
            "unclear",
            "ambiguous",
            "not enough information",
            "cannot determine",
            "insufficient"
        ]

        if any(phrase in answer.lower() for phrase in uncertainty_phrases):
            quality_score *= 0.5

        scores.append(quality_score)

        # 3. Context quality factor (0-1)
        if context_docs:
            # Use search scores
            avg_search_score = sum(doc['score'] for doc in context_docs) / len(context_docs)
            # Normalize (search scores can vary, this is a heuristic)
            context_score = min(avg_search_score / 2.0, 1.0)
        else:
            context_score = 0.0

        scores.append(context_score)

        # 4. Intent confidence (0-1)
        scores.append(intent_confidence)

        # Combined confidence (weighted average)
        weights = [0.35, 0.25, 0.25, 0.15]  # Citation, quality, context, intent
        confidence = sum(s * w for s, w in zip(scores, weights))

        return round(confidence, 3)

    def _get_cache_key(self, question: str) -> str:
        """Generate cache key for a question"""
        # Normalize question
        normalized = question.lower().strip()
        # Hash it
        return hashlib.md5(normalized.encode()).hexdigest()

    def _get_cached_answer(self, question: str) -> Optional[RAGAnswer]:
        """Retrieve cached answer if available and not expired"""
        cache_key = self._get_cache_key(question)

        if cache_key in self.cache:
            answer, timestamp = self.cache[cache_key]

            # Check if expired
            if datetime.now() - timestamp < self.cache_ttl:
                return answer
            else:
                # Remove expired entry
                del self.cache[cache_key]

        return None

    def _cache_answer(self, question: str, answer: RAGAnswer):
        """Cache an answer"""
        cache_key = self._get_cache_key(question)
        self.cache[cache_key] = (answer, datetime.now())

        # Simple cache size management
        if len(self.cache) > 1000:
            # Remove oldest 10%
            sorted_keys = sorted(
                self.cache.keys(),
                key=lambda k: self.cache[k][1]
            )
            for key in sorted_keys[:100]:
                del self.cache[key]

    def clear_cache(self):
        """Clear the answer cache"""
        self.cache.clear()
        logger.info("RAG answer cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_entries": len(self.cache),
            "cache_ttl_hours": self.cache_ttl.total_seconds() / 3600,
            "max_size": 1000
        }

    def health_check(self) -> Dict[str, Any]:
        """Check health of RAG service components"""
        health = {
            "status": "healthy",
            "components": {}
        }

        # Check search service
        search_health = self.search_service.health_check()
        health["components"]["search"] = search_health.get("status", "unknown")

        # Check Gemini client
        gemini_health = self.gemini_client.health_check()
        health["components"]["gemini"] = gemini_health.get("status", "unknown")

        # Check query parser
        health["components"]["nlp"] = "operational"

        # Overall status
        if any(status != "healthy" for status in health["components"].values()):
            if "unavailable" in health["components"].values():
                health["status"] = "degraded"
            else:
                health["status"] = "partial"

        health["cache_stats"] = self.get_cache_stats()

        return health


if __name__ == "__main__":
    # Test the RAG service
    print("=" * 80)
    print("RAG Service - Test")
    print("=" * 80)

    rag = RAGService()

    # Health check
    print("\n1. Health Check:")
    health = rag.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Components: {health['components']}")

    # Test question answering (requires Gemini API key and indexed documents)
    print("\n2. Question Answering Test:")
    question = "Can a temporary resident apply for employment insurance?"

    print(f"   Question: {question}")

    answer = rag.answer_question(
        question=question,
        num_context_docs=3,
        use_cache=False
    )

    print(f"\n   Answer: {answer.answer[:200]}...")
    print(f"   Confidence: {answer.confidence_score:.2f}")
    print(f"   Citations: {len(answer.citations)}")

    for i, citation in enumerate(answer.citations[:3], 1):
        print(f"      {i}. {citation.text} (confidence: {citation.confidence:.2f})")

    print(f"   Source Documents: {len(answer.source_documents)}")
    print(f"   Processing Time: {answer.processing_time_ms:.0f}ms")

    print("\n" + "=" * 80)
    print("Test complete!")
