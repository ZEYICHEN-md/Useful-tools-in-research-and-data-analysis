#!/usr/bin/env python3
"""
快速获取样本 - 使用 repo 搜索代替 code 搜索
"""
import requests
import os
import csv
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("GITHUB_TOKEN")
headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

start_date = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")

print(f"Searching for repos created after {start_date}\n")

# 使用 repo 搜索 + 关键词（更快，限制更宽松）
queries = [
    "vibe coding in:readme created:>" + start_date,
    "ai coding in:readme created:>" + start_date,
    "cursor project created:>" + start_date,
    "claude code created:>" + start_date,
]

all_repos = []

for q in queries:
    print(f"Query: {q}")
    url = "https://api.github.com/search/repositories"
    params = {"q": q, "sort": "created", "order": "desc", "per_page": 30}
    
    resp = requests.get(url, headers=headers, params=params)
    remaining = resp.headers.get("X-RateLimit-Remaining", "N/A")
    print(f"  Rate remaining: {remaining}")
    
    data = resp.json()
    items = data.get("items", [])
    print(f"  Found: {len(items)} repos\n")
    
    for repo in items:
        all_repos.append({
            "full_name": repo["full_name"],
            "html_url": repo["html_url"],
            "description": (repo.get("description") or "")[:200],
            "created_at": repo["created_at"],
            "stars": repo["stargazers_count"],
            "language": repo.get("language") or "Unknown",
            "query": q,
        })

# 去重
seen = {}
for r in all_repos:
    seen[r["full_name"]] = r

unique = list(seen.values())
print(f"="*50)
print(f"Total unique repos: {len(unique)}")

# 保存
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"sample_repos_{timestamp}.csv"

with open(filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["full_name", "html_url", "description", "created_at", "stars", "language", "query"])
    writer.writeheader()
    writer.writerows(unique)

print(f"Saved to: {filename}")
print("\nSample repos:")
for r in sorted(unique, key=lambda x: x["stars"], reverse=True)[:10]:
    print(f"  • {r['full_name']} (★{r['stars']}) - {r['language']}")
