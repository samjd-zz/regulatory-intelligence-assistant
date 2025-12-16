"""
Graph service for managing the regulatory knowledge graph in Neo4j.
Provides high-level operations for creating and querying regulatory entities.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, date
import uuid
import logging

from utils.neo4j_client import get_neo4j_client, Neo4jClient

logger = logging.getLogger(__name__)


class GraphService:
    """Service for managing the regulatory knowledge graph."""
    
    def __init__(self, client: Optional[Neo4jClient] = None):
        """
        Initialize graph service.
        
        Args:
            client: Neo4j client (uses global if None)
        """
        self.client = client or get_neo4j_client()
    
    # ============================================
    # LEGISLATION OPERATIONS
    # ============================================
    
    def create_legislation(
        self,
        title: str,
        jurisdiction: str,
        authority: str,
        effective_date: date,
        status: str = "active",
        full_text: Optional[str] = None,
        act_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a legislation node.
        
        Args:
            title: Legislation title
            jurisdiction: Jurisdiction (federal, provincial, municipal)
            authority: Issuing authority
            effective_date: Date when legislation became effective
            status: Status (active, amended, repealed)
            full_text: Full text of legislation
            act_number: Official act number
            metadata: Additional metadata
            
        Returns:
            Created legislation node
        """
        properties = {
            "id": str(uuid.uuid4()),
            "title": title,
            "jurisdiction": jurisdiction,
            "authority": authority,
            "effective_date": effective_date.isoformat(),
            "status": status,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if full_text:
            properties["full_text"] = full_text
        if act_number:
            properties["act_number"] = act_number
        if metadata:
            properties["metadata"] = metadata
        
        return self.client.create_node("Legislation", properties)
    
    def get_legislation(self, legislation_id: str) -> Optional[Dict[str, Any]]:
        """Get legislation by ID."""
        return self.client.find_node("Legislation", {"id": legislation_id})
    
    def find_legislation_by_title(self, title: str) -> List[Dict[str, Any]]:
        """Find legislation by title (partial match)."""
        query = """
        MATCH (l:Legislation)
        WHERE l.title CONTAINS $title
        RETURN l
        """
        results = self.client.execute_query(query, {"title": title})
        return [r['l'] for r in results]
    
    # ============================================
    # SECTION OPERATIONS
    # ============================================
    
    def create_section(
        self,
        section_number: str,
        title: str,
        content: str,
        level: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a section node.
        
        Args:
            section_number: Section number (e.g., "7(1)(a)")
            title: Section title
            content: Section content/text
            level: Nesting level (0 for top level)
            metadata: Additional metadata
            
        Returns:
            Created section node
        """
        properties = {
            "id": str(uuid.uuid4()),
            "section_number": section_number,
            "title": title,
            "content": content,
            "level": level,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if metadata:
            properties["metadata"] = metadata
        
        return self.client.create_node("Section", properties)
    
    def link_section_to_legislation(
        self,
        section_id: str,
        legislation_id: str,
        order: int = 0
    ) -> Dict[str, Any]:
        """
        Create HAS_SECTION relationship between legislation and section.
        
        Args:
            section_id: Section ID
            legislation_id: Legislation ID
            order: Section order within legislation
            
        Returns:
            Relationship summary
        """
        return self.client.create_relationship(
            "Legislation",
            legislation_id,
            "Section",
            section_id,
            "HAS_SECTION",
            {"order": order, "created_at": datetime.utcnow().isoformat()}
        )
    
    def create_section_reference(
        self,
        from_section_id: str,
        to_section_id: str,
        citation_text: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a REFERENCES relationship between sections.
        
        Args:
            from_section_id: Source section ID
            to_section_id: Target section ID
            citation_text: Citation text
            context: Context of reference
            
        Returns:
            Relationship summary
        """
        properties = {
            "citation_text": citation_text,
            "created_at": datetime.utcnow().isoformat()
        }
        if context:
            properties["context"] = context
        
        return self.client.create_relationship(
            "Section",
            from_section_id,
            "Section",
            to_section_id,
            "REFERENCES",
            properties
        )
    
    # ============================================
    # REGULATION OPERATIONS
    # ============================================
    
    def create_regulation(
        self,
        title: str,
        authority: str,
        effective_date: date,
        status: str = "active",
        full_text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a regulation node."""
        properties = {
            "id": str(uuid.uuid4()),
            "title": title,
            "authority": authority,
            "effective_date": effective_date.isoformat(),
            "status": status,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if full_text:
            properties["full_text"] = full_text
        if metadata:
            properties["metadata"] = metadata
        
        return self.client.create_node("Regulation", properties)
    
    def link_regulation_to_legislation(
        self,
        regulation_id: str,
        legislation_id: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create IMPLEMENTS relationship."""
        properties = {"created_at": datetime.utcnow().isoformat()}
        if description:
            properties["description"] = description
        
        return self.client.create_relationship(
            "Regulation",
            regulation_id,
            "Legislation",
            legislation_id,
            "IMPLEMENTS",
            properties
        )
    
    # ============================================
    # POLICY OPERATIONS
    # ============================================
    
    def create_policy(
        self,
        title: str,
        department: str,
        version: str,
        effective_date: date,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a policy node."""
        properties = {
            "id": str(uuid.uuid4()),
            "title": title,
            "department": department,
            "version": version,
            "effective_date": effective_date.isoformat(),
            "created_at": datetime.utcnow().isoformat()
        }
        
        if metadata:
            properties["metadata"] = metadata
        
        return self.client.create_node("Policy", properties)
    
    # ============================================
    # PROGRAM OPERATIONS
    # ============================================
    
    def create_program(
        self,
        name: str,
        department: str,
        description: str,
        eligibility_criteria: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a program node."""
        properties = {
            "id": str(uuid.uuid4()),
            "name": name,
            "department": department,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if eligibility_criteria:
            properties["eligibility_criteria"] = eligibility_criteria
        if metadata:
            properties["metadata"] = metadata
        
        return self.client.create_node("Program", properties)
    
    def link_regulation_to_program(
        self,
        regulation_id: str,
        program_id: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create APPLIES_TO relationship."""
        properties = {"created_at": datetime.utcnow().isoformat()}
        if description:
            properties["description"] = description
        
        return self.client.create_relationship(
            "Regulation",
            regulation_id,
            "Program",
            program_id,
            "APPLIES_TO",
            properties
        )
    
    # ============================================
    # SITUATION OPERATIONS
    # ============================================
    
    def create_situation(
        self,
        description: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a situation node."""
        properties = {
            "id": str(uuid.uuid4()),
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if tags:
            properties["tags"] = tags
        if metadata:
            properties["metadata"] = metadata
        
        return self.client.create_node("Situation", properties)
    
    def link_section_to_situation(
        self,
        section_id: str,
        situation_id: str,
        relevance_score: float,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create RELEVANT_FOR relationship."""
        properties = {
            "relevance_score": relevance_score,
            "created_at": datetime.utcnow().isoformat()
        }
        if description:
            properties["description"] = description
        
        return self.client.create_relationship(
            "Section",
            section_id,
            "Situation",
            situation_id,
            "RELEVANT_FOR",
            properties
        )
    
    # ============================================
    # GRAPH TRAVERSAL & QUERIES
    # ============================================
    
    def get_legislation_with_sections(
        self,
        legislation_id: str
    ) -> Dict[str, Any]:
        """
        Get legislation with all its sections.
        
        Args:
            legislation_id: Legislation ID
            
        Returns:
            Legislation with sections
        """
        query = """
        MATCH (l:Legislation {id: $legislation_id})-[r:HAS_SECTION]->(s:Section)
        RETURN l, collect({section: s, order: r.order}) as sections
        ORDER BY r.order
        """
        results = self.client.execute_query(query, {"legislation_id": legislation_id})
        return results[0] if results else {}
    
    def find_related_regulations(
        self,
        legislation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find all regulations that implement a legislation.
        
        Args:
            legislation_id: Legislation ID
            
        Returns:
            List of regulations
        """
        query = """
        MATCH (l:Legislation {id: $legislation_id})<-[:IMPLEMENTS]-(r:Regulation)
        RETURN r
        """
        results = self.client.execute_query(query, {"legislation_id": legislation_id})
        return [r['r'] for r in results]
    
    def find_cross_references(
        self,
        section_id: str,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find sections that reference or are referenced by a section.
        
        Args:
            section_id: Section ID
            max_depth: Maximum traversal depth
            
        Returns:
            List of related sections with paths
        """
        query = f"""
        MATCH path = (s:Section {{id: $section_id}})-[:REFERENCES*1..{max_depth}]-(related:Section)
        RETURN related, length(path) as depth
        ORDER BY depth
        """
        results = self.client.execute_query(query, {"section_id": section_id})
        return results
    
    def search_legislation_fulltext(
        self,
        search_text: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Full-text search across legislation.
        
        Args:
            search_text: Search query
            limit: Maximum results
            
        Returns:
            Matching legislation
        """
        query = """
        CALL db.index.fulltext.queryNodes('legislation_fulltext', $search_text)
        YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        LIMIT $limit
        """
        results = self.client.execute_query(
            query,
            {"search_text": search_text, "limit": limit}
        )
        return results
    
    def get_graph_overview(self) -> Dict[str, Any]:
        """
        Get overview statistics of the knowledge graph.
        
        Returns:
            Graph statistics
        """
        query = """
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        """
        node_counts = self.client.execute_query(query)
        
        query = """
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        """
        rel_counts = self.client.execute_query(query)
        
        return {
            "nodes": {item['label']: item['count'] for item in node_counts},
            "relationships": {item['type']: item['count'] for item in rel_counts}
        }
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics (alias for get_graph_overview).

        Returns:
            Graph statistics with node and relationship counts
        """
        return self.get_graph_overview()
    
    def clear_all_data(self) -> Dict[str, Any]:
        """
        Clear all nodes and relationships from the knowledge graph.
        
        WARNING: This is a destructive operation that deletes ALL data.
        Use with caution, typically only during force re-ingestion.
        
        Uses batched deletion to prevent heap errors with large datasets.
        
        Returns:
            Dictionary with deletion statistics
        """
        logger.warning("Clearing all data from Neo4j knowledge graph using batched deletion")
        
        try:
            # Delete all nodes and relationships in batches to prevent heap errors
            # APOC version (if available)
            try:
                batch_query = """
                CALL apoc.periodic.iterate(
                    "MATCH (n) RETURN n",
                    "DETACH DELETE n",
                    {batchSize: 10000}
                )
                YIELD batches, total
                RETURN batches, total
                """
                result = self.client.execute_query(batch_query)
                
                if result:
                    batches = result[0].get('batches', 0)
                    total = result[0].get('total', 0)
                    logger.info(f"Deleted {total} nodes in {batches} batches using APOC")
                    
                    return {
                        'status': 'success',
                        'message': f'Deleted {total} nodes in {batches} batches',
                        'batches': batches,
                        'total_deleted': total
                    }
                    
            except Exception as apoc_error:
                # APOC not available or failed, use native Neo4j 5.x batching
                logger.warning(f"APOC batch delete failed ({apoc_error}), using native batching")
                
                # Neo4j 5.x native batching with CALL {} IN TRANSACTIONS
                native_batch_query = """
                CALL {
                    MATCH (n)
                    WITH n LIMIT 10000
                    DETACH DELETE n
                    RETURN count(n) as deleted
                } IN TRANSACTIONS OF 10000 ROWS
                RETURN sum(deleted) as total
                """
                
                result = self.client.execute_query(native_batch_query)
                
                if result:
                    total = result[0].get('total', 0)
                    logger.info(f"Deleted {total} nodes using native batching")
                    
                    return {
                        'status': 'success',
                        'message': f'Deleted {total} nodes using native batching',
                        'total_deleted': total
                    }
            
            logger.info("Successfully cleared all Neo4j data")
            
            return {
                'status': 'success',
                'message': 'All nodes and relationships deleted'
            }
            
        except Exception as e:
            logger.error(f"Failed to clear Neo4j data: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    # ============================================
    # RAG-SPECIFIC SEARCH OPERATIONS (Tier 3)
    # ============================================
    
    def _sanitize_lucene_query(self, query: str) -> str:
        """
        Sanitize query text for Lucene full-text search.
        
        This method:
        1. Removes common stop words
        2. Handles slash-separated terms (GST/HST -> GST OR HST)
        3. Escapes remaining special characters
        4. Uses OR for broader matching
        
        Args:
            query: Raw query text
            
        Returns:
            Sanitized query safe for Lucene
        """
        # Common stop words to filter out
        stop_words = {
            'how', 'is', 'are', 'the', 'a', 'an', 'what', 'when', 'where', 
            'who', 'which', 'this', 'that', 'these', 'those', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'should', 'could', 'may', 'might', 'must', 'can'
        }
        
        # Split query into words
        words = query.split()
        expanded_words = []
        
        for word in words:
            word_lower = word.lower().strip()
            
            # Skip stop words
            if word_lower in stop_words:
                continue
            
            # Handle slash-separated terms (e.g., "GST/HST" -> ["GST", "HST"])
            if '/' in word:
                variants = word.split('/')
                variants_clean = [v.strip() for v in variants if v.strip()]
                expanded_words.extend(variants_clean)
            else:
                # Remove punctuation but keep the word
                clean_word = ''.join(c for c in word if c.isalnum() or c in ('-', '_'))
                if clean_word and clean_word.lower() not in stop_words:
                    expanded_words.append(clean_word)
        
        # If no meaningful terms extracted, use original query
        if not expanded_words:
            logger.warning(f"No meaningful terms extracted from query: '{query}', using original")
            return query
        
        # Join with OR for broader matching (instead of AND)
        # This allows partial matches instead of requiring all terms
        sanitized = ' OR '.join(expanded_words)
        
        logger.info(f"Sanitized Lucene query: '{query}' -> '{sanitized}'")
        return sanitized
    
    def semantic_search_for_rag(
        self,
        query: str,
        limit: int = 20,
        language: str = 'en'
    ) -> List[Dict[str, Any]]:
        """
        Full-text search optimized for RAG context retrieval.
        
        This method is used as Tier 3 in the multi-tier RAG search fallback.
        It searches across both Legislation and Section nodes using Neo4j's
        full-text indexes, with a fallback to simple CONTAINS matching.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            language: Language filter ('en' or 'fr')
        
        Returns:
            List of documents formatted for RAG context
        """
        try:
            # Try full-text search first
            results = self._fulltext_search(query, limit, language)
            
            # If full-text search returns no results, try fallback CONTAINS search
            if not results:
                logger.warning(f"Full-text search returned 0 results, trying fallback CONTAINS search")
                results = self._fallback_contains_search(query, limit, language)
            
            return results
            
        except Exception as e:
            logger.error(f"Neo4j semantic search failed: {e}")
            # Try fallback search even on error
            try:
                return self._fallback_contains_search(query, limit, language)
            except Exception as fallback_error:
                logger.error(f"Fallback search also failed: {fallback_error}")
                return []
    
    def _fulltext_search(
        self,
        query: str,
        limit: int,
        language: str
    ) -> List[Dict[str, Any]]:
        """
        Perform full-text search using Neo4j indexes.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            language: Language filter
            
        Returns:
            List of matching documents
        """
        # Sanitize query to prevent Lucene syntax errors
        sanitized_query = self._sanitize_lucene_query(query)
        
        # Search legislation nodes
        legislation_query = """
        CALL db.index.fulltext.queryNodes('legislation_fulltext', $query)
        YIELD node, score
        WHERE node.language = $language OR $language = 'all'
        RETURN 
            node.id as id,
            node.title as title,
            node.full_text as content,
            node.act_number as citation,
            '' as section_number,
            node.jurisdiction as jurisdiction,
            'legislation' as document_type,
            score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        leg_results = self.client.execute_query(
            legislation_query,
            {"query": sanitized_query, "limit": limit // 2, "language": language}
        )
        
        # Search section nodes
        section_query = """
        CALL db.index.fulltext.queryNodes('section_fulltext', $query)
        YIELD node, score
        MATCH (node)-[:HAS_SECTION]-(leg:Legislation)
        WHERE leg.language = $language OR $language = 'all'
        RETURN 
            node.id as id,
            node.title as title,
            node.content as content,
            leg.act_number as citation,
            node.section_number as section_number,
            leg.jurisdiction as jurisdiction,
            'section' as document_type,
            score
        ORDER BY score DESC
        LIMIT $limit
        """
        
        sec_results = self.client.execute_query(
            section_query,
            {"query": sanitized_query, "limit": limit // 2, "language": language}
        )
        
        # Combine and format results
        documents = []
        
        for result in leg_results + sec_results:
            documents.append({
                'id': result.get('id', ''),
                'title': result.get('title', ''),
                'content': result.get('content', '')[:1500],  # Truncate for RAG
                'citation': result.get('citation', ''),
                'section_number': result.get('section_number', ''),
                'jurisdiction': result.get('jurisdiction', ''),
                'document_type': result.get('document_type', ''),
                'score': float(result.get('score', 0.0))
            })
        
        # Sort by score and limit
        documents.sort(key=lambda x: x['score'], reverse=True)
        documents = documents[:limit]
        
        logger.info(f"Neo4j full-text search found {len(documents)} documents")
        return documents
    
    def _fallback_contains_search(
        self,
        query: str,
        limit: int,
        language: str
    ) -> List[Dict[str, Any]]:
        """
        Fallback search using simple CONTAINS matching.
        
        This is used when full-text search fails or returns no results.
        It's less sophisticated but more reliable.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            language: Language filter
            
        Returns:
            List of matching documents
        """
        # Extract meaningful search terms
        stop_words = {
            'how', 'is', 'are', 'the', 'a', 'an', 'what', 'when', 'where', 
            'who', 'which', 'this', 'that', 'be', 'do', 'does'
        }
        
        words = query.split()
        search_terms = []
        
        for word in words:
            word_lower = word.lower().strip()
            
            # Skip stop words
            if word_lower in stop_words:
                continue
            
            # Handle slash-separated terms
            if '/' in word:
                variants = word.split('/')
                search_terms.extend(v.strip() for v in variants if v.strip())
            else:
                clean_word = ''.join(c for c in word if c.isalnum() or c in ('-', '_'))
                if clean_word and clean_word.lower() not in stop_words:
                    search_terms.append(clean_word)
        
        if not search_terms:
            logger.warning(f"No search terms extracted from query: '{query}'")
            return []
        
        logger.info(f"Fallback CONTAINS search with terms: {search_terms}")
        
        # Build CONTAINS query for each term
        # Use UNWIND to search for any of the terms
        fallback_query = """
        WITH $search_terms AS terms
        UNWIND terms AS term

        // Search legislation
        MATCH (l:Legislation)
        WHERE (l.language = $language OR $language = 'all')
        AND (toLower(l.title) CONTAINS toLower(term) 
            OR toLower(coalesce(l.full_text, '')) CONTAINS toLower(term))
        WITH term, collect(DISTINCT {
        id: l.id,
        title: l.title,
        content: l.full_text,
        citation: l.act_number,
        section_number: '',
        jurisdiction: l.jurisdiction,
        document_type: 'legislation',
        score: CASE 
            WHEN toLower(l.title) CONTAINS toLower(term) THEN 2.0
            ELSE 1.0
        END
        }) AS leg_results

        // Search sections
        OPTIONAL MATCH (s:Section)-[:HAS_SECTION]-(parent:Legislation)
        WHERE (parent.language = $language OR $language = 'all')
        AND (toLower(s.title) CONTAINS toLower(term)
            OR toLower(coalesce(s.content, '')) CONTAINS toLower(term))
        WITH term, leg_results,
            collect(DISTINCT {
            id: s.id,
            title: s.title,
            content: s.content,
            citation: parent.act_number,
            section_number: s.section_number,
            jurisdiction: parent.jurisdiction,
            document_type: 'section',
            score: CASE 
                WHEN toLower(s.title) CONTAINS toLower(term) THEN 2.0
                ELSE 1.0
            END
            }) AS sec_results
        WITH term, leg_results + sec_results AS all_results

        UNWIND all_results AS result
        WITH result
        WHERE result.id IS NOT NULL
        RETURN result
        ORDER BY result.score DESC
        LIMIT $limit
        """
        
        try:
            results = self.client.execute_query(
                fallback_query,
                {
                    "search_terms": search_terms,
                    "limit": limit,
                    "language": language
                }
            )
            
            # Format results
            documents = []
            for row in results:
                result = row['result']
                documents.append({
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': (result.get('content') or '')[:1500],
                    'citation': result.get('citation', ''),
                    'section_number': result.get('section_number', ''),
                    'jurisdiction': result.get('jurisdiction', ''),
                    'document_type': result.get('document_type', ''),
                    'score': float(result.get('score', 1.0))
                })
            
            logger.info(f"Fallback CONTAINS search found {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Fallback CONTAINS search failed: {e}")
            return []
    
    def find_related_documents_by_traversal(
        self,
        seed_query: str,
        max_depth: int = 2,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find related documents by traversing graph relationships.
        
        This method starts with a seed search, then traverses relationships
        (REFERENCES, IMPLEMENTS, HAS_SECTION) to find connected documents.
        Useful when direct text search fails but there are related documents.
        
        Args:
            seed_query: Initial search query to find seed nodes
            max_depth: Maximum traversal depth (1-3 recommended)
            limit: Maximum number of results
        
        Returns:
            List of related documents with traversal paths
        """
        try:
            # Sanitize query to prevent Lucene syntax errors
            sanitized_query = self._sanitize_lucene_query(seed_query)
            
            # First, find seed nodes using full-text search
            seed_query_cypher = f"""
            CALL db.index.fulltext.queryNodes('legislation_fulltext', $query)
            YIELD node, score
            WITH node, score
            ORDER BY score DESC
            LIMIT 5
            
            // Traverse relationships to find related nodes
            MATCH path = (node)-[*1..{max_depth}]-(related)
            WHERE related:Legislation OR related:Section OR related:Regulation
            
            RETURN DISTINCT
                related.id as id,
                related.title as title,
                COALESCE(related.full_text, related.content) as content,
                COALESCE(related.act_number, '') as citation,
                COALESCE(related.section_number, '') as section_number,
                COALESCE(related.jurisdiction, '') as jurisdiction,
                labels(related)[0] as document_type,
                length(path) as depth,
                score as seed_score
            ORDER BY depth ASC, seed_score DESC
            LIMIT $limit
            """
            
            results = self.client.execute_query(
                seed_query_cypher,
                {"query": sanitized_query, "limit": limit}
            )
            
            # Format results
            documents = []
            for result in results:
                # Calculate relevance score (closer = higher score)
                depth = result.get('depth', max_depth)
                seed_score = result.get('seed_score', 0.0)
                relevance_score = seed_score * (1.0 / (depth + 1))
                
                documents.append({
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': (result.get('content') or '')[:1500],
                    'citation': result.get('citation', ''),
                    'section_number': result.get('section_number', ''),
                    'jurisdiction': result.get('jurisdiction', ''),
                    'document_type': result.get('document_type', '').lower(),
                    'score': relevance_score,
                    'traversal_depth': depth
                })
            
            logger.info(f"Neo4j traversal found {len(documents)} related documents")
            return documents
            
        except Exception as e:
            logger.error(f"Neo4j relationship traversal failed: {e}")
            return []
    
    # ============================================
    # BATCH OPERATIONS
    # ============================================
    
    def create_legislation_with_sections(
        self,
        legislation_data: Dict[str, Any],
        sections_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create legislation and all its sections in a single transaction.
        
        Args:
            legislation_data: Legislation properties
            sections_data: List of section properties
            
        Returns:
            Created legislation with section IDs
        """
        # Create legislation
        legislation = self.create_legislation(**legislation_data)
        legislation_id = legislation['id']
        
        # Create sections and link them
        section_ids = []
        for i, section_data in enumerate(sections_data):
            section = self.create_section(**section_data)
            section_id = section['id']
            section_ids.append(section_id)
            
            # Link section to legislation
            self.link_section_to_legislation(section_id, legislation_id, order=i)
        
        return {
            "legislation": legislation,
            "section_ids": section_ids
        }


# Global service instance
_service: Optional[GraphService] = None


def get_graph_service() -> GraphService:
    """Get global graph service instance."""
    global _service
    if _service is None:
        _service = GraphService()
    return _service
