#!/usr/bin/env python3
"""
Test script to verify the job scraper functionality with mock data.
"""

import sys
import os
from datetime import datetime
import logging
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.base_scraper import BaseScraper
from src.utils import setup_logging
from src.storage import JobStorage
from src.reporter import HtmlReporter


class MockScraper(BaseScraper):
    """Mock scraper for testing."""
    
    def __init__(self, source_name):
        super().__init__(source_name)
    
    def scrape(self, query, location, pages):
        """Mock scrape that returns sample data."""
        self.logger.info(f"Mock scraping: query='{query}', location='{location}', pages={pages}")
        
        # Generate mock jobs
        self.jobs = []
        for i in range(5):
            job = {
                'title': f'Software Engineer {i+1}',
                'company': f'Tech Company {i+1}',
                'location': location,
                'salary': '€50,000 - €70,000',
                'description': f'We are looking for a talented software engineer to join our team. Job ID: {i+1}',
                'url': f'https://example.com/jobs/{self.source_name}/{i+1}',
                'source': self.source_name
            }
            self.jobs.append(job)
        
        self.logger.info(f"Mock scrape completed. Generated {len(self.jobs)} mock jobs")
        return self.jobs


def test_storage():
    """Test JobStorage functionality."""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("Testing JobStorage")
    logger.info("=" * 80)

    test_db = "data/test_jobs.db"
    if os.path.exists(test_db):
        os.remove(test_db)

    storage = JobStorage(test_db)

    job = {
        'url': 'https://example.com/job1',
        'title': 'Test Job',
        'company': 'Test Co',
        'location': 'Dublin',
        'source': 'test'
    }

    # Test is_job_new on empty DB
    if storage.is_job_new(job['url']):
        logger.info("✓ is_job_new returned True for new job")
    else:
        logger.error("✗ is_job_new returned False for new job")
        return False

    # Test add_job
    storage.add_job(job)
    logger.info("✓ Added job to storage")

    # Test is_job_new on existing job
    if not storage.is_job_new(job['url']):
        logger.info("✓ is_job_new returned False for existing job")
    else:
        logger.error("✗ is_job_new returned True for existing job")
        return False

    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    return True


def test_reporter():
    """Test HtmlReporter functionality."""
    logger = logging.getLogger(__name__)
    logger.info("\n" + "=" * 80)
    logger.info("Testing HtmlReporter")
    logger.info("=" * 80)

    jobs = [
        {
            'title': 'Test Job 1',
            'company': 'Company A',
            'location': 'Dublin',
            'salary': '50k',
            'description': 'Desc 1',
            'url': 'http://example.com/1',
            'source': 'indeed'
        },
        {
            'title': 'Test Job 2',
            'company': 'Company B',
            'location': 'Cork',
            'salary': '60k',
            'description': 'Desc 2',
            'url': 'http://example.com/2',
            'source': 'linkedin'
        }
    ]

    reporter = HtmlReporter()
    report_file = reporter.generate_report(jobs, "test query", "test location")

    if report_file and os.path.exists(report_file):
        logger.info(f"✓ HTML report generated at {report_file}")
        # Validate content roughly
        with open(report_file, 'r') as f:
            content = f.read()
            if "Test Job 1" in content and "Company B" in content:
                logger.info("✓ HTML report content validated")
            else:
                logger.error("✗ HTML report content missing expected data")
                return False
    else:
        logger.error("✗ HTML report generation failed")
        return False

    return True


def test_csv_functionality():
    """Test CSV saving and merging functionality."""
    logger = logging.getLogger(__name__)
    
    logger.info("\n" + "=" * 80)
    logger.info("Testing Job Scraper CSV Functionality")
    logger.info("=" * 80)
    
    # Create mock scrapers
    scrapers = [
        MockScraper('mock_indeed'),
        MockScraper('mock_irishjobs'),
        MockScraper('mock_linkedin')
    ]
    
    csv_files = []
    
    # Run each scraper
    for scraper in scrapers:
        logger.info(f"\nTesting {scraper.source_name} scraper")
        jobs = scraper.scrape("software engineer", "Dublin", 1)
        
        if jobs:
            csv_file = scraper.save_to_csv()
            if csv_file:
                csv_files.append(csv_file)
                logger.info(f"✓ Successfully saved {len(jobs)} jobs to {csv_file}")
    
    # Test merging
    if csv_files:
        from scraper import merge_csv_files
        date_str = datetime.now().strftime('%Y%m%d')
        merged_filename = f"data/jobs_test_merged_{date_str}.csv"
        
        logger.info(f"\nMerging {len(csv_files)} CSV files")
        merge_csv_files(csv_files, merged_filename)
        
        # Verify merged file
        if os.path.exists(merged_filename):
            with open(merged_filename, 'r') as f:
                lines = f.readlines()
                logger.info(f"✓ Merged file created with {len(lines)-1} jobs (including header)")
        
        logger.info("\n" + "=" * 80)
        logger.info("CSV Test completed successfully!")
    else:
        logger.error("No CSV files were created")
        return False

    return True


def main():
    setup_logging()
    
    if not test_storage():
        sys.exit(1)

    if not test_reporter():
        sys.exit(1)

    if not test_csv_functionality():
        sys.exit(1)

    logging.info("\nALL TESTS PASSED!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
