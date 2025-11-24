"""
Unit tests for the compliance checking engine.
Tests rule extraction, validation logic, and compliance reporting.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.orm import Session

from services.compliance_checker import (
    ComplianceChecker, RequirementExtractor, RuleEngine
)
from schemas.compliance_rules import (
    ComplianceCheckRequest, ComplianceRule, ComplianceIssue,
    FieldValidationRequest, RequirementExtractionRequest,
    ExtractedRequirement, SeverityLevel, RequirementType
)
from models import Regulation, Section


class TestRuleEngine:
    """Test the rule validation engine."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()
    
    def test_validate_required_field_present(self):
        """Test validation passes when required field is present."""
        rule = ComplianceRule(
            name="Test Rule",
            description="Test",
            requirement_type=RequirementType.MANDATORY_FIELD,
            severity=SeverityLevel.CRITICAL,
            field_name="sin",
            validation_logic={"required": True},
            error_message="SIN required"
        )
        
        form_data = {"sin": "123-456-789"}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        
        assert valid is True
        assert error is None
    
    def test_validate_required_field_missing(self):
        """Test validation fails when required field is missing."""
        rule = ComplianceRule(
            name="Test Rule",
            description="Test",
            requirement_type=RequirementType.MANDATORY_FIELD,
            severity=SeverityLevel.CRITICAL,
            field_name="sin",
            validation_logic={"required": True},
            error_message="SIN required"
        )
        
        form_data = {}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        
        assert valid is False
        assert error == "This field is required"
    
    def test_validate_pattern_match(self):
        """Test pattern validation with matching value."""
        rule = ComplianceRule(
            name="SIN Format",
            description="Validate SIN format",
            requirement_type=RequirementType.DATA_VALIDATION,
            severity=SeverityLevel.HIGH,
            field_name="sin",
            validation_logic={"pattern": r"^\d{3}-\d{3}-\d{3}$"},
            error_message="Invalid SIN format"
        )
        
        form_data = {"sin": "123-456-789"}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        
        assert valid is True
        assert error is None
    
    def test_validate_pattern_no_match(self):
        """Test pattern validation with non-matching value."""
        rule = ComplianceRule(
            name="SIN Format",
            description="Validate SIN format",
            requirement_type=RequirementType.DATA_VALIDATION,
            severity=SeverityLevel.HIGH,
            field_name="sin",
            validation_logic={"pattern": r"^\d{3}-\d{3}-\d{3}$"},
            error_message="Invalid SIN format"
        )
        
        form_data = {"sin": "123456789"}  # Wrong format
        valid, error = self.engine.validate_rule(rule, form_data, {})
        
        assert valid is False
        assert error == "Invalid format"
    
    def test_validate_min_length(self):
        """Test minimum length validation."""
        rule = ComplianceRule(
            name="Name Length",
            description="Name must be at least 2 characters",
            requirement_type=RequirementType.DATA_VALIDATION,
            severity=SeverityLevel.MEDIUM,
            field_name="name",
            validation_logic={"min_length": 2},
            error_message="Name too short"
        )
        
        # Test valid
        form_data = {"name": "John"}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is True
        
        # Test invalid
        form_data = {"name": "J"}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is False
        assert "at least 2 characters" in error
    
    def test_validate_range(self):
        """Test numeric range validation."""
        rule = ComplianceRule(
            name="Age Range",
            description="Age must be 18-65",
            requirement_type=RequirementType.DATA_VALIDATION,
            severity=SeverityLevel.HIGH,
            field_name="age",
            validation_logic={"range": {"min": 18, "max": 65}},
            error_message="Age out of range"
        )
        
        # Test valid
        form_data = {"age": 25}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is True
        
        # Test below min
        form_data = {"age": 15}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is False
        assert "at least 18" in error
        
        # Test above max
        form_data = {"age": 70}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is False
        assert "not exceed 65" in error
    
    def test_validate_in_list(self):
        """Test value in list validation."""
        rule = ComplianceRule(
            name="Status",
            description="Valid status values",
            requirement_type=RequirementType.DATA_VALIDATION,
            severity=SeverityLevel.HIGH,
            field_name="status",
            validation_logic={"in_list": ["citizen", "permanent_resident", "temporary"]},
            error_message="Invalid status"
        )
        
        # Test valid
        form_data = {"status": "citizen"}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is True
        
        # Test invalid
        form_data = {"status": "tourist"}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is False
        assert "Must be one of" in error
    
    def test_conditional_rule_applies(self):
        """Test conditional rule when condition is true."""
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
        
        # Condition applies - should validate
        form_data = {"residency_status": "temporary"}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is False  # work_permit is missing
        
        # Condition doesn't apply - should pass
        form_data = {"residency_status": "citizen"}
        valid, error = self.engine.validate_rule(rule, form_data, {})
        assert valid is True


class TestRequirementExtractor:
    """Test requirement extraction from regulatory text."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = Mock(spec=Session)
        self.graph_service = Mock()
        self.extractor = RequirementExtractor(self.db, self.graph_service)
    
    def test_extract_mandatory_requirement(self):
        """Test extraction of mandatory requirements."""
        text = "Applicants must provide proof of residency."
        reqs = self.extractor._extract_from_text(text, "reg-1", "sec-1", "Section 5")
        
        assert len(reqs) > 0
        assert any(req.requirement_type == RequirementType.MANDATORY_FIELD for req in reqs)
        assert any(req.severity == SeverityLevel.CRITICAL for req in reqs)
    
    def test_extract_eligibility_requirement(self):
        """Test extraction of eligibility requirements."""
        text = "Persons are eligible if they have worked for 600 hours."
        reqs = self.extractor._extract_from_text(text, "reg-1", "sec-1", "Section 7")
        
        assert len(reqs) > 0
        assert any(req.requirement_type == RequirementType.ELIGIBILITY_CRITERIA for req in reqs)
    
    def test_extract_conditional_requirement(self):
        """Test extraction of conditional requirements."""
        text = "If the applicant is under 18, then parental consent must be provided."
        reqs = self.extractor._extract_from_text(text, "reg-1", "sec-1", "Section 10")
        
        assert len(reqs) > 0
        req = reqs[0]
        assert req.requirement_type == RequirementType.CONDITIONAL_REQUIREMENT
        assert req.extracted_conditions is not None
        assert req.extracted_conditions.get('has_condition') is True
    
    def test_extract_prohibited_requirement(self):
        """Test extraction of prohibited actions."""
        text = "Applicants must not submit false information."
        reqs = self.extractor._extract_from_text(text, "reg-1", "sec-1", "Section 12")
        
        assert len(reqs) > 0
        assert any(req.requirement_type == RequirementType.DATA_VALIDATION for req in reqs)
    
    def test_split_sentences(self):
        """Test sentence splitting."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = self.extractor._split_sentences(text)
        
        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]


class TestComplianceChecker:
    """Test the main compliance checker."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_graph_service(self):
        """Create mock graph service."""
        service = Mock()
        service.get_program_regulations = AsyncMock(return_value=[])
        return service
    
    @pytest.fixture
    def checker(self, mock_db, mock_graph_service):
        """Create compliance checker instance."""
        return ComplianceChecker(mock_db, mock_graph_service)
    
    @pytest.mark.asyncio
    async def test_check_compliance_all_pass(self, checker):
        """Test compliance check when all requirements pass."""
        request = ComplianceCheckRequest(
            program_id="employment-insurance",
            workflow_type="ei_application",
            form_data={
                "sin": "123-456-789",
                "employment_status": "employed",
                "residency_status": "citizen"
            }
        )
        
        # Mock rule retrieval
        with patch.object(checker, '_get_rules_for_program', new_callable=AsyncMock) as mock_rules:
            mock_rules.return_value = [
                ComplianceRule(
                    name="SIN Required",
                    description="SIN is required",
                    requirement_type=RequirementType.MANDATORY_FIELD,
                    severity=SeverityLevel.CRITICAL,
                    field_name="sin",
                    validation_logic={"required": True},
                    error_message="SIN required"
                )
            ]
            
            report = await checker.check_compliance(request)
            
            assert report.compliant is True
            assert report.passed_requirements == 1
            assert len(report.issues) == 0
            assert report.critical_issues == 0
    
    @pytest.mark.asyncio
    async def test_check_compliance_with_issues(self, checker):
        """Test compliance check with violations."""
        request = ComplianceCheckRequest(
            program_id="employment-insurance",
            workflow_type="ei_application",
            form_data={
                "employment_status": "employed",
                "residency_status": "citizen"
                # Missing SIN
            }
        )
        
        with patch.object(checker, '_get_rules_for_program', new_callable=AsyncMock) as mock_rules:
            mock_rules.return_value = [
                ComplianceRule(
                    name="SIN Required",
                    description="SIN is required",
                    requirement_type=RequirementType.MANDATORY_FIELD,
                    severity=SeverityLevel.CRITICAL,
                    field_name="sin",
                    validation_logic={"required": True},
                    error_message="SIN required"
                )
            ]
            
            report = await checker.check_compliance(request)
            
            assert report.compliant is False
            assert len(report.issues) == 1
            assert report.critical_issues == 1
            assert report.issues[0].field_name == "sin"
            assert report.issues[0].severity == SeverityLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_validate_field_valid(self, checker):
        """Test field validation with valid value."""
        request = FieldValidationRequest(
            program_id="employment-insurance",
            field_name="sin",
            field_value="123-456-789"
        )
        
        with patch.object(checker, '_get_rules_for_program', new_callable=AsyncMock) as mock_rules:
            mock_rules.return_value = [
                ComplianceRule(
                    name="SIN Format",
                    description="Validate SIN",
                    requirement_type=RequirementType.DATA_VALIDATION,
                    severity=SeverityLevel.CRITICAL,
                    field_name="sin",
                    validation_logic={
                        "required": True,
                        "pattern": r"^\d{3}-\d{3}-\d{3}$"
                    },
                    error_message="Invalid SIN"
                )
            ]
            
            result = await checker.validate_field(request)
            
            assert result.valid is True
            assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_validate_field_invalid(self, checker):
        """Test field validation with invalid value."""
        request = FieldValidationRequest(
            program_id="employment-insurance",
            field_name="sin",
            field_value="123456789"  # Wrong format
        )
        
        with patch.object(checker, '_get_rules_for_program', new_callable=AsyncMock) as mock_rules:
            mock_rules.return_value = [
                ComplianceRule(
                    name="SIN Format",
                    description="Validate SIN",
                    requirement_type=RequirementType.DATA_VALIDATION,
                    severity=SeverityLevel.CRITICAL,
                    field_name="sin",
                    validation_logic={"pattern": r"^\d{3}-\d{3}-\d{3}$"},
                    error_message="Invalid SIN format"
                )
            ]
            
            result = await checker.validate_field(request)
            
            assert result.valid is False
            assert len(result.errors) > 0
    
    def test_infer_field_name(self, checker):
        """Test field name inference from requirement text."""
        # Test SIN
        field = checker._infer_field_name("Applicant must provide Social Insurance Number")
        assert field == "sin"
        
        # Test work permit
        field = checker._infer_field_name("Valid work permit is required")
        assert field == "work_permit"
        
        # Test address
        field = checker._infer_field_name("Proof of address must be submitted")
        assert field == "address"
        
        # Test unknown
        field = checker._infer_field_name("Some unknown requirement")
        assert field is None
    
    def test_calculate_confidence(self, checker):
        """Test confidence calculation."""
        # High confidence - all requirements passed
        confidence = checker._calculate_confidence(10, 10, 10)
        assert confidence >= 0.9
        
        # Medium confidence - some requirements passed
        confidence = checker._calculate_confidence(10, 5, 8)
        assert 0.5 <= confidence < 0.9
        
        # Low confidence - few requirements
        confidence = checker._calculate_confidence(0, 0, 0)
        assert confidence == 0.5
    
    def test_generate_recommendations(self, checker):
        """Test recommendation generation."""
        issues = [
            ComplianceIssue(
                requirement="SIN Required",
                description="SIN is missing",
                severity=SeverityLevel.CRITICAL,
                field_name="sin"
            ),
            ComplianceIssue(
                requirement="Address Required",
                description="Address is missing",
                severity=SeverityLevel.HIGH,
                field_name="address"
            )
        ]
        
        recommendations = checker._generate_recommendations(issues)
        
        assert len(recommendations) > 0
        assert any("critical" in rec.lower() for rec in recommendations)
    
    def test_generate_next_steps_compliant(self, checker):
        """Test next steps when compliant."""
        next_steps = checker._generate_next_steps([], True)
        
        assert len(next_steps) > 0
        assert any("submit" in step.lower() for step in next_steps)
    
    def test_generate_next_steps_non_compliant(self, checker):
        """Test next steps when not compliant."""
        issues = [
            ComplianceIssue(
                requirement="SIN Required",
                description="SIN is missing",
                severity=SeverityLevel.CRITICAL,
                field_name="sin",
                suggestion="Enter your 9-digit SIN"
            )
        ]
        
        next_steps = checker._generate_next_steps(issues, False)
        
        assert len(next_steps) > 0
        assert any("sin" in step.lower() for step in next_steps)
    
    def test_get_essential_rules_ei(self, checker):
        """Test essential rules for employment insurance."""
        rules = checker._get_essential_rules("employment-insurance", "ei_application")
        
        assert len(rules) > 0
        assert any(rule.field_name == "sin" for rule in rules)
        assert any(rule.field_name == "work_permit" for rule in rules)
    
    def test_format_citation(self, checker):
        """Test citation formatting."""
        rule = ComplianceRule(
            name="Test",
            description="Test",
            requirement_type=RequirementType.MANDATORY_FIELD,
            severity=SeverityLevel.CRITICAL,
            section_reference="Section 7(1)(a)",
            error_message="Test"
        )
        
        citation = checker._format_citation(rule)
        assert citation == "Section 7(1)(a)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
