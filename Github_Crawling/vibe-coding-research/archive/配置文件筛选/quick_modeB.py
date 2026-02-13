#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速方案 B - 只搜索几个主要配置文件
"""

import requests
import json
import os
import csv
import base64
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import quote
from dotenv import load_dotenv
import time

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DAYS_BACK = 14
MAX_README_LENGTH = 3000

# 只搜索最重要的配置文件
VIBE_CONFIG_FILES = [
    ".cursorrules",
    "CLAUDE.md", 
    "mcp.json",
    ".cursor",
    "AGENTS.md",
]

NOISE_KEYWORDS = [
    "dataset", "data set", "bug fix", "bugfix", "hotfix", "patch",
    "tutorial", "guide", "how to", "howto", "cheatsheet", "awesome-list",
]


def make_request(url, headers, params=None):
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            if response.status_code == 403:
                time.sleep(10)
                continue
            response.raise_for_status()
            return response.json()
        except:
            if attempt < 2:
                time.sleep(2)
    return {}


def get_readme(full_name, headers):
    url = f"https://api.github.com/repos/{full_name}/readme"
    data = make_request(url, headers)
    if not data or "content" not in data:
        return ""
    try:
        content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        content = re.sub(r'```[\s\S]*?```', ' [code] ', content)
        content = re.sub(r'`[^`]+`', ' [code] ', content)
        content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', content)
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        content = re.sub(r'<[^>]+>', '', content)
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()[:MAX_README_LENGTH]
    except:
        return ""


def main():
    print("="*70)
    print("[Quick Mode B] Top 5 Config Files")
    print("="*70)
    
    if not GITHUB_TOKEN:
        print("[ERROR] No GITHUB_TOKEN")
        return
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    start_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
    print(f"\nDate filter: {start_date} onwards\n")
    
    all_repos = []
    
    for idx, filename in enumerate(VIBE_CONFIG_FILES, 1):
        print(f"[{idx}/{len(VIBE_CONFIG_FILES)}] Searching: {filename}")
        
        url = "https://api.github.com/search/code"
        params = {
            "q": f"filename:{filename}",
            "sort": "indexed",
            "order": "desc",
            "per_page": 30  # 限制数量
        }
        
        data = make_request(url, headers, params)
        items = data.get("items", [])
        
        found = 0
        for item in items:
            repo = item.get("repository", {})
            
            # 检查时间
            created = repo.get("created_at", "")
            if created and created[:10] < start_date:
                continue
            
            # 检查噪音
            text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
            if any(n in text for n in NOISE_KEYWORDS):
                continue
            
            repo_info = {
                "repo_id": repo.get("id"),
                "name": repo.get("name"),
                "full_name": repo.get("full_name"),
                "html_url": repo.get("html_url"),
                "description": (repo.get("description") or "").replace("\n", " ")[:200],
                "created_at": repo.get("created_at"),
                "stars": repo.get("stargazers_count", 0),
                "language": repo.get("language") or "Unknown",
                "topics": ",".join(repo.get("topics", [])),
                "config_file": filename,
                "readme_preview": "",
                "file_url": item.get("html_url", ""),
            }
            all_repos.append(repo_info)
            found += 1
        
        print(f"  -> Found {found} recent repos")
        time.sleep(2)  # 避免 rate limit
    
    # 去重
    seen = {}
    for repo in all_repos:
        rid = repo["repo_id"]
        if rid not in seen:
            seen[rid] = repo
        else:
            seen[rid]["config_file"] += f"|{repo['config_file']}"
    
    unique_repos = list(seen.values())
    print(f"\n[Deduplicated] {len(all_repos)} -> {len(unique_repos)} unique repos")
    
    # 获取 README
    print("\n[Fetching READMEs...]")
    for idx, repo in enumerate(unique_repos, 1):
        print(f"  [{idx}/{len(unique_repos)}] {repo['full_name'][:40]}...", end=" ")
        repo["readme_preview"] = get_readme(repo["full_name"], headers)
        print("[OK]" if repo["readme_preview"] else "[--]")
        time.sleep(0.5)
    
    # 保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"modeB_quick_{timestamp}.csv"
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "repo_id", "name", "full_name", "html_url", "description",
            "created_at", "stars", "language", "topics",
            "config_file", "readme_preview", "file_url"
        ])
        writer.writeheader()
        writer.writerows(unique_repos)
    
    print(f"\n[SAVED] {filename} ({len(unique_repos)} repos)")
    
    # 统计
    from collections import Counter
    print("\n[STATISTICS]")
    print(f"  Total: {len(unique_repos)}")
    print(f"  With README: {len([r for r in unique_repos if r['readme_preview']])}")
    
    langs = Counter([r["language"] for r in unique_repos])
    print(f"\n  Languages:")
    for lang, cnt in langs.most_common(5):
        print(f"    {lang}: {cnt}")
    
    configs = []
    for r in unique_repos:
        configs.extend(r["config_file"].split("|"))
    print(f"\n  Config files:")
    for cfg, cnt in Counter(configs).most_common():
        print(f"    {cfg}: {cnt}")
    
    print(f"\n  Top starred:")
    for r in sorted(unique_repos, key=lambda x: x["stars"], reverse=True)[:5]:
        print(f"    • {r['full_name']} (★{r['stars']})")
    
    print(f"\n[TIP] Next: python deepseek_classifier.py -> select {filename}")


if __name__ == "__main__":
    main()
