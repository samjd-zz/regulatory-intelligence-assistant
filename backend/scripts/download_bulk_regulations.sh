#!/bin/bash

# Download and Ingest SOR/DORS Regulations in Chunks
# Attempts to download the top 5000 most recent regulations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/../data/regulations/canadian_laws"
EN_REGS_DIR="$DATA_DIR/en-regs"
FR_REGS_DIR="$DATA_DIR/fr-regs"

# Configuration
CHUNK_SIZE=100
MAX_REGULATIONS=5000
START_YEAR=2000
END_YEAR=2025
MAX_NUM_PER_YEAR=999

echo "================================================================================"
echo "Bulk SOR/DORS Regulations Download (Target: ${MAX_REGULATIONS})"
echo "================================================================================"
echo ""
echo "Configuration:"
echo "  Years: ${START_YEAR}-${END_YEAR}"
echo "  Max per year: ${MAX_NUM_PER_YEAR}"
echo "  Chunk size: ${CHUNK_SIZE}"
echo "  Target total: ${MAX_REGULATIONS}"
echo ""
echo "NOTE: This will attempt to download regulations from recent years."
echo "      Not all SOR numbers exist - failed downloads are normal."
echo ""

# Create directories
mkdir -p "$EN_REGS_DIR"
mkdir -p "$FR_REGS_DIR"

# Track statistics
DOWNLOAD_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0
CHUNK_NUM=0

# Progress file
PROGRESS_FILE="$SCRIPT_DIR/.download_progress"

# Function to ingest current chunk
ingest_chunk() {
    local chunk_num=$1
    echo ""
    echo "================================================================================"
    echo "Ingesting Chunk ${chunk_num}"
    echo "================================================================================"
    
    cd "$SCRIPT_DIR/../.."
    if docker compose exec -T backend python scripts/ingest_regulations.py; then
        echo "✓ Chunk ${chunk_num} ingested successfully"
        return 0
    else
        echo "✗ Chunk ${chunk_num} ingestion failed"
        return 1
    fi
}

# Function to download regulations for a specific year
download_year_range() {
    local year=$1
    local start_num=$2
    local end_num=$3
    
    # Iterate from high to low (most recent regulations have higher numbers)
    for num in $(seq $start_num -1 $end_num); do
        # Check if we've hit the target
        if [ $DOWNLOAD_COUNT -ge $MAX_REGULATIONS ]; then
            echo "✓ Reached target of ${MAX_REGULATIONS} regulations"
            return 0
        fi
        
        # Show progress every 50 attempts
        if [ $((num % 50)) -eq 0 ]; then
            echo -n "."
        fi
        
        # Format: SOR-YYYY-NNN (3 digits) for English, DORS-YYYY-NNN for French
        SOR_NUM=$(printf "SOR-%d-%d" $year $num)
        DORS_NUM=$(printf "DORS-%d-%d" $year $num)
        EN_FILENAME="${SOR_NUM}.xml"
        FR_FILENAME="${DORS_NUM}.xml"
        EN_FILEPATH="$EN_REGS_DIR/$EN_FILENAME"
        FR_FILEPATH="$FR_REGS_DIR/$FR_FILENAME"
        
        # Check if English already exists
        if [ -f "$EN_FILEPATH" ]; then
            echo ""  # New line after dots
            echo "Found existing: ${SOR_NUM}"
            SKIP_COUNT=$((SKIP_COUNT + 1))
            # Still try French if English exists
            if [ ! -f "$FR_FILEPATH" ]; then
                FR_URL="https://laws-lois.justice.gc.ca/fra/XML/${DORS_NUM}.xml"
                echo "  Trying: $FR_URL"
                if curl -L -f -s "$FR_URL" -o "$FR_FILEPATH" 2>/dev/null; then
                    FR_SIZE=$(du -h "$FR_FILEPATH" | cut -f1)
                    echo "  └─ ${DORS_NUM} ($FR_SIZE)"
                else
                    echo "  └─ FR not available (404)"
                    rm -f "$FR_FILEPATH"
                fi
            else
                echo "  └─ FR already exists"
            fi
            continue
        fi
        
        # Try to download English
        EN_URL="https://laws-lois.justice.gc.ca/eng/XML/${SOR_NUM}.xml"
        
        if curl -L -f -s "$EN_URL" -o "$EN_FILEPATH" 2>/dev/null; then
            echo ""  # New line after dots
            SIZE=$(du -h "$EN_FILEPATH" | cut -f1)
            echo "✓ ${SOR_NUM} ($SIZE)"
            DOWNLOAD_COUNT=$((DOWNLOAD_COUNT + 1))
            
            # Also download French version
            FR_URL="https://laws-lois.justice.gc.ca/fra/XML/${DORS_NUM}.xml"
            if curl -L -f -s "$FR_URL" -o "$FR_FILEPATH" 2>/dev/null; then
                FR_SIZE=$(du -h "$FR_FILEPATH" | cut -f1)
                echo "  └─ ${DORS_NUM} ($FR_SIZE)"
            else
                rm -f "$FR_FILEPATH"
            fi
            
            # Check if chunk is complete - auto-ingest in background
            if [ $((DOWNLOAD_COUNT % CHUNK_SIZE)) -eq 0 ]; then
                CHUNK_NUM=$((CHUNK_NUM + 1))
                echo ""
                echo "════════════════════════════════════════════════════════════════════════════════"
                echo "Chunk ${CHUNK_NUM} Complete (${DOWNLOAD_COUNT} total downloaded)"
                echo "════════════════════════════════════════════════════════════════════════════════"
                
                # Auto-ingest in background
                ingest_chunk $CHUNK_NUM
                
                echo "  → Continuing downloads while ingestion runs..."
                echo ""
            fi
        else
            rm -f "$EN_FILEPATH"  # Remove failed download
            FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
    done
    
    echo ""  # New line after progress dots
    return 0
}

echo "Starting downloads (working backwards from ${END_YEAR})..."
echo "English directory: $EN_REGS_DIR"
echo "French directory: $FR_REGS_DIR"
echo ""

# Sanity check - show existing file count
EN_COUNT=$(find "$EN_REGS_DIR" -name "*.xml" 2>/dev/null | wc -l)
FR_COUNT=$(find "$FR_REGS_DIR" -name "*.xml" 2>/dev/null | wc -l)
echo "Existing files: ${EN_COUNT} English, ${FR_COUNT} French"
echo ""

# Work backwards from most recent year
for year in $(seq $END_YEAR -1 $START_YEAR); do
    echo "Processing ${year}..."
    
    if ! download_year_range $year $MAX_NUM_PER_YEAR 1; then
        # User quit
        break
    fi
    
    # Check if we've hit target
    if [ $DOWNLOAD_COUNT -ge $MAX_REGULATIONS ]; then
        break
    fi
done

echo ""
echo "================================================================================"
echo "Download Complete - Waiting for Ingestions to Finish"
echo "================================================================================"
echo "  Downloaded: ${DOWNLOAD_COUNT} files"
echo "  Skipped: ${SKIP_COUNT} files (already exist)"
echo "  Failed: ${FAIL_COUNT} attempts"
echo "  Chunks processed: ${CHUNK_NUM}"
echo "  Active ingestion processes: ${#INGESTION_PIDS[@]}"
echo "  Location: ${EN_REGS_DIR}"
echo "================================================================================"
echo ""

# Wait for all background ingestion processes to complete
if [ ${#INGESTION_PIDS[@]} -gt 0 ]; then
    echo "Waiting for ${#INGESTION_PIDS[@]} ingestion process(es) to complete..."
    for pid in "${INGESTION_PIDS[@]}"; do
        wait $pid
        echo "  ✓ Process $pid completed"
    done
    echo ""
    echo "All ingestions complete!"
    echo ""
    
    # Show ingestion status
    if [ -f "/tmp/ingest_status.log" ]; then
        echo "Ingestion Summary:"
        cat "/tmp/ingest_status.log"
        rm "/tmp/ingest_status.log"
    fi
fi

# Final statistics
TOTAL_FILES=$(find "$EN_REGS_DIR" -name "*.xml" | wc -l)
echo ""
echo "================================================================================"
echo "✓ Bulk Download & Ingestion Complete"
echo "================================================================================"
echo "  Total regulation files: ${TOTAL_FILES}"
echo "  Check your database for updated counts"
echo "================================================================================"

# Clean up progress file
rm -f "$PROGRESS_FILE"
