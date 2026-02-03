#!/usr/bin/env python3
"""
Enhanced script to fetch job descriptions from Indeed URLs.
Uses advanced anti-detection techniques to bypass Cloudflare.
"""

import json
import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# User agents to rotate
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

def extract_job_key(url):
    """Extract job key from Indeed URL."""
    match = re.search(r'[?&]jk=([a-f0-9]+)', url)
    if match:
        return match.group(1)
    return None

def create_clean_url(job_key):
    """Create a clean Indeed job URL from job key."""
    return f"https://ie.indeed.com/viewjob?jk={job_key}&from=web&vjs=3"

def fetch_job_description(url, use_stealth=True, headless=False):
    """
    Fetch job description from Indeed URL using Playwright with anti-detection.
    
    Args:
        url: Job URL
        use_stealth: Whether to use stealth mode
        headless: Whether to run in headless mode
    
    Returns:
        dict with description, posted_date, and status
    """
    result = {
        'description': '',
        'posted_date': '',
        'status': 'failed',
        'error': None
    }
    
    try:
        with sync_playwright() as p:
            # Launch browser with additional arguments to avoid detection
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            
            # Create context with realistic viewport and user agent
            user_agent = random.choice(USER_AGENTS)
            context = browser.new_context(
                user_agent=user_agent,
                viewport={'width': 1920, 'height': 1080},
                locale='en-IE',
                timezone_id='Europe/Dublin',
                permissions=['geolocation'],
                geolocation={'latitude': 53.3498, 'longitude': -6.2603},  # Dublin coordinates
            )
            
            # Additional JavaScript to hide automation
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'en-IE']
                });
            """)
            
            page = context.new_page()
            
            # Apply stealth mode
            if use_stealth:
                stealth = Stealth()
                stealth.apply_stealth_sync(page)
            
            logger.info(f"Navigating to: {url}")
            
            # Navigate with longer timeout
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Random human-like delay
            time.sleep(random.uniform(2, 4))
            
            # Scroll a bit to simulate human behavior
            page.evaluate("window.scrollBy(0, 300)")
            time.sleep(random.uniform(0.5, 1.5))
            page.evaluate("window.scrollBy(0, -200)")
            time.sleep(random.uniform(0.5, 1))
            
            # Wait for content to load - try multiple strategies
            html = page.content()
            
            # Check for Cloudflare challenge
            if 'cloudflare' in html.lower() and 'challenge' in html.lower():
                logger.warning("Cloudflare challenge detected, waiting longer...")
                # Wait for challenge to complete (up to 15 seconds)
                for i in range(30):
                    time.sleep(0.5)
                    html = page.content()
                    if 'jobDescriptionText' in html:
                        logger.info("Challenge passed!")
                        break
                    if i % 4 == 0:
                        logger.info(f"Waiting for challenge... ({i//2}s)")
            
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try multiple selectors for job description
            description_selectors = [
                'div#jobDescriptionText',
                'div.jobsearch-JobComponent-description',
                'div[class*="jobsearch-JobComponent-description"]',
                'div[id*="jobDesc"]',
                'div.job-description',
            ]
            
            description = ''
            for selector in description_selectors:
                elem = soup.select_one(selector)
                if elem:
                    description = elem.get_text(separator=' ', strip=True)
                    if len(description) > 50:
                        logger.info(f"✓ Found description with selector: {selector} ({len(description)} chars)")
                        result['description'] = description
                        result['status'] = 'success'
                        break
            
            if not description:
                # Save HTML for debugging
                with open('debug_failed.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                logger.warning("No description found. HTML saved to debug_failed.html")
                result['error'] = 'No description element found'
            
            # Try to extract posting date
            date_selectors = [
                'div.jobsearch-JobMetadataFooter',
                'span[class*="date"]',
                'div[class*="JobMetadataFooter"]',
            ]
            
            for selector in date_selectors:
                elem = soup.select_one(selector)
                if elem:
                    date_text = elem.get_text(strip=True)
                    # Look for date patterns
                    if any(word in date_text.lower() for word in ['posted', 'today', 'yesterday', 'day', 'week', 'ago']):
                        result['posted_date'] = date_text
                        break
            
            browser.close()
            
    except Exception as e:
        logger.error(f"Error fetching job: {e}")
        result['error'] = str(e)
    
    return result

def update_jobs_with_descriptions(input_file='data/jobs_20260203.json', 
                                   output_file='data/jobs_with_descriptions.json',
                                   limit=None,
                                   use_stealth=True,
                                   headless=False):
    """
    Read jobs from JSON file, fetch descriptions, and save updated file.
    
    Args:
        input_file: Path to input JSON file
        output_file: Path to output JSON file
        limit: Max number of jobs to process (None for all)
        use_stealth: Use stealth mode
        headless: Run in headless mode
    """
    logger.info(f"Loading jobs from {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        jobs = json.load(f)
    
    logger.info(f"Found {len(jobs)} jobs to process")
    
    if limit:
        jobs = jobs[:limit]
        logger.info(f"Processing first {limit} jobs only")
    
    success_count = 0
    failed_count = 0
    
    for i, job in enumerate(jobs, 1):
        url = job.get('url', '')
        
        if not url:
            logger.warning(f"Job {i}/{len(jobs)}: No URL found, skipping")
            continue
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Job {i}/{len(jobs)}: {job.get('title', 'Unknown')}")
        logger.info(f"Company: {job.get('company', 'Unknown')}")
        
        # Extract job key and create clean URL
        job_key = extract_job_key(url)
        if job_key:
            clean_url = create_clean_url(job_key)
            logger.info(f"Using clean URL with job key: {job_key}")
        else:
            clean_url = url
            logger.info(f"Using original URL")
        
        # Fetch description
        result = fetch_job_description(clean_url, use_stealth=use_stealth, headless=headless)
        
        if result['status'] == 'success':
            job['description'] = result['description']
            job['posted_date'] = result['posted_date']
            success_count += 1
            logger.info(f"✓ Success! Description: {len(result['description'])} chars")
        else:
            failed_count += 1
            logger.error(f"✗ Failed: {result['error']}")
        
        # Save progress after each job
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=2, ensure_ascii=False)
        
        # Random delay between requests to avoid rate limiting
        if i < len(jobs):
            delay = random.uniform(3, 6)
            logger.info(f"Waiting {delay:.1f}s before next request...")
            time.sleep(delay)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Completed! Success: {success_count}, Failed: {failed_count}")
    logger.info(f"Results saved to: {output_file}")
    
    return success_count, failed_count

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch job descriptions from Indeed URLs')
    parser.add_argument('--input', default='data/jobs_20260203.json', 
                        help='Input JSON file with jobs')
    parser.add_argument('--output', default='data/jobs_with_descriptions.json',
                        help='Output JSON file')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of jobs to process (for testing)')
    parser.add_argument('--no-stealth', action='store_true',
                        help='Disable stealth mode')
    parser.add_argument('--visible', action='store_true',
                        help='Run browser in visible mode (not headless)')
    
    args = parser.parse_args()
    
    update_jobs_with_descriptions(
        input_file=args.input,
        output_file=args.output,
        limit=args.limit,
        use_stealth=not args.no_stealth,
        headless=not args.visible
    )
