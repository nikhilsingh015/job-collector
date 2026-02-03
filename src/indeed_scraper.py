"""Indeed.ie job scraper."""
import requests
from bs4 import BeautifulSoup
from src.base_scraper import BaseScraper
from src.utils import random_delay
from src.network import create_session
from src.config import REQUEST_TIMEOUT


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.ie job listings."""
    
    def __init__(self):
        super().__init__('indeed')
        self.base_url = self.config.get('base_url', 'https://ie.indeed.com')
        self.session = create_session()
    
    def scrape(self, query, location, pages=1):
        """
        Scrape jobs from Indeed.ie.
        """
        self.jobs = []
        self.logger.info(f"Starting Indeed.ie scrape: query='{query}', location='{location}', pages={pages}")
        
        jobs_per_page = self.config.get('jobs_per_page', 10)

        for page in range(pages):
            try:
                start = page * jobs_per_page
                
                params = {
                    'q': query,
                    'l': location,
                    'start': start
                }
                
                url = f"{self.base_url}/jobs"
                
                self.logger.info(f"Fetching page {page + 1} from Indeed.ie")
                try:
                    response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if response.status_code == 403:
                        self.logger.error("Indeed returned 403 Forbidden (likely bot detection). Stopping scrape.")
                        break
                    elif response.status_code == 429:
                        self.logger.warning("Rate limited (429). Waiting before retrying...")
                        random_delay(30, 60)
                        continue
                    else:
                        raise e
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job cards using configured selectors
                job_cards = []
                for selector in self.config['selectors']['job_card']:
                    found = soup.select(selector)
                    if found:
                        job_cards = found
                        break
                
                self.logger.info(f"Found {len(job_cards)} job listings on page {page + 1}")
                
                if not job_cards:
                    self.logger.warning(f"No jobs found on page {page + 1}. Check selectors or if blocked.")
                    # If we found 0 jobs on page 1, we might be blocked or selectors changed.
                    # If we found 0 on page > 1, maybe we reached the end.
                    if page == 0:
                        self.logger.debug(f"HTML Content: {response.text[:500]}...")

                for card in job_cards:
                    try:
                        job = self._parse_job_card(card)
                        if job:
                            self.jobs.append(job)
                    except Exception as e:
                        self.logger.error(f"Error parsing job card: {e}")
                        continue
                
                if page < pages - 1:
                    random_delay()
                    
            except Exception as e:
                self.logger.error(f"Error scraping Indeed.ie page {page + 1}: {e}")
                continue
        
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

    def _parse_job_card(self, card):
        """Parse a single job card."""
        try:
            job = {}
            
            # Title
            title = self._extract_text(card, 'title')
            job['title'] = title
            if not title:
                return None
            
            # URL
            # Url usually is in the 'title' element which is an anchor or contains an anchor
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
