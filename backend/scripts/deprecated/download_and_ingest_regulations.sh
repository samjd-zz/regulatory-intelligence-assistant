#!/bin/bash

# Download and Ingest Canadian Regulations (SOR/DORS)
# This script downloads priority regulations and ingests them into the system

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data/regulations/canadian_laws"
EN_REGS_DIR="$DATA_DIR/en-regs"
FR_REGS_DIR="$DATA_DIR/fr-regs"

echo "================================================================================"
echo "Canadian Regulations Download and Ingestion (Priority Set)"
echo "================================================================================"
echo ""
echo "NOTE: This downloads a priority subset of ~8 key regulations."
echo "      There are thousands of SOR/DORS regulations available."
echo "      To download all, visit: https://laws-lois.justice.gc.ca/eng/regulations/"
echo ""

# Create directories
mkdir -p "$EN_REGS_DIR"
mkdir -p "$FR_REGS_DIR"

# List of priority regulations to download
declare -a REGULATIONS=(
    "SOR-96-445:Employment Insurance (Fishing) Regulations"
    "SOR-2002-227:Immigration and Refugee Protection Regulations"
    "SOR-78-859:Canada Pension Plan Regulations"
    "SOR-96-521:Old Age Security Regulations"
    "SOR-2018-144:Cannabis Regulations"
    "SOR-86-304:Employment Insurance Regulations"
    "SOR-97-175:Special Import Measures Regulations"
    "SOR-96-433:Employment Insurance (Fishing) Regulations"
)

echo "Step 1: Downloading English Regulations"
echo "================================================================================"
echo ""

DOWNLOAD_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

for reg in "${REGULATIONS[@]}"; do
    IFS=':' read -r SOR_NUM TITLE <<< "$reg"
    FILENAME="${SOR_NUM}.xml"
    FILEPATH="$EN_REGS_DIR/$FILENAME"
    
    # Check if already exists
    if [ -f "$FILEPATH" ]; then
        echo "⊘ Skipping $SOR_NUM (already exists)"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi
    
    echo "⬇ Downloading $SOR_NUM - $TITLE..."
    URL="https://laws-lois.justice.gc.ca/eng/XML/${SOR_NUM}.xml"
    
    if curl -L -f "$URL" -o "$FILEPATH" 2>/dev/null; then
        SIZE=$(du -h "$FILEPATH" | cut -f1)
        echo "  ✓ Downloaded successfully ($SIZE)"
        DOWNLOAD_COUNT=$((DOWNLOAD_COUNT + 1))
    else
        echo "  ✗ Failed to download (URL may not exist)"
        rm -f "$FILEPATH"  # Remove failed download
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
    echo ""
done

echo "================================================================================"
echo "Download Summary:"
echo "  Downloaded: $DOWNLOAD_COUNT files"
echo "  Skipped: $SKIP_COUNT files (already exist)"
echo "  Failed: $FAIL_COUNT files"
echo "  Location: $EN_REGS_DIR"
echo "================================================================================"
echo ""

# Count total XML files
TOTAL_FILES=$(find "$EN_REGS_DIR" -name "*.xml" | wc -l)
echo "Total regulation files available: $TOTAL_FILES"
echo ""

if [ $TOTAL_FILES -eq 0 ]; then
    echo "⚠ No regulation files to ingest. Exiting."
    exit 0
fi

echo "================================================================================"
echo "Step 2: Ingesting Regulations into System"
echo "================================================================================"
echo ""
echo "This will ingest regulations into:"
echo "  • PostgreSQL (regulations, sections, amendments, citations)"
echo "  • Neo4j (knowledge graph with Regulation nodes)"
echo "  • Elasticsearch (searchable documents with node_type='Regulation')"
echo ""
read -p "Proceed with ingestion? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Starting ingestion..."
    
    # Run ingestion inside Docker container
    cd "$SCRIPT_DIR/../.."
    docker compose exec backend python scripts/ingest_regulations.py
    
    echo ""
    echo "================================================================================"
    echo "✓ Download and Ingestion Complete!"
    echo "================================================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Query regulations in search API"
    echo "  2. View knowledge graph in Neo4j browser"
    echo "  3. Run Elasticsearch queries with node_type='Regulation'"
    echo ""
else
    echo ""
    echo "Ingestion cancelled. Files downloaded to: $EN_REGS_DIR"
    echo "Run manually with: docker compose exec backend python scripts/ingest_regulations.py"
fi
