"""
Graph Builder Service for populating Neo4j knowledge graph from parsed documents.
Extracts entities, creates nodes, and builds relationships.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
import uuid
import logging
import re

from models import Regulation, Section
from utils.neo4j_client import Neo4jClient

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
    
    def build_document_graph(self, regulation_id: uuid.UUID) -> Dict[str, Any]:
        """
        Build graph for a single regulation.
        
        Args:
            regulation_id: Regulation UUID
            
        Returns:
            Statistics about graph construction
        """
        logger.info(f"Building graph for regulation {regulation_id}")
        
        # Fetch regulation from database
        regulation = self.db.query(Regulation).filter_by(id=regulation_id).first()
        if not regulation:
            raise ValueError(f"Regulation {regulation_id} not found")
        
        try:
            # Create regulation node (all regulations are labeled as "Regulation" in Neo4j)
            reg_node = self._create_regulation_node(regulation)
            
            # Create section nodes and relationships
            section_nodes = self._create_section_nodes(regulation)
            
            # Create cross-reference relationships (REFERENCES)
            self._create_cross_reference_relationships(regulation)
            
            # Extract and create entities (Programs, Situations)
            self._extract_and_create_entities(regulation)
            
            # Create inter-document relationships (ENACTED_UNDER, INTERPRETS)
            self._create_parent_act_relationship(regulation)
            self._create_policy_interpretation_relationship(regulation)
            
            logger.info(f"Graph built successfully for {regulation.title}")
            return self.stats
            
        except Exception as e:
            logger.error(f"Error building graph for regulation {regulation_id}: {e}")
            self.stats["errors"].append(str(e))
            raise
    
    def _create_regulation_node(self, regulation: Regulation) -> Dict[str, Any]:
        """
        Create a Legislation or Regulation node in Neo4j based on title.
        
        Args:
            regulation: Regulation model instance
            
        Returns:
            Created node data
        """
        # Determine node label and type based on title
        # Acts/Lois = Legislation, everything else = Regulation
        node_label = self._determine_node_label(regulation.title)
        
        properties = {
            "id": str(regulation.id),
            "name": regulation.title,  # Add name property for better Neo4j visualization
            "title": regulation.title,
            "jurisdiction": regulation.jurisdiction,
            "authority": regulation.authority if regulation.authority else "Unknown",
            "status": regulation.status,
            "language": regulation.language,
            "node_type": node_label,  # Add node_type property
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add optional properties
        if regulation.effective_date:
            properties["effective_date"] = regulation.effective_date.isoformat()
        if regulation.full_text and len(regulation.full_text) < 1000000:  # Limit size
            properties["full_text"] = regulation.full_text
        if regulation.extra_metadata:
            properties["metadata"] = regulation.extra_metadata
        
        # Create node
        node = self.neo4j.create_node(node_label, properties)
        self.stats["nodes_created"] += 1
        
        logger.info(f"Created {node_label} node: {regulation.title}")
        return node
    
    def _determine_node_label(self, title: str) -> str:
        """
        Determine if regulation should be labeled as Legislation, Regulation, or Policy.
        
        Args:
            title: Regulation title
            
        Returns:
            'Legislation' for Acts/Lois, 'Policy' for policies/guidelines/directives, otherwise 'Regulation'
        """
        title_lower = title.lower()
        
        # Policy documents - check specific patterns first
        if 'order issuing' in title_lower:
            return 'Policy'
        if 'ministerial order' in title_lower:
            return 'Policy'
        if title_lower.endswith('guidelines') or title_lower.endswith('guideline'):
            return 'Policy'
        if title_lower.endswith('directive') or title_lower.endswith('directives'):
            return 'Policy'
        if 'policy' in title_lower and 'act' not in title_lower:
            return 'Policy'
        if 'proclamation' in title_lower:
            return 'Policy'
        
        # Acts and Lois (French for laws) are considered Legislation
        if ' act' in title_lower or title_lower.startswith('act ') or title_lower.endswith(' act'):
            return 'Legislation'
        if ' loi' in title_lower or title_lower.startswith('loi ') or title_lower.endswith(' loi'):
            return 'Legislation'
        
        # Everything else is a Regulation (rules, regulations, etc.)
        return 'Regulation'
    
    def _create_section_nodes(self, regulation: Regulation) -> List[Dict[str, Any]]:
        """
        Create Section nodes for all sections in a regulation.
        
        Args:
            regulation: Regulation model instance
            
        Returns:
            List of created section nodes
        """
        section_nodes = []
        
        for idx, section in enumerate(regulation.sections):
            properties = {
                "id": str(section.id),
                "section_number": section.section_number,
                "content": section.content if section.content else "",
                "level": 0,  # Can be enhanced later
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add optional properties
            if section.title:
                properties["title"] = section.title
            if section.extra_metadata:
                properties["metadata"] = section.extra_metadata
            
            # Add citation property for easier reference
            properties["citation"] = f"{regulation.title[:50]} Section {section.section_number}"
            
            # Create Section node
            node = self.neo4j.create_node("Section", properties)
            section_nodes.append(node)
            self.stats["nodes_created"] += 1
            
            # Create HAS_SECTION relationship
            self._create_has_section_relationship(
                regulation.id,
                section.id,
                idx
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
        # Match any node type (Legislation, Regulation, Policy) with the document_id
        query = """
        MATCH (d) WHERE d.id = $doc_id
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
    
    def _create_cross_reference_relationships(self, regulation: Regulation):
        """
        Create REFERENCES relationships between sections based on citations.
        
        Args:
            regulation: Regulation model instance
        """
        for section in regulation.sections:
            # Use the Section model's citations relationship
            for citation in section.citations:
                if citation.cited_section_id:
                    query = """
                    MATCH (s1:Section {id: $from_id})
                    MATCH (s2:Section {id: $to_id})
                    MERGE (s1)-[r:REFERENCES]->(s2)
                    SET r.citation_text = $citation_text
                    SET r.created_at = datetime()
                    RETURN r
                    """
                    
                    self.neo4j.execute_write(
                        query,
                        {
                            "from_id": str(section.id),
                            "to_id": str(citation.cited_section_id),
                            "citation_text": citation.citation_text or ""
                        }
                    )
                    self.stats["relationships_created"] += 1
    
    def _extract_and_create_entities(self, regulation: Regulation):
        """
        Extract and create Program and Situation entities.
        
        Args:
            regulation: Regulation model instance
        """
        # Extract programs
        programs = self._extract_programs(regulation)
        for program in programs:
            self._create_program_node(program, regulation)
        
        # Extract situations
        situations = self._extract_situations(regulation)
        for situation in situations:
            self._create_situation_node(situation, regulation)
    
    def _extract_programs(self, regulation: Regulation) -> List[Dict[str, Any]]:
        """
        Extract program mentions from regulation title and text.
        
        Args:
            regulation: Regulation model instance
            
        Returns:
            List of extracted programs
        """
        from config.program_mappings import FEDERAL_PROGRAMS
        
        programs = []
        title_lower = regulation.title.lower()
        
        # Check title and text for each known program
        for program_key, program_config in FEDERAL_PROGRAMS.items():
            found = False
            
            # Check keywords in title (most reliable)
            for keyword in program_config.get('keywords', []):
                if keyword.lower() in title_lower:
                    found = True
                    break
            
            # Check patterns in title
            if not found:
                for pattern in program_config.get('patterns', []):
                    if re.search(pattern, regulation.title, re.IGNORECASE):
                        found = True
                        break
            
            if found:
                # Convert program_key to readable name
                program_name = program_key.replace('_', ' ').title()
                
                # Avoid duplicates
                if not any(p["name"] == program_name for p in programs):
                    programs.append({
                        "name": program_name,
                        "program_key": program_key,
                        "department": regulation.authority,
                        "description": f"Program related to {regulation.title}",
                        "source_regulation_id": str(regulation.id)
                    })
        
        return programs
    
    def _extract_situations(self, regulation: Regulation) -> List[Dict[str, Any]]:
        """
        Extract applicable situations from regulation text.
        
        Args:
            regulation: Regulation model instance
            
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
        
        text = regulation.full_text or ""
        
        for section in regulation.sections[:20]:  # Limit to first 20 sections
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
    
    def _create_program_node(self, program: Dict[str, Any], regulation: Regulation):
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
        
        # Create APPLIES_TO relationship from regulation to program
        query = """
        MATCH (d) WHERE d.id = $doc_id
        MATCH (p:Program {id: $prog_id})
        MERGE (d)-[r:APPLIES_TO]->(p)
        SET r.created_at = datetime()
        RETURN r
        """
        
        self.neo4j.execute_write(
            query,
            {
                "doc_id": str(regulation.id),
                "prog_id": program_id
            }
        )
        self.stats["relationships_created"] += 1
    
    def _create_situation_node(self, situation: Dict[str, Any], regulation: Regulation):
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
    
    def _create_parent_act_relationship(self, regulation: Regulation):
        """
        Create ENACTED_UNDER relationship from Regulation to its parent Act.
        
        Args:
            regulation: Regulation model instance
        """
        # Only process regulations (not Acts)
        node_label = self._determine_node_label(regulation.title)
        if node_label != 'Regulation':
            return
        
        # Extract parent Act name from title
        parent_act_name = self._extract_parent_act_name(regulation.title)
        
        if not parent_act_name:
            return
        
        # Try to find matching Act in Neo4j
        query = """
        MATCH (r:Regulation {id: $reg_id})
        MATCH (a:Regulation)
        WHERE a.node_type = 'Legislation'
        AND (
            toLower(a.title) = toLower($parent_name)
            OR toLower(a.title) CONTAINS toLower($parent_base)
        )
        WITH r, a
        LIMIT 1
        MERGE (r)-[:ENACTED_UNDER]->(a)
        RETURN a.title as act_title
        """
        
        # Remove "Act" for fuzzy matching
        parent_base = parent_act_name.replace(' Act', '').replace(' Loi', '').strip()
        
        result = self.neo4j.execute_write(
            query,
            {
                "reg_id": str(regulation.id),
                "parent_name": parent_act_name,
                "parent_base": parent_base
            }
        )
        
        if result:
            logger.info(f"Linked {regulation.title} → {result[0]['act_title']}")
            self.stats["relationships_created"] += 1
    
    def _create_policy_interpretation_relationship(self, regulation: Regulation):
        """
        Create INTERPRETS relationship from Policy to Legislation it interprets.
        
        Args:
            regulation: Regulation model instance
        """
        # Only process policies
        node_label = self._determine_node_label(regulation.title)
        if node_label != 'Policy':
            return
        
        # Extract the Act/Legislation that this policy interprets
        interpreted_act = self._extract_interpreted_legislation(regulation.title, regulation.full_text)
        
        if not interpreted_act:
            return
        
        # Try to find matching Legislation in Neo4j
        query = """
        MATCH (p:Policy {id: $policy_id})
        MATCH (l:Regulation)
        WHERE l.node_type = 'Legislation'
        AND (
            toLower(l.title) = toLower($act_name)
            OR toLower(l.title) CONTAINS toLower($act_base)
        )
        WITH p, l
        LIMIT 1
        MERGE (p)-[:INTERPRETS]->(l)
        RETURN l.title as act_title
        """
        
        # Remove "Act" for fuzzy matching
        act_base = interpreted_act.replace(' Act', '').replace(' Loi', '').strip()
        
        result = self.neo4j.execute_write(
            query,
            {
                "policy_id": str(regulation.id),
                "act_name": interpreted_act,
                "act_base": act_base
            }
        )
        
        if result:
            logger.info(f"Policy INTERPRETS: {regulation.title} → {result[0]['act_title']}")
            self.stats["relationships_created"] += 1
    
    def _extract_interpreted_legislation(self, title: str, full_text: str) -> str:
        """
        Extract the name of the Act/Legislation that a policy interprets.
        
        Args:
            title: Policy title
            full_text: Full text of the policy
            
        Returns:
            Name of the interpreted Act, or empty string
        """
        # Manual mappings for known policies
        known_mappings = {
            'Federal Child Support Guidelines': 'Divorce Act',
            'Order Issuing a Direction to the CRTC on a Renewed Approach to Telecommunications Policy': 'Telecommunications Act',
        }
        
        if title in known_mappings:
            return known_mappings[title]
        
        # Try to find Act/Loi references in the title first
        # Example: "Order Issuing a Direction to the CRTC on Telecommunications Policy" -> "Telecommunications Act"
        
        # Pattern 1: "Guidelines" or "Policy" followed by "under the X Act"
        match = re.search(r'under the ([^,\\.]+Act)', title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: "X Act Regulations/Guidelines/Policy"
        match = re.search(r'^(.+Act)\\s+(Guidelines?|Policy|Directive)', title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 3: Look for common Act references in the text
        if full_text:
            # Find first mention of an Act in the text (first 2000 chars)
            text_sample = full_text[:2000] if len(full_text) > 2000 else full_text
            act_mentions = re.findall(r'([A-Z][\\w\\s]+Act)', text_sample)
            if act_mentions:
                # Return the most common Act mention
                from collections import Counter
                most_common = Counter(act_mentions).most_common(1)
                if most_common:
                    return most_common[0][0].strip()
        
        return ""
    
    def _extract_parent_act_name(self, regulation_title: str) -> str:
        """
        Extract the parent Act name from a regulation title.
        
        Examples:
        - "Employment Insurance (Fishing) Regulations" → "Employment Insurance Act"
        - "Canada Pension Plan Regulations" → "Canada Pension Plan"
        
        Args:
            regulation_title: Title of the regulation
            
        Returns:
            Likely parent Act name or empty string
        """
        title_lower = regulation_title.lower()
        
        # Remove common regulation suffixes
        patterns = [
            r'\s+regulations?$',
            r'\s+\(.*?\)\s+regulations?$',
            r'\s+rules?$',
            r'\s+\(.*?\)\s+rules?$',
            r'\s+order$',
            r'\s+\(.*?\)\s+order$',
        ]
        
        base_name = regulation_title
        for pattern in patterns:
            base_name = re.sub(pattern, '', base_name, flags=re.IGNORECASE)
        
        # If it doesn't end with "Act" or "Loi", add "Act"
        if not base_name.lower().endswith('act') and not base_name.lower().endswith('loi'):
            if 'act' not in title_lower and 'loi' not in title_lower:
                return f"{base_name.strip()} Act"
        
        return base_name.strip()
    
    def _create_policy_interpretation_relationship(self, regulation: Regulation):
        """
        Create INTERPRETS relationship from Policy to Legislation it interprets.
        
        Args:
            regulation: Regulation model instance
        """
        # Only process policies
        node_label = self._determine_node_label(regulation.title)
        if node_label != 'Policy':
            return
        
        # Extract the Act/Legislation that this policy interprets
        interpreted_act = self._extract_interpreted_legislation(regulation.title, regulation.full_text)
        
        if not interpreted_act:
            return
        
        # Try to find matching Legislation in Neo4j
        query = """
        MATCH (p:Policy {id: $policy_id})
        MATCH (l:Regulation)
        WHERE l.node_type = 'Legislation'
        AND (
            toLower(l.title) = toLower($act_name)
            OR toLower(l.title) CONTAINS toLower($act_base)
        )
        WITH p, l
        LIMIT 1
        MERGE (p)-[:INTERPRETS]->(l)
        RETURN l.title as act_title
        """
        
        # Remove "Act" for fuzzy matching
        act_base = interpreted_act.replace(' Act', '').replace(' Loi', '').strip()
        
        result = self.neo4j.execute_write(
            query,
            {
                "policy_id": str(regulation.id),
                "act_name": interpreted_act,
                "act_base": act_base
            }
        )
        
        if result:
            logger.info(f"Policy INTERPRETS: {regulation.title} → {result[0]['act_title']}")
            self.stats["relationships_created"] += 1
    
    def _extract_interpreted_legislation(self, title: str, full_text: str) -> str:
        """
        Extract the name of the Act/Legislation that a policy interprets.
        
        Args:
            title: Policy title
            full_text: Full text of the policy
            
        Returns:
            Name of the interpreted Act, or empty string
        """
        # Try to find Act/Loi references in the title first
        # Example: "Order Issuing a Direction to the CRTC on Telecommunications Policy" -> "Telecommunications Act"
        
        # Pattern 1: "Guidelines" or "Policy" followed by "under the X Act"
        match = re.search(r'under the ([^,\.]+Act)', title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: "X Act Regulations/Guidelines/Policy"
        match = re.search(r'^(.+Act)\s+(Guidelines?|Policy|Directive)', title, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Pattern 3: Look for common Act references in the text
        if full_text:
            # Find first mention of an Act in the text (first 2000 chars)
            text_sample = full_text[:2000] if len(full_text) > 2000 else full_text
            act_mentions = re.findall(r'([A-Z][\w\s]+Act)', text_sample)
            if act_mentions:
                # Return the most common Act mention
                from collections import Counter
                most_common = Counter(act_mentions).most_common(1)
                if most_common:
                    return most_common[0][0].strip()
        
        return ""
    
    def build_all_documents(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Build graphs for all processed regulations.
        
        Args:
            limit: Maximum number of regulations to process
            
        Returns:
            Overall statistics
        """
        query = self.db.query(Regulation)
        
        if limit:
            query = query.limit(limit)
        
        regulations = query.all()
        
        logger.info(f"Building graphs for {len(regulations)} regulations")
        
        overall_stats = {
            "total_regulations": len(regulations),
            "successful": 0,
            "failed": 0,
            "total_nodes": 0,
            "total_relationships": 0,
            "errors": []
        }
        
        for reg in regulations:
            try:
                self.stats = {
                    "nodes_created": 0,
                    "relationships_created": 0,
                    "errors": []
                }
                
                self.build_document_graph(reg.id)
                
                overall_stats["successful"] += 1
                overall_stats["total_nodes"] += self.stats["nodes_created"]
                overall_stats["total_relationships"] += self.stats["relationships_created"]
                
            except Exception as e:
                logger.error(f"Failed to build graph for {reg.title}: {e}")
                overall_stats["failed"] += 1
                overall_stats["errors"].append({
                    "regulation_id": str(reg.id),
                    "title": reg.title,
                    "error": str(e)
                })
        
        return overall_stats
    
    def create_inter_document_relationships(self):
        """
        Create relationships between different documents.
        This should be run after all documents are processed.
        """
        logger.info("Creating inter-document relationships")
        
        # Link regulations that implement legislation
        self._link_regulations_to_legislation()
        
        # Create supersedes relationships from amendment history
        self._create_supersedes_relationships()
        
        logger.info("Inter-document relationships complete")
    
    def _link_regulations_to_legislation(self):
        """Link Regulation nodes to Legislation nodes they implement."""
        logger.info("Linking Regulations to Legislation...")
        
        # Get all regulations from Neo4j (those without 'Act' or 'Loi' in title)
        # These should have been labeled as 'Regulation' during creation
        regulations_query = """
        MATCH (r:Regulation)
        RETURN r.id as id, r.title as title
        """
        
        regulations = self.neo4j.execute_query(regulations_query)
        
        linked_count = 0
        for reg in regulations:
            # Search for legislation mentions in regulation title
            keywords = self._extract_legislation_keywords(reg["title"])
            
            for keyword in keywords:
                # Find matching legislation in Neo4j
                query = """
                MATCH (l:Legislation)
                WHERE l.title CONTAINS $keyword
                RETURN l.id as id, l.title as title
                LIMIT 1
                """
                
                matches = self.neo4j.execute_query(query, {"keyword": keyword})
                
                if matches:
                    legislation = matches[0]
                    
                    # Create IMPLEMENTS relationship
                    link_query = """
                    MATCH (r:Regulation {id: $reg_id})
                    MATCH (l:Legislation {id: $leg_id})
                    MERGE (r)-[rel:IMPLEMENTS]->(l)
                    SET rel.description = $description
                    SET rel.created_at = datetime()
                    RETURN rel
                    """
                    
                    self.neo4j.execute_write(
                        link_query,
                        {
                            "reg_id": reg["id"],
                            "leg_id": legislation["id"],
                            "description": f"Implements provisions of {legislation['title']}"
                        }
                    )
                    
                    linked_count += 1
                    logger.info(f"Linked {reg['title'][:60]} to {legislation['title'][:60]}")
                    break  # Only link to first matching legislation
        
        logger.info(f"Created {linked_count} IMPLEMENTS relationships")
    
    def _create_supersedes_relationships(self):
        """
        Create SUPERSEDES relationships based on amendment history.
        Uses the amendments table to find which Acts supersede others.
        """
        logger.info("Creating SUPERSEDES relationships from amendment history...")
        
        from models import Amendment
        
        # Get all amendments from database
        amendments = self.db.query(Amendment).all()
        
        supersedes_count = 0
        
        for amendment in amendments:
            # Get the regulation this amendment belongs to
            source_reg = self.db.query(Regulation).filter_by(id=amendment.regulation_id).first()
            if not source_reg:
                continue
            
            # Extract bill number or citation from amendment metadata
            bill_info = amendment.extra_metadata.get('bill_number') if amendment.extra_metadata else None
            if not bill_info:
                continue
            
            # Try to find the superseding legislation by bill number in title
            # Format: "2023, c. 29" or "S.C. 2023, c. 29"
            # Parse to find Act with this chapter
            if ', c. ' in bill_info:
                # Extract year and chapter
                import re
                match = re.search(r'(\d{4}).*c\.\s*(\d+)', bill_info)
                if match:
                    year = match.group(1)
                    chapter_num = match.group(2)
                    
                    # Search for Act with this chapter reference
                    query = """
                    MATCH (newer:Legislation)
                    WHERE newer.title CONTAINS $year 
                       OR newer.id IN (
                           SELECT r.id FROM regulations r 
                           WHERE r.extra_metadata->>'chapter' LIKE $pattern
                       )
                    RETURN newer.id as id, newer.title as title
                    LIMIT 1
                    """
                    
                    # Try to find matching legislation in Neo4j
                    # Use source regulation's node
                    source_node_query = """
                    MATCH (n)
                    WHERE n.id = $reg_id
                    RETURN n.id as id, n.title as title, labels(n) as labels
                    """
                    
                    source_nodes = self.neo4j.execute_query(source_node_query, {"reg_id": str(source_reg.id)})
                    
                    if source_nodes:
                        source_node = source_nodes[0]
                        
                        # Create SUPERSEDES relationship if we can identify the amending act
                        # For now, create self-reference with amendment info
                        # This tracks that the Act was amended/superseded
                        link_query = """
                        MATCH (source {id: $source_id})
                        SET source.last_amended = $amendment_date
                        SET source.amendment_info = $bill_info
                        RETURN source
                        """
                        
                        self.neo4j.execute_write(
                            link_query,
                            {
                                "source_id": str(source_reg.id),
                                "amendment_date": amendment.effective_date.isoformat() if amendment.effective_date else None,
                                "bill_info": bill_info
                            }
                        )
                        
                        supersedes_count += 1
        
        logger.info(f"Processed {supersedes_count} amendment relationships")
        logger.info("Note: Full SUPERSEDES implementation requires matching bill numbers to actual Acts")
    
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
                "name": regulation.title,  # Add name property for better Neo4j visualization
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
            
            # Create PART_OF relationships for section hierarchy
            logger.info(f"Creating section hierarchy (PART_OF relationships)...")
            hierarchy_count = 0
            
            for section in sections:
                # Check if section has a parent
                parent_number = section.extra_metadata.get('parent_number') if section.extra_metadata else None
                
                if parent_number:
                    # Find parent section by section_number within same regulation
                    parent_section = self.db.query(Section).filter(
                        Section.regulation_id == regulation.id,
                        Section.section_number == parent_number
                    ).first()
                    
                    if parent_section:
                        try:
                            hierarchy_query = """
                            MATCH (child:Section {id: $child_id})
                            MATCH (parent:Section {id: $parent_id})
                            MERGE (child)-[r:PART_OF]->(parent)
                            SET r.created_at = datetime()
                            RETURN r
                            """
                            
                            self.neo4j.execute_write(
                                hierarchy_query,
                                {
                                    "child_id": str(section.id),
                                    "parent_id": str(parent_section.id)
                                }
                            )
                            self.stats["relationships_created"] += 1
                            hierarchy_count += 1
                        except Exception as e:
                            logger.warning(f"Failed to create PART_OF relationship for section {section.section_number}: {e}")
            
            if hierarchy_count > 0:
                logger.info(f"Created {hierarchy_count} PART_OF relationships for section hierarchy")
            
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
