"""
Unit tests for GraphBuilder service.

Tests the build_regulation_subgraph method that creates Neo4j nodes
and relationships from PostgreSQL Regulation model.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date
import uuid

from services.graph_builder import GraphBuilder
from models.models import Regulation, Section, Citation, Amendment
from services.graph_service import GraphService


@pytest.fixture
def mock_db_session():
    """Mock database session with chained query support."""
    session = Mock()
    
    # Create a single query mock that can be configured by tests
    query_mock = Mock()
    filter_by_mock = Mock()
    filter_mock = Mock()
    
    # Configure return values for chained calls
    filter_by_mock.first = Mock(return_value=None)
    filter_by_mock.all = Mock(return_value=[])
    filter_mock.all = Mock(return_value=[])  # For Citation queries
    
    # Setup chaining: query().filter_by() returns filter_by_mock
    query_mock.filter_by = Mock(return_value=filter_by_mock)
    
    # Setup chaining for join queries: query().join().filter() returns filter_mock  
    query_mock.join = Mock(return_value=query_mock)  # join returns self for chaining
    query_mock.filter = Mock(return_value=filter_mock)  # filter after join
    
    # session.query() returns query_mock
    session.query = Mock(return_value=query_mock)
    
    return session


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client."""
    client = Mock()
    client.create_node = Mock(return_value={'id': str(uuid.uuid4())})
    client.create_relationship = Mock(return_value={'created': True})
    client.execute_write = Mock()
    return client


@pytest.fixture
def mock_regulation():
    """Create a mock regulation."""
    reg = Mock(spec=Regulation)
    reg.id = uuid.uuid4()
    reg.title = "Test Employment Act"
    reg.jurisdiction = "federal"
    reg.authority = "S.C. 2024, c. 1"
    reg.status = "active"
    reg.effective_date = date(2024, 1, 1)
    return reg


@pytest.fixture
def mock_sections():
    """Create mock sections."""
    sections = []
    for i in range(3):
        section = Mock(spec=Section)
        section.id = uuid.uuid4()
        section.regulation_id = uuid.uuid4()  # Will be set by test
        section.section_number = f"{i+1}"
        section.title = f"Section {i+1}"
        section.content = f"Content of section {i+1}"
        section.extra_metadata = {'level': 0}
        sections.append(section)
    return sections


@pytest.fixture
def mock_citations(mock_sections):
    """Create mock citations between sections."""
    citations = []
    if len(mock_sections) >= 2:
        citation = Mock(spec=Citation)
        citation.id = uuid.uuid4()
        citation.section_id = mock_sections[0].id
        citation.cited_section_id = mock_sections[1].id
        citation.citation_text = "as defined in section 2"
        citations.append(citation)
    return citations


@pytest.fixture
def graph_builder(mock_db_session, mock_neo4j_client):
    """Create GraphBuilder instance with mocks."""
    return GraphBuilder(mock_db_session, mock_neo4j_client)


class TestGraphBuilderInit:
    """Test GraphBuilder initialization."""
    
    def test_init_with_dependencies(self, mock_db_session, mock_neo4j_client):
        """Test initialization with required dependencies."""
        builder = GraphBuilder(mock_db_session, mock_neo4j_client)
        
        assert builder.neo4j == mock_neo4j_client
        assert builder.db == mock_db_session
        assert isinstance(builder.stats, dict)
        assert builder.stats['nodes_created'] == 0
        assert builder.stats['relationships_created'] == 0
    
    def test_init_stats_structure(self, graph_builder):
        """Test that stats dictionary has correct structure."""
        expected_keys = {'nodes_created', 'relationships_created', 'errors'}
        assert set(graph_builder.stats.keys()) == expected_keys


class TestBuildRegulationSubgraph:
    """Test build_regulation_subgraph method."""
    
    def test_builds_graph_for_valid_regulation(
        self, 
        graph_builder, 
        mock_db_session, 
        mock_regulation,
        mock_sections
    ):
        """Test successful graph building for a regulation."""
        # Setup
        regulation_id = str(mock_regulation.id)
        
        # Mock database queries
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_regulation
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = mock_sections
        
        # Execute
        result = graph_builder.build_regulation_subgraph(regulation_id)
        
        # Assert
        assert result['nodes_created'] == 4  # 1 regulation + 3 sections
        assert result['relationships_created'] == 3  # 3 HAS_SECTION relationships
        assert len(result.get('errors', [])) == 0
    
    def test_creates_regulation_node(
        self,
        graph_builder,
        mock_db_session,
        mock_regulation,
        mock_sections
    ):
        """Test that regulation node is created with correct properties."""
        regulation_id = str(mock_regulation.id)
        
        # Setup mocks
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_regulation
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = mock_sections
        
        # Execute
        graph_builder.build_regulation_subgraph(regulation_id)
        
        # Get the create_node call for the Regulation
        create_node_calls = graph_builder.neo4j.create_node.call_args_list
        
        # First call should be for Regulation node
        reg_call = create_node_calls[0]
        assert reg_call[0][0] == "Regulation"
        
        reg_properties = reg_call[0][1]
        assert reg_properties['id'] == str(mock_regulation.id)
        assert reg_properties['title'] == mock_regulation.title
        assert reg_properties['jurisdiction'] == mock_regulation.jurisdiction
        assert reg_properties['authority'] == mock_regulation.authority
        assert reg_properties['status'] == mock_regulation.status
    
    def test_creates_section_nodes(
        self,
        graph_builder,
        mock_db_session,
        mock_regulation,
        mock_sections
    ):
        """Test that section nodes are created for all sections."""
        regulation_id = str(mock_regulation.id)
        
        # Setup
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_regulation
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = mock_sections
        
        # Execute
        graph_builder.build_regulation_subgraph(regulation_id)
        
        # Get all create_node calls
        create_node_calls = graph_builder.neo4j.create_node.call_args_list
        
        # Should have 1 Regulation + 3 Sections = 4 nodes
        assert len(create_node_calls) == 4
        
        # Check section nodes (calls 1, 2, 3)
        for i, section in enumerate(mock_sections):
            section_call = create_node_calls[i + 1]
            assert section_call[0][0] == "Section"
            
            section_props = section_call[0][1]
            assert section_props['id'] == str(section.id)
            assert section_props['section_number'] == section.section_number
            assert section_props['title'] == section.title
            assert section_props['content'] == section.content
    
    def test_creates_has_section_relationships(
        self,
        graph_builder,
        mock_db_session,
        mock_regulation,
        mock_sections
    ):
        """Test that HAS_SECTION relationships are created."""
        regulation_id = str(mock_regulation.id)
        
        # Setup
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_regulation
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = mock_sections
        
        # Execute
        graph_builder.build_regulation_subgraph(regulation_id)
        
        # Check relationship calls (using execute_write for relationships)
        execute_write_calls = graph_builder.neo4j.execute_write.call_args_list
        
        # Should have 3 HAS_SECTION relationships
        assert len(execute_write_calls) >= 3
        
        # Verify execute_write was called for HAS_SECTION relationships
        for call in execute_write_calls[:3]:
            # Check that the query contains HAS_SECTION
            query = call[0][0]
            assert "HAS_SECTION" in query
    
    def test_creates_references_relationships_with_citations(
        self,
        graph_builder,
        mock_db_session,
        mock_regulation,
        mock_sections,
        mock_citations
    ):
        """Test that REFERENCES relationships are created for citations."""
        regulation_id = str(mock_regulation.id)
        
        # Setup - return citations when queried
        def mock_query_side_effect(model):
            query_mock = Mock()
            filter_by_mock = Mock()
            filter_mock = Mock()
            
            if model == Regulation:
                filter_by_mock.first = Mock(return_value=mock_regulation)
                query_mock.filter_by = Mock(return_value=filter_by_mock)
            elif model == Section:
                filter_by_mock.all = Mock(return_value=mock_sections)
                query_mock.filter_by = Mock(return_value=filter_by_mock)
            elif model == Citation:
                # Citation query uses join().filter().all()
                filter_mock.all = Mock(return_value=mock_citations)
                query_mock.join = Mock(return_value=query_mock)
                query_mock.filter = Mock(return_value=filter_mock)
            
            return query_mock
        
        mock_db_session.query.side_effect = mock_query_side_effect
        
        # Execute
        result = graph_builder.build_regulation_subgraph(regulation_id)
        
        # Should have additional REFERENCES relationships
        assert result['relationships_created'] >= 4  # 3 HAS_SECTION + 1 REFERENCES
    
    def test_raises_error_for_nonexistent_regulation(
        self,
        graph_builder,
        mock_db_session
    ):
        """Test that error is raised for non-existent regulation."""
        fake_id = str(uuid.uuid4())
        
        # Setup - return None for regulation
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        # Execute & Assert
        with pytest.raises(ValueError, match=f"Regulation {fake_id} not found"):
            graph_builder.build_regulation_subgraph(fake_id)
    
    def test_handles_regulation_with_no_sections(
        self,
        graph_builder,
        mock_db_session,
        mock_regulation
    ):
        """Test handling of regulation with no sections."""
        regulation_id = str(mock_regulation.id)
        
        # Setup - return empty list for sections
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_regulation
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = []
        
        # Execute
        result = graph_builder.build_regulation_subgraph(regulation_id)
        
        # Should still create regulation node
        assert result['nodes_created'] == 1
        assert result['relationships_created'] == 0
    
    def test_stats_tracking(
        self,
        graph_builder,
        mock_db_session,
        mock_regulation,
        mock_sections
    ):
        """Test that statistics are properly tracked."""
        regulation_id = str(mock_regulation.id)
        
        # Setup
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_regulation
        mock_db_session.query.return_value.filter_by.return_value.all.return_value = mock_sections
        
        # Execute
        result = graph_builder.build_regulation_subgraph(regulation_id)
        
        # Verify stats structure
        assert 'nodes_created' in result
        assert 'relationships_created' in result
        assert 'errors' in result
        assert isinstance(result['errors'], list)
        
        # Verify counts
        assert result['nodes_created'] > 0
        assert result['relationships_created'] > 0


class TestErrorHandling:
    """Test error handling in GraphBuilder."""
    
    def test_handles_neo4j_connection_error(
        self,
        graph_builder,
        mock_db_session,
        mock_regulation
    ):
        """Test handling of Neo4j connection errors."""
        regulation_id = str(mock_regulation.id)
        
        # Setup - mock Neo4j error
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_regulation
        graph_builder.neo4j.create_node.side_effect = Exception("Connection failed")
        
        # Execute & Assert
        with pytest.raises(Exception):
            graph_builder.build_regulation_subgraph(regulation_id)
    
    def test_handles_database_query_error(
        self,
        graph_builder,
        mock_db_session
    ):
        """Test handling of database query errors."""
        regulation_id = str(uuid.uuid4())
        
        # Setup - mock database error
        mock_db_session.query.side_effect = Exception("Database error")
        
        # Execute & Assert
        with pytest.raises(Exception):
            graph_builder.build_regulation_subgraph(regulation_id)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
