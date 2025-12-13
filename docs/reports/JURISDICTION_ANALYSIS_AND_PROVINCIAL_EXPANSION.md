# Jurisdiction Analysis and Provincial Law Expansion Plan

**Date**: December 13, 2025  
**Status**: Analysis Complete - Ready for Planning

---

## Executive Summary

**Current State**: ✅ Federal-only data sources  
**Database Support**: ✅ Multi-jurisdiction ready  
**Next Step**: 🔄 Add provincial law sources

---

## 1. Current Jurisdiction Coverage

### Data Source Analysis

**Primary Source**: Justice Canada GitHub Repository
- **URL**: https://github.com/justicecanada/laws-lois-xml
- **Coverage**: All Canadian federal acts and regulations (500+ documents)
- **Format**: XML (Justice Laws Canada schema)
- **Jurisdiction**: Federal only

### Code Analysis

#### XML Parser (canadian_law_xml_parser.py)
```python
# Line 196 - HARDCODED TO FEDERAL
jurisdiction='federal',
```

**Finding**: The jurisdiction is hardcoded to `'federal'` in the `_parse_consolidation()` and `_parse_statute()` methods.

#### Data Pipeline (data_pipeline.py)
```python
# Lines 392-404 - Jurisdiction detection with fallback
detected_jurisdiction = self.program_detector.detect_jurisdiction(
    title=parsed_reg.title,
    content=parsed_reg.full_text[:1000],
    authority=parsed_reg.chapter or ""
)

# Use detected jurisdiction if parsed jurisdiction is missing or generic
final_jurisdiction = parsed_reg.jurisdiction
if not final_jurisdiction or final_jurisdiction == 'unknown':
    final_jurisdiction = detected_jurisdiction
```

**Finding**: The pipeline HAS jurisdiction detection logic, but it only activates if the XML parser returns 'unknown'. Since the parser always returns 'federal', the detection is never used.

#### Program Detector (program_mappings.py)
```python
# Lines 145-185 - Jurisdiction keywords defined
JURISDICTION_KEYWORDS = {
    'federal': [...],
    'provincial': [
        'ontario', 'quebec', 'british columbia', 'alberta',
        'manitoba', 'saskatchewan', 'nova scotia', 'new brunswick',
        'prince edward island', 'newfoundland', 'labrador',
        'provincial', 'legislature'
    ],
    'municipal': [...]
}
```

**Finding**: The infrastructure for multi-jurisdiction detection EXISTS but is not being fully utilized.

---

## 2. Database Model Support

### Regulation Model (models.py)

```python
class Regulation(Base):
    __tablename__ = "regulations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    jurisdiction = Column(String(100), nullable=False, index=True)  # ✅ READY
    authority = Column(String(255), nullable=True)
    # ... other fields
```

**Status**: ✅ **Fully Ready for Multi-Jurisdiction**

- Jurisdiction field is indexed for fast filtering
- String type allows flexible jurisdiction values
- Can support: 'federal', 'ontario', 'quebec', 'british_columbia', etc.

---

## 3. Provincial Law Data Sources

### Research Required

Each Canadian province maintains its own legal database:

#### Ontario
- **Source**: Ontario.ca Laws Website
- **URL**: https://www.ontario.ca/laws
- **Format**: HTML/XML (e-Laws format)
- **Coverage**: Statutes, regulations, and recent bills
- **API**: Limited public API available
- **Estimated Documents**: 500+ statutes, 1,000+ regulations

#### Quebec
- **Source**: Légis Québec
- **URL**: http://legisquebec.gouv.qc.ca
- **Format**: HTML/XML (custom format)
- **Coverage**: Lois et règlements du Québec
- **Language**: French primary, some bilingual
- **Estimated Documents**: 600+ statutes, 2,000+ regulations

#### British Columbia
- **Source**: BC Laws Website
- **URL**: https://www.bclaws.gov.bc.ca
- **Format**: HTML/XML (custom format)
- **Coverage**: Statutes and regulations
- **Estimated Documents**: 400+ statutes, 800+ regulations

#### Alberta
- **Source**: Alberta Queen's Printer
- **URL**: https://www.qp.alberta.ca/laws
- **Format**: HTML/PDF (custom format)
- **Coverage**: Statutes and regulations
- **Estimated Documents**: 350+ statutes, 700+ regulations

#### Other Provinces
Similar databases exist for:
- Manitoba: https://web2.gov.mb.ca/laws/
- Saskatchewan: https://www.canlii.org/en/sk/laws/
- Nova Scotia, New Brunswick, PEI, Newfoundland & Labrador

### Common Challenges

1. **Format Inconsistency**: Each province uses a different XML/HTML schema
2. **No Standard API**: Most provinces don't provide programmatic access
3. **Scraping Required**: May need to build custom scrapers for each province
4. **Update Frequency**: Provinces update at different cadences
5. **Bilingual Content**: Quebec requires French language support

---

## 4. Implementation Plan for Provincial Laws

### Phase 1: Infrastructure Updates (Week 1)

#### 1.1 Update XML Parser
**File**: `backend/ingestion/canadian_law_xml_parser.py`

**Change**:
```python
# BEFORE (Line 196):
jurisdiction='federal',

# AFTER:
jurisdiction=self._detect_jurisdiction_from_metadata(root, title, chapter),
```

**Add Method**:
```python
def _detect_jurisdiction_from_metadata(self, root, title, chapter):
    """Detect jurisdiction from XML metadata, authority, or title."""
    # Check chapter notation (S.C. = federal, S.O. = Ontario, etc.)
    if chapter:
        if chapter.startswith('S.C.') or chapter.startswith('R.S.C.'):
            return 'federal'
        elif chapter.startswith('S.O.') or chapter.startswith('R.S.O.'):
            return 'ontario'
        elif chapter.startswith('S.Q.') or chapter.startswith('R.S.Q.'):
            return 'quebec'
        # ... add other provinces
    
    # Fallback to title-based detection
    title_lower = title.lower()
    if 'ontario' in title_lower:
        return 'ontario'
    elif 'quebec' in title_lower or 'québec' in title_lower:
        return 'quebec'
    # ... add other provinces
    
    # Default to federal for Canadian laws
    return 'federal'
```

#### 1.2 Create Provincial XML Parsers
**New Files**:
- `backend/ingestion/ontario_law_xml_parser.py`
- `backend/ingestion/quebec_law_xml_parser.py`
- `backend/ingestion/bc_law_xml_parser.py`

**Structure** (inherit from base):
```python
class OntarioLawXMLParser(CanadianLawXMLParser):
    """Parser for Ontario e-Laws XML format."""
    
    def __init__(self):
        super().__init__()
        self.default_jurisdiction = 'ontario'
    
    def _parse_statute(self, root):
        # Override with Ontario-specific XML structure
        # e-Laws format differs from federal format
        pass
```

#### 1.3 Update Data Pipeline
**File**: `backend/ingestion/data_pipeline.py`

**Add Parser Selection**:
```python
def _select_parser(self, xml_path: str, jurisdiction: str = None):
    """Select appropriate parser based on jurisdiction or file structure."""
    if jurisdiction == 'ontario':
        return OntarioLawXMLParser()
    elif jurisdiction == 'quebec':
        return QuebecLawXMLParser()
    elif jurisdiction == 'british_columbia':
        return BCLawXMLParser()
    else:
        return CanadianLawXMLParser()  # Federal
```

### Phase 2: Data Acquisition (Week 2)

#### 2.1 Ontario Pilot
**Goal**: Ingest 50 Ontario statutes as proof-of-concept

**Steps**:
1. Identify Ontario e-Laws API/download endpoint
2. Create downloader script: `backend/ingestion/download_ontario_laws.py`
3. Download sample statutes (Employment Standards Act, etc.)
4. Test ingestion pipeline with Ontario data
5. Verify jurisdiction filtering in search

**Success Criteria**:
- 50 Ontario statutes in database
- Jurisdiction = 'ontario' correctly set
- Search can filter by jurisdiction
- Knowledge graph shows provincial-federal relationships

#### 2.2 Web Scraping Strategy
Since most provinces lack APIs:

**Tool**: Scrapy or Beautiful Soup
**Approach**:
1. Build custom scrapers per province
2. Extract statute/regulation metadata
3. Download XML/HTML content
4. Convert to standardized format
5. Feed into ingestion pipeline

### Phase 3: Knowledge Graph Extensions (Week 3)

#### 3.1 Federal-Provincial Relationships
**New Relationship Types**:
- `PROVINCIAL_IMPLEMENTATION_OF` (provincial law implements federal)
- `CONFLICTS_WITH` (jurisdictional conflicts)
- `COMPLEMENTS` (provincial law complements federal)

**Example**:
```cypher
// Ontario Employment Standards Act implements federal Labour Code
MATCH (provincial:Regulation {jurisdiction: 'ontario', title: 'Employment Standards Act'})
MATCH (federal:Regulation {jurisdiction: 'federal', title: 'Canada Labour Code'})
CREATE (provincial)-[:PROVINCIAL_IMPLEMENTATION_OF]->(federal)
```

#### 3.2 Jurisdiction Hierarchy
```
Canada (Federal)
├── Ontario
│   ├── Toronto (Municipal)
│   └── Ottawa (Municipal)
├── Quebec
│   ├── Montreal (Municipal)
│   └── Quebec City (Municipal)
└── British Columbia
    └── Vancouver (Municipal)
```

### Phase 4: UI & Search Updates (Week 4)

#### 4.1 Jurisdiction Filter
**Frontend Update**: `frontend/src/components/search/FilterPanel.tsx`

**Add Dropdown**:
```tsx
<Select onValueChange={(value) => setJurisdiction(value)}>
  <SelectTrigger>
    <SelectValue placeholder="Select Jurisdiction" />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">All Jurisdictions</SelectItem>
    <SelectItem value="federal">Federal</SelectItem>
    <SelectItem value="ontario">Ontario</SelectItem>
    <SelectItem value="quebec">Quebec</SelectItem>
    <SelectItem value="british_columbia">British Columbia</SelectItem>
    {/* ... other provinces */}
  </SelectContent>
</Select>
```

#### 4.2 Search API Update
**Backend**: `backend/routes/search.py`

**Add Jurisdiction Filter**:
```python
@router.post("/keyword")
def search_keyword(
    query: str,
    jurisdiction: Optional[str] = None,  # NEW
    size: int = 10
):
    # Pass jurisdiction to search service
    results = search_service.search(
        query=query,
        filters={'jurisdiction': jurisdiction} if jurisdiction else {},
        size=size
    )
    return results
```

#### 4.3 Province-Specific Programs
Update `backend/config/program_mappings.py`:

```python
PROVINCIAL_PROGRAMS = {
    'ontario': {
        'ontario_works': {...},
        'ontario_disability_support': {...},
        'trillium_benefit': {...}
    },
    'quebec': {
        'quebec_pension_plan': {...},
        'ramq': {...}  # Régie de l'assurance maladie du Québec
    }
}
```

---

## 5. Estimated Effort

### Timeline: 4-6 Weeks for MVP

| Phase | Duration | Resources |
|-------|----------|-----------|
| Infrastructure Updates | 1 week | 1 developer |
| Ontario Pilot | 1 week | 1 developer |
| Knowledge Graph Extensions | 1 week | 1 developer |
| UI & Search Updates | 1 week | 1 frontend, 1 backend |
| Testing & Validation | 2 weeks | Legal expert + QA |

### Data Ingestion Scale

| Jurisdiction | Estimated Documents | Ingestion Time |
|-------------|-------------------|----------------|
| Federal | 500 (✅ Done) | - |
| Ontario | 1,500 | 2-3 hours |
| Quebec | 2,600 | 4-5 hours |
| BC | 1,200 | 2-3 hours |
| Alberta | 1,050 | 2 hours |
| Other Provinces | ~5,000 | 8-10 hours |
| **Total** | **~12,000** | **~20 hours** |

---

## 6. Risks & Mitigation

### Risk 1: Inconsistent Data Formats
**Impact**: High  
**Likelihood**: High  
**Mitigation**: 
- Build format converters for each province
- Create base parser class with province-specific overrides
- Test with sample data before full ingestion

### Risk 2: Legal Accuracy Across Jurisdictions
**Impact**: Critical  
**Likelihood**: Medium  
**Mitigation**:
- Engage legal experts for each province
- Create province-specific test cases
- Validate jurisdictional boundaries in knowledge graph

### Risk 3: Data Freshness
**Impact**: Medium  
**Likelihood**: Medium  
**Mitigation**:
- Set up scheduled scrapers for each province
- Monitor provincial legislative websites for updates
- Implement change detection and notification system

### Risk 4: French Language Support (Quebec)
**Impact**: High  
**Likelihood**: High  
**Mitigation**:
- Already have bilingual support (en/fr in database)
- Test with French content during Quebec pilot
- Ensure NLP models handle French legal terminology

---

## 7. Quick Start: Proof of Concept

### Test with Ontario Employment Standards Act

**Step 1**: Download sample Ontario statute
```bash
# Create Ontario data directory
mkdir -p backend/data/regulations/ontario

# Download (manual or scripted)
# Save as: backend/data/regulations/ontario/employment-standards-act.xml
```

**Step 2**: Update parser temporarily
```python
# In canadian_law_xml_parser.py, line 196:
jurisdiction='ontario',  # TEST CHANGE
```

**Step 3**: Ingest
```bash
docker compose exec backend python -m ingestion.data_pipeline \
  data/regulations/ontario \
  --limit 1
```

**Step 4**: Verify in database
```sql
SELECT id, title, jurisdiction 
FROM regulations 
WHERE jurisdiction = 'ontario';
```

**Step 5**: Test search filter
```bash
curl -X POST "http://localhost:8000/api/search/keyword" \
  -H "Content-Type: application/json" \
  -d '{"query": "employment", "jurisdiction": "ontario", "size": 5}'
```

---

## 8. Recommendations

### Priority Order

1. ✅ **Immediate** (This Sprint)
   - Update XML parser to use dynamic jurisdiction detection
   - Test with manual Ontario statute upload
   - Verify jurisdiction filtering works

2. 🔄 **Short-term** (Next Sprint)
   - Build Ontario data scraper/downloader
   - Ingest 50 Ontario statutes
   - Add jurisdiction filter to UI

3. 📅 **Medium-term** (1-2 Months)
   - Add Quebec, BC, Alberta
   - Build federal-provincial relationship mapping
   - Create province-specific program detection

4. 🎯 **Long-term** (3-6 Months)
   - Complete all 10 provinces + 3 territories
   - Add municipal bylaws for major cities
   - Implement automated update monitoring

### Resource Requirements

**Developers**: 2-3 (1 backend, 1 frontend, 1 data engineer)  
**Legal Experts**: 1 per province (for validation)  
**Timeline**: 6 months for complete coverage  
**Budget**: Estimate $50k-$100k (developer time + legal review)

---

## 9. Conclusion

**Current State**: Your system is **100% federal** data sources with jurisdiction hardcoded to `'federal'`.

**Infrastructure**: ✅ **Ready** - Database model supports multi-jurisdiction with indexed field.

**Next Steps**:
1. Update XML parser to detect jurisdiction dynamically
2. Pilot with Ontario (1,500 documents)
3. Extend to other provinces incrementally
4. Build federal-provincial knowledge graph relationships

**Value Proposition**: Adding provincial laws would increase your regulatory coverage from **~500 documents to ~12,000 documents** (24x increase), making the system far more valuable for Canadian public servants who deal with both federal and provincial regulations daily.

---

**Document Status**: Ready for Review  
**Next Action**: Review with stakeholders and prioritize implementation phases
