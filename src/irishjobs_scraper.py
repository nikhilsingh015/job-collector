"""IrishJobs.ie job scraper."""
import requests
from bs4 import BeautifulSoup
from src.base_scraper import BaseScraper
from src.utils import random_delay
from src.network import create_session
from src.config import REQUEST_TIMEOUT


class IrishJobsScraper(BaseScraper):
    """Scraper for IrishJobs.ie job listings."""
    
    def __init__(self):
        super().__init__('irishjobs')
        self.base_url = self.config.get('base_url', 'https://www.irishjobs.ie')
        self.session = create_session()
    
    def scrape(self, query, location, pages=1):
        """
        Scrape jobs from IrishJobs.ie.
        """
        self.jobs = []
        self.logger.info(f"Starting IrishJobs.ie scrape: query='{query}', location='{location}', pages={pages}")
        
        for page in range(1, pages + 1):
            try:
                search_url = f"{self.base_url}/jobs"
                params = {
                    'Keywords': query,
                    'Location': location,
                    'Page': page
                }
                
                self.logger.info(f"Fetching page {page} from IrishJobs.ie")
                try:
                    response = self.session.get(search_url, params=params, timeout=REQUEST_TIMEOUT)
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    self.logger.error(f"HTTP Error: {e}")
                    if response.status_code == 404:
                         self.logger.warning("Page not found, stopping pagination.")
                         break
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job cards
                job_cards = []
                for selector in self.config['selectors']['job_card']:
                    found = soup.select(selector)
                    if found:
                        job_cards = found
                        break
                
                self.logger.info(f"Found {len(job_cards)} job listings on page {page}")
                
                if not job_cards:
                    self.logger.warning(f"No jobs found on page {page}, stopping pagination")
                    break
                
                for card in job_cards:
                    try:
                        job = self._parse_job_card(card)
                        if job:
                            self.jobs.append(job)
                    except Exception as e:
                        self.logger.error(f"Error parsing job card: {e}")
                        continue
                
                if page < pages:
                    random_delay()
                    
            except Exception as e:
                self.logger.error(f"Error scraping IrishJobs.ie page {page}: {e}")
                continue
        
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
