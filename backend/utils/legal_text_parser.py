"""
Legal text parser for extracting structured content from regulatory documents.
Handles section numbering, hierarchies, and cross-references.
"""
import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedSection:
    """Represents a parsed section with its components."""
    number: str
    title: Optional[str]
    content: str
    level: int
    section_type: str  # section, subsection, clause, paragraph
    parent_number: Optional[str] = None
    order_index: int = 0


@dataclass
class ParsedCrossReference:
    """Represents a cross-reference found in text."""
    source_location: str
    target_location: str
    reference_type: str
    citation_text: str
    context: str


class LegalTextParser:
    """
    Parser for legal and regulatory text.
    Extracts sections, subsections, clauses, and cross-references.
    """
    
    # Pattern for section numbers (e.g., "7", "7(1)", "7(1)(a)", "Section 7.1")
    SECTION_PATTERNS = [
        # Standard Canadian format: Section 7(1)(a)
        r'(?:Section|Sec\.|§)\s*(\d+)(?:\((\d+)\))?(?:\(([a-z])\))?(?:\(([ivx]+)\))?',
        # Numeric only: 7.1.2
        r'(\d+)\.(\d+)(?:\.(\d+))?',
        # Article format: Article 7
        r'(?:Article|Art\.)\s*(\d+)',
        # Chapter format: Chapter 3, Part II
        r'(?:Chapter|Ch\.|Part)\s*([IVXLCDM]+|\d+)',
    ]
    
    # Cross-reference patterns
    CROSS_REF_PATTERNS = [
        r'see\s+(?:also\s+)?(?:Section|Sec\.|§)\s*[\d\(\)a-z]+',
        r'pursuant\s+to\s+(?:Section|Sec\.|§)\s*[\d\(\)a-z]+',
        r'as\s+defined\s+in\s+(?:Section|Sec\.|§)\s*[\d\(\)a-z]+',
        r'in\s+accordance\s+with\s+(?:Section|Sec\.|§)\s*[\d\(\)a-z]+',
        r'subject\s+to\s+(?:Section|Sec\.|§)\s*[\d\(\)a-z]+',
        r'notwithstanding\s+(?:Section|Sec\.|§)\s*[\d\(\)a-z]+',
    ]
    
    def __init__(self):
        """Initialize the legal text parser."""
        self.compiled_section_patterns = [re.compile(p, re.IGNORECASE) for p in self.SECTION_PATTERNS]
        self.compiled_cross_ref_patterns = [re.compile(p, re.IGNORECASE) for p in self.CROSS_REF_PATTERNS]
    
    def parse_document(self, text: str) -> Dict[str, Any]:
        """
        Parse a complete regulatory document.
        
        Args:
            text: Full document text
            
        Returns:
            Dictionary containing parsed sections, subsections, clauses, and cross-references
        """
        logger.info("Starting document parsing")
        
        # Split into lines for processing
        lines = text.split('\n')
        
        # Extract sections
        sections = self.extract_sections(lines)
        
        # Extract cross-references
        cross_references = self.extract_cross_references(text, sections)
        
        # Build hierarchy
        hierarchy = self.build_hierarchy(sections)
        
        return {
            'sections': sections,
            'cross_references': cross_references,
            'hierarchy': hierarchy,
            'total_sections': len(sections),
            'total_cross_references': len(cross_references)
        }
    
    def extract_sections(self, lines: List[str]) -> List[ParsedSection]:
        """
        Extract sections from document lines.
        
        Args:
            lines: List of text lines
            
        Returns:
            List of ParsedSection objects
        """
        sections = []
        current_section = None
        current_content = []
        order_index = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check if this line starts a new section
            section_match = self._match_section_header(line)
            
            if section_match:
                # Save previous section if exists
                if current_section:
                    current_section.content = '\n'.join(current_content).strip()
                    sections.append(current_section)
                    order_index += 1
                
                # Start new section
                section_number, title = section_match
                level = self._determine_level(section_number)
                section_type = self._determine_section_type(section_number)
                
                current_section = ParsedSection(
                    number=section_number,
                    title=title,
                    content='',
                    level=level,
                    section_type=section_type,
                    order_index=order_index
                )
                current_content = []
            else:
                # Add to current section content
                if current_section:
                    current_content.append(line)
        
        # Don't forget the last section
        if current_section:
            current_section.content = '\n'.join(current_content).strip()
            sections.append(current_section)
        
        logger.info(f"Extracted {len(sections)} sections")
        return sections
    
    def _match_section_header(self, line: str) -> Optional[Tuple[str, Optional[str]]]:
        """
        Check if a line is a section header and extract number and title.
        
        Args:
            line: Text line to check
            
        Returns:
            Tuple of (section_number, title) or None
        """
        for pattern in self.compiled_section_patterns:
            match = pattern.match(line)
            if match:
                # Extract section number
                groups = match.groups()
                section_number = self._build_section_number(groups)
                
                # Extract title (everything after the number)
                title_start = match.end()
                title = line[title_start:].strip()
                title = title.lstrip('.-:').strip() if title else None
                
                return (section_number, title)
        
        return None
    
    def _build_section_number(self, groups: Tuple) -> str:
        """
        Build section number from regex match groups.
        
        Args:
            groups: Regex match groups
            
        Returns:
            Formatted section number
        """
        # Filter out None values
        parts = [str(g) for g in groups if g is not None]
        
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]}({parts[1]})"
        elif len(parts) == 3:
            return f"{parts[0]}({parts[1]})({parts[2]})"
        elif len(parts) >= 4:
            return f"{parts[0]}({parts[1]})({parts[2]})({parts[3]})"
        
        return '.'.join(parts)
    
    def _determine_level(self, section_number: str) -> int:
        """
        Determine nesting level based on section number.
        
        Args:
            section_number: Section number string
            
        Returns:
            Nesting level (0 = top level)
        """
        # Count parentheses or dots
        paren_count = section_number.count('(')
        dot_count = section_number.count('.')
        
        return max(paren_count, dot_count)
    
    def _determine_section_type(self, section_number: str) -> str:
        """
        Determine section type based on format.
        
        Args:
            section_number: Section number string
            
        Returns:
            Section type string
        """
        if '(' not in section_number and '.' not in section_number:
            return 'section'
        elif section_number.count('(') == 1:
            return 'subsection'
        elif section_number.count('(') == 2:
            return 'clause'
        elif section_number.count('(') >= 3:
            return 'subclause'
        elif '.' in section_number:
            level = section_number.count('.')
            if level == 1:
                return 'subsection'
            elif level == 2:
                return 'clause'
            else:
                return 'subclause'
        
        return 'section'
    
    def extract_cross_references(
        self, 
        text: str, 
        sections: List[ParsedSection]
    ) -> List[ParsedCrossReference]:
        """
        Extract cross-references from document text.
        
        Args:
            text: Full document text
            sections: List of parsed sections
            
        Returns:
            List of ParsedCrossReference objects
        """
        cross_references = []
        
        # Search for cross-references in each section
        for section in sections:
            section_text = f"{section.title or ''} {section.content}"
            
            for pattern in self.compiled_cross_ref_patterns:
                matches = pattern.finditer(section_text)
                
                for match in matches:
                    citation_text = match.group(0)
                    
                    # Extract target section number
                    target_match = re.search(r'(?:Section|Sec\.|§)\s*([\d\(\)a-z]+)', citation_text, re.IGNORECASE)
                    if target_match:
                        target_location = target_match.group(1)
                        
                        # Determine reference type
                        ref_type = self._determine_reference_type(citation_text)
                        
                        # Get context (surrounding text)
                        context_start = max(0, match.start() - 50)
                        context_end = min(len(section_text), match.end() + 50)
                        context = section_text[context_start:context_end].strip()
                        
                        cross_ref = ParsedCrossReference(
                            source_location=section.number,
                            target_location=target_location,
                            reference_type=ref_type,
                            citation_text=citation_text,
                            context=context
                        )
                        cross_references.append(cross_ref)
        
        logger.info(f"Extracted {len(cross_references)} cross-references")
        return cross_references
    
    def _determine_reference_type(self, citation_text: str) -> str:
        """
        Determine the type of cross-reference.
        
        Args:
            citation_text: Citation text
            
        Returns:
            Reference type string
        """
        citation_lower = citation_text.lower()
        
        if 'see also' in citation_lower:
            return 'see_also'
        elif 'pursuant to' in citation_lower:
            return 'pursuant_to'
        elif 'as defined in' in citation_lower:
            return 'definition'
        elif 'in accordance with' in citation_lower:
            return 'accordance'
        elif 'subject to' in citation_lower:
            return 'subject_to'
        elif 'notwithstanding' in citation_lower:
            return 'notwithstanding'
        else:
            return 'refers_to'
    
    def build_hierarchy(self, sections: List[ParsedSection]) -> Dict[str, Any]:
        """
        Build hierarchical structure of sections.
        
        Args:
            sections: List of ParsedSection objects
            
        Returns:
            Hierarchical dictionary
        """
        hierarchy = {
            'top_level': [],
            'parent_map': {}
        }
        
        # Track parent sections by level
        level_stack = {}
        
        for section in sections:
            level = section.level
            
            # Find parent
            if level > 0:
                # Look for parent at previous level
                for parent_level in range(level - 1, -1, -1):
                    if parent_level in level_stack:
                        parent = level_stack[parent_level]
                        section.parent_number = parent.number
                        hierarchy['parent_map'][section.number] = parent.number
                        break
            else:
                # Top-level section
                hierarchy['top_level'].append(section.number)
            
            # Update level stack
            level_stack[level] = section
            
            # Clear deeper levels
            for l in list(level_stack.keys()):
                if l > level:
                    del level_stack[l]
        
        return hierarchy
    
    def extract_subsections(self, section_content: str) -> List[Dict[str, Any]]:
        """
        Extract subsections from section content.
        
        Args:
            section_content: Content of a section
            
        Returns:
            List of subsection dictionaries
        """
        subsections = []
        
        # Pattern for subsections like (1), (2), (a), (b)
        subsection_pattern = re.compile(r'^\s*\(([0-9]+|[a-z]|[ivx]+)\)\s+', re.MULTILINE | re.IGNORECASE)
        
        # Split by subsection markers
        parts = subsection_pattern.split(section_content)
        
        # Process parts (odd indices are subsection numbers, even are content)
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                subsection_number = parts[i]
                content = parts[i + 1].strip()
                
                subsections.append({
                    'number': subsection_number,
                    'content': content,
                    'order': len(subsections)
                })
        
        return subsections
    
    def extract_clauses(self, subsection_content: str) -> List[Dict[str, Any]]:
        """
        Extract clauses from subsection content.
        
        Args:
            subsection_content: Content of a subsection
            
        Returns:
            List of clause dictionaries
        """
        clauses = []
        
        # Pattern for clauses like (a), (b), (i), (ii)
        clause_pattern = re.compile(r'^\s*\(([a-z]|[ivx]+)\)\s+', re.MULTILINE | re.IGNORECASE)
        
        # Split by clause markers
        parts = clause_pattern.split(subsection_content)
        
        # Process parts
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                clause_identifier = parts[i]
                content = parts[i + 1].strip()
                
                clauses.append({
                    'identifier': clause_identifier,
                    'content': content,
                    'order': len(clauses)
                })
        
        return clauses
