"""
Ontario e-Laws Sitemap Parser.

Parses the sitemap XML from Ontario's e-Laws system to discover available regulations.
Source: https://www.ontario.ca/laws

This parser extracts metadata about Ontario regulations from the sitemap,
which can then be used to download the actual regulation content.

Sitemap structure:
<urlset xmlns:law="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.ontario.ca/laws/regulation/r06183</loc>
    <lastmod>2015-04-20</lastmod>
    <law:state>source</law:state>
    <law:title>Rules of Vintners Quality Alliance Ontario...</law:title>
    <law:act>VINTNERS QUALITY ALLIANCE ACT, 1999</law:act>
    <law:year>2006</law:year>
    <law:chapter>183</law:chapter>
    <law:volume>O. Reg. 183/06</law:volume>
    <law:datefrom>2006-05-05</law:datefrom>
  </url>
  ...
</urlset>
"""
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class OntarioRegulationMetadata:
    """Metadata for an Ontario regulation extracted from sitemap."""
    
    url: str
    title: str
    parent_act: str
    year: int
    chapter: str
    volume: str  # Citation like "O. Reg. 183/06"
    last_modified: Optional[datetime] = None
    date_from: Optional[datetime] = None
    state: Optional[str] = None  # e.g., "source", "consolidated"
    
    @property
    def regulation_id(self) -> str:
        """Extract regulation ID from URL or volume."""
        # URL format: https://www.ontario.ca/laws/regulation/r06183
        # Extract: r06183
        return self.url.split('/')[-1]
    
    @property
    def citation(self) -> str:
        """Return formatted citation."""
        return self.volume
    
    @property
    def jurisdiction(self) -> str:
        """Always Ontario."""
        return 'ontario'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'url': self.url,
            'regulation_id': self.regulation_id,
            'title': self.title,
            'parent_act': self.parent_act,
            'year': self.year,
            'chapter': self.chapter,
            'volume': self.volume,
            'citation': self.citation,
            'jurisdiction': self.jurisdiction,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'date_from': self.date_from.isoformat() if self.date_from else None,
            'state': self.state,
        }


class OntarioSitemapParser:
    """
    Parser for Ontario e-Laws sitemap XML.
    
    Extracts metadata about available regulations from the sitemap
    to facilitate bulk downloading and ingestion.
    """
    
    # XML namespaces used in Ontario sitemap
    NAMESPACES = {
        'sitemap': 'http://www.sitemaps.org/schemas/sitemap/0.9',
        'law': 'http://www.sitemaps.org/schemas/sitemap/0.9'
    }
    
    def __init__(self):
        """Initialize sitemap parser."""
        logger.info("Initialized Ontario sitemap parser")
    
    def parse_sitemap(self, xml_path: str) -> List[OntarioRegulationMetadata]:
        """
        Parse Ontario e-Laws sitemap XML file.
        
        Args:
            xml_path: Path to sitemap XML file
            
        Returns:
            List of OntarioRegulationMetadata objects
        """
        logger.info(f"Parsing Ontario sitemap: {xml_path}")
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            regulations = []
            
            # Find all <url> elements
            for url_elem in root.findall('sitemap:url', self.NAMESPACES):
                try:
                    metadata = self._parse_url_entry(url_elem)
                    if metadata:
                        regulations.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to parse URL entry: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(regulations)} Ontario regulations from sitemap")
            return regulations
            
        except Exception as e:
            logger.error(f"Error parsing Ontario sitemap: {e}")
            raise
    
    def _parse_url_entry(self, url_elem: ET.Element) -> Optional[OntarioRegulationMetadata]:
        """
        Parse a single <url> entry from sitemap.
        
        Args:
            url_elem: XML <url> element
            
        Returns:
            OntarioRegulationMetadata or None if parsing fails
        """
        # Extract required fields
        loc = self._get_text(url_elem, 'sitemap:loc')
        title = self._get_text(url_elem, 'law:title')
        parent_act = self._get_text(url_elem, 'law:act')
        year_str = self._get_text(url_elem, 'law:year')
        chapter = self._get_text(url_elem, 'law:chapter')
        volume = self._get_text(url_elem, 'law:volume')
        
        # Validate required fields
        if not all([loc, title, volume]):
            logger.warning(f"Missing required fields in URL entry")
            return None
        
        # Extract optional fields
        last_modified = self._parse_date(self._get_text(url_elem, 'sitemap:lastmod'))
        date_from = self._parse_date(self._get_text(url_elem, 'law:datefrom'))
        state = self._get_text(url_elem, 'law:state')
        
        # Parse year as integer
        try:
            year = int(year_str) if year_str else 0
        except (ValueError, TypeError):
            year = 0
        
        return OntarioRegulationMetadata(
            url=loc,
            title=title,
            parent_act=parent_act or "Unknown Act",
            year=year,
            chapter=chapter or "",
            volume=volume,
            last_modified=last_modified,
            date_from=date_from,
            state=state
        )
    
    def _get_text(self, parent: ET.Element, tag: str) -> Optional[str]:
        """
        Safely get text content from XML element.
        
        Args:
            parent: Parent XML element
            tag: Tag name (with namespace prefix)
            
        Returns:
            Text content or None
        """
        elem = parent.find(tag, self.NAMESPACES)
        if elem is not None and elem.text:
            return elem.text.strip()
        return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            datetime object or None
        """
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            logger.warning(f"Failed to parse date: {date_str}")
            return None
    
    def filter_by_act(
        self,
        regulations: List[OntarioRegulationMetadata],
        act_name: str
    ) -> List[OntarioRegulationMetadata]:
        """
        Filter regulations by parent act name.
        
        Args:
            regulations: List of regulations
            act_name: Act name to filter by (case-insensitive partial match)
            
        Returns:
            Filtered list of regulations
        """
        act_lower = act_name.lower()
        return [
            reg for reg in regulations
            if act_lower in reg.parent_act.lower()
        ]
    
    def filter_by_year(
        self,
        regulations: List[OntarioRegulationMetadata],
        min_year: Optional[int] = None,
        max_year: Optional[int] = None
    ) -> List[OntarioRegulationMetadata]:
        """
        Filter regulations by year range.
        
        Args:
            regulations: List of regulations
            min_year: Minimum year (inclusive)
            max_year: Maximum year (inclusive)
            
        Returns:
            Filtered list of regulations
        """
        filtered = regulations
        
        if min_year is not None:
            filtered = [reg for reg in filtered if reg.year >= min_year]
        
        if max_year is not None:
            filtered = [reg for reg in filtered if reg.year <= max_year]
        
        return filtered
    
    def get_statistics(self, regulations: List[OntarioRegulationMetadata]) -> Dict:
        """
        Get statistics about the regulations in the sitemap.
        
        Args:
            regulations: List of regulations
            
        Returns:
            Dictionary with statistics
        """
        if not regulations:
            return {
                'total': 0,
                'years': {},
                'top_acts': {},
                'date_range': None
            }
        
        # Count by year
        years = {}
        for reg in regulations:
            if reg.year:
                years[reg.year] = years.get(reg.year, 0) + 1
        
        # Count by parent act (top 10)
        acts = {}
        for reg in regulations:
            acts[reg.parent_act] = acts.get(reg.parent_act, 0) + 1
        
        top_acts = dict(sorted(acts.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Date range
        dates = [reg.date_from for reg in regulations if reg.date_from]
        date_range = None
        if dates:
            date_range = {
                'earliest': min(dates).isoformat(),
                'latest': max(dates).isoformat()
            }
        
        return {
            'total': len(regulations),
            'years': dict(sorted(years.items())),
            'top_acts': top_acts,
            'date_range': date_range
        }


# Convenience functions

def parse_ontario_sitemap(xml_path: str) -> List[OntarioRegulationMetadata]:
    """
    Convenience function to parse Ontario sitemap.
    
    Args:
        xml_path: Path to sitemap XML file
        
    Returns:
        List of regulation metadata
    """
    parser = OntarioSitemapParser()
    return parser.parse_sitemap(xml_path)


def export_to_csv(regulations: List[OntarioRegulationMetadata], output_path: str):
    """
    Export regulations to CSV file.
    
    Args:
        regulations: List of regulations
        output_path: Path to output CSV file
    """
    import csv
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if not regulations:
            return
        
        # Get fieldnames from first regulation
        fieldnames = list(regulations[0].to_dict().keys())
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for reg in regulations:
            writer.writerow(reg.to_dict())
    
    logger.info(f"Exported {len(regulations)} regulations to {output_path}")


def export_to_json(regulations: List[OntarioRegulationMetadata], output_path: str):
    """
    Export regulations to JSON file.
    
    Args:
        regulations: List of regulations
        output_path: Path to output JSON file
    """
    import json
    
    data = [reg.to_dict() for reg in regulations]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Exported {len(regulations)} regulations to {output_path}")


# CLI interface
if __name__ == "__main__":
    import sys
    import json
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Usage: python ontario_sitemap_parser.py <sitemap.xml> [--stats] [--export-csv output.csv] [--export-json output.json]")
        print("\nOptions:")
        print("  --stats              Show statistics about regulations")
        print("  --export-csv FILE    Export to CSV file")
        print("  --export-json FILE   Export to JSON file")
        print("  --filter-act NAME    Filter by parent act name")
        print("  --filter-year-min Y  Filter by minimum year")
        print("  --filter-year-max Y  Filter by maximum year")
        sys.exit(1)
    
    sitemap_path = sys.argv[1]
    
    # Parse sitemap
    parser = OntarioSitemapParser()
    regulations = parser.parse_sitemap(sitemap_path)
    
    # Apply filters if specified
    if '--filter-act' in sys.argv:
        idx = sys.argv.index('--filter-act')
        if idx + 1 < len(sys.argv):
            act_name = sys.argv[idx + 1]
            regulations = parser.filter_by_act(regulations, act_name)
            print(f"Filtered to {len(regulations)} regulations for act: {act_name}")
    
    if '--filter-year-min' in sys.argv:
        idx = sys.argv.index('--filter-year-min')
        if idx + 1 < len(sys.argv):
            min_year = int(sys.argv[idx + 1])
            regulations = parser.filter_by_year(regulations, min_year=min_year)
            print(f"Filtered to {len(regulations)} regulations from year {min_year}+")
    
    if '--filter-year-max' in sys.argv:
        idx = sys.argv.index('--filter-year-max')
        if idx + 1 < len(sys.argv):
            max_year = int(sys.argv[idx + 1])
            regulations = parser.filter_by_year(regulations, max_year=max_year)
            print(f"Filtered to {len(regulations)} regulations up to year {max_year}")
    
    # Show statistics
    if '--stats' in sys.argv or len(sys.argv) == 2:
        stats = parser.get_statistics(regulations)
        print("\n=== Ontario Regulations Statistics ===")
        print(f"Total regulations: {stats['total']}")
        print(f"\nTop 10 Parent Acts:")
        for act, count in stats['top_acts'].items():
            print(f"  {act}: {count}")
        print(f"\nRegulations by Year:")
        for year, count in sorted(stats['years'].items(), reverse=True)[:10]:
            print(f"  {year}: {count}")
        if stats['date_range']:
            print(f"\nDate Range:")
            print(f"  Earliest: {stats['date_range']['earliest']}")
            print(f"  Latest: {stats['date_range']['latest']}")
    
    # Export if requested
    if '--export-csv' in sys.argv:
        idx = sys.argv.index('--export-csv')
        if idx + 1 < len(sys.argv):
            export_to_csv(regulations, sys.argv[idx + 1])
    
    if '--export-json' in sys.argv:
        idx = sys.argv.index('--export-json')
        if idx + 1 < len(sys.argv):
            export_to_json(regulations, sys.argv[idx + 1])
    
    # Print sample regulations
    if not any(arg in sys.argv for arg in ['--export-csv', '--export-json']):
        print(f"\n=== Sample Regulations (first 5) ===")
        for reg in regulations[:5]:
            print(f"\nTitle: {reg.title}")
            print(f"Citation: {reg.citation}")
            print(f"Parent Act: {reg.parent_act}")
            print(f"Year: {reg.year}")
            print(f"URL: {reg.url}")
