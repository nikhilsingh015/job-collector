"""LinkedIn job scraper using Playwright."""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from src.base_scraper import BaseScraper
from src.utils import random_delay
import logging


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings using Playwright."""
    
    def __init__(self):
        super().__init__('linkedin')
        self.base_url = 'https://www.linkedin.com'
    
    def scrape(self, query, location, pages=1):
        """
        Scrape jobs from LinkedIn.
        
        Args:
            query: Job search query
            location: Location to search in
            pages: Number of pages to scrape
            
        Returns:
            List of job dictionaries
        """
        self.jobs = []
        self.logger.info(f"Starting LinkedIn scrape: query='{query}', location='{location}', pages={pages}")
        
        try:
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = context.new_page()
                
                for page_num in range(pages):
                    try:
                        # Calculate start parameter (LinkedIn uses 25 jobs per page typically)
                        start = page_num * 25
                        
                        # Build search URL
                        search_url = f"{self.base_url}/jobs/search/?keywords={query}&location={location}&start={start}"
                        
                        self.logger.info(f"Fetching page {page_num + 1} from LinkedIn")
                        page.goto(search_url, wait_until='networkidle', timeout=30000)
                        
                        # Wait for job cards to load
                        try:
                            page.wait_for_selector('ul.jobs-search__results-list', timeout=10000)
                        except PlaywrightTimeoutError:
                            self.logger.warning(f"Timeout waiting for job listings on page {page_num + 1}")
                            continue
                        
                        # Scroll to load all jobs on the page
                        page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        page.wait_for_timeout(2000)
                        
                        # Get job cards
                        job_cards = page.query_selector_all('li.jobs-search-results__list-item')
                        
                        self.logger.info(f"Found {len(job_cards)} job listings on page {page_num + 1}")
                        
                        for card in job_cards:
                            try:
                                job = self._parse_job_card(card)
                                if job:
                                    self.jobs.append(job)
                            except Exception as e:
                                self.logger.error(f"Error parsing job card: {e}")
                                continue
                        
                        # Random delay between pages
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
    
    def _parse_job_card(self, card):
        """Parse a single job card."""
        try:
            job = {}
            
            # Title and URL
            title_elem = card.query_selector('h3.base-search-card__title')
            if title_elem:
                job['title'] = self._clean_text(title_elem.inner_text())
            else:
                return None
            
            # URL
            link_elem = card.query_selector('a.base-card__full-link')
            if link_elem:
                job['url'] = link_elem.get_attribute('href') or ''
            else:
                job['url'] = ''
            
            # Company
            company_elem = card.query_selector('h4.base-search-card__subtitle')
            if not company_elem:
                company_elem = card.query_selector('a.hidden-nested-link')
            job['company'] = self._clean_text(company_elem.inner_text()) if company_elem else ''
            
            # Location
            location_elem = card.query_selector('span.job-search-card__location')
            job['location'] = self._clean_text(location_elem.inner_text()) if location_elem else ''
            
            # Salary - LinkedIn doesn't always show salary
            salary_elem = card.query_selector('span.job-search-card__salary-info')
            job['salary'] = self._clean_text(salary_elem.inner_text()) if salary_elem else ''
            
            # Description - Get snippet from card
            desc_elem = card.query_selector('p.base-search-card__snippet')
            job['description'] = self._clean_text(desc_elem.inner_text()) if desc_elem else ''
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job details: {e}")
            return None
