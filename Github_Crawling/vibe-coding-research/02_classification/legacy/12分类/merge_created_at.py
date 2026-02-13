#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge created_at time into analysis results
Use repo_id as key
"""

import json
import os
import sys

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

DATASET_FILE = "vibe_coding_dataset_2w.jsonl"
ANALYSIS_FILE = "vibe_coding_analysis.jsonl"
OUTPUT_FILE = "vibe_coding_analysis_with_time.jsonl"

def load_created_at_mapping():
    """Load repo_id -> created_at mapping from dataset"""
    mapping = {}
    
    if not os.path.exists(DATASET_FILE):
        print(f"Error: File not found: {DATASET_FILE}")
        return mapping
    
    with open(DATASET_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                repo_id = data.get('id')
                created_at = data.get('created_at')
                if repo_id and created_at:
                    mapping[repo_id] = created_at
            except json.JSONDecodeError:
                continue
    
    print(f"Loaded {len(mapping)} created_at records from dataset")
    return mapping

def merge_and_save(mapping):
    """Merge and save"""
    if not os.path.exists(ANALYSIS_FILE):
        print(f"Error: File not found: {ANALYSIS_FILE}")
        return
    
    merged_count = 0
    missing_count = 0
    
    with open(ANALYSIS_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                repo_id = data.get('repo_id')
                
                if repo_id in mapping:
                    data['created_at'] = mapping[repo_id]
                    merged_count += 1
                else:
                    data['created_at'] = None
                    missing_count += 1
                
                f_out.write(json.dumps(data, ensure_ascii=False) + '\n')
                
            except json.JSONDecodeError:
                continue
    
    print(f"Merge complete:")
    print(f"  - Matched: {merged_count}")
    print(f"  - Missing: {missing_count}")
    print(f"  - Output: {OUTPUT_FILE}")

def main():
    print("=" * 50)
    print("Merge created_at into analysis results")
    print("=" * 50)
    
    mapping = load_created_at_mapping()
    if mapping:
        merge_and_save(mapping)
    
    print("=" * 50)

if __name__ == "__main__":
    main()
