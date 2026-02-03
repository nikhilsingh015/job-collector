#!/usr/bin/env python3
"""
Test script to fetch a single job description and see what we get.
This helps debug the Cloudflare bypass approach.
"""

import json
from fetch_descriptions import fetch_job_description, extract_job_key, create_clean_url

# Load the first job from our data
with open('data/jobs_20260203.json', 'r') as f:
    jobs = json.load(f)

if jobs:
    job = jobs[0]
    print(f"Testing with job: {job['title']}")
    print(f"Company: {job['company']}")
    print(f"Original URL: {job['url']}\n")
    
    # Extract job key
    job_key = extract_job_key(job['url'])
    if job_key:
        clean_url = create_clean_url(job_key)
        print(f"Job Key: {job_key}")
        print(f"Clean URL: {clean_url}\n")
    else:
        clean_url = job['url']
        print("Could not extract job key, using original URL\n")
    
    print("="*60)
    print("Fetching with stealth mode enabled (visible browser)...")
    print("="*60)
    
    # Fetch with visible browser so we can see what happens
    result = fetch_job_description(clean_url, use_stealth=True, headless=False)
    
    print(f"\nStatus: {result['status']}")
    if result['status'] == 'success':
        print(f"Description length: {len(result['description'])} characters")
        print(f"Posted date: {result['posted_date']}")
        print(f"\nDescription preview (first 500 chars):")
        print("="*60)
        print(result['description'][:500])
        print("="*60)
    else:
        print(f"Error: {result['error']}")
        print("\nCheck debug_failed.html for the page content")
else:
    print("No jobs found in data file!")
