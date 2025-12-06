#!/bin/bash
#
# Data Summary Script
# Provides a comprehensive overview of data across all services:
# - PostgreSQL (regulations, sections, citations)
# - Neo4j (nodes, relationships)
# - Elasticsearch (indexed documents)
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Container names (adjust if your setup is different)
POSTGRES_CONTAINER="regulatory-postgres"
NEO4J_CONTAINER="regulatory-neo4j"
ELASTICSEARCH_CONTAINER="regulatory-elasticsearch"

echo ""
echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║   REGULATORY INTELLIGENCE ASSISTANT - DATA SUMMARY REPORT    ║${NC}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Generated: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
echo ""

# Function to print section header
print_header() {
    echo ""
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${BLUE}  $1${NC}"
    echo -e "${BOLD}${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to check if container is running
check_container() {
    local container=$1
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        echo -e "${RED}✗ Container not running: $container${NC}"
        return 1
    fi
    echo -e "${GREEN}✓ Container running: $container${NC}"
    return 0
}

# Check container status
print_header "DOCKER CONTAINER STATUS"
check_container "$POSTGRES_CONTAINER" || echo -e "${YELLOW}  Note: PostgreSQL container not found with expected name${NC}"
check_container "$NEO4J_CONTAINER" || echo -e "${YELLOW}  Note: Neo4j container not found with expected name${NC}"
check_container "$ELASTICSEARCH_CONTAINER" || echo -e "${YELLOW}  Note: Elasticsearch container not found with expected name${NC}"

# =============================================================================
# POSTGRESQL STATISTICS
# =============================================================================
print_header "POSTGRESQL DATABASE"

echo -e "${CYAN}Querying PostgreSQL...${NC}"

# Get database statistics
POSTGRES_STATS=$(docker exec $POSTGRES_CONTAINER psql -U postgres -d regulatory_db -t -A -c "
SELECT 
    (SELECT COUNT(*) FROM regulations) as regulations,
    (SELECT COUNT(*) FROM sections) as sections,
    (SELECT COUNT(*) FROM citations) as citations,
    (SELECT COUNT(*) FROM regulations WHERE language='en') as english_regs,
    (SELECT COUNT(*) FROM regulations WHERE language='fr') as french_regs,
    (SELECT COUNT(*) FROM regulations WHERE status='active') as active_regs;
" 2>/dev/null || echo "0|0|0|0|0|0")

IFS='|' read -r TOTAL_REGS TOTAL_SECTIONS TOTAL_CITATIONS ENG_REGS FR_REGS ACTIVE_REGS <<< "$POSTGRES_STATS"

echo ""
echo -e "  ${BOLD}Regulations:${NC}"
echo -e "    Total:           ${GREEN}${TOTAL_REGS}${NC}"
echo -e "    English:         ${CYAN}${ENG_REGS}${NC}"
echo -e "    French:          ${CYAN}${FR_REGS}${NC}"
echo -e "    Active:          ${GREEN}${ACTIVE_REGS}${NC}"
echo ""
echo -e "  ${BOLD}Sections:${NC}          ${GREEN}${TOTAL_SECTIONS}${NC}"
echo -e "  ${BOLD}Citations:${NC}         ${GREEN}${TOTAL_CITATIONS}${NC}"

# Get top jurisdictions
echo ""
echo -e "  ${BOLD}Top Jurisdictions:${NC}"
docker exec $POSTGRES_CONTAINER psql -U postgres -d regulatory_db -t -c "
SELECT 
    jurisdiction, 
    COUNT(*) as count 
FROM regulations 
GROUP BY jurisdiction 
ORDER BY count DESC 
LIMIT 5;
" 2>/dev/null | while read -r line; do
    if [[ ! -z "$line" ]]; then
        echo -e "    $line"
    fi
done

# =============================================================================
# NEO4J GRAPH DATABASE
# =============================================================================
print_header "NEO4J KNOWLEDGE GRAPH"

echo -e "${CYAN}Querying Neo4j...${NC}"

# Get node counts by label
echo ""
echo -e "  ${BOLD}Nodes by Type:${NC}"

NEO4J_PASS=$(grep NEO4J_PASSWORD backend/.env 2>/dev/null | cut -d'=' -f2 || echo "password123")

docker exec $NEO4J_CONTAINER cypher-shell -u neo4j -p "$NEO4J_PASS" "
MATCH (n)
RETURN labels(n)[0] as label, count(n) as count
ORDER BY count DESC
LIMIT 10;
" 2>/dev/null | tail -n +2 | while IFS=', ' read -r label count; do
    label=$(echo "$label" | tr -d '"' | xargs)
    count=$(echo "$count" | xargs)
    if [[ ! -z "$label" ]] && [[ "$label" != "label" ]] && [[ ! -z "$count" ]]; then
        printf "    %-20s ${GREEN}%s${NC}\n" "$label:" "$count"
    fi
done

# Get total node count
TOTAL_NODES=$(docker exec $NEO4J_CONTAINER cypher-shell -u neo4j -p "$NEO4J_PASS" "
MATCH (n) RETURN count(n) as total;
" 2>/dev/null | grep -E '^[0-9]+$' || echo "0")

echo ""
echo -e "  ${BOLD}Total Nodes:${NC}       ${GREEN}${TOTAL_NODES}${NC}"

# Get relationship counts
echo ""
echo -e "  ${BOLD}Relationships by Type:${NC}"

docker exec $NEO4J_CONTAINER cypher-shell -u neo4j -p "$NEO4J_PASS" "
MATCH ()-[r]->()
RETURN type(r) as type, count(r) as count
ORDER BY count DESC
LIMIT 10;
" 2>/dev/null | tail -n +2 | while IFS=', ' read -r rel_type count; do
    rel_type=$(echo "$rel_type" | tr -d '"' | xargs)
    count=$(echo "$count" | xargs)
    if [[ ! -z "$rel_type" ]] && [[ "$rel_type" != "type" ]] && [[ ! -z "$count" ]]; then
        printf "    %-20s ${GREEN}%s${NC}\n" "$rel_type:" "$count"
    fi
done

# Get total relationship count
TOTAL_RELS=$(docker exec $NEO4J_CONTAINER cypher-shell -u neo4j -p "$NEO4J_PASS" "
MATCH ()-[r]->() RETURN count(r) as total;
" 2>/dev/null | grep -E '^[0-9]+$' || echo "0")

echo ""
echo -e "  ${BOLD}Total Relationships:${NC} ${GREEN}${TOTAL_RELS}${NC}"

# =============================================================================
# ELASTICSEARCH INDEX
# =============================================================================
print_header "ELASTICSEARCH SEARCH INDEX"

echo -e "${CYAN}Querying Elasticsearch...${NC}"

# Get index statistics
ES_STATS=$(docker exec $ELASTICSEARCH_CONTAINER curl -s -X GET "localhost:9200/regulatory_documents/_stats" 2>/dev/null)

if [[ ! -z "$ES_STATS" ]]; then
    TOTAL_DOCS=$(echo "$ES_STATS" | jq -r '._all.primaries.docs.count // 0' 2>/dev/null)
    INDEX_SIZE=$(echo "$ES_STATS" | jq -r '._all.primaries.store.size_in_bytes // 0' 2>/dev/null)
    
    echo ""
    echo -e "  ${BOLD}Index:${NC}             regulatory_documents"
    echo -e "  ${BOLD}Total Documents:${NC}   ${GREEN}${TOTAL_DOCS}${NC}"
    echo -e "  ${BOLD}Index Size:${NC}        ${CYAN}${INDEX_SIZE}${NC}"
    
    # Get document counts by type
    echo ""
    echo -e "  ${BOLD}Documents by Type:${NC}"
    
    REG_COUNT=$(docker exec $ELASTICSEARCH_CONTAINER curl -s -X GET "localhost:9200/regulatory_documents/_count" \
        -H 'Content-Type: application/json' \
        -d '{"query":{"term":{"document_type":"regulation"}}}' 2>/dev/null | jq -r '.count' 2>/dev/null || echo "0")
    
    SECT_COUNT=$(docker exec $ELASTICSEARCH_CONTAINER curl -s -X GET "localhost:9200/regulatory_documents/_count" \
        -H 'Content-Type: application/json' \
        -d '{"query":{"term":{"document_type":"section"}}}' 2>/dev/null | jq -r '.count' 2>/dev/null || echo "0")
    
    echo -e "    Regulations:     ${CYAN}${REG_COUNT}${NC}"
    echo -e "    Sections:        ${CYAN}${SECT_COUNT}${NC}"
else
    echo -e "  ${RED}Unable to query Elasticsearch${NC}"
fi

# =============================================================================
# SUMMARY
# =============================================================================
print_header "SUMMARY"

echo ""
echo -e "  ${BOLD}Data Distribution:${NC}"
echo -e "    PostgreSQL:      ${GREEN}${TOTAL_REGS}${NC} regulations, ${GREEN}${TOTAL_SECTIONS}${NC} sections"
echo -e "    Neo4j:           ${GREEN}${TOTAL_NODES}${NC} nodes, ${GREEN}${TOTAL_RELS}${NC} relationships"
echo -e "    Elasticsearch:   ${GREEN}${TOTAL_DOCS}${NC} indexed documents (${GREEN}${REG_COUNT}${NC} regs + ${GREEN}${SECT_COUNT}${NC} sections)"

echo ""
echo -e "  ${BOLD}System Health:${NC}"

# Check if data is consistent
if [[ "$TOTAL_REGS" -gt 0 ]] && [[ "$TOTAL_NODES" -gt 0 ]] && [[ "$TOTAL_DOCS" -gt 0 ]]; then
    echo -e "    ${GREEN}✓ All systems operational${NC}"
    echo -e "    ${GREEN}✓ Data present in all databases${NC}"
else
    echo -e "    ${YELLOW}⚠ Some services may be empty or not fully synced${NC}"
fi

# Check for data consistency between PostgreSQL and Elasticsearch
EXPECTED_ES_DOCS=$((TOTAL_REGS + TOTAL_SECTIONS))
if [[ "$EXPECTED_ES_DOCS" -eq "$TOTAL_DOCS" ]]; then
    echo -e "    ${GREEN}✓ PostgreSQL and Elasticsearch are in sync${NC}"
    echo -e "    ${GREEN}✓ All regulations and sections indexed${NC}"
else
    DIFF=$((EXPECTED_ES_DOCS - TOTAL_DOCS))
    if [[ $DIFF -lt 0 ]]; then
        DIFF=$((-DIFF))
    fi
    echo -e "    ${YELLOW}⚠ Data mismatch: Expected ${EXPECTED_ES_DOCS}, found ${TOTAL_DOCS} (diff: ${DIFF})${NC}"
fi

echo ""
echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${CYAN}║                    END OF DATA SUMMARY                        ║${NC}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
