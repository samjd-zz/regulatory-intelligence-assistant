# Quick Start Guide

Get the Regulatory Intelligence Assistant running in under 5 minutes.

## Prerequisites

- Docker & Docker Compose
- Git
- 8GB RAM minimum
- Gemini API key (optional for RAG features)

## Installation

### 1. Clone & Setup

```bash
git clone <repository-url>
cd regulatory-intelligence-assistant
cp backend/.env.example backend/.env
```

### 2. Configure API Keys

Edit `backend/.env`:

```bash
# Required for RAG/Q&A features
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Use Ollama instead
# OLLAMA_HOST=http://ollama:11434
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Neo4j, Elasticsearch, Backend, Frontend)
docker compose up -d

# Wait for services to be ready (~30 seconds)
docker compose ps
```

### 4. Initialize Database

```bash
# Run migrations and create tables
docker compose exec backend python create_tables.py

# Load sample data (10 Canadian federal acts)
docker compose exec backend python seed_data.py
```

### 5. Access the Application

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (neo4j/password123)

## Verify Installation

### Test Search

```bash
curl "http://localhost:8000/api/search?q=employment+insurance&limit=5"
```

### Test RAG Q&A

```bash
curl -X POST http://localhost:8000/api/rag/answer \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is eligible for employment insurance?"}'
```

### Test Compliance Check

```bash
curl -X POST http://localhost:8000/api/compliance/check \
  -H "Content-Type: application/json" \
  -d '{
    "program_id": "employment-insurance",
    "workflow_type": "ei_application",
    "form_data": {
      "sin": "123-456-789",
      "hours_worked": 700
    }
  }'
```

## Common Issues

### Services Not Starting

```bash
# Check logs
docker compose logs backend
docker compose logs postgres

# Restart services
docker compose restart
```

### Port Conflicts

Edit `docker-compose.yml` to change ports:
- Frontend: 5173 → 3000
- Backend: 8000 → 8080
- Neo4j: 7474 → 7475

### Low Memory

Reduce Elasticsearch memory in `docker-compose.yml`:
```yaml
environment:
  - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
```

## Next Steps

- **Load More Data**: See [Data Ingestion Guide](./DATA_INGESTION.md)
- **API Reference**: Browse http://localhost:8000/docs
- **Architecture**: Read [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Development**: See [DEVELOPMENT.md](./DEVELOPMENT.md)

## Stop Services

```bash
# Stop all services
docker compose down

# Stop and remove volumes (delete all data)
docker compose down -v
```
