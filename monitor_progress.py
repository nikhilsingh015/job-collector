#!/usr/bin/env python3
"""
Monitor the progress of description fetching.
"""

import json
import os
from datetime import datetime

def monitor_progress():
    """Monitor and display progress of description fetching."""
    
    input_file = 'data/jobs_20260203.json'
    output_file = 'data/jobs_with_descriptions.json'
    
    # Load original jobs
    if os.path.exists(input_file):
        with open(input_file, 'r') as f:
            original_jobs = json.load(f)
        total_jobs = len(original_jobs)
    else:
        print(f"Input file {input_file} not found!")
        return
    
    # Load updated jobs
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            updated_jobs = json.load(f)
    else:
        print(f"Output file {output_file} not found yet. Waiting for first update...")
        return
    
    # Count jobs with descriptions
    jobs_with_desc = sum(1 for job in updated_jobs if job.get('description') and len(job.get('description', '')) > 100)
    jobs_with_date = sum(1 for job in updated_jobs if job.get('posted_date'))
    
    # Calculate progress
    progress_pct = (jobs_with_desc / total_jobs) * 100 if total_jobs > 0 else 0
    
    # Display status
    print("=" * 70)
    print(f"Job Description Fetching Progress - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)
    print(f"Total jobs:              {total_jobs}")
    print(f"Jobs with descriptions:  {jobs_with_desc} ({progress_pct:.1f}%)")
    print(f"Jobs with posting date:  {jobs_with_date}")
    print(f"Remaining:               {total_jobs - jobs_with_desc}")
    print("=" * 70)
    
    # Show some sample jobs
    if jobs_with_desc > 0:
        print("\n📝 Sample jobs with descriptions:")
        count = 0
        for job in updated_jobs:
            if job.get('description') and len(job.get('description', '')) > 100:
                desc_len = len(job['description'])
                print(f"  • {job['title'][:50]:<50} ({desc_len:,} chars)")
                count += 1
                if count >= 5:
                    break
    
    # Show log tail if exists
    log_file = 'fetch_descriptions.log'
    if os.path.exists(log_file):
        print(f"\n📊 Recent log entries:")
        print("-" * 70)
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Show last 10 lines
            for line in lines[-10:]:
                print(f"  {line.rstrip()}")
    
    print()

if __name__ == '__main__':
    monitor_progress()
