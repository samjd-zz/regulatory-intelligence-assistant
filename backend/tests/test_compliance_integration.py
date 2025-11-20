"""
Integration test for compliance checking engine.
Tests the full compliance checking workflow without pytest dependency.
"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from schemas.compliance_rules import (
    ComplianceCheckRequest, ComplianceRule, FieldValidationRequest,
    SeverityLevel, RequirementType
)
from services.compliance_checker import RuleEngine, ComplianceChecker
from unittest.mock import Mock, AsyncMock


def test_rule_engine():
    """Test the rule validation engine."""
    print("\n=== Testing RuleEngine ===")
    engine = RuleEngine()
    
    # Test 1: Required field validation
    print("\n1. Testing required field validation...")
    rule = ComplianceRule(
        name="SIN Required",
        description="Social Insurance Number is mandatory",
        requirement_type=RequirementType.MANDATORY_FIELD,
        severity=SeverityLevel.CRITICAL,
        field_name="sin",
        validation_logic={"required": True},
        error_message="SIN is required"
    )
    
    # Should pass
    valid, error = engine.validate_rule(rule, {"sin": "123-456-789"}, {})
    assert valid is True, "Required field validation failed when field present"
    print("✓ Pass: Required field present")
    
    # Should fail
    valid, error = engine.validate_rule(rule, {}, {})
    assert valid is False, "Required field validation passed when field missing"
    assert error == "This field is required"
    print("✓ Pass: Required field missing detected")
    
    # Test 2: Pattern validation
    print("\n2. Testing pattern validation...")
    rule = ComplianceRule(
        name="SIN Format",
        description="Validate SIN format",
        requirement_type=RequirementType.DATA_VALIDATION,
        severity=SeverityLevel.HIGH,
        field_name="sin",
        validation_logic={"pattern": r"^\d{3}-\d{3}-\d{3}$"},
        error_message="Invalid SIN format"
    )
    
    # Should pass
    valid, error = engine.validate_rule(rule, {"sin": "123-456-789"}, {})
    assert valid is True, "Pattern validation failed on valid format"
    print("✓ Pass: Valid pattern accepted")
    
    # Should fail
    valid, error = engine.validate_rule(rule, {"sin": "123456789"}, {})
    assert valid is False, "Pattern validation passed on invalid format"
    print("✓ Pass: Invalid pattern rejected")
    
    # Test 3: Range validation
    print("\n3. Testing range validation...")
    rule = ComplianceRule(
        name="Age Range",
        description="Age must be 18-65",
        requirement_type=RequirementType.DATA_VALIDATION,
        severity=SeverityLevel.HIGH,
        field_name="age",
        validation_logic={"range": {"min": 18, "max": 65}},
        error_message="Age out of range"
    )
    
    valid, error = engine.validate_rule(rule, {"age": 25}, {})
    assert valid is True, "Range validation failed on valid value"
    print("✓ Pass: Valid age accepted")
    
    valid, error = engine.validate_rule(rule, {"age": 15}, {})
    assert valid is False, "Range validation passed on too low value"
    print("✓ Pass: Below minimum rejected")
    
    # Test 4: Conditional validation
    print("\n4. Testing conditional validation...")
    rule = ComplianceRule(
        name="Work Permit Required",
        description="Temporary residents need work permit",
        requirement_type=RequirementType.CONDITIONAL_REQUIREMENT,
        severity=SeverityLevel.CRITICAL,
        field_name="work_permit",
        validation_logic={"required": True},
        condition={
            "type": "field_equals",
            "field": "residency_status",
            "value": "temporary"
        },
        error_message="Work permit required"
    )
    
    # Condition applies - should fail (no work_permit)
    valid, error = engine.validate_rule(rule, {"residency_status": "temporary"}, {})
    assert valid is False, "Conditional rule passed when should validate"
    print("✓ Pass: Conditional rule applies and validates")
    
    # Condition doesn't apply - should pass
    valid, error = engine.validate_rule(rule, {"residency_status": "citizen"}, {})
    assert valid is True, "Conditional rule failed when shouldn't apply"
    print("✓ Pass: Conditional rule skipped when condition false")
    
    print("\n✅ All RuleEngine tests passed!")
    return True


async def test_compliance_checker():
    """Test the compliance checker."""
    print("\n=== Testing ComplianceChecker ===")
    
    # Mock dependencies
    mock_db = Mock()
    mock_graph_service = Mock()
    mock_graph_service.get_program_regulations = AsyncMock(return_value=[])
    
    checker = ComplianceChecker(mock_db, mock_graph_service)
    
    # Test 1: Field name inference
    print("\n1. Testing field name inference...")
    field = checker._infer_field_name("Applicant must provide Social Insurance Number")
    assert field == "sin", f"Expected 'sin', got '{field}'"
    print("✓ Pass: SIN field inferred")
    
    field = checker._infer_field_name("Valid work permit is required")
    assert field == "work_permit", f"Expected 'work_permit', got '{field}'"
    print("✓ Pass: Work permit field inferred")
    
    # Test 2: Citation formatting
    print("\n2. Testing citation formatting...")
    rule = ComplianceRule(
        name="Test",
        description="Test",
        requirement_type=RequirementType.MANDATORY_FIELD,
        severity=SeverityLevel.CRITICAL,
        section_reference="Section 7(1)(a)",
        error_message="Test"
    )
    citation = checker._format_citation(rule)
