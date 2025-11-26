"""
Core SQLAlchemy models for regulatory data, users, and workflows.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    Boolean,
    DateTime,
    Date,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from database import Base


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False, default="citizen")
    department = Column(String(255), nullable=True)
    preferences = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    query_history = relationship("QueryHistory", back_populates="user")
    workflow_sessions = relationship("WorkflowSession", back_populates="user")
    alert_subscriptions = relationship("AlertSubscription", back_populates="user")


class Regulation(Base):
    """Model for regulations, acts, and legal documents."""

    __tablename__ = "regulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    jurisdiction = Column(String(100), nullable=False, index=True)
    authority = Column(String(255), nullable=True)
    effective_date = Column(Date, nullable=True)
    status = Column(String(50), default="active", index=True)
    full_text = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sections = relationship(
        "Section", back_populates="regulation", cascade="all, delete-orphan"
    )
    amendments = relationship(
        "Amendment", back_populates="regulation", cascade="all, delete-orphan"
    )
    alerts = relationship("Alert", back_populates="regulation")

    __table_args__ = (
        Index("ix_regulations_title_jurisdiction", "title", "jurisdiction"),
    )


class Section(Base):
    """Model for sections within regulations."""

    __tablename__ = "sections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulation_id = Column(
        UUID(as_uuid=True), ForeignKey("regulations.id"), nullable=False
    )
    section_number = Column(String(50), nullable=False)
    title = Column(String(500), nullable=True)
    content = Column(Text, nullable=True)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    regulation = relationship("Regulation", back_populates="sections")
    citations = relationship(
        "Citation", back_populates="section", foreign_keys="Citation.section_id"
    )
    cited_by = relationship(
        "Citation",
        back_populates="cited_section",
        foreign_keys="Citation.cited_section_id",
    )

    __table_args__ = (
        UniqueConstraint(
            "regulation_id", "section_number", name="uq_section_regulation"
        ),
        Index("ix_sections_regulation_number", "regulation_id", "section_number"),
    )


class Citation(Base):
    """Model for cross-references between sections."""

    __tablename__ = "citations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("sections.id"), nullable=False)
    cited_section_id = Column(
        UUID(as_uuid=True), ForeignKey("sections.id"), nullable=True
    )
    citation_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    section = relationship(
        "Section", back_populates="citations", foreign_keys=[section_id]
    )
    cited_section = relationship(
        "Section", back_populates="cited_by", foreign_keys=[cited_section_id]
    )


class Amendment(Base):
    """Model for tracking regulation amendments."""

    __tablename__ = "amendments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    regulation_id = Column(
        UUID(as_uuid=True), ForeignKey("regulations.id"), nullable=False
    )
    amendment_type = Column(String(50), nullable=False)
    effective_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    regulation = relationship("Regulation", back_populates="amendments")


class QueryHistory(Base):
    """Model for tracking user queries."""

    __tablename__ = "query_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    query = Column(Text, nullable=False)
    entities = Column(JSON, default=dict)
    intent = Column(String(100), nullable=True)
    results = Column(JSON, default=list)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="query_history")


class WorkflowSession(Base):
    """Model for workflow sessions."""

    __tablename__ = "workflow_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    workflow_type = Column(String(100), nullable=False)
    state = Column(JSON, default=dict)
    status = Column(String(50), default="active")
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="workflow_sessions")
    steps = relationship(
        "WorkflowStep", back_populates="session", cascade="all, delete-orphan"
    )


class WorkflowStep(Base):
    """Model for individual workflow steps."""

    __tablename__ = "workflow_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(
        UUID(as_uuid=True), ForeignKey("workflow_sessions.id"), nullable=False
    )
    step_number = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False)
    input_data = Column(JSON, default=dict)
    validation_result = Column(JSON, default=dict)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("WorkflowSession", back_populates="steps")


class AlertSubscription(Base):
    """Model for alert subscriptions."""

    __tablename__ = "alert_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    jurisdiction = Column(String(100), nullable=True)
    topics = Column(JSON, default=list)
    frequency = Column(String(50), default="daily")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alert_subscriptions")
    alerts = relationship(
        "Alert", back_populates="subscription", cascade="all, delete-orphan"
    )


class Alert(Base):
    """Model for regulatory change alerts."""

    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(
        UUID(as_uuid=True), ForeignKey("alert_subscriptions.id"), nullable=False
    )
    change_type = Column(String(50), nullable=False)
    regulation_id = Column(
        UUID(as_uuid=True), ForeignKey("regulations.id"), nullable=True
    )
    summary = Column(Text, nullable=True)
    read = Column(Boolean, default=False)
    extra_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscription = relationship("AlertSubscription", back_populates="alerts")
    regulation = relationship("Regulation", back_populates="alerts")
