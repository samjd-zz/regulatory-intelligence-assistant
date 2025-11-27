# Testing Guide for Regulatory Intelligence Assistant

## Overview

This guide explains how to run the complete test suite for the Regulatory Intelligence Assistant backend. We have comprehensive test coverage including unit tests, integration tests, and end-to-end workflow tests.

## Test Infrastructure

### Test Data Seeding

The test suite uses **automatic test data seeding** via pytest fixtures in `conftest.py`:

- **8 sample Canadian regulations** covering federal and provincial laws
- **Automatic Elasticsearch indexing** before tests run
- **Session-scoped fixtures** for efficient test execution
- **Automatic service detection** (skips tests if services unavailable)

### Test Categories

1. **Unit Tests** - Test individual components in isolation
2. **Integration Tests** - Test service interactions (require Elasticsearch/Gemini API)
3. **End-to-End Tests** - Test complete user workflows

## Prerequisites

### 1. Start Docker Services

```bash
# From project root
docker compose up -d

# Wait ~30 seconds for services to be ready
docker compose ps

# Expected output: All services "healthy"
```

### 2. Set Up Python Environment

```bash
cd backend

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (if not already done)
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env and set:
# - GEMINI_API_KEY=your_key_here (for RAG tests)
