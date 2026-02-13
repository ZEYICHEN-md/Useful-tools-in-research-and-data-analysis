#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小白 Vibe Coders 项目爬虫

目标：抓取真正的"普通人用 AI coding agent" build 的项目
特征：
- 0-50 stars（刚创建的草根项目）
- 可能是 app / tool / website / side project
- 不依赖 README 里提到特定关键词
- 包含 README 内容供人工/AI筛选
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
MAX_README_LENGTH = 4000

# ========== 搜索策略 ==========
# 策略1：生活场景关键词（不依赖AI工具名，去AI偏见）
# 按人类真实需求分类，而非技术栈
PROJECT_KEYWORDS = [
    # === 个人/情感类 ===
    "birthday gift",
    "wedding invitation",
    "anniversary",
    "for my girlfriend",
    "for my boyfriend", 
    "for my mom",
    "for my dad",
    "love letter",
    "memory book",
    "personal diary",
    
    # === 实用工具类（细分场景）===
    "expense tracker",
    "habit tracker",
    "mood tracker",
    "sleep tracker",
    "workout log",
    "recipe app",
    "shopping list",
    "password manager",
    "url shortener",
    "qr generator",
    "pomodoro timer",
    "countdown timer",
    "calculator",
    "converter",
    "reminder app",
    "water reminder",
    
    # === 小游戏/娱乐 ===
    "wordle game",
    "tetris game",
    "snake game",
    "tic tac toe",
    "quiz game",
    "trivia game",
    "memory game",
    "puzzle game",
    "2048 game",
    "flappy bird",
    
    # === 内容展示类 ===
    "portfolio website",
    "personal blog",
    "resume site",
    "cv website",
    "wedding website",
    "event page",
    "landing page",
    "documentation site",
    
    # === 特定群体需求 ===
    "baby tracker",
    "plant care app",
    "meditation app",
    "study helper",
    "exam prep",
    "interview practice",
    "for students",
    "for teachers",
    
    # === 数据/信息类 ===
    "weather app",
    "crypto tracker",
    "stock watcher",
    "movie database",
    "book library",
    "music player",
    "playlist maker",
    "job board",
    
    # === 项目类型词（通用）===
    "my first app",
    "side project",
    "weekend project",
    "just built",
    "just made",
    "finally shipped",
    "pet project",
    "practice project",
    "learning project",
    "mvp project",
    "dashboard app",
    "chrome extension",
    "browser extension",
    "discord bot",
    "telegram bot",
    "slack bot",
    "automation script",
    "productivity app",
    "task manager",
    "note taking app",
]

# 策略2：技术栈 + 创建时间（小白常用，去AI偏见）
# 扩展更多适合新手的技术组合
TECH_COMBINATIONS = [
    # Web前端（最易上手）
    "react beginner created:>2025-02-01",
    "vue beginner created:>2025-02-01",
    "html css javascript created:>2025-02-01",
    "static website created:>2025-02-01",
    
    # 后端/脚本（AI辅助最多）
    "python automation created:>2025-02-01",
    "python beginner created:>2025-02-01",
    "flask beginner created:>2025-02-01",
    "fastapi beginner created:>2025-02-01",
    
    # 跨平台（AI生成代码友好）
    "electron app created:>2025-02-01",
    "tauri app created:>2025-02-01",
    "flutter beginner created:>2025-02-01",
    "react native beginner created:>2025-02-01",
    
    # 扩展/工具类
    "chrome extension created:>2025-02-01",
    "vscode extension created:>2025-02-01",
    "discord bot created:>2025-02-01",
    "telegram bot created:>2025-02-01",
    
    # 无代码/低代码倾向（新手友好）
    "no code created:>2025-02-01",
    "low code created:>2025-02-01",
]

# 噪音过滤（排除明显不是vibe coding的）
NOISE_KEYWORDS = [
    "official", "microsoft", "google", "facebook", "amazon",
    "enterprise", "corporate", "company",
    "deprecated", "archived", "obsolete",
    "homework", "assignment", "course project",
    "leetcode", "algorithm",
    "config", "dotfiles", "my settings",
    "awesome-list", "curated list",
    "tutorial", "example code", "demo only",
]


class VibeCodersCrawler:
    def __init__(self, token: str = ""):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
        self.all_repos = []
        
    def _request(self, url: str, params: dict = None) -> dict:
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=self.headers, params=params, timeout=30)
                if resp.status_code == 403:
                    time.sleep(5)
                    continue
                resp.raise_for_status()
                return resp.json()
            except:
                if attempt < 2:
                    time.sleep(2)
        return {}
    
    def get_readme(self, full_name: str) -> dict:
        """
        获取README内容，返回原始内容和清理后的内容
        保留两种格式供DeepSeek分类使用
        """
        url = f"{self.base_url}/repos/{full_name}/readme"
        data = self._request(url)
        if not data or "content" not in data:
            return {"raw": "", "cleaned": "", "html_url": ""}
        
        try:
            # Base64解码获取原始内容
            raw_content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            
            # 清理后的内容（用于快速预览）
            cleaned = raw_content
            # 简化代码块，但保留存在性标记
            cleaned = re.sub(r'```[\s\S]*?```', '\n[CODE_BLOCK]\n', cleaned)
            cleaned = re.sub(r'`[^`]+`', '[code]', cleaned)
            # 移除图片
            cleaned = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', cleaned)
            # 简化链接，保留文本
            cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)
            # 移除HTML标签
            cleaned = re.sub(r'<[^>]+>', '', cleaned)
            # 简化格式标记
            cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
            cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
            # 规范化空白
            cleaned = re.sub(r'\s+', ' ', cleaned)
            cleaned = cleaned.strip()
            
            return {
                "raw": raw_content[:MAX_README_LENGTH],  # 原始内容（截断）
                "cleaned": cleaned[:MAX_README_LENGTH],  # 清理后内容（截断）
                "html_url": data.get("html_url", ""),
                "size": data.get("size", 0),
            }
        except Exception as e:
            print(f"[ERROR] Failed to decode README for {full_name}: {e}")
            return {"raw": "", "cleaned": "", "html_url": ""}
    
    def is_noise(self, repo: dict) -> bool:
        """噪音检测"""
        text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
        for noise in NOISE_KEYWORDS:
            if noise.lower() in text:
                return True
        # 排除组织账号（通常不是个人vibe coding）
        if repo.get('owner', {}).get('type') == 'Organization':
            # 但保留小组织
            pass
        return False
    
    def search_by_keywords(self, start_date: str) -> list:
        """策略1：项目关键词搜索"""
        print("\n" + "="*70)
        print("[Strategy 1] Project Type Keywords")
        print("="*70)
        
        repos = []
        
        for idx, keyword in enumerate(PROJECT_KEYWORDS, 1):
            print(f"\n[{idx}/{len(PROJECT_KEYWORDS)}] '{keyword}'")
            
            query = f'{keyword} created:>{start_date}'
            url = f"{self.base_url}/search/repositories"
            
            page = 1
            found = 0
            filtered = 0
            
            while page <= 2:  # 每关键词最多200个
                params = {
                    "q": query,
                    "sort": "created",  # 按创建时间，不是stars！
                    "order": "desc",
                    "per_page": 100,
                    "page": page
                }
                
                data = self._request(url, params)
                items = data.get("items", [])
                
                if not items:
                    break
                
                for repo in items:
                    # 噪音过滤
                    if self.is_noise(repo):
                        filtered += 1
                        continue
                    
                    repos.append({
                        "repo_id": repo["id"],
                        "name": repo["name"],
                        "full_name": repo["full_name"],
                        "html_url": repo["html_url"],
                        "description": (repo.get("description") or "")[:500],  # 增加描述长度
                        "created_at": repo["created_at"],
                        "updated_at": repo["updated_at"],
                        "stars": repo["stargazers_count"],
                        "language": repo.get("language") or "Unknown",
                        "topics": ",".join(repo.get("topics", [])),
                        "owner_type": repo.get("owner", {}).get("type", "Unknown"),
                        "owner_login": repo.get("owner", {}).get("login", ""),
                        "source_keyword": keyword,
                        "readme_raw": "",           # 原始README（完整）
                        "readme_cleaned": "",       # 清理后README（用于预览）
                        "readme_url": "",           # README文件URL
                    })
                    found += 1
                
                if len(items) < 100:
                    break
                page += 1
                time.sleep(0.5)
            
            print(f"  -> Found {found} (filtered {filtered})")
        
        return repos
    
    def search_by_tech(self, start_date: str) -> list:
        """策略2：技术栈组合搜索"""
        print("\n" + "="*70)
        print("[Strategy 2] Tech Stack Combinations")
        print("="*70)
        
        repos = []
        
        for idx, query in enumerate(TECH_COMBINATIONS, 1):
            print(f"\n[{idx}/{len(TECH_COMBINATIONS)}] '{query}'")
            
            url = f"{self.base_url}/search/repositories"
            
            found = 0
            filtered = 0
            
            # 只取前100个（避免太多）
            params = {
                "q": query.replace("2025-02-01", start_date),
                "sort": "created",
                "order": "desc",
                "per_page": 100,
                "page": 1
            }
            
            data = self._request(url, params)
            items = data.get("items", [])
            
            for repo in items:
                if self.is_noise(repo):
                    filtered += 1
                    continue
                
                repos.append({
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
                    "source_keyword": query.split()[0],
                    "readme_raw": "",
                    "readme_cleaned": "",
                    "readme_url": "",
                })
                found += 1
            
            print(f"  -> Found {found} (filtered {filtered})")
            time.sleep(0.5)
        
        return repos
    
    def fetch_readmes(self, repos: list) -> list:
        """批量获取README，保留原始和清理后两种格式"""
        print("\n" + "="*70)
        print("[Fetching READMEs]")
        print("="*70)
        
        success_count = 0
        fail_count = 0
        
        for idx, repo in enumerate(repos, 1):
            print(f"  [{idx}/{len(repos)}] {repo['full_name'][:45]:45} ", end="", flush=True)
            
            readme_data = self.get_readme(repo["full_name"])
            
            if readme_data["raw"]:
                repo["readme_raw"] = readme_data["raw"]
                repo["readme_cleaned"] = readme_data["cleaned"]
                repo["readme_url"] = readme_data["html_url"]
                success_count += 1
                # 显示README大小
                size_kb = len(readme_data["raw"]) / 1024
                print(f"[OK] {size_kb:.1f}KB")
            else:
                fail_count += 1
                print("[--]")
            
            # 每10个休息下，避免触发限流
            if idx % 10 == 0:
                time.sleep(1)
        
        print(f"\n  README fetched: {success_count}/{len(repos)} ({fail_count} failed)")
        return repos
    
    def deduplicate(self, repos: list) -> list:
        """去重"""
        seen = {}
        for r in repos:
            rid = r["repo_id"]
            if rid not in seen:
                seen[rid] = r
            else:
                seen[rid]["source_keyword"] += f"|{r['source_keyword']}"
        return list(seen.values())
    
    def detect_readme_style(self, readme: str) -> dict:
        """
        检测README写作风格是否像AI生成
        不依赖关键词匹配，而是看写作特征
        """
        if not readme or len(readme) < 50:
            return {"is_ai_like": False, "confidence": 0}
        
        text_lower = readme.lower()
        signals = []
        score = 0
        
        # 信号1：过度结构化的标题（## Features, ## Installation）
        if re.search(r'##\s+(features|installation|getting started|tech stack)', text_lower):
            signals.append("structured")
            score += 15
        
        # 信号2：AI常用词汇
        ai_words = ["leverage", "seamlessly", "robust", "empower", "utilize"]
        if any(w in text_lower for w in ai_words):
            signals.append("ai_words")
            score += 10
        
        # 信号3：标题emoji（AI喜欢在标题加emoji）
        if re.search(r'^##?\s+[\U0001F300-\U0001F9FF]', readme, re.MULTILINE):
            signals.append("emoji_headers")
            score += 10
        
        # 信号4：完美列表格式（AI生成的通常很规整）
        if re.search(r'##\s+\w+\s*\n+(?:-\s+.+\n+){3,}', readme):
            signals.append("perfect_list")
            score += 10
        
        # 信号5：包含shields.io徽章
        if "shields.io" in readme or ("![" in readme and "github.com" in readme):
            signals.append("badges")
            score += 8
        
        # 信号6：明确提到AI工具（最强信号）
        ai_tools = ["cursor", "claude", "copilot", "gpt", "chatgpt", "ai generated", "cursorrules"]
        if any(t in text_lower for t in ai_tools):
            signals.append("mentions_ai")
            score += 30
        
        # 信号7：README篇幅（AI生成的通常完整但不太长）
        word_count = len(readme.split())
        if 150 < word_count < 1000:
            score += 10
        
        is_ai_like = score >= 35
        confidence = min(score / 60, 1.0)
        
        return {
            "is_ai_like": is_ai_like,
            "confidence": round(confidence, 2),
            "signals": signals,
            "word_count": word_count
        }
    
    def classify_project_type(self, repo: dict) -> str:
        """自动分类项目类型/场景"""
        text = f"{repo.get('name', '')} {repo.get('description', '')}".lower()
        
        categories = {
            "个人/情感": ["birthday", "wedding", "anniversary", "girlfriend", "boyfriend", 
                       "mom", "dad", "love", "gift", "memory", "diary"],
            "实用工具": ["tracker", "calculator", "converter", "manager", "reminder",
                       "password", "url", "qr", "timer", "scheduler"],
            "游戏娱乐": ["game", "quiz", "puzzle", "wordle", "tetris", "snake", "fun"],
            "内容展示": ["portfolio", "blog", "resume", "cv", "landing", "website", "docs"],
            "学习教育": ["study", "exam", "learn", "practice", "flashcard", "quiz"],
            "生活助手": ["recipe", "shopping", "habit", "mood", "sleep", "workout", 
                       "plant", "meditation", "baby", "water"],
            "数据信息": ["weather", "crypto", "stock", "movie", "book", "music", "job"],
            "社交沟通": ["chat", "bot", "discord", "telegram", "slack"],
        }
        
        scores = {}
        for cat, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[cat] = score
        
        if scores:
            return max(scores, key=scores.get)
        return "其他"
    
    def filter_vibe_coding_candidates(self, repos: list) -> tuple:
        """
        筛选可能是vibe coding的项目
        使用 readme_raw 进行风格检测（更完整的信号）
        返回: (高可能性, 中等可能性, 全部)
        """
        high = []
        medium = []
        
        for r in repos:
            # 分析README风格（使用原始内容，保留更多信号）
            style = self.detect_readme_style(r.get("readme_raw", ""))
            r["readme_style"] = style
            # 项目类型只做简单标记，详细分类留给DeepSeek
            r["project_type"] = self.classify_project_type(r)
            
            # 高可能性：README风格像AI生成
            if style["is_ai_like"]:
                r["ai_likelihood"] = "high"
                high.append(r)
            # 中等可能性：草根项目特征
            elif r["stars"] < 30 and r["owner_type"] == "User":
                if r["readme_raw"] and len(r["readme_raw"]) > 100:
                    r["ai_likelihood"] = "medium"
                    medium.append(r)
                else:
                    r["ai_likelihood"] = "low"
                    medium.append(r)
            else:
                r["ai_likelihood"] = "low"
                medium.append(r)
        
        return high, medium, repos
    
    def save_csv(self, repos: list, filename: str):
        """保存CSV"""
        if not repos:
            print(f"[WARNING] No data for {filename}")
            return
        
        # 展平嵌套字段
        flat_repos = []
        for r in repos:
            flat_r = dict(r)
            # 处理readme_style
            style = flat_r.pop("readme_style", {})
            flat_r["ai_style"] = style.get("is_ai_like", False)
            flat_r["ai_confidence"] = style.get("confidence", 0)
            flat_r["ai_signals"] = ",".join(style.get("signals", []))
            flat_r["readme_words"] = style.get("word_count", 0)
            # 保留project_type
            flat_r["project_type"] = flat_r.get("project_type", "其他")
            flat_r["ai_likelihood"] = flat_r.get("ai_likelihood", "unknown")
            flat_repos.append(flat_r)
        
        fieldnames = [
            "repo_id", "name", "full_name", "html_url", "description",
            "created_at", "updated_at", "stars", "language", "topics",
            "owner_type", "owner_login", "source_keyword", "project_type",
            "ai_likelihood", "ai_style", "ai_confidence", "ai_signals", "readme_words",
            "readme_url",      # README文件链接
            "readme_cleaned",  # 清理后的README（适合预览）
            "readme_raw",      # 原始README（适合DeepSeek分析）
        ]
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_repos)
        
        print(f"  Saved {len(repos)} -> {filename}")
    
    def run(self):
        """主流程"""
        print("\n" + "="*70)
        print("[Vibe Coders Crawler]")
        print("Target: Grassroots projects built by ordinary people with AI")
        print("="*70)
        
        if not self.token:
            print("[ERROR] No GITHUB_TOKEN")
            return
        
        start_date = (datetime.now() - timedelta(days=DAYS_BACK)).strftime("%Y-%m-%d")
        print(f"\nDate range: Last {DAYS_BACK} days (from {start_date})")
        
        # 搜索
        repos_a = self.search_by_keywords(start_date)
        repos_b = self.search_by_tech(start_date)
        
        # 合并
        all_repos = repos_a + repos_b
        print(f"\n[Before dedup] {len(all_repos)} repos")
        
        unique = self.deduplicate(all_repos)
        print(f"[After dedup] {len(unique)} repos")
        
        # 获取README
        enriched = self.fetch_readmes(unique)
        
        # 筛选vibe coding候选
        high, medium, all_data = self.filter_vibe_coding_candidates(enriched)
        
        # 保存
        print("\n" + "="*70)
        print("[Saving Results]")
        print("="*70)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.save_csv(all_data, f"vibe_coders_all_{timestamp}.csv")
        self.save_csv(high, f"vibe_coders_high_prob_{timestamp}.csv")
        self.save_csv(medium, f"vibe_coders_medium_prob_{timestamp}.csv")
        
        # 统计
        print("\n" + "="*70)
        print("[Statistics]")
        print("="*70)
        
        print(f"\n  Total unique repos: {len(all_data)}")
        print(f"  High probability (AI-style README): {len(high)}")
        print(f"  Medium probability: {len(medium)}")
        print(f"  With README: {len([r for r in all_data if r['readme_raw']])}")
        
        # Stars分布（更细致）
        star_ranges = {"0★": 0, "1-5★": 0, "6-10★": 0, "11-20★": 0, "21-50★": 0, "50+★": 0}
        for r in all_data:
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
        
        print(f"\n  Stars distribution:")
        for rng, cnt in star_ranges.items():
            bar = "█" * int(cnt / max(len(all_data)/50, 1))
            print(f"    {rng:8} {cnt:4} {bar}")
        
        # 项目类型分布（核心指标）
        print(f"\n  Project Type Distribution:")
        types = Counter([r.get("project_type", "其他") for r in all_data])
        for ptype, cnt in types.most_common():
            pct = cnt / len(all_data) * 100
            bar = "█" * int(pct / 2)
            print(f"    {ptype:12} {cnt:4} ({pct:5.1f}%) {bar}")
        
        # AI风格 vs 项目类型交叉分析
        print(f"\n  AI-style README by Project Type:")
        ai_by_type = Counter([r.get("project_type", "其他") for r in high])
        for ptype, cnt in ai_by_type.most_common(5):
            total = types.get(ptype, 1)
            pct = cnt / total * 100
            print(f"    {ptype:12} {cnt:4}/{total:4} ({pct:5.1f}%)")
        
        # 语言分布
        print(f"\n  Language top 5:")
        langs = Counter([r["language"] for r in all_data])
        for lang, cnt in langs.most_common(5):
            print(f"    {lang}: {cnt}")
        
        # 展示一些有代表性的项目
        print(f"\n  Sample projects (AI-style + low stars):")
        samples = [r for r in high if r["stars"] <= 20][:10]
        for r in samples:
            ptype = r.get("project_type", "其他")
            print(f"    • {r['full_name'][:45]:45} ★{r['stars']:3} | {ptype:12}")
            if r["description"]:
                desc = r["description"][:50].encode('ascii', 'ignore').decode('ascii')
                print(f"      {desc}...")
        
        print("\n" + "="*70)
        print("[DONE]")
        print("="*70)
        
        return all_data


def main():
    crawler = VibeCodersCrawler(GITHUB_TOKEN)
    try:
        crawler.run()
    except KeyboardInterrupt:
        print("\n\n[Interrupted]")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
