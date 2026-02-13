#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Coding 项目爬虫 - 投资人研究版

核心特性：
- 按天切片爬取，确保时间覆盖均匀
- 分层抽样：区分"沉默大多数"和"高价值信号"
- 断点续传：支持中断后继续
- 全面的负向噪音过滤
- 流式落盘，每处理完一个仓库立即保存
"""

import os
import json
import re
import random
import time
import sys
from datetime import datetime, timedelta
from typing import Optional, Set, Dict, Any
from dotenv import load_dotenv
from github import Github, GithubException, RateLimitExceededException
from github.Repository import Repository

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

# ========== 配置常量 ==========
TARGET_TOTAL = 5000  # 目标仓库总数
START_DATE = datetime(2026, 1, 28)  # 从两周前开始
OUTPUT_FILE = "vibe_coding_dataset_2w.jsonl"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# 分层抽样配置
TIER1_STAR_THRESHOLD = 20  # stars <= 20 视为沉默大多数
TIER1_SAMPLE_RATE = 0.2    # 沉默大多数保留 20%

# 搜索参数
SIZE_RANGE = "50..80000"   # 50KB - 80MB
STARS_RANGE = "0..3000"    # 避免超大型机构项目
RESULTS_PER_DAY = 1000     # 每天最多获取 1000 个结果

# ========== 负向噪音关键词（综合全面版）==========
NOISE_FILTERS = {
    # 1. 教育/学习类（明显是作业或练习）
    "education_keywords": [
        "homework", "assignment", "course", "tutorial", "demo only",
        "learning", "study", "exercise", "lesson", "class project",
        "final project", "coursework", "school", "university", "college",
        "student", "assignment", "lab", "lecture", "notes",
    ],
    
    # 2. 算法/刷题类
    "algorithm_keywords": [
        "leetcode", "algorithm", "solutions", "coding challenge",
        "competitive programming", "codeforces", "atcoder",
        "interview prep", "interview questions", "dsa",
    ],
    
    # 3. 配置/备份类
    "config_keywords": [
        "deprecated", "archived", "backup", "dotfiles", "config",
        "my settings", "configuration", "personal", "dot files",
        "sync settings", "rc files", "shell config",
    ],
    
    # 4. Awesome List / 资源收集类
    "awesome_keywords": [
        "awesome list", "curated list", "collection of",
        "resources", "awesome-", ".awesome",
    ],
    
    # 5. 教程/示例代码类
    "tutorial_keywords": [
        "example code", "sample app", "starter template",
        "boilerplate", "getting started", "how to",
        "walkthrough", "guide", "intro to", "101",
    ],
    
    # 6. 明显是大公司/官方的
    "owner_blacklist": [
        "microsoft", "google", "facebook", "meta", "amazon", "apple",
        "netflix", "twitter", "x", "openai", "anthropic", "stabilityai",
        "midjourney", "apache", "mozilla", "ibm", "oracle", "adobe",
        "salesforce", "kubernetes", "docker", "nodejs", "react",
        "vuejs", "angular", "googlecloud", "azure", "aws",
    ],
    
    # 7. 项目名特征（明显是库/框架而非应用）
    "name_patterns": [
        r"^lib[-_]", r"[-_]lib$", r"^sdk[-_]", r"[-_]sdk$",
        r"^api[-_]", r"[-_]api$", r"^core[-_]", r"[-_]core$",
        r"^framework", r"framework$", r"^plugin[-_]", r"[-_]plugin$",
        r"^extension[-_]", r"[-_]extension$", r"^module[-_]", r"[-_]module$",
        r"^component[-_]", r"[-_]component$", r"^utils[-_]", r"[-_]utils$",
        r"^helper[-_]", r"[-_]helper$", r"^toolkit[-_]", r"[-_]toolkit$",
    ],
    
    # 8. 描述中的排除词（企业/官方产品）
    "desc_keywords": [
        "official", "enterprise", "corporate", "company product",
        "deprecated", "archived", "no longer maintained", "abandoned",
        "mirror of", "fork of", "cloned from",
    ],
    
    # 9. Topics标签排除
    "topic_blacklist": [
        "awesome-list", "curated-list", "examples", "tutorial",
        "homework", "academic", "course", "education",
        "deprecated", "archived", "backup", "dotfiles",
        "leetcode", "algorithm", "interview",
    ],
}

# 合并所有关键词用于快速检查
ALL_NOISE_KEYWORDS = (
    NOISE_FILTERS["education_keywords"] +
    NOISE_FILTERS["algorithm_keywords"] +
    NOISE_FILTERS["config_keywords"] +
    NOISE_FILTERS["awesome_keywords"] +
    NOISE_FILTERS["tutorial_keywords"] +
    NOISE_FILTERS["desc_keywords"]
)


class VibeCodingCrawler:
    def __init__(self, token: str):
        self.token = token
        self.github = Github(token, per_page=100)
        self.saved_ids: Set[int] = set()
        self.total_saved = 0
        self.stats = {
            "days_scanned": 0,
            "repos_scanned": 0,
            "repos_passed_filter": 0,
            "repos_sampled": 0,
            "tier1_silent": 0,
            "tier2_signal": 0,
            "readme_success": 0,
            "readme_failed": 0,
            "filtered_by": {
                "education": 0,
                "algorithm": 0,
                "config": 0,
                "awesome": 0,
                "tutorial": 0,
                "owner_blacklist": 0,
                "name_pattern": 0,
                "desc_keyword": 0,
                "topic_blacklist": 0,
                "fork": 0,
                "empty_repo": 0,
                "tier1_skip": 0,  # 分层抽样跳过的
            }
        }
        
    def load_existing_data(self) -> None:
        """加载已存在的数据，用于断点续传"""
        if not os.path.exists(OUTPUT_FILE):
            return
            
        print(f"[Resume] 发现已有数据文件: {OUTPUT_FILE}")
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    repo_id = data.get('id')
                    if repo_id:
                        self.saved_ids.add(repo_id)
                        self.total_saved += 1
                except json.JSONDecodeError:
                    continue
        
        print(f"[Resume] 已加载 {self.total_saved} 个已有仓库ID，将继续爬取...")
    
    def is_noise(self, repo: Repository) -> tuple:
        """
        判断仓库是否是噪音
        返回: (是否噪音, 原因)
        """
        owner = repo.owner.login.lower() if repo.owner else ""
        name = repo.name.lower()
        desc = (repo.description or "").lower()
        topics = [t.lower() for t in repo.get_topics()]
        
        # 1. Fork 的项目
        if repo.fork:
            self.stats["filtered_by"]["fork"] += 1
            return True, "fork"
        
        # 2. 空项目
        if repo.size == 0:
            self.stats["filtered_by"]["empty_repo"] += 1
            return True, "empty_repo"
        
        # 3. 黑名单 owner
        if owner in NOISE_FILTERS["owner_blacklist"]:
            self.stats["filtered_by"]["owner_blacklist"] += 1
            return True, f"owner_blacklist:{owner}"
        
        # 4. 项目名模式匹配
        for pattern in NOISE_FILTERS["name_patterns"]:
            if re.search(pattern, name, re.IGNORECASE):
                self.stats["filtered_by"]["name_pattern"] += 1
                return True, f"name_pattern:{pattern}"
        
        # 5. 教育/学习类关键词
        for keyword in NOISE_FILTERS["education_keywords"]:
            if keyword in desc or keyword in name:
                self.stats["filtered_by"]["education"] += 1
                return True, f"education:{keyword}"
        
        # 6. 算法/刷题类
        for keyword in NOISE_FILTERS["algorithm_keywords"]:
            if keyword in desc or keyword in name:
                self.stats["filtered_by"]["algorithm"] += 1
                return True, f"algorithm:{keyword}"
        
        # 7. 配置/备份类
        for keyword in NOISE_FILTERS["config_keywords"]:
            if keyword in desc or keyword in name:
                self.stats["filtered_by"]["config"] += 1
                return True, f"config:{keyword}"
        
        # 8. Awesome List 类
        for keyword in NOISE_FILTERS["awesome_keywords"]:
            if keyword in desc or keyword in name:
                self.stats["filtered_by"]["awesome"] += 1
                return True, f"awesome:{keyword}"
        
        # 9. 教程/示例类
        for keyword in NOISE_FILTERS["tutorial_keywords"]:
            if keyword in desc or keyword in name:
                self.stats["filtered_by"]["tutorial"] += 1
                return True, f"tutorial:{keyword}"
        
        # 10. 描述中的排除词
        for keyword in NOISE_FILTERS["desc_keywords"]:
            if keyword in desc:
                self.stats["filtered_by"]["desc_keyword"] += 1
                return True, f"desc:{keyword}"
        
        # 11. Topics 黑名单
        for topic in topics:
            if topic in NOISE_FILTERS["topic_blacklist"]:
                self.stats["filtered_by"]["topic_blacklist"] += 1
                return True, f"topic:{topic}"
        
        return False, ""
    
    def should_sample(self, stars: int) -> tuple:
        """
        分层抽样决策
        返回: (是否保留, tier级别)
        """
        if stars <= TIER1_STAR_THRESHOLD:
            # Tier 1: 沉默大多数，随机保留 20%
            if random.random() > TIER1_SAMPLE_RATE:
                self.stats["filtered_by"]["tier1_skip"] += 1
                return False, "silent"
            return True, "silent"
        else:
            # Tier 2: 高价值信号，100% 保留
            return True, "signal"
    
    def get_readme_content(self, repo: Repository) -> Optional[str]:
        """获取 README 内容，失败返回 None"""
        try:
            readme = repo.get_readme()
            content = readme.decoded_content.decode('utf-8', errors='ignore')
            return content
        except GithubException as e:
            if e.status == 404:
                return None  # 无 README
            raise  # 其他错误向上抛，由外层处理 rate limit
        except Exception:
            return None
    
    def save_repo(self, repo_data: Dict[str, Any]) -> None:
        """流式落盘：立即追加写入 JSONL"""
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            json.dump(repo_data, f, ensure_ascii=False)
            f.write('\n')
        
        self.saved_ids.add(repo_data['id'])
        self.total_saved += 1
    
    def handle_rate_limit(self, exception: RateLimitExceededException) -> None:
        """处理速率限制，计算等待时间"""
        try:
            core_rate = self.github.get_rate_limit().core
            reset_timestamp = core_rate.reset.timestamp()
            now_timestamp = datetime.now().timestamp()
            sleep_seconds = max(int(reset_timestamp - now_timestamp) + 5, 60)
        except Exception:
            sleep_seconds = 60  # 默认等待 60 秒
        
        reset_time = datetime.fromtimestamp(reset_timestamp).strftime('%H:%M:%S')
        print(f"\n[Rate Limit] 触发速率限制！将在 {sleep_seconds} 秒后继续 (reset at {reset_time})")
        time.sleep(sleep_seconds)
    
    def process_single_repo(self, repo: Repository) -> bool:
        """
        处理单个仓库
        返回: 是否成功保存
        """
        # 检查是否已存在（断点续传）
        if repo.id in self.saved_ids:
            return False
        
        self.stats["repos_scanned"] += 1
        
        # 负向关键词过滤
        is_noise, reason = self.is_noise(repo)
        if is_noise:
            return False
        
        self.stats["repos_passed_filter"] += 1
        
        # 分层抽样
        should_keep, tier = self.should_sample(repo.stargazers_count)
        if not should_keep:
            return False
        
        self.stats["repos_sampled"] += 1
        
        # 获取 README
        try:
            readme_content = self.get_readme_content(repo)
            if readme_content is not None:
                self.stats["readme_success"] += 1
            else:
                self.stats["readme_failed"] += 1
        except RateLimitExceededException as e:
            raise  # 向上抛，让外层处理
        except Exception:
            readme_content = None
            self.stats["readme_failed"] += 1
        
        # 构造数据
        repo_data = {
            "id": repo.id,
            "repo_name": repo.full_name,
            "repo_url": repo.html_url,
            "stars": repo.stargazers_count,
            "description": repo.description,
            "language": repo.language,
            "topics": repo.get_topics(),
            "created_at": repo.created_at.isoformat() if repo.created_at else None,
            "pushed_at": repo.pushed_at.isoformat() if repo.pushed_at else None,
            "tier": tier,
            "size_kb": repo.size,
            "forks_count": repo.forks_count,
            "open_issues": repo.open_issues_count,
            "owner_login": repo.owner.login if repo.owner else None,
            "owner_type": repo.owner.type if repo.owner else None,
            "readme_content": readme_content,
        }
        
        # 流式落盘
        self.save_repo(repo_data)
        
        # 更新 tier 统计
        if tier == "silent":
            self.stats["tier1_silent"] += 1
        else:
            self.stats["tier2_signal"] += 1
        
        return True
    
    def search_repos_for_day(self, date: datetime) -> int:
        """
        搜索某一天的仓库
        返回: 当天保存的数量
        """
        date_str = date.strftime('%Y-%m-%d')
        next_date_str = (date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 构造查询
        # created:YYYY-MM-DD size:50..80000 pushed:>YYYY-MM-DD stars:0..2000
        query = f"created:{date_str} size:{SIZE_RANGE} pushed:>{next_date_str} stars:{STARS_RANGE}"
        
        print(f"\n[{date_str}] 开始搜索...")
        
        day_saved = 0
        day_scanned = 0
        
        try:
            repos = self.github.search_repositories(
                query=query,
                sort='updated',
                order='desc'
            )
            
            # 遍历结果
            for repo in repos:
                # 检查总量熔断
                if self.total_saved >= TARGET_TOTAL:
                    print(f"\n[完成] 已达到目标数量 {TARGET_TOTAL}，停止爬取")
                    return day_saved
                
                try:
                    saved = self.process_single_repo(repo)
                    if saved:
                        day_saved += 1
                    day_scanned += 1
                    
                    # 进度输出
                    if day_scanned % 10 == 0:
                        print(f"  [{date_str}] 扫描: {day_scanned} | 保存: {day_saved} | 总进度: {self.total_saved}/{TARGET_TOTAL}")
                    
                    # 每处理 50 个休息一小下，避免触发限制
                    if day_scanned % 50 == 0:
                        time.sleep(0.5)
                        
                except RateLimitExceededException as e:
                    self.handle_rate_limit(e)
                    continue
                except Exception as e:
                    # 网络错误等，跳过当前仓库
                    continue
                    
        except RateLimitExceededException as e:
            self.handle_rate_limit(e)
        except Exception as e:
            print(f"  [{date_str}] 搜索出错: {e}")
        
        return day_saved
    
    def run(self) -> None:
        """主流程"""
        print("="*70)
        print("[Vibe Coding 项目爬虫 - 投资人研究版]")
        print("="*70)
        print(f"目标数量: {TARGET_TOTAL} 个仓库")
        print(f"时间范围: {START_DATE.strftime('%Y-%m-%d')} 至今天")
        print(f"分层抽样: stars <= {TIER1_STAR_THRESHOLD} 保留 {TIER1_SAMPLE_RATE*100:.0f}%")
        print(f"输出文件: {OUTPUT_FILE}")
        print("="*70)
        
        if not self.token:
            print("[错误] 未设置 GITHUB_TOKEN 环境变量")
            return
        
        # 加载已有数据（断点续传）
        self.load_existing_data()
        
        # 检查是否已完成
        if self.total_saved >= TARGET_TOTAL:
            print(f"[完成] 已存在 {self.total_saved} 个仓库，达到目标数量")
            self.print_final_stats()
            return
        
        # 按天循环
        current_date = START_DATE
        end_date = datetime.now()
        
        while current_date <= end_date and self.total_saved < TARGET_TOTAL:
            day_saved = self.search_repos_for_day(current_date)
            self.stats["days_scanned"] += 1
            
            if day_saved > 0:
                print(f"  [{current_date.strftime('%Y-%m-%d')}] 当日保存: {day_saved} 个")
            
            current_date += timedelta(days=1)
            
            # 每天搜索后休息一小下
            time.sleep(1)
        
        print("\n" + "="*70)
        print("[爬取完成]")
        print("="*70)
        self.print_final_stats()
    
    def print_final_stats(self) -> None:
        """打印最终统计"""
        print(f"\n总体统计:")
        print(f"  - 扫描天数: {self.stats['days_scanned']}")
        print(f"  - 扫描仓库: {self.stats['repos_scanned']}")
        print(f"  - 通过过滤: {self.stats['repos_passed_filter']}")
        print(f"  - 抽样保留: {self.stats['repos_sampled']}")
        print(f"  - 最终保存: {self.total_saved}")
        
        print(f"\n分层分布:")
        print(f"  - Tier 1 (沉默大多数, <=20★): {self.stats['tier1_silent']}")
        print(f"  - Tier 2 (高价值信号, >20★): {self.stats['tier2_signal']}")
        
        print(f"\nREADME 获取:")
        print(f"  - 成功: {self.stats['readme_success']}")
        print(f"  - 失败/无: {self.stats['readme_failed']}")
        
        print(f"\n过滤原因统计:")
        for reason, count in sorted(self.stats["filtered_by"].items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  - {reason}: {count}")
        
        print(f"\n输出文件: {OUTPUT_FILE}")
        print("="*70)


def main():
    crawler = VibeCodingCrawler(GITHUB_TOKEN)
    try:
        crawler.run()
    except KeyboardInterrupt:
        print("\n\n[中断] 用户手动停止")
        crawler.print_final_stats()
    except Exception as e:
        print(f"\n[错误] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
