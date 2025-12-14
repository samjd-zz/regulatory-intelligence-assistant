"""
Ontario Regulations Downloader.

Downloads regulation XML/HTML/PDF/Word content from Ontario e-Laws website.
Uses the sitemap catalog to fetch individual regulations.

Source: https://www.ontario.ca/laws
"""
import logging
import json
import time
import requests
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

from ontario_sitemap_parser import OntarioRegulationMetadata, parse_ontario_sitemap

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Result of a regulation download attempt."""

    regulation_id: str
    url: str
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None
    status_code: Optional[int] = None


class OntarioRegulationDownloader:
    """
    Downloads Ontario regulations from e-Laws website.

    Handles rate limiting, retries, and saves content to disk.
    """

    def __init__(
        self,
        output_dir: str = "data/regulations/ontario",
        delay_seconds: float = 0.5,
        max_retries: int = 3,
        timeout: int = 30,
    ):
        """
        Initialize downloader.

        Args:
            output_dir: Directory to save downloaded files
            delay_seconds: Delay between requests (rate limiting)
            max_retries: Maximum retry attempts per regulation
            timeout: Request timeout in seconds
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout = timeout

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Regulatory Intelligence Assistant Bot/1.0 (Research Project)"
            }
        )

        logger.info(f"Initialized Ontario downloader - output: {self.output_dir}")

    def _build_doc_id(self, regulation_id: str) -> str:
        """
        Derive Word doc id from regulation_id.

        Example:
            regulation_id: r06183 -> R06183_e
        """
        base = regulation_id[1:].upper()
        return f"R{base}_e"

    def download_regulation(
        self,
        metadata: OntarioRegulationMetadata,
        format: str = "xml",
    ) -> DownloadResult:
        """
        Download a single regulation.

        Ontario e-Laws URLs can be accessed with different formats:
        - HTML: https://www.ontario.ca/laws/regulation/r06183
        - PDF:  https://www.ontario.ca/laws/regulation/r06183/pdf
        - Word: https://www.ontario.ca/laws/docs/R06183_e.doc

        (The old XML endpoint is no longer available; XML format will likely 404.)

        Args:
            metadata: Regulation metadata from sitemap
            format: Output format ('xml', 'html', 'pdf', 'doc')

        Returns:
            DownloadResult with success status and file path
        """
        regulation_id = metadata.regulation_id

        # Construct download URL based on format
        if format == "xml":
            download_url = f"{metadata.url}/xml"
            file_ext = "xml"
        elif format == "pdf":
            download_url = f"{metadata.url}/pdf"
            file_ext = "pdf"
        elif format == "doc":
            # Word document under /laws/docs/<DOC_ID>.doc
            # Try to use metadata.doc_id if available; fall back to derived id
            doc_id = getattr(metadata, "doc_id", None) or self._build_doc_id(
                regulation_id
            )
            download_url = f"https://www.ontario.ca/laws/docs/{doc_id}.doc"
            file_ext = "doc"
        else:  # html
            download_url = metadata.url
            file_ext = "html"

        # Determine output file path
        file_name = f"{regulation_id}.{file_ext}"
        file_path = self.output_dir / file_name

        # Skip if already downloaded
        if file_path.exists():
            logger.info(f"Already exists: {file_name}")
            return DownloadResult(
                regulation_id=regulation_id,
                url=download_url,
                success=True,
                file_path=str(file_path),
            )

        # Attempt download with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    f"Downloading {regulation_id} (attempt {attempt}/{self.max_retries})"
                )

                response = self.session.get(
                    download_url,
                    timeout=self.timeout,
                    allow_redirects=True,
                )

                # Check response status
                if response.status_code == 200:
                    # Save content
                    with open(file_path, "wb") as f:
                        f.write(response.content)

                    logger.info(
                        f"Downloaded: {file_name} ({len(response.content)} bytes)"
                    )

                    # Rate limiting delay
                    time.sleep(self.delay_seconds)

                    return DownloadResult(
                        regulation_id=regulation_id,
                        url=download_url,
                        success=True,
                        file_path=str(file_path),
                        status_code=response.status_code,
                    )

                elif response.status_code == 404:
                    logger.warning(f"Not found: {regulation_id} (404)")
                    return DownloadResult(
                        regulation_id=regulation_id,
                        url=download_url,
                        success=False,
                        error="Not found (404)",
                        status_code=404,
                    )

                else:
                    logger.warning(f"HTTP {response.status_code}: {regulation_id}")

                    if attempt < self.max_retries:
                        # Exponential backoff
                        wait_time = self.delay_seconds * (2**attempt)
                        logger.debug(f"Retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        return DownloadResult(
                            regulation_id=regulation_id,
                            url=download_url,
                            success=False,
                            error=f"HTTP {response.status_code}",
                            status_code=response.status_code,
                        )

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout: {regulation_id}")
                if attempt < self.max_retries:
                    time.sleep(self.delay_seconds * 2)
                else:
                    return DownloadResult(
                        regulation_id=regulation_id,
                        url=download_url,
                        success=False,
                        error="Timeout",
                    )

            except Exception as e:
                logger.error(f"Error downloading {regulation_id}: {e}")
                return DownloadResult(
                    regulation_id=regulation_id,
                    url=download_url,
                    success=False,
                    error=str(e),
                )

        # Should not reach here, but just in case
        return DownloadResult(
            regulation_id=regulation_id,
            url=download_url,
            success=False,
            error="Max retries exceeded",
        )

    def download_batch(
        self,
        regulations: List[OntarioRegulationMetadata],
        format: str = "xml",
        max_workers: int = 1,
    ) -> List[DownloadResult]:
        """
        Download multiple regulations.

        Args:
            regulations: List of regulation metadata
            format: Output format ('xml', 'html', 'pdf', 'doc')
            max_workers: Number of parallel download threads (default: 1 for politeness)

        Returns:
            List of DownloadResult objects
        """
        logger.info(
            f"Starting batch download of {len(regulations)} regulations (format: {format})"
        )

        results: List[DownloadResult] = []

        if max_workers == 1:
            # Sequential download
            for i, reg in enumerate(regulations, 1):
                logger.info(f"Progress: {i}/{len(regulations)}")
                result = self.download_regulation(reg, format=format)
                results.append(result)
        else:
            # Parallel download
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.download_regulation, reg, format): reg
                    for reg in regulations
                }

                for i, future in enumerate(as_completed(futures), 1):
                    logger.info(f"Progress: {i}/{len(regulations)}")
                    result = future.result()
                    results.append(result)

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        logger.info(f"Download complete: {successful} succeeded, {failed} failed")

        return results

    def save_download_report(
        self,
        results: List[DownloadResult],
        report_path: str,
    ):
        """
        Save download results to JSON report.

        Args:
            results: List of download results
            report_path: Path to save report
        """
        report_data: Dict[str, object] = {
            "total": len(results),
            "successful": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "results": [
                {
                    "regulation_id": r.regulation_id,
                    "url": r.url,
                    "success": r.success,
                    "file_path": r.file_path,
                    "error": r.error,
                    "status_code": r.status_code,
                }
                for r in results
            ],
        }

        with open(report_path, "w") as f:
            json.dump(report_data, f, indent=2)

        logger.info(f"Download report saved to {report_path}")


def main():
    """CLI interface for downloading Ontario regulations."""

    parser = argparse.ArgumentParser(
        description="Download Ontario regulations from e-Laws website"
    )

    parser.add_argument(
        "--sitemap",
        type=str,
        required=True,
        help="Path to Ontario sitemap XML file",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/regulations/ontario",
        help="Output directory for downloaded files (default: data/regulations/ontario)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["xml", "html", "pdf", "doc"],
        default="xml",
        help="Download format (default: xml)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of regulations to download (for testing)",
    )

    parser.add_argument(
        "--filter-act",
        type=str,
        help="Filter by parent act name (partial match)",
    )

    parser.add_argument(
        "--filter-year-min",
        type=int,
        help="Filter by minimum year",
    )

    parser.add_argument(
        "--filter-year-max",
        type=int,
        help="Filter by maximum year",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between requests in seconds (default: 0.5)",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Number of parallel download threads (default: 1, max recommended: 3)",
    )

    parser.add_argument(
        "--report",
        type=str,
        default="download_report.json",
        help="Path to save download report (default: download_report.json)",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse sitemap
    logger.info(f"Parsing sitemap: {args.sitemap}")
    regulations = parse_ontario_sitemap(args.sitemap)
    logger.info(f"Found {len(regulations)} regulations in sitemap")

    # Apply filters
    from ontario_sitemap_parser import OntarioSitemapParser

    parser_obj = OntarioSitemapParser()

    if args.filter_act:
        regulations = parser_obj.filter_by_act(regulations, args.filter_act)
        logger.info(
            f"Filtered to {len(regulations)} regulations for act: {args.filter_act}"
        )

    if args.filter_year_min or args.filter_year_max:
        regulations = parser_obj.filter_by_year(
            regulations,
            min_year=args.filter_year_min,
            max_year=args.filter_year_max,
        )
        logger.info(f"Filtered to {len(regulations)} regulations by year")

    # Apply limit
    if args.limit:
        regulations = regulations[: args.limit]
        logger.info(f"Limited to {len(regulations)} regulations")

    # Download
    downloader = OntarioRegulationDownloader(
        output_dir=args.output_dir,
        delay_seconds=args.delay,
    )

    results = downloader.download_batch(
        regulations,
        format=args.format,
        max_workers=args.workers,
    )

    # Save report
    downloader.save_download_report(results, args.report)

    # Print summary
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful

    print("\n=== Download Summary ===")
    print(f"Total: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {args.output_dir}")
    print(f"Report: {args.report}")


if __name__ == "__main__":
    main()
