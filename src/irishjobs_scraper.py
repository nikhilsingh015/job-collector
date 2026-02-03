"""IrishJobs.ie job scraper."""
import requests
from bs4 import BeautifulSoup
from src.base_scraper import BaseScraper
from src.utils import get_random_user_agent, random_delay
import logging


class IrishJobsScraper(BaseScraper):
    """Scraper for IrishJobs.ie job listings."""
    
    def __init__(self):
        super().__init__('irishjobs')
        self.base_url = 'https://www.irishjobs.ie'
    
    def scrape(self, query, location, pages=1):
        """
        Scrape jobs from IrishJobs.ie.
        
        Args:
            query: Job search query
            location: Location to search in
            pages: Number of pages to scrape
            
        Returns:
            List of job dictionaries
        """
        self.jobs = []
        self.logger.info(f"Starting IrishJobs.ie scrape: query='{query}', location='{location}', pages={pages}")
        
        for page in range(1, pages + 1):
            try:
                # Build search URL
                # IrishJobs uses a different URL structure
                search_url = f"{self.base_url}/jobs"
                params = {
                    'Keywords': query,
                    'Location': location,
                    'Page': page
                }
                
                # Make request with random user agent
                headers = {'User-Agent': get_random_user_agent()}
                
                self.logger.info(f"Fetching page {page} from IrishJobs.ie")
                response = requests.get(search_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job cards - IrishJobs specific selectors
                job_cards = soup.find_all('article', class_='job')
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.find_all('div', class_='job-item')
                
                self.logger.info(f"Found {len(job_cards)} job listings on page {page}")
                
                if len(job_cards) == 0:
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
                
                # Random delay between pages
                if page < pages:
                    random_delay()
                    
            except Exception as e:
                self.logger.error(f"Error scraping IrishJobs.ie page {page}: {e}")
                continue
        
        self.logger.info(f"IrishJobs.ie scrape completed. Found {len(self.jobs)} jobs total")
        return self.jobs
    
    def _parse_job_card(self, card):
        """Parse a single job card."""
        try:
            job = {}
            
            # Title and URL
            title_elem = card.find('h2', class_='job-title')
            if not title_elem:
                title_elem = card.find('a', class_='job-link')
            
            if title_elem:
                link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if link:
                    job['title'] = self._clean_text(link.get_text())
                    href = link.get('href', '')
                    job['url'] = self.base_url + href if href.startswith('/') else href
                else:
                    job['title'] = self._clean_text(title_elem.get_text())
                    job['url'] = ''
            else:
                return None
            
            # Company
            company_elem = card.find('span', class_='company')
            if not company_elem:
                company_elem = card.find('div', class_='employer')
            job['company'] = self._clean_text(company_elem.get_text()) if company_elem else ''
            
            # Location
            location_elem = card.find('span', class_='location')
            if not location_elem:
                location_elem = card.find('div', class_='job-location')
            job['location'] = self._clean_text(location_elem.get_text()) if location_elem else ''
            
            # Salary
            salary_elem = card.find('span', class_='salary')
            if not salary_elem:
                salary_elem = card.find('div', class_='job-salary')
            job['salary'] = self._clean_text(salary_elem.get_text()) if salary_elem else ''
            
            # Description
            desc_elem = card.find('div', class_='job-description')
            if not desc_elem:
                desc_elem = card.find('p', class_='description')
            job['description'] = self._clean_text(desc_elem.get_text()) if desc_elem else ''
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job details: {e}")
            return None
