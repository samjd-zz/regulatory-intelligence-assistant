from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class GraphRelationshipService:
    """Service for querying Neo4j graph relationships"""
    def __init__(self, neo4j_client):
        self.client = neo4j_client
    
    def find_references(
        self, 
        document_id: Optional[str] = None,
        document_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find what a document references (outgoing CITES relationships)"""
        
        query = """
        MATCH (source:Document)-[r:CITES]->(target:Document)
        WHERE $document_id IS NULL OR source.id = $document_id
        OR ($document_title IS NOT NULL AND source.title CONTAINS $document_title)
        RETURN 
            source.title AS source_title,
            source.id AS source_id,
            target.title AS target_title,
            target.id AS target_id,
            r.section AS cited_section,
            type(r) AS relationship_type
        LIMIT $limit
        """
        
        return self.client.execute_query(
            query,
            {
                "document_id": document_id,
                "document_title": document_title,
                "limit": limit
            }
        )
    
    def find_referenced_by(
        self,
        document_id: Optional[str] = None,
        document_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find what references a document (incoming CITES relationships)"""
        
        query = """
        MATCH (source:Document)-[r:CITES]->(target:Document)
        WHERE $document_id IS NULL OR target.id = $document_id
        OR ($document_title IS NOT NULL AND target.title CONTAINS $document_title)
        RETURN 
            source.title AS referencing_document,
            source.id AS source_id,
            target.title AS referenced_document,
            target.id AS target_id,
            r.section AS cited_section,
            type(r) AS relationship_type
        LIMIT $limit
        """
        
        return self.client.execute_query(
            query,
            {
                "document_id": document_id,
                "document_title": document_title,
                "limit": limit
            }
        )
    
    def find_amendments(
        self,
        document_id: Optional[str] = None,
        document_title: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find amendments to a document"""
        
        query = """
        MATCH (source:Document)-[r:AMENDS]->(target:Document)
        WHERE $document_id IS NULL OR target.id = $document_id
        OR ($document_title IS NOT NULL AND target.title CONTAINS $document_title)
        RETURN 
            source.title AS amending_document,
            source.id AS source_id,
            target.title AS amended_document,
            target.id AS target_id,
            r.effective_date AS effective_date,
            type(r) AS relationship_type
        """
        
        return self.client.execute_query(
            query,
            {
                "document_id": document_id,
                "document_title": document_title
            }
        )
    
    def find_implementations(
        self,
        act_title: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find regulations that implement an act"""
        
        query = """
        MATCH (reg:Document)-[r:IMPLEMENTS]->(act:Document)
        WHERE $act_title IS NULL OR act.title CONTAINS $act_title
        RETURN 
            reg.title AS regulation_title,
            reg.id AS regulation_id,
            act.title AS act_title,
            act.id AS act_id,
            type(r) AS relationship_type
        """
        
        return self.client.execute_query(
            query,
            {"act_title": act_title}
        )
    
    def format_relationship_answer(
        self,
        relationships: List[Dict[str, Any]],
        question: str,
        relationship_type: str = "references"
    ) -> str:
        """Format graph relationships into natural language"""
        
        if not relationships:
            return f"I couldn't find any {relationship_type} for the specified document in the knowledge graph."
        
        count = len(relationships)
        
        # Build natural language response
        answer = f"Based on the knowledge graph, I found {count} {relationship_type}:\n\n"
        
        for i, rel in enumerate(relationships[:10], 1):  # Limit to top 10 for readability
            if relationship_type == "references":
                answer += f"{i}. **{rel['source_title']}** references **{rel['target_title']}**"
                if rel.get('cited_section'):
                    answer += f" (Section {rel['cited_section']})"
                answer += "\n"
            
            elif relationship_type == "referenced_by":
                answer += f"{i}. **{rel['referencing_document']}** references this document"
                if rel.get('cited_section'):
                    answer += f" (citing Section {rel['cited_section']})"
                answer += "\n"
            
            elif relationship_type == "amendments":
                answer += f"{i}. **{rel['amending_document']}** amends this document"
                if rel.get('effective_date'):
                    answer += f" (effective {rel['effective_date']})"
                answer += "\n"
            
            elif relationship_type == "implementations":
                answer += f"{i}. **{rel['regulation_title']}** implements this act\n"
        
        if count > 10:
            answer += f"\n... and {count - 10} more {relationship_type}."
        
        return answer.strip()