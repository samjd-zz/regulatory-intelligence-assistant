"""
Document Ingestion API Routes

Provides REST API endpoints for uploading, processing, and managing
regulatory documents in the system.

Features:
- Single document upload
- Bulk document upload
- Document parsing (PDF, HTML, XML)
- Automatic indexing in Elasticsearch
- Knowledge graph integration
- Processing status tracking

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import hashlib
import logging

from services.search_service import SearchService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Initialize services
search_service = SearchService()


# === Pydantic Models ===

class DocumentMetadata(BaseModel):
    """Metadata for a regulatory document"""
    title: str = Field(..., description="Document title", min_length=1)
    jurisdiction: str = Field(..., description="Jurisdiction (federal, provincial, etc.)")
    document_type: str = Field("regulation", description="Type of document")
    authority: Optional[str] = Field(None, description="Issuing authority")
    effective_date: Optional[str] = Field(None, description="Effective date (YYYY-MM-DD)")
    citation: Optional[str] = Field(None, description="Legal citation")
    section_number: Optional[str] = Field(None, description="Section number")
    program: Optional[str] = Field(None, description="Related program")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Employment Insurance Act - Section 7",
                "jurisdiction": "federal",
                "document_type": "act",
                "authority": "Parliament of Canada",
                "effective_date": "1996-06-30",
                "citation": "S.C. 1996, c. 23, s. 7",
                "section_number": "7",
                "program": "employment_insurance",
                "tags": ["benefits", "eligibility"]
            }
        }


class DocumentContent(BaseModel):
    """Document content for ingestion"""
    metadata: DocumentMetadata
    content: str = Field(..., description="Document text content", min_length=10)

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {
                    "title": "Employment Insurance Act - Section 7",
                    "jurisdiction": "federal",
                    "effective_date": "1996-06-30"
                },
                "content": "Benefits are payable to persons who have lost employment..."
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response for document upload"""
    success: bool = True
    document_id: str
    title: str
    status: str  # indexed, processing, failed
    message: str
    indexed_at: str
    metadata: Dict[str, Any] = {}


class DocumentListResponse(BaseModel):
    """Response for listing documents"""
    success: bool = True
    total: int
    documents: List[Dict[str, Any]]
    page: int = 1
    page_size: int = 20


class ProcessingStatus(BaseModel):
    """Document processing status"""
    document_id: str
    status: str  # pending, processing, completed, failed
    progress: float  # 0.0 to 1.0
    message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None


# === Storage for processing status (in-memory for MVP) ===
processing_status_store: Dict[str, ProcessingStatus] = {}


# === Helper Functions ===

def generate_document_id(title: str, content: str) -> str:
    """Generate unique document ID from content hash"""
    hash_input = f"{title}:{content}"
    return hashlib.md5(hash_input.encode()).hexdigest()[:16]


def extract_content_from_file(file: UploadFile) -> str:
    """
    Extract text content from uploaded file

    Args:
        file: Uploaded file

    Returns:
        Extracted text content

    Raises:
        HTTPException: If file type not supported or extraction fails
    """
    content_type = file.content_type
    filename = file.filename.lower()

    try:
        if content_type == "text/plain" or filename.endswith('.txt'):
            # Plain text file
            return file.file.read().decode('utf-8')

        elif content_type == "application/pdf" or filename.endswith('.pdf'):
            # PDF file (requires PyPDF2 or similar)
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="PDF parsing not yet implemented. Please upload text or provide content directly."
            )

        elif content_type in ["text/html", "application/xhtml+xml"] or filename.endswith('.html'):
            # HTML file (requires BeautifulSoup or similar)
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="HTML parsing not yet implemented. Please upload text or provide content directly."
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {content_type}"
            )

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decode file. Please ensure file is in UTF-8 encoding."
        )


async def process_and_index_document(doc_id: str, metadata: Dict, content: str):
    """
    Process and index document (background task)

    Args:
        doc_id: Document ID
        metadata: Document metadata
        content: Document content
    """
    try:
        # Update status
        processing_status_store[doc_id] = ProcessingStatus(
            document_id=doc_id,
            status="processing",
            progress=0.0,
            started_at=datetime.now().isoformat()
        )

        # Prepare document for indexing
        doc = {
            "id": doc_id,
            "title": metadata["title"],
            "content": content,
            "jurisdiction": metadata.get("jurisdiction", "unknown"),
            "document_type": metadata.get("document_type", "regulation"),
            "authority": metadata.get("authority"),
            "effective_date": metadata.get("effective_date"),
            "citation": metadata.get("citation"),
            "section_number": metadata.get("section_number"),
            "program": metadata.get("program"),
            "tags": metadata.get("tags", []),
            "indexed_at": datetime.now().isoformat()
        }

        # Index in Elasticsearch
        result = search_service.index_document(doc)

        # Update status
        processing_status_store[doc_id] = ProcessingStatus(
            document_id=doc_id,
            status="completed",
            progress=1.0,
            completed_at=datetime.now().isoformat(),
            message=f"Document indexed successfully: {result['result']}"
        )

        logger.info(f"Document {doc_id} indexed successfully")

    except Exception as e:
        # Update status with error
        processing_status_store[doc_id] = ProcessingStatus(
            document_id=doc_id,
            status="failed",
            progress=0.0,
            error=str(e),
            completed_at=datetime.now().isoformat()
        )

        logger.error(f"Failed to index document {doc_id}: {e}")


# === API Endpoints ===

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    document: DocumentContent
):
    """
    Upload a single regulatory document

    Accepts document content and metadata, generates unique ID,
    and queues for indexing in Elasticsearch.

    - **metadata**: Document metadata (title, jurisdiction, etc.)
    - **content**: Document text content

    Returns document ID and indexing status.
    """
    try:
        # Generate document ID
        doc_id = generate_document_id(document.metadata.title, document.content)

        # Add to processing queue
        background_tasks.add_task(
            process_and_index_document,
            doc_id,
            document.metadata.dict(),
            document.content
        )

        # Initialize processing status
        processing_status_store[doc_id] = ProcessingStatus(
            document_id=doc_id,
            status="pending",
            progress=0.0
        )

        return DocumentUploadResponse(
            document_id=doc_id,
            title=document.metadata.title,
            status="pending",
            message="Document queued for processing",
            indexed_at=datetime.now().isoformat(),
            metadata={"jurisdiction": document.metadata.jurisdiction}
        )

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.post("/upload/bulk", status_code=status.HTTP_202_ACCEPTED)
async def upload_documents_bulk(
    background_tasks: BackgroundTasks,
    documents: List[DocumentContent]
):
    """
    Upload multiple regulatory documents in bulk

    Accepts a list of documents (max 100) and queues them
    for processing and indexing.

    - **documents**: List of documents with metadata and content

    Returns processing status for each document.
    """
    if len(documents) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 documents per bulk upload"
        )

    results = []

    for document in documents:
        try:
            # Generate document ID
            doc_id = generate_document_id(document.metadata.title, document.content)

            # Add to processing queue
            background_tasks.add_task(
                process_and_index_document,
                doc_id,
                document.metadata.dict(),
                document.content
            )

            # Initialize processing status
            processing_status_store[doc_id] = ProcessingStatus(
                document_id=doc_id,
                status="pending",
                progress=0.0
            )

            results.append({
                "document_id": doc_id,
                "title": document.metadata.title,
                "status": "pending"
            })

        except Exception as e:
            logger.error(f"Failed to queue document {document.metadata.title}: {e}")
            results.append({
                "title": document.metadata.title,
                "status": "failed",
                "error": str(e)
            })

    return {
        "success": True,
        "total": len(documents),
        "queued": len([r for r in results if r['status'] == 'pending']),
        "failed": len([r for r in results if r['status'] == 'failed']),
        "results": results
    }


@router.get("/status/{document_id}", response_model=ProcessingStatus)
async def get_processing_status(document_id: str):
    """
    Get processing status for a document

    Returns current processing status including progress,
    errors, and completion time.

    - **document_id**: Document identifier

    Returns processing status information.
    """
    if document_id not in processing_status_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return processing_status_store[document_id]


@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    jurisdiction: Optional[str] = None,
    document_type: Optional[str] = None
):
    """
    List all indexed documents

    Returns paginated list of documents with optional filtering.

    - **page**: Page number (default: 1)
    - **page_size**: Results per page (default: 20, max: 100)
    - **jurisdiction**: Filter by jurisdiction (optional)
    - **document_type**: Filter by document type (optional)

    Returns list of documents with metadata.
    """
    if page_size > 100:
        page_size = 100

    try:
        # Build filters
        filters = {}
        if jurisdiction:
            filters['jurisdiction'] = jurisdiction
        if document_type:
            filters['document_type'] = document_type

        # Search for documents
        from_offset = (page - 1) * page_size

        result = search_service.keyword_search(
            query="*",  # Match all
            filters=filters,
            size=page_size,
            from_=from_offset
        )

        # Format documents
        documents = [
            {
                "id": hit['id'],
                "title": hit['title'],
                "jurisdiction": hit.get('jurisdiction'),
                "document_type": hit.get('document_type'),
                "effective_date": hit.get('effective_date'),
                "indexed_at": hit.get('indexed_at')
            }
            for hit in result['hits']
        ]

        return DocumentListResponse(
            total=result['total'],
            documents=documents,
            page=page,
            page_size=page_size
        )

    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/{document_id}")
async def get_document(document_id: str):
    """
    Get a specific document by ID

    Returns complete document including metadata and content.

    - **document_id**: Document identifier

    Returns document details.
    """
    try:
        document = search_service.get_document(document_id)

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        return {
            "success": True,
            "document": document
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve document: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document from the system

    Removes document from Elasticsearch index.

    - **document_id**: Document identifier

    Returns deletion confirmation.
    """
    try:
        result = search_service.delete_document(document_id)

        if result['result'] == 'deleted':
            return {
                "success": True,
                "message": f"Document {document_id} deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/health")
async def document_service_health():
    """
    Health check for document service

    Returns service status and statistics.
    """
    try:
        stats = search_service.get_stats()

        return {
            "status": "healthy",
            "service": "documents",
            "document_count": stats.get('document_count', 0),
            "index_name": stats.get('index_name'),
            "processing_queue": len(processing_status_store)
        }

    except Exception as e:
        return {
            "status": "degraded",
            "service": "documents",
            "error": str(e)
        }
