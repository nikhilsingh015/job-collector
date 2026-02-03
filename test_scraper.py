#!/usr/bin/env python3
"""
Test script to verify the job scraper functionality with mock data.
"""

import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from src.base_scraper import BaseScraper
from src.utils import setup_logging
import logging


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
                'url': f'https://example.com/jobs/{i+1}'
            }
            self.jobs.append(job)
        
        self.logger.info(f"Mock scrape completed. Generated {len(self.jobs)} mock jobs")
        return self.jobs


def test_csv_functionality():
    """Test CSV saving and merging functionality."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 80)
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
        logger.info("Test completed successfully!")
        logger.info(f"Created files:")
        for csv_file in csv_files:
            logger.info(f"  - {csv_file}")
        logger.info(f"  - {merged_filename}")
        logger.info("=" * 80)
    else:
        logger.error("No CSV files were created")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(test_csv_functionality())
