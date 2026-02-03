# Job Collector

A Python web scraper for educational purposes that automatically parses your CV and collects relevant job listings from Indeed.ie, IrishJobs.ie, and LinkedIn.

## Features

- **Automatic CV Parsing**: Extracts skills, experience, and job titles from your resume
- **Smart Job Search**: Generates relevant search queries based on your profile
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
- Generates HTML reports for easy viewing
- Implements anti-detection measures:
  - Random delays (3-7 seconds)
  - User-agent rotation
- Job deduplication using SQLite database
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

## Quick Start (Automated Mode)

The easiest way to use Job Collector is with the automated mode that parses your CV:

1. Place your CV/Resume PDF in the project directory (filename should contain "CV" or "Resume")
2. Run:
```bash
python main.py
```

The tool will:
1. Automatically find and parse your CV
2. Extract relevant job titles and skills
3. Search multiple job sites for matching positions
4. Output a consolidated CSV file with all results

### Automated Mode Options

```bash
# Use default settings (auto-detect CV, 5 queries, 1 page per source)
python main.py

# Specify a CV file
python main.py --cv "path/to/your/cv.pdf"

# Override the search location
python main.py --location "Cork"

# Scrape more pages per source
python main.py --pages 3

# Limit the number of search queries
python main.py --queries-limit 3

# Specify output file
python main.py --output "my_jobs.csv"

# Ignore job history (include previously seen jobs)
python main.py --ignore-history
```

## Manual Mode

You can also run the scraper manually with specific queries:

```bash
python scraper.py --query "software engineer" --location "Dublin" --pages 2
```

### Manual Mode Arguments

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
- `title` - Job title
- `company` - Company name
- `location` - Job location
- `salary` - Salary information (if available)
- `description` - Job description snippet
- `url` - Link to full job posting
- `source` - Source website (indeed, irishjobs, or linkedin)

### Example Output

```
title,company,location,salary,description,url,source
Software Engineer,Tech Company,Dublin,"€50,000 - €70,000",We are looking for a talented engineer...,https://ie.indeed.com/jobs/...,indeed
Senior Developer,Innovation Ltd,Cork,€60,000+,Join our growing team...,https://www.irishjobs.ie/jobs/...,irishjobs
```

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
│   ├── cv_parser.py         # CV/Resume PDF parser
│   ├── config.py            # Configuration settings
│   ├── indeed_scraper.py    # Indeed.ie scraper
│   ├── irishjobs_scraper.py # IrishJobs.ie scraper
│   ├── linkedin_scraper.py  # LinkedIn scraper
│   ├── network.py           # Network utilities
│   ├── reporter.py          # HTML report generator
│   ├── storage.py           # Job history storage
│   └── utils.py             # Utility functions
├── data/                     # Output directory for CSV files
├── main.py                  # Automated CV-based job collector
├── scraper.py               # Manual CLI script
├── test_scraper.py          # Test suite
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Testing

A test script is provided to validate the scraper functionality:

```bash
python test_scraper.py
```

This test script uses mock data to verify:
- CSV file creation and formatting
- Data merging functionality
- Logging system
- Base scraper functionality

**Note**: The actual scrapers require internet access to the job websites. The test script demonstrates the functionality without requiring external network access.

## Educational Purpose

This scraper is built for educational purposes to demonstrate:
- Web scraping techniques with BeautifulSoup and Playwright
- HTTP requests with proper headers and delays
- Data extraction and CSV file handling
- Error handling and logging
- Command-line interface development

**Important Notes**:
- Always respect website terms of service and robots.txt files
- Use responsibly and ethically
- Implement appropriate delays to avoid overloading servers
- Be aware that websites may change their HTML structure, requiring scraper updates
- Some websites may block scraping attempts; this is for educational purposes only

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- playwright
- lxml

## License

This project is for educational purposes only.