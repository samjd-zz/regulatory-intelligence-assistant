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
    
    # ============================================
    # RAG-SPECIFIC SEARCH OPERATIONS (Tier 3)
    # ============================================
    
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
        full-text indexes.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            language: Language filter ('en' or 'fr')
        
        Returns:
            List of documents formatted for RAG context
        """
        try:
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
                {"query": query, "limit": limit // 2, "language": language}
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
                {"query": query, "limit": limit // 2, "language": language}
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
            
            logger.info(f"Neo4j semantic search found {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Neo4j semantic search failed: {e}")
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
                {"query": seed_query, "limit": limit}
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
