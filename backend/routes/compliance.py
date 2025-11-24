"""
FastAPI routes for compliance checking endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas.compliance_rules import (
    ComplianceCheckRequest, ComplianceReport,
    FieldValidationRequest, FieldValidationResponse,
    RequirementExtractionRequest, ExtractedRequirement,
    ComplianceMetrics, ComplianceRuleSet
)
from services.compliance_checker import ComplianceChecker
from services.graph_service import GraphService
from utils.neo4j_client import Neo4jClient


router = APIRouter(prefix="/api/compliance", tags=["compliance"])


def get_compliance_checker(db: Session = Depends(get_db)) -> ComplianceChecker:
    """Dependency to get compliance checker instance."""
    neo4j_client = Neo4jClient()
    graph_service = GraphService(neo4j_client)
    return ComplianceChecker(db, graph_service)


@router.post("/check", response_model=ComplianceReport)
async def check_compliance(
    request: ComplianceCheckRequest,
    checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """
    Check form submission for regulatory compliance.
    
    This endpoint validates form data against applicable regulations and returns
    a comprehensive compliance report with issues, recommendations, and next steps.
    
    **Example Request:**
    ```json
    {
      "program_id": "employment-insurance",
      "workflow_type": "ei_application",
      "form_data": {
        "sin": "123-456-789",
        "employment_status": "employed",
        "residency_status": "citizen"
      },
      "user_context": {
        "jurisdiction": "federal"
      },
      "check_optional": false
    }
    ```
    
    **Response includes:**
    - Overall compliance status
    - List of compliance issues (critical, high, medium, low)
    - Specific field violations with suggestions
    - Legal citations for requirements
    - Recommendations and next steps
    """
    try:
        report = await checker.check_compliance(request)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance check failed: {str(e)}"
        )


@router.post("/validate-field", response_model=FieldValidationResponse)
async def validate_field(
    request: FieldValidationRequest,
    checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """
    Validate a single form field in real-time.
    
    This endpoint provides immediate feedback on a single field as the user types,
    helping guide them to provide compliant data before form submission.
    
    **Example Request:**
    ```json
    {
      "program_id": "employment-insurance",
      "field_name": "sin",
      "field_value": "123-456-78",
      "form_context": {
        "employment_status": "employed"
      }
    }
    ```
    
    **Response includes:**
    - Validation status (valid/invalid)
    - Error messages for critical/high severity issues
    - Warnings for medium/low severity issues
    - Suggestions to fix validation errors
    """
    try:
        result = await checker.validate_field(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Field validation failed: {str(e)}"
        )


@router.post("/requirements/extract", response_model=List[ExtractedRequirement])
async def extract_requirements(
    request: RequirementExtractionRequest,
    checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """
    Extract compliance requirements from regulatory documents.
    
    This endpoint analyzes regulatory text to identify and extract specific
    requirements, eligibility criteria, mandatory fields, and validations.
    
    **Example Request:**
    ```json
    {
      "program_id": "employment-insurance",
      "regulation_id": "uuid-of-regulation",
      "section_ids": ["uuid-of-section-1", "uuid-of-section-2"]
    }
    ```
    
    **Response includes:**
    - Extracted requirement text
    - Requirement type (mandatory, eligibility, document, etc.)
    - Severity level
    - Source citations
    - Extracted conditions
    - Confidence score
    """
    try:
        requirements = await checker.requirement_extractor.extract_requirements(request)
        return requirements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Requirement extraction failed: {str(e)}"
        )


@router.get("/requirements/{program_id}", response_model=ComplianceRuleSet)
async def get_program_requirements(
    program_id: str,
    workflow_type: str = "general",
    checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """
    Get all compliance requirements for a specific program.
    
    Returns the complete rule set for a program, including extracted requirements
    from regulations and predefined validation rules.
    
    **Path Parameters:**
    - program_id: Unique identifier for the program/service
    
    **Query Parameters:**
    - workflow_type: Type of workflow (default: "general")
    
    **Response includes:**
    - Program information
    - Complete list of compliance rules
    - Rule metadata (severity, type, citations)
    - Validation logic for each rule
    """
    try:
        rules = await checker._get_rules_for_program(program_id, workflow_type)
        
        # Create rule set response
        rule_set = ComplianceRuleSet(
            program_id=program_id,
            program_name=program_id,  # Would fetch from database
            jurisdiction="federal",  # Would determine from context
            rules=rules
        )
        
        return rule_set
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve requirements: {str(e)}"
        )


@router.get("/metrics", response_model=ComplianceMetrics)
async def get_compliance_metrics(
    db: Session = Depends(get_db)
):
    """
    Get compliance checking metrics and statistics.
    
    Returns aggregate metrics about compliance checking performance,
    accuracy, and common issues across all checks.
    
    **Response includes:**
    - Total compliance checks performed
    - Pass/fail rates
    - Average confidence scores
    - Most common compliance issues
    - Accuracy metrics (when validation data available)
    """
    try:
        # This would query actual metrics from the database
        # For MVP, return placeholder data
        
        from models import WorkflowSession
        from sqlalchemy import func
        
        # Count workflow sessions
        total_workflows = db.query(func.count(WorkflowSession.id)).scalar() or 0
        completed = db.query(func.count(WorkflowSession.id)).filter(
            WorkflowSession.status == 'completed'
        ).scalar() or 0
        
        metrics = ComplianceMetrics(
            total_checks=total_workflows,
            passed_checks=completed,
            failed_checks=total_workflows - completed,
            average_confidence=0.82,  # Would calculate from actual data
            common_issues=[
                {
                    "issue": "Missing Social Insurance Number",
                    "count": 45,
                    "severity": "critical"
                },
                {
                    "issue": "Invalid work permit format",
                    "count": 28,
                    "severity": "high"
                },
                {
                    "issue": "Incomplete address information",
                    "count": 19,
                    "severity": "medium"
                }
            ]
        )
        
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve metrics: {str(e)}"
        )


@router.delete("/cache/{program_id}")
async def clear_rule_cache(
    program_id: str,
    workflow_type: str = "general",
    checker: ComplianceChecker = Depends(get_compliance_checker)
):
    """
    Clear cached compliance rules for a program.
    
    Use this endpoint after updating regulations or rules to force
    the system to re-extract requirements on the next check.
    
    **Path Parameters:**
    - program_id: Unique identifier for the program/service
    
    **Query Parameters:**
    - workflow_type: Type of workflow (default: "general")
    """
    try:
        cache_key = f"{program_id}:{workflow_type}"
        if cache_key in checker.rule_cache:
            del checker.rule_cache[cache_key]
            return {"message": f"Cache cleared for {program_id}", "cache_key": cache_key}
        else:
            return {"message": f"No cache found for {program_id}", "cache_key": cache_key}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )
