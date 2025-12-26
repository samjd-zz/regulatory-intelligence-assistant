from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class GraphRelationshipService:
    """Service for querying Neo4j graph relationships"""
    def __init__(self, neo4j_client):
        self.client = neo4j_client

    def find_amends(self, amendment_id: Optional[str] = None, regulation_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Find regulations amended by an amendment (AMENDS)"""
        query = """
        MATCH (a:Amendment)-[r:AMENDS]->(r:Regulation)
        WHERE ($amendment_id IS NULL OR a.id = $amendment_id)
          AND ($regulation_id IS NULL OR r.id = $regulation_id)
        RETURN a.id AS amendment_id,
               a.bill_number AS bill_number,
               r.id AS regulation_id,
               r.title AS regulation_title,
               r.jurisdiction AS jurisdiction,
               r.status AS status,
               r.language AS language,
               r.node_type AS node_type,
               r.created_at AS created_at,
               r.effective_date AS effective_date,
               r.metadata AS metadata,
               r.full_text AS full_text,
               r.authority AS authority,
               r.extra_metadata AS extra_metadata,
               r.last_amended AS last_amended,
               r.amendment_info AS amendment_info
        LIMIT $limit
        """
        return self.client.execute_query(
            query,
            {"amendment_id": amendment_id, "regulation_id": regulation_id, "limit": limit}
        )

    def find_supersedes(self, amendment_id: Optional[str] = None, legislation_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Find legislation superseded by an amendment (SUPERSEDES)"""
        query = """
        MATCH (a:Amendment)-[r:SUPERSEDES]->(l:Legislation)
        WHERE ($amendment_id IS NULL OR a.id = $amendment_id)
          AND ($legislation_id IS NULL OR l.id = $legislation_id)
        RETURN a.id AS amendment_id,
               a.bill_number AS bill_number,
               l.id AS legislation_id,
               l.title AS legislation_title,
               r.chapter AS chapter,
               r.created_at AS created_at
        LIMIT $limit
        """
        return self.client.execute_query(
            query,
            {"amendment_id": amendment_id, "legislation_id": legislation_id, "limit": limit}
        )

    def find_has_section(
        self,
        legislation_id: Optional[str] = None,
        legislation_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find sections belonging to a legislation (HAS_SECTION)"""
        query = """
        MATCH (l:Legislation)-[r:HAS_SECTION]->(s:Section)
        WHERE ($legislation_id IS NULL OR l.id = $legislation_id)
          AND ($legislation_title IS NULL OR l.title CONTAINS $legislation_title)
        RETURN l.title AS legislation_title,
               l.id AS legislation_id,
               s.title AS section_title,
               s.id AS section_id,
               s.section_number AS section_number,
               r.order AS section_order,
               r.created_at AS created_at
        ORDER BY r.order
        LIMIT $limit
        """
        return self.client.execute_query(
            query,
            {
                "legislation_id": legislation_id,
                "legislation_title": legislation_title,
                "limit": limit
            }
        )

    def find_part_of(
        self,
        section_id: Optional[str] = None,
        section_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find parent-child section hierarchy (PART_OF)"""
        query = """
        MATCH (child:Section)-[r:PART_OF]->(parent:Section)
        WHERE ($section_id IS NULL OR child.id = $section_id)
          AND ($section_title IS NULL OR child.title CONTAINS $section_title)
        RETURN child.title AS child_title,
               child.id AS child_id,
               parent.title AS parent_title,
               parent.id AS parent_id,
               r.created_at AS created_at
        LIMIT $limit
        """
        return self.client.execute_query(
            query,
            {
                "section_id": section_id,
                "section_title": section_title,
                "limit": limit
            }
        )

    def find_relevant_for(
        self,
        section_title: Optional[str] = None,
        situation_description: Optional[str] = None,
        relationship_type: str = "references"
    ) -> List[Dict[str, Any]]:
        """Find sections relevant for a situation (RELEVANT_FOR)"""
        query = """
        MATCH (s:Section)-[r:RELEVANT_FOR]->(sit:Situation)
        WHERE ($situation_description IS NULL OR sit.description CONTAINS $situation_description)
        RETURN s.title AS section_title,
               s.id AS section_id,
               sit.description AS situation_description,
               sit.id AS situation_id,
               r.relevance_score AS relevance_score,
               r.created_at AS created_at
        """
        return self.client.execute_query(
            query,
            {
                "situation_description": situation_description
            }
        )
    
    def find_references(
        self, 
        source_id: Optional[str] = None,
        source_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find what a legislation/regulation references (outgoing REFERENCES relationships)"""
        query = """
        MATCH (source)-[r:REFERENCES]->(target)
        WHERE (source:Legislation OR source:Regulation OR source:Policy)
          AND (target:Legislation OR target:Regulation OR target:Policy)
          AND ($source_id IS NULL OR source.id = $source_id)
          AND ($source_title IS NULL OR source.title CONTAINS $source_title)
        RETURN 
            source.title AS source_title,
            source.id AS source_id,
            labels(source)[0] AS source_type,
            target.title AS target_title,
            target.id AS target_id,
            labels(target)[0] AS target_type,
            r.citation_text AS citation_text,
            r.created_at AS created_at
        LIMIT $limit
        """
        return self.client.execute_query(
            query,
            {
                "source_id": source_id,
                "source_title": source_title,
                "limit": limit
            }
        )
    
    def find_referenced_by(
        self,
        target_id: Optional[str] = None,
        target_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find what references a legislation/regulation (incoming REFERENCES relationships)"""
        query = """
        MATCH (source)-[r:REFERENCES]->(target)
        WHERE (source:Legislation OR source:Regulation OR source:Policy)
          AND (target:Legislation OR target:Regulation OR target:Policy)
          AND ($target_id IS NULL OR target.id = $target_id)
          AND ($target_title IS NULL OR target.title CONTAINS $target_title)
        RETURN 
            source.title AS referencing_document,
            source.id AS source_id,
            labels(source)[0] AS source_type,
            target.title AS referenced_document,
            target.id AS target_id,
            labels(target)[0] AS target_type,
            r.citation_text AS citation_text,
            r.created_at AS created_at
        LIMIT $limit
        """
        return self.client.execute_query(
            query,
            {
                "target_id": target_id,
                "target_title": target_title,
                "limit": limit
            }
        )
    
    def find_implementations(
        self,
        legislation_title: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Find regulations that implement legislation (IMPLEMENTS)"""
        query = """
        MATCH (reg:Regulation)-[r:IMPLEMENTS]->(leg:Legislation)
        WHERE $legislation_title IS NULL OR leg.title CONTAINS $legislation_title
        RETURN 
            reg.title AS regulation_title,
            reg.id AS regulation_id,
            leg.title AS legislation_title,
            leg.id AS legislation_id,
            r.description AS description,
            r.created_at AS created_at
        LIMIT $limit
        """
        return self.client.execute_query(
            query,
            {"legislation_title": legislation_title, "limit": limit}
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
                if rel.get('citation_text'):
                    answer += f" ({rel['citation_text']})"
                answer += "\n"
            
            elif relationship_type == "referenced_by":
                answer += f"{i}. **{rel['referencing_document']}** references this document"
                if rel.get('citation_text'):
                    answer += f" ({rel['citation_text']})"
                answer += "\n"
            
            elif relationship_type == "implementations":
                answer += f"{i}. **{rel['regulation_title']}** implements **{rel['legislation_title']}**"
                if rel.get('description'):
                    answer += f" - {rel['description']}"
                answer += "\n"
            
            elif relationship_type == "has_section":
                answer += f"{i}. **{rel['legislation_title']}** has section **{rel['section_title']}**"
                if rel.get('section_number'):
                    answer += f" (Section {rel['section_number']})"
                answer += "\n"
            
            elif relationship_type == "applies_to":
                answer += f"{i}. **{rel['regulation_title']}** applies to **{rel['program_name']}**\n"
            
            elif relationship_type == "relevant_for":
                answer += f"{i}. **{rel['section_title']}** is relevant for: {rel['situation_description']}"
                if rel.get('relevance_score'):
                    answer += f" (relevance: {rel['relevance_score']:.2f})"
                answer += "\n"
        
        if count > 10:
            answer += f"\n... and {count - 10} more {relationship_type}."
        
        return answer.strip()
