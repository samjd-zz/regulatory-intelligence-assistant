#!/bin/bash

# =============================================================================
# Real Canadian Data Download and Ingestion Script
# =============================================================================
# This script follows the REAL_CANADIAN_DATA_INGESTION_PLAN.md to download
# and ingest official Canadian federal regulations from Justice Canada.
#
# Source: https://github.com/justicecanada/laws-lois-xml
# License: Open Government License - Canada
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/justicecanada/laws-lois-xml.git"
STAGING_DIR="backend/data/staging/canadian_laws"
TARGET_DIR="backend/data/regulations/canadian_laws"
BACKUP_DIR="backend/data/regulations/canadian_laws.sample.backup"
LIMIT=10  # Number of files to process (set to 0 for all)

# =============================================================================
# Helper Functions
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed. Please install it first."
        exit 1
    fi
}

# =============================================================================
# Step 1: Pre-flight Checks
# =============================================================================

log_info "Running pre-flight checks..."

# Check required commands
check_command git
check_command docker
check_command curl

# Check if Docker services are running
if ! docker ps &> /dev/null; then
    log_error "Docker is not running. Please start Docker first."
    exit 1
fi

log_success "Pre-flight checks passed"

# =============================================================================
# Step 2: Download Real Data from GitHub
# =============================================================================

log_info "Downloading real Canadian regulatory data from Justice Canada..."

# Check if repo already exists with valid .git directory
if [ -d "$STAGING_DIR/.git" ]; then
    log_info "Repository already exists. Pulling latest changes..."
    cd "$STAGING_DIR"
    git pull origin main || git pull origin master
    cd - > /dev/null
else
    # If directory exists but no .git, remove it first
    if [ -d "$STAGING_DIR" ]; then
        log_warning "Staging directory exists but is not a git repo. Removing..."
        rm -rf "$STAGING_DIR"
    fi
    
    # Create fresh staging directory
    mkdir -p "$STAGING_DIR"
    
    log_info "Cloning repository (this may take a few minutes)..."
    git clone --depth 1 "$REPO_URL" "$STAGING_DIR"
fi

# Count XML files
XML_COUNT=$(find "$STAGING_DIR" -name "*.xml" -type f | wc -l)
log_success "Downloaded $XML_COUNT XML files"

if [ "$XML_COUNT" -lt 100 ]; then
    log_warning "Expected more XML files. Found only $XML_COUNT files."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# =============================================================================
# Step 3: Backup Current Sample Data (Optional)
# =============================================================================

log_info "Backing up current sample data..."

if [ -d "$TARGET_DIR" ]; then
    if [ -d "$BACKUP_DIR" ]; then
        log_warning "Backup directory already exists. Removing old backup..."
        rm -rf "$BACKUP_DIR"
    fi
    mv "$TARGET_DIR" "$BACKUP_DIR"
    log_success "Sample data backed up to $BACKUP_DIR"
else
    log_info "No existing data to backup"
fi

# Create fresh target directory
mkdir -p "$TARGET_DIR"

# =============================================================================
# Step 4: Copy XML Files to Target Directory (English & French)
# =============================================================================

log_info "Copying XML files to target directory..."

# Create subdirectories for each language
mkdir -p "$TARGET_DIR/en"
mkdir -p "$TARGET_DIR/fr"

# Copy English files from eng/acts directory
if [ -d "$STAGING_DIR/eng/acts" ]; then
    cp "$STAGING_DIR/eng/acts"/*.xml "$TARGET_DIR/en/" 2>/dev/null || {
        log_warning "No English XML files found in $STAGING_DIR/eng/acts"
    }
    EN_COUNT=$(ls -1 "$TARGET_DIR/en"/*.xml 2>/dev/null | wc -l)
    log_success "Copied $EN_COUNT English regulation XML files"
else
    log_warning "Directory $STAGING_DIR/eng/acts not found!"
fi

# Copy French files from fra/lois directory (not TOPS index files)
if [ -d "$STAGING_DIR/fra/lois" ]; then
    cp "$STAGING_DIR/fra/lois"/*.xml "$TARGET_DIR/fr/" 2>/dev/null || {
        log_warning "No French XML files found in $STAGING_DIR/fra/lois"
    }
    FR_COUNT=$(ls -1 "$TARGET_DIR/fr"/*.xml 2>/dev/null | wc -l)
    log_success "Copied $FR_COUNT French regulation XML files"
else
    log_warning "Directory $STAGING_DIR/fra/lois not found!"
fi

COPIED_COUNT=$((EN_COUNT + FR_COUNT))

if [ "$COPIED_COUNT" -eq 0 ]; then
    log_error "No XML files were copied!"
    log_error "The repository structure may have changed."
    exit 1
fi

log_success "Total: $COPIED_COUNT regulation files ($EN_COUNT English + $FR_COUNT French)"

# =============================================================================
# Step 5: Database Backup (Recommended)
# =============================================================================

log_info "Creating database backups..."

# Backup PostgreSQL
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
POSTGRES_BACKUP="backend/data/backups/postgres_backup_${BACKUP_DATE}.sql"
mkdir -p backend/data/backups

log_info "Backing up PostgreSQL database..."
docker compose exec -T postgres pg_dump -U postgres regulatory > "$POSTGRES_BACKUP" 2>/dev/null || {
    log_warning "PostgreSQL backup failed (this is okay if database is empty)"
}

log_success "Database backups created (if applicable)"

# =============================================================================
# Step 6: Clear Existing Databases
# =============================================================================

log_warning "About to clear all databases (PostgreSQL, Neo4j, Elasticsearch)"
log_warning "This will delete all existing regulatory data!"
read -p "Are you sure you want to continue? (yes/N) " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_info "Operation cancelled by user"
    exit 0
fi

log_info "Clearing PostgreSQL tables..."
docker compose exec -T backend python -c "
from database import SessionLocal
from models.models import Regulation, Section, Amendment, Citation
db = SessionLocal()
try:
    db.query(Citation).delete()
    db.query(Amendment).delete()
    db.query(Section).delete()
    db.query(Regulation).delete()
    db.commit()
    print('✅ PostgreSQL cleared successfully')
except Exception as e:
    print(f'❌ Error clearing PostgreSQL: {e}')
    db.rollback()
finally:
    db.close()
" || log_error "Failed to clear PostgreSQL"

log_info "Clearing Neo4j graph..."
docker compose exec -T backend python -c "
from utils.neo4j_client import Neo4jClient
try:
    client = Neo4jClient()
    client.connect()
    client.execute_write('MATCH (n) DETACH DELETE n')
    client.close()
    print('✅ Neo4j graph cleared successfully')
except Exception as e:
    print(f'❌ Error clearing Neo4j: {e}')
" || log_error "Failed to clear Neo4j"

log_info "Clearing Elasticsearch index..."
curl -X DELETE "localhost:9200/regulatory_documents" 2>/dev/null || log_warning "Elasticsearch index may not exist"
curl -X PUT "localhost:9200/regulatory_documents" \
     -H 'Content-Type: application/json' \
     -d @backend/config/elasticsearch_mappings.json 2>/dev/null || log_error "Failed to recreate Elasticsearch index"

log_success "All databases cleared"

# =============================================================================
# Step 7: Run Data Ingestion Pipeline
# =============================================================================

log_info "Starting data ingestion pipeline..."
log_info "This may take 1-2 hours for 500+ regulations..."

INGESTION_CMD="python -m ingestion.data_pipeline data/regulations/canadian_laws --validate --force"

if [ "$LIMIT" -gt 0 ]; then
    INGESTION_CMD="$INGESTION_CMD --limit $LIMIT"
    log_info "Processing up to $LIMIT files with force re-ingestion..."
else
    log_info "Processing all files with force re-ingestion..."
fi

# Run ingestion
docker compose exec backend $INGESTION_CMD || {
    log_error "Data ingestion failed!"
    log_info "You can restore backup data by running:"
    log_info "  mv $BACKUP_DIR $TARGET_DIR"
    exit 1
}

log_success "Data ingestion completed"

# =============================================================================
# Step 8: Verify Data Integrity
# =============================================================================

log_info "Verifying data integrity..."

log_info "Checking API health..."
HEALTH_CHECK=$(curl -s http://localhost:8000/health/all | jq -r '.status' 2>/dev/null || echo "unknown")

if [ "$HEALTH_CHECK" = "healthy" ]; then
    log_success "API health check passed"
else
    log_warning "API health check returned: $HEALTH_CHECK"
fi

log_info "Running graph verification..."
docker compose exec backend python scripts/verify_graph.py || log_warning "Graph verification had warnings"

log_info "Testing search functionality..."
SEARCH_TEST=$(curl -s -X POST "http://localhost:8000/api/search/keyword" \
     -H "Content-Type: application/json" \
     -d '{"query": "employment insurance", "size": 5}' | jq -r '.results | length' 2>/dev/null || echo "0")

if [ "$SEARCH_TEST" -gt 0 ]; then
    log_success "Search is working ($SEARCH_TEST results found)"
else
    log_warning "Search test returned no results"
fi

# =============================================================================
# Step 9: Summary
# =============================================================================

echo ""
echo "============================================================"
log_success "Real Canadian Data Ingestion Complete!"
echo "============================================================"
echo ""
log_info "Summary:"
echo "  - Source: Justice Canada GitHub (laws-lois-xml)"
echo "  - XML Files Downloaded: $XML_COUNT"
echo "  - Files Copied: $COPIED_COUNT"
echo "  - Ingestion Limit: ${LIMIT:-All files}"
echo "  - Backup Location: $BACKUP_DIR"
echo "  - PostgreSQL Backup: $POSTGRES_BACKUP"
echo ""
log_info "Next Steps:"
echo "  1. Test search at: http://localhost:5173"
echo "  2. Test API at: http://localhost:8000/docs"
echo "  3. Check Neo4j at: http://localhost:7474"
echo "  4. Run full test suite: docker compose exec backend pytest"
echo ""
log_info "To restore sample data (if needed):"
echo "  mv $BACKUP_DIR $TARGET_DIR"
echo "  docker compose exec backend python -m ingestion.data_pipeline data/regulations/canadian_laws --limit 100 --validate"
echo ""
log_success "All done! 🎉"
