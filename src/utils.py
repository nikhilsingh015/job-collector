"""Utility functions for the job scraper."""
import random
import time
import logging
from src.config import MIN_DELAY, MAX_DELAY


def random_delay(min_seconds=MIN_DELAY, max_seconds=MAX_DELAY):
    """Sleep for a random amount of time between min and max seconds."""
    delay = random.uniform(min_seconds, max_seconds)
    logger = logging.getLogger(__name__)
    logger.debug(f"Sleeping for {delay:.2f} seconds")
    time.sleep(delay)


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('job_scraper.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
