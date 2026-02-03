#!/usr/bin/env -S python3
"""
Complete Job Scraper - Single executable that scrapes jobs and fetches descriptions.
Uses upsert logic: updates existing entries or creates new ones.
"""

import argparse
import json
import os
import sys
import time
import random
import logging
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re

from src.utils import setup_logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('job_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]


def load_or_create_jobs_file(filepath):
    """Load existing jobs file or create new empty list."""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse {filepath}, starting fresh")
            return []
    return []


def save_jobs_file(jobs, filepath):
    """Save jobs to JSON file."""
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(jobs)} jobs to {filepath}")


def upsert_job(jobs_list, new_job, key_field='url'):
    """
    Upsert a job into the jobs list.
    If job with same key exists, update it. Otherwise, append it.
    
    Args:
        jobs_list: List of job dictionaries
        new_job: New job dictionary to upsert
        key_field: Field to use as unique key (default: 'url')
    
    Returns:
        bool: True if updated existing, False if inserted new
    """
    key_value = new_job.get(key_field)
    if not key_value:
        jobs_list.append(new_job)
        return False
    
    # Look for existing job
    for i, job in enumerate(jobs_list):
        if job.get(key_field) == key_value:
            # Update existing job (merge fields)
            jobs_list[i].update(new_job)
            return True
    
    # Not found, insert new
    jobs_list.append(new_job)
    return False


def extract_job_key(url):
    """Extract job key from Indeed URL."""
    match = re.search(r'[?&]jk=([a-f0-9]+)', url)
    if match:
        return match.group(1)
    return None


def create_clean_url(job_key):
    """Create a clean Indeed job URL from job key."""
    return f"https://ie.indeed.com/viewjob?jk={job_key}&from=web&vjs=3"


def fetch_job_description(url, use_stealth=True, headless=True):
    """
    Fetch job description from Indeed URL using Playwright with anti-detection.
    
    Args:
        url: Job URL
        use_stealth: Whether to use stealth mode
        headless: Whether to run in headless mode
    
    Returns:
        dict with description, posted_date, and status
    """
    # Import here to avoid requiring playwright if not needed
    from playwright.sync_api import sync_playwright
    from playwright_stealth import Stealth
    
    result = {
        'description': '',
        'posted_date': '',
        'status': 'failed',
        'error': None
    }
    
    try:
        with sync_playwright() as p:
            # Launch browser with anti-detection arguments
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                ]
            )
            
            # Create context with realistic settings
            user_agent = random.choice(USER_AGENTS)
            context = browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-IE',
                timezone_id='Europe/Dublin',
                geolocation={'latitude': 53.3498, 'longitude': -6.2603},
            )
            
            # Hide automation markers
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = context.new_page()
            
            # Apply stealth mode
            if use_stealth:
                stealth = Stealth()
                stealth.apply_stealth_sync(page)
            
            # Navigate to page
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            time.sleep(random.uniform(2, 4))
            
            # Simulate human behavior
            page.evaluate("window.scrollBy(0, 300)")
            time.sleep(random.uniform(0.5, 1.5))
            
            html = page.content()
            
            # Check for Cloudflare challenge
            if 'cloudflare' in html.lower() and 'challenge' in html.lower():
                logger.warning("Cloudflare challenge detected, waiting...")
                for i in range(30):
                    time.sleep(0.5)
                    html = page.content()
                    if 'jobDescriptionText' in html:
                        break
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract job description
            description_selectors = [
                'div#jobDescriptionText',
                'div.jobsearch-JobComponent-description',
                'div[class*="jobsearch-JobComponent-description"]',
                'div[id*="jobDesc"]',
            ]
            
            for selector in description_selectors:
                elem = soup.select_one(selector)
                if elem:
                    description = elem.get_text(separator=' ', strip=True)
                    if len(description) > 50:
                        logger.info(f"✓ Found description ({len(description)} chars)")
                        result['description'] = description
                        result['status'] = 'success'
                        break
            
            # Extract posted date
            date_selectors = [
                'div.jobsearch-JobMetadataFooter',
                'span[class*="date"]',
                'div[class*="JobMetadata"]',
            ]
            
            for selector in date_selectors:
                elem = soup.select_one(selector)
                if elem:
                    date_text = elem.get_text(strip=True)
                    if any(word in date_text.lower() for word in ['posted', 'today', 'yesterday', 'day', 'ago']):
                        result['posted_date'] = date_text
                        break
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Error fetching description: {str(e)}")
        result['error'] = str(e)
    
    return result


def scrape_jobs(cv_path=None):
    """Scrape jobs from Indeed based on CV."""
    # Import here to avoid requiring dependencies if not needed
    from src.cv_parser import CVParser
    from src.indeed_scraper import IndeedScraper
    from src.storage import JobStorage
    
    logger.info("Starting job scraping...")
    
    # Parse CV to get job queries
    parser = CVParser(cv_path if cv_path else "")
    queries = parser.get_job_search_queries()
    logger.info(f"Generated {len(queries)} search queries")
    
    # Initialize scrapers
    storage = JobStorage()
    scrapers = [
        IndeedScraper(location="Ireland"),
    ]
    
    all_jobs = []
    
    # Scrape each query
    for query in queries:
        logger.info(f"Searching for: {query}")
        for scraper in scrapers:
            try:
                jobs = scraper.scrape(query)
                logger.info(f"Found {len(jobs)} jobs from {scraper.__class__.__name__}")
                
                # Add search query to each job
                for job in jobs:
                    job['search_query'] = query
                    if storage.is_new_job(job['url']):
                        all_jobs.append(job)
                        storage.add_job(job['url'])
                
            except Exception as e:
                logger.error(f"Error scraping {scraper.__class__.__name__}: {e}")
    
    logger.info(f"Total unique jobs scraped: {len(all_jobs)}")
    return all_jobs


def enrich_jobs_with_descriptions(jobs, output_file, headless=True):
    """
    Enrich jobs with full descriptions using upsert logic.
    
    Args:
        jobs: List of job dictionaries
        output_file: Path to output JSON file
        headless: Run browser in headless mode
    """
    # Load existing jobs from output file (if exists)
    existing_jobs = load_or_create_jobs_file(output_file)
    logger.info(f"Loaded {len(existing_jobs)} existing jobs from {output_file}")
    
    # Process each job
    success_count = 0
    failed_count = 0
    updated_count = 0
    new_count = 0
    
    for idx, job in enumerate(jobs, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"Job {idx}/{len(jobs)}: {job['title']}")
        logger.info(f"Company: {job['company']}")
        
        # Check if job already has description in existing data
        existing_job = next((j for j in existing_jobs if j.get('url') == job['url']), None)
        if existing_job and existing_job.get('description') and len(existing_job['description']) > 100:
            logger.info("✓ Job already has description, skipping")
            success_count += 1
            continue
        
        # Extract job key and create clean URL
        job_key = extract_job_key(job['url'])
        if job_key:
            clean_url = create_clean_url(job_key)
            logger.info(f"Using clean URL with job key: {job_key}")
        else:
            clean_url = job['url']
            logger.info("Using original URL")
        
        # Fetch description
        result = fetch_job_description(clean_url, headless=headless)
        
        if result['status'] == 'success':
            job['description'] = result['description']
            job['posted_date'] = result['posted_date']
            logger.info(f"✓ Success! Description: {len(result['description'])} chars")
            success_count += 1
        else:
            logger.error(f"✗ Failed: {result.get('error', 'Unknown error')}")
            failed_count += 1
        
        # Upsert into existing jobs
        was_updated = upsert_job(existing_jobs, job, key_field='url')
        if was_updated:
            updated_count += 1
        else:
            new_count += 1
        
        # Save progress after each job
        save_jobs_file(existing_jobs, output_file)
        
        # Human-like delay
        if idx < len(jobs):
            delay = random.uniform(3, 6)
            logger.info(f"Waiting {delay:.1f}s before next request...")
            time.sleep(delay)
    
    logger.info("\n" + "="*60)
    logger.info("Completed!")
    logger.info(f"Success: {success_count}, Failed: {failed_count}")
    logger.info(f"Updated: {updated_count}, New: {new_count}")
    logger.info(f"Results saved to: {output_file}")
    
    return existing_jobs


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Complete Job Scraper with Description Fetching')
    parser.add_argument('--cv', type=str, help='Path to CV file')
    parser.add_argument('--scrape-only', action='store_true', help='Only scrape jobs, skip descriptions')
    parser.add_argument('--enrich-only', action='store_true', help='Only enrich existing jobs with descriptions')
    parser.add_argument('--input', type=str, default='data/jobs.json', help='Input jobs file (for enrich-only mode)')
    parser.add_argument('--output', type=str, default='data/jobs_complete.json', help='Output file path')
    parser.add_argument('--visible', action='store_true', help='Run browser in visible mode')
    parser.add_argument('--limit', type=int, help='Limit number of jobs to process')
    
    args = parser.parse_args()
    
    headless = not args.visible
    
    try:
        if args.enrich_only:
            # Only enrich existing jobs
            logger.info("Mode: Enrich existing jobs only")
            jobs = load_or_create_jobs_file(args.input)
            if not jobs:
                logger.error(f"No jobs found in {args.input}")
                return 1
            
            if args.limit:
                jobs = jobs[:args.limit]
            
            enrich_jobs_with_descriptions(jobs, args.output, headless=headless)
            
        elif args.scrape_only:
            # Only scrape jobs
            logger.info("Mode: Scrape jobs only")
            jobs = scrape_jobs(args.cv)
            save_jobs_file(jobs, args.output)
            
        else:
            # Full pipeline: scrape + enrich
            logger.info("Mode: Full pipeline (scrape + enrich)")
            
            # Step 1: Scrape jobs
            jobs = scrape_jobs(args.cv)
            
            if not jobs:
                logger.warning("No jobs found during scraping")
                return 0
            
            if args.limit:
                jobs = jobs[:args.limit]
            
            # Step 2: Enrich with descriptions
            enriched_jobs = enrich_jobs_with_descriptions(jobs, args.output, headless=headless)
            
            # Step 3: Generate report
            from src.reporter import HtmlReporter
            reporter = HtmlReporter(enriched_jobs)
            report_path = reporter.generate_report()
            logger.info(f"HTML report generated: {report_path}")
        
        logger.info("All done!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
