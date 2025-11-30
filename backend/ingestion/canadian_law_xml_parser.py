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
            
            # Determine format: Statute (real format) vs Consolidation (test format)
            root_tag = root.tag.split('}')[-1] if '}' in root.tag else root.tag
            
            if root_tag == 'Statute':
                return self._parse_statute(root)
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
        """Safely get text from element."""
        if element is not None and element.text:
            return element.text.strip()
        return default
    
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
        
        logger.info(f"Parsing regulation: {title}")
        
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
            jurisdiction='federal',
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
        logger.info("Parsing Statute element (Justice Canada format)")
        
        # Extract title - check multiple possible locations
        title = self._extract_statute_title(root)
        
        logger.info(f"Parsing regulation: {title}")
        
        # Extract chapter/citation
        chapter = ""
        chapter_elem = self._find(root, 'ChapterNumber')
        if chapter_elem is not None:
            chapter = self._get_text(chapter_elem)
        
        # Determine act type
        act_type = self._determine_act_type(chapter) if chapter else "Act"
        
        # Parse body sections
        body = self._find(root, 'Body')
        sections = []
        full_text_parts = []
        
        if body is not None:
            # Find all direct Section elements
            section_elements = self._findall(body, 'Section')
            
            for section_elem in section_elements:
                section, text = self._parse_statute_section(section_elem)
                if section:
                    sections.append(section)
                    full_text_parts.append(text)
        
        # Build full text
        full_text = "\n\n".join(full_text_parts) if full_text_parts else ""
        
        # Extract metadata from attributes
        metadata = {
            'chapter': chapter,
            'act_type': act_type,
            'source': 'Justice Laws Canada',
            'format': 'Statute XML'
        }
        
        # Add any attributes from root
        if hasattr(root, 'attrib'):
            for key, value in root.attrib.items():
                clean_key = key.split('}')[-1] if '}' in key else key
                metadata[f'attr_{clean_key}'] = value
        
        regulation = ParsedRegulation(
            title=title,
            chapter=chapter,
            act_type=act_type,
            enabled_date=None,  # Not in Statute format
            consolidation_date=None,  # Not in Statute format
            jurisdiction='federal',
            full_text=full_text,
            sections=sections,
            amendments=[],  # Amendments handled differently in this format
            cross_references=self._extract_cross_references(sections),
            metadata=metadata
        )
        
        logger.info(f"Parsed {len(sections)} sections from Statute format")
        return regulation
    
    def _extract_statute_title(self, root: ET.Element) -> str:
        """
        Extract title from Statute format XML.
        
        Tries multiple strategies in order:
        1. Direct <Title> element
        2. <TitleText> element
        3. First <Heading> with <TitleText>
        4. Long title from <LongTitle> or <RunningHead>
        5. Filename-based fallback
        """
        # Strategy 1: Direct <Title> element
        title_elem = self._find(root, 'Title')
        if title_elem is not None:
            title = self._get_text(title_elem)
            if title:
                return title
        
        # Strategy 2: Direct <TitleText> element
        title_text_elem = self._find(root, 'TitleText')
        if title_text_elem is not None:
            title = self._get_text(title_text_elem)
            if title:
                return title
        
        # Strategy 3: First <Heading> with <TitleText> (usually the act title)
        headings = self._findall(root, './/Heading')
        if headings:
            for heading in headings[:3]:  # Check first 3 headings
                # Skip headings with Labels (these are part titles, not act titles)
                if self._find(heading, 'Label') is None:
                    title_text = self._find(heading, 'TitleText')
                    if title_text is not None:
                        title = self._get_text(title_text)
                        if title and len(title) > 10:  # Act titles are usually longer
                            return title
        
        # Strategy 4: LongTitle or RunningHead
        long_title = self._find(root, 'LongTitle')
        if long_title is not None:
            title = self._get_text(long_title)
            if title:
                return title
        
        running_head = self._find(root, 'RunningHead')
        if running_head is not None:
            title = self._get_text(running_head)
            if title:
                return title
        
        # Strategy 5: Look in Identification section (some files have this)
        identification = self._find(root, 'Identification')
        if identification is not None:
            id_title = self._find(identification, 'TitleText')
            if id_title is not None:
                title = self._get_text(id_title)
                if title:
                    return title
        
        # Fallback: Return a descriptive default
        return "Untitled Statute"
    
    def _parse_statute_section(
        self,
        section_elem: ET.Element,
        level: int = 1,
        parent_id: Optional[str] = None
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
        
        if not number:
            return None, ""
        
        # Build content and full text
        content_parts = []
        full_text_parts = [f"Section {number}"]
        
        if title:
            full_text_parts.append(f"{title}")
            content_parts.append(title)
        
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
            
            # Get subsection title (if any)
            sub_margin_elem = self._find(subsection_elem, 'MarginalNote')
            sub_title = self._get_text(sub_margin_elem) if sub_margin_elem is not None else None
            
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
