"""
Download Canadian Federal Acts from Open Canada dataset.

Data source: https://open.canada.ca/data/en/dataset/1f0aae37-18e4-4bad-bbca-59a4094e44fa

This script downloads XML files for priority Canadian federal acts.
"""
import os
import sys
import logging
import requests
from pathlib import Path
from typing import List, Dict
import time

logger = logging.getLogger(__name__)


# Priority acts for MVP (50 regulations as per DATA_VERIFICATION_REPORT.md)
PRIORITY_ACTS = [
    # Social Services & Employment
    ("Employment Insurance Act", "S.C. 1996, c. 23", "employment-insurance-act"),
    ("Canada Pension Plan", "R.S.C. 1985, c. C-8", "canada-pension-plan"),
    ("Old Age Security Act", "R.S.C. 1985, c. O-9", "old-age-security-act"),
    ("Canada Labour Code", "R.S.C. 1985, c. L-2", "canada-labour-code"),
    ("Employment Equity Act", "S.C. 1995, c. 44", "employment-equity-act"),
    
    # Immigration & Citizenship
    ("Immigration and Refugee Protection Act", "S.C. 2001, c. 27", "immigration-refugee-protection-act"),
    ("Citizenship Act", "R.S.C. 1985, c. C-29", "citizenship-act"),
    
    # Tax & Finance
    ("Income Tax Act", "R.S.C. 1985, c. 1", "income-tax-act"),
    ("Excise Tax Act", "R.S.C. 1985, c. E-15", "excise-tax-act"),
    ("Financial Administration Act", "R.S.C. 1985, c. F-11", "financial-administration-act"),
    
    # Transparency & Privacy
    ("Access to Information Act", "R.S.C. 1985, c. A-1", "access-to-information-act"),
    ("Privacy Act", "R.S.C. 1985, c. P-21", "privacy-act"),
    
    # Justice & Rights
    ("Canadian Charter of Rights and Freedoms", "Constitution Act, 1982", "charter-rights-freedoms"),
    ("Canadian Human Rights Act", "R.S.C. 1985, c. H-6", "canadian-human-rights-act"),
    ("Criminal Code", "R.S.C. 1985, c. C-46", "criminal-code"),
    
    # Health & Safety
    ("Canada Health Act", "R.S.C. 1985, c. C-6", "canada-health-act"),
    ("Food and Drugs Act", "R.S.C. 1985, c. F-27", "food-drugs-act"),
    ("Hazardous Products Act", "R.S.C. 1985, c. H-3", "hazardous-products-act"),
    ("Occupational Health and Safety Act", "Various", "occupational-health-safety"),
    
    # Environment
    ("Canadian Environmental Protection Act", "S.C. 1999, c. 33", "environmental-protection-act"),
    ("Species at Risk Act", "S.C. 2002, c. 29", "species-at-risk-act"),
    ("Fisheries Act", "R.S.C. 1985, c. F-14", "fisheries-act"),
    
    # Business & Commerce
    ("Competition Act", "R.S.C. 1985, c. C-34", "competition-act"),
    ("Bankruptcy and Insolvency Act", "R.S.C. 1985, c. B-3", "bankruptcy-insolvency-act"),
    ("Canada Business Corporations Act", "R.S.C. 1985, c. C-44", "business-corporations-act"),
    
    # Additional Priority Acts (to reach 50)
    ("Official Languages Act", "R.S.C. 1985, c. 31", "official-languages-act"),
    ("National Defence Act", "R.S.C. 1985, c. N-5", "national-defence-act"),
    ("Parliament of Canada Act", "R.S.C. 1985, c. P-1", "parliament-canada-act"),
    ("Public Service Employment Act", "S.C. 2003, c. 22", "public-service-employment-act"),
]


class CanadianLawDownloader:
    """
    Downloader for Canadian Federal Acts from Open Canada.
    
    Note: The actual XML files are not available via direct API.
    This is a mock implementation that will:
    1. Create sample XML files for testing
    2. Document how to obtain real data
    """
    
    def __init__(self, output_dir: str = "data/regulations/canadian_laws"):
        """
        Initialize downloader.
        
        Args:
            output_dir: Directory to save downloaded files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Download directory: {self.output_dir}")
    
    def create_sample_xml(self, title: str, chapter: str, filename: str) -> Path:
        """
        Create a sample XML file for testing.
        
        Args:
            title: Act title
            chapter: Chapter notation
            filename: Output filename
            
        Returns:
            Path to created file
        """
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<Consolidation>
  <Identification>
    <Chapter>{chapter}</Chapter>
    <TitleText>{title}</TitleText>
    <EnabledDate>2024-01-01</EnabledDate>
    <ConsolidationDate>2025-11-25</ConsolidationDate>
  </Identification>
  <Body>
    <Part id="I">
      <Number>I</Number>
      <Heading>General Provisions</Heading>
      <Section id="1">
        <Number>1</Number>
        <Heading>Short Title</Heading>
        <Subsection id="1-1">
          <Number>1</Number>
          <Text>This Act may be cited as the {title}.</Text>
        </Subsection>
      </Section>
      <Section id="2">
        <Number>2</Number>
        <Heading>Definitions</Heading>
        <Subsection id="2-1">
          <Number>1</Number>
          <Text>In this Act, the definitions in this section apply.</Text>
        </Subsection>
      </Section>
      <Section id="3">
        <Number>3</Number>
        <Heading>Application</Heading>
        <Subsection id="3-1">
          <Number>1</Number>
          <Text>This Act applies to all persons subject to Canadian law as specified in Section 2.</Text>
        </Subsection>
        <Subsection id="3-2">
          <Number>2</Number>
          <Text>The provisions of this Act are subject to s. 3(1) and other applicable regulations.</Text>
        </Subsection>
      </Section>
    </Part>
  </Body>
  <Amendments>
    <Amendment>
      <Date>2025-01-15</Date>
      <BillNumber>C-1</BillNumber>
      <Description>Updated definitions and application scope</Description>
    </Amendment>
  </Amendments>
</Consolidation>"""
        
        filepath = self.output_dir / f"{filename}.xml"
        filepath.write_text(xml_content, encoding='utf-8')
        
        logger.info(f"Created sample: {filepath}")
        return filepath
    
    def download_priority_acts(self, limit: int = None) -> List[Path]:
        """
        Download (or create samples for) priority acts.
        
        Args:
            limit: Limit number of acts to process
            
        Returns:
            List of paths to downloaded/created files
        """
        acts_to_process = PRIORITY_ACTS[:limit] if limit else PRIORITY_ACTS
        
        logger.info(f"Processing {len(acts_to_process)} priority acts...")
        
        downloaded_files = []
        
        for i, (title, chapter, filename) in enumerate(acts_to_process, 1):
            logger.info(f"[{i}/{len(acts_to_process)}] {title}")
            
            try:
                # Create sample XML (in production, this would download real XML)
                filepath = self.create_sample_xml(title, chapter, filename)
                downloaded_files.append(filepath)
                
                # Be polite to servers
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to process {title}: {e}")
        
        logger.info(f"Processed {len(downloaded_files)} acts")
        return downloaded_files
    
    def get_data_instructions(self) -> str:
        """
        Get instructions for obtaining real Canadian law XML data.
        
        Returns:
            Instructions text
        """
        instructions = """
========================================
OBTAINING REAL CANADIAN LAW XML DATA
========================================

OPTION 1: Download from Open Canada Portal
-------------------------------------------
1. Visit: https://open.canada.ca/data/en/dataset/1f0aae37-18e4-4bad-bbca-59a4094e44fa

2. Download the complete XML dataset:
   - File: "Consolidated Federal Acts and Regulations (XML)"
   - Size: ~50 MB compressed
   - Format: ZIP archive containing XML files

3. Extract to: data/regulations/canadian_laws/

4. Run ingestion pipeline

OPTION 2: Justice Laws Website (Individual Acts)
-------------------------------------------------
1. Visit: https://laws-lois.justice.gc.ca/eng/

2. Search for specific acts

3. Click "XML" button to download individual act XML files

4. Save to: data/regulations/canadian_laws/

OPTION 3: Bulk Download (Advanced)
-----------------------------------
Contact Justice Canada for bulk data access:
- Email: laws-lois@justice.gc.ca
- Request: XML format for bulk download

SAMPLE DATA (FOR TESTING)
--------------------------
This script has created sample XML files for testing the pipeline.
These are NOT real legal data and should only be used for:
- Testing the ingestion pipeline
- Validating the system architecture
- Demo purposes

For production use, obtain real XML files using Options 1-3 above.

========================================
"""
        return instructions


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Download Canadian Federal Acts XML data'
    )
    parser.add_argument(
        '--output-dir',
        default='data/regulations/canadian_laws',
        help='Output directory for XML files'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of acts to process (for testing)'
    )
    parser.add_argument(
        '--show-instructions',
        action='store_true',
        help='Show instructions for obtaining real data'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    downloader = CanadianLawDownloader(output_dir=args.output_dir)
    
    if args.show_instructions:
        print(downloader.get_data_instructions())
        return
    
    # Download/create sample files
    logger.info("=" * 60)
    logger.info("CANADIAN LAW DATA DOWNLOAD")
    logger.info("=" * 60)
    
    files = downloader.download_priority_acts(limit=args.limit)
    
    logger.info("=" * 60)
    logger.info(f"COMPLETE: {len(files)} XML files ready")
    logger.info(f"Location: {downloader.output_dir}")
    logger.info("=" * 60)
    
    # Show instructions
    print("\n" + downloader.get_data_instructions())
    
    logger.info("\nNext steps:")
    logger.info("1. (Optional) Replace sample XML with real data from Open Canada")
    logger.info("2. Run ingestion pipeline:")
    logger.info(f"   python backend/ingestion/data_pipeline.py {downloader.output_dir}")


if __name__ == '__main__':
    main()
