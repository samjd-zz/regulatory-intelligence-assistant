"""
Unit tests for Canadian Law XML Parser.
Tests the parsing of Canadian Justice Laws XML format.
"""
import pytest
from ingestion.canadian_law_xml_parser import (
    CanadianLawXMLParser,
    ParsedRegulation,
    ParsedSection,
    ParsedAmendment,
    ParsedCrossReference
)


class TestCanadianLawXMLParser:
    """Test suite for CanadianLawXMLParser."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return CanadianLawXMLParser()
    
    @pytest.fixture
    def simple_xml(self):
        """Simple valid XML for basic testing."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>S.C. 1996, c. 23</Chapter>
    <TitleText>Employment Insurance Act</TitleText>
    <EnabledDate>1996-06-30</EnabledDate>
    <ConsolidationDate>2024-01-15</ConsolidationDate>
  </Identification>
  <Body>
    <Section id="1">
      <Number>1</Number>
      <Heading>Short Title</Heading>
      <Text>This Act may be cited as the Employment Insurance Act.</Text>
    </Section>
  </Body>
</Consolidation>"""
    
    @pytest.fixture
    def complex_xml(self):
        """Complex XML with parts, subsections, and amendments."""
        return """<?xml version="1.0" encoding="UTF-8"?>
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
          <Text>An insured person qualifies if they meet requirements in s. 7(1).</Text>
        </Subsection>
      </Section>
      <Section id="8">
        <Number>8</Number>
        <Heading>Application</Heading>
        <Subsection id="8-1">
          <Number>1</Number>
          <Text>Applications must reference Section 7(1) requirements.</Text>
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
    <Amendment>
      <Date>2023-06-30</Date>
      <BillNumber>C-42</BillNumber>
      <Description>Revised benefit calculation</Description>
    </Amendment>
  </Amendments>
</Consolidation>"""
    
    def test_parser_initialization(self, parser):
        """Test parser initializes correctly."""
        assert parser is not None
        assert parser.namespace_map == {}
    
    def test_parse_simple_xml(self, parser, simple_xml):
        """Test parsing simple XML."""
        result = parser.parse_string(simple_xml)
        
        assert isinstance(result, ParsedRegulation)
        assert result.title == "Employment Insurance Act"
        assert result.chapter == "S.C. 1996, c. 23"
        assert result.enabled_date == "1996-06-30"
        assert result.consolidation_date == "2024-01-15"
        assert result.jurisdiction == "federal"
        assert len(result.sections) == 1
    
    def test_parse_identification_section(self, parser, simple_xml):
        """Test parsing Identification section."""
        result = parser.parse_string(simple_xml)
        
        assert result.title == "Employment Insurance Act"
        assert result.chapter == "S.C. 1996, c. 23"
        assert result.act_type == "Statute of Canada"
        assert result.metadata['source'] == "Justice Laws Canada"
        assert result.metadata['format'] == "XML"
    
    def test_determine_act_type(self, parser):
        """Test act type determination from chapter notation."""
        assert parser._determine_act_type("S.C. 1996, c. 23") == "Statute of Canada"
        assert parser._determine_act_type("R.S.C. 1985, c. C-8") == "Revised Statutes of Canada"
        assert parser._determine_act_type("S.O. 2000, c. 5") == "Statute of Ontario"
        assert parser._determine_act_type("Unknown") == "Act"
    
    def test_parse_sections(self, parser, simple_xml):
        """Test section parsing."""
        result = parser.parse_string(simple_xml)
        
        assert len(result.sections) == 1
        section = result.sections[0]
        
        assert isinstance(section, ParsedSection)
        assert section.number == "1"
        assert section.title == "Short Title"
        assert "This Act may be cited" in section.content
        assert section.level == 1
    
    def test_parse_parts_and_sections(self, parser, complex_xml):
        """Test parsing parts with multiple sections."""
        result = parser.parse_string(complex_xml)
        
        assert len(result.sections) == 2
        
        # Check first section
        section1 = result.sections[0]
        assert section1.number == "7"
        assert section1.title == "Qualification for benefits"
        assert section1.level == 2  # Inside a Part
        
        # Check second section
        section2 = result.sections[1]
        assert section2.number == "8"
        assert section2.title == "Application"
    
    def test_parse_subsections(self, parser, complex_xml):
        """Test subsection parsing."""
        result = parser.parse_string(complex_xml)
        
        section = result.sections[0]  # Section 7
        assert len(section.subsections) == 2
        
        # Check subsection structure
        subsection1 = section.subsections[0]
        assert subsection1.number == "7(1)"
        assert "benefits are payable" in subsection1.content
        assert subsection1.level == 3  # Part > Section > Subsection
        
        subsection2 = section.subsections[1]
        assert subsection2.number == "7(2)"
        assert "insured person qualifies" in subsection2.content
    
    def test_parse_amendments(self, parser, complex_xml):
        """Test amendment parsing."""
        result = parser.parse_string(complex_xml)
        
        assert len(result.amendments) == 2
        
        # Check first amendment
        amendment1 = result.amendments[0]
        assert isinstance(amendment1, ParsedAmendment)
        assert amendment1.date == "2024-01-15"
        assert amendment1.bill_number == "C-47"
        assert "Updated eligibility" in amendment1.description
        
        # Check second amendment
        amendment2 = result.amendments[1]
        assert amendment2.date == "2023-06-30"
        assert amendment2.bill_number == "C-42"
    
    def test_extract_cross_references(self, parser, complex_xml):
        """Test cross-reference extraction."""
        result = parser.parse_string(complex_xml)
        
        assert len(result.cross_references) > 0
        
        # Check cross-reference structure
        cross_ref = result.cross_references[0]
        assert isinstance(cross_ref, ParsedCrossReference)
        # Source can be from main section or subsection
        assert cross_ref.source_section in ["7", "7(1)", "7(2)", "8(1)"]
        assert cross_ref.target_section != cross_ref.source_section
        assert len(cross_ref.citation_text) > 0
    
    def test_cross_reference_patterns(self, parser):
        """Test various cross-reference patterns."""
        xml_with_refs = """<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>Test</Chapter>
    <TitleText>Test Act</TitleText>
  </Identification>
  <Body>
    <Section id="1">
      <Number>1</Number>
      <Text>Reference to Section 5 and s. 10(2) and subsection 15(3).</Text>
    </Section>
  </Body>
</Consolidation>"""
        
        result = parser.parse_string(xml_with_refs)
        
        # Should find 3 cross-references
        assert len(result.cross_references) == 3
        
        targets = [ref.target_section for ref in result.cross_references]
        assert "5" in targets
        assert "10(2)" in targets
        assert "15(3)" in targets
    
    def test_full_text_generation(self, parser, complex_xml):
        """Test full text generation."""
        result = parser.parse_string(complex_xml)
        
        assert len(result.full_text) > 0
        assert "PART I" in result.full_text
        assert "Unemployment Insurance" in result.full_text
        assert "Section 7" in result.full_text
        assert "Qualification for benefits" in result.full_text
    
    def test_missing_identification_raises_error(self, parser):
        """Test that missing Identification section raises error."""
        invalid_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Body>
    <Section id="1">
      <Number>1</Number>
      <Text>Test</Text>
    </Section>
  </Body>
</Consolidation>"""
        
        with pytest.raises(ValueError, match="No Identification section found"):
            parser.parse_string(invalid_xml)
    
    def test_invalid_xml_raises_error(self, parser):
        """Test that invalid XML raises error."""
        invalid_xml = "This is not XML"
        
        with pytest.raises(ValueError, match="Failed to parse XML"):
            parser.parse_string(invalid_xml)
    
    def test_empty_sections(self, parser):
        """Test handling of empty body."""
        xml_no_sections = """<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>Test</Chapter>
    <TitleText>Empty Act</TitleText>
  </Identification>
  <Body>
  </Body>
</Consolidation>"""
        
        result = parser.parse_string(xml_no_sections)
        assert len(result.sections) == 0
        assert len(result.amendments) == 0
    
    def test_metadata_structure(self, parser, simple_xml):
        """Test metadata dictionary structure."""
        result = parser.parse_string(simple_xml)
        
        assert 'chapter' in result.metadata
        assert 'enabled_date' in result.metadata
        assert 'consolidation_date' in result.metadata
        assert 'act_type' in result.metadata
        assert 'source' in result.metadata
        assert 'format' in result.metadata
        
        assert result.metadata['source'] == "Justice Laws Canada"
        assert result.metadata['format'] == "XML"
    
    def test_section_without_number_skipped(self, parser):
        """Test that sections without numbers are skipped."""
        xml_no_number = """<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>Test</Chapter>
    <TitleText>Test Act</TitleText>
  </Identification>
  <Body>
    <Section id="invalid">
      <Heading>No Number</Heading>
      <Text>This section has no number element.</Text>
    </Section>
    <Section id="valid">
      <Number>1</Number>
      <Text>Valid section.</Text>
    </Section>
  </Body>
</Consolidation>"""
        
        result = parser.parse_string(xml_no_number)
        
        # Should only parse the valid section
        assert len(result.sections) == 1
        assert result.sections[0].number == "1"
    
    def test_amendments_without_date_skipped(self, parser):
        """Test that amendments without dates are skipped."""
        xml_invalid_amendment = """<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>Test</Chapter>
    <TitleText>Test Act</TitleText>
  </Identification>
  <Body>
    <Section id="1">
      <Number>1</Number>
      <Text>Test</Text>
    </Section>
  </Body>
  <Amendments>
    <Amendment>
      <BillNumber>C-1</BillNumber>
      <Description>No date</Description>
    </Amendment>
    <Amendment>
      <Date>2024-01-15</Date>
      <Description>Valid amendment</Description>
    </Amendment>
  </Amendments>
</Consolidation>"""
        
        result = parser.parse_string(xml_invalid_amendment)
        
        # Should only parse valid amendment
        assert len(result.amendments) == 1
        assert result.amendments[0].date == "2024-01-15"
    
    def test_namespace_detection(self, parser):
        """Test namespace detection for namespaced XML."""
        namespaced_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ns:Consolidation xmlns:ns="http://example.com/legal">
  <ns:Identification>
    <ns:Chapter>Test</ns:Chapter>
    <ns:TitleText>Test Act</ns:TitleText>
  </ns:Identification>
  <ns:Body>
    <ns:Section id="1">
      <ns:Number>1</ns:Number>
      <ns:Text>Test</ns:Text>
    </ns:Section>
  </ns:Body>
</ns:Consolidation>"""
        
        result = parser.parse_string(namespaced_xml)
        
        # Should parse correctly despite namespace
        assert result.title == "Test Act"
        assert len(result.sections) == 1
    
    def test_self_referencing_section_excluded(self, parser):
        """Test that self-referencing sections are not included in cross-references."""
        xml_self_ref = """<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>Test</Chapter>
    <TitleText>Test Act</TitleText>
  </Identification>
  <Body>
    <Section id="5">
      <Number>5</Number>
      <Text>This section references Section 5 and Section 10.</Text>
    </Section>
  </Body>
</Consolidation>"""
        
        result = parser.parse_string(xml_self_ref)
        
        # Should only find reference to Section 10, not self-reference to 5
        cross_refs = [ref for ref in result.cross_references if ref.source_section == "5"]
        targets = [ref.target_section for ref in cross_refs]
        
        assert "5" not in targets  # Self-reference excluded
        assert "10" in targets  # External reference included


class TestParsedDataClasses:
    """Test data classes."""
    
    def test_parsed_section_creation(self):
        """Test ParsedSection creation."""
        section = ParsedSection(
            section_id="7",
            number="7",
            title="Test Section",
            content="Test content",
            level=1
        )
        
        assert section.section_id == "7"
        assert section.number == "7"
        assert section.title == "Test Section"
        assert section.content == "Test content"
        assert section.level == 1
        assert len(section.subsections) == 0
        assert section.parent_id is None
    
    def test_parsed_amendment_creation(self):
        """Test ParsedAmendment creation."""
        amendment = ParsedAmendment(
            date="2024-01-15",
            bill_number="C-47",
            description="Test amendment"
        )
        
        assert amendment.date == "2024-01-15"
        assert amendment.bill_number == "C-47"
        assert amendment.description == "Test amendment"
    
    def test_parsed_cross_reference_creation(self):
        """Test ParsedCrossReference creation."""
        cross_ref = ParsedCrossReference(
            source_section="7",
            target_section="12",
            citation_text="Section 12"
        )
        
        assert cross_ref.source_section == "7"
        assert cross_ref.target_section == "12"
        assert cross_ref.citation_text == "Section 12"
    
    def test_parsed_regulation_creation(self):
        """Test ParsedRegulation creation."""
        regulation = ParsedRegulation(
            title="Test Act",
            chapter="S.C. 1996, c. 23",
            act_type="Statute of Canada",
            enabled_date="1996-06-30",
            consolidation_date="2024-01-15",
            jurisdiction="federal",
            full_text="Test text",
            sections=[],
            amendments=[],
            cross_references=[],
            metadata={}
        )
        
        assert regulation.title == "Test Act"
        assert regulation.chapter == "S.C. 1996, c. 23"
        assert regulation.act_type == "Statute of Canada"
        assert regulation.jurisdiction == "federal"
        assert len(regulation.sections) == 0
        assert len(regulation.amendments) == 0
        assert len(regulation.cross_references) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
