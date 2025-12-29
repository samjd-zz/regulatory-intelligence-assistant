"""
XML parser for Canadian Justice Laws format.
Parses the official XML format from laws-lois.justice.gc.ca
"""
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParsedSection:
    """Represents a parsed section from XML."""
    section_id: str
    number: str
    title: Optional[str]
    content: str
    level: int
    subsections: List['ParsedSection'] = field(default_factory=list)
    parent_id: Optional[str] = None
    

@dataclass
class ParsedAmendment:
    """Represents an amendment from XML."""
    date: str
    bill_number: Optional[str]
    description: str


@dataclass
class ParsedCrossReference:
    """Represents a cross-reference from XML."""
    source_section: str
    target_section: str
    citation_text: str
    

@dataclass
class ParsedRegulation:
    """Represents a parsed regulation from XML."""
    title: str
    chapter: str
    act_type: str
    enabled_date: Optional[str]
    consolidation_date: Optional[str]
    jurisdiction: str
    full_text: str
    sections: List[ParsedSection]
    amendments: List[ParsedAmendment]
    cross_references: List[ParsedCrossReference]
    metadata: Dict[str, Any]


class CanadianLawXMLParser:
    """
    Parser for Canadian Justice Laws XML format.
    
    Handles the structure from the Open Canada dataset:
    https://open.canada.ca/data/en/dataset/1f0aae37-18e4-4bad-bbca-59a4094e44fa
    
    Example XML structure:
    <Consolidation>
      <Identification>
        <Chapter>S.C. 1996, c. 23</Chapter>
        <TitleText>Employment Insurance Act</TitleText>
        <EnabledDate>1996-06-30</EnabledDate>
        <ConsolidationDate>2024-01-15</ConsolidationDate>
      </Identification>
      <Body>
        <Part id="I">
          <Section id="7">
            <Number>7</Number>
            <Heading>Qualification for benefits</Heading>
            <Subsection id="7-1">
              <Number>1</Number>
              <Text>Subject to this Part, benefits are payable...</Text>
            </Subsection>
          </Section>
        </Part>
      </Body>
      <Amendments>
        <Amendment>
          <Date>2024-01-15</Date>
          <BillNumber>C-47</BillNumber>
          <Description>Updated eligibility requirements</Description>
        </Amendment>
      </Amendments>
    </Consolidation>
    """
    
    def __init__(self):
        """Initialize the parser."""
        self.namespace_map = {}
        
    def parse_file(self, xml_path: str) -> ParsedRegulation:
        """
        Parse an XML file from Canadian Justice Laws.
        
        Args:
            xml_path: Path to XML file
            
        Returns:
            ParsedRegulation object with structured data
        """
        logger.info(f"Parsing Canadian Law XML: {xml_path}")
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Detect namespace
            self._detect_namespace(root)
            
            # Determine format: Statute, Regulation (real formats) vs Consolidation (test format)
            root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            
            if root_tag == 'Statute':
                return self._parse_statute(root)
            elif root_tag == 'Regulation':
                return self._parse_regulation(root)
            else:
                # Fall back to old consolidation format
                return self._parse_consolidation(root)
            
        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            raise ValueError(f"Invalid XML format: {e}")
        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            raise
    
    def parse_string(self, xml_content: str) -> ParsedRegulation:
        """
        Parse XML content from string.
        
        Args:
            xml_content: XML content as string
            
        Returns:
            ParsedRegulation object
        """
        try:
            root = ET.fromstring(xml_content)
            self._detect_namespace(root)
            return self._parse_consolidation(root)
        except Exception as e:
            logger.error(f"Error parsing XML string: {e}")
            raise ValueError(f"Failed to parse XML: {e}")
    
    def _detect_namespace(self, root: ET.Element):
        """Detect XML namespace from root element."""
        if root.tag.startswith('{'):
            # Extract namespace
            namespace = root.tag[1:root.tag.index('}')]
            self.namespace_map = {'': namespace}
        else:
            self.namespace_map = {}
    
    def _find(self, element: ET.Element, path: str) -> Optional[ET.Element]:
        """Find element with namespace support."""
        return element.find(path, self.namespace_map)
    
    def _findall(self, element: ET.Element, path: str) -> List[ET.Element]:
        """Find all elements with namespace support."""
        return element.findall(path, self.namespace_map)
    
    def _get_text(self, element: Optional[ET.Element], default: str = "") -> str:
        """
        Safely get text from element, including all text from child elements.
        
        This handles cases where XML has inline formatting tags like:
        <Text>The employer shall <Emphasis>prepare</Emphasis> a plan</Text>
        
        Using itertext() ensures we get ALL text content, not just the first text node.
        """
        if element is not None:
            # Get all text content, including text from child elements
            text = ''.join(element.itertext()).strip()
            if text:
                return text
        return default
    
    def _detect_jurisdiction_from_metadata(self, root: ET.Element, title: str, chapter: str) -> str:
        """
        Detect jurisdiction from XML metadata, authority, or title.
        
        Args:
            root: XML root element
            title: Document title
            chapter: Chapter/authority notation (e.g., "S.C. 1996, c. 23")
            
        Returns:
            Detected jurisdiction: 'federal', 'ontario', 'quebec', etc.
        """
        # Check chapter notation (S.C. = federal, S.O. = Ontario, etc.)
        if chapter:
            chapter_upper = chapter.upper()
            
            # Federal
            if chapter_upper.startswith('S.C.') or chapter_upper.startswith('R.S.C.'):
                return 'federal'
            
            # Ontario
            elif chapter_upper.startswith('S.O.') or chapter_upper.startswith('R.S.O.'):
                return 'ontario'
            
            # Quebec
            elif chapter_upper.startswith('S.Q.') or chapter_upper.startswith('R.S.Q.') or \
                 chapter_upper.startswith('L.R.Q.') or chapter_upper.startswith('L.Q.'):
                return 'quebec'
            
            # British Columbia
            elif chapter_upper.startswith('S.B.C.') or chapter_upper.startswith('R.S.B.C.'):
                return 'british_columbia'
            
            # Alberta
            elif chapter_upper.startswith('S.A.') or chapter_upper.startswith('R.S.A.'):
                return 'alberta'
            
            # Manitoba
            elif chapter_upper.startswith('S.M.') or chapter_upper.startswith('R.S.M.'):
                return 'manitoba'
            
            # Saskatchewan
            elif chapter_upper.startswith('S.S.') or chapter_upper.startswith('R.S.S.'):
                return 'saskatchewan'
            
            # Nova Scotia
            elif chapter_upper.startswith('S.N.S.') or chapter_upper.startswith('R.S.N.S.'):
                return 'nova_scotia'
            
            # New Brunswick
            elif chapter_upper.startswith('S.N.B.') or chapter_upper.startswith('R.S.N.B.'):
                return 'new_brunswick'
            
            # Prince Edward Island
            elif chapter_upper.startswith('S.P.E.I.') or chapter_upper.startswith('R.S.P.E.I.'):
                return 'prince_edward_island'
            
            # Newfoundland and Labrador
            elif chapter_upper.startswith('S.N.L.') or chapter_upper.startswith('R.S.N.L.') or \
                 chapter_upper.startswith('S.N.') or chapter_upper.startswith('R.S.N.'):
                return 'newfoundland_labrador'
        
        # Fallback to title-based detection
        if title:
            title_lower = title.lower()
            
            # Provincial keywords
            if 'ontario' in title_lower:
                return 'ontario'
            elif 'quebec' in title_lower or 'québec' in title_lower:
                return 'quebec'
            elif 'british columbia' in title_lower or 'b.c.' in title_lower:
                return 'british_columbia'
            elif 'alberta' in title_lower:
                return 'alberta'
            elif 'manitoba' in title_lower:
                return 'manitoba'
            elif 'saskatchewan' in title_lower:
                return 'saskatchewan'
            elif 'nova scotia' in title_lower:
                return 'nova_scotia'
            elif 'new brunswick' in title_lower:
                return 'new_brunswick'
            elif 'prince edward island' in title_lower or 'p.e.i.' in title_lower:
                return 'prince_edward_island'
            elif 'newfoundland' in title_lower or 'labrador' in title_lower:
                return 'newfoundland_labrador'
        
        # Default to federal for Canadian laws (Justice Canada repository)
        logger.info(f"No jurisdiction indicators found, defaulting to 'federal'")
        return 'federal'
    
    def _parse_consolidation(self, root: ET.Element) -> ParsedRegulation:
        """Parse Consolidation element (root)."""
        logger.info("Parsing Consolidation element")
        
        # Parse identification section
        identification = self._find(root, './/Identification')
        if identification is None:
            identification = self._find(root, 'Identification')
        
        if identification is None:
            raise ValueError("No Identification section found in XML")
        
        title = self._get_text(self._find(identification, 'TitleText'), "Untitled Act")
        chapter = self._get_text(self._find(identification, 'Chapter'), "")
        enabled_date = self._get_text(self._find(identification, 'EnabledDate'))
        consolidation_date = self._get_text(self._find(identification, 'ConsolidationDate'))
        
        # Determine act type from chapter notation
        act_type = self._determine_act_type(chapter)
        
        # Detect jurisdiction dynamically
        jurisdiction = self._detect_jurisdiction_from_metadata(root, title, chapter)
        
        logger.info(f"Parsing regulation: {title}")
        logger.info(f"Detected jurisdiction: {jurisdiction}")
        
        # Parse body (sections)
        body = self._find(root, './/Body')
        if body is None:
            body = self._find(root, 'Body')
        sections = []
        full_text_parts = []
        
        if body is not None:
            sections, full_text_parts = self._parse_body(body)
        
        # Parse amendments
        amendments = self._parse_amendments(root)
        
        # Extract cross-references from sections
        cross_references = self._extract_cross_references(sections)
        
        # Build full text
        full_text = "\n\n".join(full_text_parts) if full_text_parts else ""
        
        # Build metadata
        metadata = {
            'chapter': chapter,
            'enabled_date': enabled_date,
            'consolidation_date': consolidation_date,
            'act_type': act_type,
            'source': 'Justice Laws Canada',
            'format': 'XML'
        }
        
        regulation = ParsedRegulation(
            title=title,
            chapter=chapter,
            act_type=act_type,
            enabled_date=enabled_date,
            consolidation_date=consolidation_date,
            jurisdiction=jurisdiction,  # Use detected jurisdiction
            full_text=full_text,
            sections=sections,
            amendments=amendments,
            cross_references=cross_references,
            metadata=metadata
        )
        
        logger.info(f"Parsed {len(sections)} sections, {len(amendments)} amendments")
        return regulation
    
    def _parse_statute(self, root: ET.Element) -> ParsedRegulation:
        """
        Parse Statute element (real Justice Canada format).
        
        Structure:
        <Statute>
          <Title>Act Title</Title>
          <Body>
            <Section lims:id="...">
              <MarginalNote>Section Title</MarginalNote>
              <Label>140</Label>
              <Subsection>
                <Label>(1)</Label>
                <Text>Content...</Text>
              </Subsection>
            </Section>
          </Body>
        </Statute>
        """
        logger.info("Parsing Statute element (Justice Canada LIMS format)")
        
        # Parse Identification section (required in official format)
        identification = self._find(root, 'Identification')
        if identification is None:
            raise ValueError("No Identification section found in Statute")
        
        # Extract title from Identification section (prefers ShortTitle)
        title = self._extract_statute_title(root)
        
        # Also extract LongTitle for metadata (the formal "An Act respecting..." version)
        long_title = None
        if identification is not None:
            long_title_elem = self._find(identification, 'LongTitle')
            if long_title_elem is not None:
                long_title = self._get_text(long_title_elem)
        
        logger.info(f"Parsing statute: {title}")
        if long_title and long_title != title:
            logger.info(f"  Long title: {long_title}")
        
        # Extract chapter/citation from Chapter/ConsolidatedNumber (official structure)
        chapter = ""
        chapter_elem = self._find(identification, 'Chapter')
        if chapter_elem is not None:
            consolidated_num = self._find(chapter_elem, 'ConsolidatedNumber')
            if consolidated_num is not None:
                chapter = self._get_text(consolidated_num)
        
        # Determine act type
        act_type = self._determine_act_type(chapter) if chapter else "Statute"
        
        # Parse body sections
        body = self._find(root, 'Body')
        sections = []
        full_text_parts = []
        
        if body is not None:
            # Find all direct Section elements
            section_elements = self._findall(body, 'Section')
            for section_elem in section_elements:
                section, text = self._parse_statute_section(section_elem, regulation_title=title)
                if section:
                    sections.append(section)
                    full_text_parts.append(text)
        
        # Build full text
        full_text = "\n\n".join(full_text_parts) if full_text_parts else ""
        
        # Parse RecentAmendments if present (official format)
        amendments = self._parse_recent_amendments(root)
        
        # Extract metadata from attributes and dates
        metadata = {
            'chapter': chapter,
            'act_type': act_type,
            'source': 'Justice Laws Canada',
            'format': 'Statute XML (LIMS)',
            'long_title': long_title  # Store formal title for reference
        }
        
        # Add LIMS-specific attributes from root
        if hasattr(root, 'attrib'):
            for key, value in root.attrib.items():
                clean_key = key.split('}')[-1] if '}' in key else key
                if clean_key in ['pit-date', 'lastAmendedDate', 'current-date', 'inforce-start-date']:
                    metadata[clean_key] = value
        
        # Detect jurisdiction dynamically
        jurisdiction = self._detect_jurisdiction_from_metadata(root, title, chapter)
        logger.info(f"Detected jurisdiction: {jurisdiction}")
        
        regulation = ParsedRegulation(
            title=title,
            chapter=chapter,
            act_type=act_type,
            enabled_date=None,  # Use inforce-start-date from metadata
            consolidation_date=metadata.get('current-date'),
            jurisdiction=jurisdiction,  # Use detected jurisdiction
            full_text=full_text,
            sections=sections,
            amendments=amendments,
            cross_references=self._extract_cross_references(sections),
            metadata=metadata
        )
        
        logger.info(f"Parsed {len(sections)} sections from Statute format")
        return regulation
    
    def _parse_regulation(self, root: ET.Element) -> ParsedRegulation:
        """
        Parse Regulation element (SOR/DORS format).
        
        Structure:
        <Regulation regulation-type="ministerial" xml:lang="en">
          <Identification>
            <ConsolidatedNumber>SOR/96-445</ConsolidatedNumber>
            <Title>Employment Insurance Regulations</Title>
            <EnablingAuthority>Employment Insurance Act</EnablingAuthority>
          </Identification>
          <Body>
            <Section>...</Section>
          </Body>
          <RecentAmendments>...</RecentAmendments>
        </Regulation>
        """
        logger.info("Parsing Regulation format (SOR/DORS)")
        
        # Get regulation type from root attribute
        regulation_type = root.get('regulation-type', 'regulation')
        
        # Extract identification info
        identification = self._find(root, 'Identification')
        if identification is None:
            raise ValueError("No Identification section found in Regulation XML")
        
        # Title extraction - try multiple fields
        title = (
            self._get_text(self._find(identification, 'Title')) or
            self._get_text(self._find(identification, 'LongTitle')) or
            self._get_text(self._find(identification, 'ShortTitle')) or
            "Untitled Regulation"
        )
        
        # Get SOR/DORS number
        chapter = self._get_text(self._find(identification, 'ConsolidatedNumber'), "")
        if not chapter:
            chapter = self._get_text(self._find(identification, 'Chapter'), "")
        
        # Get enabling authority (parent Act)
        enabling_authority = self._get_text(self._find(identification, 'EnablingAuthority'))
        
        # Get dates
        enabled_date = None
        consolidation_date = None
        
        # Check for dates in Identification
        date_elem = self._find(identification, 'Date')
        if date_elem is not None:
            year = self._get_text(self._find(date_elem, 'YYYY'))
            month = self._get_text(self._find(date_elem, 'MM'))
            day = self._get_text(self._find(date_elem, 'DD'))
            if year and month and day:
                enabled_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Check root attributes for dates
        if hasattr(root, 'attrib'):
            consolidation_date = root.get('current-date') or root.get('pit-date')
            if not enabled_date:
                enabled_date = root.get('inforce-start-date')
        
        # Parse body sections
        body = self._find(root, 'Body')
        sections = []
        full_text_parts = []
        
        if body is not None:
            for section_elem in self._findall(body, './/Section'):
                section, text = self._parse_statute_section(section_elem, regulation_title=title)
                if section:
                    sections.append(section)
                    full_text_parts.append(text)
        
        # Build full text
        full_text = "\n\n".join(full_text_parts) if full_text_parts else ""
        
        # Parse RecentAmendments
        amendments = self._parse_recent_amendments(root)
        
        # Detect jurisdiction
        jurisdiction = self._detect_jurisdiction_from_metadata(root, title, chapter)
        
        # Extract metadata
        metadata = {
            'chapter': chapter,
            'act_type': 'Regulation',
            'regulation_type': regulation_type,
            'enabling_authority': enabling_authority,
            'source': 'Justice Laws Canada',
            'format': 'Regulation XML (LIMS)'
        }
        
        # Add LIMS attributes
        if hasattr(root, 'attrib'):
            for key, value in root.attrib.items():
                clean_key = key.split('}')[-1] if '}' in key else key
                if clean_key in ['pit-date', 'lastAmendedDate', 'current-date', 'inforce-start-date']:
                    metadata[clean_key] = value
        
        regulation = ParsedRegulation(
            title=title,
            chapter=chapter,
            act_type='Regulation',
            enabled_date=enabled_date,
            consolidation_date=consolidation_date or metadata.get('current-date'),
            jurisdiction=jurisdiction,
            full_text=full_text,
            sections=sections,
            amendments=amendments,
            cross_references=self._extract_cross_references(sections),
            metadata=metadata
        )
        
        logger.info(f"Parsed Regulation: {title} ({chapter})")
        logger.info(f"Enabling Authority: {enabling_authority}")
        logger.info(f"Parsed {len(sections)} sections from Regulation format")
        return regulation
    
    def _extract_statute_title(self, root: ET.Element) -> str:
        """
        Extract title from Statute format XML.
        
        Official structure (LIMS format):
        <Statute>
          <Identification>
            <LongTitle>Full official title</LongTitle>
            <ShortTitle>Short Title Act</ShortTitle>
            <RunningHead>Running Head</RunningHead>
          </Identification>
        </Statute>
        
        Tries multiple strategies in order:
        1. Identification/ShortTitle (user-friendly official short title) ⭐ PREFERRED
        2. Identification/RunningHead (header title)
        3. Body section with "Short Title" - extract from content
        4. Identification/LongTitle (full formal title - fallback)
        5. Document ID from attributes (last resort)
        
        Note: ShortTitle is preferred over LongTitle for better UX.
        The LongTitle (formal "An Act respecting...") is stored in metadata.
        """
        import re
        
        # Get Identification section first (required in official LIMS format)
        identification = self._find(root, 'Identification')
        
        # Strategy 1: ShortTitle in Identification (official short title - PREFERRED)
        if identification is not None:
            short_title = self._find(identification, 'ShortTitle')
            if short_title is not None:
                title = self._get_text(short_title)
                if title and len(title) > 5 and title.lower() not in ['untitled', 'title', 'short title']:
                    logger.info(f"Found title from Identification/ShortTitle: {title}")
                    return title
        
        # Strategy 2: RunningHead in Identification (official short title for headers)
        if identification is not None:
            running_head = self._find(identification, 'RunningHead')
            if running_head is not None:
                title = self._get_text(running_head)
                if title and len(title) > 5 and title.lower() not in ['untitled', 'title']:
                    logger.info(f"Found title from Identification/RunningHead: {title}")
                    return title
        
        # Strategy 3: Extract from "Short Title" section content
        # This is a common pattern in Canadian legislation
        body = self._find(root, 'Body')
        if body is not None:
            sections = self._findall(body, './/Section')
            for section in sections[:10]:  # Check first 10 sections
                margin_note = self._find(section, 'MarginalNote')
                if margin_note is not None:
                    note_text = self._get_text(margin_note).lower()
                    # Look for "short title" sections (not just "title")
                    if 'short title' in note_text:
                        # Get the text content from this section or its subsections
                        text_elems = self._findall(section, './/Text')
                        if not text_elems:
                            text_elems = [self._find(section, 'Text')]
                        
                        for text_elem in text_elems:
                            if text_elem is not None:
                                section_text = self._get_text(text_elem)
                                if not section_text:
                                    continue
                                
                                # Extract title from patterns like:
                                # "This Act may be cited as the Employment Insurance Act"
                                # "This Act may be cited as the « Employment Insurance Act »"
                                # Multiple patterns for bilingual content
                                patterns = [
                                    r'(?:cited as|known as|called|intitulée)\s+(?:the\s+)?["\u00ab\u201c]([^"\u00bb\u201d]+)["\u00bb\u201d]',
                                    r'(?:cited as|known as|called|intitulée)\s+(?:the\s+)?([A-Z][^.]+Act)',
                                    r'(?:cited as|known as|called|intitulée)\s+(?:the\s+)?([A-Z][^.]+Loi)',
                                ]
                                
                                for pattern in patterns:
                                    match = re.search(pattern, section_text, re.IGNORECASE)
                                    if match:
                                        title = match.group(1).strip()
                                        # Clean up the title
                                        title = title.replace('\u00a0', ' ')  # Non-breaking space
                                        title = title.strip()
                                        if title and len(title) > 5 and len(title) < 200:
                                            logger.info(f"Extracted title from Short Title section: {title}")
                                            return title
        
        # Strategy 4: LongTitle in Identification (full formal title - fallback only)
        # This gives "An Act respecting..." format which is less user-friendly
        if identification is not None:
            long_title = self._find(identification, 'LongTitle')
            if long_title is not None:
                title = self._get_text(long_title)
                if title and len(title) > 5 and title.lower() not in ['untitled', 'title']:
                    logger.info(f"Found title from Identification/LongTitle (using as fallback): {title}")
                    return title
        
        # Strategy 5: Extract from document ID in attributes (last resort)
        if hasattr(root, 'attrib'):
            for key, value in root.attrib.items():
                clean_key = key.split('}')[-1] if '}' in key else key
                if clean_key in ['id', 'xml:id', 'docNumber'] and value:
                    # Try to extract a readable title from the ID
                    logger.info(f"Using document ID as fallback title: {value}")
                    return f"Act {value}"
        
        # Final fallback: Return generic but descriptive
        logger.warning("Could not extract title from XML, using generic fallback")
        return "Canadian Federal Statute"
    
    def _parse_statute_section(
        self,
        section_elem: ET.Element,
        level: int = 1,
        parent_id: Optional[str] = None,
        regulation_title: Optional[str] = None
    ) -> Tuple[Optional[ParsedSection], str]:
        """
        Parse a Section element in Statute format.
        
        Structure:
          <Section lims:id="...">
            <MarginalNote>Section Title</MarginalNote>
            <Label>140</Label>
            <Subsection lims:id="...">
              <MarginalNote>Subsection title (optional)</MarginalNote>
              <Label>(1)</Label>
              <Text>Content here...</Text>
              <Paragraph lims:id="...">
                <Label>a)</Label>
                <Text>Paragraph text...</Text>
              </Paragraph>
            </Subsection>
          </Section>
        """
        # Get section ID from lims:id attribute
        section_id = section_elem.get('id', '')
        if not section_id:
            # Try with namespace
            for key in section_elem.attrib:
                if key.endswith('id'):
                    section_id = section_elem.attrib[key]
                    break
        # Get section number from Label
        label_elem = self._find(section_elem, 'Label')
        number = self._get_text(label_elem) if label_elem is not None else ""
        # Get title from MarginalNote
        margin_note_elem = self._find(section_elem, 'MarginalNote')
        title = self._get_text(margin_note_elem) if margin_note_elem is not None else None
        # Fallback: if title is missing or empty, use regulation_title if provided
        if (not title or not title.strip()) and regulation_title:
            title = regulation_title
        # Improved fallback: If no Label found, use section_id or generate a unique number
        # instead of using the full title which can be too long
        if not number:
            if section_id:
                # Use the section ID as the number (e.g., "476027")
                number = section_id
                logger.warning(f"Section missing Label, using section_id as number: {section_id}")
            else:
                # Last resort: skip this section
                logger.warning(f"Section missing both Label and ID, skipping")
                return None, ""
        # Build content and full text
        content_parts = []
        full_text_parts = [f"Section {number}"]
        if title:
            full_text_parts.append(f"{title}")
            # Don't add title to content_parts - title is stored separately
        
        # Parse subsections
        subsections = []
        subsection_elements = self._findall(section_elem, 'Subsection')
        for subsection_elem in subsection_elements:
            # Get subsection label
            sub_label_elem = self._find(subsection_elem, 'Label')
            sub_label = self._get_text(sub_label_elem) if sub_label_elem is not None else ""
            # Get subsection text
            text_elem = self._find(subsection_elem, 'Text')
            sub_text = self._get_text(text_elem) if text_elem is not None else ""
            # Get subsection ID
            sub_id = subsection_elem.get('id', '')
            if not sub_id:
                for key in subsection_elem.attrib:
                    if key.endswith('id'):
                        sub_id = subsection_elem.attrib[key]
                        break
            # Get subsection title - inherit from parent section if missing
            # Subsections typically don't have separate titles in legal documents
            sub_margin_elem = self._find(subsection_elem, 'MarginalNote')
            sub_title = self._get_text(sub_margin_elem) if sub_margin_elem is not None else None
            # Inherit title from parent section first, then fall back to regulation title
            if not sub_title or not sub_title.strip():
                sub_title = title if title else regulation_title
            if sub_text:
                # Create subsection
                subsection = ParsedSection(
                    section_id=sub_id or f"{section_id}-{sub_label}",
                    number=f"{number}{sub_label}",
                    title=sub_title,
                    content=sub_text,
                    level=level + 1,
                    parent_id=section_id
                )
                subsections.append(subsection)
                content_parts.append(f"{sub_label} {sub_text}")
                full_text_parts.append(f"  {sub_label} {sub_text}")
        
        # If no subsections found, check for direct Text element
        if not subsections:
            text_elem = self._find(section_elem, 'Text')
            if text_elem is not None:
                text = self._get_text(text_elem)
                if text:
                    content_parts.append(text)
                    full_text_parts.append(f"  {text}")
        
        content = "\n".join(content_parts)
        full_text = "\n".join(full_text_parts)
        
        section = ParsedSection(
            section_id=section_id,
            number=number,
            title=title,
            content=content,
            level=level,
            subsections=subsections,
            parent_id=parent_id
        )
        
        return section, full_text
    
    def _determine_act_type(self, chapter: str) -> str:
        """Determine act type from chapter notation."""
        if chapter.startswith('S.C.'):
            return 'Statute of Canada'
        elif chapter.startswith('R.S.C.'):
            return 'Revised Statutes of Canada'
        elif chapter.startswith('S.O.'):
            return 'Statute of Ontario'
        else:
            return 'Act'
    
    def _parse_body(self, body: ET.Element) -> Tuple[List[ParsedSection], List[str]]:
        """
        Parse Body element containing sections and parts.
        
        Returns:
            Tuple of (sections list, full text parts list)
        """
        sections = []
        full_text_parts = []
        
        # Handle Parts (major divisions)
        parts = self._findall(body, './/Part') or self._findall(body, 'Part')
        
        if parts:
            for part in parts:
                part_sections, part_text = self._parse_part(part)
                sections.extend(part_sections)
                full_text_parts.extend(part_text)
        else:
            # No parts, parse sections directly
            section_elements = self._findall(body, './/Section') or self._findall(body, 'Section')
            for section_elem in section_elements:
                section, text = self._parse_section(section_elem, level=1)
                if section:
                    sections.append(section)
                    full_text_parts.append(text)
        
        return sections, full_text_parts
    
    def _parse_part(self, part: ET.Element) -> Tuple[List[ParsedSection], List[str]]:
        """Parse a Part element."""
        part_id = part.get('id', '')
        part_number = self._get_text(self._find(part, 'Number'))
        part_heading = self._get_text(self._find(part, 'Heading'))
        
        sections = []
        full_text_parts = []
        
        # Add part heading to text
        if part_heading:
            full_text_parts.append(f"PART {part_number}: {part_heading}")
        
        # Parse sections within part
        section_elements = self._findall(part, 'Section')
        for section_elem in section_elements:
            section, text = self._parse_section(section_elem, level=2, parent_id=part_id)
            if section:
                sections.append(section)
                full_text_parts.append(text)
        
        return sections, full_text_parts
    
    def _parse_section(
        self, 
        section_elem: ET.Element, 
        level: int = 1,
        parent_id: Optional[str] = None
    ) -> Tuple[Optional[ParsedSection], str]:
        """
        Parse a Section element.
        
        Returns:
            Tuple of (ParsedSection or None, full text)
        """
        section_id = section_elem.get('id', '')
        number = self._get_text(self._find(section_elem, 'Number'))
        heading = self._get_text(self._find(section_elem, 'Heading'))
        
        if not number:
            return None, ""
        
        # Build section content and full text
        content_parts = []
        full_text_parts = [f"Section {number}"]
        
        if heading:
            full_text_parts.append(f"{heading}")
            content_parts.append(heading)
        
        # Parse subsections
        subsections = []
        subsection_elements = self._findall(section_elem, 'Subsection')
        
        for subsection_elem in subsection_elements:
            subsection_num = self._get_text(self._find(subsection_elem, 'Number'))
            subsection_text = self._get_text(self._find(subsection_elem, 'Text'))
            
            if subsection_text:
                # Create subsection as nested ParsedSection
                subsection = ParsedSection(
                    section_id=f"{section_id}-{subsection_num}",
                    number=f"{number}({subsection_num})",
                    title=None,
                    content=subsection_text,
                    level=level + 1,
                    parent_id=section_id
                )
                subsections.append(subsection)
                
                content_parts.append(f"({subsection_num}) {subsection_text}")
                full_text_parts.append(f"  ({subsection_num}) {subsection_text}")
        
        # If no subsections, check for direct text content
        if not subsections:
            text_elem = self._find(section_elem, 'Text')
            if text_elem is not None:
                text = self._get_text(text_elem)
                content_parts.append(text)
                full_text_parts.append(f"  {text}")
        
        content = "\n".join(content_parts)
        full_text = "\n".join(full_text_parts)
        
        section = ParsedSection(
            section_id=section_id,
            number=number,
            title=heading,
            content=content,
            level=level,
            subsections=subsections,
            parent_id=parent_id
        )
        
        return section, full_text
    
    def _parse_amendments(self, root: ET.Element) -> List[ParsedAmendment]:
        """Parse Amendments section."""
        amendments = []
        
        amendments_section = self._find(root, './/Amendments')
        if amendments_section is None:
            amendments_section = self._find(root, 'Amendments')
        if amendments_section is None:
            return amendments
        
        amendment_elements = self._findall(amendments_section, 'Amendment')
        
        for amendment_elem in amendment_elements:
            date = self._get_text(self._find(amendment_elem, 'Date'))
            bill_number = self._get_text(self._find(amendment_elem, 'BillNumber'))
            description = self._get_text(self._find(amendment_elem, 'Description'))
            
            if date and description:
                amendments.append(ParsedAmendment(
                    date=date,
                    bill_number=bill_number if bill_number else None,
                    description=description
                ))
        
        logger.info(f"Found {len(amendments)} amendments")
        return amendments
    
    def _parse_recent_amendments(self, root: ET.Element) -> List[ParsedAmendment]:
        """
        Parse RecentAmendments section (official LIMS format).
        
        Structure:
        <RecentAmendments>
          <Amendment>
            <AmendmentCitation link="2023_29">2023, c. 29</AmendmentCitation>
            <AmendmentDate>2024-01-22</AmendmentDate>
          </Amendment>
        </RecentAmendments>
        """
        amendments = []
        
        recent_amendments = self._find(root, 'RecentAmendments')
        if recent_amendments is None:
            return amendments
        
        amendment_elements = self._findall(recent_amendments, 'Amendment')
        
        for amendment_elem in amendment_elements:
            citation_elem = self._find(amendment_elem, 'AmendmentCitation')
            date_elem = self._find(amendment_elem, 'AmendmentDate')
            
            if citation_elem is not None and date_elem is not None:
                citation = self._get_text(citation_elem)
                date = self._get_text(date_elem)
                
                if date and citation:
                    amendments.append(ParsedAmendment(
                        date=date,
                        bill_number=citation,  # Use citation as bill reference
                        description=f"Amendment by {citation}"
                    ))
        
        logger.info(f"Found {len(amendments)} recent amendments")
        return amendments
    
    def _extract_cross_references(self, sections: List[ParsedSection]) -> List[ParsedCrossReference]:
        """
        Extract cross-references from section content.
        
        Looks for patterns like:
        - "Section 7(1)"
        - "s. 7(1)"
        - "subsection 7(2)"
        """
        import re
        
        cross_references = []
        
        # Pattern to match section references
        # Matches: "Section 7", "s. 7(1)", "subsection 7(2)", etc.
        ref_pattern = r'(?:Section|section|s\.|subsection)\s+(\d+)(?:\((\d+)\))?(?:\(([a-z])\))?'
        
        for section in sections:
            # Search in section content
            matches = re.finditer(ref_pattern, section.content)
            
            for match in matches:
                target_section = match.group(1)
                target_subsection = match.group(2)
                target_clause = match.group(3)
                
                # Build target location
                target = target_section
                if target_subsection:
                    target += f"({target_subsection})"
                if target_clause:
                    target += f"({target_clause})"
                
                # Only add if referencing a different section
                if target != section.number:
                    cross_references.append(ParsedCrossReference(
                        source_section=section.number,
                        target_section=target,
                        citation_text=match.group(0)
                    ))
            
            # Also check subsections
            for subsection in section.subsections:
                matches = re.finditer(ref_pattern, subsection.content)
                for match in matches:
                    target_section = match.group(1)
                    target_subsection = match.group(2)
                    target_clause = match.group(3)
                    
                    target = target_section
                    if target_subsection:
                        target += f"({target_subsection})"
                    if target_clause:
                        target += f"({target_clause})"
                    
                    if target != subsection.number:
                        cross_references.append(ParsedCrossReference(
                            source_section=subsection.number,
                            target_section=target,
                            citation_text=match.group(0)
                        ))
        
        logger.info(f"Extracted {len(cross_references)} cross-references")
        return cross_references


def test_parser():
    """Test the parser with sample XML."""
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>S.C. 1996, c. 23</Chapter>
    <TitleText>Employment Insurance Act</TitleText>
    <EnabledDate>1996-06-30</EnabledDate>
    <ConsolidationDate>2024-01-15</ConsolidationDate>
  </Identification>
  <Body>
    <Part id="I">
      <Number>I</Number>
      <Heading>Unemployment Insurance</Heading>
      <Section id="7">
        <Number>7</Number>
        <Heading>Qualification for benefits</Heading>
        <Subsection id="7-1">
          <Number>1</Number>
          <Text>Subject to this Part, benefits are payable as provided in Section 12.</Text>
        </Subsection>
        <Subsection id="7-2">
          <Number>2</Number>
          <Text>An insured person qualifies if they have accumulated sufficient hours as per s. 7(1).</Text>
        </Subsection>
      </Section>
    </Part>
  </Body>
  <Amendments>
    <Amendment>
      <Date>2024-01-15</Date>
      <BillNumber>C-47</BillNumber>
      <Description>Updated eligibility requirements</Description>
    </Amendment>
  </Amendments>
</Consolidation>"""
    
    parser = CanadianLawXMLParser()
    result = parser.parse_string(sample_xml)
    
    print(f"Title: {result.title}")
    print(f"Chapter: {result.chapter}")
    print(f"Sections: {len(result.sections)}")
    print(f"Amendments: {len(result.amendments)}")
    print(f"Cross-references: {len(result.cross_references)}")
    
    return result


if __name__ == "__main__":
    # Test the parser
    logging.basicConfig(level=logging.INFO)
    test_parser()
