"""
FastAPI routes for document upload and management.
"""
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field
from uuid import UUID

from database import get_db
from services.document_parser import get_document_parser, DocumentParser
from models.document_models import (
    Document, DocumentSection, DocumentType, DocumentStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


# ============================================
# Pydantic Schemas
# ============================================

class DocumentUploadResponse(BaseModel):
    """Response schema for document upload."""
    id: UUID
    title: str
    document_type: DocumentType
    jurisdiction: str
    file_format: str
    file_size: int
    total_sections: int
    total_cross_references: int
    is_processed: bool
    upload_date: datetime
    
    class Config:
        from_attributes = True


class DocumentDetail(BaseModel):
    """Detailed document information."""
    id: UUID
    title: str
    document_type: DocumentType
    jurisdiction: str
    authority: str
    document_number: Optional[str]
    full_text: Optional[str]
    file_format: str
    file_size: int
    effective_date: Optional[datetime]
    publication_date: Optional[datetime]
    status: DocumentStatus
    doc_metadata: dict = Field(alias="metadata")
    is_processed: bool
    upload_date: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True


class SectionResponse(BaseModel):
    """Section information."""
    id: UUID
    section_number: str
    section_title: Optional[str]
    section_type: str
    content: str
    level: int
    order_index: int
    
    class Config:
        from_attributes = True


class CrossReferenceResponse(BaseModel):
    """Cross-reference information."""
    id: UUID
    source_location: str
    target_location: str
    reference_type: str
    citation_text: str
    context: str
    
    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    """Search request schema."""
    query: str = Field(..., min_length=2, description="Search query")
    document_type: Optional[DocumentType] = None
    jurisdiction: Optional[str] = None
    status: Optional[DocumentStatus] = None


# ============================================
# API Endpoints
# ============================================

@router.post("/upload", response_model=DocumentUploadResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(..., description="Document file to upload"),
    document_type: DocumentType = Form(..., description="Type of document"),
    jurisdiction: str = Form(..., description="Jurisdiction"),
    authority: str = Form(..., description="Issuing authority"),
    document_number: Optional[str] = Form(None, description="Official document number"),
    effective_date: Optional[str] = Form(None, description="Effective date (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a regulatory document.
    
    Supported formats: PDF, HTML, XML, TXT
    
    The uploaded document will be:
    - Parsed to extract sections, subsections, and clauses
    - Analyzed for cross-references
    - Stored in the database with full structure
    """
    logger.info(f"Uploading document: {file.filename}")
    
    # Validate file format
    file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if file_ext not in ['pdf', 'html', 'htm', 'xml', 'txt']:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported: PDF, HTML, XML, TXT"
        )
    
    try:
        # Parse metadata
        metadata = {}
        if document_number:
            metadata['document_number'] = document_number
        if effective_date:
            metadata['effective_date'] = effective_date
        
        # Parse document
        parser = get_document_parser(db)
        document = parser.parse_file(
            file=file.file,
            filename=file.filename,
            document_type=document_type,
            jurisdiction=jurisdiction,
            authority=authority,
            metadata=metadata
        )
        
        # Update document number if provided
        if document_number:
            document.document_number = document_number
        if effective_date:
            document.effective_date = datetime.fromisoformat(effective_date)
        
        db.commit()
        
        # Count sections and cross-references
        total_sections = db.query(DocumentSection).filter_by(document_id=document.id).count()
        total_cross_refs = len(document.cross_references)
        
        return DocumentUploadResponse(
            id=document.id,
            title=document.title,
            document_type=document.document_type,
            jurisdiction=document.jurisdiction,
            file_format=document.file_format,
            file_size=document.file_size,
            total_sections=total_sections,
            total_cross_references=total_cross_refs,
            is_processed=document.is_processed,
            upload_date=document.upload_date
        )
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("/{document_id}", response_model=DocumentDetail)
async def get_document(
    document_id: UUID,
    include_full_text: bool = Query(True, description="Include full document text"),
    db: Session = Depends(get_db)
):
    """
    Retrieve document details by ID.
    """
    document = db.query(Document).filter_by(id=document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Optionally exclude full text for performance
    if not include_full_text:
        document.full_text = None
    
    return document


@router.get("/{document_id}/sections", response_model=List[SectionResponse])
async def get_document_sections(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve all sections for a document.
    """
    # Verify document exists
    document = db.query(Document).filter_by(id=document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get sections
    sections = db.query(DocumentSection).filter_by(
        document_id=document_id
    ).order_by(DocumentSection.order_index).all()
    
    return sections


@router.get("/{document_id}/cross-references", response_model=List[CrossReferenceResponse])
async def get_document_cross_references(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Retrieve all cross-references for a document.
    """
    # Verify document exists
    document = db.query(Document).filter_by(id=document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return document.cross_references


@router.post("/search", response_model=List[DocumentDetail])
async def search_documents(
    search_request: DocumentSearchRequest,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Search documents by text query and filters.
    """
    parser = get_document_parser(db)
    
    # Perform search
    documents = parser.search_documents(
        query=search_request.query,
        document_type=search_request.document_type,
        jurisdiction=search_request.jurisdiction
    )
    
    # Apply status filter if provided
    if search_request.status:
        documents = [d for d in documents if d.status == search_request.status]
    
    # Apply pagination
    total = len(documents)
    documents = documents[skip:skip + limit]
    
    # Exclude full text for performance
    for doc in documents:
        doc.full_text = None
    
    return documents


@router.get("/", response_model=List[DocumentDetail])
async def list_documents(
    document_type: Optional[DocumentType] = None,
    jurisdiction: Optional[str] = None,
    status: Optional[DocumentStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all documents with optional filters.
    """
    query = db.query(Document)
    
    # Apply filters
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if jurisdiction:
        query = query.filter(Document.jurisdiction == jurisdiction)
    if status:
        query = query.filter(Document.status == status)
    
    # Order by upload date (newest first)
    query = query.order_by(Document.upload_date.desc())
    
    # Pagination
    documents = query.offset(skip).limit(limit).all()
    
    # Exclude full text for performance
    for doc in documents:
        doc.full_text = None
    
    return documents


@router.delete("/{document_id}")
async def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a document and all its associated data.
    """
    document = db.query(Document).filter_by(id=document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        db.delete(document)
        db.commit()
        
        return {"message": "Document deleted successfully", "id": str(document_id)}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete document")


@router.get("/statistics/summary")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get document statistics.
    """
    from sqlalchemy import func
    
    # Total documents
    total_documents = db.query(func.count(Document.id)).scalar()
    
    # Documents by type
    by_type = db.query(
        Document.document_type,
        func.count(Document.id).label('count')
    ).group_by(Document.document_type).all()
    
    # Documents by jurisdiction
    by_jurisdiction = db.query(
        Document.jurisdiction,
        func.count(Document.id).label('count')
    ).group_by(Document.jurisdiction).all()
    
    # Documents by status
    by_status = db.query(
        Document.status,
        func.count(Document.id).label('count')
    ).group_by(Document.status).all()
    
    # Total sections
    total_sections = db.query(func.count(DocumentSection.id)).scalar()
    
    return {
        "total_documents": total_documents,
        "total_sections": total_sections,
        "by_type": {str(item[0]): item[1] for item in by_type},
        "by_jurisdiction": {item[0]: item[1] for item in by_jurisdiction},
        "by_status": {str(item[0]): item[1] for item in by_status}
    }
