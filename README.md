# Job Collector

A Python web scraper for educational purposes that collects job listings from Indeed.ie, IrishJobs.ie, and LinkedIn.

## Features

- Scrapes job listings from multiple sources:
  - Indeed.ie
  - IrishJobs.ie
  - LinkedIn
- Extracts comprehensive job information:
  - Title
  - Company
  - Location
  - Salary
  - Description
  - URL
- Saves data to CSV files (per source and merged)
- Implements anti-detection measures:
  - Random delays (3-7 seconds)
  - User-agent rotation
- Robust error handling and logging
- Command-line interface for easy use

## Installation

1. Clone the repository:
```bash
git clone https://github.com/nikhilsingh015/job-collector.git
cd job-collector
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

Run the scraper with the following command:

```bash
python scraper.py --query "software engineer" --location "Dublin" --pages 2
```

### Command-line Arguments

- `--query`: Job search query (required)
  - Example: "software engineer", "data scientist", "product manager"
- `--location`: Location to search in (required)
  - Example: "Dublin", "Ireland", "Cork"
- `--pages`: Number of pages to scrape per source (optional, default: 1)
  - Example: 1, 2, 3

### Examples

Search for software engineering jobs in Dublin:
```bash
python scraper.py --query "software engineer" --location "Dublin" --pages 1
```

Search for data science jobs in Ireland across multiple pages:
```bash
python scraper.py --query "data scientist" --location "Ireland" --pages 3
```

## Output

The scraper creates the following files in the `data/` directory:

- `jobs_indeed_YYYYMMDD.csv` - Jobs from Indeed.ie
- `jobs_irishjobs_YYYYMMDD.csv` - Jobs from IrishJobs.ie
- `jobs_linkedin_YYYYMMDD.csv` - Jobs from LinkedIn
- `jobs_merged_YYYYMMDD.csv` - All jobs combined from all sources

Each CSV file contains the following columns:
- title
- company
- location
- salary
- description
- url
- source

## Logging

The scraper logs all operations to:
- Console output (INFO level)
- `job_scraper.log` file (detailed logs)

## Project Structure

```
job-collector/
├── src/
│   ├── __init__.py
│   ├── base_scraper.py      # Base scraper class
│   ├── indeed_scraper.py    # Indeed.ie scraper
│   ├── irishjobs_scraper.py # IrishJobs.ie scraper
│   ├── linkedin_scraper.py  # LinkedIn scraper
│   └── utils.py             # Utility functions
├── data/                     # Output directory for CSV files
├── scraper.py               # Main CLI script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Educational Purpose

This scraper is built for educational purposes to demonstrate:
- Web scraping techniques with BeautifulSoup and Playwright
- HTTP requests with proper headers and delays
- Data extraction and CSV file handling
- Error handling and logging
- Command-line interface development

**Note**: Always respect website terms of service and robots.txt files. Use responsibly and ethically.

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- playwright
- lxml

## License

This project is for educational purposes only.