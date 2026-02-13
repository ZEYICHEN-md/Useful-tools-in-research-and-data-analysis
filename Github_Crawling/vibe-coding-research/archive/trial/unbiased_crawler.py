#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真正无偏的 Vibe Coding 项目爬虫

核心理念：
- 不预设任何项目类型或关键词
- 抓取"所有最近创建的草根项目"
- 通过元数据排除噪音（而非通过关键词筛选目标）
- 保留完整README给DeepSeek做最终判断
"""

import requests
import json
import os
import csv
import base64
import re
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
import time
from collections import Counter

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DAYS_BACK = 14
MAX_README_LENGTH = 20000  # 20KB，足够完整README

# ========== 极简搜索策略 ==========
# 策略：用极宽泛的关键词 + 时间窗口，抓取大量项目后用元数据过滤

BROAD_QUERIES = [
    # 最宽泛的关键词，几乎涵盖所有项目
    "created:>{date}",  # 纯时间筛选，无关键词限制
    "app created:>{date}",
    "website created:>{date}",
    "tool created:>{date}",
    "script created:>{date}",
]

# ========== 噪音排除规则（关键！）==========
# 不是"找什么"，而是"不要什么"

NOISE_FILTERS = {
    # 1. 明显是大公司/官方的
    "owner_blacklist": [
        "microsoft", "google", "facebook", "meta", "amazon", "apple", "netflix",
        "twitter", "x", "openai", "anthropic", "stabilityai", "midjourney",
        "apache", "mozilla", "ibm", "oracle", "adobe", "salesforce",
        "kubernetes", "docker", "nodejs", "react", "vuejs", "angular",
    ],
    
    # 2. 项目名特征（明显是库/框架而非应用）
    "name_patterns": [
        r"^lib-", r"-lib$", r"^sdk-", r"-sdk$",
        r"^api-", r"-api$",
        r"^core-", r"-core$",
        r"^framework", r"framework$",
        r"^plugin-", r"-plugin$",
        r"^extension-", r"-extension$",
        r"^module-", r"-module$",
        r"^component-", r"-component$",
        r"^utils-", r"-utils$",
        r"^helper-", r"-helper$",
    ],
    
    # 3. 描述中的排除词
    "desc_keywords": [
        "enterprise", "corporate", "company product",
        "deprecated", "archived", "no longer maintained",
        "homework", "assignment", "course project", "final project",
        "leetcode", "algorithm practice", "coding challenge",
        "awesome list", "curated list", "collection of",
        "tutorial", "example code", "course demo",
        "config files", "dotfiles", "my settings", "backup of",
    ],
    
    # 4. Topics标签排除（明显不是应用）
    "topic_blacklist": [
        "awesome-list", "curated-list", "examples", "tutorial",
        "homework", "academic", "course",
        "deprecated", "archived",
    ],
}

# 5. 星级阈值（草根项目通常不会有太高star）
MAX_STARS = 200  # 超过这个数基本不是草根项目


class UnbiasedVibeCrawler:
    def __init__(self, token: str = ""):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
        self.stats = {
            "total_fetched": 0,
            "filtered": {
                "owner_blacklist": 0,
                "name_pattern": 0,
                "desc_keyword": 0,
                "topic_blacklist": 0,
                "high_stars": 0,
                "fork": 0,
                "empty_repo": 0,
            }
        }
        
    def _request(self, url: str, params: dict = None) -> dict:
        """带重试的请求，更短超时"""
        for attempt in range(2):  # 减少重试次数
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=15)
                if resp.status_code == 403:
                    print(" [rate limit!]", end="")
                    time.sleep(3)
                    continue
                if resp.status_code == 422:
                    return {}
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                if attempt < 1:
                    time.sleep(1)
                else:
                    print(f" [ERR:{str(e)[:20]}]", end="")
        return {}
    
    def is_noise(self, repo: dict) -> tuple:
        """
        判断是否是噪音（非草根项目）
        返回: (是否噪音, 原因)
        """
        owner = repo.get("owner", {}).get("login", "").lower()
        name = repo.get("name", "").lower()
        desc = (repo.get("description") or "").lower()
        topics = [t.lower() for t in repo.get("topics", [])]
        stars = repo.get("stargazers_count", 0)
        
        # 1. Fork的项目
        if repo.get("fork", False):
            self.stats["filtered"]["fork"] += 1
            return True, "fork"
        
        # 2. 空项目或无效项目
        if not repo.get("size", 1):
            self.stats["filtered"]["empty_repo"] += 1
            return True, "empty"
        
        # 3. 黑名单owner
        if owner in NOISE_FILTERS["owner_blacklist"]:
            self.stats["filtered"]["owner_blacklist"] += 1
            return True, f"owner_blacklist:{owner}"
        
        # 4. 项目名匹配库/框架模式
        for pattern in NOISE_FILTERS["name_patterns"]:
            if re.search(pattern, name, re.IGNORECASE):
                self.stats["filtered"]["name_pattern"] += 1
                return True, f"name_pattern:{pattern}"
        
        # 5. 描述中的排除词
        for keyword in NOISE_FILTERS["desc_keywords"]:
            if keyword in desc:
                self.stats["filtered"]["desc_keyword"] += 1
                return True, f"desc_keyword:{keyword}"
        
        # 6. Topics黑名单
        for topic in topics:
            if topic in NOISE_FILTERS["topic_blacklist"]:
                self.stats["filtered"]["topic_blacklist"] += 1
                return True, f"topic:{topic}"
        
        # 7. 星级过高
        if stars > MAX_STARS:
            self.stats["filtered"]["high_stars"] += 1
            return True, f"high_stars:{stars}"
        
        return False, ""
    
    def get_readme(self, full_name: str) -> dict:
        """获取README内容"""
        url = f"{self.base_url}/repos/{full_name}/readme"
        data = self._request(url)
        if not data or "content" not in data:
            return {"raw": "", "cleaned": "", "html_url": "", "size": 0}
        
        try:
            raw = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            
            # 清理版本（用于预览）
            cleaned = raw
            cleaned = re.sub(r'```[\s\S]*?```', '\n[CODE_BLOCK]\n', cleaned)
            cleaned = re.sub(r'`[^`]+`', '[code]', cleaned)
            cleaned = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', cleaned)
            cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
            cleaned = re.sub(r'<[^>]+>', '', cleaned)
            cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
            cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            return {
                "raw": raw[:MAX_README_LENGTH],
                "cleaned": cleaned[:MAX_README_LENGTH],
                "html_url": data.get("html_url", ""),
                "size": data.get("size", 0),
            }
        except Exception as e:
            return {"raw": "", "cleaned": "", "html_url": "", "size": 0}
    
    def fetch_repos(self, start_date: str) -> list:
        """
        抓取项目：极简关键词 + 大量结果 + 元数据过滤
        """
        print("\n" + "="*70)
        print("[Fetching Repositories - Unbiased Strategy]")
        print("="*70)
        print(f"Date range: Last {DAYS_BACK} days (from {start_date})")
        print("Strategy: Broad queries + Metadata filtering")
        
        all_repos = []
        
        for query_template in BROAD_QUERIES:
            query = query_template.format(date=start_date)
            print(f"\n[Query] {query}")
            
            url = f"{self.base_url}/search/repositories"
            page = 1
            query_total = 0
            query_kept = 0
            
            # 每个查询抓10页（1000个），完整覆盖版本
            while page <= 10:
                params = {
                    "q": query,
                    "sort": "created",  # 按创建时间
                    "order": "desc",
                    "per_page": 100,
                    "page": page
                }
                
                data = self._request(url, params)
                items = data.get("items", [])
                
                if not items:
                    break
                
                for repo in items:
                    self.stats["total_fetched"] += 1
                    
                    is_noise, reason = self.is_noise(repo)
                    if is_noise:
                        continue
                    
                    all_repos.append({
                        "repo_id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "html_url": repo["html_url"],
                        "description": (repo.get("description") or "")[:500],
                        "created_at": repo["created_at"],
                        "updated_at": repo["updated_at"],
                        "stars": repo["stargazers_count"],
                        "language": repo.get("language") or "Unknown",
                        "topics": ",".join(repo.get("topics", [])),
                        "owner_type": repo.get("owner", {}).get("type", "Unknown"),
                        "owner_login": repo.get("owner", {}).get("login", ""),
                        "size_kb": repo.get("size", 0),
                        "has_wiki": repo.get("has_wiki", False),
                        "open_issues": repo.get("open_issues_count", 0),
                        "readme_raw": "",
                        "readme_cleaned": "",
                        "readme_url": "",
                    })
                    query_kept += 1
                
                query_total += len(items)
                print(f"  Page {page}: {len(items)} fetched, {query_kept} kept so far")
                
                if len(items) < 100:
                    break
                
                page += 1
                time.sleep(0.1)  # 更快翻页
            
            print(f"  [Summary] Total: {query_total}, Kept: {query_kept}")
            time.sleep(0.5)  # 更短间隔
        
        return all_repos
    
    def deduplicate(self, repos: list) -> list:
        """去重"""
        seen = {}
        for r in repos:
            rid = r["repo_id"]
            if rid not in seen:
                seen[rid] = r
        return list(seen.values())
    
    def fetch_readmes(self, repos: list) -> list:
        """批量获取README"""
        print("\n" + "="*70)
        print(f"[Fetching READMEs for {len(repos)} repos]")
        print("="*70)
        
        success = 0
        fail = 0
        
        for idx, repo in enumerate(repos, 1):
            if idx % 50 == 1 or idx == len(repos):
                print(f"  Progress: {idx}/{len(repos)} (success: {success}, fail: {fail})")
            
            readme = self.get_readme(repo["full_name"])
            
            if readme["raw"]:
                repo["readme_raw"] = readme["raw"]
                repo["readme_cleaned"] = readme["cleaned"]
                repo["readme_url"] = readme["html_url"]
                success += 1
            else:
                fail += 1
            
            # 限速保护
            if idx % 20 == 0:
                time.sleep(1)
        
        print(f"\n  README fetched: {success}/{len(repos)} ({fail} failed)")
        return repos
    
    def save_csv(self, repos: list, filename: str):
        """保存CSV"""
        if not repos:
            print(f"[WARNING] No data for {filename}")
            return
        
        fieldnames = [
            "repo_id", "name", "full_name", "html_url", "description",
            "created_at", "updated_at", "stars", "language", "topics",
            "owner_type", "owner_login", "size_kb", "has_wiki", "open_issues",
            "readme_url", "readme_cleaned", "readme_raw",
        ]
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(repos)
        
        print(f"  Saved {len(repos)} -> {filename}")
    
    def run(self):
        """主流程"""
        print("\n" + "="*70)
        print("[Unbiased Vibe Coding Crawler]")
        print("Philosophy: Exclude noise, keep everything else")
        print("="*70)
        
        if not self.token:
            print("[ERROR] No GITHUB_TOKEN")
            return
        
        start_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
        
        # 1. 抓取项目（宽泛查询 + 元数据过滤）
        repos = self.fetch_repos(start_date)
        print(f"\n[After fetching] {len(repos)} repos")
        
        # 2. 去重
        unique = self.deduplicate(repos)
        print(f"[After dedup] {len(unique)} unique repos")
        
        # 3. 获取README
        enriched = self.fetch_readmes(unique)
        
        # 4. 分层保存（简单按star分层，不做AI判断）
        print("\n" + "="*70)
        print("[Saving Results]")
        print("="*70)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存全部
        self.save_csv(enriched, f"unbiased_all_{timestamp}.csv")
        
        # 按star分层（方便DeepSeek分批处理）
        low_star = [r for r in enriched if r["stars"] <= 10]
        mid_star = [r for r in enriched if 11 <= r["stars"] <= 50]
        high_star = [r for r in enriched if r["stars"] > 50]
        
        self.save_csv(low_star, f"unbiased_lowstar_{timestamp}.csv")
        self.save_csv(mid_star, f"unbiased_midstar_{timestamp}.csv")
        self.save_csv(high_star, f"unbiased_highstar_{timestamp}.csv")
        
        # 5. 统计
        print("\n" + "="*70)
        print("[Statistics]")
        print("="*70)
        
        print(f"\n  Total fetched: {self.stats['total_fetched']}")
        print(f"  After filtering: {len(enriched)}")
        print(f"  Filter rate: {(1 - len(enriched)/max(self.stats['total_fetched'],1))*100:.1f}%")
        
        print(f"\n  Filter breakdown:")
        for reason, count in self.stats["filtered"].items():
            if count > 0:
                print(f"    {reason:20} {count:5}")
        
        print(f"\n  Stars distribution:")
        star_ranges = {"0★": 0, "1-5★": 0, "6-10★": 0, "11-20★": 0, "21-50★": 0, "50+★": 0}
        for r in enriched:
            s = r["stars"]
            if s == 0:
                star_ranges["0★"] += 1
            elif s <= 5:
                star_ranges["1-5★"] += 1
            elif s <= 10:
                star_ranges["6-10★"] += 1
            elif s <= 20:
                star_ranges["11-20★"] += 1
            elif s <= 50:
                star_ranges["21-50★"] += 1
            else:
                star_ranges["50+★"] += 1
        
        for rng, cnt in star_ranges.items():
            bar = "█" * int(cnt / max(len(enriched)/30, 1))
            print(f"    {rng:8} {cnt:4} {bar}")
        
        print(f"\n  Language top 10:")
        langs = Counter([r["language"] for r in enriched])
        for lang, cnt in langs.most_common(10):
            print(f"    {lang}: {cnt}")
        
        print(f"\n  Owner type:")
        owners = Counter([r["owner_type"] for r in enriched])
        for ot, cnt in owners.most_common():
            print(f"    {ot}: {cnt}")
        
        print(f"\n  With README: {len([r for r in enriched if r['readme_raw']])}/{len(enriched)}")
        
        print("\n" + "="*70)
        print("[DONE] Results ready for DeepSeek classification")
        print("="*70)
        
        return enriched


def main():
    crawler = UnbiasedVibeCrawler(GITHUB_TOKEN)
    try:
        crawler.run()
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    main()
