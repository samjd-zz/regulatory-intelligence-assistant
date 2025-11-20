"""
Pydantic schemas for compliance checking rules and validations.
Defines data structures for compliance requirements, checks, and reports.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Literal
from datetime import datetime
from enum import Enum
import uuid


class SeverityLevel(str, Enum):
    """Severity levels for compliance issues."""
    CRITICAL = "critical"  # Must be fixed to proceed
    HIGH = "high"  # Should be fixed, impacts compliance
    MEDIUM = "medium"  # Recommended fix, minor impact
    LOW = "low"  # Optional improvement


class RequirementType(str, Enum):
    """Types of compliance requirements."""
    MANDATORY_FIELD = "mandatory_field"  # Required form field
    ELIGIBILITY_CRITERIA = "eligibility_criteria"  # Eligibility check
    DOCUMENT_REQUIREMENT = "document_requirement"  # Required document
    DATA_VALIDATION = "data_validation"  # Data format/value validation
    CONDITIONAL_REQUIREMENT = "conditional_requirement"  # Depends on other fields


class ComplianceRule(BaseModel):
    """Definition of a compliance rule extracted from regulations."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Detailed rule description")
    requirement_type: RequirementType
    severity: SeverityLevel
    regulation_id: Optional[str] = Field(None, description="Source regulation UUID")
    section_reference: Optional[str] = Field(None, description="Specific section (e.g., 'Section 7(1)(a)')")
    field_name: Optional[str] = Field(None, description="Form field this rule applies to")
    validation_logic: Dict[str, Any] = Field(default_factory=dict, description="Rule logic as JSON")
    condition: Optional[Dict[str, Any]] = Field(None, description="When this rule applies")
    error_message: str = Field(..., description="Error message to show user")
    suggestion: Optional[str] = Field(None, description="Helpful suggestion to fix the issue")
    
    class Config:
        use_enum_values = True


class ComplianceRequirement(BaseModel):
    """A specific requirement for a program/workflow."""
    rule: ComplianceRule
    applies: bool = Field(True, description="Whether this requirement applies in current context")
    reason: Optional[str] = Field(None, description="Why this requirement applies/doesn't apply")


class ValidationResult(BaseModel):
    """Result of validating a single field or requirement."""
    field_name: str
    rule_id: str
    passed: bool
    severity: SeverityLevel
    error_message: Optional[str] = None
    suggestion: Optional[str] = None
    regulation_reference: Optional[str] = None


class ComplianceIssue(BaseModel):
    """A compliance issue found during checking."""
    issue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    field_name: Optional[str] = None
    requirement: str = Field(..., description="What requirement was not met")
    description: str = Field(..., description="Detailed issue description")
    severity: SeverityLevel
    regulation_citation: Optional[str] = Field(None, description="Full legal citation")
    regulation_id: Optional[str] = None
    section_id: Optional[str] = None
    suggestion: Optional[str] = Field(None, description="How to fix this issue")
    current_value: Optional[Any] = Field(None, description="Current field value")
    expected_value: Optional[Any] = Field(None, description="Expected value or format")


class ComplianceCheckRequest(BaseModel):
    """Request to check compliance for a form submission."""
    program_id: str = Field(..., description="Program/service identifier")
    workflow_type: str = Field(..., description="Type of workflow (e.g., 'ei_application')")
    form_data: Dict[str, Any] = Field(..., description="Form field data to validate")
    user_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="User context (role, location, etc.)")
    check_optional: bool = Field(False, description="Also check optional/recommended fields")


class ComplianceReport(BaseModel):
    """Complete compliance checking report."""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    program_id: str
    workflow_type: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    compliant: bool = Field(..., description="Overall compliance status")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment (0-1)")
    issues: List[ComplianceIssue] = Field(default_factory=list)
    passed_requirements: int = Field(0, description="Number of requirements passed")
    total_requirements: int = Field(0, description="Total requirements checked")
    critical_issues: int = Field(0, description="Number of critical issues")
    high_issues: int = Field(0, description="Number of high severity issues")
    recommendations: List[str] = Field(default_factory=list, description="General recommendations")
    next_steps: List[str] = Field(default_factory=list, description="What to do next")
    
    @validator('compliant')
    def validate_compliance(cls, v, values):
        """Compliance is false if there are any critical issues."""
        if 'critical_issues' in values and values['critical_issues'] > 0:
            return False
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FieldValidationRequest(BaseModel):
    """Request to validate a specific field."""
    program_id: str
    field_name: str
    field_value: Any
    form_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Other form fields for context")


class FieldValidationResponse(BaseModel):
    """Response for field validation."""
    field_name: str
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class RequirementExtractionRequest(BaseModel):
    """Request to extract requirements from regulations."""
    regulation_id: Optional[str] = None
    program_id: Optional[str] = None
    section_ids: Optional[List[str]] = None


class ExtractedRequirement(BaseModel):
    """A requirement extracted from regulatory text."""
    requirement_text: str
    requirement_type: RequirementType
    severity: SeverityLevel
    source_regulation_id: str
    source_section_id: Optional[str] = None
    citation: str
    extracted_conditions: Optional[Dict[str, Any]] = None
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence")


class ComplianceRuleSet(BaseModel):
    """A set of compliance rules for a program."""
    program_id: str
    program_name: str
    jurisdiction: str
    rules: List[ComplianceRule]
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field("1.0", description="Rule set version")


class ComplianceMetrics(BaseModel):
    """Metrics about compliance checking performance."""
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    average_confidence: float = 0.0
    common_issues: List[Dict[str, Any]] = Field(default_factory=list)
    accuracy_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
