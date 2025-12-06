# US Law XML Schema Documentation

## Overview

This document describes the official XML schemas used for United States federal laws and regulations, published by the U.S. Government Publishing Office (GPO). The system uses two primary schemas:

1. **USLM (United States Legislative Markup)** - For the United States Code (USC)
2. **CFRMergedXML** - For the Code of Federal Regulations (CFR)

## 1. USLM Schema (United States Code)

### Schema Information
- **Current Version**: 2.0.5
- **Schema URL**: https://www.govinfo.gov/schemas/xml/uslm/uslm-2.0.5.xsd
- **Namespace**: http://schemas.gpo.gov/xml/uslm
- **Publisher**: U.S. Government Publishing Office (GPO)
- **Maintained By**: Office of the Law Revision Counsel (OLRC)

### Schema Purpose

The USLM schema is designed to model:
- United States Code titles and appendices
- Enrolled Bills
- Public Laws
- Statutes at Large
- Statute Compilations
- Federal Register
- Code of Federal Regulations (alternate format)

### Key Design Principles

1. **Venetian Blind Pattern**: Each element type is defined separately with separate element declarations for maximum reusability
2. **Abstract to Concrete Hierarchy**: Derivation goes from most abstract to most concrete
3. **XHTML Compatibility**: Maximizes consistency with XHTML naming conventions
4. **Metadata in Attributes**: Text content is in element bodies; attributes contain metadata or normalized forms
5. **Editing-Friendly**: Schema validates "empty documents" to support document creation/editing workflows

### USLM Document Structure

```xml
<uslm:doc xmlns:uslm="http://schemas.gpo.gov/xml/uslm">
  <meta>
    <!-- Dublin Core metadata -->
    <dc:title>...</dc:title>
    <dc:date>...</dc:date>
  </meta>
  <main>
    <title number="XX">
      <heading>Title Heading</heading>
      <chapter number="YY">
        <heading>Chapter Heading</heading>
        <section number="XXXX">
          <num>§ XXXX.</num>
          <heading>Section Heading</heading>
          <content>
            <p>Section text...</p>
          </content>
          <notes>
            <note type="source">Source notes</note>
          </notes>
        </section>
      </chapter>
    </title>
  </main>
</uslm:doc>
```

### Key USLM Elements

#### Structural Elements
- `<title>` - US Code Title (e.g., Title 26 - Internal Revenue Code)
- `<subtitle>` - Subdivision of a title
- `<chapter>` - Chapter within a title
- `<subchapter>` - Subdivision of a chapter
- `<part>` - Part within a subchapter
- `<section>` - Individual code section (primary content unit)

#### Content Elements
- `<num>` - Section number (e.g., "§ 501")
- `<heading>` - Section or division heading
- `<content>` - Main content container
- `<p>` - Paragraph
- `<quotedContent>` - Quoted material
- `<ref>` - Cross-reference to other sections

#### Metadata Elements
- `<meta>` - Container for document metadata
- `<dc:title>` - Dublin Core title
- `<dc:date>` - Document date
- `<dc:identifier>` - Unique identifier
- `<notes>` - Editorial notes, source citations, amendments

### USLM Attributes

Common attributes across elements:
- `@identifier` - Unique ID for the element
- `@status` - Status of provision (enacted, repealed, reserved)
- `@class` - Classification or category
- `@date` - Relevant date for the element

### Data Sources for USLM

#### Official US Code Downloads
- **Primary Source**: https://uscode.house.gov/download/download.shtml
- **Format**: XML files in USLM format
- **Coverage**: All 54 titles of the US Code
- **Update Frequency**: Updated as legislation is enacted

#### GovInfo Bulk Data
- **API Endpoint**: https://api.govinfo.gov/collections/USCODE/
- **Bulk Downloads**: https://www.govinfo.gov/bulkdata/USCODE
- **Authentication**: API key required (free registration)
- **Format**: ZIP archives containing USLM XML files

## 2. CFRMergedXML Schema (Code of Federal Regulations)

### Schema Information
- **Schema URL**: https://www.govinfo.gov/bulkdata/CFR/resources/CFRMergedXML.xsd
- **Publisher**: U.S. Government Publishing Office (GPO)
- **Format**: XMLSchema 1.0

### Schema Purpose

The CFRMergedXML schema models the Code of Federal Regulations, which contains the codified rules and regulations of U.S. federal agencies.

### CFR Document Structure

```xml
<CFRDOC>
  <FMTR>
    <TITLE>Title Number</TITLE>
    <DATE>Date</DATE>
  </FMTR>
  <TITLE>
    <TITLEHD>Title Heading</TITLEHD>
  </TITLE>
  <CHAPTER>
    <CHAPTI>Chapter Number and Agency</CHAPTI>
    <PART>
      <PTHD>Part Heading</PTHD>
      <SECTION>
        <SECTNO>§ XX.XX</SECTNO>
        <SUBJECT>Section Subject</SUBJECT>
        <P>Section content...</P>
      </SECTION>
    </PART>
  </CHAPTER>
</CFRDOC>
```

### Key CFR Elements

#### Hierarchical Structure
- `<CFRDOC>` - Root element for CFR documents
- `<TITLE>` - CFR Title (50 titles total)
- `<CHAPTER>` - Chapter (usually assigned to one agency)
- `<SUBCHAP>` - Subchapter (optional grouping)
- `<PART>` - Part (main regulatory unit)
- `<SUBPART>` - Subpart (optional subdivision)
- `<SECTION>` - Individual regulation section

#### Content Elements
- `<SECTNO>` - Section number (e.g., "§ 1.101")
- `<SUBJECT>` - Section subject/heading
- `<P>` - Paragraph of text
- `<HD>` - Heading at various levels
- `<EXTRACT>` - Quoted or extracted material
- `<GPOTABLE>` - Tables

#### Bibliographic Elements
- `<FMTR>` - Front matter (title, date, revision info)
- `<AUTH>` - Authority citation
- `<SOURCE>` - Source citation
- `<EDNOTE>` - Editorial notes
- `<AMDDATE>` - Amendment date

#### Special Elements
- `<RESERVED>` - Reserved sections
- `<APPENDIX>` - Appendices to parts
- `<SUBJGRP>` - Subject group
- `<CITE>` - Citations
- `<PNOTICE>` - Privacy Act notices

### CFR Attributes
- `@N` - Number attribute (on various elements)
- `@TYPE` - Type classification
- `@ED` - Editor initials (eCFR only)
- `@REV` - Revisor initials (eCFR only)

### Data Sources for CFR

#### GovInfo Bulk Data
- **Primary Source**: https://www.govinfo.gov/bulkdata/CFR
- **Annual Editions**: Complete CFR as of each year
- **Format**: XML files validated against CFRMergedXML.xsd
- **Structure**: One file per CFR title
- **Update**: Annual updates, usually released quarterly

#### eCFR (Electronic Code of Federal Regulations)
- **Website**: https://www.ecfr.gov/
- **API**: https://www.ecfr.gov/developers/documentation/api/v1
- **Format**: JSON and XML
- **Update Frequency**: Daily updates
- **Coverage**: Current in-force regulations

#### Data.gov
- **CFR Dataset**: https://catalog.data.gov/dataset/code-of-federal-regulations
- **Format**: XML bulk downloads
- **Historical Data**: Available for past years

## Comparison: US vs Canadian XML Schemas

### Structural Differences

| Aspect | Canadian (XML Act Schema) | US USLM | US CFR |
|--------|---------------------------|---------|---------|
| **Root Element** | `<act>` or `<regulation>` | `<doc>` or `<title>` | `<CFRDOC>` |
| **Hierarchy** | Act → Part → Section → Subsection | Title → Chapter → Section | Title → Chapter → Part → Section |
| **Sections** | `<Section>` | `<section>` | `<SECTION>` |
| **Headings** | `<MarginalNote>` | `<heading>` | `<SUBJECT>`, `<HD>` |
| **Content** | Mixed within section | `<content>` wrapper | Direct in `<P>` |
| **Metadata** | `<Identification>` | `<meta>` with Dublin Core | `<FMTR>` |
| **Language** | Bilingual (en/fr) | English only | English only |
| **Updates** | Amendment-based | Version-controlled | Annual + eCFR daily |

### Citation Style Differences

#### Canadian Citations
- Format: `Act Title, SC 2001, c 27, s 5`
- Example: `Employment Insurance Act, SC 1996, c 23`
- Pattern: Statute/Regulation → Year → Chapter → Section

#### US Code Citations
- Format: `Title USC § Section`
- Example: `26 USC § 501(c)(3)`
- Pattern: Title Number → "USC" → Section Number

#### CFR Citations
- Format: `Title CFR § Section.Subsection`
- Example: `26 CFR § 1.501(c)(3)-1`
- Pattern: Title Number → "CFR" → Part.Section

### Naming Conventions

| Element | Canadian | USLM | CFR |
|---------|----------|------|-----|
| Case Style | PascalCase | camelCase | UPPERCASE |
| Example | `<MarginalNote>` | `<heading>` | `<SECTNO>` |
| Verbosity | Descriptive | Moderate | Abbreviated |

### Metadata Standards

- **Canadian**: Custom identification elements, bilingual
- **USLM**: Dublin Core metadata standard
- **CFR**: GPO-specific bibliographic elements

## Implementation Guide for Parsing US Regulations

### 1. USLM Parser Implementation

```python
from lxml import etree
from typing import Dict, List, Optional

class USLMParser:
    """Parser for USLM-formatted US Code XML."""
    
    NAMESPACE = {'uslm': 'http://schemas.gpo.gov/xml/uslm'}
    
    def parse_title(self, xml_path: str) -> Dict:
        """Parse a USLM title XML file."""
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        return {
            'type': 'usc_title',
            'title_number': self._get_title_number(root),
            'title_name': self._get_title_name(root),
            'metadata': self._extract_metadata(root),
            'chapters': self._extract_chapters(root),
            'sections': self._extract_sections(root)
        }
    
    def _get_title_number(self, root) -> str:
        """Extract title number."""
        title = root.find('.//uslm:title', self.NAMESPACE)
        return title.get('number') if title is not None else ''
    
    def _extract_sections(self, root) -> List[Dict]:
        """Extract all sections from the document."""
        sections = []
        for section in root.findall('.//uslm:section', self.NAMESPACE):
            sections.append({
                'identifier': section.get('identifier', ''),
                'num': self._get_text(section, './/uslm:num'),
                'heading': self._get_text(section, './/uslm:heading'),
                'content': self._get_all_text(section.find('.//uslm:content', self.NAMESPACE)),
                'notes': self._extract_notes(section)
            })
        return sections
    
    def _get_text(self, element, xpath: str) -> str:
        """Get text from xpath."""
        found = element.find(xpath, self.NAMESPACE)
        return found.text if found is not None else ''
```

### 2. CFR Parser Implementation

```python
class CFRParser:
    """Parser for CFRMergedXML-formatted CFR documents."""
    
    def parse_cfr_title(self, xml_path: str) -> Dict:
        """Parse a CFR title XML file."""
        tree = etree.parse(xml_path)
        root = tree.getroot()
        
        return {
            'type': 'cfr_title',
            'title_info': self._extract_front_matter(root),
            'chapters': self._extract_chapters(root),
            'parts': self._extract_parts(root)
        }
    
    def _extract_front_matter(self, root) -> Dict:
        """Extract bibliographic information."""
        fmtr = root.find('.//FMTR')
        if fmtr is None:
            return {}
        
        return {
            'title': self._get_element_text(fmtr, 'TITLE'),
            'date': self._get_element_text(fmtr, 'DATE'),
            'volume': self._get_element_text(fmtr, 'VOL')
        }
    
    def _extract_parts(self, root) -> List[Dict]:
        """Extract all parts from CFR document."""
        parts = []
        for part in root.findall('.//PART'):
            parts.append({
                'heading': self._get_element_text(part, 'PTHD'),
                'authority': self._get_element_text(part, 'AUTH'),
                'source': self._get_element_text(part, 'SOURCE'),
                'sections': self._extract_cfr_sections(part)
            })
        return parts
    
    def _extract_cfr_sections(self, part) -> List[Dict]:
        """Extract sections from a CFR part."""
        sections = []
        for section in part.findall('.//SECTION'):
            sections.append({
                'number': self._get_element_text(section, 'SECTNO'),
                'subject': self._get_element_text(section, 'SUBJECT'),
                'content': self._get_all_paragraphs(section)
            })
        return sections
```

### 3. Unified Document Model

Both parsers should output to a unified document model:

```python
{
    'doc_id': 'usc-26-501',
    'jurisdiction': 'federal-us',
    'doc_type': 'statute',  # or 'regulation'
    'title_number': '26',
    'citation': '26 USC § 501',
    'heading': 'Exemption from tax on corporations...',
    'content': 'Full text content...',
    'language': 'en',
    'enacted_date': '1954-08-16',
    'last_amended': '2023-12-31',
    'metadata': {
        'schema_version': 'uslm-2.0.5',
        'publisher': 'GPO',
        'authority': 'Congressional authority citation'
    },
    'relationships': [
        {
            'type': 'cites',
            'target': '26 USC § 502'
        }
    ]
}
```

## Data Acquisition Strategy

### Phase 1: Initial Download (US Code)
```bash
# Download complete US Code in USLM format
curl -o usc-title-26.zip "https://www.govinfo.gov/bulkdata/USCODE/2023/title-26/USCODE-2023-title26.zip"
unzip usc-title-26.zip
```

### Phase 2: CFR Download
```bash
# Download CFR Title (e.g., Title 26 - IRS regulations)
curl -o cfr-title-26-2024.xml "https://www.govinfo.gov/bulkdata/CFR/2024/title-26/CFR-2024-title26.xml"
```

### Phase 3: GovInfo API Integration

```python
import requests

class GovInfoAPI:
    """Client for GovInfo API."""
    
    BASE_URL = "https://api.govinfo.gov"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.params = {'api_key': api_key}
    
    def get_uscode_packages(self, year: int = 2023) -> List[Dict]:
        """Get list of available USC packages."""
        url = f"{self.BASE_URL}/collections/USCODE/{year}"
        response = self.session.get(url)
        return response.json()
    
    def download_uscode_title(self, title_num: int, year: int, output_path: str):
        """Download a specific USC title."""
        package_id = f"USCODE-{year}-title{title_num}"
        url = f"{self.BASE_URL}/packages/{package_id}/zip"
        
        response = self.session.get(url, stream=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
```

## Schema Validation

### Validate USLM Documents
```python
from lxml import etree

def validate_uslm(xml_path: str, xsd_path: str) -> bool:
    """Validate USLM XML against schema."""
    schema = etree.XMLSchema(etree.parse(xsd_path))
    doc = etree.parse(xml_path)
    return schema.validate(doc)
```

### Validate CFR Documents
```python
def validate_cfr(xml_path: str, xsd_path: str) -> bool:
    """Validate CFR XML against schema."""
    schema = etree.XMLSchema(etree.parse(xsd_path))
    doc = etree.parse(xml_path)
    return schema.validate(doc)
```

## Integration Checklist

- [ ] Download USLM and CFR schemas
- [ ] Set up GovInfo API access (get API key)
- [ ] Implement USLM parser
- [ ] Implement CFR parser
- [ ] Create unified document model mapper
- [ ] Test parsers with sample titles
- [ ] Download bulk US Code data
- [ ] Download bulk CFR data
- [ ] Ingest into PostgreSQL database
- [ ] Index in Elasticsearch
- [ ] Build knowledge graph in Neo4j
- [ ] Update frontend for US regulations
- [ ] Test cross-references between USC and CFR
- [ ] Implement citation resolver
- [ ] Add US-specific compliance rules

## Resources

### Official Documentation
- **USLM User Guide**: https://github.com/usgpo/uslm
- **CFR XML User Guide**: Available via GPO bulk data resources
- **GovInfo API Docs**: https://api.govinfo.gov/docs/

### Data Sources
- **US Code**: https://uscode.house.gov/
- **eCFR**: https://www.ecfr.gov/
- **GovInfo**: https://www.govinfo.gov/
- **Bulk Data**: https://www.govinfo.gov/bulkdata/

### Schemas
- **USLM XSD**: https://www.govinfo.gov/schemas/xml/uslm/uslm-2.0.5.xsd
- **CFR XSD**: https://www.govinfo.gov/bulkdata/CFR/resources/CFRMergedXML.xsd

## Notes

1. **Language**: US regulations are English-only (unlike bilingual Canadian regulations)
2. **Updates**: US Code uses version control; CFR uses annual editions with daily eCFR updates
3. **Size**: US Code contains ~54 titles; CFR contains 50 titles
4. **Complexity**: CFR structure is simpler than USLM but has more abbreviated element names
5. **Authentication**: GovInfo API requires free API key registration
6. **Legal Status**: USC contains statutes (primary law); CFR contains regulations (secondary law)

## Next Steps

1. Extend the Canadian law parser to support USLM and CFR formats
2. Create jurisdiction-aware routing in the data pipeline
3. Update Elasticsearch mappings for US-specific fields
4. Implement US citation parsing and linking
5. Add US program mappings (Social Security, Medicare, IRS, etc.)
6. Create test cases with sample US regulations
