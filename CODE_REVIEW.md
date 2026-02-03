# Code Review: Job Collector

## 1. Code Quality
*   **Severity**: Medium
*   **Location**: `src/indeed_scraper.py`, `src/irishjobs_scraper.py`, `src/linkedin_scraper.py`
*   **Explanation**: Violates DRY (Don't Repeat Yourself) principle. The scraping loops and HTML parsing logic structure are very similar across files but duplicated. Hardcoded selectors (magic strings) are scattered throughout the code.
*   **Fix**:
    1.  Extract selectors into a configuration file (JSON/YAML) or a constants module.
    2.  Create a more robust `BaseScraper` that handles the generic "fetch page -> parse items -> next page" loop if possible, or at least standardized request handling.

## 2. Error Handling
*   **Severity**: High
*   **Location**: `src/indeed_scraper.py:48`, `src/linkedin_scraper.py:43`
*   **Explanation**:
    *   **Broad Exception Handling**: `except Exception as e` catches everything, including KeyboardInterrupts in some contexts (though not here usually), but mainly it hides specific network errors like 403 Forbidden or 429 Too Many Requests which require different handling (backoff vs stop).
    *   **HTTP Errors**: `response.raise_for_status()` is used, but there's no specific handling for 403 (Cloudflare/Bot detection) or 429 (Rate Limit). The scraper will just log an error and move to the next page, potentially triggering more blocks.
*   **Fix**:
    *   Implement specific exception handling for `requests.exceptions.HTTPError`.
    *   Add retry logic with exponential backoff for 429/5xx errors.
    *   For 403, detect it and abort/pause, as continuing is futile.

## 3. Scraping Ethics
*   **Severity**: Medium
*   **Location**: `src/utils.py`
*   **Explanation**:
    *   **Robots.txt**: The scrapers do not check `robots.txt` permissions.
    *   **Delays**: `random_delay` (3-7s) is decent, but might be too fast for strict sites like LinkedIn if scraping many pages.
*   **Fix**:
    *   Implement a `RobotsParser` check (though many job sites disallow scraping in robots.txt, so this is a policy decision).
    *   Increase default delays or make them configurable.

## 4. Security
*   **Severity**: Low
*   **Location**: `scraper.py` (CLI arguments)
*   **Explanation**: Input validation is minimal. While not critical for a CLI tool, passing weird characters into the URL parameters without proper encoding (though `requests` handles params encoding usually) could be an issue.
*   **Fix**: Ensure inputs are sanitized.

## 5. Performance
*   **Severity**: Medium
*   **Location**: `src/linkedin_scraper.py`
*   **Explanation**:
    *   **Browser Instantiation**: The Playwright scraper launches a new browser context for the session. This is fine, but for daily runs, persistent context (saving cookies) would reduce the likelihood of hitting auth walls.
    *   **Synchronous Scraping**: The scrapers run sequentially (Indeed -> IrishJobs -> LinkedIn).
*   **Fix**:
    *   Use `asyncio` to run scrapers in parallel (though this increases the "noise" on the network, for a personal laptop it saves time). *Note: Given the user wants "Reliability" and runs it locally, sequential is actually safer to avoid flagging.*

## 6. Reliability
*   **Severity**: Critical
*   **Location**: `src/indeed_scraper.py`, `src/linkedin_scraper.py`
*   **Explanation**:
    *   **Anti-Bot Detection**: Indeed and LinkedIn have aggressive bot detection. A simple `requests` call to Indeed will almost certainly return a 403 Cloudflare challenge after a few requests or even the first one.
    *   **Selectors**: CSS selectors like `div.job_seen_beacon` or `div.job_seen_beacon` are prone to change.
*   **Fix**:
    *   Use `playwright` (or `selenium`) with `stealth` plugins for Indeed as well, or a scraping API.
    *   For the "No Paid Proxy" constraint: Use `undetected-chromedriver` or similar Playwright stealth techniques.
    *   **Deduplication**: The scraper doesn't check if it has seen a job before. Daily runs will result in massive duplicate data.

## 7. Testing
*   **Severity**: High
*   **Location**: `test_scraper.py`
*   **Explanation**: The tests only use `MockScraper`. There are no integration tests or unit tests for the *actual* parsing logic (e.g. feeding an HTML file to the parser). If the site structure changes, tests still pass, which gives false confidence.
*   **Fix**:
    *   Save sample HTML files from each site.
    *   Write tests that parse these local HTML files to verify selectors work.

## 8. Documentation
*   **Severity**: Low
*   **Location**: `README.md`
*   **Explanation**: Documentation is clear but lacks troubleshooting for common scraping issues (Captcha, 403s).
*   **Fix**: Add a "Troubleshooting" section.

---

# 3-5 Improvements for Production-Readiness (Daily Personal Use)

1.  **Job History & Deduplication (SQLite)**
    *   **Why**: You only want to see *new* jobs each day.
    *   **How**: Create a local SQLite database `jobs.db`. Before adding a job to the results, check if its URL (or a hash of title+company+location) exists in the DB. If yes, skip. If no, save to DB and add to "New Jobs" list.

2.  **Robust Configuration (Config File)**
    *   **Why**: When selectors change (and they will), you shouldn't hunt through python files.
    *   **How**: Move all CSS selectors, base URLs, and timeout settings into `config.json` or `settings.py`.

3.  **Enhanced HTML Reporting**
    *   **Why**: Reading a CSV is tedious.
    *   **How**: Generate a simple HTML report (e.g., `daily_jobs_2023-10-27.html`) with clickable links and highlighted salary info for the *new* jobs found.

4.  **Resilient Networking (Retries & Headers)**
    *   **Why**: Networks fail, and sites rate-limit.
    *   **How**: Implement a `requests.Session` with `HTTPAdapter` for retries on 500/502/503/504 errors. Use a better library for User-Agent rotation (like `fake-useragent`).

5.  **Hybrid Scraping Approach**
    *   **Why**: `requests` fails on Indeed.
    *   **How**: Implement robust `requests` handling with session management, retries, and browser-like headers. Optionally move to Playwright if strict blocking persists.
