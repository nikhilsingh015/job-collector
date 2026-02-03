#!/usr/bin/env python3
"""Test fetching job details from Indeed"""
import json

# Load the jobs
data = json.load(open('data/jobs_20260203.json'))

print(f"Total jobs: {len(data)}\n")

# Check what fields we have
if data:
    print("Fields in first job:")
    for key, value in data[0].items():
        val_preview = str(value)[:100] if value else "(empty)"
        print(f"  {key}: {val_preview}")
    
    # Count jobs with each field
    print(f"\nJobs with data:")
    print(f"  Description: {sum(1 for j in data if j.get('description'))}")
    print(f"  Posted date: {sum(1 for j in data if j.get('posted_date'))}")
    print(f"  Salary: {sum(1 for j in data if j.get('salary'))}")
    
    # Show a sample with description
    jobs_with_desc = [j for j in data if j.get('description')]
    if jobs_with_desc:
        print(f"\n=== Sample Job with Description ===")
        job = jobs_with_desc[0]
        print(f"Title: {job['title']}")
        print(f"Company: {job.get('company', '')}")
        print(f"Posted: {job.get('posted_date', 'N/A')}")
        print(f"Description ({len(job['description'])} chars):")
        print(f"{job['description'][:500]}...")
    else:
        print(f"\n⚠️ No jobs have descriptions!")
        print(f"\nFirst job URL: {data[0].get('url', 'N/A')}")
