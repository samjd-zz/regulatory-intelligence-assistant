"""
SQLAlchemy models for document management and processing.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


class DocumentType(str, enum.Enum):
    """Types of regulatory documents."""

    ACT = "act"
    REGULATION = "regulation"
    POLICY = "policy"
    GUIDELINE = "guideline"
    ORDER = "order"
    DIRECTIVE = "directive"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    ERROR = "error"


class Document(Base):
    """Model for uploaded regulatory documents."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    document_type = Column(
        SQLEnum(DocumentType), nullable=False, default=DocumentType.REGULATION
    )
    jurisdiction = Column(String(100), nullable=False, index=True)
    authority = Column(String(255), nullable=True)
    document_number = Column(String(100), nullable=True)
    full_text = Column(Text, nullable=True)

    # File info
    file_format = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=True, unique=True, index=True)

    # Dates
    effective_date = Column(DateTime, nullable=True)
    publication_date = Column(DateTime, nullable=True)

    # Processing status
    status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING)
    is_processed = Column(Boolean, default=False)

    # Metadata
    doc_metadata = Column(JSON, default=dict)

    # Timestamps
    upload_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sections = relationship(
        "DocumentSection", back_populates="document", cascade="all, delete-orphan"
    )
    cross_references = relationship(
        "CrossReference", back_populates="document", cascade="all, delete-orphan"
    )
    metadata_entries = relationship(
        "DocumentMetadata", back_populates="document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_documents_type_jurisdiction", "document_type", "jurisdiction"),
    )


class DocumentSection(Base):
    """Model for sections within documents."""

    __tablename__ = "document_sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    # Section identification
    section_number = Column(String(100), nullable=False)
    section_title = Column(String(500), nullable=True)
    section_type = Column(String(50), default="section")

    # Content
    content = Column(Text, nullable=True)

    # Hierarchy
    parent_section_id = Column(
        UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=True
    )
    level = Column(Integer, default=0)
    order_index = Column(Integer, default=0)

    # Metadata
    section_metadata = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="sections")
    parent_section = relationship(
        "DocumentSection", remote_side=[id], backref="subsections"
    )
    clauses = relationship(
        "DocumentClause", back_populates="section", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_document_sections_doc_number", "document_id", "section_number"),
    )


class DocumentSubsection(Base):
    """Model for subsections (deprecated, use DocumentSection with parent_section_id)."""

    __tablename__ = "document_subsections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(
        UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=False
    )

    subsection_number = Column(String(100), nullable=False)
    subsection_title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    subsection_metadata = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentClause(Base):
    """Model for individual clauses within sections."""

    __tablename__ = "document_clauses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(
        UUID(as_uuid=True), ForeignKey("document_sections.id"), nullable=False
    )

    clause_number = Column(String(50), nullable=True)
    clause_type = Column(String(50), default="clause")
    content = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)

    clause_metadata = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    section = relationship("DocumentSection", back_populates="clauses")


class CrossReference(Base):
    """Model for cross-references within documents."""

    __tablename__ = "cross_references"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    # Source reference
    source_section = Column(String(100), nullable=True)
    source_text = Column(Text, nullable=True)

    # Target reference
    target_document = Column(String(500), nullable=True)
    target_section = Column(String(100), nullable=True)
    target_document_id = Column(UUID(as_uuid=True), nullable=True)

    # Reference metadata
    reference_type = Column(String(50), default="citation")
    reference_metadata = Column(JSON, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="cross_references")


class DocumentMetadata(Base):
    """Model for additional document metadata."""

    __tablename__ = "document_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)

    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String(50), default="string")

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="metadata_entries")

    __table_args__ = (Index("ix_document_metadata_doc_key", "document_id", "key"),)
