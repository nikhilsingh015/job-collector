"""Configuration settings for the job scraper."""

# Scraping Settings
REQUEST_TIMEOUT = 30
PAGE_LOAD_TIMEOUT = 30000  # ms for Playwright
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
MIN_DELAY = 5
MAX_DELAY = 15

# User Agent Rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

# Selectors and URLs
SCRAPER_CONFIG = {
    'indeed': {
        'base_url': 'https://ie.indeed.com',
        'jobs_per_page': 10,
        'selectors': {
            'job_card': ['div.job_seen_beacon', 'td.resultContent', 'div.cardOutline'],
            'title': ['h2.jobTitle', 'a.jcs-JobTitle'],
            'company': ['span.companyName', 'span[data-testid="company-name"]'],
            'location': ['div.companyLocation', 'div[data-testid="text-location"]'],
            'salary': ['div.salary-snippet', 'div[data-testid="attribute_snippet_testid"]'],
            'description': ['div.job-snippet', 'div[data-testid="job-snippet"]'],
        }
    },
    'irishjobs': {
        'base_url': 'https://www.irishjobs.ie',
        'jobs_per_page': 25,  # Approximate
        'selectors': {
            'job_card': ['article.job', 'div.job-item', 'div.res-1t6m82k'], # updated selector
            'title': ['h2.job-title', 'a.job-link', 'a.res-1na8b7y'],
            'company': ['span.company', 'div.employer', 'a.res-14k2z3y'],
            'location': ['span.location', 'div.job-location', 'span.res-1c25221'],
            'salary': ['span.salary', 'div.job-salary', 'span.res-1dp9s8x'],
            'description': ['div.job-description', 'p.description', 'span.res-162u0s4'],
        }
    },
    'linkedin': {
        'base_url': 'https://www.linkedin.com',
        'jobs_per_page': 25,
        'selectors': {
            'job_card': 'li.jobs-search-results__list-item',
            'title': 'h3.base-search-card__title',
            'company': ['h4.base-search-card__subtitle', 'a.hidden-nested-link'],
            'location': 'span.job-search-card__location',
            'salary': 'span.job-search-card__salary-info',
            'description': 'p.base-search-card__snippet',
            'link': 'a.base-card__full-link'
        }
    }
}
