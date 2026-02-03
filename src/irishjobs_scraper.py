"""IrishJobs.ie job scraper using Playwright with stealth mode."""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
from src.base_scraper import BaseScraper
from src.utils import random_delay
from src.config import USER_AGENTS
import random
import time


class IrishJobsScraper(BaseScraper):
    """Scraper for IrishJobs.ie job listings using Playwright with stealth mode."""
    
    def __init__(self):
        super().__init__('irishjobs')
        self.base_url = self.config.get('base_url', 'https://www.irishjobs.ie')
    
    def scrape(self, query, location, pages=1):
        """
        Scrape jobs from IrishJobs.ie using Playwright with stealth mode.
        """
        self.jobs = []
        self.logger.info(f"Starting IrishJobs.ie scrape: query='{query}', location='{location}', pages={pages}")
        
        try:
            with sync_playwright() as p:
                # Launch with more realistic browser args
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                    ]
                )
                
                user_agent = random.choice(USER_AGENTS)
                
                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-IE',
                    timezone_id='Europe/Dublin',
                    extra_http_headers={
                        'Accept-Language': 'en-IE,en-US;q=0.9,en;q=0.8',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    }
                )
                
                page = context.new_page()
                
                # Apply stealth mode to avoid detection
                stealth = Stealth()
                stealth.apply_stealth_sync(page)
        
                for page_num in range(1, pages + 1):
                    try:
                        search_url = f"{self.base_url}/jobs?Keywords={query}&Location={location}&Page={page_num}"
                        
                        self.logger.info(f"Fetching page {page_num} from IrishJobs.ie")
                        
                        try:
                            # Navigate and wait for network to be idle
                            page.goto(search_url, wait_until='networkidle', timeout=60000)
                            
                            # Wait longer for Akamai bot protection challenge to complete
                            self.logger.debug("Waiting for Akamai challenge to complete...")
                            page.wait_for_timeout(8000)
                            
                            # Check if we're still on a challenge page
                            current_url = page.url
                            if 'bm-verify' in current_url or len(current_url) > len(search_url) + 100:
                                self.logger.warning(f"Still on challenge page, waiting longer...")
                                page.wait_for_timeout(10000)
                            
                        except PlaywrightTimeoutError:
                            self.logger.error(f"Timeout loading page {page_num}")
                            continue

                        # Get the page HTML
                        html = page.content()
                        
                        # Check if we got past bot protection
                        if 'akamai' in html.lower() or 'please wait' in html.lower():
                            self.logger.warning(f"Bot protection detected on page {page_num}, skipping")
                            break
                        
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Find job cards using multiple selectors
                        job_cards = []
                        for selector in self.config['selectors']['job_card']:
                            found = soup.select(selector)
                            if found:
                                job_cards = found
                                self.logger.debug(f"Found jobs using selector: {selector}")
                                break
                        
                        self.logger.info(f"Found {len(job_cards)} job listings on page {page_num}")
                        
                        if not job_cards:
                            self.logger.warning(f"No jobs found on page {page_num}")
                            if page_num == 1:
                                # Try to find any job-related elements for debugging
                                all_links = soup.find_all('a', href=True)
                                job_links = [a for a in all_links if 'job' in a.get('href', '').lower()]
                                self.logger.debug(f"Found {len(job_links)} links with 'job' in href")
                                self.logger.debug(f"HTML snippet: {html[:500]}...")
                            break
                        
                        for card in job_cards:
                            try:
                                job = self._parse_job_card(card)
                                if job:
                                    self.jobs.append(job)
                            except Exception as e:
                                self.logger.error(f"Error parsing job card: {e}")
                                continue
                        
                        if page_num < pages:
                            random_delay()
                            
                    except Exception as e:
                        self.logger.error(f"Error scraping IrishJobs.ie page {page_num}: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            self.logger.error(f"Error initializing Playwright: {e}")
        
        self.logger.info(f"IrishJobs.ie scrape completed. Found {len(self.jobs)} jobs total")
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

    def _parse_job_card(self, card):
        """Parse a single job card."""
        try:
            job = {}
            
            job['title'] = self._extract_text(card, 'title')
            if not job['title']:
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
            job['description'] = self._extract_text(card, 'description')
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job details: {e}")
            return None
