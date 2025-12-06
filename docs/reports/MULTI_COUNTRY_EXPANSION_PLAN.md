# Multi-Country Support Assessment

## Current State: ❌ Canada-Only System

The Regulatory Intelligence Assistant is currently **NOT multi-country**. It's specifically designed and hardcoded for Canadian regulations only.

---

## What IS Multi-Country Ready

### ✅ 1. Database Schema (PostgreSQL)

The database models are flexible and ready for multi-country:

```python
# backend/models/models.py
class Regulation(Base):
    jurisdiction = Column(String(100), nullable=False, index=True)  # ✅ Can store any jurisdiction
    language = Column(String(10), nullable=False, default="en", index=True)  # ✅ Any language
    authority = Column(String(255), nullable=True)  # ✅ Any country's authority
    extra_metadata = Column(JSON, default=dict)  # ✅ Flexible for country-specific fields
```

**Capability:** Can store regulations from any country simply by changing the `jurisdiction` value.

### ✅ 2. Neo4j Graph Schema

The graph schema is country-agnostic:

- Node types (`Legislation`, `Section`, `Regulation`, `Policy`, `Program`) work for any country
- Relationships (`HAS_SECTION`, `REFERENCES`, `IMPLEMENTS`) are universal
- `jurisdiction` property on nodes can hold any country/region

---

## What is Canada-Specific (Hardcoded)

### ❌ 1. NLP Terminology (`legal_nlp.py`)

All entity extraction is Canadian-only:

```python
PERSON_TYPES = {
    "citizen": ["canadian citizen", "citizen of canada"],
    "permanent_resident": ["permanent resident", "pr", "landed immigrant"],
    "temporary_resident": ["temporary resident", "temporary foreign worker", "tfr"],
    "indigenous_person": ["first nations", "métis", "inuit"],  # 🇨🇦 Canada-specific
    # ...
}

PROGRAMS = {
    "employment_insurance": ["employment insurance", "ei"],  # 🇨🇦 Canadian program
    "canada_pension_plan": ["canada pension plan", "cpp"],  # 🇨🇦 Canadian program
    "old_age_security": ["old age security", "oas"],  # 🇨🇦 Canada-specific
    # ...
}

JURISDICTIONS = {
    "federal": ["federal", "canada", "government of canada"],  # 🇨🇦 Canada only
    "ontario": ["ontario", "on"],  # 🇨🇦 Canadian province
    "quebec": ["quebec", "qc"],  # 🇨🇦 Canadian province
    # No other countries!
}
```

**Impact:** Entity extraction won't recognize programs, person types, or jurisdictions from other countries.

### ❌ 2. Program Mappings (`program_mappings.py`)

All program detection is Canadian federal programs only:

```python
FEDERAL_PROGRAMS = {
    'employment_insurance': { ... },  # 🇨🇦 EI
    'canada_pension_plan': { ... },  # 🇨🇦 CPP
    'old_age_security': { ... },  # 🇨🇦 OAS
    'immigration': { ... },  # 🇨🇦 Canadian immigration
    # No US Social Security, UK NHS, etc.
}

JURISDICTION_KEYWORDS = {
    'federal': ['canada', 'federal', 'parliament of canada'],  # 🇨🇦 Only Canada
    'provincial': ['ontario', 'quebec', 'british columbia'],  # 🇨🇦 Only Canadian provinces
    # No US states, UK counties, etc.
}
```

**Impact:** Program detection and jurisdiction classification won't work for other countries.

### ❌ 3. XML Parser (`canadian_law_xml_parser.py`)

The ingestion pipeline is hardcoded for Canadian Justice Laws XML format:

```python
class CanadianLawXMLParser:
    """
    Parser for Canadian Justice Laws XML format.
    Handles the structure from the Open Canada dataset:
    https://open.canada.ca/data/en/dataset/...
    """
    def _parse_statute(self, root: ET.Element) -> ParsedRegulation:
        # Hardcoded to parse:
        # - Canadian Chapter notation (S.C., R.S.C., S.O.)
        # - Canadian Act structure (Identification, Body, Amendments)
        jurisdiction='federal',  # 🇨🇦 Hardcoded!
```

**Impact:** Cannot ingest legal documents from other countries without writing new parsers.

### ❌ 4. Query Parser Intent Patterns

Query intent detection assumes Canadian context:

```python
# backend/services/query_parser.py
INTENT_PATTERNS = {
    QueryIntent.ELIGIBILITY: [
        r'\b(eligible|eligibility|qualify|qualifies)\b',  # Generic
        r'\b(can.*apply|may.*apply)\b',  # Generic
        # But trained/tested only on Canadian programs
    ]
}
```

**Impact:** Works generically but has no country-specific tuning for other legal systems.

---

## Frontend

### ✅ Multi-Language Support

The frontend already supports multiple languages (English/French):

```typescript
// frontend/src/i18n.ts
// frontend/src/locales/en/translation.json
// frontend/src/locales/fr/translation.json
```

**Capability:** Easy to add Spanish, German, etc. for other countries.

### ⚠️ UI Filters

Filter components may need country-specific jurisdictions:

```typescript
// frontend/src/components/search/FilterPanel.tsx
// Currently shows: federal, provincial, municipal (Canadian structure)
```

---

## How to Make It Multi-Country

### Option 1: Configuration-Based Approach (Recommended)

```python
# New file: backend/config/country_config.py
COUNTRY_CONFIGS = {
    'canada': {
        'jurisdictions': ['federal', 'provincial', 'municipal'],
        'programs': CANADIAN_PROGRAMS,
        'person_types': CANADIAN_PERSON_TYPES,
        'parser_class': CanadianLawXMLParser,
    },
    'usa': {
        'jurisdictions': ['federal', 'state', 'local'],
        'programs': USA_PROGRAMS,  # Social Security, Medicare, etc.
        'person_types': USA_PERSON_TYPES,  # US citizen, green card holder, etc.
        'parser_class': USLawParser,
    },
    'uk': {
        'jurisdictions': ['national', 'devolved'],
        'programs': UK_PROGRAMS,  # NHS, Universal Credit, etc.
        'person_types': UK_PERSON_TYPES,
        'parser_class': UKLawParser,
    }
}
```

### Option 2: Database-Driven Configuration

Create a `countries` table with:
- Country code (ISO 3166)
- Legal terminology (JSON)
- Program definitions (JSON)
- Jurisdiction structure (JSON)

---

## Required Changes

### 1. Database
✅ Already ready (add country filter to queries)

### 2. NLP Service
Refactor to load terminology by country:

```python
def __init__(self, country_code: str = 'canada'):
    self.terminology = load_country_terminology(country_code)
```

### 3. Parsers
Create abstract base class:

```python
class BaseLegalDocumentParser(ABC):
    @abstractmethod
    def parse_file(self, path: str) -> ParsedRegulation:
        pass
```

### 4. Search/RAG
Add country context to queries:

```python
def search(self, query: str, country: str = 'canada', jurisdiction: str = None):
    filters = {'country': country}
    if jurisdiction:
        filters['jurisdiction'] = jurisdiction
    return self._search_with_filters(query, filters)
```

### 5. Frontend
Add country selector dropdown

---

## Effort Estimation

| Component | Effort | Priority |
|-----------|--------|----------|
| Country config framework | 3-5 days | HIGH |
| USA/UK terminology | 2-3 days per country | MEDIUM |
| Additional XML parsers | 5-7 days per country | HIGH |
| Database migrations | 1 day | HIGH |
| Frontend country selector | 2 days | MEDIUM |
| Testing & validation | 3-5 days | HIGH |

**Total:** ~3-4 weeks for USA support, then ~2 weeks per additional country.

---

## Recommendation

### For G7 GovAI Challenge
**Keep Canada-only focus for now** (deadline driven).

### For Production
Implement multi-country as Phase 2:

1. **Start with USA** (similar legal system, large market)
2. **Add UK** (commonwealth legal tradition)
3. **Then other G7 countries** (France, Germany, Italy, Japan)

---

## Next on the Menu

### 🇺🇸 US Federal + 50 State Systems
- **Federal level:** CFR (Code of Federal Regulations), USC (United States Code)
- **State level:** All 50 states' statutes and administrative codes
- **Data source:** GovInfo.gov, State legislative websites
- **Challenge:** Federalism complexity (federal vs state jurisdiction)

### 🇬🇧 UK (750+ Years of Legislation since 1267)
- **Source:** legislation.gov.uk
- **Coverage:** Acts of Parliament, Statutory Instruments, UK Public General Acts
- **Historical depth:** Legislation dating back to Statute of Marlborough (1267)
- **Challenge:** Historical consolidation and amendments

### 🇫🇷 French Civil Law
- **Source:** Légifrance (legifrance.gouv.fr)
- **Coverage:** French codes (Civil Code, Penal Code, Labor Code, etc.)
- **Legal system:** Civil law tradition (different from common law)
- **Challenge:** French language processing, civil law structure

### 🇩🇪 German Federal Code
- **Source:** gesetze-im-internet.de
- **Coverage:** Federal laws (Bundesrecht)
- **States:** 16 Länder (state-level laws)
- **Challenge:** German language, federal structure, comprehensive codification

### 🇪🇺 EU Directives (24 Languages)
- **Source:** EUR-Lex (eur-lex.europa.eu)
- **Coverage:** EU regulations, directives, decisions
- **Languages:** All 24 official EU languages
- **Challenge:** Multi-lingual corpus, supranational law, cross-country applicability

### 🇮🇹 Italian Legal System
- **Source:** Normattiva (normattiva.it)
- **Coverage:** Italian Republic's legislation
- **Challenge:** Italian language, civil law tradition

### 🇯🇵 Japanese Law
- **Source:** e-Gov Laws and Regulations (elaws.e-gov.go.jp)
- **Coverage:** Japanese statutes and regulations
- **Language:** Japanese (requires specialized NLP)
- **Challenge:** Language barrier, unique legal structure

---

## Key Insight

**The architecture is well-positioned for multi-country expansion—most components just need configuration, not redesign.**

The system was built with the right abstractions:
- ✅ Flexible database schema
- ✅ Graph structure independent of country
- ✅ Modular NLP service
- ✅ Pluggable parser architecture

**Main work:** Creating country-specific configurations and parsers, not refactoring core architecture.
