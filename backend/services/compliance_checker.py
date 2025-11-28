"""
Compliance Checking Engine for validating form submissions against regulations.
Extracts requirements from regulations and validates data for compliance.
"""
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
import re
from sqlalchemy.orm import Session
from sqlalchemy import and_

from schemas.compliance_rules import (
    ComplianceRule, ComplianceIssue, ComplianceReport,
    ComplianceCheckRequest, FieldValidationRequest, FieldValidationResponse,
    RequirementExtractionRequest, ExtractedRequirement, ComplianceRuleSet,
    SeverityLevel, RequirementType
)
from models import Regulation, Section
from services.graph_service import GraphService


class RequirementExtractor:
    """Extract compliance requirements from regulatory text."""
    
    def __init__(self, db: Session, graph_service: GraphService):
        self.db = db
        self.graph_service = graph_service
        
        # Patterns for extracting requirements from legal text
        self.requirement_patterns = {
            'mandatory': [
                r'must\s+(?:provide|submit|include|have|be)',
                r'shall\s+(?:provide|submit|include|have|be)',
                r'is\s+required\s+to',
                r'required\s+to\s+(?:provide|submit|include)',
            ],
            'prohibited': [
                r'must\s+not',
                r'shall\s+not',
                r'prohibited\s+from',
                r'may\s+not',
            ],
            'conditional': [
                r'if\s+.*\s+then',
                r'unless\s+.*\s+must',
                r'where\s+.*\s+shall',
            ],
            'eligibility': [
                r'eligible\s+(?:if|when|where)',
                r'qualifies\s+(?:if|when|where)',
                r'entitled\s+to\s+.*\s+if',
            ]
        }
    
    async def extract_requirements(
        self, 
        request: RequirementExtractionRequest
    ) -> List[ExtractedRequirement]:
        """Extract requirements from regulations."""
        requirements = []
        
        # Get relevant sections from database
        query = self.db.query(Section)
        
        if request.regulation_id:
            query = query.filter(Section.regulation_id == request.regulation_id)
        
        if request.section_ids:
            query = query.filter(Section.id.in_(request.section_ids))
        
        sections = query.all()
        
        # Note: Graph service integration for program-specific regulations 
        # can be added when get_program_regulations method is implemented
        
        # Extract requirements from each section
        for section in sections:
            section_requirements = self._extract_from_text(
                section.content,
                section.regulation_id,
                section.id,
                f"{section.section_number}"
            )
            requirements.extend(section_requirements)
        
        return requirements
    
    def _extract_from_text(
        self,
        text: str,
        regulation_id: str,
        section_id: Optional[str],
        citation: str
    ) -> List[ExtractedRequirement]:
        """Extract requirements from regulatory text."""
        requirements = []
        sentences = self._split_sentences(text)
        
        # Check patterns in priority order: conditional > eligibility > prohibited > mandatory
        # This ensures complex patterns are matched before simpler ones
        priority_order = ['conditional', 'eligibility', 'prohibited', 'mandatory']
        
        for sentence in sentences:
            matched = False
            # Check each pattern type in priority order
            for req_type in priority_order:
                if matched:
                    break
                patterns = self.requirement_patterns.get(req_type, [])
                for pattern in patterns:
                    if re.search(pattern, sentence, re.IGNORECASE):
                        requirement = self._parse_requirement(
                            sentence,
                            req_type,
                            regulation_id,
                            section_id,
                            citation
                        )
                        if requirement:
                            requirements.append(requirement)
                            matched = True
                        break
        
        return requirements
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting (can be improved with NLP)
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _parse_requirement(
        self,
        text: str,
        req_type: str,
        regulation_id: str,
        section_id: Optional[str],
        citation: str
    ) -> Optional[ExtractedRequirement]:
        """Parse a requirement from a sentence."""
        # Determine requirement type
        if req_type == 'mandatory':
            requirement_type = RequirementType.MANDATORY_FIELD
            severity = SeverityLevel.CRITICAL
        elif req_type == 'prohibited':
            requirement_type = RequirementType.DATA_VALIDATION
            severity = SeverityLevel.HIGH
        elif req_type == 'conditional':
            requirement_type = RequirementType.CONDITIONAL_REQUIREMENT
            severity = SeverityLevel.HIGH
        elif req_type == 'eligibility':
            requirement_type = RequirementType.ELIGIBILITY_CRITERIA
            severity = SeverityLevel.CRITICAL
        else:
            return None
        
        # Extract conditions (simplified)
        conditions = {}
        if 'if' in text.lower():
            conditions['has_condition'] = True
            conditions['condition_text'] = text
        
        return ExtractedRequirement(
            requirement_text=text,
            requirement_type=requirement_type,
            severity=severity,
            source_regulation_id=str(regulation_id),
            source_section_id=str(section_id) if section_id else None,
            citation=citation,
            extracted_conditions=conditions if conditions else None,
            confidence=0.75  # Base confidence for pattern matching
        )


class RuleEngine:
    """Rule engine for validating data against compliance rules."""
    
    def __init__(self):
        self.validation_functions = {
            'required': self._validate_required,
            'min_length': self._validate_min_length,
            'max_length': self._validate_max_length,
            'pattern': self._validate_pattern,
            'range': self._validate_range,
            'in_list': self._validate_in_list,
            'date_format': self._validate_date_format,
            'conditional': self._validate_conditional,
        }
    
    def validate_rule(
        self,
        rule: ComplianceRule,
        form_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate a single rule against form data."""
        
        # Check if rule applies based on conditions
        if rule.condition and not self._check_condition(rule.condition, form_data, context):
            return True, "Rule does not apply in this context"
        
        # Get field value
        field_value = form_data.get(rule.field_name)
        
        # Validate based on validation logic
        for validation_type, validation_params in rule.validation_logic.items():
            if validation_type in self.validation_functions:
                valid, error = self.validation_functions[validation_type](
                    field_value,
                    validation_params,
                    form_data,
                    context
                )
                if not valid:
                    return False, error
        
        return True, None
    
    def _check_condition(
        self,
        condition: Dict[str, Any],
        form_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if a conditional rule applies."""
        condition_type = condition.get('type', 'field_equals')
        
        if condition_type == 'field_equals':
            field = condition.get('field')
            value = condition.get('value')
            return form_data.get(field) == value
        
        elif condition_type == 'field_exists':
            field = condition.get('field')
            return field in form_data and form_data[field] is not None
        
        elif condition_type == 'context_equals':
            key = condition.get('key')
            value = condition.get('value')
            return context.get(key) == value
        
        return True
    
    def _validate_required(
        self,
        value: Any,
        params: Any,
        form_data: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Validate that a required field is present and not empty."""
        if params and (value is None or value == ''):
            return False, "This field is required"
        return True, None
    
    def _validate_min_length(
        self,
        value: Any,
        params: int,
        form_data: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Validate minimum length."""
        if value and len(str(value)) < params:
            return False, f"Must be at least {params} characters"
        return True, None
    
    def _validate_max_length(
        self,
        value: Any,
        params: int,
        form_data: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Validate maximum length."""
        if value and len(str(value)) > params:
            return False, f"Must not exceed {params} characters"
        return True, None
    
    def _validate_pattern(
        self,
        value: Any,
        params: str,
        form_data: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Validate against regex pattern."""
        if value and not re.match(params, str(value)):
            return False, "Invalid format"
        return True, None
    
    def _validate_range(
        self,
        value: Any,
        params: Dict[str, Any],
        form_data: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Validate numeric range."""
        if value is not None:
            try:
                num_value = float(value)
                min_val = params.get('min')
                max_val = params.get('max')
                
                if min_val is not None and num_value < min_val:
                    return False, f"Must be at least {min_val}"
                if max_val is not None and num_value > max_val:
                    return False, f"Must not exceed {max_val}"
            except (ValueError, TypeError):
                return False, "Must be a valid number"
        return True, None
    
    def _validate_in_list(
        self,
        value: Any,
        params: List[Any],
        form_data: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Validate value is in allowed list."""
        if value and value not in params:
            return False, f"Must be one of: {', '.join(map(str, params))}"
        return True, None
    
    def _validate_date_format(
        self,
        value: Any,
        params: str,
        form_data: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Validate date format."""
        if value:
            try:
                datetime.strptime(str(value), params)
            except ValueError:
                return False, f"Must be in format {params}"
        return True, None
    
    def _validate_conditional(
        self,
        value: Any,
        params: Dict[str, Any],
        form_data: Dict,
        context: Dict
    ) -> Tuple[bool, Optional[str]]:
        """Validate conditional logic."""
        condition = params.get('condition', {})
        if self._check_condition(condition, form_data, context):
            # If condition is true, apply the validation
            validation = params.get('validation', {})
            for val_type, val_params in validation.items():
                if val_type in self.validation_functions:
                    return self.validation_functions[val_type](
                        value, val_params, form_data, context
                    )
        return True, None


class ComplianceChecker:
    """Main compliance checking engine."""
    
    def __init__(self, db: Session, graph_service: GraphService):
        self.db = db
        self.graph_service = graph_service
        self.rule_engine = RuleEngine()
        self.requirement_extractor = RequirementExtractor(db, graph_service)
        
        # Cache for rule sets
        self.rule_cache: Dict[str, ComplianceRuleSet] = {}
    
    async def check_compliance(
        self,
        request: ComplianceCheckRequest
    ) -> ComplianceReport:
        """Check form data for compliance with regulations."""
        
        # Get applicable rules
        rules = await self._get_rules_for_program(
            request.program_id,
            request.workflow_type
        )
        
        # Validate each rule
        issues: List[ComplianceIssue] = []
        passed_requirements = 0
        total_requirements = 0
        
        for rule in rules:
            total_requirements += 1
            
            # Skip optional rules unless requested
            if rule.severity == SeverityLevel.LOW and not request.check_optional:
                continue
            
            # Validate rule
            valid, error = self.rule_engine.validate_rule(
                rule,
                request.form_data,
                request.user_context
            )
            
            if valid:
                passed_requirements += 1
            else:
                # Create compliance issue
                # Use the detailed error_message from rule if error is generic
                description = error
                if error in ["This field is required", "Required"]:
                    # Use the more detailed rule error message which includes requirement text
                    description = rule.error_message
                elif not error:
                    description = rule.error_message
                    
                issue = ComplianceIssue(
                    field_name=rule.field_name,
                    requirement=rule.name,
                    description=description,
                    severity=rule.severity,
                    regulation_citation=self._format_citation(rule),
                    regulation_id=rule.regulation_id,
                    section_id=None,  # Would need to track this
                    suggestion=rule.suggestion,
                    current_value=request.form_data.get(rule.field_name),
                    expected_value=rule.validation_logic.get('in_list')
                )
                issues.append(issue)
        
        # Count issues by severity
        critical_issues = sum(1 for i in issues if i.severity == SeverityLevel.CRITICAL)
        high_issues = sum(1 for i in issues if i.severity == SeverityLevel.HIGH)
        
        # Determine compliance status
        compliant = critical_issues == 0
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            total_requirements,
            passed_requirements,
            len(rules)
        )
        
        # Generate recommendations and next steps
        recommendations = self._generate_recommendations(issues)
        next_steps = self._generate_next_steps(issues, compliant)
        
        # Create report
        report = ComplianceReport(
            program_id=request.program_id,
            workflow_type=request.workflow_type,
            compliant=compliant,
            confidence=confidence,
            issues=issues,
            passed_requirements=passed_requirements,
            total_requirements=total_requirements,
            critical_issues=critical_issues,
            high_issues=high_issues,
            recommendations=recommendations,
            next_steps=next_steps
        )
        
        return report
    
    async def validate_field(
        self,
        request: FieldValidationRequest
    ) -> FieldValidationResponse:
        """Validate a single field in real-time."""
        
        # Get rules for this field
        rules = await self._get_rules_for_program(
            request.program_id,
            "field_validation"
        )
        
        field_rules = [r for r in rules if r.field_name == request.field_name]
        
        errors = []
        warnings = []
        suggestions = []
        
        # Create form data context
        form_data = {request.field_name: request.field_value}
        form_data.update(request.form_context)
        
        for rule in field_rules:
            valid, error = self.rule_engine.validate_rule(
                rule,
                form_data,
                {}
            )
            
            if not valid:
                if rule.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
                    errors.append(error or rule.error_message)
                else:
                    warnings.append(error or rule.error_message)
                
                if rule.suggestion:
                    suggestions.append(rule.suggestion)
        
        return FieldValidationResponse(
            field_name=request.field_name,
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    
    async def _get_rules_for_program(
        self,
        program_id: str,
        workflow_type: str
    ) -> List[ComplianceRule]:
        """Get compliance rules for a program."""
        
        cache_key = f"{program_id}:{workflow_type}"
        
        # Check cache
        if cache_key in self.rule_cache:
            rule_set = self.rule_cache[cache_key]
            # Check if cache is still valid (less than 1 hour old)
            if (datetime.utcnow() - rule_set.last_updated).seconds < 3600:
                return rule_set.rules
        
        # For now, use only the hardcoded essential rules since we don't have
        # a reliable way to filter extracted requirements by program yet
        # TODO: Implement program-specific regulation filtering in the graph service
        
        # Extract requirements for this program (currently extracts all - needs filtering)
        # extraction_request = RequirementExtractionRequest(
        #     program_id=program_id
        # )
        # 
        # extracted_requirements = await self.requirement_extractor.extract_requirements(
        #     extraction_request
        # )
        # 
        # # Convert to compliance rules
        # rules = [
        #     self._requirement_to_rule(req, program_id, workflow_type)
        #     for req in extracted_requirements
        # ]
        
        # Use hardcoded essential rules for each program
        rules = self._get_essential_rules(program_id, workflow_type)
        
        # Cache the rule set
        rule_set = ComplianceRuleSet(
            program_id=program_id,
            program_name=program_id,  # Would fetch from database
            jurisdiction="federal",  # Would determine from context
            rules=rules
        )
        self.rule_cache[cache_key] = rule_set
        
        return rules
    
    def _requirement_to_rule(
        self,
        requirement: ExtractedRequirement,
        program_id: str,
        workflow_type: str
    ) -> ComplianceRule:
        """Convert extracted requirement to compliance rule."""
        
        # Infer field name from requirement text (simplified)
        field_name = self._infer_field_name(requirement.requirement_text)
        
        # If we can't infer a field name, log it and use a generic one
        if field_name is None:
            print(f"⚠️ Could not infer field name from requirement: {requirement.requirement_text[:100]}")
            # Extract first few words as a fallback identifier
            import re
            words = re.findall(r'\b\w+\b', requirement.requirement_text.lower())
            field_name = '_'.join(words[:3]) if words else 'unknown_requirement'
        
        # Build validation logic
        validation_logic = {}
        if requirement.requirement_type == RequirementType.MANDATORY_FIELD:
            validation_logic['required'] = True
        elif requirement.requirement_type == RequirementType.DOCUMENT_REQUIREMENT:
            validation_logic['required'] = True
            validation_logic['pattern'] = r'.+\.(pdf|jpg|png|doc|docx)$'
        
        # Create a more descriptive error message that includes the requirement text
        error_message = requirement.requirement_text
        if len(error_message) > 200:
            error_message = error_message[:200] + "..."
        
        return ComplianceRule(
            name=f"Requirement from {requirement.citation}",
            description=requirement.requirement_text,
            requirement_type=requirement.requirement_type,
            severity=requirement.severity,
            regulation_id=requirement.source_regulation_id,
            section_reference=requirement.citation,
            field_name=field_name,
            validation_logic=validation_logic,
            error_message=error_message,
            suggestion=self._generate_suggestion(requirement)
        )
    
    def _infer_field_name(self, requirement_text: str) -> Optional[str]:
        """Infer field name from requirement text."""
        # Enhanced keyword matching with more patterns
        field_mappings = {
            # Primary identifiers
            'social insurance number': 'sin',
            'sin': 'sin',
            'work permit': 'work_permit',
            'employment': 'employment_status',
            'address': 'address',
            'proof of residency': 'residency_proof',
            'identification': 'id_document',
            'id_document': 'id_document',
            
            # Employment related
            'hours worked': 'hours_worked',
            'hours of work': 'hours_worked',
            'employment status': 'employment_status',
            'employed': 'employment_status',
            
            # Personal information
            'full name': 'full_name',
            'legal name': 'full_name',
            'name': 'full_name',
            
            # Residency
            'residency': 'residency_status',
            'resident': 'residency_status',
            'citizenship': 'residency_status',
            'citizen': 'residency_status',
        }
        
        text_lower = requirement_text.lower()
        
        # Try exact phrase matches first (longer phrases first)
        sorted_keywords = sorted(field_mappings.keys(), key=len, reverse=True)
        for keyword in sorted_keywords:
            if keyword in text_lower:
                return field_mappings[keyword]
        
        return None
    
    def _get_essential_rules(
        self,
        program_id: str,
        workflow_type: str
    ) -> List[ComplianceRule]:
        """Get essential hardcoded rules for common scenarios."""
        
        # Employment Insurance (EI)
        if 'employment' in program_id.lower() or 'ei' in program_id.lower():
            return [
                ComplianceRule(
                    name="Social Insurance Number Required",
                    description="Valid Social Insurance Number is mandatory for Employment Insurance",
                    requirement_type=RequirementType.MANDATORY_FIELD,
                    severity=SeverityLevel.CRITICAL,
                    field_name="sin",
                    validation_logic={'required': True, 'pattern': r'^\d{3}-\d{3}-\d{3}$'},
                    error_message="Social Insurance Number is required for Employment Insurance",
                    suggestion="Enter your 9-digit SIN in format XXX-XXX-XXX"
                ),
                ComplianceRule(
                    name="Work Authorization Required",
                    description="Must have valid work authorization in Canada",
                    requirement_type=RequirementType.ELIGIBILITY_CRITERIA,
                    severity=SeverityLevel.CRITICAL,
                    field_name="work_permit",
                    validation_logic={
                        'required': True,
                        'conditional': {
                            'condition': {'type': 'field_equals', 'field': 'residency_status', 'value': 'temporary'},
                            'validation': {'required': True}
                        }
                    },
                    condition={'type': 'field_equals', 'field': 'residency_status', 'value': 'temporary'},
                    error_message="Valid work permit is required for temporary residents",
                    suggestion="Upload a copy of your valid work permit"
                ),
            ]
        
        # Canada Pension Plan (CPP) / Old Age Security (OAS) / Retirement
        elif 'pension' in program_id.lower() or 'cpp' in program_id.lower() or 'oas' in program_id.lower() or 'retirement' in program_id.lower():
            return [
                ComplianceRule(
                    name="Age Requirement",
                    description="Must be at least 60 years old for CPP retirement pension",
                    requirement_type=RequirementType.ELIGIBILITY_CRITERIA,
                    severity=SeverityLevel.CRITICAL,
                    field_name="age",
                    validation_logic={'required': True, 'range': {'min': 60, 'max': 120}},
                    error_message="You must be at least 60 years old to apply for CPP retirement pension",
                    suggestion="CPP retirement pension is available from age 60, with full pension at age 65"
                ),
                ComplianceRule(
                    name="Social Insurance Number Required",
                    description="Valid Social Insurance Number is mandatory",
                    requirement_type=RequirementType.MANDATORY_FIELD,
                    severity=SeverityLevel.CRITICAL,
                    field_name="sin",
                    validation_logic={'required': True, 'pattern': r'^\d{3}-\d{3}-\d{3}$'},
                    error_message="Social Insurance Number is required",
                    suggestion="Enter your 9-digit SIN in format XXX-XXX-XXX"
                ),
                ComplianceRule(
                    name="Years of Contribution",
                    description="Must have contributed to CPP for at least one year",
                    requirement_type=RequirementType.ELIGIBILITY_CRITERIA,
                    severity=SeverityLevel.CRITICAL,
                    field_name="years_of_contribution",
                    validation_logic={'required': True, 'range': {'min': 1}},
                    error_message="You must have contributed to CPP for at least one year",
                    suggestion="Review your CPP contribution history"
                ),
            ]
        
        # Canada Child Benefit (CCB)
        elif 'child' in program_id.lower() or 'ccb' in program_id.lower():
            return [
                ComplianceRule(
                    name="Social Insurance Number Required",
                    description="Valid Social Insurance Number is mandatory",
                    requirement_type=RequirementType.MANDATORY_FIELD,
                    severity=SeverityLevel.CRITICAL,
                    field_name="sin",
                    validation_logic={'required': True, 'pattern': r'^\d{3}-\d{3}-\d{3}$'},
                    error_message="Social Insurance Number is required",
                    suggestion="Enter your 9-digit SIN in format XXX-XXX-XXX"
                ),
                ComplianceRule(
                    name="Child Information Required",
                    description="Information about dependent children is required",
                    requirement_type=RequirementType.MANDATORY_FIELD,
                    severity=SeverityLevel.CRITICAL,
                    field_name="number_of_children",
                    validation_logic={'required': True, 'range': {'min': 1, 'max': 20}},
                    error_message="Number of dependent children under 18 is required",
                    suggestion="Include all children under 18 years of age"
                ),
            ]
        
        # Guaranteed Income Supplement (GIS)
        elif 'gis' in program_id.lower() or 'supplement' in program_id.lower():
            return [
                ComplianceRule(
                    name="Age Requirement",
                    description="Must be at least 65 years old for GIS",
                    requirement_type=RequirementType.ELIGIBILITY_CRITERIA,
                    severity=SeverityLevel.CRITICAL,
                    field_name="age",
                    validation_logic={'required': True, 'range': {'min': 65}},
                    error_message="You must be at least 65 years old to apply for GIS",
                    suggestion="GIS is available to OAS recipients aged 65 and older"
                ),
                ComplianceRule(
                    name="Income Information",
                    description="Annual income information is required to determine eligibility",
                    requirement_type=RequirementType.MANDATORY_FIELD,
                    severity=SeverityLevel.CRITICAL,
                    field_name="annual_income",
                    validation_logic={'required': True, 'range': {'min': 0}},
                    error_message="Annual income information is required",
                    suggestion="Provide your total income from the previous tax year"
                ),
            ]
        
        # Social Assistance / Welfare
        elif 'social' in program_id.lower() or 'assistance' in program_id.lower() or 'welfare' in program_id.lower():
            return [
                ComplianceRule(
                    name="Proof of Identity",
                    description="Valid government-issued ID is required",
                    requirement_type=RequirementType.DOCUMENT_REQUIREMENT,
                    severity=SeverityLevel.CRITICAL,
                    field_name="id_document",
                    validation_logic={'required': True},
                    error_message="Government-issued identification is required",
                    suggestion="Upload a copy of your driver's license, passport, or other government ID"
                ),
                ComplianceRule(
                    name="Proof of Residency",
                    description="Proof of current address is required",
                    requirement_type=RequirementType.DOCUMENT_REQUIREMENT,
                    severity=SeverityLevel.CRITICAL,
                    field_name="proof_of_residency",
                    validation_logic={'required': True},
                    error_message="Proof of current residence is required",
                    suggestion="Upload a recent utility bill, lease agreement, or bank statement showing your address"
                ),
            ]
        
        return []
    
    def _generate_suggestion(self, requirement: ExtractedRequirement) -> str:
        """Generate helpful suggestion for a requirement."""
        if requirement.requirement_type == RequirementType.MANDATORY_FIELD:
            return "This field must be completed to proceed with your application."
        elif requirement.requirement_type == RequirementType.DOCUMENT_REQUIREMENT:
            return "Please upload the required document in PDF, JPG, or PNG format."
        elif requirement.requirement_type == RequirementType.ELIGIBILITY_CRITERIA:
            return "Ensure you meet this eligibility requirement before proceeding."
        else:
            return "Please review the requirement and provide the necessary information."
    
    def _format_citation(self, rule: ComplianceRule) -> str:
        """Format a legal citation."""
        if rule.section_reference:
            return rule.section_reference
        elif rule.regulation_id:
            # Would fetch regulation title from database
            return f"Regulation {rule.regulation_id}"
        return "Regulatory requirement"
    
    def _calculate_confidence(
        self,
        total_requirements: int,
        passed_requirements: int,
        total_rules: int
    ) -> float:
        """Calculate confidence in compliance assessment."""
        if total_requirements == 0:
            return 0.5  # Low confidence if no requirements
        
        # Base confidence on coverage
        coverage = total_rules / max(total_requirements, 1)
        
        # Adjust based on pass rate
        pass_rate = passed_requirements / total_requirements if total_requirements > 0 else 0
        
        # Combine factors
        confidence = min(0.95, 0.5 + (coverage * 0.3) + (pass_rate * 0.2))
        
        return round(confidence, 2)
    
    def _generate_recommendations(self, issues: List[ComplianceIssue]) -> List[str]:
        """Generate recommendations based on issues."""
        recommendations = []
        
        # Critical issues
        critical = [i for i in issues if i.severity == SeverityLevel.CRITICAL]
        if critical:
            recommendations.append(
                f"Address {len(critical)} critical issue(s) before submission"
            )
        
        # High priority issues
        high = [i for i in issues if i.severity == SeverityLevel.HIGH]
        if high:
            recommendations.append(
                f"Review {len(high)} high-priority compliance requirement(s)"
            )
        
        # Common issue patterns
        missing_fields = [i for i in issues if i.current_value is None]
        if missing_fields:
            recommendations.append(
                "Complete all required fields to ensure compliance"
            )
        
        return recommendations
    
    def _generate_next_steps(
        self,
        issues: List[ComplianceIssue],
        compliant: bool
    ) -> List[str]:
        """Generate next steps for the user."""
        if compliant:
            return [
                "Your submission meets all regulatory requirements",
                "Review your information for accuracy",
                "Submit your application when ready"
            ]
        
        next_steps = []
        
        # Prioritize critical issues
        critical = [i for i in issues if i.severity == SeverityLevel.CRITICAL]
        if critical:
            for issue in critical[:3]:  # Top 3
                if issue.suggestion:
                    next_steps.append(issue.suggestion)
        
        # Add general guidance
        if len(issues) > 3:
            next_steps.append(
                f"Review and address all {len(issues)} compliance issues"
            )
        
        next_steps.append(
            "Contact support if you need assistance with any requirements"
        )
        
        return next_steps
