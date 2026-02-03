#!/usr/bin/env python3
"""Check if descriptions are populated in JSON"""
import json

data = json.load(open('data/jobs_20260203.json'))
desc_count = sum(1 for j in data if len(j.get('description', '').strip()) > 20)

print(f'Total jobs: {len(data)}')
print(f'Jobs with descriptions: {desc_count}')

sample = [j for j in data if len(j.get('description', '').strip()) > 20][:2]
print(f'\nSample jobs with descriptions:')
for i, job in enumerate(sample):
    print(f'\n{i+1}. {job["title"]}')
    print(f'   Company: {job.get("company", "")}')
    print(f'   Description ({len(job["description"])} chars):')
    print(f'   {job["description"][:350]}...')
