# Developer Setup Guide - Regulatory Intelligence Assistant

**Author:** Developer 2 (AI/ML Engineer)
**Created:** 2025-11-22
**Version:** 1.0

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Detailed Setup](#detailed-setup)
4. [Running Tests](#running-tests)
5. [Development Workflow](#development-workflow)
6. [Troubleshooting](#troubleshooting)
7. [Performance Benchmarking](#performance-benchmarking)
8. [API Testing](#api-testing)

---

## Prerequisites

### Required Software

- **Python:** 3.10 or higher
- **PostgreSQL:** 15+
- **Elasticsearch:** 8.11+
- **Neo4j:** 5.x Community Edition
- **Redis:** 7+ (optional for MVP, in-memory cache used)
- **Git:** Latest version

### Required API Keys

- **Gemini API Key:** Get from [Google AI Studio](https://ai.google.dev/)
  - Set as environment variable: `GEMINI_API_KEY`

### System Requirements

- **RAM:** Minimum 8GB, recommended 16GB
- **Disk:** 10GB free space
- **OS:** Linux, macOS, or Windows with WSL2

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/your-org/regulatory-intelligence-assistant.git
cd regulatory-intelligence-assistant
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file in `backend/` directory:

```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=regulatory_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Redis (optional)
REDIS_URL=redis://localhost:6379

# AI Services
GEMINI_API_KEY=your_gemini_api_key_here

# App Configuration
APP_ENV=development
DEBUG=True
LOG_LEVEL=INFO
```

### 4. Start Services with Docker

```bash
# From project root
cd ..
docker-compose up -d postgres neo4j elasticsearch redis
```

### 5. Initialize Database

```bash
cd backend

# Run Alembic migrations
alembic upgrade head

# Seed sample data (optional)
python seed_data.py
```

### 6. Initialize Elasticsearch

```bash
# Create index with legal mappings
python -c "from services.search_service import SearchService; SearchService().create_index()"
```

### 7. Initialize Neo4j

```bash
# Run Neo4j initialization script
python scripts/init_neo4j.py
```

### 8. Start Backend Server

```bash
# Development server with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

---

## Detailed Setup

### PostgreSQL Setup

#### Manual Installation (without Docker)

**On Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

**On macOS:**
```bash
brew install postgresql@15
brew services start postgresql@15
```

**Create Database:**
```bash
sudo -u postgres psql
CREATE DATABASE regulatory_db;
CREATE USER postgres WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE regulatory_db TO postgres;
\q
```

### Elasticsearch Setup

#### Manual Installation

**On Ubuntu:**
```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install apt-transport-https
echo "deb https://artifacts.elastic.co/packages/8.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-8.x.list
sudo apt-get update && sudo apt-get install elasticsearch
sudo systemctl start elasticsearch
```

**On macOS:**
```bash
brew install elasticsearch
brew services start elasticsearch
```

**Verify:**
```bash
curl http://localhost:9200
```

### Neo4j Setup

#### Manual Installation

**On Ubuntu:**
```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo "deb https://debian.neo4j.com stable latest" | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt-get update
sudo apt-get install neo4j
sudo systemctl start neo4j
```

**On macOS:**
```bash
brew install neo4j
brew services start neo4j
```

**Access Neo4j Browser:**
- URL: `http://localhost:7474`
- Default credentials: `neo4j / neo4j`
- Change password on first login

---

## Running Tests

### Unit Tests

```bash
cd backend

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_legal_nlp.py -v

# Run with coverage
pytest --cov=services --cov-report=html
```

### Integration Tests

```bash
# NLP integration tests
pytest tests/BAITMAN_test_integration_nlp.py -v

# Search integration tests (requires Elasticsearch)
pytest tests/BAITMAN_test_integration_search.py -v

# RAG integration tests (requires Gemini API key)
pytest tests/BAITMAN_test_integration_rag.py -v
```

### End-to-End Tests

```bash
# E2E workflow tests
pytest tests/BAITMAN_test_e2e_workflows.py -v
```

### Skip Tests Missing Dependencies

```bash
# Skip tests requiring Elasticsearch
pytest -v -m "not elasticsearch"

# Skip tests requiring Gemini API
pytest -v -m "not gemini"
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow coding standards:
- PEP 8 for Python code
- Type hints for function signatures
- Docstrings for all public functions/classes
- Comprehensive error handling

### 3. Run Tests

```bash
# Run relevant tests
pytest tests/test_your_module.py -v

# Check code style
flake8 services/

# Type checking
mypy services/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: Add your feature description"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

---

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

**Error:** `Address already in use`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### 2. Elasticsearch Connection Failed

**Error:** `ConnectionError: Connection refused`

**Solution:**
```bash
# Check Elasticsearch status
curl http://localhost:9200

# Restart Elasticsearch
docker-compose restart elasticsearch

# Check logs
docker-compose logs elasticsearch
```

#### 3. Gemini API Rate Limit

**Error:** `429 Too Many Requests`

**Solution:**
- Implement rate limiting in code
- Use caching for repeated queries
- Upgrade Gemini API plan if needed

#### 4. PostgreSQL Permission Denied

**Error:** `FATAL: password authentication failed`

**Solution:**
```bash
# Update .env file with correct credentials
# Verify connection
psql -h localhost -U postgres -d regulatory_db
```

#### 5. Neo4j Authentication Failed

**Error:** `AuthError: The client is unauthorized`

**Solution:**
```bash
# Reset Neo4j password
neo4j-admin set-initial-password new_password

# Update .env file
NEO4J_PASSWORD=new_password
```

---

## Performance Benchmarking

### Run Full Benchmark Suite

```bash
cd backend/evaluation
python BAITMAN_performance_benchmark.py
```

**Expected Output:**
```
================================================================================
PERFORMANCE BENCHMARK SUITE
================================================================================
Started at: 2025-11-22T...

LATENCY BENCHMARKS
================================================================================

NLP - Query Parsing
  Running 100 iterations.......... Done!
  Results:
    Min:         8.45 ms
    Mean:       12.34 ms
    Median:     11.89 ms
    P95:        18.90 ms
    P99:        22.34 ms
    Max:        25.67 ms
    Std Dev:     3.21 ms
    Target:    100.00 ms
    Status:     ✅ PASS

Search - Hybrid (BM25 + Vector)
  Running 50 iterations..... Done!
  Results:
    Min:       245.32 ms
    Mean:      312.45 ms
    Median:    298.67 ms
    P95:       420.12 ms
    P99:       456.78 ms
    Max:       489.90 ms
    Std Dev:    45.23 ms
    Target:    500.00 ms
    Status:     ✅ PASS

...

BENCHMARK SUMMARY
================================================================================
Latency Benchmarks: 7/7 passed

Results:
  ✅ NLP - Query Parsing                           P95:    18.9ms (target: 100ms)
  ✅ Search - Keyword (BM25)                       P95:    89.2ms (target: 100ms)
  ✅ Search - Vector (Semantic)                    P95:   356.7ms (target: 400ms)
  ✅ Search - Hybrid (BM25 + Vector)               P95:   420.1ms (target: 500ms)
  ✅ RAG - Answer Generation (Gemini API)          P95:  4567.8ms (target: 5000ms)
  ✅ RAG - Cached Answer Retrieval                 P95:    12.3ms (target: 100ms)

Throughput Benchmarks:
  • NLP - Throughput                                  850.3 qps
  • Search - Throughput                                25.6 qps
```

### Run Search Quality Evaluation

```bash
cd backend/evaluation
python BAITMAN_evaluate_search_quality.py
```

**Expected Output:**
```
================================================================================
SEARCH AND RAG QUALITY EVALUATION
================================================================================
Started at: 2025-11-22T...
Total test queries: 30

1. Evaluating search precision and recall...
   Precision@10: 82.00%
   Recall@10: 76.00%

2. Evaluating entity extraction accuracy...
   Accuracy: 89.00%

3. Evaluating intent classification accuracy...
   Accuracy: 87.50%

4. Evaluating RAG answer quality (10 samples)...
   Average coverage: 78.00%
   Average confidence: 0.72
   Average citations: 2.1
   Average time: 3245ms

Results saved to: BAITMAN_evaluation_results_20251122_143022.json
```

---

## API Testing

### Using cURL

#### 1. NLP - Extract Entities

```bash
curl -X POST "http://localhost:8000/api/nlp/extract-entities" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Can a permanent resident in Ontario apply for employment insurance?",
    "entity_types": ["person_type", "jurisdiction", "program"]
  }'
```

#### 2. Search - Hybrid Search

```bash
curl -X POST "http://localhost:8000/api/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "employment insurance eligibility",
    "size": 10,
    "keyword_weight": 0.5,
    "vector_weight": 0.5
  }'
```

#### 3. RAG - Ask Question

```bash
curl -X POST "http://localhost:8000/api/rag/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the Canada Pension Plan?",
    "num_context_docs": 5,
    "use_cache": true
  }'
```

#### 4. Compliance - Check Form

```bash
curl -X POST "http://localhost:8000/api/compliance/check" \
  -H "Content-Type: application/json" \
  -d '{
    "program_id": "employment_insurance",
    "form_data": {
      "applicant_type": "permanent_resident",
      "work_status": "unemployed",
      "insurable_hours": 600
    }
  }'
```

### Using Python Requests

```python
import requests

# NLP Query Parsing
response = requests.post(
    "http://localhost:8000/api/nlp/parse-query",
    json={
        "query": "Can refugees work in Canada?"
    }
)
print(response.json())

# Search
response = requests.post(
    "http://localhost:8000/api/search/hybrid",
    json={
        "query": "old age security eligibility",
        "size": 5
    }
)
print(response.json())

# RAG Question Answering
response = requests.post(
    "http://localhost:8000/api/rag/ask",
    json={
        "question": "Who is eligible for GIS?",
        "num_context_docs": 3
    }
)
answer = response.json()
print(f"Answer: {answer['answer']}")
print(f"Confidence: {answer['confidence_score']}")
print(f"Citations: {len(answer['citations'])}")
```

---

## Additional Resources

### Documentation

- [Legal NLP Service](./BAITMAN_legal-nlp-service.md)
- [Search Service](./BAITMAN_search-service.md)
- [RAG Service](./BAITMAN_rag-service.md)
- [Compliance Report](../BAITMAN_COMPLIANCE_REPORT.md)

### API Documentation

- Interactive API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Monitoring

- Health Check: `http://localhost:8000/health/all`
- Neo4j Browser: `http://localhost:7474`
- Elasticsearch: `http://localhost:9200`

### Support

- GitHub Issues: `https://github.com/your-org/regulatory-intelligence-assistant/issues`
- Developer Chat: [Link to Slack/Discord]

---

## Next Steps

1. **Read the Documentation:** Familiarize yourself with the service documentation
2. **Run the Tests:** Ensure all tests pass in your environment
3. **Try the API:** Use the interactive docs to explore endpoints
4. **Review Code:** Check out the codebase structure and conventions
5. **Start Contributing:** Pick up an issue and start coding!

---

**Happy Coding!** 🚀
