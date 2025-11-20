"""
Neo4j database client for knowledge graph operations.
Provides connection management and query execution utilities.
"""
from neo4j import GraphDatabase, Driver, Session
from typing import Dict, List, Any, Optional
import os
import json
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


class Neo4jClient:
    """Neo4j database client with connection pooling."""
    
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI (default from env)
            user: Neo4j username (default from env)
            password: Neo4j password (default from env)
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password123")
        
        self._driver: Optional[Driver] = None
        
    def connect(self) -> Driver:
        """Establish connection to Neo4j."""
        if not self._driver:
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            logger.info(f"Connected to Neo4j at {self.uri}")
        return self._driver
    
    def close(self):
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")
    
    def verify_connectivity(self) -> bool:
        """
        Verify Neo4j connection.
        
        Returns:
            True if connected successfully
        """
        try:
            driver = self.connect()
            driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed: {e}")
            return False
    
    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            List of result records as dictionaries
        """
        driver = self.connect()
        with driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a write transaction.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
            
        Returns:
            Result summary
        """
        driver = self.connect()
        with driver.session() as session:
            result = session.run(query, parameters or {})
            summary = result.consume()
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set,
                "labels_added": summary.counters.labels_added,
            }
    
    def create_node(
        self,
        label: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a single node.
        
        Args:
            label: Node label (e.g., 'Legislation', 'Section')
            properties: Node properties
            
        Returns:
            Created node data
        """
        # Serialize complex types to JSON strings
        processed_props = {}
        for key, value in properties.items():
            if isinstance(value, dict):
                # Convert dict to JSON string
                processed_props[key] = json.dumps(value)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                # Convert list of dicts to JSON string
                processed_props[key] = json.dumps(value)
            else:
                processed_props[key] = value
        
        query = f"""
        CREATE (n:{label} $properties)
        RETURN n
        """
        results = self.execute_query(query, {"properties": processed_props})
        return results[0]['n'] if results else {}
    
    def create_relationship(
        self,
        from_label: str,
        from_id: str,
        to_label: str,
        to_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a relationship between two nodes.
        
        Args:
            from_label: Source node label
            from_id: Source node ID
            to_label: Target node label
            to_id: Target node ID
            rel_type: Relationship type
            properties: Relationship properties
            
        Returns:
            Relationship summary
        """
        query = f"""
        MATCH (a:{from_label} {{id: $from_id}})
        MATCH (b:{to_label} {{id: $to_id}})
        CREATE (a)-[r:{rel_type}]->(b)
        SET r += $properties
        RETURN r
        """
        return self.execute_write(
            query,
            {
                "from_id": from_id,
                "to_id": to_id,
                "properties": properties or {}
            }
        )
    
    def find_node(
        self,
        label: str,
        properties: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find a node by label and properties.
        
        Args:
            label: Node label
            properties: Properties to match
            
        Returns:
            Node data or None if not found
        """
        # Build WHERE clause
        where_conditions = [f"n.{key} = ${key}" for key in properties.keys()]
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        MATCH (n:{label})
        WHERE {where_clause}
        RETURN n
        LIMIT 1
        """
        results = self.execute_query(query, properties)
        return results[0]['n'] if results else None
    
    def find_related_nodes(
        self,
        node_label: str,
        node_id: str,
        rel_type: Optional[str] = None,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        Find nodes related to a given node.
        
        Args:
            node_label: Source node label
            node_id: Source node ID
            rel_type: Relationship type (None for any type)
            direction: 'outgoing', 'incoming', or 'both'
            
        Returns:
            List of related nodes
        """
        rel_pattern = f"[:{rel_type}]" if rel_type else "[]"
        
        if direction == "outgoing":
            pattern = f"(n:{node_label} {{id: $node_id}})-{rel_pattern}->(m)"
        elif direction == "incoming":
            pattern = f"(n:{node_label} {{id: $node_id}})<-{rel_pattern}-(m)"
        else:  # both
            pattern = f"(n:{node_label} {{id: $node_id}})-{rel_pattern}-(m)"
        
        query = f"""
        MATCH {pattern}
        RETURN m, labels(m) as labels
        """
        return self.execute_query(query, {"node_id": node_id})
    
    def delete_node(self, label: str, node_id: str) -> Dict[str, Any]:
        """
        Delete a node and its relationships.
        
        Args:
            label: Node label
            node_id: Node ID
            
        Returns:
            Deletion summary
        """
        query = f"""
        MATCH (n:{label} {{id: $node_id}})
        DETACH DELETE n
        """
        return self.execute_write(query, {"node_id": node_id})
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """
        Get graph statistics.
        
        Returns:
            Statistics about nodes and relationships
        """
        query = """
        MATCH (n)
        RETURN count(n) as node_count,
               labels(n) as labels
        """
        node_results = self.execute_query(query)
        
        query = """
        MATCH ()-[r]->()
        RETURN count(r) as rel_count,
               type(r) as type
        """
        rel_results = self.execute_query(query)
        
        return {
            "nodes": node_results,
            "relationships": rel_results
        }


# Global client instance
_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """
    Get global Neo4j client instance.
    
    Returns:
        Neo4jClient instance
    """
    global _client
    if _client is None:
        _client = Neo4jClient()
        _client.connect()
    return _client


def close_neo4j_client():
    """Close global Neo4j client."""
    global _client
    if _client:
        _client.close()
        _client = None
