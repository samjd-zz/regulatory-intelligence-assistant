# Deprecated Scripts

This folder contains old scripts that have been superseded by newer implementations.

## Replaced Scripts

### `download_regulations.sh` → Superseded
**Replacement**: Use `download_bulk_regulations.sh` or `download_and_ingest_real_data.sh`  
**Reason**: Old script only provided manual instructions, newer scripts handle automatic downloads

### `download_and_ingest_regulations.sh` → Superseded  
**Replacement**: Use `init_data.py` with download integration  
**Reason**: Limited to 8 priority regulations, new system handles full dataset with options

### `seed_graph_data.py` → Superseded
**Replacement**: Use `init_data.py` which calls `data_pipeline.py`  
**Reason**: Manual sample data, replaced by automated ingestion pipeline with real data

### `test_document_api.py` → Superseded
**Replacement**: Use `pytest` test suite in `backend/tests/`  
**Reason**: Proper test framework with fixtures and assertions

### `test_graph_system.py` → Superseded
**Replacement**: Use `pytest` test suite in `backend/tests/`  
**Reason**: Proper test framework with fixtures and assertions

### `force_reload.sh` → Superseded
**Replacement**: Use `docker compose restart backend`  
**Reason**: Docker Compose handles container restarts properly

## Archived Documentation

### `PHASE4_DEPLOYMENT_GUIDE.md`
Legacy deployment guide from Phase 4 database optimizations. Kept for historical reference.

---

**Note**: These files are kept for reference only and should not be used in production.
