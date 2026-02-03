# Complete Job Scraper - Single Executable

A unified script that scrapes jobs and fetches full descriptions with **upsert logic** - automatically updates existing entries or creates new ones.

## ✅ Status

The background job is **COMPLETED**:
- **44 out of 45 jobs** successfully fetched (97.8% success rate)
- Results saved to: `data/jobs_with_descriptions.json`

## Quick Start

### Run Full Pipeline (Scrape + Enrich)

```bash
.venv/bin/python run_scraper.py
```

This will:
1. Scrape new jobs from Indeed based on your CV
2. Enrich them with full descriptions
3. Generate HTML report
4. Use **upsert logic**: updates existing jobs or creates new ones

### Enrich Existing Jobs Only

```bash
.venv/bin/python run_scraper.py --enrich-only --input data/jobs_20260203.json --output data/jobs_complete.json
```

This mode:
- Reads jobs from input file
- Fetches missing descriptions
- **Skips jobs that already have descriptions**
- Updates the output file progressively

### Scrape Jobs Only (No Descriptions)

```bash
.venv/bin/python run_scraper.py --scrape-only --output data/jobs_basic.json
```

## Upsert Logic

The script uses **smart upsert** based on job URL:

```
IF job URL exists in output file:
  - Skip if already has description (saves time!)
  - Otherwise, fetch description and UPDATE existing entry
ELSE:
  - INSERT new job entry
```

This means:
- ✅ Safe to run multiple times
- ✅ Won't duplicate jobs
- ✅ Won't re-fetch existing descriptions
- ✅ Progressively builds complete dataset
- ✅ Can be interrupted and resumed

## Command Line Options

```
--cv PATH              Path to CV file (optional)
--scrape-only          Only scrape jobs, don't fetch descriptions
--enrich-only          Only enrich existing jobs with descriptions
--input PATH           Input jobs file (default: data/jobs.json)
--output PATH          Output file path (default: data/jobs_complete.json)
--visible              Run browser in visible mode (for debugging)
--limit N              Process only first N jobs (for testing)
```

## Examples

### Test with 5 Jobs

```bash
.venv/bin/python run_scraper.py --enrich-only --input data/jobs_20260203.json --limit 5 --visible
```

### Resume Interrupted Job

```bash
# The script automatically skips jobs that already have descriptions
.venv/bin/python run_scraper.py --enrich-only --input data/jobs_20260203.json --output data/jobs_complete.json
```

### Full Pipeline in Background

```bash
nohup .venv/bin/python run_scraper.py --output data/jobs_complete.json > scraper.log 2>&1 &
```

## Output Format

All jobs saved to JSON with complete data:

```json
[
  {
    "title": "Software Engineer",
    "company": "Tech Corp",
    "location": "Dublin",
    "url": "https://ie.indeed.com/...",
    "salary": "€60,000 - €80,000",
    "description": "Full 4000+ character description...",
    "posted_date": "Posted 2 days ago",
    "search_query": "Software Engineer"
  }
]
```

## Performance

- **Scraping**: ~45 jobs in 1 minute (fast)
- **Description fetching**: ~6-10 seconds per job
- **Success rate**: ~97% with Cloudflare bypass
- **Smart caching**: Skips jobs with existing descriptions

## Monitoring Progress

Check log file:

```bash
tail -f job_scraper.log
```

The script logs:
- Which jobs are being processed
- Description lengths
- Success/failure status
- Total counts

## Troubleshooting

### Job Already Has Description

```
✓ Job already has description, skipping
```

This is normal! The script is saving time by not re-fetching.

### Cloudflare Challenge

```
Cloudflare challenge detected, waiting...
```

The script automatically waits for challenges to complete (up to 15 seconds).

### Rate Limiting

The script includes:
- Random 3-6 second delays between requests
- Human-like scrolling behavior
- Realistic browser fingerprints

If you still get rate limited, wait 10-15 minutes before retrying.

## Migration from Old Scripts

If you have existing data:

```bash
# Enrich old scraped jobs
.venv/bin/python run_scraper.py --enrich-only --input data/jobs_20260203.json --output data/jobs_complete.json

# The new file will have all jobs with descriptions added
```

## Benefits Over Separate Scripts

✅ **Single command** - no need to run multiple scripts  
✅ **Upsert logic** - safe to run repeatedly  
✅ **Progressive saving** - no data loss if interrupted  
✅ **Smart caching** - skips existing descriptions  
✅ **Unified logging** - single log file to monitor  
✅ **Flexible modes** - scrape-only, enrich-only, or full pipeline  

## Next Steps

1. Check your results: `cat data/jobs_complete.json | grep description | wc -l`
2. Open HTML report: `open data/report_*.html`
3. Run again to catch any new jobs: `.venv/bin/python run_scraper.py`
