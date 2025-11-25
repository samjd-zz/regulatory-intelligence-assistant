"""
Unit tests for GraphService.

Tests the get_graph_stats and get_graph_overview methods.
"""
import pytest
from unittest.mock import Mock, patch
from services.graph_service import GraphService


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client."""
    client = Mock()
    client.execute_query = Mock()
    return client


@pytest.fixture
def graph_service(mock_neo4j_client):
    """Create GraphService with mock client."""
    return GraphService(client=mock_neo4j_client)


class TestGetGraphOverview:
    """Test get_graph_overview method."""
    
    def test_returns_overview_with_nodes_and_relationships(self, graph_service, mock_neo4j_client):
        """Test that overview contains nodes and relationships."""
        # Mock node counts
        mock_neo4j_client.execute_query.side_effect = [
            [
                {'label': 'Legislation', 'count': 4},
                {'label': 'Section', 'count': 10},
                {'label': 'Regulation', 'count': 5}
            ],
            [
                {'type': 'HAS_SECTION', 'count': 10},
                {'type': 'REFERENCES', 'count': 15}
            ]
        ]
        
        result = graph_service.get_graph_overview()
        
        assert 'nodes' in result
        assert 'relationships' in result
        assert result['nodes']['Legislation'] == 4
        assert result['nodes']['Section'] == 10
        assert result['nodes']['Regulation'] == 5
        assert result['relationships']['HAS_SECTION'] == 10
        assert result['relationships']['REFERENCES'] == 15
    
    def test_handles_empty_graph(self, graph_service, mock_neo4j_client):
        """Test handling of empty graph."""
        mock_neo4j_client.execute_query.side_effect = [
            [],  # No nodes
            []   # No relationships
        ]
        
        result = graph_service.get_graph_overview()
        
        assert result['nodes'] == {}
        assert result['relationships'] == {}
    
    def test_makes_two_queries(self, graph_service, mock_neo4j_client):
        """Test that two queries are executed."""
        mock_neo4j_client.execute_query.side_effect = [
            [{'label': 'Test', 'count': 1}],
            [{'type': 'TEST_REL', 'count': 1}]
        ]
        
        graph_service.get_graph_overview()
        
        assert mock_neo4j_client.execute_query.call_count == 2
    
    def test_first_query_gets_node_counts(self, graph_service, mock_neo4j_client):
        """Test that first query gets node counts."""
        mock_neo4j_client.execute_query.side_effect = [
            [{'label': 'Test', 'count': 1}],
            []
        ]
        
        graph_service.get_graph_overview()
        
        first_call = mock_neo4j_client.execute_query.call_args_list[0]
        query = first_call[0][0]
        
        # Check query contains node matching
        assert 'MATCH (n)' in query
        assert 'labels(n)' in query
        assert 'count(n)' in query
    
    def test_second_query_gets_relationship_counts(self, graph_service, mock_neo4j_client):
        """Test that second query gets relationship counts."""
        mock_neo4j_client.execute_query.side_effect = [
            [],
            [{'type': 'TEST', 'count': 1}]
        ]
        
        graph_service.get_graph_overview()
        
        second_call = mock_neo4j_client.execute_query.call_args_list[1]
        query = second_call[0][0]
        
        # Check query contains relationship matching
        assert 'MATCH ()-[r]->()' in query
        assert 'type(r)' in query
        assert 'count(r)' in query


class TestGetGraphStats:
    """Test get_graph_stats method."""
    
    def test_is_alias_for_get_graph_overview(self, graph_service, mock_neo4j_client):
        """Test that get_graph_stats returns same data as get_graph_overview."""
        # Mock data
        mock_neo4j_client.execute_query.side_effect = [
            [{'label': 'Regulation', 'count': 10}],
            [{'type': 'HAS_SECTION', 'count': 30}]
        ]
        
        result = graph_service.get_graph_stats()
        
        assert 'nodes' in result
        assert 'relationships' in result
        assert result['nodes']['Regulation'] == 10
        assert result['relationships']['HAS_SECTION'] == 30
    
    def test_returns_same_structure_as_overview(self, graph_service, mock_neo4j_client):
        """Test that get_graph_stats has same structure as get_graph_overview."""
        mock_neo4j_client.execute_query.side_effect = [
            [{'label': 'Section', 'count': 50}],
            [{'type': 'REFERENCES', 'count': 25}]
        ]
        
        stats_result = graph_service.get_graph_stats()
        
        # Reset mock for second call
        mock_neo4j_client.execute_query.side_effect = [
            [{'label': 'Section', 'count': 50}],
            [{'type': 'REFERENCES', 'count': 25}]
        ]
        
        overview_result = graph_service.get_graph_overview()
        
        assert stats_result.keys() == overview_result.keys()
    
    def test_works_with_multiple_node_types(self, graph_service, mock_neo4j_client):
        """Test with multiple node types."""
        mock_neo4j_client.execute_query.side_effect = [
            [
                {'label': 'Legislation', 'count': 4},
                {'label': 'Section', 'count': 20},
                {'label': 'Regulation', 'count': 8},
                {'label': 'Program', 'count': 3},
                {'label': 'Situation', 'count': 5}
            ],
            [
                {'type': 'HAS_SECTION', 'count': 20},
                {'type': 'REFERENCES', 'count': 35},
                {'type': 'APPLIES_TO', 'count': 12},
                {'type': 'RELEVANT_FOR', 'count': 18}
            ]
        ]
        
        result = graph_service.get_graph_stats()
        
        # Check all node types present
        assert len(result['nodes']) == 5
        assert result['nodes']['Legislation'] == 4
        assert result['nodes']['Program'] == 3
        
        # Check all relationship types present
        assert len(result['relationships']) == 4
        assert result['relationships']['APPLIES_TO'] == 12
        assert result['relationships']['RELEVANT_FOR'] == 18
    
    def test_handles_large_counts(self, graph_service, mock_neo4j_client):
        """Test handling of large node/relationship counts."""
        mock_neo4j_client.execute_query.side_effect = [
            [
                {'label': 'Section', 'count': 10000},
                {'label': 'Regulation', 'count': 5000}
            ],
            [{'type': 'HAS_SECTION', 'count': 50000}]
        ]
        
        result = graph_service.get_graph_stats()
        
        assert result['nodes']['Section'] == 10000
        assert result['nodes']['Regulation'] == 5000
        assert result['relationships']['HAS_SECTION'] == 50000


class TestErrorHandling:
    """Test error handling in GraphService."""
    
    def test_handles_neo4j_connection_error(self, graph_service, mock_neo4j_client):
        """Test handling of Neo4j connection errors."""
        mock_neo4j_client.execute_query.side_effect = Exception("Connection failed")
        
        with pytest.raises(Exception, match="Connection failed"):
            graph_service.get_graph_stats()
    
    def test_handles_query_execution_error(self, graph_service, mock_neo4j_client):
        """Test handling of query execution errors."""
        mock_neo4j_client.execute_query.side_effect = Exception("Query syntax error")
        
        with pytest.raises(Exception):
            graph_service.get_graph_overview()
    
    def test_handles_malformed_response(self, graph_service, mock_neo4j_client):
        """Test handling of malformed responses."""
        # Return malformed data (missing 'count' key)
        mock_neo4j_client.execute_query.side_effect = [
            [{'label': 'Test'}],  # Missing 'count'
            []
        ]
        
        # Should raise KeyError or similar
        with pytest.raises(Exception):
            graph_service.get_graph_stats()


class TestIntegrationWithRealQueries:
    """Test that queries are properly formatted for Neo4j."""
    
    def test_node_query_format(self, graph_service, mock_neo4j_client):
        """Test that node count query is properly formatted."""
        mock_neo4j_client.execute_query.side_effect = [
            [{'label': 'Test', 'count': 1}],
            []
        ]
        
        graph_service.get_graph_stats()
        
        node_query = mock_neo4j_client.execute_query.call_args_list[0][0][0]
        
        # Verify Cypher syntax
        assert node_query.strip().startswith('MATCH')
        assert 'RETURN' in node_query
        assert '(n)' in node_query
    
    def test_relationship_query_format(self, graph_service, mock_neo4j_client):
        """Test that relationship count query is properly formatted."""
        mock_neo4j_client.execute_query.side_effect = [
            [],
            [{'type': 'TEST', 'count': 1}]
        ]
        
        graph_service.get_graph_stats()
        
        rel_query = mock_neo4j_client.execute_query.call_args_list[1][0][0]
        
        # Verify Cypher syntax
        assert rel_query.strip().startswith('MATCH')
        assert 'RETURN' in rel_query
        assert '-[r]->' in rel_query


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
