"""
Graph Builder Service for populating Neo4j knowledge graph from parsed documents.
Extracts entities, creates nodes, and builds relationships.
"""
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Session
import uuid
import logging
import re

from models import Regulation, Section, Amendment
from utils.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)


class GraphBuilder:
    """
    Builds and populates the Neo4j knowledge graph from parsed documents.
    """
    # Pre-compile regex once. This is much faster for 400k iterations.
    SITUATION_PATTERNS = [
        re.compile(r"if\s+(?:you|a\s+person|an\s+individual)\s+(?:is|are|has|have)\s+([^.]{10,100})", re.IGNORECASE),
        re.compile(r"where\s+(?:a|an|the)\s+([^.]{10,100})", re.IGNORECASE),
        re.compile(r"in\s+the\s+case\s+of\s+([^.]{10,100})", re.IGNORECASE),
        re.compile(r"when\s+(?:a|an|the)\s+([^.]{10,100})", re.IGNORECASE),
    ]
    
    def __init__(self, db: Session, neo4j_client: Neo4jClient, batch_size: int = 2500):
        """
        Initialize graph builder.
        
        Args:
            db: SQLAlchemy database session
            neo4j_client: Neo4j client instance
            batch_size: Number of nodes/relationships to batch before flushing (default: 2500)
        """
        self.db = db
        self.neo4j = neo4j_client
        self.batch_size = batch_size
        self.stats = {
            "nodes_created": 0,
            "relationships_created": 0,
            "errors": []
        }
        
        # Batch collections for nodes and relationships
        self._node_batches: Dict[str, List[Dict[str, Any]]] = {}  # label -> list of node properties
        self._relationship_batches: List[Dict[str, Any]] = []  # list of relationship definitions
        
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
    
    def _add_node_to_batch(self, label: str, properties: Dict[str, Any]):
        """
        Add a node to the batch collection.
        
        Args:
            label: Node label
            properties: Node properties
        """
        if label not in self._node_batches:
            self._node_batches[label] = []
        
        # Serialize complex types to JSON strings
        processed_props = {}
        for key, value in properties.items():
            if isinstance(value, dict):
                import json
                processed_props[key] = json.dumps(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                import json
                processed_props[key] = json.dumps(value)
            else:
                processed_props[key] = value
        
        self._node_batches[label].append(processed_props)
        
        # Auto-flush if batch size reached
        if len(self._node_batches[label]) >= self.batch_size:
            self._flush_node_batch(label)
    
    def _add_relationship_to_batch(self, rel_def: Dict[str, Any]):
        """
        Add a relationship to the batch collection.
        
        Args:
            rel_def: Relationship definition with keys:
                - from_label: Source node label
                - from_id: Source node ID
                - to_label: Target node label
                - to_id: Target node ID
                - rel_type: Relationship type
                - properties: Relationship properties (optional)
        """
        self._relationship_batches.append(rel_def)
        
        # Auto-flush if batch size reached
        if len(self._relationship_batches) >= self.batch_size:
            self._flush_relationship_batch()
    
    def _flush_node_batch(self, label: str):
        """
        Flush nodes of a specific label using UNWIND.
        
        Args:
            label: Node label to flush
        """
        if label not in self._node_batches or not self._node_batches[label]:
            return
        
        nodes = self._node_batches[label]
        
        query = f"""
        UNWIND $nodes AS nodeProps
        CREATE (n:{label})
        SET n = nodeProps
        """
        
        try:
            result = self.neo4j.execute_write(query, {"nodes": nodes})
            created_count = len(nodes)
            self.stats["nodes_created"] += created_count
            logger.debug(f"Flushed {created_count} {label} nodes")
        except Exception as e:
            logger.error(f"Error flushing {label} nodes: {e}")
            self.stats["errors"].append(f"Node batch flush error: {e}")
        finally:
            self._node_batches[label] = []
    
    def _flush_relationship_batch(self):
        """
        Flush relationships using UNWIND with label hints for performance.
        Groups by (rel_type, from_label, to_label) for optimal query planning.
        """
        if not self._relationship_batches:
            return
        
        relationships = self._relationship_batches
        
        # Group relationships by (rel_type, from_label, to_label) for optimal query planning
        rel_by_signature = {}
        for rel in relationships:
            rel_type = rel["rel_type"]
            from_label = rel.get("from_label", "")
            to_label = rel.get("to_label", "")
            signature = (rel_type, from_label, to_label)
            
            if signature not in rel_by_signature:
                rel_by_signature[signature] = []
            rel_by_signature[signature].append(rel)
        
        # Flush each signature separately with label hints
        for (rel_type, from_label, to_label), rels in rel_by_signature.items():
            # Use labels if available for MUCH better performance (5-10x faster)
            if from_label and to_label:
                query = f"""
                UNWIND $rels AS rel
                MATCH (a:{from_label} {{id: rel.from_id}})
                MATCH (b:{to_label} {{id: rel.to_id}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += rel.properties
                """
            else:
                # Fallback to label-less matching (slower, but still works)
                logger.warning(f"Relationship batch missing labels for {rel_type}, using slower query")
                query = f"""
                UNWIND $rels AS rel
                MATCH (a {{id: rel.from_id}})
                MATCH (b {{id: rel.to_id}})
                MERGE (a)-[r:{rel_type}]->(b)
                SET r += rel.properties
                """
            
            try:
                result = self.neo4j.execute_write(query, {"rels": rels})
                created_count = len(rels)
                self.stats["relationships_created"] += created_count
                label_info = f"{from_label}->{to_label}" if from_label and to_label else "unlabeled"
                logger.debug(f"Flushed {created_count} {rel_type} ({label_info}) relationships")
            except Exception as e:
                logger.error(f"Error flushing {rel_type} relationships: {e}")
                self.stats["errors"].append(f"Relationship batch flush error: {e}")
        
        self._relationship_batches = []
    
    def flush_all_batches(self):
        """
        Flush all pending node and relationship batches.
        Call this at the end of batch processing.
        """
        # Flush all node batches
        for label in list(self._node_batches.keys()):
            self._flush_node_batch(label)
        
        # Flush relationship batch
        self._flush_relationship_batch()
        
        logger.debug("All batches flushed")
    
    
    def build_document_graph(self, regulation_id: uuid.UUID) -> Dict[str, Any]:
        """
        Build graph for a single regulation with optimized SQL and Batching.
        Accepts either a UUID (and fetches it efficiently) or a pre-fetched object.
        """
        # 1. OPTIMIZED SQL LOADING
        # UUID, fetch it with eager loading to stop N+1 queries
        
        regulation = self.db.query(Regulation).options(
            joinedload(Regulation.sections).joinedload(Section.citations)
        ).filter_by(id=regulation_id).first()
        
        if not regulation:
            logger.warning(f"Regulation {regulation_id} not found")
            return self.stats

        logger.info(f"Building graph for regulation {regulation.id} (Optimized)")

        try:
            # 2. QUEUE NODES (Using batching instead of direct writes)
            # We don't need the return values anymore because we aren't using them immediately
            self._create_regulation_node(regulation)
            self._create_section_nodes(regulation)
            
            # 3. QUEUE RELATIONSHIPS
            # These methods already used batching in your code, so they just work faster now
            # because the SQL data is already in memory (no lazy loading lag).
            self._create_cross_reference_relationships(regulation)
            
            # Extract and create entities (Programs, Situations)
            self._extract_and_create_entities(regulation)
            
            # Create inter-document relationships
            self._create_parent_act_relationship(regulation)
            self._create_policy_interpretation_relationship(regulation)
            
            # 4. EXECUTE BATCHES (The "Commit" step)
            # This sends everything to Neo4j in one or two big network requests
            self.flush_all_batches()
            
            logger.info(f"Graph built successfully for {regulation.title}")
            return self.stats
            
        except Exception as e:
            logger.error(f"Error building graph for regulation {regulation.id}: {e}")
            self.stats["errors"].append(str(e))
            # Clear batches on error to prevent bad data polluting next run
            self._node_batches = {}
            self._relationship_batches = []
            raise

    def _create_regulation_node(self, regulation: Regulation) -> None:
        """
        Queue a Legislation or Regulation node for batch creation.
        """
        node_label = self._determine_node_label(regulation.title)
        
        properties = {
            "id": str(regulation.id),
            "name": regulation.title,
            "title": regulation.title,
            "jurisdiction": regulation.jurisdiction,
            "authority": regulation.authority if regulation.authority else "Unknown",
            "status": regulation.status,
            "language": regulation.language,
            "node_type": node_label,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if regulation.effective_date:
            properties["effective_date"] = regulation.effective_date.isoformat()
        if regulation.full_text and len(regulation.full_text) < 1000000:
            properties["full_text"] = regulation.full_text
        if regulation.extra_metadata:
            # Note: _add_node_to_batch handles JSON serialization for dicts automatically
            properties["metadata"] = regulation.extra_metadata
            
        # CHANGED: Use batching instead of direct create
        self._add_node_to_batch(node_label, properties)
    
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
    
    def _create_section_nodes(self, regulation: Regulation) -> None:
        """
        Queue Section nodes and their relationships (HAS_SECTION, PART_OF) for batch creation.
        Optimized to use in-memory lookups for hierarchy instead of SQL queries.
        """
        # 1. Pre-calculate common data to save CPU cycles inside the loop
        reg_id_str = str(regulation.id)
        current_time = datetime.utcnow().isoformat()
        reg_title_short = regulation.title[:50]

        # 2. Create a lookup map for fast parent finding (O(1) lookup)
        # This replaces the need to query the DB for every single section to find its parent
        # Map: section_number -> section_id_string
        section_map = {s.section_number: str(s.id) for s in regulation.sections if s.section_number}

        for idx, section in enumerate(regulation.sections):
            section_id_str = str(section.id)
            
            # --- A. Create Section Node ---
            properties = {
                "id": section_id_str,
                "section_number": section.section_number,
                "content": section.content if section.content else "",
                "level": 0,
                "created_at": current_time,
                "citation": f"{reg_title_short} Section {section.section_number}"
            }
            
            if section.title:
                properties["title"] = section.title
            if section.extra_metadata:
                properties["metadata"] = section.extra_metadata
            
            # Add to Node Batch
            self._add_node_to_batch("Section", properties)
            
            # Get node label for this regulation (for relationship label hints)
            node_label = self._determine_node_label(regulation.title)
            
            # --- B. Create HAS_SECTION Relationship ---
            # Link Regulation -> Section (WITH LABEL HINTS for 5-10x performance)
            self._add_relationship_to_batch({
                "from_id": reg_id_str,
                "to_id": section_id_str,
                "from_label": node_label,  # NEW: Performance optimization
                "to_label": "Section",      # NEW: Performance optimization
                "rel_type": "HAS_SECTION",
                "properties": {
                    "order": idx,
                    "created_at": current_time
                }
            })

            # --- C. Create PART_OF Hierarchy (Optimized) ---
            # Link Section -> Parent Section (if applicable)
            # This logic now runs entirely in memory without touching the DB
            if section.extra_metadata:
                parent_number = section.extra_metadata.get('parent_number')
                
                # Check if we have a parent number AND that parent exists in this regulation
                if parent_number and parent_number in section_map:
                    parent_id = section_map[parent_number]
                    
                    # Add to Relationship Batch (WITH LABEL HINTS)
                    self._add_relationship_to_batch({
                        "from_id": section_id_str,
                        "to_id": parent_id,
                        "from_label": "Section",  # NEW: Performance optimization
                        "to_label": "Section",    # NEW: Performance optimization
                        "rel_type": "PART_OF",
                        "properties": {
                            "created_at": current_time
                        }
                    })
    
    def _create_has_section_relationship(
        self,
        document_id: uuid.UUID,
        section_id: uuid.UUID,
        order: int,
        from_label: str = "Regulation"
    ):
        """Create HAS_SECTION relationship between document and section using batching with label hints."""
        self._add_relationship_to_batch({
            "from_id": str(document_id),
            "to_id": str(section_id),
            "from_label": from_label,  # NEW: Performance optimization
            "to_label": "Section",     # NEW: Performance optimization
            "rel_type": "HAS_SECTION",
            "properties": {
                "order": order,
                "created_at": datetime.utcnow().isoformat()
            }
        })
    
    def _create_cross_reference_relationships(self, regulation: Regulation):
        """
        Create REFERENCES relationships between sections based on citations using batching with label hints.
        
        Args:
            regulation: Regulation model instance
        """
        for section in regulation.sections:
            # Use the Section model's citations relationship
            for citation in section.citations:
                if citation.cited_section_id:
                    self._add_relationship_to_batch({
                        "from_id": str(section.id),
                        "to_id": str(citation.cited_section_id),
                        "from_label": "Section",  # NEW: Performance optimization
                        "to_label": "Section",    # NEW: Performance optimization
                        "rel_type": "REFERENCES",
                        "properties": {
                            "citation_text": citation.citation_text or "",
                            "created_at": datetime.utcnow().isoformat()
                        }
                    })
    
    def _create_entity_nodes_only(self, regulation: Regulation):
        """
        Extract and create ONLY Program and Situation nodes (no relationships).
        Called during Pass 1 (node creation).
        
        Args:
            regulation: Regulation model instance
        """
        # Extract programs
        programs = self._extract_programs(regulation)
        for program in programs:
            # Create ONLY the node (no relationships)
            program_id = str(uuid.uuid4())
            properties = {
                "id": program_id,
                "name": program["name"],
                "department": program["department"],
                "description": program["description"],
                "created_at": datetime.utcnow().isoformat()
            }
            self._add_node_to_batch("Program", properties)
        
        # Extract situations
        situations = self._extract_situations(regulation)
        for situation in situations:
            # Create ONLY the node (no relationships)
            situation_id = str(uuid.uuid4())
            properties = {
                "id": situation_id,
                "description": situation["description"],
                "tags": situation.get("tags", []),
                "created_at": datetime.utcnow().isoformat()
            }
            self._add_node_to_batch("Situation", properties)
    
    def _create_entity_relationships_only(self, regulation: Regulation):
        """
        Create ONLY relationships for Program and Situation entities.
        Called during Pass 2 (relationship creation).
        
        Args:
            regulation: Regulation model instance
        """
        # Determine regulation node label for relationship hints
        node_label = self._determine_node_label(regulation.title)
        
        # Extract programs and create relationships
        programs = self._extract_programs(regulation)
        for program in programs:
            # Find the Program node by name (since we created it in Pass 1)
            find_query = """
            MATCH (p:Program)
            WHERE p.name = $name AND p.department = $department
            RETURN p.id as program_id
            LIMIT 1
            """
            result = self.neo4j.execute_query(
                find_query,
                {"name": program["name"], "department": program["department"]}
            )
            
            if result:
                program_id = result[0]["program_id"]
                
                # Add APPLIES_TO relationship to batch
                self._add_relationship_to_batch({
                    "from_id": str(regulation.id),
                    "to_id": program_id,
                    "from_label": node_label,
                    "to_label": "Program",
                    "rel_type": "APPLIES_TO",
                    "properties": {
                        "created_at": datetime.utcnow().isoformat()
                    }
                })
        
        # Extract situations and create relationships
        situations = self._extract_situations(regulation)
        for situation in situations:
            # Find the Situation node by description (since we created it in Pass 1)
            find_query = """
            MATCH (s:Situation)
            WHERE s.description = $description
            RETURN s.id as situation_id
            LIMIT 1
            """
            result = self.neo4j.execute_query(
                find_query,
                {"description": situation["description"]}
            )
            
            if result and "source_section_id" in situation:
                situation_id = result[0]["situation_id"]
                
                # Add RELEVANT_FOR relationship to batch
                self._add_relationship_to_batch({
                    "from_id": situation["source_section_id"],
                    "to_id": situation_id,
                    "from_label": "Section",
                    "to_label": "Situation",
                    "rel_type": "RELEVANT_FOR",
                    "properties": {
                        "relevance_score": 0.8,
                        "created_at": datetime.utcnow().isoformat()
                    }
                })
    
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
        situation_patterns = self.SITUATION_PATTERNS
        
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
        """Create Program node and relationships using batching with label hints."""
        program_id = str(uuid.uuid4())
        
        properties = {
            "id": program_id,
            "name": program["name"],
            "department": program["department"],
            "description": program["description"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add Program node to batch
        self._add_node_to_batch("Program", properties)
        
        # Determine regulation node label for relationship
        node_label = self._determine_node_label(regulation.title)
        
        # Add APPLIES_TO relationship to batch (WITH LABEL HINTS)
        self._add_relationship_to_batch({
            "from_id": str(regulation.id),
            "to_id": program_id,
            "from_label": node_label,  # NEW: Performance optimization
            "to_label": "Program",     # NEW: Performance optimization
            "rel_type": "APPLIES_TO",
            "properties": {
                "created_at": datetime.utcnow().isoformat()
            }
        })
    
    def _create_situation_node(self, situation: Dict[str, Any], regulation: Regulation):
        """Create Situation node and relationships using batching with label hints."""
        situation_id = str(uuid.uuid4())
        
        properties = {
            "id": situation_id,
            "description": situation["description"],
            "tags": situation.get("tags", []),
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add Situation node to batch
        self._add_node_to_batch("Situation", properties)
        
        # Add RELEVANT_FOR relationship to batch (WITH LABEL HINTS)
        if "source_section_id" in situation:
            self._add_relationship_to_batch({
                "from_id": situation["source_section_id"],
                "to_id": situation_id,
                "from_label": "Section",    # NEW: Performance optimization
                "to_label": "Situation",    # NEW: Performance optimization
                "rel_type": "RELEVANT_FOR",
                "properties": {
                    "relevance_score": 0.8,
                    "created_at": datetime.utcnow().isoformat()
                }
            })
    
    def _create_parent_act_relationship(self, regulation: Regulation):
        """
        Create ENACTED_UNDER relationship from Regulation to its parent Act using batching.
        
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
        find_query = """
        MATCH (a:Regulation)
        WHERE a.node_type = 'Legislation'
        AND (
            toLower(a.title) = toLower($parent_name)
            OR toLower(a.title) CONTAINS toLower($parent_base)
        )
        RETURN a.id as act_id, a.title as act_title
        LIMIT 1
        """
        
        # Remove "Act" for fuzzy matching
        parent_base = parent_act_name.replace(' Act', '').replace(' Loi', '').strip()
        
        result = self.neo4j.execute_query(
            find_query,
            {
                "parent_name": parent_act_name,
                "parent_base": parent_base
            }
        )
        
        if result:
            act_id = result[0]['act_id']
            act_title = result[0]['act_title']
            
            # Add ENACTED_UNDER relationship to batch (WITH LABEL HINTS)
            self._add_relationship_to_batch({
                "from_id": str(regulation.id),
                "to_id": act_id,
                "from_label": "Regulation",   # NEW: Performance optimization
                "to_label": "Legislation",    # NEW: Performance optimization (parent is always Legislation)
                "rel_type": "ENACTED_UNDER",
                "properties": {
                    "created_at": datetime.utcnow().isoformat()
                }
            })
            
            logger.info(f"Queued ENACTED_UNDER: {regulation.title} → {act_title}")
    
    def _create_policy_interpretation_relationship(self, regulation: Regulation):
        """
        Create INTERPRETS relationship from Policy to Legislation it interprets using batching.
        
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
        find_query = """
        MATCH (l:Regulation)
        WHERE l.node_type = 'Legislation'
        AND (
            toLower(l.title) = toLower($act_name)
            OR toLower(l.title) CONTAINS toLower($act_base)
        )
        RETURN l.id as act_id, l.title as act_title
        LIMIT 1
        """
        
        # Remove "Act" for fuzzy matching
        act_base = interpreted_act.replace(' Act', '').replace(' Loi', '').strip()
        
        result = self.neo4j.execute_query(
            find_query,
            {
                "act_name": interpreted_act,
                "act_base": act_base
            }
        )
        
        if result:
            act_id = result[0]['act_id']
            act_title = result[0]['act_title']
            
            # Add INTERPRETS relationship to batch (WITH LABEL HINTS)
            self._add_relationship_to_batch({
                "from_id": str(regulation.id),
                "to_id": act_id,
                "from_label": "Policy",       # NEW: Performance optimization
                "to_label": "Legislation",    # NEW: Performance optimization
                "rel_type": "INTERPRETS",
                "properties": {
                    "created_at": datetime.utcnow().isoformat()
                }
            })
            
            logger.info(f"Queued INTERPRETS: {regulation.title} → {act_title}")
    
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
    
    def create_nodes_for_regulation(self, regulation: uuid.UUID) -> Dict[str, Any]:
        """
        Create ONLY nodes (Regulation + Sections + Programs + Situations) for a regulation using batching.
        This is Pass 1 of two-pass processing.

        Args:
            regulation_id: Regulation UUID

        Returns:
            Statistics about node creation
        """
        logger.debug(f"Creating nodes for regulation {regulation.id}")

        if not regulation:
            raise ValueError(f"Regulation {regulation.id} not found")

        try:
            # Determine node label
            node_label = self._determine_node_label(regulation.title)
            
            # Prepare regulation node properties
            reg_properties = {
                "id": str(regulation.id),
                "name": regulation.title,
                "title": regulation.title,
                "jurisdiction": regulation.jurisdiction,
                "authority": regulation.authority if regulation.authority else "Unknown",
                "status": regulation.status,
                "language": regulation.language,
                "node_type": node_label,
                "created_at": datetime.utcnow().isoformat()
            }
            
            if regulation.effective_date:
                reg_properties["effective_date"] = regulation.effective_date.isoformat()
            if regulation.full_text and len(regulation.full_text) < 1000000:
                reg_properties["full_text"] = regulation.full_text
            if regulation.extra_metadata:
                reg_properties["metadata"] = regulation.extra_metadata
            
            # Add regulation node to batch
            self._add_node_to_batch(node_label, reg_properties)

            # Add section nodes to batch
            for idx, section in enumerate(regulation.sections):
                properties = {
                    "id": str(section.id),
                    "section_number": section.section_number,
                    "content": section.content if section.content else "",
                    "level": 0,
                    "created_at": datetime.utcnow().isoformat()
                }

                if section.title:
                    properties["title"] = section.title
                if section.extra_metadata:
                    properties["metadata"] = section.extra_metadata

                properties["citation"] = f"{regulation.title[:50]} Section {section.section_number}"

                # Add Section node to batch
                self._add_node_to_batch("Section", properties)

            # Extract and create Program/Situation NODES ONLY (no relationships yet)
            self._create_entity_nodes_only(regulation)

            logger.debug(f"Batched {len(regulation.sections)} section nodes for {regulation.title}")
            return self.stats

        except Exception as e:
            logger.error(f"Error creating nodes for regulation {regulation.id}: {e}")
            self.stats["errors"].append(str(e))
            raise

    def create_relationships_for_regulation(self, regulation: uuid.UUID) -> Dict[str, Any]:
        """
        Create ONLY relationships for a regulation.
        This is Pass 2 of two-pass processing.

        Args:
            regulation_id: Regulation UUID

        Returns:
            Statistics about relationship creation
        """
        logger.debug(f"Creating relationships for regulation {regulation.id}")

        try:
            # Determine node label for performance optimization
            node_label = self._determine_node_label(regulation.title)
            
            # Create HAS_SECTION relationships (WITH LABEL HINTS)
            for idx, section in enumerate(regulation.sections):
                self._create_has_section_relationship(
                    regulation.id,
                    section.id,
                    idx,
                    from_label=node_label  # NEW: Performance optimization
                )

            # Create cross-reference relationships (REFERENCES)
            self._create_cross_reference_relationships(regulation)

            # Create entity relationships ONLY (Programs, Situations)
            # The nodes were already created in Pass 1
            self._create_entity_relationships_only(regulation)

            # Create inter-document relationships (ENACTED_UNDER, INTERPRETS)
            self._create_parent_act_relationship(regulation)
            self._create_policy_interpretation_relationship(regulation)

            logger.debug(f"Created relationships for {regulation.title}")
            return self.stats

        except Exception as e:
            logger.error(f"Error creating relationships for regulation {regulation.id}: {e}")
            self.stats["errors"].append(str(e))
            raise

    def build_all_documents(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Build graphs for all regulations.
        Refactored to fetch IDs only, saving memory and preventing lazy-loading issues.
        """
        # 1. Fetch ONLY IDs
        # We query only the ID column. Loading 4,200 full objects into RAM 
        # at once causes memory bloat and lazy-loading lag.
        query = self.db.query(Regulation.id)
        
        if limit:
            query = query.limit(limit)
        
        # SQLAlchemy returns list of tuples [(uuid1,), (uuid2,)], so we flatten it
        regulation_ids = [r.id for r in query.all()]
        
        logger.info(f"Building graphs for {len(regulation_ids)} regulations")
        
        overall_stats = {
            "total_regulations": len(regulation_ids),
            "successful": 0,
            "failed": 0,
            "total_nodes": 0,
            "total_relationships": 0,
            "errors": []
        }
        
        # 2. Iterate over IDs
        for i, reg_id in enumerate(regulation_ids):
            try:
                # Reset local stats for this run
                self.stats = {
                    "nodes_created": 0,
                    "relationships_created": 0,
                    "errors": []
                }
                
                # Pass the ID! 
                # Our new build_document_graph will receive this ID, 
                # perform a 'joinedload' query, and fetch data instantly.
                doc_stats = self.build_document_graph(reg_id)
                
                overall_stats["successful"] += 1
                overall_stats["total_nodes"] += doc_stats["nodes_created"]
                overall_stats["total_relationships"] += doc_stats["relationships_created"]
                
                # Optional: Log progress every 100 documents so you know it's working
                if (i + 1) % 100 == 0:
                    logger.info(f"Progress: Processed {i + 1}/{len(regulation_ids)} regulations...")
                
            except Exception as e:
                # Log error but keep going
                logger.error(f"Failed to build graph for regulation ID {reg_id}: {e}")
                overall_stats["failed"] += 1
                overall_stats["errors"].append({
                    "regulation_id": str(reg_id),
                    "error": str(e)
                })
        
        # 3. Global Cleanup
        # Since build_document_graph flushes its own batches, we just need to run 
        # the inter-document linkers at the very end.
        try:
            self.create_inter_document_relationships()
        except Exception as e:
            logger.error(f"Error linking documents: {e}")
            overall_stats["errors"].append(f"Inter-document linking error: {e}")

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
        """Link Regulation nodes to Legislation nodes they implement using batching."""
        logger.info("Linking Regulations to Legislation...")

        # OPTIMIZED: Get all regulations and legislation in single queries
        regulations_query = """
        MATCH (r:Regulation)
        RETURN r.id as id, r.title as title
        """
        regulations = self.neo4j.execute_query(regulations_query)

        legislation_query = """
        MATCH (l:Legislation)
        RETURN l.id as id, l.title as title
        """
        all_legislation = self.neo4j.execute_query(legislation_query)

        # Create lookup map for fast legislation matching
        legislation_map = {leg['title'].lower(): leg for leg in all_legislation}

        linked_count = 0
        implements_rels = []

        for reg in regulations:
            # Search for legislation mentions in regulation title
            keywords = self._extract_legislation_keywords(reg["title"])

            for keyword in keywords:
                # Find matching legislation using in-memory lookup
                keyword_lower = keyword.lower()
                matching_legislation = None

                # Try exact match first
                if keyword_lower in legislation_map:
                    matching_legislation = legislation_map[keyword_lower]
                else:
                    # Try partial matches
                    for leg_title, leg_data in legislation_map.items():
                        if keyword_lower in leg_title:
                            matching_legislation = leg_data
                            break

                if matching_legislation:
                    # Queue IMPLEMENTS relationship for batching
                    implements_rels.append({
                        "reg_id": reg["id"],
                        "leg_id": matching_legislation["id"],
                        "description": f"Implements provisions of {matching_legislation['title']}"
                    })

                    linked_count += 1
                    logger.debug(f"Queued link: {reg['title'][:60]} → {matching_legislation['title'][:60]}")
                    break  # Only link to first matching legislation

        # BATCH CREATE: Use UNWIND for efficient bulk relationship creation
        if implements_rels:
            batch_query = """
            UNWIND $rels AS rel
            MATCH (r:Regulation {id: rel.reg_id})
            MATCH (l:Legislation {id: rel.leg_id})
            MERGE (r)-[imp:IMPLEMENTS]->(l)
            SET imp.description = rel.description
            SET imp.created_at = datetime()
            """
            self.neo4j.execute_write(batch_query, {"rels": implements_rels})

        logger.info(f"Created {linked_count} IMPLEMENTS relationships using batching")
    
    def _create_supersedes_relationships(self):
        """
        Create SUPERSEDES relationships based on amendment history using batching.
        Uses the amendments table to find which Acts supersede others and creates explicit Amendment nodes in Neo4j.
        """
        logger.info("Creating explicit Amendment nodes and SUPERSEDES relationships from amendment history...")

        from sqlalchemy.orm import joinedload

        # OPTIMIZED: Fetch all amendments with their regulations in one query (no N+1)
        amendments = self.db.query(Amendment).options(
            joinedload(Amendment.regulation)
        ).all()

        if not amendments:
            logger.info("No amendments found")
            return

        amendment_nodes = []
        amends_rels = []
        supersedes_rels = []

        for amendment in amendments:
            if not amendment.regulation:
                continue

            # Queue Amendment node for batching
            amendment_properties = {
                "id": str(amendment.id),
                "bill_number": amendment.extra_metadata.get('bill_number') if amendment.extra_metadata else None,
                "effective_date": amendment.effective_date.isoformat() if amendment.effective_date else None,
                "description": amendment.description if hasattr(amendment, 'description') else None,
                "metadata": amendment.extra_metadata,
                "created_at": datetime.utcnow().isoformat()
            }
            amendment_nodes.append(amendment_properties)

            # Queue AMENDS relationship for batching
            amends_rels.append({
                "amendment_id": str(amendment.id),
                "reg_id": str(amendment.regulation.id),
                "effective_date": amendment.effective_date.isoformat() if amendment.effective_date else None
            })

            # Queue SUPERSEDES relationship if applicable
            bill_info = amendment.extra_metadata.get('bill_number') if amendment.extra_metadata else None
            if bill_info and ', c. ' in bill_info:
                import re
                match = re.search(r'(\d{4}).*c\.\s*(\d+)', bill_info)
                if match:
                    year = match.group(1)
                    chapter_num = match.group(2)
                    supersedes_rels.append({
                        "amendment_id": str(amendment.id),
                        "year": year,
                        "chapter_num": chapter_num
                    })

        # BATCH CREATE: Amendment nodes
        if amendment_nodes:
            nodes_query = """
            UNWIND $nodes AS nodeProps
            CREATE (a:Amendment)
            SET a = nodeProps
            """
            self.neo4j.execute_write(nodes_query, {"nodes": amendment_nodes})
            logger.info(f"Created {len(amendment_nodes)} Amendment nodes in batch")

        # BATCH CREATE: AMENDS relationships
        if amends_rels:
            amends_query = """
            UNWIND $rels AS rel
            MATCH (a:Amendment {id: rel.amendment_id})
            MATCH (r:Regulation {id: rel.reg_id})
            MERGE (a)-[amends:AMENDS]->(r)
            SET amends.effective_date = rel.effective_date
            SET amends.created_at = datetime()
            """
            self.neo4j.execute_write(amends_query, {"rels": amends_rels})
            logger.info(f"Created {len(amends_rels)} AMENDS relationships in batch")

        # BATCH CREATE: SUPERSEDES relationships (with legislation lookup)
        if supersedes_rels:
            # First, get all legislation for matching
            legislation_query = """
            MATCH (l:Legislation)
            RETURN l.id as id, l.title as title
            """
            all_legislation = self.neo4j.execute_query(legislation_query)
            legislation_map = {leg['title'].lower(): leg for leg in all_legislation}

            # Match supersedes relationships to legislation
            matched_supersedes = []
            for rel in supersedes_rels:
                # Find legislation containing the year
                year = rel['year']
                matching_leg = None
                for leg_title, leg_data in legislation_map.items():
                    if year in leg_title:
                        matching_leg = leg_data
                        break

                if matching_leg:
                    matched_supersedes.append({
                        "amendment_id": rel["amendment_id"],
                        "leg_id": matching_leg["id"],
                        "chapter_num": rel["chapter_num"]
                    })

            if matched_supersedes:
                supersedes_query = """
                UNWIND $rels AS rel
                MATCH (a:Amendment {id: rel.amendment_id})
                MATCH (l:Legislation {id: rel.leg_id})
                MERGE (a)-[sup:SUPERSEDES]->(l)
                SET sup.chapter = rel.chapter_num
                SET sup.created_at = datetime()
                """
                self.neo4j.execute_write(supersedes_query, {"rels": matched_supersedes})
                logger.info(f"Created {len(matched_supersedes)} SUPERSEDES relationships in batch")

        total_count = len(amendment_nodes) + len(amends_rels) + len(matched_supersedes) if 'matched_supersedes' in locals() else 0
        logger.info(f"Created {len(amendment_nodes)} Amendment nodes and {total_count} relationships using batching")
    
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
    
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.stats
