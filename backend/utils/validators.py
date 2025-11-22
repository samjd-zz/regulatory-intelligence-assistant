"""
Data Validation Framework

Comprehensive validation utilities for regulatory data including:
- Input sanitization
- Schema validation
- Legal content validation
- Citation format validation
- Date and jurisdiction validation
- Custom validators for domain-specific data

Author: Developer 2 (AI/ML Engineer)
Created: 2025-11-22
"""

import re
from typing import Any, List, Dict, Optional, Callable, Union
from datetime import datetime, date
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# === Validation Results ===

@dataclass
class ValidationError:
    """Represents a validation error"""
    field: str
    message: str
    value: Any = None
    code: str = "VALIDATION_ERROR"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'field': self.field,
            'message': self.message,
            'code': self.code,
            'value': str(self.value) if self.value is not None else None
        }


@dataclass
class ValidationResult:
    """Result of validation"""
    valid: bool
    errors: List[ValidationError]
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'valid': self.valid,
            'errors': [e.to_dict() for e in self.errors],
            'warnings': self.warnings,
            'error_count': self.error_count
        }


# === Input Sanitization ===

class InputSanitizer:
    """Sanitize user inputs to prevent injection attacks"""

    @staticmethod
    def sanitize_string(value: str, max_length: int = 10000) -> str:
        """
        Sanitize string input

        Args:
            value: Input string
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")

        # Trim whitespace
        sanitized = value.strip()

        # Truncate to max length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')

        # Normalize whitespace
        sanitized = ' '.join(sanitized.split())

        return sanitized

    @staticmethod
    def sanitize_query(query: str) -> str:
        """
        Sanitize search query

        Args:
            query: Search query string

        Returns:
            Sanitized query
        """
        # Basic sanitization
        sanitized = InputSanitizer.sanitize_string(query, max_length=500)

        # Remove potentially dangerous characters for Elasticsearch
        dangerous_chars = ['\\', '{', '}', '[', ']', '<', '>']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized

    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        Sanitize HTML content (basic - for display only)

        Args:
            value: HTML string

        Returns:
            Sanitized HTML (tags escaped)
        """
        sanitized = InputSanitizer.sanitize_string(value)

        # Escape HTML special characters
        html_escapes = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }

        for char, escape in html_escapes.items():
            sanitized = sanitized.replace(char, escape)

        return sanitized


# === Legal Content Validators ===

class LegalContentValidator:
    """Validators for legal content and regulatory data"""

    # Canadian legal citation patterns
    STATUTE_CITATION_PATTERN = r'[RS]\.?[SC]\.?\s*\d{4}[^.]*'
    REGULATION_CITATION_PATTERN = r'[SC]\.?O\.?R\.?[/\s]*\d{2,4}[-/]\d+'
    CASE_CITATION_PATTERN = r'\d{4}\s+[A-Z]{2,4}\s+\d+'

    # Jurisdiction patterns
    VALID_JURISDICTIONS = {
        'federal', 'alberta', 'british_columbia', 'manitoba',
        'new_brunswick', 'newfoundland_labrador', 'northwest_territories',
        'nova_scotia', 'nunavut', 'ontario', 'prince_edward_island',
        'quebec', 'saskatchewan', 'yukon'
    }

    # Document types
    VALID_DOCUMENT_TYPES = {
        'act', 'regulation', 'policy', 'guideline',
        'directive', 'order', 'bylaw', 'treaty'
    }

    @staticmethod
    def validate_citation(citation: str) -> ValidationResult:
        """
        Validate legal citation format

        Args:
            citation: Citation string

        Returns:
            ValidationResult
        """
        errors = []

        if not citation or len(citation.strip()) == 0:
            errors.append(ValidationError(
                field='citation',
                message='Citation cannot be empty',
                code='EMPTY_CITATION'
            ))
            return ValidationResult(valid=False, errors=errors)

        # Check if matches any valid citation pattern
        patterns = [
            LegalContentValidator.STATUTE_CITATION_PATTERN,
            LegalContentValidator.REGULATION_CITATION_PATTERN,
            LegalContentValidator.CASE_CITATION_PATTERN
        ]

        matches_pattern = False
        for pattern in patterns:
            if re.search(pattern, citation, re.IGNORECASE):
                matches_pattern = True
                break

        if not matches_pattern:
            errors.append(ValidationError(
                field='citation',
                message='Citation does not match recognized legal format',
                value=citation,
                code='INVALID_CITATION_FORMAT'
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    @staticmethod
    def validate_jurisdiction(jurisdiction: str) -> ValidationResult:
        """
        Validate jurisdiction code

        Args:
            jurisdiction: Jurisdiction identifier

        Returns:
            ValidationResult
        """
        errors = []

        if not jurisdiction:
            errors.append(ValidationError(
                field='jurisdiction',
                message='Jurisdiction is required',
                code='MISSING_JURISDICTION'
            ))
        elif jurisdiction.lower() not in LegalContentValidator.VALID_JURISDICTIONS:
            errors.append(ValidationError(
                field='jurisdiction',
                message=f'Invalid jurisdiction: {jurisdiction}',
                value=jurisdiction,
                code='INVALID_JURISDICTION'
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    @staticmethod
    def validate_document_type(doc_type: str) -> ValidationResult:
        """
        Validate document type

        Args:
            doc_type: Document type

        Returns:
            ValidationResult
        """
        errors = []

        if not doc_type:
            errors.append(ValidationError(
                field='document_type',
                message='Document type is required',
                code='MISSING_DOCUMENT_TYPE'
            ))
        elif doc_type.lower() not in LegalContentValidator.VALID_DOCUMENT_TYPES:
            errors.append(ValidationError(
                field='document_type',
                message=f'Invalid document type: {doc_type}',
                value=doc_type,
                code='INVALID_DOCUMENT_TYPE'
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    @staticmethod
    def validate_effective_date(date_str: str) -> ValidationResult:
        """
        Validate effective date

        Args:
            date_str: Date string (YYYY-MM-DD format)

        Returns:
            ValidationResult
        """
        errors = []

        if not date_str:
            # Optional field
            return ValidationResult(valid=True, errors=[])

        # Try to parse date
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Check if date is reasonable (not too far in past or future)
            if parsed_date.year < 1867:  # Before Canadian Confederation
                errors.append(ValidationError(
                    field='effective_date',
                    message='Date is before Canadian Confederation (1867)',
                    value=date_str,
                    code='DATE_TOO_OLD'
                ))

            if parsed_date > date.today():
                # Future dates are allowed for upcoming legislation
                pass

        except ValueError:
            errors.append(ValidationError(
                field='effective_date',
                message='Invalid date format. Use YYYY-MM-DD',
                value=date_str,
                code='INVALID_DATE_FORMAT'
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    @staticmethod
    def validate_section_number(section: str) -> ValidationResult:
        """
        Validate section number format

        Args:
            section: Section number (e.g., "7", "7(1)", "7.1")

        Returns:
            ValidationResult
        """
        errors = []

        if not section:
            # Optional field
            return ValidationResult(valid=True, errors=[])

        # Valid patterns: "7", "7(1)", "7.1", "7(1)(a)"
        pattern = r'^\d+(\.\d+)?(\([0-9a-z]+\))*$'

        if not re.match(pattern, section, re.IGNORECASE):
            errors.append(ValidationError(
                field='section_number',
                message='Invalid section number format',
                value=section,
                code='INVALID_SECTION_FORMAT'
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )


# === Document Validation ===

class DocumentValidator:
    """Validator for regulatory documents"""

    @staticmethod
    def validate_document(
        title: str,
        content: str,
        jurisdiction: str,
        document_type: str,
        citation: Optional[str] = None,
        effective_date: Optional[str] = None,
        section_number: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate complete document

        Args:
            title: Document title
            content: Document content
            jurisdiction: Jurisdiction code
            document_type: Type of document
            citation: Optional legal citation
            effective_date: Optional effective date
            section_number: Optional section number

        Returns:
            ValidationResult with all errors
        """
        errors = []
        warnings = []

        # Validate title
        if not title or len(title.strip()) == 0:
            errors.append(ValidationError(
                field='title',
                message='Title is required',
                code='MISSING_TITLE'
            ))
        elif len(title) < 5:
            errors.append(ValidationError(
                field='title',
                message='Title is too short (minimum 5 characters)',
                value=title,
                code='TITLE_TOO_SHORT'
            ))
        elif len(title) > 500:
            errors.append(ValidationError(
                field='title',
                message='Title is too long (maximum 500 characters)',
                code='TITLE_TOO_LONG'
            ))

        # Validate content
        if not content or len(content.strip()) == 0:
            errors.append(ValidationError(
                field='content',
                message='Content is required',
                code='MISSING_CONTENT'
            ))
        elif len(content) < 10:
            errors.append(ValidationError(
                field='content',
                message='Content is too short (minimum 10 characters)',
                code='CONTENT_TOO_SHORT'
            ))
        elif len(content) > 1000000:
            errors.append(ValidationError(
                field='content',
                message='Content exceeds maximum length (1MB)',
                code='CONTENT_TOO_LONG'
            ))

        # Validate jurisdiction
        result = LegalContentValidator.validate_jurisdiction(jurisdiction)
        errors.extend(result.errors)

        # Validate document type
        result = LegalContentValidator.validate_document_type(document_type)
        errors.extend(result.errors)

        # Validate optional fields
        if citation:
            result = LegalContentValidator.validate_citation(citation)
            if result.has_errors:
                # Citation format errors are warnings, not hard errors
                warnings.extend([e.message for e in result.errors])

        if effective_date:
            result = LegalContentValidator.validate_effective_date(effective_date)
            errors.extend(result.errors)

        if section_number:
            result = LegalContentValidator.validate_section_number(section_number)
            errors.extend(result.errors)

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


# === Query Validation ===

class QueryValidator:
    """Validator for search queries and user inputs"""

    @staticmethod
    def validate_search_query(
        query: str,
        min_length: int = 2,
        max_length: int = 500
    ) -> ValidationResult:
        """
        Validate search query

        Args:
            query: Search query string
            min_length: Minimum query length
            max_length: Maximum query length

        Returns:
            ValidationResult
        """
        errors = []

        if not query or len(query.strip()) == 0:
            errors.append(ValidationError(
                field='query',
                message='Search query cannot be empty',
                code='EMPTY_QUERY'
            ))
            return ValidationResult(valid=False, errors=errors)

        # Check length
        query_clean = query.strip()

        if len(query_clean) < min_length:
            errors.append(ValidationError(
                field='query',
                message=f'Query too short (minimum {min_length} characters)',
                value=query,
                code='QUERY_TOO_SHORT'
            ))

        if len(query_clean) > max_length:
            errors.append(ValidationError(
                field='query',
                message=f'Query too long (maximum {max_length} characters)',
                code='QUERY_TOO_LONG'
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )

    @staticmethod
    def validate_filters(filters: Dict[str, Any]) -> ValidationResult:
        """
        Validate search filters

        Args:
            filters: Filter dictionary

        Returns:
            ValidationResult
        """
        errors = []
        warnings = []

        if not isinstance(filters, dict):
            errors.append(ValidationError(
                field='filters',
                message='Filters must be a dictionary',
                code='INVALID_FILTERS_TYPE'
            ))
            return ValidationResult(valid=False, errors=errors)

        # Validate specific filter fields
        if 'jurisdiction' in filters:
            result = LegalContentValidator.validate_jurisdiction(filters['jurisdiction'])
            errors.extend(result.errors)

        if 'document_type' in filters:
            result = LegalContentValidator.validate_document_type(filters['document_type'])
            errors.extend(result.errors)

        if 'effective_date' in filters:
            result = LegalContentValidator.validate_effective_date(filters['effective_date'])
            errors.extend(result.errors)

        # Check for unknown filters
        known_filters = {
            'jurisdiction', 'document_type', 'authority',
            'program', 'effective_date', 'tags'
        }

        for key in filters.keys():
            if key not in known_filters:
                warnings.append(f"Unknown filter '{key}' will be ignored")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


# === Utility Functions ===

def validate_email(email: str) -> bool:
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_uuid(uuid_str: str) -> bool:
    """Validate UUID format"""
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str, re.IGNORECASE))


# === Example Usage ===

if __name__ == "__main__":
    # Example 1: Validate document
    validator = DocumentValidator()
    result = validator.validate_document(
        title="Employment Insurance Act - Section 7",
        content="Benefits are payable to persons who have lost employment...",
        jurisdiction="federal",
        document_type="act",
        citation="S.C. 1996, c. 23, s. 7",
        effective_date="1996-06-30",
        section_number="7"
    )

    print(f"Document valid: {result.valid}")
    if result.has_errors:
        for error in result.errors:
            print(f"  Error: {error.message}")

    # Example 2: Validate search query
    query_result = QueryValidator.validate_search_query(
        "employment insurance eligibility"
    )
    print(f"\nQuery valid: {query_result.valid}")

    # Example 3: Sanitize input
    sanitized = InputSanitizer.sanitize_query(
        "  Can <script>alert('test')</script> refugees work?  "
    )
    print(f"\nSanitized query: '{sanitized}'")
