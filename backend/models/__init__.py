"""
Models package for regulatory intelligence assistant.
Contains all SQLAlchemy ORM models.
"""

from models.models import (
    User,
    Regulation,
    Section,
    Citation,
    Amendment,
    QueryHistory,
    WorkflowSession,
    WorkflowStep,
    AlertSubscription,
    Alert,
)

from models.document_models import (
    Document,
    DocumentSection,
    DocumentSubsection,
    DocumentClause,
    CrossReference,
    DocumentMetadata,
    DocumentType,
    DocumentStatus,
)

__all__ = [
    # Core models
    "User",
    "Regulation",
    "Section",
    "Citation",
    "Amendment",
    "QueryHistory",
    "WorkflowSession",
    "WorkflowStep",
    "AlertSubscription",
    "Alert",
    # Document models
    "Document",
    "DocumentSection",
    "DocumentSubsection",
    "DocumentClause",
    "CrossReference",
    "DocumentMetadata",
    "DocumentType",
    "DocumentStatus",
]
