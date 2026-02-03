#!/usr/bin/env python3
"""Test script to check posted date extraction from Indeed job pages."""

import json
import time
import random
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

# Load first job
with open('data/jobs_20260203.json', 'r') as f:
    jobs = json.load(f)
    job = jobs[0]

print(f"Testing job: {job['title']}")
print(f"URL: {job['url']}")
print()

def extract_job_key(url):
    """Extract job key from Indeed URL."""
    if 'jk=' in url:
        start = url.index('jk=') + 3
        end = url.find('&', start)
        if end == -1:
            return url[start:]
        return url[start:end]
    return None

job_key = extract_job_key(job['url'])
clean_url = f"https://ie.indeed.com/viewjob?jk={job_key}&from=web&vjs=3" if job_key else job['url']

print(f"Using URL: {clean_url}")
print()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080},
        locale='en-IE',
        timezone_id='Europe/Dublin',
    )
    
    page = context.new_page()
    stealth = Stealth()
    stealth.apply_stealth_sync(page)
    
    page.goto(clean_url, wait_until='domcontentloaded', timeout=30000)
    time.sleep(3)
    
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    print("=" * 70)
    print("SEARCHING FOR DATE ELEMENTS")
    print("=" * 70)
    
    # Try all possible date selectors
    selectors_to_try = [
        'div.jobsearch-JobMetadataFooter',
        'span.jobsearch-JobMetadataFooter',
        'div[class*="JobMetadata"]',
        'span[class*="date"]',
        'div[class*="date"]',
        'span[data-testid*="date"]',
        'div[data-testid*="date"]',
        'span.css-kyg8or',
        'div.css-kyg8or',
    ]
    
    for selector in selectors_to_try:
        elems = soup.select(selector)
        if elems:
            print(f"\n✓ Selector '{selector}' found {len(elems)} element(s):")
            for i, elem in enumerate(elems[:3]):  # Show first 3
                text = elem.get_text(strip=True)
                print(f"  [{i+1}] {text[:200]}")
    
    # Also search for text containing "Posted"
    print("\n" + "=" * 70)
    print("ELEMENTS CONTAINING 'Posted' or 'ago'")
    print("=" * 70)
    
    for elem in soup.find_all(string=lambda text: text and ('Posted' in text or 'ago' in text)):
        parent = elem.parent
        print(f"\nTag: {parent.name}, Classes: {parent.get('class', [])}")
        print(f"Text: {elem.strip()[:200]}")
    
    print("\n" + "=" * 70)
    print("Full HTML snippet around 'Posted' (if exists)")
    print("=" * 70)
    
    # Find the HTML section containing "Posted"
    if 'Posted' in html or 'ago' in html:
        for line in html.split('\n'):
            if 'Posted' in line or 'ago' in line.lower():
                print(line.strip()[:300])
                break
    
    input("\n\nPress Enter to close browser...")
    browser.close()
