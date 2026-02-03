"""LinkedIn job scraper using Playwright."""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from src.base_scraper import BaseScraper
from src.utils import random_delay
from src.config import USER_AGENTS
import random


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings using Playwright."""
    
    def __init__(self):
        super().__init__('linkedin')
        self.base_url = self.config.get('base_url', 'https://www.linkedin.com')
    
    def scrape(self, query, location, pages=1):
        """
        Scrape jobs from LinkedIn.
        """
        self.jobs = []
        self.logger.info(f"Starting LinkedIn scrape: query='{query}', location='{location}', pages={pages}")
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)

                # Use a random user agent from config
                user_agent = random.choice(USER_AGENTS)

                context = browser.new_context(
                    user_agent=user_agent,
                    viewport={'width': 1920, 'height': 1080}
                )

                page = context.new_page()
                
                jobs_per_page = self.config.get('jobs_per_page', 25)

                for page_num in range(pages):
                    try:
                        start = page_num * jobs_per_page
                        search_url = f"{self.base_url}/jobs/search/?keywords={query}&location={location}&start={start}"
                        
                        self.logger.info(f"Fetching page {page_num + 1} from LinkedIn")
                        
                        try:
                            # Use domcontentloaded instead of networkidle (faster and more reliable)
                            page.goto(search_url, wait_until='domcontentloaded', timeout=60000)
                            page.wait_for_timeout(3000)  # Wait for dynamic content
                        except PlaywrightTimeoutError:
                            self.logger.error(f"Timeout loading page {page_num + 1}")
                            continue
                        
                        # Check if we hit an auth wall
                        if "authwall" in page.url or "login" in page.url:
                            self.logger.error("Hit LinkedIn Authwall. LinkedIn requires login for job searches.")
                            break
                        
                        # Wait for job cards
                        card_selector = self.config['selectors']['job_card']
                        if isinstance(card_selector, list):
                            card_selector = card_selector[0]

                        try:
                            page.wait_for_selector(card_selector, timeout=10000)
                        except PlaywrightTimeoutError:
                            self.logger.warning(f"Timeout waiting for job listings on page {page_num + 1}")
                            continue
                        
                        # Scroll
                        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        page.wait_for_timeout(2000)
                        
                        job_cards = page.query_selector_all(card_selector)
                        self.logger.info(f"Found {len(job_cards)} job listings on page {page_num + 1}")
                        
                        for card in job_cards:
                            try:
                                job = self._parse_job_card(card)
                                if job:
                                    self.jobs.append(job)
                            except Exception as e:
                                self.logger.error(f"Error parsing job card: {e}")
                                continue
                        
                        if page_num < pages - 1:
                            random_delay()
                            
                    except Exception as e:
                        self.logger.error(f"Error scraping LinkedIn page {page_num + 1}: {e}")
                        continue
                
                browser.close()
                
        except Exception as e:
            self.logger.error(f"Error initializing Playwright: {e}")
        
        self.logger.info(f"LinkedIn scrape completed. Found {len(self.jobs)} jobs total")
        return self.jobs
    
    def _extract_text(self, card, selector_key):
        """Helper to extract text from Playwright element."""
        selectors = self.config['selectors'].get(selector_key, [])
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            elem = card.query_selector(selector)
            if elem:
                return self._clean_text(elem.inner_text())
        return ''

    def _parse_job_card(self, card):
        """Parse a single job card."""
        try:
            job = {}
            
            job['title'] = self._extract_text(card, 'title')
            if not job['title']:
                return None
            
            # URL
            # LinkedIn URL selector
            url_selectors = self.config['selectors'].get('link', 'a.base-card__full-link')
            if isinstance(url_selectors, str):
                url_selectors = [url_selectors]
            
            job['url'] = ''
            for selector in url_selectors:
                link_elem = card.query_selector(selector)
                if link_elem:
                    job['url'] = link_elem.get_attribute('href') or ''
                    break
            
            job['company'] = self._extract_text(card, 'company')
            job['location'] = self._extract_text(card, 'location')
            job['salary'] = self._extract_text(card, 'salary')
            job['description'] = self._extract_text(card, 'description')
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job details: {e}")
            return None
