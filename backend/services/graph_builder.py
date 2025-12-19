"""
Graph Builder Service for populating Neo4j knowledge graph from parsed documents.
Extracts entities, creates nodes, and builds relationships.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import logging
import re

from models.document_models import (
    Document, DocumentSection, DocumentSubsection, 
    DocumentClause, CrossReference, DocumentType
)
from models import Regulation, Section
from utils.neo4j_client import Neo4jClient
from services.document_parser import DocumentParser

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builds and populates the Neo4j knowledge graph from parsed documents.
    """
    
    def __init__(self, db: Session, neo4j_client: Neo4jClient):
        """
        Initialize graph builder.
        
        Args:
            db: SQLAlchemy database session
            neo4j_client: Neo4j client instance
        """
        self.db = db
        self.neo4j = neo4j_client
        self.stats = {
            "nodes_created": 0,
            "relationships_created": 0,
            "errors": []
        }
        
        # Ensure fulltext indexes exist for graph search functionality
        self._ensure_fulltext_indexes()
    
    def _ensure_fulltext_indexes(self):
        """
        Ensure that required fulltext indexes exist in Neo4j.
        
        This is called during GraphBuilder initialization to ensure that
        fulltext search capabilities are available whenever we build graphs.
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
                    self.neo4j.execute_query(clean_query)
                    logger.debug(f"Ensured fulltext index: {clean_query[:50]}...")
                except Exception as e:
                    if "already exists" in str(e) or "Equivalent" in str(e):
                        logger.debug(f"Fulltext index already exists")
                    else:
                        logger.warning(f"Could not create fulltext index: {e}")
            
            logger.info("✅ All fulltext indexes are ensured for graph building")
            
        except Exception as e:
            # Log warning but don't fail the graph building process
            logger.warning(f"Could not ensure fulltext indexes: {e}")
    
    def build_document_graph(self, document_id: uuid.UUID) -> Dict[str, Any]:
        """
        Build graph for a single document.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Statistics about graph construction
        """
        logger.info(f"Building graph for document {document_id}")
        
        # Fetch document from database
        document = self.db.query(Document).filter_by(id=document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        try:
            # Create legislation/regulation node
            node_type = self._get_node_type(document.document_type)
            doc_node = self._create_document_node(document, node_type)
            
            # Create section nodes and relationships
            section_nodes = self._create_section_nodes(document)
            
            # Create hierarchy relationships (PART_OF)
            self._create_hierarchy_relationships(document)
            
            # Create cross-reference relationships
            self._create_cross_reference_relationships(document)
            
            # Extract and create entities (Programs, Situations)
            self._extract_and_create_entities(document)
            
            logger.info(f"Graph built successfully for {document.title}")
            return self.stats
            
        except Exception as e:
            logger.error(f"Error building graph for document {document_id}: {e}")
            self.stats["errors"].append(str(e))
            raise
    
    def _get_node_type(self, document_type: DocumentType) -> str:
        """Map document type to Neo4j node label."""
        mapping = {
            DocumentType.LEGISLATION: "Legislation",
            DocumentType.REGULATION: "Regulation",
            DocumentType.POLICY: "Policy",
            DocumentType.GUIDELINE: "Policy",
            DocumentType.DIRECTIVE: "Policy"
        }
        return mapping.get(document_type, "Document")
    
    def _create_document_node(self, document: Document, node_type: str) -> Dict[str, Any]:
        """
        Create a Legislation/Regulation/Policy node in Neo4j.
        
        Args:
            document: Document model instance
            node_type: Neo4j node label
            
        Returns:
            Created node data
        """
        properties = {
            "id": str(document.id),
            "title": document.title,
            "jurisdiction": document.jurisdiction,
            "authority": document.authority,
            "status": document.status.value,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add optional properties
        if document.document_number:
            properties["act_number"] = document.document_number
        if document.effective_date:
            properties["effective_date"] = document.effective_date.isoformat()
        if document.full_text and len(document.full_text) < 1000000:  # Limit size
            properties["full_text"] = document.full_text
        if document.document_metadata:
            properties["metadata"] = document.document_metadata
        
        # Create node
        node = self.neo4j.create_node(node_type, properties)
        self.stats["nodes_created"] += 1
        
        logger.info(f"Created {node_type} node: {document.title}")
        return node
    
    def _create_section_nodes(self, document: Document) -> List[Dict[str, Any]]:
        """
        Create Section nodes for all sections in a document.
        
        Args:
            document: Document model instance
            
        Returns:
            List of created section nodes
        """
        section_nodes = []
        
        for section in document.sections:
            properties = {
                "id": str(section.id),
                "section_number": section.section_number,
                "content": section.content,
                "level": section.level,
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add optional properties
            if section.section_title:
                properties["title"] = section.section_title
            if section.document_metadata:
                properties["metadata"] = section.document_metadata
            
            # Create Section node
            node = self.neo4j.create_node("Section", properties)
            section_nodes.append(node)
            self.stats["nodes_created"] += 1
            
            # Create HAS_SECTION relationship
            self._create_has_section_relationship(
                document.id,
                section.id,
                section.order_index
            )
        
        logger.info(f"Created {len(section_nodes)} Section nodes")
        return section_nodes
    
    def _create_has_section_relationship(
        self,
        document_id: uuid.UUID,
        section_id: uuid.UUID,
        order: int
    ):
        """Create HAS_SECTION relationship between document and section."""
        query = """
        MATCH (d {id: $doc_id})
        MATCH (s:Section {id: $sec_id})
        MERGE (d)-[r:HAS_SECTION]->(s)
        SET r.order = $order
        SET r.created_at = datetime()
        RETURN r
        """
        
        self.neo4j.execute_write(
            query,
            {
                "doc_id": str(document_id),
                "sec_id": str(section_id),
                "order": order
            }
        )
        self.stats["relationships_created"] += 1
    
    def _create_hierarchy_relationships(self, document: Document):
        """
        Create PART_OF relationships for section hierarchy.
        
        Args:
            document: Document model instance
        """
        for section in document.sections:
            if section.parent_section_id:
                query = """
                MATCH (child:Section {id: $child_id})
                MATCH (parent:Section {id: $parent_id})
                MERGE (child)-[r:PART_OF]->(parent)
                SET r.order = $order
                SET r.created_at = datetime()
                RETURN r
                """
                
                self.neo4j.execute_write(
                    query,
                    {
                        "child_id": str(section.id),
                        "parent_id": str(section.parent_section_id),
                        "order": section.order_index
                    }
                )
                self.stats["relationships_created"] += 1
    
    def _create_cross_reference_relationships(self, document: Document):
        """
        Create REFERENCES relationships from cross-references.
        
        Args:
            document: Document model instance
        """
        for ref in document.cross_references:
            if not ref.target_section_id:
                continue
            
            query = """
            MATCH (source:Section {id: $source_id})
            MATCH (target:Section {id: $target_id})
            MERGE (source)-[r:REFERENCES]->(target)
            SET r.citation_text = $citation
            SET r.context = $context
            SET r.created_at = datetime()
            RETURN r
            """
            
            self.neo4j.execute_write(
                query,
                {
                    "source_id": str(ref.source_section_id),
                    "target_id": str(ref.target_section_id),
                    "citation": ref.citation_text or "",
                    "context": ref.context or ""
                }
            )
            self.stats["relationships_created"] += 1
    
    def _extract_and_create_entities(self, document: Document):
        """
        Extract and create Program and Situation entities.
        
        Args:
            document: Document model instance
        """
        # Extract programs
        programs = self._extract_programs(document)
        for program in programs:
            self._create_program_node(program, document)
        
        # Extract situations
        situations = self._extract_situations(document)
        for situation in situations:
            self._create_situation_node(situation, document)
    
    def _extract_programs(self, document: Document) -> List[Dict[str, Any]]:
        """
        Extract program mentions from document text.
        
        Args:
            document: Document model instance
            
        Returns:
            List of extracted programs
        """
        programs = []
        
        # Program keywords to look for
        program_patterns = [
            r"(?i)(employment\s+insurance)\s+(program|benefits?)",
            r"(?i)(old\s+age\s+security)\s+(program|benefits?)",
            r"(?i)(canada\s+pension\s+plan)\s+(benefits?|program)?",
            r"(?i)(workers['']?\s+compensation)\s+(program|benefits?)",
            r"(?i)(disability\s+benefits?)\s+program",
            r"(?i)(parental\s+benefits?)\s+program",
            r"(?i)(maternity\s+benefits?)\s+program",
            r"(?i)(sickness\s+benefits?)\s+program",
        ]
        
        text = document.full_text or ""
        
        for pattern in program_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                program_name = match.group(0).strip()
                
                # Avoid duplicates
                if not any(p["name"] == program_name for p in programs):
                    programs.append({
                        "name": program_name,
                        "department": document.authority,
                        "description": f"Program mentioned in {document.title}",
                        "source_document_id": str(document.id)
                    })
        
        return programs[:10]  # Limit to 10 programs per document
    
    def _extract_situations(self, document: Document) -> List[Dict[str, Any]]:
        """
        Extract applicable situations from document text.
        
        Args:
            document: Document model instance
            
        Returns:
            List of extracted situations
        """
        situations = []
        
        # Situation patterns
        situation_patterns = [
            r"(?i)if\s+(?:you|a\s+person|an\s+individual)\s+(?:is|are|has|have)\s+([^.]{10,100})",
            r"(?i)where\s+(?:a|an|the)\s+([^.]{10,100})",
            r"(?i)in\s+the\s+case\s+of\s+([^.]{10,100})",
            r"(?i)when\s+(?:a|an|the)\s+([^.]{10,100})",
        ]
        
        text = document.full_text or ""
        
        for section in document.sections[:20]:  # Limit to first 20 sections
            for pattern in situation_patterns:
                matches = re.finditer(pattern, section.content)
                for match in matches:
                    description = match.group(1).strip()
                    
                    # Clean up description
                    description = description[:200]  # Limit length
                    
                    if len(description) > 20:  # Minimum length
                        situations.append({
                            "description": description,
                            "tags": self._extract_tags(description),
                            "source_section_id": str(section.id)
                        })
        
        return situations[:15]  # Limit to 15 situations per document
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        tags = []
        
        tag_keywords = {
            "employment": ["employment", "unemployed", "job"],
            "disability": ["disability", "disabled", "impairment"],
            "retirement": ["retirement", "retired", "pension"],
            "maternity": ["maternity", "pregnancy", "pregnant"],
            "parental": ["parental", "parent", "child care"],
            "sickness": ["sickness", "sick", "illness"],
            "temporary_worker": ["temporary", "foreign worker", "work permit"],
            "caregiver": ["caregiver", "caring for"],
        }
        
        text_lower = text.lower()
        for tag, keywords in tag_keywords.items():
            if any(kw in text_lower for kw in keywords):
                tags.append(tag)
        
        return tags
    
    def _create_program_node(self, program: Dict[str, Any], document: Document):
        """Create Program node and relationships."""
        program_id = str(uuid.uuid4())
        
        properties = {
            "id": program_id,
            "name": program["name"],
            "department": program["department"],
            "description": program["description"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create Program node
        self.neo4j.create_node("Program", properties)
        self.stats["nodes_created"] += 1
        
        # Create APPLIES_TO relationship from document to program
        query = """
        MATCH (d {id: $doc_id})
        MATCH (p:Program {id: $prog_id})
        MERGE (d)-[r:APPLIES_TO]->(p)
        SET r.created_at = datetime()
        RETURN r
        """
        
        self.neo4j.execute_write(
            query,
            {
                "doc_id": str(document.id),
                "prog_id": program_id
            }
        )
        self.stats["relationships_created"] += 1
    
    def _create_situation_node(self, situation: Dict[str, Any], document: Document):
        """Create Situation node and relationships."""
        situation_id = str(uuid.uuid4())
        
        properties = {
            "id": situation_id,
            "description": situation["description"],
            "tags": situation.get("tags", []),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create Situation node
        self.neo4j.create_node("Situation", properties)
        self.stats["nodes_created"] += 1
        
        # Create RELEVANT_FOR relationship from section to situation
        if "source_section_id" in situation:
            query = """
            MATCH (s:Section {id: $sec_id})
            MATCH (sit:Situation {id: $sit_id})
            MERGE (s)-[r:RELEVANT_FOR]->(sit)
            SET r.relevance_score = 0.8
            SET r.created_at = datetime()
            RETURN r
            """
            
            self.neo4j.execute_write(
                query,
                {
                    "sec_id": situation["source_section_id"],
                    "sit_id": situation_id
                }
            )
            self.stats["relationships_created"] += 1
    
    def build_all_documents(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Build graphs for all processed documents.
        
        Args:
            limit: Maximum number of documents to process
            
        Returns:
            Overall statistics
        """
        query = self.db.query(Document).filter_by(is_processed=True)
        
        if limit:
            query = query.limit(limit)
        
        documents = query.all()
        
        logger.info(f"Building graphs for {len(documents)} documents")
        
        overall_stats = {
            "total_documents": len(documents),
            "successful": 0,
            "failed": 0,
            "total_nodes": 0,
            "total_relationships": 0,
            "errors": []
        }
        
        for doc in documents:
            try:
                self.stats = {
                    "nodes_created": 0,
                    "relationships_created": 0,
                    "errors": []
                }
                
                self.build_document_graph(doc.id)
                
                overall_stats["successful"] += 1
                overall_stats["total_nodes"] += self.stats["nodes_created"]
                overall_stats["total_relationships"] += self.stats["relationships_created"]
                
            except Exception as e:
                logger.error(f"Failed to build graph for {doc.title}: {e}")
                overall_stats["failed"] += 1
                overall_stats["errors"].append({
                    "document_id": str(doc.id),
                    "title": doc.title,
                    "error": str(e)
                })
        
        return overall_stats
    
    def create_inter_document_relationships(self):
        """
        Create relationships between different documents.
        This should be run after all documents are processed.
        """
        logger.info("Creating inter-document relationships")
        
        # Find regulations that implement legislation
        self._link_regulations_to_legislation()
        
        # Find policies that interpret legislation
        self._link_policies_to_legislation()
        
        # Create SUPERSEDES relationships
        self._create_supersedes_relationships()
    
    def _link_regulations_to_legislation(self):
        """Link Regulation nodes to Legislation nodes they implement."""
        # Get all regulations
        regulations = self.db.query(Document).filter_by(
            document_type=DocumentType.REGULATION
        ).all()
        
        for reg in regulations:
            # Search for legislation mentions in regulation title/text
            keywords = self._extract_legislation_keywords(reg.title)
            
            for keyword in keywords:
                # Find matching legislation
                legislation = self.db.query(Document).filter(
                    and_(
                        Document.document_type == DocumentType.LEGISLATION,
                        Document.title.ilike(f"%{keyword}%")
                    )
                ).first()
                
                if legislation:
                    query = """
                    MATCH (r:Regulation {id: $reg_id})
                    MATCH (l:Legislation {id: $leg_id})
                    MERGE (r)-[rel:IMPLEMENTS]->(l)
                    SET rel.description = $description
                    SET rel.created_at = datetime()
                    RETURN rel
                    """
                    
                    self.neo4j.execute_write(
                        query,
                        {
                            "reg_id": str(reg.id),
                            "leg_id": str(legislation.id),
                            "description": f"Implements provisions of {legislation.title}"
                        }
                    )
                    
                    logger.info(f"Linked {reg.title} to {legislation.title}")
    
    def _link_policies_to_legislation(self):
        """Link Policy nodes to Legislation nodes they interpret."""
        policies = self.db.query(Document).filter_by(
            document_type=DocumentType.POLICY
        ).all()
        
        for policy in policies:
            keywords = self._extract_legislation_keywords(policy.title)
            
            for keyword in keywords:
                legislation = self.db.query(Document).filter(
                    and_(
                        Document.document_type == DocumentType.LEGISLATION,
                        Document.title.ilike(f"%{keyword}%")
                    )
                ).first()
                
                if legislation:
                    query = """
                    MATCH (p:Policy {id: $pol_id})
                    MATCH (l:Legislation {id: $leg_id})
                    MERGE (p)-[rel:INTERPRETS]->(l)
                    SET rel.created_at = datetime()
                    RETURN rel
                    """
                    
                    self.neo4j.execute_write(
                        query,
                        {
                            "pol_id": str(policy.id),
                            "leg_id": str(legislation.id)
                        }
                    )
    
    def _create_supersedes_relationships(self):
        """Create SUPERSEDES relationships for updated legislation."""
        # This would require metadata about which legislation supersedes which
        # For now, we'll use a simple date-based heuristic
        
        documents = self.db.query(Document).filter_by(
            document_type=DocumentType.LEGISLATION
        ).order_by(Document.effective_date).all()
        
        # Group by similar titles
        title_groups = {}
        for doc in documents:
            base_title = self._get_base_title(doc.title)
            if base_title not in title_groups:
                title_groups[base_title] = []
            title_groups[base_title].append(doc)
        
        # Create SUPERSEDES relationships for same-titled documents
        for base_title, docs in title_groups.items():
            if len(docs) > 1:
                # Sort by effective date
                sorted_docs = sorted(
                    [d for d in docs if d.effective_date],
                    key=lambda x: x.effective_date
                )
                
                for i in range(len(sorted_docs) - 1):
                    older = sorted_docs[i]
                    newer = sorted_docs[i + 1]
                    
                    query = """
                    MATCH (new:Legislation {id: $new_id})
                    MATCH (old:Legislation {id: $old_id})
                    MERGE (new)-[rel:SUPERSEDES]->(old)
                    SET rel.effective_date = $effective_date
                    SET rel.created_at = datetime()
                    RETURN rel
                    """
                    
                    self.neo4j.execute_write(
                        query,
                        {
                            "new_id": str(newer.id),
                            "old_id": str(older.id),
                            "effective_date": newer.effective_date.isoformat()
                        }
                    )
    
    def _extract_legislation_keywords(self, title: str) -> List[str]:
        """Extract key legislation names from text."""
        keywords = []
        
        # Common legislation name patterns
        patterns = [
            r"Employment\s+Insurance",
            r"Canada\s+Pension\s+Plan",
            r"Old\s+Age\s+Security",
            r"Workers['']?\s+Compensation",
            r"Labour\s+Standards",
            r"Human\s+Rights",
            r"Immigration",
            r"Citizenship",
        ]
        
        for pattern in patterns:
            if re.search(pattern, title, re.IGNORECASE):
                keywords.append(re.search(pattern, title, re.IGNORECASE).group(0))
        
        return keywords
    
    def _get_base_title(self, title: str) -> str:
        """Extract base title without amendments/years."""
        # Remove year references
        base = re.sub(r'\b(19|20)\d{2}\b', '', title)
        # Remove common suffixes
        base = re.sub(r'\b(Act|Regulations?|Amendment)\b', '', base)
        return base.strip().lower()
    
    def build_regulation_subgraph(self, regulation_id: str) -> Dict[str, Any]:
        """
        Build graph for a regulation from the Regulation model.
        This is a simplified version for regulations ingested via data pipeline.
        
        Args:
            regulation_id: Regulation UUID as string
            
        Returns:
            Statistics about graph construction
        """
        logger.info(f"Building graph for regulation {regulation_id}")
        
        # Reset stats
        self.stats = {
            "nodes_created": 0,
            "relationships_created": 0,
            "errors": []
        }
        
        # Fetch regulation from database
        regulation = self.db.query(Regulation).filter_by(id=uuid.UUID(regulation_id)).first()
        if not regulation:
            raise ValueError(f"Regulation {regulation_id} not found")
        
        try:
            # Create Regulation node
            reg_properties = {
                "id": str(regulation.id),
                "title": regulation.title,
                "jurisdiction": regulation.jurisdiction,
                "authority": regulation.authority or "",
                "status": regulation.status,
                "created_at": datetime.utcnow().isoformat()
            }
            
            if regulation.effective_date:
                reg_properties["effective_date"] = regulation.effective_date.isoformat()
            
            if regulation.extra_metadata:
                reg_properties["metadata"] = regulation.extra_metadata
            
            # Create Regulation node
            self.neo4j.create_node("Regulation", reg_properties)
            self.stats["nodes_created"] += 1
            
            # Create Section nodes
            sections = self.db.query(Section).filter_by(regulation_id=regulation.id).all()
            
            for section in sections:
                sec_properties = {
                    "id": str(section.id),
                    "section_number": section.section_number or "",
                    "content": section.content,
                    "created_at": datetime.utcnow().isoformat()
                }
                
                if section.title:
                    sec_properties["title"] = section.title
                
                if section.extra_metadata:
                    sec_properties["metadata"] = section.extra_metadata
                    if "level" in section.extra_metadata:
                        sec_properties["level"] = section.extra_metadata["level"]
                
                # Create Section node
                self.neo4j.create_node("Section", sec_properties)
                self.stats["nodes_created"] += 1
                
                # Create HAS_SECTION relationship
                query = """
                MATCH (r:Regulation {id: $reg_id})
                MATCH (s:Section {id: $sec_id})
                MERGE (r)-[rel:HAS_SECTION]->(s)
                SET rel.created_at = datetime()
                RETURN rel
                """
                
                self.neo4j.execute_write(
                    query,
                    {
                        "reg_id": str(regulation.id),
                        "sec_id": str(section.id)
                    }
                )
                self.stats["relationships_created"] += 1
            
            # Create citation relationships for ALL citations involving this regulation's sections
            # This includes both internal citations and cross-regulation citations
            from models.models import Citation
            
            # Get all section IDs for this regulation
            section_ids = [str(section.id) for section in sections]
            
            # Query citations where source OR target is in this regulation
            citations = self.db.query(Citation).join(
                Section, Citation.section_id == Section.id
            ).filter(Section.regulation_id == regulation.id).all()
            
            # Also get citations that TARGET this regulation's sections (from other regulations)
            target_citations = self.db.query(Citation).filter(
                Citation.cited_section_id.in_([section.id for section in sections])
            ).all()
            
            # Combine and deduplicate
            all_citations = {citation.id: citation for citation in citations}
            for citation in target_citations:
                all_citations[citation.id] = citation
            
            logger.info(f"Creating {len(all_citations)} citation relationships (includes cross-regulation references)")
            
            for citation in all_citations.values():
                try:
                    query = """
                    MATCH (source:Section {id: $source_id})
                    MATCH (target:Section {id: $target_id})
                    MERGE (source)-[r:REFERENCES]->(target)
                    SET r.citation_text = $citation_text
                    SET r.created_at = datetime()
                    RETURN r
                    """
                    
                    self.neo4j.execute_write(
                        query,
                        {
                            "source_id": str(citation.section_id),
                            "target_id": str(citation.cited_section_id),
                            "citation_text": citation.citation_text or ""
                        }
                    )
                    self.stats["relationships_created"] += 1
                except Exception as e:
                    logger.warning(f"Failed to create citation relationship: {e}")
                    # Continue processing other citations even if one fails
            
            logger.info(f"Graph built successfully for {regulation.title}")
            logger.info(f"Created {self.stats['nodes_created']} nodes, {self.stats['relationships_created']} relationships")
            
            return self.stats
            
        except Exception as e:
            logger.error(f"Error building graph for regulation {regulation_id}: {e}", exc_info=True)
            self.stats["errors"].append(str(e))
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.stats
