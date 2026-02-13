#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方案 B 单独运行版本 - 只搜索配置文件（高置信度）
运行更快，专注于确定的 vibe coding 项目
"""

import requests
import json
import os
import csv
import base64
import re
import sys
from datetime import datetime, timedelta

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')
from urllib.parse import quote
from dotenv import load_dotenv
import time

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DAYS_BACK = 14
MAX_README_LENGTH = 3000

# 高置信度配置文件列表
VIBE_CONFIG_FILES = [
    "CLAUDE.md", "claude.md",
    "AGENTS.md", "agents.md",
    "GEMINI.md", "gemini.md",
    ".cursor", ".cursorrules", ".cursorignore",
    ".clinerules", ".clineignore",
    "mcp.json", "mcp.yaml", "mcp.yml", ".mcp.json",
    ".aider.conf.yml", ".aiderignore", "aider.md", "CONVENTIONS.md",
    ".github/copilot-instructions.md",
    ".windsurf", ".windsurfrules",
    ".devin", "devin.md",
    "ai-instructions.md", "ai-rules.md",
]

# 噪音过滤
NOISE_KEYWORDS = [
    "dataset", "data set", "bug fix", "bugfix", "hotfix", "patch",
    "tutorial", "guide", "how to", "howto", "cheatsheet", "awesome-list",
    "curated list", "examples", "template", "boilerplate only",
    "config files", "dotfiles", "leetcode", "algorithm", "homework",
    "test repo", "draft", "work in progress", "wip", "deprecated", "archive",
]


class ModeBCrawler:
    def __init__(self, token: str = ""):
        self.token = token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "VibeCodingModeB/1.0"
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        
        self.base_url = "https://api.github.com"
        
    def _make_request(self, url: str, params: dict = None) -> dict:
        """发送请求带重试"""
        for attempt in range(3):
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=30)
                
                if response.status_code == 403 and "rate limit" in response.text.lower():
                    reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                    wait_time = max(reset_time - int(time.time()), 0) + 5
                    print(f"    ⏳ 速率限制，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except Exception as e:
                if attempt < 2:
                    time.sleep((attempt + 1) * 2)
                else:
                    return {}
        return {}
    
    def get_date_range(self) -> str:
        """获取开始日期"""
        start_date = datetime.now() - timedelta(days=DAYS_BACK)
        return start_date.strftime("%Y-%m-%d")
    
    def is_noise_repo(self, repo: dict) -> bool:
        """噪音过滤"""
        text = " ".join(filter(None, [
            repo.get("name", ""),
            repo.get("description", ""),
        ])).lower()
        
        for noise in NOISE_KEYWORDS:
            if noise.lower() in text:
                return True
        
        if repo.get("fork", False):
            return True
            
        return False
    
    def get_readme(self, full_name: str) -> str:
        """获取 README"""
        url = f"{self.base_url}/repos/{full_name}/readme"
        data = self._make_request(url)
        
        if not data or "content" not in data:
            return ""
        
        try:
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            # 清理 markdown
            content = re.sub(r'```[\s\S]*?```', ' [code] ', content)
            content = re.sub(r'`[^`]+`', ' [code] ', content)
            content = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', content)
            content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
            content = re.sub(r'\*([^*]+)\*', r'\1', content)
            content = re.sub(r'\s+', ' ', content)
            return content.strip()[:MAX_README_LENGTH]
        except:
            return ""
    
    def search_by_configs(self, start_date: str) -> list:
        """搜索包含配置文件的仓库"""
        print("\n" + "="*70)
        print("[Mode B] Searching Vibe Coding Config Files")
        print("="*70)
        print(f"   Searching {len(VIBE_CONFIG_FILES)} config files")
        print(f"   Date range: {start_date} to now")
        
        all_repos = []
        
        for idx, filename in enumerate(VIBE_CONFIG_FILES, 1):
            print(f"\n[{idx:2d}/{len(VIBE_CONFIG_FILES)}] Searching: {filename}")
            
            query = f'filename:{quote(filename)} created:>{start_date}'
            url = f"{self.base_url}/search/code"
            
            page = 1
            file_repos = []
            seen_repos = set()
            filtered = 0
            
            while page <= 10:
                params = {
                    "q": query,
                    "sort": "indexed",
                    "order": "desc",
                    "per_page": 100,
                    "page": page
                }
                
                data = self._make_request(url, params)
                items = data.get("items", [])
                
                if not items:
                    break
                
                for item in items:
                    repo = item.get("repository", {})
                    repo_name = repo.get("full_name")
                    
                    if repo_name in seen_repos:
                        continue
                    seen_repos.add(repo_name)
                    
                    # 检查时间
                    created = repo.get("created_at", "")
                    if created and created[:10] < start_date:
                        continue
                    
                    # 噪音过滤
                    if self.is_noise_repo(repo):
                        filtered += 1
                        continue
                    
                    repo_info = {
                        "repo_id": repo.get("id"),
                        "name": repo.get("name"),
                        "full_name": repo_name,
                        "html_url": repo.get("html_url"),
                        "description": (repo.get("description") or "").replace("\n", " "),
                        "created_at": repo.get("created_at"),
                        "updated_at": repo.get("updated_at"),
                        "stars": repo.get("stargazers_count", 0),
                        "language": repo.get("language") or "Unknown",
                        "topics": ",".join(repo.get("topics", [])),
                        "config_file": filename,
                        "file_url": item.get("html_url", ""),
                    }
                    file_repos.append(repo_info)
                
                if len(items) < 100:
                    break
                
                page += 1
                time.sleep(0.3)
            
            status = "✓" if file_repos else "○"
            print(f"  {status} Found {len(file_repos):3d} repos (filtered {filtered} noise)")
            all_repos.extend(file_repos)
            time.sleep(0.5)
        
        return all_repos
    
    def enrich_with_readme(self, repos: list) -> list:
        """获取 README"""
        print("\n" + "="*70)
        print("[Fetching README content]")
        print("="*70)
        
        for idx, repo in enumerate(repos, 1):
            full_name = repo["full_name"]
            print(f"  [{idx:3d}/{len(repos)}] {full_name[:50]:50} ", end="", flush=True)
            
            readme = self.get_readme(full_name)
            repo["readme_preview"] = readme
            
            status = "[OK]" if readme else "[--]"
            print(status)
            
            # 每5个休息一下
            if idx % 5 == 0:
                time.sleep(0.5)
        
        return repos
    
    def deduplicate(self, repos: list) -> list:
        """去重，合并配置信息"""
        seen = {}
        
        for repo in repos:
            repo_id = repo["repo_id"]
            if repo_id not in seen:
                seen[repo_id] = repo
            else:
                # 合并配置信息
                existing = seen[repo_id]
                existing["config_file"] += f"|{repo['config_file']}"
        
        return list(seen.values())
    
    def save_csv(self, repos: list, filename: str):
        """保存 CSV"""
        if not repos:
            print(f"⚠️ 没有数据")
            return
        
        fieldnames = [
            "repo_id", "name", "full_name", "html_url", "description",
            "created_at", "updated_at", "stars", "language", "topics",
            "config_file", "readme_preview", "file_url"
        ]
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(repos)
        
        print(f"  Saved {len(repos)} records to {filename}")
    
    def run(self):
        """运行方案 B"""
        print("\n" + "="*70)
        print("[Mode B] Vibe Coding High Confidence Projects")
        print("="*70)
        
        if not self.token:
            print("\n[ERROR] GITHUB_TOKEN not found")
            return None
        
        start_date = self.get_date_range()
        print(f"\n[Date Range] Last {DAYS_BACK} days")
        print(f"   Start: {start_date}")
        
        # 搜索
        repos = self.search_by_configs(start_date)
        
        # 去重
        print("\n🔄 去重中...")
        unique_repos = self.deduplicate(repos)
        print(f"   原始: {len(repos)}, 去重后: {len(unique_repos)}")
        
        # 获取 README
        enriched = self.enrich_with_readme(unique_repos)
        
        # 保存
        print("\n" + "="*70)
        print("[Saving results]")
        print("="*70)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"modeB_highconf_{timestamp}.csv"
        self.save_csv(enriched, filename)
        
        # 统计
        from collections import Counter
        
        print("\n" + "="*70)
        print("[Statistics]")
        print("="*70)
        
        print(f"\n  Total repos: {len(enriched)}")
        print(f"  With README: {len([r for r in enriched if r.get('readme_preview')])}")
        
        # 语言分布
        langs = Counter([r["language"] for r in enriched])
        print(f"\n  [Language Top 5]")
        for lang, count in langs.most_common(5):
            print(f"     {lang}: {count}")
        
        # 配置文件分布
        configs = []
        for r in enriched:
            configs.extend(r["config_file"].split("|"))
        config_counter = Counter(configs)
        
        print(f"\n  [Config File Top 5]")
        for cfg, count in config_counter.most_common(5):
            print(f"     {cfg}: {count}")
        
        # 预览
        print(f"\n  [Top Starred Repos]")
        for repo in sorted(enriched, key=lambda x: x["stars"], reverse=True)[:5]:
            print(f"     • {repo['full_name']} Stars:{repo['stars']}")
            if repo['description']:
                print(f"       {repo['description'][:60]}...")
        
        print("\n" + "="*70)
        print(f"[DONE] File: {filename}")
        print("="*70)
        
        return filename, enriched


def main():
    crawler = ModeBCrawler(GITHUB_TOKEN)
    try:
        result = crawler.run()
        if result:
            filename, repos = result
            print(f"\n[TIP] Run 'python deepseek_classifier.py' to classify {filename}")
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
