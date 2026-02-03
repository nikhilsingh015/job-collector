"""Indeed.ie job scraper."""
import requests
from bs4 import BeautifulSoup
from src.base_scraper import BaseScraper
from src.utils import get_random_user_agent, random_delay
import logging


class IndeedScraper(BaseScraper):
    """Scraper for Indeed.ie job listings."""
    
    def __init__(self):
        super().__init__('indeed')
        self.base_url = 'https://ie.indeed.com'
    
    def scrape(self, query, location, pages=1):
        """
        Scrape jobs from Indeed.ie.
        
        Args:
            query: Job search query
            location: Location to search in
            pages: Number of pages to scrape
            
        Returns:
            List of job dictionaries
        """
        self.jobs = []
        self.logger.info(f"Starting Indeed.ie scrape: query='{query}', location='{location}', pages={pages}")
        
        for page in range(pages):
            try:
                # Calculate start parameter (Indeed uses 10 jobs per page)
                start = page * 10
                
                # Build search URL
                params = {
                    'q': query,
                    'l': location,
                    'start': start
                }
                
                url = f"{self.base_url}/jobs"
                
                # Make request with random user agent
                headers = {'User-Agent': get_random_user_agent()}
                
                self.logger.info(f"Fetching page {page + 1} from Indeed.ie")
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Parse HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find job cards - Indeed uses various class names, we'll try multiple selectors
                job_cards = soup.find_all('div', class_='job_seen_beacon')
                
                if not job_cards:
                    # Try alternative selector
                    job_cards = soup.find_all('td', class_='resultContent')
                
                self.logger.info(f"Found {len(job_cards)} job listings on page {page + 1}")
                
                for card in job_cards:
                    try:
                        job = self._parse_job_card(card)
                        if job:
                            self.jobs.append(job)
                    except Exception as e:
                        self.logger.error(f"Error parsing job card: {e}")
                        continue
                
                # Random delay between pages
                if page < pages - 1:
                    random_delay()
                    
            except Exception as e:
                self.logger.error(f"Error scraping Indeed.ie page {page + 1}: {e}")
                continue
        
        self.logger.info(f"Indeed.ie scrape completed. Found {len(self.jobs)} jobs total")
        return self.jobs
    
    def _parse_job_card(self, card):
        """Parse a single job card."""
        try:
            job = {}
            
            # Title and URL
            title_elem = card.find('h2', class_='jobTitle')
            if not title_elem:
                title_elem = card.find('a', class_='jcs-JobTitle')
            
            if title_elem:
                link = title_elem.find('a') if title_elem.name != 'a' else title_elem
                if link:
                    job['title'] = self._clean_text(link.get_text())
                    job['url'] = self.base_url + link.get('href', '')
                else:
                    job['title'] = self._clean_text(title_elem.get_text())
                    job['url'] = ''
            else:
                return None
            
            # Company
            company_elem = card.find('span', class_='companyName')
            if not company_elem:
                company_elem = card.find('span', {'data-testid': 'company-name'})
            job['company'] = self._clean_text(company_elem.get_text()) if company_elem else ''
            
            # Location
            location_elem = card.find('div', class_='companyLocation')
            if not location_elem:
                location_elem = card.find('div', {'data-testid': 'text-location'})
            job['location'] = self._clean_text(location_elem.get_text()) if location_elem else ''
            
            # Salary
            salary_elem = card.find('div', class_='salary-snippet')
            if not salary_elem:
                salary_elem = card.find('div', {'data-testid': 'attribute_snippet_testid'})
            job['salary'] = self._clean_text(salary_elem.get_text()) if salary_elem else ''
            
            # Description
            desc_elem = card.find('div', class_='job-snippet')
            if not desc_elem:
                desc_elem = card.find('div', {'data-testid': 'job-snippet'})
            job['description'] = self._clean_text(desc_elem.get_text()) if desc_elem else ''
            
            return job
            
        except Exception as e:
            self.logger.error(f"Error parsing job details: {e}")
            return None
