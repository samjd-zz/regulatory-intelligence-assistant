"""
Graph service for managing the regulatory knowledge graph in Neo4j.
Provides high-level operations for creating and querying regulatory entities.
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import uuid
import logging
import re

from utils.neo4j_client import get_neo4j_client, Neo4jClient

try:
    from config.legal_synonyms import expand_query_with_synonyms
    SYNONYMS_AVAILABLE = True
except ImportError:
    SYNONYMS_AVAILABLE = False
    def expand_query_with_synonyms(query: str) -> str:
        return query

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
        self._indexes_checked = False
    
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
        try:
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
        except Exception as e:
            if "legislation_fulltext" in str(e):
                logger.warning(f"Fulltext index missing, attempting to create: {e}")
                if self._ensure_fulltext_indexes():
                    # Retry the query after creating indexes
                    try:
                        results = self.client.execute_query(
                            query,
                            {"search_text": search_text, "limit": limit}
                        )
                        return results
                    except Exception as retry_error:
                        logger.error(f"Fulltext search failed after index creation: {retry_error}")
                        return []
                else:
                    logger.error(f"Failed to create fulltext indexes")
                    return []
            else:
                logger.error(f"Fulltext search failed: {e}")
                return []
    
    def get_graph_overview(self) -> Dict[str, Any]:
        """
        Get overview statistics of the knowledge graph including indexes.
        
        Returns:
            Graph statistics with node counts, relationship counts, and index info
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
        
        # Get index information
        indexes_query = "SHOW INDEXES"
        try:
            index_results = self.client.execute_query(indexes_query)
            fulltext_indexes = []
            range_indexes = []
            
            for idx in index_results:
                idx_type = idx.get('type', '')
                idx_name = idx.get('name', '')
                idx_state = idx.get('state', '')
                read_count = idx.get('readCount', 0)
                
                if idx_type == 'FULLTEXT':
                    fulltext_indexes.append({
                        'name': idx_name,
                        'state': idx_state,
                        'read_count': read_count,
                        'labels': idx.get('labelsOrTypes', []),
                        'properties': idx.get('properties', [])
                    })
                elif idx_type == 'RANGE':
                    range_indexes.append({
                        'name': idx_name,
                        'labels': idx.get('labelsOrTypes', []),
                        'properties': idx.get('properties', [])
                    })
            
            indexes_info = {
                'fulltext_count': len(fulltext_indexes),
                'range_count': len(range_indexes),
                'fulltext_indexes': fulltext_indexes[:5],  # Limit for readability
                'query_expansion': SYNONYMS_AVAILABLE
            }
        except Exception as e:
            logger.warning(f"Could not retrieve index information: {e}")
            indexes_info = {'error': str(e)}
        
        return {
            "nodes": {item['label']: item['count'] for item in node_counts},
            "relationships": {item['type']: item['count'] for item in rel_counts},
            "indexes": indexes_info
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
    
    def _ensure_fulltext_indexes(self) -> bool:
        """
        Ensure that required fulltext indexes exist in Neo4j.
        
        Creates the following indexes if they don't exist:
        - legislation_fulltext: For searching Legislation nodes
        - section_fulltext: For searching Section nodes
        - regulation_fulltext: For searching Regulation nodes
        
        Returns:
            True if indexes exist or were created successfully, False otherwise
        """
        try:
            # Create fulltext indexes using the same syntax as init_graph.cypher
            fulltext_indexes = [
                """
                CREATE FULLTEXT INDEX legislation_fulltext IF NOT EXISTS
                FOR (l:Legislation) ON EACH [l.title, l.full_text, l.act_number]
                """,
                """
                CREATE FULLTEXT INDEX regulation_fulltext IF NOT EXISTS
                FOR (r:Regulation) ON EACH [r.title, r.full_text]
                """,
                """
                CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
                FOR (s:Section) ON EACH [s.title, s.content, s.section_number]
                """
            ]
            
            for index_query in fulltext_indexes:
                try:
                    clean_query = ' '.join(line.strip() for line in index_query.split('\n') if line.strip())
                    self.client.execute_query(clean_query)
                    logger.debug(f"Ensured fulltext index: {clean_query[:50]}...")
                except Exception as e:
                    if "already exists" in str(e) or "Equivalent" in str(e):
                        logger.debug(f"Fulltext index already exists: {e}")
                    else:
                        logger.warning(f"Could not create fulltext index: {e}")
            
            logger.info("✅ All fulltext indexes are ensured")
            return True
                
        except Exception as e:
            logger.error(f"Failed to ensure fulltext indexes: {e}")
            return False
    
    # ============================================
    # RAG-SPECIFIC SEARCH OPERATIONS (Tier 3)
    # ============================================
    
    def _extract_snippet(self, text: str, query_terms: List[str], max_length: int = 500) -> Tuple[str, bool]:
        """
        Extract a relevant snippet from text containing query terms.
        
        Args:
            text: Full text to extract from
            query_terms: List of query terms to highlight
            max_length: Maximum snippet length
            
        Returns:
            Tuple of (snippet with highlights, found_match)
        """
        if not text:
            return '', False
        
        text_lower = text.lower()
        
        # Find first occurrence of any query term
        best_pos = -1
        matched_term = None
        
        for term in query_terms:
            term_lower = term.lower()
            pos = text_lower.find(term_lower)
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos
                matched_term = term
        
        if best_pos == -1:
            # No match found, return beginning
            snippet = text[:max_length]
            if len(text) > max_length:
                snippet += '...'
            return snippet, False
        
        # Extract context around the match
        start = max(0, best_pos - max_length // 2)
        end = min(len(text), start + max_length)
        
        snippet = text[start:end]
        
        # Add ellipsis
        if start > 0:
            snippet = '...' + snippet
        if end < len(text):
            snippet += '...'
        
        # Highlight all query terms
        for term in query_terms:
            # Use regex for case-insensitive replacement
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            snippet = pattern.sub(lambda m: f'<mark>{m.group(0)}</mark>', snippet)
        
        return snippet, True
    
    def _sanitize_lucene_query(self, query: str) -> str:
        """
        Sanitize query text for Lucene full-text search.
        
        This method:
        1. Expands query with legal synonyms (if available)
        2. Removes common stop words
        3. Handles slash-separated terms (GST/HST -> GST OR HST)
        4. Escapes remaining special characters
        5. Uses OR for broader matching
        
        Args:
            query: Raw query text
            
        Returns:
            Sanitized query safe for Lucene
        """
        # Apply legal synonym expansion if available
        if SYNONYMS_AVAILABLE:
            expanded_query = expand_query_with_synonyms(query)
            if expanded_query != query:
                logger.info(f"Expanded query with synonyms: '{query}' -> '{expanded_query}'")
                query = expanded_query
        
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
        # Ensure fulltext indexes exist before searching
        if not self._indexes_checked:
            self._ensure_fulltext_indexes()
            self._indexes_checked = True
        
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
        
        leg_results = []
        reg_results = []
        
        # Try searching Legislation nodes (if any exist)
        try:
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
                {"query": sanitized_query, "limit": limit // 3, "language": language}
            )
        except Exception as e:
            logger.debug(f"Legislation search returned no results or index missing: {e}")
            leg_results = []
        
        # Search Regulation nodes (primary data source)
        try:
            regulation_query = """
            CALL db.index.fulltext.queryNodes('regulation_fulltext', $query)
            YIELD node, score
            WHERE node.language = $language OR $language = 'all'
            RETURN 
                node.id as id,
                node.title as title,
                node.full_text as content,
                coalesce(node.act_number, '') as citation,
                '' as section_number,
                coalesce(node.jurisdiction, '') as jurisdiction,
                'regulation' as document_type,
                score
            ORDER BY score DESC
            LIMIT $limit
            """
            
            reg_results = self.client.execute_query(
                regulation_query,
                {"query": sanitized_query, "limit": limit // 3, "language": language}
            )
        except Exception as e:
            if "regulation_fulltext" in str(e):
                logger.error(f"Neo4j regulation search failed: {e}")
                logger.info("Attempting to create missing fulltext indexes...")
                if self._ensure_fulltext_indexes():
                    try:
                        reg_results = self.client.execute_query(
                            regulation_query,
                            {"query": sanitized_query, "limit": limit // 3, "language": language}
                        )
                    except Exception as retry_error:
                        logger.error(f"Regulation search failed after index creation: {retry_error}")
                        reg_results = []
                else:
                    logger.error(f"Failed to create fulltext indexes")
                    reg_results = []
            else:
                logger.error(f"Neo4j regulation search failed: {e}")
                reg_results = []
        
        # Search section nodes
        sec_results = []
        try:
            section_query = """
            CALL db.index.fulltext.queryNodes('section_fulltext', $query)
            YIELD node, score
            MATCH (node)-[:HAS_SECTION|PART_OF]-(parent)
            WHERE (parent:Regulation OR parent:Legislation)
            AND (parent.language = $language OR $language = 'all')
            RETURN 
                node.id as id,
                node.title as title,
                node.content as content,
                coalesce(parent.act_number, '') as citation,
                node.section_number as section_number,
                coalesce(parent.jurisdiction, '') as jurisdiction,
                'section' as document_type,
                score
            ORDER BY score DESC
            LIMIT $limit
            """
            
            sec_results = self.client.execute_query(
                section_query,
                {"query": sanitized_query, "limit": limit // 3, "language": language}
            )
        except Exception as e:
            if "section_fulltext" in str(e):
                logger.error(f"Neo4j section search failed: {e}")
                logger.info("Section fulltext index missing, using fallback search")
                sec_results = []
            else:
                logger.error(f"Neo4j section search failed: {e}")
                sec_results = []
        
        # Combine and format results with snippets
        documents = []
        
        # Extract query terms for snippet highlighting
        query_terms = [w.strip() for w in sanitized_query.split(' OR ') if w.strip()]
        
        for result in leg_results + reg_results + sec_results:
            content = result.get('content', '')
            
            # Generate snippet with highlights
            snippet, has_match = self._extract_snippet(content, query_terms, max_length=1500)
            
            # Boost score if snippet contains highlighted match
            base_score = float(result.get('score', 0.0))
            adjusted_score = base_score * 1.2 if has_match else base_score
            
            documents.append({
                'id': result.get('id', ''),
                'title': result.get('title', ''),
                'content': snippet,
                'full_content': content[:3000],  # Keep more context for RAG
                'citation': result.get('citation', ''),
                'section_number': result.get('section_number', ''),
                'jurisdiction': result.get('jurisdiction', ''),
                'document_type': result.get('document_type', ''),
                'score': adjusted_score,
                'has_highlight': has_match
            })
        
        # Sort by adjusted score and limit
        documents.sort(key=lambda x: x['score'], reverse=True)
        documents = documents[:limit]
        
        logger.info(f"Neo4j full-text search found {len(documents)} documents (avg score: {sum(d['score'] for d in documents) / len(documents) if documents else 0:.4f})")
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
        It is less sophisticated but more reliable.
        
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
    
    def similarity_search(
        self,
        query: str,
        limit: int = 20,
        language: str = 'en',
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Fuzzy similarity search using Levenshtein distance approximation.
        
        This is useful for typo-tolerant search when full-text search fails.
        Uses case-insensitive CONTAINS matching with scoring based on
        match position and frequency.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            language: Language filter ('en' or 'fr')
            min_similarity: Minimum similarity threshold (0.0-1.0)
        
        Returns:
            List of similar documents with similarity scores
        """
        # Extract search terms
        query_lower = query.lower()
        terms = [t.strip() for t in query_lower.split() if len(t.strip()) > 2]
        
        if not terms:
            logger.warning(f"No valid search terms for similarity search: '{query}'")
            return []
        
        logger.info(f"Similarity search for terms: {terms}")
        
        # Build similarity query
        # Score based on: title match (high), content match (medium), term frequency
        similarity_query = """
        WITH $terms AS search_terms, $min_sim AS min_similarity, $language AS lang
        
        // Search in Regulations (primary data source)
        MATCH (r:Regulation)
        WHERE r.language = lang OR lang = 'all'
        WITH r, search_terms, min_similarity,
            size([term IN search_terms WHERE toLower(r.title) CONTAINS term]) AS title_count,
            size([term IN search_terms WHERE toLower(coalesce(r.full_text, '')) CONTAINS term]) AS content_count,
            size(search_terms) AS total_terms
        WHERE (title_count + content_count) > 0
        WITH r,
            (toFloat(title_count) * 3.0 + toFloat(content_count)) / toFloat(total_terms) AS similarity,
            title_count, content_count
        WHERE similarity >= min_similarity
        
        RETURN
            r.id as id,
            r.title as title,
            r.full_text as content,
            coalesce(r.act_number, '') as citation,
            '' as section_number,
            coalesce(r.jurisdiction, '') as jurisdiction,
            'regulation' as document_type,
            similarity as score,
            title_count as title_matches,
            content_count as content_matches
        
        UNION ALL
        
        // Search in Sections
        MATCH (s:Section)-[:HAS_SECTION|PART_OF]-(parent)
        WHERE (parent:Regulation OR parent:Legislation)
        AND (parent.language = $language OR $language = 'all')
        WITH s, parent, $terms AS search_terms, $min_sim AS min_similarity,
            size([term IN $terms WHERE toLower(coalesce(s.title, '')) CONTAINS term]) AS title_count,
            size([term IN $terms WHERE toLower(coalesce(s.content, '')) CONTAINS term]) AS content_count,
            size($terms) AS total_terms
        WHERE (title_count + content_count) > 0
        WITH s, parent,
            (toFloat(title_count) * 3.0 + toFloat(content_count)) / toFloat(total_terms) AS similarity,
            title_count, content_count
        WHERE similarity >= min_similarity
        
        RETURN
            s.id as id,
            coalesce(s.title, s.section_number) as title,
            s.content as content,
            coalesce(parent.act_number, '') as citation,
            s.section_number as section_number,
            coalesce(parent.jurisdiction, '') as jurisdiction,
            'section' as document_type,
            similarity as score,
            title_count as title_matches,
            content_count as content_matches
        
        ORDER BY score DESC
        LIMIT $limit
        """
        
        try:
            results = self.client.execute_query(
                similarity_query,
                {
                    'terms': terms,
                    'limit': limit,
                    'language': language,
                    'min_sim': min_similarity
                }
            )
            
            # Format results with snippets
            documents = []
            for result in results:
                content = result.get('content', '')
                snippet, has_match = self._extract_snippet(content, terms, max_length=1500)
                
                documents.append({
                    'id': result.get('id', ''),
                    'title': result.get('title', ''),
                    'content': snippet,
                    'full_content': content[:3000],
                    'citation': result.get('citation', ''),
                    'section_number': result.get('section_number', ''),
                    'jurisdiction': result.get('jurisdiction', ''),
                    'document_type': result.get('document_type', ''),
                    'score': float(result.get('score', 0.0)),
                    'similarity_type': 'fuzzy',
                    'title_matches': result.get('title_matches', 0),
                    'content_matches': result.get('content_matches', 0)
                })
            
            logger.info(f"Similarity search found {len(documents)} documents (min_similarity={min_similarity})")
            return documents
            
        except Exception as e:
            logger.error(f"Neo4j similarity search failed: {e}")
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
