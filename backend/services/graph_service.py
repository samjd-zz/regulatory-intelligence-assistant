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
