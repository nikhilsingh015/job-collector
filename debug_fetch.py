#!/usr/bin/env python3
"""Test a single job detail fetch directly"""
import json
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# Simple text cleaning
def clean_text(text):
    if not text:
        return ''
    return ' '.join(text.strip().split())

# Load a job URL
data = json.load(open('data/jobs_20260203.json'))
if data:
    test_url = data[0]['url']
    print(f"Testing URL: {test_url}\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print(f"Step 1: Navigating to job page...")
        page.goto(test_url, wait_until='domcontentloaded', timeout=20000)
        page.wait_for_timeout(2000)
        
        print(f"Step 2: Getting HTML content...")
        html = page.content()
        print(f"HTML length: {len(html)} bytes")
        
        print(f"Step 3: Parsing with BeautifulSoup...")
        soup = BeautifulSoup(html, 'html.parser')
        
        print(f"Step 4: Testing description selectors...")
        description_selectors = [
            'div#jobDescriptionText',
            'div.jobsearch-jobDescriptionText',
            'div[id*="jobDesc"]',
            'div.job-description',
        ]
        
        for selector in description_selectors:
            print(f"\nTrying selector: {selector}")
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = clean_text(desc_elem.get_text())
                print(f"  ✅ Found! Length: {len(description)} chars")
                if len(description) > 50:
                    print(f"  ✅ Length > 50, would accept!")
                    print(f"  Preview: {description[:200]}...")
                    break
                else:
                    print(f"  ⚠️  Length <= 50, would reject")
            else:
                print(f"  ❌ Not found")
        
        browser.close()
