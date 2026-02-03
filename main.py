#!/usr/bin/env python3
"""
Automated Job Collector - Parses CV and scrapes relevant jobs.

This script:
1. Parses the CV from the repository
2. Extracts relevant job search queries based on profile
3. Scrapes job listings from multiple sources
4. Outputs consolidated results to CSV
"""

import argparse
import sys
import csv
from datetime import datetime
import os
import logging
import glob as glob_module

from src.utils import setup_logging
from src.cv_parser import CVParser
from src.indeed_scraper import IndeedScraper
from src.irishjobs_scraper import IrishJobsScraper
from src.linkedin_scraper import LinkedInScraper
from src.storage import JobStorage
from src.reporter import HtmlReporter


def find_cv_file(directory: str = ".") -> str:
    """
    Find CV/Resume PDF file in the directory.

    Args:
        directory: Directory to search in.

    Returns:
        Path to the CV file.

    Raises:
        FileNotFoundError: If no CV file is found.
    """
    logger = logging.getLogger(__name__)

    # Common CV file patterns
    patterns = [
        "*CV*.pdf",
        "*cv*.pdf",
        "*Resume*.pdf",
        "*resume*.pdf",
        "*RESUME*.pdf",
    ]

    for pattern in patterns:
        matches = glob_module.glob(os.path.join(directory, pattern))
        if matches:
            logger.info(f"Found CV file: {matches[0]}")
            return matches[0]

    # If no match with patterns, look for any PDF
    pdf_files = glob_module.glob(os.path.join(directory, "*.pdf"))
    if pdf_files:
        logger.info(f"Using PDF file as CV: {pdf_files[0]}")
        return pdf_files[0]

    raise FileNotFoundError(
        f"No CV/Resume PDF file found in {directory}. "
        "Please add a PDF file named with 'CV' or 'Resume' in the filename."
    )


def merge_job_results(all_jobs: list, output_filename: str) -> str:
    """
    Merge all job results into a single CSV file.

    Args:
        all_jobs: List of job dictionaries.
        output_filename: Output CSV filename.

    Returns:
        Path to the output file.
    """
    logger = logging.getLogger(__name__)

    if not all_jobs:
        logger.warning("No jobs to merge")
        return ""

    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)

    headers = [
        "title",
        "company",
        "location",
        "salary",
        "description",
        "url",
        "source",
        "search_query",
    ]

    try:
        with open(output_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            # Remove duplicates based on URL
            seen_urls = set()
            unique_jobs = []
            for job in all_jobs:
                url = job.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_jobs.append(job)

            for job in unique_jobs:
                row = {header: job.get(header, "") for header in headers}
                writer.writerow(row)

        logger.info(
            f"Saved {len(unique_jobs)} unique jobs to {output_filename}"
        )
        return output_filename

    except Exception as e:
        logger.error(f"Error saving jobs to CSV: {e}")
        return ""


def run_scrapers(query: str, location: str, pages: int, storage: JobStorage) -> list:
    """
    Run all scrapers for a given query.

    Args:
        query: Job search query.
        location: Location to search in.
        pages: Number of pages to scrape.
        storage: JobStorage instance for deduplication.

    Returns:
        List of job dictionaries.
    """
    logger = logging.getLogger(__name__)
    all_jobs = []

    scrapers = [
        IndeedScraper(),
        IrishJobsScraper(),
        LinkedInScraper(),
    ]

    for scraper in scrapers:
        try:
            logger.info(f"Running {scraper.source_name} scraper for: '{query}'")
            jobs = scraper.scrape(query, location, pages)

            # Filter duplicates and add search query
            new_jobs = []
            for job in jobs:
                if storage.is_job_new(job.get("url", "")):
                    job["search_query"] = query
                    new_jobs.append(job)
                    storage.add_job(job)
                else:
                    logger.debug(
                        f"Skipping duplicate: {job.get('title')} at {job.get('company')}"
                    )

            logger.info(
                f"{scraper.source_name}: Found {len(jobs)} jobs, "
                f"{len(new_jobs)} new"
            )
            all_jobs.extend(new_jobs)

        except Exception as e:
            logger.error(f"Error running {scraper.source_name}: {e}")
            continue

    return all_jobs


def main():
    """Main function to run the automated job collector."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Automated Job Collector - Parse CV and scrape relevant jobs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This tool automatically:
1. Finds and parses your CV/Resume PDF
2. Extracts relevant job titles and skills
3. Searches multiple job sites for matching positions
4. Outputs a consolidated CSV file with all results

Examples:
  %(prog)s                           # Auto-detect CV and run with defaults
  %(prog)s --cv "path/to/cv.pdf"     # Specify CV file
  %(prog)s --pages 3                 # Scrape 3 pages per source
  %(prog)s --queries-limit 3         # Limit to 3 search queries
        """,
    )

    parser.add_argument(
        "--cv",
        type=str,
        help="Path to CV/Resume PDF file (auto-detected if not specified)",
    )

    parser.add_argument(
        "--location",
        type=str,
        help="Override location for job search (extracted from CV if not specified)",
    )

    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Number of pages to scrape per source (default: 1)",
    )

    parser.add_argument(
        "--queries-limit",
        type=int,
        default=5,
        help="Maximum number of search queries to run (default: 5)",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV filename (default: data/jobs_YYYYMMDD.csv)",
    )

    parser.add_argument(
        "--ignore-history",
        action="store_true",
        help="Scrape all jobs regardless of history",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)
    logger.info("Automated Job Collector Started")
    logger.info("=" * 80)

    try:
        # Step 1: Find and parse CV
        cv_path = args.cv if args.cv else find_cv_file()
        logger.info(f"Using CV: {cv_path}")

        cv_parser = CVParser(cv_path)
        profile = cv_parser.parse()

        logger.info(f"Parsed profile for: {profile['name']}")
        logger.info(f"Title: {profile['title']}")
        logger.info(f"Location: {profile['location']}")
        logger.info(f"Experience: {profile['experience_years']}+ years")
        logger.info(f"Skills: {', '.join(profile['skills'][:10])}...")
        logger.info(f"Search queries: {profile['job_search_queries']}")

        # Step 2: Determine search parameters
        location = args.location or cv_parser.get_search_location()
        queries = cv_parser.get_search_queries()[: args.queries_limit]

        if not queries:
            logger.error("No job search queries could be generated from CV")
            return 1

        logger.info(f"\nWill search for {len(queries)} job types in {location}")

        # Step 3: Initialize storage
        storage = JobStorage()

        # Step 4: Run scrapers for each query
        all_jobs = []
        for i, query in enumerate(queries, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Query {i}/{len(queries)}: {query}")
            logger.info("=" * 80)

            jobs = run_scrapers(query, location, args.pages, storage)
            all_jobs.extend(jobs)

            logger.info(f"Total jobs so far: {len(all_jobs)}")

        # Step 5: Save results
        date_str = datetime.now().strftime("%Y%m%d")
        output_file = args.output or f"data/jobs_{date_str}.csv"

        if all_jobs:
            output_path = merge_job_results(all_jobs, output_file)

            # Generate HTML report
            reporter = HtmlReporter()
            report_file = reporter.generate_report(
                all_jobs,
                ", ".join(queries[:3]),
                location,
            )

            logger.info("\n" + "=" * 80)
            logger.info("Job Collection Completed Successfully!")
            logger.info("=" * 80)
            logger.info(f"Profile: {profile['name']}")
            logger.info(f"Queries searched: {len(queries)}")
            logger.info(f"Total unique jobs found: {len(all_jobs)}")
            logger.info(f"Output CSV: {output_path}")
            if report_file:
                logger.info(f"HTML Report: {report_file}")
            logger.info("=" * 80)
        else:
            logger.warning("No jobs were found matching your profile")
            return 1

    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
