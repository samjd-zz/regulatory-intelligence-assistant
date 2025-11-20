# Compliance Checking Engine Documentation



## Overview



The Compliance Checking Engine is a sophisticated system for validating form submissions against complex regulatory requirements. It extracts requirements from legal text, validates data in real-time, and provides actionable compliance reports with citations and recommendations.



## Architecture



### Components



1. **RequirementExtractor**: Extracts structured requirements from regulatory text using pattern matching

2. **RuleEngine**: Validates form data against compliance rules using 8 validation types

3. **ComplianceChecker**: Orchestrates compliance checking with caching and reporting
   
   

### Data Flow



```

User Request → ComplianceChecker → Rule Retrieval (cached/DB/graph)

                      ↓

               RuleEngine Validation

                      ↓

          Generate Compliance Report

                      ↓

            Return with Recommendations

```



## API Endpoints



### 1. Check Full Compliance



**POST** `/api/v1/compliance/check`



Validates complete form submission against all regulatory requirements.



**Request:**

```json

{

  "program_id": "employment-insurance",

  "workflow_type": "ei_application",

  "form_data": {

    "sin": "123-456-789",

    "employment_status": "unemployed",

    "residency_status": "citizen"

  },

  "user_context": {

    "role": "applicant",

    "session_id": "abc123"

  },

  "check_optional": false

}

```



**Response:**

```json

{

  "program_id": "employment-insurance",

  "workflow_type": "ei_application",

  "compliant": true,

  "confidence": 0.92,

  "issues": [],

  "passed_requirements": 15,

  "total_requirements": 15,

  "critical_issues": 0,

  "high_issues": 0,

  "recommendations": [

    "Your submission meets all regulatory requirements"

  ],

  "next_steps": [

    "Review your information for accuracy",

    "Submit your application when ready"

  ],

  "checked_at": "2025-01-20T15:30:00Z"

}

```



### 2. Validate Single Field



**POST** `/api/v1/compliance/validate-field`



Real-time validation for individual field as user types.



**Request:**

```json

{

  "program_id": "employment-insurance",

  "field_name": "sin",

  "field_value": "123-456-789",

  "form_context": {

    "residency_status": "citizen"

  }

}

```



**Response:**

```json

{

  "field_name": "sin",

  "valid": true,

  "errors": [],

  "warnings": [],

  "suggestions": []

}

```



### 3. Extract Requirements



**POST** `/api/v1/compliance/requirements/extract`



Extract structured requirements from regulatory text.



**Request:**

```json

{

  "program_id": "employment-insurance",

  "regulation_id": "ei-reg-2025",

  "section_ids": ["sec-7-1-a", "sec-7-1-b"]

}

```



**Response:**

```json

{

  "requirements": [

    {

      "requirement_text": "Applicants must provide valid Social Insurance Number",

      "requirement_type": "mandatory_field",

      "severity": "critical",

      "source_regulation_id": "ei-reg-2025",

      "source_section_id": "sec-7-1-a",

      "citation": "Section 7(1)(a)",

      "extracted_conditions": null,

      "confidence": 0.85

    }

  ]

}

```



### 4. Get Program Requirements



**GET** `/api/v1/compliance/requirements/{program_id}`



Retrieve all compliance requirements for a program.



**Response:**

```json

{

  "program_id": "employment-insurance",

  "program_name": "Employment Insurance",

  "jurisdiction": "federal",

  "rules": [

    {

      "id": "rule-uuid",

      "name": "Social Insurance Number Required",

      "description": "Valid SIN is mandatory for all applicants",

      "requirement_type": "mandatory_field",

      "severity": "critical",

      "field_name": "sin",

      "validation_logic": {

        "required": true,

        "pattern": "^\\d{3}-\\d{3}-\\d{3}$"

      },

      "error_message": "Social Insurance Number is required",

      "suggestion": "Enter your 9-digit SIN in format XXX-XXX-XXX"

    }

  ],

  "last_updated": "2025-01-20T14:00:00Z"

}

```



### 5. Get Compliance Metrics



**GET** `/api/v1/compliance/metrics`



Retrieve aggregate compliance metrics.



**Query Parameters:**

- `program_id`: Filter by program (optional)

- `start_date`: Start date for metrics (optional)

- `end_date`: End date for metrics (optional)
  
  

**Response:**

```json

{

  "total_checks": 1250,

  "compliant_submissions": 875,

  "compliance_rate": 0.70,

  "common_issues": [

    {

      "field_name": "sin",

      "count": 125,

      "percentage": 0.33

    }

  ],

  "average_confidence": 0.85

}

```



### 6. Clear Rule Cache



**DELETE** `/api/v1/compliance/cache/{program_id}`



Manually clear cached rules for a program (useful after regulatory updates).



**Response:**

```json

{

  "message": "Cache cleared successfully for program: employment-insurance"

}

```



## Validation Types



### 1. Required Field

Ensures field is present and non-empty.



```python

validation_logic = {"required": True}

```



### 2. Pattern Matching

Validates against regex pattern.



```python

validation_logic = {"pattern": r"^\d{3}-\d{3}-\d{3}$"}

```



### 3. Length Constraints

Minimum and maximum length validation.



```python

validation_logic = {

    "min_length": 2,

    "max_length": 50

}

```



### 4. Numeric Range

Validates numeric values within range.



```python

validation_logic = {

    "range": {

        "min": 18,

        "max": 65

    }

}

```



### 5. Allowed Values

Validates against list of allowed values.



```python

validation_logic = {

    "in_list": ["citizen", "permanent_resident", "temporary"]

}

```



### 6. Date Format

Validates date string format.



```python

validation_logic = {

    "date_format": "%Y-%m-%d"

}

```



### 7. Conditional Logic

Applies validation only when condition is met.



```python

validation_logic = {

    "conditional": {

        "condition": {

            "type": "field_equals",

            "field": "residency_status",

            "value": "temporary"

        },

        "validation": {"required": True}

    }

}

```



### 8. Combined Validations

Multiple validations can be combined.



```python

validation_logic = {

    "required": True,

    "pattern": r"^\d{3}-\d{3}-\d{3}$",

    "min_length": 11,

    "max_length": 11

}

```



## Requirement Extraction



### Pattern Matching



The system uses regex patterns to identify different requirement types:



**Mandatory Requirements:**

- "must provide", "shall submit", "is required to"
  
  

**Prohibited Actions:**

- "must not", "shall not", "prohibited from"
  
  

**Conditional Requirements:**

- "if...then", "unless...must", "where...shall"
  
  

**Eligibility Criteria:**

- "eligible if", "qualifies when", "entitled to...if"
  
  

### Priority Order



Patterns are checked in priority order to handle complex sentences:

1. Conditional (most specific)

2. Eligibility

3. Prohibited

4. Mandatory (most general)
   
   

This ensures "If X then must Y" is classified as conditional, not mandatory.



## Severity Levels



### Critical

- Blocks submission if not satisfied

- Examples: Missing SIN, invalid citizenship status

- User cannot proceed until resolved
  
  

### High

- Strongly recommended to fix

- May cause application delays

- Examples: Invalid phone format, missing optional document
  
  

### Medium

- Should be addressed for complete application

- Examples: Missing optional fields, formatting suggestions
  
  

### Low

- Nice-to-have improvements

- Examples: Additional documentation, clarifications
  
  

## Confidence Scoring



The system calculates confidence in compliance assessments:



```python

confidence = 0.5 + (coverage * 0.3) + (pass_rate * 0.2)

```



**Factors:**

- **Coverage**: Ratio of rules checked to total requirements

- **Pass Rate**: Percentage of requirements passed

- **Base**: 0.5 minimum confidence
  
  

**Interpretation:**

- **0.90-0.95**: High confidence (comprehensive check, most passed)

- **0.70-0.89**: Good confidence (reasonable coverage)

- **0.50-0.69**: Moderate confidence (limited coverage or many failures)
  
  

## Rule Caching



Rules are cached for 1 hour to improve performance:



```python

cache_key = f"{program_id}:{workflow_type}"

cache_ttl = 3600  # 1 hour

```



**Cache Invalidation:**

- Automatic after 1 hour

- Manual via DELETE `/api/v1/compliance/cache/{program_id}`

- Triggered by regulatory updates
  
  

## Error Handling



### Validation Errors

```json

{

  "field_name": "sin",

  "errors": ["Invalid format"],

  "warnings": [],

  "suggestions": ["Enter your 9-digit SIN in format XXX-XXX-XXX"]

}

```



### System Errors

```json

{

  "detail": "Failed to retrieve regulations",

  "error_code": "REGULATION_NOT_FOUND",

  "timestamp": "2025-01-20T15:30:00Z"

}

```



## Best Practices



### 1. Real-time Validation

Use field validation endpoint as user types:

```javascript

const validateField = async (fieldName, value, context) => {

  const response = await fetch('/api/v1/compliance/validate-field', {

    method: 'POST',

    body: JSON.stringify({

      program_id: 'employment-insurance',

      field_name: fieldName,

      field_value: value,

      form_context: context

    })

  });

  return response.json();

};

```



### 2. Batch Validation

Check full compliance before submission:

```javascript

const checkCompliance = async (formData) => {

  const response = await fetch('/api/v1/compliance/check', {

    method: 'POST',

    body: JSON.stringify({

      program_id: 'employment-insurance',

      workflow_type: 'ei_application',

      form_data: formData

    })

  });

  return response.json();

};

```



### 3. Progressive Disclosure

Show issues by severity:

```javascript

const displayIssues = (report) => {

  // Show critical issues first

  const critical = report.issues.filter(i => i.severity === 'critical');

  if (critical.length > 0) {

    showCriticalAlert(critical);

  }

  // Then high priority

  const high = report.issues.filter(i => i.severity === 'high');

  if (high.length > 0) {

    showWarnings(high);

  }

};

```



### 4. Contextual Help

Use suggestions and citations:

```javascript

const showFieldHelp = (issue) => {

  return {

    error: issue.description,

    help: issue.suggestion,

    reference: issue.regulation_citation

  };

};

```



## Testing



### Unit Tests

Run with pytest:

```bash

cd backend

source ../.venv/bin/activate

python -m pytest tests/test_compliance_checker.py -v

```



**Test Coverage:**

- 24 unit tests

- 100% code coverage for validation functions

- Tests for all 8 validation types

- Edge case handling
  
  

### Integration Tests

```bash

python -m pytest tests/test_compliance_integration.py -v

```



## Performance



### Benchmarks

- Field validation: <50ms

- Full compliance check (15 rules): <200ms

- Requirement extraction: <500ms

- Rule cache hit: <10ms
  
  

### Optimization

- Rule caching (1-hour TTL)

- Lazy loading of regulations

- Batch validation support

- Async/await for I/O operations
  
  

## Security Considerations



### Input Validation

- All inputs sanitized

- Regex patterns validated

- SQL injection prevention

- XSS protection
  
  

### Access Control

- API endpoints protected by authentication

- Program-level access control

- Audit logging for compliance checks
  
  

### Data Privacy

- No PII stored in logs

- Encrypted data in transit

- Compliance reports include only necessary data
  
  

## Deployment



### Environment Variables

```bash

# Required

DATABASE_URL=postgresql://user:pass@localhost/ria

NEO4J_URI=bolt://localhost:7687

GEMINI_API_KEY=your-key



# Optional

RULE_CACHE_TTL=3600  # 1 hour

MAX_REQUIREMENTS_PER_CHECK=100

CONFIDENCE_THRESHOLD=0.7

```



### Docker Deployment

```yaml

services:

  backend:

    environment:

      - DATABASE_URL=postgresql://user:pass@db/ria

      - NEO4J_URI=bolt://neo4j:7687

      - RULE_CACHE_TTL=3600

```



### Monitoring

- Compliance check success rate

- Average response time

- Cache hit rate

- Common validation failures
  
  

## Future Enhancements



### Planned Features

1. **ML-based Requirement Extraction**: Use NLP models for better accuracy

2. **Cross-regulation Validation**: Check conflicts between regulations

3. **Automated Rule Generation**: Learn from expert validations

4. **Multi-language Support**: Bilingual requirement extraction

5. **Workflow-specific Rules**: Custom validation logic per workflow

6. **Historical Analysis**: Track compliance trends over time
   
   

### API Extensions

- Bulk compliance checking

- Partial submission validation

- Draft validation (lenient mode)

- Regulation diff and change tracking
  
  

## Support



### Common Issues



**Issue: Low confidence scores**

- Check rule coverage for program

- Verify regulations are up to date

- Review requirement extraction patterns
  
  

**Issue: False positives**

- Refine validation patterns

- Add program-specific rules

- Report edge cases for pattern improvement
  
  

**Issue: Performance degradation**

- Check cache hit rate

- Monitor database query performance

- Consider increasing cache TTL
  
  

### Contact

For questions or issues, contact the development team or file an issue in the repository.



## Changelog



### Version 1.0.0 (2025-01-20)

- Initial release

- 8 validation types

- Real-time field validation

- Full compliance checking

- Requirement extraction from regulatory text

- Rule caching

- Confidence scoring

- Recommendation generation

- 24 unit tests with 100% pass rate
