"""Base scraper class with common functionality."""
import logging
from abc import ABC, abstractmethod
from datetime import datetime
import csv
import os
from src.config import SCRAPER_CONFIG


class BaseScraper(ABC):
    """Base class for all job scrapers."""
    
    def __init__(self, source_name):
        """
        Initialize the base scraper.
        
        Args:
            source_name: Name of the job source (e.g., 'indeed', 'irishjobs')
        """
        self.source_name = source_name
        self.logger = logging.getLogger(f"{__name__}.{source_name}")
        self.jobs = []
        self.config = SCRAPER_CONFIG.get(source_name, {})
    
    @abstractmethod
    def scrape(self, query, location, pages):
        """
        Scrape job listings.
        
        Args:
            query: Job search query
            location: Location to search in
            pages: Number of pages to scrape
            
        Returns:
            List of job dictionaries
        """
        pass
    
    def save_to_csv(self, filename=None):
        """
        Save scraped jobs to CSV file.
        
        Args:
            filename: Optional custom filename. If not provided, uses standard naming.
            
        Returns:
            Path to the saved CSV file
        """
        if not self.jobs:
            self.logger.warning("No jobs to save")
            return None
        
        if filename is None:
            date_str = datetime.now().strftime('%Y%m%d')
            filename = f"data/jobs_{self.source_name}_{date_str}.csv"
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        # Define CSV headers
        headers = ['title', 'company', 'location', 'salary', 'description', 'url', 'source']
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                
                for job in self.jobs:
                    # Ensure all required fields exist
                    row = {
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', ''),
                        'salary': job.get('salary', ''),
                        'description': job.get('description', ''),
                        'url': job.get('url', ''),
                        'source': self.source_name
                    }
                    writer.writerow(row)
            
            self.logger.info(f"Saved {len(self.jobs)} jobs to {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Error saving to CSV: {e}")
            return None
    
    def _clean_text(self, text):
        """Clean and normalize text."""
        if not text:
            return ''
        return ' '.join(text.strip().split())
