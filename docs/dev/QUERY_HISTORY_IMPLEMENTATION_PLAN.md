# Query History Implementation Plan

## Overview
Implement query history tracking for all user queries using the existing `QueryHistory` database model. This will enable analytics, improve search quality, and track user interactions.

## Current State

### ✅ Database Model (Source of Truth)
The `QueryHistory` model exists in `backend/models/models.py`:

```python
class QueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    query = Column(Text, nullable=False)
    entities = Column(JSON, default=dict)
    intent = Column(String(100), nullable=True)
    results = Column(JSON, default=list)
    rating = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 🔍 Query Entry Points
1. **Search API** (`backend/routes/search.py`):
   - `/api/search/keyword`, `/api/search/vector`, `/api/search/hybrid`
   - ✅ Already extracting: query, entities, intent
   - ❌ Not logging to database

2. **RAG API** (`backend/routes/rag.py`):
   - `/api/rag/ask`, `/api/rag/ask/batch`
   - ✅ Already extracting: question, intent
   - ❌ Not logging to database

### 📝 Sample Data Structure
```json
{
  "query": "Can a temporary resident apply for employment insurance?",
  "entities": {"program": ["employment_insurance"], "person_type": ["temporary_resident"]},
  "intent": "search",
  "results": [{"relevance": 0.95, "regulation_id": "cb261096-..."}]
}
```

---

## Implementation Plan

### Phase 1: Default User Setup ✅ COMPLETE
**Goal**: Ensure default citizen user exists for logging

#### Tasks:
- [x] **1.1** Check if default citizen user exists in database
  ```bash
  docker compose exec backend python -c "
  from database import SessionLocal
  from models.models import User
  db = SessionLocal()
  user = db.query(User).filter_by(email='citizen@example.com').first()
  print(f'User exists: {user is not None}')
  db.close()
  "
  ```
  User to use from the database:
  	4b472957-46b0-45c0-a76f-fa093421190b	citizen@example.com	citizen		{"language": "en"}	2025-11-27 19:58:45.554091	2025-11-27 19:58:45.554092

- [x] **1.2** Update `backend/seed_data.py` to include default citizen user:
  *(Not needed - database already has user table and citizen user)*

- [x] **1.3** Run seed script: `docker compose exec backend python seed_data.py`
  *(Not needed - citizen user already exists)*

---

### Phase 2: Query History Service ✅ COMPLETE
**Goal**: Create reusable service for logging queries

#### Tasks:
- [x] **2.1** Create `backend/services/query_history_service.py`
- [x] **2.2** Implement `QueryHistoryService` class with methods:
  - `log_query()` - Main logging method
  - `format_search_results()` - Format search results for storage
  - `format_rag_results()` - Format RAG results for storage
  - `get_default_citizen_user()` - Get/cache default user

- [x] **2.3** Add error handling to prevent logging failures from breaking queries

**Service Interface:**
```python
class QueryHistoryService:
    def log_query(
        self,
        db: Session,
        user_id: UUID,
        query: str,
        entities: dict,
        intent: str,
        results: list,
        rating: int = None
    ) -> Optional[QueryHistory]:
        """Log a user query to the database."""
```

---

### Phase 3: Search API Integration ✅ COMPLETE
**Goal**: Add query logging to all search endpoints

#### Files to Modify:
- `backend/routes/search.py`

#### Tasks:
- [x] **3.1** Add imports to `search.py`:
  ```python
  from database import SessionLocal
  from services.query_history_service import QueryHistoryService
  ```

- [x] **3.2** Initialize service (module level):
  ```python
  query_history_service = QueryHistoryService()
  ```

- [x] **3.3** Modify `/api/search/keyword` endpoint:
  - Add database session management
  - Extract parsed entities and intent
  - Call `query_history_service.log_query()` after successful search
  - Wrap logging in try-except to prevent failures

- [x] **3.4** Repeat for `/api/search/vector` endpoint

- [x] **3.5** Repeat for `/api/search/hybrid` endpoint

**Pattern for each endpoint:**
```python
@router.post("/keyword", response_model=SearchResponse)
async def keyword_search(request: SearchRequest):
    db = SessionLocal()
    try:
        # ... existing search logic ...
        
        # Log query history (non-blocking)
        try:
            user = query_history_service.get_default_citizen_user(db)
            query_history_service.log_query(
                db=db,
                user_id=user.id,
                query=request.query,
                entities=parsed.entities if request.parse_query else {},
                intent=query_info.get('intent') if query_info else None,
                results=query_history_service.format_search_results(results)
            )
        except Exception as e:
            logger.error(f"Failed to log query history: {e}")
        
        return response
    finally:
        db.close()
```

---

### Phase 4: RAG API Integration ✅ COMPLETE
**Goal**: Add query logging to RAG endpoints

#### Files to Modify:
- `backend/routes/rag.py`

#### Tasks:
- [x] **4.1** Add imports (same as Phase 3)

- [x] **4.2** Initialize service (module level)

- [x] **4.3** Modify `/api/rag/ask` endpoint:
  - Add database session
  - Log after successful answer generation
  - Extract intent from RAG answer
  - Format RAG results appropriately

- [x] **4.4** Modify `/api/rag/ask/batch` endpoint:
  - Log each question individually
  - Use same pattern as single question

**Pattern for RAG:**
```python
@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    db = SessionLocal()
    try:
        # ... existing RAG logic ...
        
        # Log query history
        try:
            user = query_history_service.get_default_citizen_user(db)
            query_history_service.log_query(
                db=db,
                user_id=user.id,
                query=request.question,
                entities={},  # Extract from RAG answer if available
                intent=rag_answer.intent,
                results=query_history_service.format_rag_results(rag_answer)
            )
        except Exception as e:
            logger.error(f"Failed to log query history: {e}")
        
        return response
    finally:
        db.close()
```

---

### Phase 5: Testing
**Goal**: Ensure query history logging works correctly

#### Tasks:
- [ ] **5.1** Create unit tests:
  ```python
  # backend/tests/test_query_history_service.py
  def test_log_query_creates_record()
  def test_log_query_with_entities()
  def test_log_query_handles_missing_user()
  def test_format_search_results()
  def test_format_rag_results()
  def test_get_default_citizen_user_caching()
  ```

- [ ] **5.2** Create integration tests:
  ```python
  # backend/tests/test_integration_query_history.py
  def test_search_keyword_logs_history()
  def test_search_vector_logs_history()
  def test_search_hybrid_logs_history()
  def test_rag_ask_logs_history()
  def test_rag_batch_logs_history()
  ```

- [ ] **5.3** Manual testing:
  1. Start backend: `docker compose up -d`
  2. Make search query: `POST /api/search/keyword`
  3. Verify in database:
     ```sql
     SELECT query, intent, entities, created_at 
     FROM query_history 
     ORDER BY created_at DESC 
     LIMIT 5;
     ```
  4. Check all fields populated correctly
  5. Repeat for RAG endpoint

- [ ] **5.4** Performance testing:
  - Test with 100 queries
  - Ensure logging doesn't slow down queries significantly
  - Monitor database performance

---

### Phase 6: Verification & Documentation
**Goal**: Confirm implementation and document usage

#### Tasks:
- [ ] **6.1** Verify data in database matches expected schema
- [ ] **6.2** Verify intent values are correctly extracted
- [ ] **6.3** Verify entities are properly formatted
- [ ] **6.4** Verify results array is properly formatted
- [ ] **6.5** Update API documentation with query history behavior
- [ ] **6.6** Create admin query to view recent history:
  ```sql
  SELECT 
      qh.query,
      qh.intent,
      qh.entities,
      array_length(qh.results, 1) as result_count,
      qh.created_at,
      u.email as user_email
  FROM query_history qh
  JOIN users u ON qh.user_id = u.id
  ORDER BY qh.created_at DESC
  LIMIT 20;
  ```

---

## Implementation Details

### QueryHistory Field Usage

| Field | Purpose | Example Value | Source |
|-------|---------|---------------|--------|
| `id` | Primary key | UUID | Auto-generated |
| `user_id` | User who made query | UUID | Default citizen user |
| `query` | User query text | `"Can a temporary resident apply for EI?"` | Request parameter |
| `entities` | Extracted entities | `{"program": ["employment_insurance"]}` | Query parser |
| `intent` | Query intent | `"search"`, `"compliance"`, `"eligibility"` | Query parser |
| `results` | Search/RAG results | `[{"id": "...", "score": 0.95}]` | Service response |
| `rating` | User rating (optional) | `4` | Future feature |
| `created_at` | Timestamp | `2025-12-22 20:55:00` | Auto-generated |

### Intent Values
From `backend/services/query_parser.py`:
- `search` - Information lookup
- `compliance` - Compliance checking
- `guidance` - How-to questions
- `eligibility` - Eligibility questions
- `interpretation` - Legal interpretation
- `compare` - Comparison questions
- `unknown` - Cannot determine intent

### Results Format

**Search Results:**
```json
[
  {
    "id": "regulation-uuid",
    "score": 0.95,
    "title": "Employment Insurance Act - Section 7"
  }
]
```

**RAG Results:**
```json
[
  {
    "id": "source-doc-uuid",
    "score": 0.89,
    "title": "CPP Regulations",
    "citation": "C.R.C., c. 385"
  }
]
```

---

## Error Handling Strategy

### Non-Blocking Logging
Query history logging MUST NOT break user queries:

```python
try:
    # Log query history
    query_history_service.log_query(...)
except Exception as e:
    # Log error but don't raise
    logger.error(f"Failed to log query history: {e}")
    # Continue with normal response
```

### Database Connection Management
- Use `SessionLocal()` to create new session
- Always close session in `finally` block
- Don't reuse sessions across requests

### User Lookup Caching
- Cache default citizen user in memory
- Refresh if user is deleted
- Log warning if user not found

---

## Future Enhancements

1. **User Authentication**: Replace default citizen user with actual authenticated users
2. **Rating Feature**: Add UI for users to rate query results
3. **Query Analytics**: Dashboard showing query patterns, popular topics, etc.
4. **Search Improvements**: Use query history to improve search relevance
5. **Personalization**: Use history to personalize results per user
6. **Export API**: Allow users to download their query history

---

## Success Criteria

### Functional Requirements:
- ✅ All search queries logged to database
- ✅ All RAG queries logged to database  
- ✅ Intent correctly extracted and stored
- ✅ Entities correctly extracted and stored
- ✅ Results properly formatted and stored
- ✅ Default citizen user automatically used

### Performance Requirements:
- ✅ Query logging adds < 50ms to response time
- ✅ No query failures due to logging errors
- ✅ Database can handle 1000+ queries/day

### Data Quality Requirements:
- ✅ 100% of queries captured
- ✅ Intent extraction accuracy > 80%
- ✅ Entity extraction accuracy > 75%
- ✅ No duplicate query records (except for identical retries)

---

## Rollout Plan

### Step 1: Development (Local)
1. Implement query history service
2. Add logging to search endpoints
3. Test locally with manual queries
4. Verify data in local database

### Step 2: Testing (Local)
1. Run unit tests
2. Run integration tests
3. Performance testing with 100+ queries
4. Fix any issues

### Step 3: Documentation
1. Update API docs
2. Create admin queries for viewing history
3. Document field meanings

### Step 4: Deploy
1. Deploy to staging/production
2. Monitor for errors
3. Verify queries being logged
4. Check database performance

---

## Monitoring & Maintenance

### Metrics to Track:
- Number of queries logged per day
- Query logging error rate
- Database query_history table size
- Most common intents
- Most common entities
- Average queries per user

### Database Maintenance:
- Monitor table size growth
- Consider partitioning by date for large datasets
- Implement data retention policy (e.g., keep 90 days)
- Regular vacuum and analyze

---

## Questions Resolved

1. ✅ **Rating vs Response Time**: Use existing `rating` field as-is for user ratings
2. ✅ **No New Columns**: Work with existing schema, don't add response_time_ms
3. ✅ **Default User**: Use `citizen@example.com` as default user
4. ✅ **Results Storage**: Store summarized results (ID, score, title only)

---

## Timeline Estimate

- **Phase 1** (User Setup): 30 minutes
- **Phase 2** (Service Creation): 2-3 hours
- **Phase 3** (Search Integration): 2-3 hours
- **Phase 4** (RAG Integration): 1-2 hours
- **Phase 5** (Testing): 2-3 hours
- **Phase 6** (Verification): 1 hour

**Total**: 8-12 hours

---

## Implementation Checklist

- [x] Phase 1: Default user setup
- [x] Phase 2: Query history service
- [x] Phase 3: Search API integration
- [x] Phase 4: RAG API integration
- [ ] Phase 5: Testing
- [ ] Phase 6: Verification & documentation
