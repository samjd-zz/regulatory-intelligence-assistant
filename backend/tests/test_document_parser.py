"""
Tests for document_parser service.
"""
import pytest
import hashlib
from io import BytesIO
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from sqlalchemy.orm import Session

from services.document_parser import DocumentParser, get_document_parser
from models.document_models import (
    Document, DocumentSection, DocumentType, DocumentStatus
)


class TestDocumentParser:
    """Unit tests for DocumentParser class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def parser(self, mock_db):
        """Create DocumentParser instance with mock DB."""
        return DocumentParser(mock_db)
    
    def test_calculate_hash(self, parser):
        """Test file hash calculation."""
        content = b"test content"
        expected_hash = hashlib.sha256(content).hexdigest()
        
        result = parser._calculate_hash(content)
        
        assert result == expected_hash
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 produces 64 hex characters
    
    def test_calculate_hash_different_content(self, parser):
        """Test that different content produces different hashes."""
        content1 = b"test content 1"
        content2 = b"test content 2"
        
        hash1 = parser._calculate_hash(content1)
        hash2 = parser._calculate_hash(content2)
        
        assert hash1 != hash2
    
    def test_get_file_format(self, parser):
        """Test file format extraction from filename."""
        assert parser._get_file_format("document.pdf") == "pdf"
        assert parser._get_file_format("policy.html") == "html"
        assert parser._get_file_format("law.XML") == "xml"
        assert parser._get_file_format("text.txt") == "txt"
        assert parser._get_file_format("noextension") == "txt"
    
    def test_extract_text_plain(self, parser):
        """Test plain text extraction."""
        content = b"This is plain text content"
        
        result = parser._extract_text(content, 'txt')
        
        assert result == "This is plain text content"
    
    def test_extract_text_with_encoding(self, parser):
        """Test text extraction handles encoding errors."""
        # Include some invalid UTF-8 bytes
        content = b"Valid text \xff\xfe Invalid bytes"
        
        result = parser._extract_text(content, 'txt')
        
        # Should not raise error, uses errors='ignore'
        assert "Valid text" in result
    
    def test_extract_html_text_no_beautifulsoup(self, parser):
        """Test HTML parsing fallback without BeautifulSoup."""
        html_content = b"<html><body><h1>Title</h1><p>Content</p></body></html>"
        
        with patch('services.document_parser.HTML_AVAILABLE', False):
            result = parser._extract_html_text(html_content)
        
        # Should strip HTML tags
        assert "Title" in result
        assert "Content" in result
        assert "<html>" not in result
    
    def test_extract_html_text_with_beautifulsoup(self, parser):
        """Test HTML parsing with BeautifulSoup."""
        html_content = b"<html><body><h1>Title</h1><p>Content</p><script>alert('test')</script></body></html>"
        
        with patch('services.document_parser.HTML_AVAILABLE', True):
            with patch('services.document_parser.BeautifulSoup') as mock_bs:
                # Create mock script element
                mock_script = Mock()
                mock_script.decompose = Mock()
                
                # Create mock BeautifulSoup object that can be called
                mock_soup = MagicMock()
                mock_soup.get_text.return_value = "Title\n\nContent"
                # Make soup(['script', 'style']) return a list for iteration
                mock_soup.return_value = [mock_script]
                
                mock_bs.return_value = mock_soup
                
                result = parser._extract_html_text(html_content)
                
                assert "Title" in result
                assert "Content" in result
    
    def test_extract_xml_text(self, parser):
        """Test XML text extraction."""
        xml_content = b"""<?xml version="1.0"?>
        <document>
            <title>Document Title</title>
            <section>Section content</section>
        </document>
        """
        
        result = parser._extract_xml_text(xml_content)
        
        assert "Document Title" in result
        assert "Section content" in result
    
    def test_extract_xml_text_malformed(self, parser):
        """Test XML extraction with malformed XML."""
        malformed_xml = b"<document><unclosed>"
        
        with pytest.raises(ValueError, match="Failed to parse XML"):
            parser._extract_xml_text(malformed_xml)
    
    def test_extract_title_from_metadata(self, parser):
        """Test title extraction from metadata."""
        text = "Some document text"
        parsed_data = {'sections': []}
        metadata = {'title': 'Document Title from Metadata'}
        
        result = parser._extract_title(text, parsed_data, metadata)
        
        assert result == 'Document Title from Metadata'
    
    def test_extract_title_from_first_line(self, parser):
        """Test title extraction from first line."""
        text = "Document Title\nRest of content"
        parsed_data = {'sections': []}
        metadata = None
        
        result = parser._extract_title(text, parsed_data, metadata)
        
        assert result == "Document Title"
    
    def test_extract_title_fallback(self, parser):
        """Test title extraction fallback to default."""
        text = ""
        parsed_data = {'sections': []}
        metadata = None
        
        result = parser._extract_title(text, parsed_data, metadata)
        
        assert result == "Untitled Document"
    
    @patch('services.document_parser.PDF_AVAILABLE', False)
    def test_extract_pdf_text_not_available(self, parser):
        """Test PDF extraction when PyPDF2 is not available."""
        content = b"fake pdf content"
        
        with pytest.raises(ValueError, match="PDF parsing not available"):
            parser._extract_pdf_text(content)
    
    def test_get_document_by_id(self, parser, mock_db):
        """Test retrieving document by ID."""
        doc_id = "doc-123"
        expected_doc = Mock(spec=Document, id=doc_id)
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = expected_doc
        
        result = parser.get_document_by_id(doc_id)
        
        assert result == expected_doc
        mock_db.query.assert_called_once_with(Document)
        mock_query.filter_by.assert_called_once_with(id=doc_id)
    
    def test_get_document_sections(self, parser, mock_db):
        """Test retrieving document sections."""
        doc_id = "doc-123"
        sections = [
            Mock(spec=DocumentSection, order_index=1),
            Mock(spec=DocumentSection, order_index=2)
        ]
        
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter_by.return_value.order_by.return_value.all.return_value = sections
        
        result = parser.get_document_sections(doc_id)
        
        assert result == sections
        assert len(result) == 2
        mock_db.query.assert_called_once_with(DocumentSection)
        mock_query.filter_by.assert_called_once_with(document_id=doc_id)


class TestDocumentParserIntegration:
    """Integration tests for DocumentParser with real database."""
    
    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        # This would typically use a test database
        # For now, we'll skip if no test DB is available
        pytest.skip("Integration tests require test database setup")
    
    @pytest.fixture
    def parser(self, db_session):
        """Create DocumentParser with real DB session."""
        return DocumentParser(db_session)
    
    def test_parse_text_file_complete_workflow(self, parser, db_session):
        """Test complete workflow of parsing a text file."""
        # Create test file
        content = """Privacy Act
        
Section 1: Purpose
This section defines the purpose of the act.

Section 2: Definitions
This section provides key definitions.
"""
        file = BytesIO(content.encode())
        
        # Parse file
        document = parser.parse_file(
            file=file,
            filename="privacy_act.txt",
            document_type=DocumentType.ACT,
            jurisdiction="Federal",
            authority="Parliament of Canada",
            metadata={'title': 'Privacy Act'}
        )
        
        # Verify document created
        assert document is not None
        assert document.title == 'Privacy Act'
        assert document.document_type == DocumentType.ACT
        assert document.jurisdiction == "Federal"
        assert document.is_processed is True
        
        # Verify sections created
        sections = parser.get_document_sections(document.id)
        assert len(sections) >= 2


class TestPDFParsing:
    """Tests specific to PDF parsing functionality."""
    
    @pytest.fixture
    def parser_with_pdf(self):
        """Create parser with PDF support mocked."""
        mock_db = Mock(spec=Session)
        parser = DocumentParser(mock_db)
        return parser
    
    def test_extract_pdf_text_success(self, parser_with_pdf, monkeypatch):
        """Test successful PDF text extraction."""
        with patch('services.document_parser.PDF_AVAILABLE', True):
            # Mock PyPDF2 module
            mock_pypdf2_module = MagicMock()
            
            # Create mock PDF reader
            mock_page = Mock()
            mock_page.extract_text.return_value = "Test PDF content"
            
            mock_reader = Mock()
            mock_reader.pages = [mock_page]
            
            mock_pypdf2_module.PdfReader.return_value = mock_reader
            
            # Add mock module to sys.modules so it can be imported
            import sys
            monkeypatch.setitem(sys.modules, 'PyPDF2', mock_pypdf2_module)
            
            content = b"fake pdf content"
            result = parser_with_pdf._extract_pdf_text(content)
            
            assert "Test PDF content" in result
            assert isinstance(result, str)
    
    def test_extract_pdf_text_empty_pages(self, parser_with_pdf, monkeypatch):
        """Test PDF extraction with empty pages."""
        with patch('services.document_parser.PDF_AVAILABLE', True):
            # Mock PyPDF2 module
            mock_pypdf2_module = MagicMock()
            
            # Create mock PDF reader with empty pages
            mock_page = Mock()
            mock_page.extract_text.return_value = ""
            
            mock_reader = Mock()
            mock_reader.pages = [mock_page]
            
            mock_pypdf2_module.PdfReader.return_value = mock_reader
            
            # Add mock module to sys.modules
            import sys
            monkeypatch.setitem(sys.modules, 'PyPDF2', mock_pypdf2_module)
            
            content = b"fake pdf content"
            
            with pytest.raises(ValueError, match="PDF contains no extractable text"):
                parser_with_pdf._extract_pdf_text(content)
    
    def test_extract_pdf_text_parsing_error(self, parser_with_pdf, monkeypatch):
        """Test PDF extraction with parsing error."""
        with patch('services.document_parser.PDF_AVAILABLE', True):
            # Mock PyPDF2 module
            mock_pypdf2_module = MagicMock()
            mock_pypdf2_module.PdfReader.side_effect = Exception("Corrupted PDF")
            
            # Add mock module to sys.modules
            import sys
            monkeypatch.setitem(sys.modules, 'PyPDF2', mock_pypdf2_module)
            
            content = b"fake pdf content"
            
            with pytest.raises(ValueError, match="Failed to parse PDF"):
                parser_with_pdf._extract_pdf_text(content)


class TestDocumentParserFactory:
    """Tests for factory function."""
    
    def test_get_document_parser(self):
        """Test factory function creates DocumentParser instance."""
        mock_db = Mock(spec=Session)
        
        parser = get_document_parser(mock_db)
        
        assert isinstance(parser, DocumentParser)
        assert parser.db == mock_db


class TestSearchDocuments:
    """Tests for document search functionality."""
    
    @pytest.fixture
    def parser(self):
        """Create parser with mock DB."""
        mock_db = Mock(spec=Session)
        return DocumentParser(mock_db)
    
    def test_search_documents_by_query(self, parser):
        """Test searching documents by text query."""
        query = "privacy"
        docs = [
            Mock(spec=Document, title="Privacy Act"),
            Mock(spec=Document, title="Data Privacy Regulation")
        ]
        
        mock_query_builder = MagicMock()
        parser.db.query.return_value = mock_query_builder
        mock_query_builder.filter.return_value.all.return_value = docs
        
        results = parser.search_documents(query)
        
        assert len(results) == 2
        parser.db.query.assert_called_once_with(Document)
    
    def test_search_documents_with_filters(self, parser):
        """Test searching with document type and jurisdiction filters."""
        query = "tax"
        doc_type = DocumentType.REGULATION
        jurisdiction = "Federal"
        
        mock_query_builder = MagicMock()
        parser.db.query.return_value = mock_query_builder
        mock_query_builder.filter.return_value.all.return_value = []
        
        results = parser.search_documents(
            query, 
            document_type=doc_type,
            jurisdiction=jurisdiction
        )
        
        parser.db.query.assert_called_once_with(Document)
        # Verify filter was called (complex filter with multiple conditions)
        assert mock_query_builder.filter.called


class TestDocumentStructureCreation:
    """Tests for document structure creation (sections, subsections, clauses)."""
    
    @pytest.fixture
    def parser(self):
        """Create parser with mock DB."""
        mock_db = Mock(spec=Session)
        mock_db.add = Mock()
        mock_db.flush = Mock()
        return DocumentParser(mock_db)
    
    def test_create_document_structure_basic(self, parser):
        """Test creating basic document structure."""
        document = Mock(spec=Document, id="doc-123")
        
        # Create mock parsed section
        mock_section = Mock()
        mock_section.number = "1"
        mock_section.title = "Section Title"
        mock_section.content = "Section content"
        mock_section.section_type = "section"
        mock_section.level = 0
        mock_section.order_index = 0
        
        parsed_data = {
            'sections': [mock_section],
            'hierarchy': {'parent_map': {}},
            'cross_references': []
        }
        
        # Mock text parser methods
        with patch.object(parser.text_parser, 'extract_subsections', return_value=[]):
            parser._create_document_structure(document, parsed_data)
        
        # Verify section was added to DB
        assert parser.db.add.called
        assert parser.db.flush.called
    
    def test_create_cross_references(self, parser):
        """Test creating cross-references."""
        document = Mock(spec=Document, id="doc-123")
        
        # Create mock cross-reference
        mock_ref = Mock()
        mock_ref.source_location = "Section 1"
        mock_ref.target_location = "Section 2"
        mock_ref.reference_type = "reference"
        mock_ref.citation_text = "See Section 2"
        mock_ref.context = "Context text"
        
        parsed_data = {
            'cross_references': [mock_ref]
        }
        
        # Mock query for source section
        mock_query = MagicMock()
        parser.db.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None
        
        # Mock CrossReference model to avoid field mismatch
        with patch('services.document_parser.CrossReference') as mock_cross_ref_class:
            mock_cross_ref_instance = Mock()
            mock_cross_ref_class.return_value = mock_cross_ref_instance
            
            parser._create_cross_references(document, parsed_data)
            
            # Verify cross-reference was created and added
            assert mock_cross_ref_class.called
            assert parser.db.add.called
            assert parser.db.flush.called


class TestDOCXParsing:
    """Tests specific to DOCX parsing functionality."""
    
    @pytest.fixture
    def parser_with_docx(self):
        """Create parser with DOCX support mocked."""
        mock_db = Mock(spec=Session)
        parser = DocumentParser(mock_db)
        return parser
    
    @patch('services.document_parser.DOCX_AVAILABLE', False)
    def test_extract_docx_text_not_available(self, parser_with_docx):
        """Test DOCX extraction when python-docx is not available."""
        content = b"fake docx content"
        
        with pytest.raises(ValueError, match="DOCX parsing not available"):
            parser_with_docx._extract_docx_text(content)
    
    def test_extract_docx_text_success(self, parser_with_docx, monkeypatch):
        """Test successful DOCX text extraction."""
        with patch('services.document_parser.DOCX_AVAILABLE', True):
            # Mock docx module and Document class
            mock_docx_module = MagicMock()
            
            # Create mock paragraphs
            mock_para1 = Mock()
            mock_para1.text = "Privacy Act"
            
            mock_para2 = Mock()
            mock_para2.text = "Section 1: Purpose"
            
            mock_para3 = Mock()
            mock_para3.text = "This act protects personal information."
            
            # Create mock document
            mock_doc = Mock()
            mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
            mock_doc.tables = []
            
            # Set up the mock module's Document class
            mock_docx_module.Document.return_value = mock_doc
            
            # Add mock module to sys.modules
            import sys
            monkeypatch.setitem(sys.modules, 'docx', mock_docx_module)
            
            content = b"fake docx content"
            result = parser_with_docx._extract_docx_text(content)
            
            assert "Privacy Act" in result
            assert "Section 1: Purpose" in result
            assert "This act protects personal information." in result
            assert isinstance(result, str)
    
    def test_extract_docx_text_with_tables(self, parser_with_docx, monkeypatch):
        """Test DOCX extraction with tables."""
        with patch('services.document_parser.DOCX_AVAILABLE', True):
            # Mock docx module and Document class
            mock_docx_module = MagicMock()
            
            # Create mock paragraphs
            mock_para = Mock()
            mock_para.text = "Document with table"
            
            # Create mock table cells
            mock_cell1 = Mock()
            mock_cell1.text = "Header 1"
            
            mock_cell2 = Mock()
            mock_cell2.text = "Header 2"
            
            mock_cell3 = Mock()
            mock_cell3.text = "Data 1"
            
            mock_cell4 = Mock()
            mock_cell4.text = "Data 2"
            
            # Create mock rows
            mock_row1 = Mock()
            mock_row1.cells = [mock_cell1, mock_cell2]
            
            mock_row2 = Mock()
            mock_row2.cells = [mock_cell3, mock_cell4]
            
            # Create mock table
            mock_table = Mock()
            mock_table.rows = [mock_row1, mock_row2]
            
            # Create mock document
            mock_doc = Mock()
            mock_doc.paragraphs = [mock_para]
            mock_doc.tables = [mock_table]
            
            # Set up the mock module's Document class
            mock_docx_module.Document.return_value = mock_doc
            
            # Add mock module to sys.modules
            import sys
            monkeypatch.setitem(sys.modules, 'docx', mock_docx_module)
            
            content = b"fake docx content"
            result = parser_with_docx._extract_docx_text(content)
            
            assert "Document with table" in result
            assert "Header 1" in result
            assert "Header 2" in result
            assert "Data 1" in result
            assert "Data 2" in result
            assert " | " in result  # Table delimiter
    
    def test_extract_docx_text_empty(self, parser_with_docx, monkeypatch):
        """Test DOCX extraction with empty document."""
        with patch('services.document_parser.DOCX_AVAILABLE', True):
            # Mock docx module and Document class
            mock_docx_module = MagicMock()
            
            # Create empty mock document
            mock_doc = Mock()
            mock_doc.paragraphs = []
            mock_doc.tables = []
            
            # Set up the mock module's Document class
            mock_docx_module.Document.return_value = mock_doc
            
            # Add mock module to sys.modules
            import sys
            monkeypatch.setitem(sys.modules, 'docx', mock_docx_module)
            
            content = b"fake docx content"
            
            with pytest.raises(ValueError, match="DOCX contains no extractable text"):
                parser_with_docx._extract_docx_text(content)
    
    def test_extract_docx_text_parsing_error(self, parser_with_docx, monkeypatch):
        """Test DOCX extraction with parsing error."""
        with patch('services.document_parser.DOCX_AVAILABLE', True):
            # Mock docx module and Document class
            mock_docx_module = MagicMock()
            mock_docx_module.Document.side_effect = Exception("Corrupted DOCX")
            
            # Add mock module to sys.modules
            import sys
            monkeypatch.setitem(sys.modules, 'docx', mock_docx_module)
            
            content = b"fake docx content"
            
            with pytest.raises(ValueError, match="Failed to parse DOCX"):
                parser_with_docx._extract_docx_text(content)
    
    def test_extract_docx_text_with_empty_paragraphs(self, parser_with_docx, monkeypatch):
        """Test DOCX extraction filters out empty paragraphs."""
        with patch('services.document_parser.DOCX_AVAILABLE', True):
            # Mock docx module and Document class
            mock_docx_module = MagicMock()
            
            # Create mix of empty and non-empty paragraphs
            mock_para1 = Mock()
            mock_para1.text = "First line"
            
            mock_para2 = Mock()
            mock_para2.text = "   "  # Empty whitespace
            
            mock_para3 = Mock()
            mock_para3.text = "Second line"
            
            mock_doc = Mock()
            mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
            mock_doc.tables = []
            
            # Set up the mock module's Document class
            mock_docx_module.Document.return_value = mock_doc
            
            # Add mock module to sys.modules
            import sys
            monkeypatch.setitem(sys.modules, 'docx', mock_docx_module)
            
            content = b"fake docx content"
            result = parser_with_docx._extract_docx_text(content)
            
            assert "First line" in result
            assert "Second line" in result
            # Should not have excessive whitespace from empty para
            assert result.count("\n\n") <= 1


class TestDocumentParserEdgeCases:
    """Tests for edge cases and error handling."""
    
    @pytest.fixture
    def parser(self):
        """Create parser with mock DB."""
        mock_db = Mock(spec=Session)
        return DocumentParser(mock_db)
    
    def test_parse_file_duplicate_hash(self, parser):
        """Test parsing file that already exists (duplicate hash)."""
        content = b"test content"
        file = BytesIO(content)
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Mock existing document with same hash
        existing_doc = Mock(spec=Document, file_hash=file_hash)
        
        mock_query = MagicMock()
        parser.db.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = existing_doc
        
        result = parser.parse_file(
            file=file,
            filename="test.txt",
            document_type=DocumentType.ACT,
            jurisdiction="Federal",
            authority="Government"
        )
        
        # Should return existing document
        assert result == existing_doc
    
    def test_parse_file_empty_text(self, parser):
        """Test parsing file with no extractable text."""
        content = b""
        file = BytesIO(content)
        
        # Mock no existing document
        mock_query = MagicMock()
        parser.db.query.return_value = mock_query
        mock_query.filter_by.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="Could not extract text"):
            parser.parse_file(
                file=file,
                filename="empty.txt",
                document_type=DocumentType.ACT,
                jurisdiction="Federal",
                authority="Government"
            )
    
    def test_unsupported_file_format(self, parser):
        """Test handling of unsupported file format."""
        content = b"binary content"
        
        # Should fall back to text extraction
        result = parser._extract_text(content, 'unknown')
        
        # Should attempt to decode as text
        assert isinstance(result, str)
