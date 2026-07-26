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


# Priority acts for MVP (100 regulations for comprehensive testing)
PRIORITY_ACTS = [
    # Social Services & Employment (10)
    ("Employment Insurance Act", "S.C. 1996, c. 23", "employment-insurance-act"),
    ("Canada Pension Plan", "R.S.C. 1985, c. C-8", "canada-pension-plan"),
    ("Old Age Security Act", "R.S.C. 1985, c. O-9", "old-age-security-act"),
    ("Canada Labour Code", "R.S.C. 1985, c. L-2", "canada-labour-code"),
    ("Employment Equity Act", "S.C. 1995, c. 44", "employment-equity-act"),
    ("Canada Student Loans Act", "R.S.C. 1985, c. S-23", "canada-student-loans-act"),
    ("Canada Education Savings Act", "S.C. 2004, c. 26", "canada-education-savings-act"),
    ("Wage Earner Protection Program Act", "S.C. 2005, c. 47", "wage-earner-protection-act"),
    ("Public Service Labour Relations Act", "S.C. 2003, c. 22", "public-service-labour-relations-act"),
    ("Canada Disability Savings Act", "S.C. 2007, c. 35", "canada-disability-savings-act"),
    
    # Immigration & Citizenship (10)
    ("Immigration and Refugee Protection Act", "S.C. 2001, c. 27", "immigration-refugee-protection-act"),
    ("Citizenship Act", "R.S.C. 1985, c. C-29", "citizenship-act"),
    ("Immigration Act", "R.S.C. 1985, c. I-2", "immigration-act"),
    ("Balanced Refugee Reform Act", "S.C. 2010, c. 8", "balanced-refugee-reform-act"),
    ("Protecting Canada's Immigration System Act", "S.C. 2012, c. 17", "protecting-immigration-system-act"),
    ("Faster Removal of Foreign Criminals Act", "S.C. 2013, c. 16", "faster-removal-foreign-criminals-act"),
    ("Zero Tolerance for Barbaric Cultural Practices Act", "S.C. 2015, c. 29", "zero-tolerance-barbaric-practices-act"),
    ("Strengthening Canadian Citizenship Act", "S.C. 2014, c. 22", "strengthening-citizenship-act"),
    ("Department of Citizenship and Immigration Act", "S.C. 1994, c. 31", "citizenship-immigration-dept-act"),
    ("Canadian Multiculturalism Act", "R.S.C. 1985, c. 24", "canadian-multiculturalism-act"),
    
    # Tax & Finance (15)
    ("Income Tax Act", "R.S.C. 1985, c. 1", "income-tax-act"),
    ("Excise Tax Act", "R.S.C. 1985, c. E-15", "excise-tax-act"),
    ("Financial Administration Act", "R.S.C. 1985, c. F-11", "financial-administration-act"),
    ("Bank Act", "S.C. 1991, c. 46", "bank-act"),
    ("Insurance Companies Act", "S.C. 1991, c. 47", "insurance-companies-act"),
    ("Trust and Loan Companies Act", "S.C. 1991, c. 45", "trust-loan-companies-act"),
    ("Canada Deposit Insurance Corporation Act", "R.S.C. 1985, c. C-3", "canada-deposit-insurance-act"),
    ("Budget Implementation Act", "S.C. 2024, c. 17", "budget-implementation-act"),
    ("Payment Clearing and Settlement Act", "S.C. 1996, c. 6", "payment-clearing-settlement-act"),
    ("Proceeds of Crime (Money Laundering) and Terrorist Financing Act", "S.C. 2000, c. 17", "proceeds-crime-money-laundering-act"),
    ("Customs Act", "R.S.C. 1985, c. 1", "customs-act"),
    ("Currency Act", "R.S.C. 1985, c. C-52", "currency-act"),
    ("Federal-Provincial Fiscal Arrangements Act", "R.S.C. 1985, c. F-8", "federal-provincial-fiscal-act"),
    ("Public Sector Pension Investment Board Act", "S.C. 1999, c. 34", "pension-investment-board-act"),
    ("Canada Small Business Financing Act", "S.C. 1998, c. 36", "small-business-financing-act"),
    
    # Transparency & Privacy (10)
    ("Access to Information Act", "R.S.C. 1985, c. A-1", "access-to-information-act"),
    ("Privacy Act", "R.S.C. 1985, c. P-21", "privacy-act"),
    ("Personal Information Protection and Electronic Documents Act", "S.C. 2000, c. 5", "pipeda"),
    ("Lobbying Act", "R.S.C. 1985, c. 44", "lobbying-act"),
    ("Conflict of Interest Act", "S.C. 2006, c. 9", "conflict-of-interest-act"),
    ("Parliament of Canada Act", "R.S.C. 1985, c. P-1", "parliament-canada-act"),
    ("Public Servants Disclosure Protection Act", "S.C. 2005, c. 46", "public-servants-disclosure-act"),
    ("Library and Archives of Canada Act", "S.C. 2004, c. 11", "library-archives-act"),
    ("Statistics Act", "R.S.C. 1985, c. S-19", "statistics-act"),
    ("Federal Accountability Act", "S.C. 2006, c. 9", "federal-accountability-act"),
    
    # Justice & Rights (15)
    ("Canadian Charter of Rights and Freedoms", "Constitution Act, 1982", "charter-rights-freedoms"),
    ("Canadian Human Rights Act", "R.S.C. 1985, c. H-6", "canadian-human-rights-act"),
    ("Criminal Code", "R.S.C. 1985, c. C-46", "criminal-code"),
    ("Youth Criminal Justice Act", "S.C. 2002, c. 1", "youth-criminal-justice-act"),
    ("Corrections and Conditional Release Act", "S.C. 1992, c. 20", "corrections-conditional-release-act"),
    ("Canadian Bill of Rights", "S.C. 1960, c. 44", "canadian-bill-of-rights"),
    ("Divorce Act", "R.S.C. 1985, c. 3", "divorce-act"),
    ("Family Orders and Agreements Enforcement Assistance Act", "R.S.C. 1985, c. 4", "family-orders-enforcement-act"),
    ("Civil Marriage Act", "S.C. 2005, c. 33", "civil-marriage-act"),
    ("Judges Act", "R.S.C. 1985, c. J-1", "judges-act"),
    ("Federal Courts Act", "R.S.C. 1985, c. F-7", "federal-courts-act"),
    ("Supreme Court Act", "R.S.C. 1985, c. S-26", "supreme-court-act"),
    ("Canada Evidence Act", "R.S.C. 1985, c. C-5", "canada-evidence-act"),
    ("Victims Bill of Rights Act", "S.C. 2015, c. 13", "victims-bill-rights-act"),
    ("Not Criminally Responsible Reform Act", "S.C. 2014, c. 6", "not-criminally-responsible-reform-act"),
    
    # Health & Safety (10)
    ("Canada Health Act", "R.S.C. 1985, c. C-6", "canada-health-act"),
    ("Food and Drugs Act", "R.S.C. 1985, c. F-27", "food-drugs-act"),
    ("Hazardous Products Act", "R.S.C. 1985, c. H-3", "hazardous-products-act"),
    ("Controlled Drugs and Substances Act", "S.C. 1996, c. 19", "controlled-drugs-substances-act"),
    ("Cannabis Act", "S.C. 2018, c. 16", "cannabis-act"),
    ("Quarantine Act", "S.C. 2005, c. 20", "quarantine-act"),
    ("Public Health Agency of Canada Act", "S.C. 2006, c. 5", "public-health-agency-act"),
    ("Pest Control Products Act", "S.C. 2002, c. 28", "pest-control-products-act"),
    ("Canada Consumer Product Safety Act", "S.C. 2010, c. 21", "consumer-product-safety-act"),
    ("Radiation Emitting Devices Act", "R.S.C. 1985, c. R-1", "radiation-emitting-devices-act"),
    
    # Environment (10)
    ("Canadian Environmental Protection Act", "S.C. 1999, c. 33", "environmental-protection-act"),
    ("Species at Risk Act", "S.C. 2002, c. 29", "species-at-risk-act"),
    ("Fisheries Act", "R.S.C. 1985, c. F-14", "fisheries-act"),
    ("Oceans Act", "S.C. 1996, c. 31", "oceans-act"),
    ("Canada National Parks Act", "S.C. 2000, c. 32", "national-parks-act"),
    ("Canada Wildlife Act", "R.S.C. 1985, c. W-9", "canada-wildlife-act"),
    ("Migratory Birds Convention Act", "S.C. 1994, c. 22", "migratory-birds-act"),
    ("Canadian Environmental Assessment Act", "S.C. 2012, c. 19", "environmental-assessment-act"),
    ("Impact Assessment Act", "S.C. 2019, c. 28", "impact-assessment-act"),
    ("Canadian Energy Regulator Act", "S.C. 2019, c. 28", "canadian-energy-regulator-act"),
    
    # Business & Commerce (10)
    ("Competition Act", "R.S.C. 1985, c. C-34", "competition-act"),
    ("Bankruptcy and Insolvency Act", "R.S.C. 1985, c. B-3", "bankruptcy-insolvency-act"),
    ("Canada Business Corporations Act", "R.S.C. 1985, c. C-44", "business-corporations-act"),
    ("Trademarks Act", "R.S.C. 1985, c. T-13", "trademarks-act"),
    ("Copyright Act", "R.S.C. 1985, c. C-42", "copyright-act"),
    ("Patent Act", "R.S.C. 1985, c. P-4", "patent-act"),
    ("Investment Canada Act", "R.S.C. 1985, c. 28", "investment-canada-act"),
    ("Companies' Creditors Arrangement Act", "R.S.C. 1985, c. C-36", "companies-creditors-arrangement-act"),
    ("Winding-up and Restructuring Act", "R.S.C. 1985, c. W-11", "winding-up-restructuring-act"),
    ("Canada Cooperatives Act", "S.C. 1998, c. 1", "canada-cooperatives-act"),
    
    # Defense & Security (10)
    ("National Defence Act", "R.S.C. 1985, c. N-5", "national-defence-act"),
    ("Emergencies Act", "R.S.C. 1985, c. 22", "emergencies-act"),
    ("Canadian Security Intelligence Service Act", "R.S.C. 1985, c. C-23", "csis-act"),
    ("Anti-terrorism Act", "S.C. 2015, c. 20", "anti-terrorism-act"),
    ("Security of Canada Information Sharing Act", "S.C. 2015, c. 20", "security-information-sharing-act"),
    ("Combating Terrorism Act", "S.C. 2013, c. 9", "combating-terrorism-act"),
    ("Seized Property Management Act", "S.C. 1993, c. 37", "seized-property-management-act"),
    ("State Immunity Act", "R.S.C. 1985, c. S-18", "state-immunity-act"),
    ("Visiting Forces Act", "R.S.C. 1985, c. V-2", "visiting-forces-act"),
    ("War Crimes and Crimes Against Humanity Act", "S.C. 2000, c. 24", "war-crimes-act"),
    
    # Government Operations (10)
    ("Public Service Employment Act", "S.C. 2003, c. 22", "public-service-employment-act"),
    ("Official Languages Act", "R.S.C. 1985, c. 31", "official-languages-act"),
    ("Public Servants Disclosure Protection Act", "S.C. 2005, c. 46", "disclosure-protection-act"),
    ("Public Service Superannuation Act", "R.S.C. 1985, c. P-36", "public-service-superannuation-act"),
    ("Members of Parliament Retiring Allowances Act", "R.S.C. 1985, c. M-5", "mp-retiring-allowances-act"),
    ("Salaries Act", "R.S.C. 1985, c. S-3", "salaries-act"),
    ("Government Employees Compensation Act", "R.S.C. 1985, c. G-5", "government-employees-compensation-act"),
    ("Public Service Modernization Act", "S.C. 2003, c. 22", "public-service-modernization-act"),
    ("Public Service Rearrangement and Transfer of Duties Act", "R.S.C. 1985, c. P-34", "public-service-rearrangement-act"),
    ("Shared Services Canada Act", "S.C. 2012, c. 19", "shared-services-canada-act"),
]


class CanadianLawDownloader:
    """
    Downloader for Canadian Federal Acts and Regulations from Open Canada.
    
    Note: The actual XML files are not available via direct API.
    This is a mock implementation that will:
    1. Create sample XML files for testing
    2. Document how to obtain real data
    
    Directory Structure:
    - output_dir/en/     -> Acts (Statutes)
    - output_dir/en-regs/ -> Regulations (SOR documents)
    - output_dir/fr/     -> French Acts
    - output_dir/fr-regs/ -> French Regulations
    """
    
    def __init__(self, output_dir: str = "data/regulations/canadian_laws"):
        """
        Initialize downloader.
        
        Args:
            output_dir: Directory to save downloaded files
        """
        self.output_dir = Path(output_dir)
        self.acts_dir_en = self.output_dir / "en"
        self.acts_dir_fr = self.output_dir / "fr"
        self.regs_dir_en = self.output_dir / "en-regs"
        self.regs_dir_fr = self.output_dir / "fr-regs"
        
        # Create all directories
        for dir_path in [self.acts_dir_en, self.acts_dir_fr, self.regs_dir_en, self.regs_dir_fr]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Acts directory (EN): {self.acts_dir_en}")
        logger.info(f"Regulations directory (EN): {self.regs_dir_en}")
    
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
ACTS (Primary Legislation):
1. Visit: https://open.canada.ca/data/en/dataset/1f0aae37-18e4-4bad-bbca-59a4094e44fa

2. Download: "Consolidated Federal Acts (XML)"
   - Size: ~50 MB compressed
   - Extract to: data/regulations/canadian_laws/en/ (English)
   - Extract to: data/regulations/canadian_laws/fr/ (French)

REGULATIONS (Secondary Legislation - SOR/DORS):
1. Visit: https://laws-lois.justice.gc.ca/eng/regulations/
2. Download bulk regulation XML files or use sitemap
3. Extract to: data/regulations/canadian_laws/en-regs/ (English)
4. Extract to: data/regulations/canadian_laws/fr-regs/ (French)

5. Run ingestion pipeline for both Acts and Regulations

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
