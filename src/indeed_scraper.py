"""Indeed.ie job scraper using Playwright."""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from src.base_scraper import BaseScraper
from src.utils import random_delay
from src.config import PAGE_LOAD_TIMEOUT, USER_AGENTS
import random


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.ie job listings using Playwright."""
    
    def __init__(self):
        super().__init__('indeed')
        self.base_url = self.config.get('base_url', 'https://ie.indeed.com')
    
    def scrape(self, query, location, pages=1):
        """
        Scrape jobs from Indeed.ie using Playwright.
        """
        self.jobs = []
        self.logger.info(f"Starting Indeed.ie scrape: query='{query}', location='{location}', pages={pages}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                user_agent = random.choice(USER_AGENTS)
                
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = context.new_page()
                jobs_per_page = self.config.get('jobs_per_page', 10)

                for page_num in range(pages):
                    try:
                        start = page_num * jobs_per_page
                        search_url = f"{self.base_url}/jobs?q={query}&l={location}&start={start}"
                        
                        self.logger.info(f"Fetching page {page_num + 1} from Indeed.ie")
                        
                        try:
                            page.goto(search_url, wait_until='domcontentloaded', timeout=PAGE_LOAD_TIMEOUT)
                            page.wait_for_timeout(3000)  # Wait for dynamic content
                        except PlaywrightTimeoutError:
                            self.logger.error(f"Timeout loading page {page_num + 1}")
                            continue
                        
                        # Get the page HTML
                        html = page.content()
                        soup = BeautifulSoup(html, 'lxml')
                        
                        # Find job cards using configured selectors
                        job_cards = []
                        for selector in self.config['selectors']['job_card']:
                            found = soup.select(selector)
                            if found:
                                job_cards = found
                                break
                        
                        self.logger.info(f"Found {len(job_cards)} job listings on page {page_num + 1}")
                        
                        if not job_cards:
                            self.logger.warning(f"No jobs found on page {page_num + 1}")
                            if page_num == 0:
                                self.logger.debug(f"HTML snippet: {html[:500]}...")
                            break

                        for card in job_cards:
                            try:
                                job = self._parse_job_card(card, page)
                                if job:
                                    self.jobs.append(job)
                            except Exception as e:
                                self.logger.error(f"Error parsing job card: {e}")
                                continue
                        
                        if page_num < pages - 1:
                            random_delay()
                            
                    except Exception as e:
                        self.logger.error(f"Error scraping Indeed.ie page {page_num + 1}: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            self.logger.error(f"Error initializing Playwright: {e}")
        
        self.logger.info(f"Indeed.ie scrape completed. Found {len(self.jobs)} jobs total")
        return self.jobs
    
    def _extract_text(self, card, selector_key):
        """Helper to extract text using configured selectors."""
        selectors = self.config['selectors'].get(selector_key, [])
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                return self._clean_text(elem.get_text())
        return ''

    def _parse_job_card(self, card, page):
        """Parse a single job card and fetch full details."""
        try:
            job = {}
            
            # Title
            title = self._extract_text(card, 'title')
            job['title'] = title
            if not title:
                return None
            
            # URL
            url = ''
            for selector in self.config['selectors']['title']:
                elem = card.select_one(selector)
                if elem:
                    if elem.name == 'a':
                        href = elem.get('href')
                        if href:
                            url = self.base_url + href if href.startswith('/') else href
                            break
                    else:
                        link = elem.find('a')
                        if link:
                            href = link.get('href')
                            if href:
                                url = self.base_url + href if href.startswith('/') else href
                                break
            job['url'] = url
            
            job['company'] = self._extract_text(card, 'company')
            job['location'] = self._extract_text(card, 'location')
            job['salary'] = self._extract_text(card, 'salary')
            
            # Extract description snippet from the search results card (if available)
            # Note: Full descriptions require bypassing Cloudflare, so we extract what's available here
            job['description'] = self._extract_text(card, 'description')
            job['posted_date'] = ''  # Posted date not available on search results page
            
            self.logger.debug(f"Extracted job: {job['title']} at {job['company']}")
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job details: {e}")
            return None
    
    def _fetch_job_details(self, job_url, page):
        """Fetch full job description and posting date from job detail page."""
        details = {'description': '', 'posted_date': ''}
        
        try:
            self.logger.info(f"Fetching full details from: {job_url}")
            
            # Navigate to job detail page
            page.goto(job_url, wait_until='domcontentloaded', timeout=15000)
            page.wait_for_timeout(3000)  # Wait 3 seconds for dynamic content to load
            
            # Get the HTML and parse it
            html = page.content()
            
            # Debug: save first job HTML to file
            import os
            if not hasattr(self, '_debug_saved'):
                with open('debug_job_page.html', 'w', encoding='utf-8') as f:
                    f.write(html)
                self._debug_saved = True
                self.logger.info(f"Saved debug HTML to debug_job_page.html")
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract full job description
            description_selectors = [
                'div#jobDescriptionText',
                'div.jobsearch-jobDescriptionText',
                'div[id*="jobDesc"]',
                'div.job-description',
            ]
            
            for selector in description_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = self._clean_text(desc_elem.get_text())
                    self.logger.info(f"Selector '{selector}' found: {len(description)} chars (before filter)")
                    if len(description) > 50:
                        details['description'] = description
                        self.logger.info(f"Description accepted: {len(description)} chars")
                        break
                else:
                    self.logger.debug(f"Selector '{selector}' not found")
            
            # Extract posting date
            date_selectors = [
                'div.jobsearch-JobMetadataFooter',
                'span.date',
                'div[class*="date"]',
                'span[class*="date"]',
            ]
            
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = self._clean_text(date_elem.get_text())
                    # Look for patterns like "Posted 3 days ago", "Today", etc.
                    if any(word in date_text.lower() for word in ['posted', 'today', 'yesterday', 'day', 'week', 'hour', 'ago']):
                        details['posted_date'] = date_text
                        break
            
            # If no specific date found, try to find it in the footer/metadata
            if not details['posted_date']:
                footer = soup.find('div', class_=lambda x: x and 'footer' in x.lower())
                if footer:
                    footer_text = self._clean_text(footer.get_text())
                    # Extract date-like strings
                    import re
                    date_match = re.search(r'(Posted|Active)?\s*(Today|Yesterday|\d+\s+(?:hour|day|week)s?\s+ago)', footer_text, re.IGNORECASE)
                    if date_match:
                        details['posted_date'] = date_match.group(0).strip()
            
            return details
            
        except Exception as e:
            self.logger.error(f"Could not fetch full details from {job_url}: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return details
