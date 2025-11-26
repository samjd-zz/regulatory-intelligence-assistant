# Document Parser and Ingestion System

## Overview

The Document Parser and Ingestion System processes regulatory documents in multiple formats (PDF, HTML, XML, TXT) and extracts structured content including sections, subsections, clauses, and cross-references.

## Features

### ✅ Document Upload API
- Multi-format support: PDF, HTML, XML, TXT
- File validation and deduplication (SHA-256 hashing)
- Metadata extraction and storage
- Automatic document processing

### ✅ Intelligent Parsing
- **Section Extraction**: Automatically identifies sections, subsections, and clauses
- **Hierarchy Building**: Constructs parent-child relationships
- **Cross-Reference Detection**: Finds and catalogs references between sections
- **Multiple Formats**: Handles various legal citation formats

### ✅ Structured Storage
- PostgreSQL database with normalized schema
- Full-text content preservation
- Hierarchical section structure
- Cross-reference mapping
- Extensible metadata system

### ✅ REST API
- Document upload and retrieval
- Section browsing
- Cross-reference exploration
- Full-text and metadata search
- Statistics and analytics

## Architecture

```
┌─────────────────┐
│   Upload File   │
│  (PDF/HTML/XML) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Document Parser │
│   Service       │
└────────┬────────┘
         │
         ├──▶ Extract Text (format-specific)
         │
         ├──▶ Legal Text Parser
         │    ├─ Identify sections
         │    ├─ Extract subsections
         │    ├─ Find clauses
         │    └─ Detect cross-references
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│   Database      │
│                 │
│ ├─ documents    │
│ ├─ sections     │
│ ├─ subsections  │
│ ├─ clauses      │
│ └─ cross_refs   │
└─────────────────┘
```

## Database Schema

### Documents Table
```sql
- id (UUID, PK)
- title
- document_type (legislation, regulation, policy, etc.)
- jurisdiction
- authority
- document_number
- full_text
- file_format, file_size, file_hash
- effective_date, publication_date
- status (draft, active, amended, repealed)
- metadata (JSONB)
- is_processed, processed_date
- created_at, updated_at
```

### Document Sections Table
```sql
- id (UUID, PK)
- document_id (FK)
- section_number ("7", "7(1)", etc.)
- section_title
- section_type (section, subsection, clause)
- content (full text)
- parent_section_id (self-referencing FK)
- order_index, level
- metadata (JSONB)
```

### Document Subsections Table
```sql
- id (UUID, PK)
- section_id (FK)
- subsection_number ("1", "2", "a", "b")
- content
- parent_subsection_id (self-referencing FK)
- order_index, level
```

### Document Clauses Table
```sql
- id (UUID, PK)
- subsection_id (FK)
- clause_identifier ("a", "b", "i", "ii")
- content
- order_index
```

### Cross References Table
```sql
- id (UUID, PK)
- source_document_id (FK)
- source_section_id (FK)
- source_location
- target_document_id (FK)
- target_section_id (FK)
- target_location
- reference_type (see_also, pursuant_to, etc.)
- citation_text
- context
```

## API Endpoints

### Upload Document
```http
POST /documents/upload
Content-Type: multipart/form-data

Parameters:
- file: Document file (required)
- document_type: legislation | regulation | policy | guideline | directive
- jurisdiction: e.g., "federal", "provincial"
- authority: Issuing authority
- document_number: Official number (optional)
- effective_date: ISO date (optional)

Response:
{
  "id": "uuid",
  "title": "Employment Insurance Act",
  "document_type": "legislation",
  "jurisdiction": "federal",
  "file_format": "pdf",
  "file_size": 1048576,
  "total_sections": 45,
  "total_cross_references": 23,
  "is_processed": true,
  "upload_date": "2024-11-22T10:30:00Z"
}
```

### Get Document
```http
GET /documents/{document_id}?include_full_text=false

Response:
{
  "id": "uuid",
  "title": "Employment Insurance Act",
  "document_type": "legislation",
  "jurisdiction": "federal",
  "authority": "Parliament of Canada",
  "document_number": "S.C. 1996, c. 23",
  "status": "active",
  ...
}
```

### Get Document Sections
```http
GET /documents/{document_id}/sections

Response: [
  {
    "id": "uuid",
    "section_number": "7(1)",
    "section_title": "Eligibility for benefits",
    "section_type": "subsection",
    "content": "Subject to this Part...",
    "level": 1,
    "order_index": 0
  },
  ...
]
```

### Get Cross-References
```http
GET /documents/{document_id}/cross-references

Response: [
  {
    "id": "uuid",
    "source_location": "7(1)",
    "target_location": "7(2)",
    "reference_type": "see_also",
    "citation_text": "see Section 7(2)",
    "context": "...eligibility requirements..."
  },
  ...
]
```

### Search Documents
```http
POST /documents/search

Body:
{
  "query": "employment insurance",
  "document_type": "legislation",
  "jurisdiction": "federal",
  "status": "active"
}

Response: [
  {
    "id": "uuid",
    "title": "Employment Insurance Act",
    ...
  }
]
```

### List Documents
```http
GET /documents?document_type=legislation&jurisdiction=federal&skip=0&limit=20

Response: [...]
```

### Get Statistics
```http
GET /documents/statistics/summary

Response:
{
  "total_documents": 15,
  "total_sections": 234,
  "by_type": {
    "legislation": 10,
    "regulation": 5
  },
  "by_jurisdiction": {
    "federal": 12,
    "provincial": 3
  },
  "by_status": {
    "active": 13,
    "amended": 2
  }
}
```

## Parsing Capabilities

### Section Number Formats Supported

The parser recognizes various legal citation formats:

- **Standard Canadian**: Section 7(1)(a)
- **Numeric**: 7.1.2
- **Article**: Article 7
- **Chapter**: Chapter 3, Part II

### Cross-Reference Detection

Automatically detects references like:
- "see Section 7(2)"
- "pursuant to Section 12"
- "as defined in Section 3(1)"
- "in accordance with Section 5"
- "subject to Section 10"
- "notwithstanding Section 4"

### Hierarchy Construction

Builds parent-child relationships:
```
Section 7
├── Section 7(1)
│   ├── Section 7(1)(a)
│   └── Section 7(1)(b)
└── Section 7(2)
    ├── Section 7(2)(a)
    └── Section 7(2)(b)
```

## Usage Examples

### Upload a PDF Document

```python
import requests

url = "http://localhost:8000/documents/upload"

files = {"file": open("employment_insurance_act.pdf", "rb")}
data = {
    "document_type": "legislation",
    "jurisdiction": "federal",
    "authority": "Parliament of Canada",
    "document_number": "S.C. 1996, c. 23",
    "effective_date": "1996-06-30"
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

### Search for Documents

```python
import requests

url = "http://localhost:8000/documents/search"

payload = {
    "query": "employment insurance",
    "document_type": "legislation",
    "jurisdiction": "federal"
}

response = requests.post(url, json=payload)
documents = response.json()

for doc in documents:
    print(f"{doc['title']} - {doc['document_number']}")
```

### Retrieve Document Structure

```python
import requests

document_id = "your-document-uuid"

# Get document details
doc = requests.get(f"http://localhost:8000/documents/{document_id}").json()
print(f"Document: {doc['title']}")

# Get all sections
sections = requests.get(f"http://localhost:8000/documents/{document_id}/sections").json()
print(f"Total sections: {len(sections)}")

for section in sections[:5]:
    print(f"  - {section['section_number']}: {section['section_title']}")

# Get cross-references
refs = requests.get(f"http://localhost:8000/documents/{document_id}/cross-references").json()
print(f"Total cross-references: {len(refs)}")
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

### 3. Start the API Server

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Access API Documentation

Open http://localhost:8000/docs for interactive API documentation.

## Testing

### Run Unit Tests

```bash
cd backend
pytest tests/test_document_parser.py -v
```

### Test with Sample Documents

```bash
# Upload a sample document
curl -X POST http://localhost:8000/documents/upload \
  -F "file=@sample_regulation.pdf" \
  -F "document_type=regulation" \
  -F "jurisdiction=federal" \
  -F "authority=Government of Canada"

# Check statistics
curl http://localhost:8000/documents/statistics/summary
```

## Performance Considerations

- **File Size Limits**: Adjust FastAPI's `max_upload_size` for large documents
- **Text Extraction**: PDF parsing can be CPU-intensive
- **Indexing**: Consider full-text search indexes for large document sets
- **Caching**: Implement Redis caching for frequently accessed documents

## Future Enhancements

- [ ] OCR support for scanned PDFs
- [ ] DOCX format support
- [ ] Batch document upload
- [ ] Document versioning
- [ ] Advanced section matching algorithms
- [ ] Machine learning for improved cross-reference detection
- [ ] Integration with Neo4j for graph-based relationships
- [ ] Elasticsearch integration for advanced search

## Troubleshooting

### PDF Extraction Fails
```bash
pip install --upgrade PyPDF2
# Or try alternative: pdfplumber, pypdf
```

### HTML Parsing Issues
```bash
pip install --upgrade beautifulsoup4 lxml
```

### Database Connection Errors
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

## Files

- `backend/models/document_models.py` - SQLAlchemy models
- `backend/services/document_parser.py` - Document parsing service
- `backend/utils/legal_text_parser.py` - Legal text parsing utilities
- `backend/routes/documents.py` - FastAPI routes
- `backend/alembic/versions/002_document_models.py` - Database migration
