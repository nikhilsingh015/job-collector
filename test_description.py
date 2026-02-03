#!/usr/bin/env python3
"""Test description extraction"""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    url = 'https://ie.indeed.com/jobs?q=software+engineer&l=Dublin'
    print(f'Loading: {url}')
    page.goto(url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(3000)
    
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find job cards
    selectors_to_try = ['div.job_seen_beacon', 'td.resultContent', 'div.cardOutline', 'div.slider_item', 'div[class*="job"]']
    job_cards = []
    found_selector = None
    
    for selector in selectors_to_try:
        job_cards = soup.select(selector)
        if job_cards:
            found_selector = selector
            break
    
    print(f'\n✅ Found {len(job_cards)} job cards with selector: {found_selector}\n')
    
    if job_cards:
        card = job_cards[0]
        print("Testing first job card...\n")
        
        # Try description selectors
        desc_selectors = [
            'div.job-snippet',
            'div[data-testid="job-snippet"]',
            'div.jobCardShelfContainer',
            'table.jobCardShelfContainer',
            'ul',
            'div'
        ]
        
        for selector in desc_selectors:
            elem = card.select_one(selector)
            if elem:
                text = elem.get_text().strip()
                if len(text) > 20:
                    print(f'✅ {selector}: {len(text)} chars')
                    print(f'   Preview: {text[:150]}...\n')
                    break
        else:
            print("❌ No description found with any selector")
            print("\nAll divs in card:")
            divs = card.find_all('div', limit=5)
            for i, div in enumerate(divs):
                text = div.get_text().strip()
                if len(text) > 20:
                    print(f"  Div {i}: {div.get('class')} - {len(text)} chars")
    
    browser.close()
    print("\nTest complete!")
