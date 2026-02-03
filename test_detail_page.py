#!/usr/bin/env python3
"""Test fetching a single job detail page"""
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Load a job URL from the latest results
data = json.load(open('data/jobs_20260203.json'))
if data:
    test_url = data[0]['url']
    print(f"Testing URL: {test_url}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Non-headless to see what happens
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigating to job page...")
        page.goto(test_url, wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(3000)
        
        # Save the HTML to a file
        html = page.content()
        with open('test_page.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("Saved HTML to test_page.html")
        
        # Parse and test selectors
        soup = BeautifulSoup(html, 'html.parser')
        
        description_selectors = [
            'div#jobDescriptionText',
            'div.jobsearch-jobDescriptionText',
            'div[id*="jobDesc"]',
            'div.job-description',
        ]
        
        print("\nTesting description selectors:")
        for selector in description_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                print(f"✅ {selector}: Found ({len(text)} chars)")
                print(f"   Preview: {text[:200]}...")
            else:
                print(f"❌ {selector}: Not found")
        
        posted_selectors = [
            'span.date',
            'div.jobsearch-JobMetadataFooter',
            'span[data-testid="myJobsStateDate"]',
        ]
        
        print("\nTesting posted date selectors:")
        for selector in posted_selectors:
            elem = soup.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                print(f"✅ {selector}: Found - '{text}'")
            else:
                print(f"❌ {selector}: Not found")
        
        print("\nWaiting 5 seconds so you can see the page...")
        page.wait_for_timeout(5000)
        
        browser.close()
else:
    print("No jobs found in data/jobs_20260203.json")
