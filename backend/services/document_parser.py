"""
Document parser service for processing regulatory documents.
Supports PDF, HTML, XML, and text formats.
"""
import hashlib
import io
import logging
from typing import Dict, List, Any, Optional, BinaryIO
from datetime import datetime
import re

# PDF parsing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logging.warning("PyPDF2 not available. PDF parsing will be disabled.")

# HTML parsing
try:
    from bs4 import BeautifulSoup
    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False
    logging.warning("BeautifulSoup4 not available. HTML parsing will be disabled.")

# XML parsing
import xml.etree.ElementTree as ET

from sqlalchemy.orm import Session
from models.document_models import (
    Document, DocumentSection, DocumentSubsection,
    DocumentClause, CrossReference, DocumentType, DocumentStatus
)
from utils.legal_text_parser import LegalTextParser, ParsedSection

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Service for parsing and processing regulatory documents.
    """
    
    SUPPORTED_FORMATS = ['pdf', 'html', 'htm', 'xml', 'txt']
    
    def __init__(self, db: Session):
        """
        Initialize document parser.
        
        Args:
            db: Database session
        """
        self.db = db
        self.text_parser = LegalTextParser()
    
    def parse_file(
        self,
        file: BinaryIO,
        filename: str,
        document_type: DocumentType,
        jurisdiction: str,
        authority: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Parse uploaded file and create document in database.
        
        Args:
            file: File binary stream
            filename: Original filename
            document_type: Type of document
            jurisdiction: Jurisdiction
            authority: Issuing authority
            metadata: Additional metadata
            
        Returns:
            Created Document object
        """
        logger.info(f"Parsing file: {filename}")
        
        # Read file content
        file_content = file.read()
        file_size = len(file_content)
        
        # Calculate file hash
        file_hash = self._calculate_hash(file_content)
        
        # Check if document already exists
        existing = self.db.query(Document).filter_by(file_hash=file_hash).first()
        if existing:
            logger.warning(f"Document with hash {file_hash} already exists")
            return existing
        
        # Determine file format
        file_format = self._get_file_format(filename)
        
        # Extract text based on format
        text = self._extract_text(file_content, file_format)
        
        if not text:
            raise ValueError(f"Could not extract text from {filename}")
        
        # Parse text structure
        parsed_data = self.text_parser.parse_document(text)
        
        # Extract document title from metadata or first section
        title = self._extract_title(text, parsed_data, metadata)
        
        # Create document record
        document = Document(
            title=title,
            document_type=document_type,
            jurisdiction=jurisdiction,
            authority=authority,
            full_text=text,
            original_filename=filename,
            file_format=file_format,
            file_size=file_size,
            file_hash=file_hash,
            status=DocumentStatus.ACTIVE,
            metadata=metadata or {},
            is_processed=False
        )
        
        self.db.add(document)
        self.db.flush()  # Get document ID
        
        # Create sections, subsections, and clauses
        self._create_document_structure(document, parsed_data)
        
        # Create cross-references
        self._create_cross_references(document, parsed_data)
        
        # Mark as processed
        document.is_processed = True
        document.processed_date = datetime.utcnow()
        
        self.db.commit()
        
        logger.info(f"Successfully parsed document: {document.id}")
        return document
    
    def _calculate_hash(self, content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(content).hexdigest()
    
    def _get_file_format(self, filename: str) -> str:
        """Extract file format from filename."""
        return filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'txt'
    
    def _extract_text(self, content: bytes, file_format: str) -> str:
        """
        Extract text from file content based on format.
        
        Args:
            content: File content bytes
            file_format: File format
            
        Returns:
            Extracted text
        """
        if file_format == 'pdf':
            return self._extract_pdf_text(content)
        elif file_format in ['html', 'htm']:
            return self._extract_html_text(content)
        elif file_format == 'xml':
            return self._extract_xml_text(content)
        else:  # txt or unknown
            return content.decode('utf-8', errors='ignore')
    
    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF content."""
        if not PDF_AVAILABLE:
            logger.error("PyPDF2 not installed. Cannot parse PDF files.")
            raise ValueError("PDF parsing not available. Install PyPDF2.")
        
        try:
            from io import BytesIO
            import PyPDF2
            
            pdf_file = BytesIO(content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            logger.info(f"PDF has {len(pdf_reader.pages)} pages")
            
            text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                    logger.debug(f"Extracted {len(page_text)} chars from page {page_num + 1}")
                else:
                    logger.warning(f"No text extracted from page {page_num + 1}")
            
            if not text.strip():
                logger.error("No text could be extracted from PDF. It might be a scanned document.")
                raise ValueError("PDF contains no extractable text. Use OCR for scanned documents.")
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {str(e)}")
            raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    def _extract_html_text(self, content: bytes) -> str:
        """Extract text from HTML content."""
        if not HTML_AVAILABLE:
            # Fallback: basic HTML stripping
            html = content.decode('utf-8', errors='ignore')
            return re.sub(r'<[^>]+>', ' ', html)
        
        try:
            html = content.decode('utf-8', errors='ignore')
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            text = '\n'.join(line for line in lines if line)
            
            logger.info("Extracted text from HTML")
            return text
        except Exception as e:
            logger.error(f"Error extracting HTML text: {e}")
            raise ValueError(f"Failed to parse HTML: {e}")
    
    def _extract_xml_text(self, content: bytes) -> str:
        """Extract text from XML content."""
        try:
            xml_str = content.decode('utf-8', errors='ignore')
            root = ET.fromstring(xml_str)
            
            # Extract all text content
            text_parts = []
            for elem in root.iter():
                if elem.text:
                    text_parts.append(elem.text.strip())
                if elem.tail:
                    text_parts.append(elem.tail.strip())
            
            text = '\n'.join(part for part in text_parts if part)
            
            logger.info("Extracted text from XML")
            return text
        except Exception as e:
            logger.error(f"Error extracting XML text: {e}")
            raise ValueError(f"Failed to parse XML: {e}")
    
    def _extract_title(
        self,
        text: str,
        parsed_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """Extract document title from various sources."""
        # Try metadata first
        if metadata and 'title' in metadata:
            return metadata['title']
        
        # Try first line of text
        first_line = text.split('\n')[0].strip()
        if len(first_line) > 10 and len(first_line) < 200:
            return first_line
        
        # Try first section title
        if parsed_data['sections'] and parsed_data['sections'][0].title:
            return parsed_data['sections'][0].title
        
        # Default
        return "Untitled Document"
    
    def _create_document_structure(
        self,
        document: Document,
        parsed_data: Dict[str, Any]
    ):
        """
        Create document structure (sections, subsections, clauses).
        
        Args:
            document: Document object
            parsed_data: Parsed document data
        """
        logger.info(f"Creating structure for {len(parsed_data['sections'])} sections")
        
        # Create sections
        section_map = {}  # Map section number to DB object
        
        for parsed_section in parsed_data['sections']:
            # Create section
            section = DocumentSection(
                document_id=document.id,
                section_number=parsed_section.number,
                section_title=parsed_section.title,
                section_type=parsed_section.section_type,
                content=parsed_section.content,
                level=parsed_section.level,
                order_index=parsed_section.order_index
            )
            
            self.db.add(section)
            self.db.flush()  # Get section ID
            
            section_map[parsed_section.number] = section
            
            # Extract and create subsections
            subsections = self.text_parser.extract_subsections(parsed_section.content)
            for subsection_data in subsections:
                subsection = DocumentSubsection(
                    section_id=section.id,
                    subsection_number=subsection_data['number'],
                    content=subsection_data['content'],
                    order_index=subsection_data['order'],
                    level=0
                )
                
                self.db.add(subsection)
                self.db.flush()
                
                # Extract and create clauses
                clauses = self.text_parser.extract_clauses(subsection_data['content'])
                for clause_data in clauses:
                    clause = DocumentClause(
                        subsection_id=subsection.id,
                        clause_identifier=clause_data['identifier'],
                        content=clause_data['content'],
                        order_index=clause_data['order']
                    )
                    
                    self.db.add(clause)
        
        # Set parent relationships based on hierarchy
        hierarchy = parsed_data['hierarchy']
        for section_number, parent_number in hierarchy['parent_map'].items():
            if section_number in section_map and parent_number in section_map:
                section_map[section_number].parent_section_id = section_map[parent_number].id
        
        self.db.flush()
        logger.info("Document structure created")
    
    def _create_cross_references(
        self,
        document: Document,
        parsed_data: Dict[str, Any]
    ):
        """
        Create cross-reference records.
        
        Args:
            document: Document object
            parsed_data: Parsed document data
        """
        logger.info(f"Creating {len(parsed_data['cross_references'])} cross-references")
        
        for parsed_ref in parsed_data['cross_references']:
            # Find source section
            source_section = self.db.query(DocumentSection).filter_by(
                document_id=document.id,
                section_number=parsed_ref.source_location
            ).first()
            
            # Create cross-reference
            cross_ref = CrossReference(
                source_document_id=document.id,
                source_section_id=source_section.id if source_section else None,
                source_location=parsed_ref.source_location,
                target_location=parsed_ref.target_location,
                reference_type=parsed_ref.reference_type,
                citation_text=parsed_ref.citation_text,
                context=parsed_ref.context
            )
            
            self.db.add(cross_ref)
        
        self.db.flush()
        logger.info("Cross-references created")
    
    def get_document_by_id(self, document_id: str) -> Optional[Document]:
        """Retrieve document by ID."""
        return self.db.query(Document).filter_by(id=document_id).first()
    
    def get_document_sections(self, document_id: str) -> List[DocumentSection]:
        """Retrieve all sections for a document."""
        return self.db.query(DocumentSection).filter_by(
            document_id=document_id
        ).order_by(DocumentSection.order_index).all()
    
    def search_documents(
        self,
        query: str,
        document_type: Optional[DocumentType] = None,
        jurisdiction: Optional[str] = None
    ) -> List[Document]:
        """
        Search documents by text query.
        
        Args:
            query: Search query
            document_type: Filter by document type
            jurisdiction: Filter by jurisdiction
            
        Returns:
            List of matching documents
        """
        filters = []
        
        if document_type:
            filters.append(Document.document_type == document_type)
        if jurisdiction:
            filters.append(Document.jurisdiction == jurisdiction)
        
        # Text search in title or full_text
        filters.append(
            (Document.title.ilike(f'%{query}%')) |
            (Document.full_text.ilike(f'%{query}%'))
        )
        
        return self.db.query(Document).filter(*filters).all()


def get_document_parser(db: Session) -> DocumentParser:
    """
    Factory function to create DocumentParser instance.
    
    Args:
        db: Database session
        
    Returns:
        DocumentParser instance
    """
    return DocumentParser(db)
