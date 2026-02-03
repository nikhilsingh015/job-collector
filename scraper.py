#!/usr/bin/env python3
"""
Job Scraper CLI - Educational web scraper for job listings.

This script scrapes job listings from Indeed.ie, IrishJobs.ie, and LinkedIn
for educational purposes.
"""

import argparse
import sys
import csv
from datetime import datetime
import os
import logging

from src.utils import setup_logging
from src.indeed_scraper import IndeedScraper
from src.irishjobs_scraper import IrishJobsScraper
from src.linkedin_scraper import LinkedInScraper
from src.storage import JobStorage
from src.reporter import HtmlReporter


def merge_csv_files(csv_files, output_filename):
    """
    Merge multiple CSV files into a single file.
    """
    logger = logging.getLogger(__name__)
    
    if not csv_files:
        logger.warning("No CSV files to merge")
        return []
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    headers = ['title', 'company', 'location', 'salary', 'description', 'url', 'source']
    all_jobs = []
    
    # Read all CSV files
    for csv_file in csv_files:
        if csv_file and os.path.exists(csv_file):
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        all_jobs.append(row)
                logger.info(f"Read {csv_file}")
            except Exception as e:
                logger.error(f"Error reading {csv_file}: {e}")
    
    # Write merged file
    if all_jobs:
        try:
            with open(output_filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(all_jobs)
            logger.info(f"Merged {len(all_jobs)} jobs from {len(csv_files)} files to {output_filename}")
        except Exception as e:
            logger.error(f"Error writing merged file: {e}")
    else:
        logger.warning("No jobs found to merge")

    return all_jobs


def main():
    """Main function to run the job scraper."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description='Job Scraper - Scrape job listings from Indeed.ie, IrishJobs.ie, and LinkedIn',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --query "software engineer" --location "Dublin" --pages 2
  %(prog)s --query "data scientist" --location "Ireland" --ignore-history
        """
    )
    
    parser.add_argument(
        '--query',
        type=str,
        required=True,
        help='Job search query (e.g., "software engineer", "data scientist")'
    )
    
    parser.add_argument(
        '--location',
        type=str,
        required=True,
        help='Location to search in (e.g., "Dublin", "Ireland")'
    )
    
    parser.add_argument(
        '--pages',
        type=int,
        default=1,
        help='Number of pages to scrape per source (default: 1)'
    )
    
    parser.add_argument(
        '--ignore-history',
        action='store_true',
        help='If set, scrapes all jobs regardless of whether they were seen before.'
    )

    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
    logger.info("Job Scraper Started")
    logger.info(f"Query: {args.query}")
    logger.info(f"Location: {args.location}")
    logger.info(f"Pages: {args.pages}")
    logger.info(f"Ignore History: {args.ignore_history}")
    logger.info("=" * 80)
    
    # Initialize storage
    storage = JobStorage()

    # Initialize scrapers
    scrapers = [
        IndeedScraper(),
        IrishJobsScraper(),
        LinkedInScraper()
    ]
    
    csv_files = []
    date_str = datetime.now().strftime('%Y%m%d')
    
    # Run each scraper
    for scraper in scrapers:
        try:
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Starting {scraper.source_name} scraper")
            logger.info(f"{'=' * 80}")
            
            # Scrape jobs
            jobs = scraper.scrape(args.query, args.location, args.pages)
            
            # Filter duplicates if not ignoring history
            if not args.ignore_history:
                new_jobs = []
                for job in jobs:
                    if storage.is_job_new(job['url']):
                        new_jobs.append(job)
                        storage.add_job(job)
                    else:
                        logger.debug(f"Skipping seen job: {job['title']} at {job['company']}")

                logger.info(f"Filtered {len(jobs) - len(new_jobs)} duplicates. {len(new_jobs)} new jobs.")
                scraper.jobs = new_jobs
            else:
                # Still add to storage to mark them as seen for future runs?
                # Yes, if we run with ignore-history, we probably still want to update our DB.
                for job in jobs:
                    storage.add_job(job)

            # Save to CSV
            if scraper.jobs:
                csv_file = scraper.save_to_csv()
                if csv_file:
                    csv_files.append(csv_file)
            else:
                logger.warning(f"No new jobs found for {scraper.source_name}")
                
        except Exception as e:
            logger.error(f"Error running {scraper.source_name} scraper: {e}", exc_info=True)
            continue
    
    # Merge all CSV files
    if csv_files:
        merged_filename = f"data/jobs_merged_{date_str}.csv"
        logger.info(f"\n{'=' * 80}")
        logger.info("Merging CSV files")
        logger.info(f"{'=' * 80}")
        all_merged_jobs = merge_csv_files(csv_files, merged_filename)

        # Generate HTML Report
        reporter = HtmlReporter()
        report_file = reporter.generate_report(all_merged_jobs, args.query, args.location)
        
        logger.info(f"\n{'=' * 80}")
        logger.info("Job Scraper Completed Successfully")
        logger.info(f"Individual files: {len(csv_files)}")
        logger.info(f"Merged file: {merged_filename}")
        if report_file:
            logger.info(f"HTML Report: {report_file}")
        logger.info(f"{'=' * 80}")
    else:
        logger.error("No data was scraped from any source")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
