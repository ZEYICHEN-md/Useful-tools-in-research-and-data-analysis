#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vibe Coding 深度分析器 - 基于 DeepSeek API

核心特性:
- 断点续传: 进度自动保存，随时中断随时恢复
- 稳健重试: 网络波动自动重试，指数退避
- 并发控制: 支持并发请求提升速度，但有速率保护
- 成本控制: 实时统计 token 使用，支持预算上限
- 双重输出: JSON + CSV 两种格式
- 实时统计: 终端显示进度、分类分布、成本估算
- 严格遵循提示词: 完全使用 LLM提示词 文件的分类逻辑

数据说明:
- 输入: vibe_coding_dataset_2w.jsonl (约 2103 个仓库)
- 实际待分析: 约 1548 个仓库 (README 非空)
- 预计成本: 约 ¥46 (按 0.03元/条计算)

作者: AI Assistant
日期: 2026-02-11
"""

import os
import json
import csv
import time
import signal
import sys
import re
from datetime import datetime
from typing import Optional, Dict, Any, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
import requests

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

# ========== 配置常量 ==========
INPUT_FILE = "vibe_coding_dataset_2w.jsonl"
OUTPUT_JSON = "vibe_coding_analysis.jsonl"
OUTPUT_CSV = "vibe_coding_analysis.csv"
PROGRESS_FILE = "analyzer_progress.json"
FAILED_FILE = "analyzer_failed.jsonl"

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"  # 可选: deepseek-chat, deepseek-reasoner

# 并发和速率控制
MAX_WORKERS = 5          # 并发线程数
REQUEST_DELAY = 0.5      # 每个请求间隔(秒)
MAX_RETRIES = 3          # 最大重试次数
RETRY_DELAY_BASE = 2     # 重试基础延迟(秒)

# 成本控制
MAX_BUDGET_CNY = 50      # 预算上限(人民币元)，约等于 500万 tokens
# DeepSeek chat 模型: 输入 1元/百万token, 输出 2元/百万token
# 平均每个请求约 2000 输入 + 500 输出 = 3分钱

# 读取提示词文件
PROMPT_FILE = "LLM提示词"


@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    # 输入数据
    repo_id: int
    repo_name: str
    repo_url: str
    stars: int
    description: Optional[str]
    language: Optional[str]
    topics: List[str]
    tier: str
    size_kb: int
    
    # 分析结果
    ai_generation_score: int
    core_intent: str
    macro_category: str
    micro_scenario: str
    complexity_level: int
    analytical_insight: str
    
    # 元数据
    analyzed_at: str
    tokens_input: int = 0
    tokens_output: int = 0
    api_cost_cny: float = 0.0
    retry_count: int = 0


class VibeCodingAnalyzer:
    """Vibe Coding 分析器主类"""
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # 统计信息
        self.stats = {
            "total": 0,              # 总仓库数
            "readme_ok": 0,          # README 有效的
            "processed": 0,          # 已处理
            "success": 0,            # 成功
            "failed": 0,             # 失败
            "skipped": 0,            # 跳过(已处理过)
            "tokens_input": 0,       # 总输入 token
            "tokens_output": 0,      # 总输出 token
            "total_cost_cny": 0.0,   # 总成本
            "start_time": None,
            "end_time": None,
        }
        
        # 分类分布统计
        self.category_stats = {
            "macro_category": {},
            "micro_scenario": {},
            "ai_generation_score": {i: 0 for i in range(1, 6)},
            "complexity_level": {i: 0 for i in range(1, 6)},
        }
        
        # 进度跟踪
        self.processed_ids: Set[int] = set()
        self.failed_ids: Set[int] = set()
        self.lock = Lock()
        self.running = True
        
        # 加载系统提示词
        self.system_prompt = self._load_system_prompt()
    
    def _load_system_prompt(self) -> str:
        """加载提示词文件"""
        try:
            if os.path.exists(PROMPT_FILE):
                with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                print(f"⚠️ 提示词文件 {PROMPT_FILE} 不存在，使用内置提示词")
                return self._get_default_prompt()
        except Exception as e:
            print(f"⚠️ 读取提示词文件失败: {e}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """使用 LLM提示词 文件中的完整内容"""
        return """你是一位深谙科技行业与风险投资趋势的数据分析师。你的任务是分析 GitHub 仓库的元数据和 README 内容，从中提炼出开发者的真实构建意图、行业落地场景以及 AI 参与编程的浓度。

请阅读提供的单个 GitHub 项目数据（JSON 格式），并严格按照以下 JSON 结构输出你的分析结果。必须输出合法的 JSON 格式，禁止包含任何额外的解释性文本。

分析维度与输出字段说明：

1. ai_generation_score (整数 1 到 5)
评估该项目借助 AI 辅助生成（Vibe Coding）的程度。注意：现代 AI 完全可以生成复杂的工程架构，因此不能单纯按代码复杂度打分，而应寻找 AI 工作流的特征。
- 1: 极低。明确的传统人工手写痕迹，缺乏任何 AI 配置文件，常规的细粒度开发记录。
- 3: 中等。混合开发，可能使用了 AI 辅助补全代码，但在系统设计和 README 编写上保留了个人定制化的人类痕迹。
- 5: 极高。具备明显的 AI 原生特征，例如：根目录包含特定的模型上下文协议文件（如 AGENTS.md, .cursorrules, CLAUDE.md, .devin, .windsurf, .mcp.json, .aider.conf.yml, .github/copilot-instructions.md）；或是直接从 Google/Vercel 等官方 AI 模板生成的项目；或是 README 具有高度标准化的机器生成语感。

2. core_intent (字符串)
用一句话（不超过 15 个字）极其精炼地概括该项目解决的核心痛点或业务逻辑。抛弃营销词汇，直击本质。例如：抓取指定网页并推送到飞书、将PDF转换为播客。

3. macro_category (字符串)
评估项目形态的宏观维度。必须从以下 3 个选项中精确选择其一：
- 个人效能与辅助工具：服务于单一用户的日常痛点，通常是脚本或自动化流程，以提升个人生产力为核心目的。偏向轻量级的提效。
- 基础设施与底层组件：服务于其他软件或系统开发，泛指各类包、框架、协议、中间件或数据库连接器，不直接面向终端非技术用户。
- 产品与系统原型：服务于多用户群体，具备完整的前后端结构或交互界面，带有产品验证性质。

4. micro_scenario (字符串)
评估项目业务场景的微观维度。必须从以下 12 个选项中精确选择其一，选择最核心的落地场景：
- productivity: 跨行业的通用效率提升，如笔记管理、日程规划、通用格式转换等。
- content_creation: 专门针对图、文、音、视等媒体形态的生成、编辑与处理。
- business_automation: 企业级或特定商业流程的自动化，如 CRM 管理、销售漏斗、客服自动回复等。
- education: 知识传授、考试辅助与技能学习场景。
- social: 人与人之间的信息交换、通讯匹配与社区连接。
- fintech: 资金流转、加密资产交易、量化脚本与金融数据分析。
- health: 医疗数据解析、健康追踪、饮食与运动管理。
- entertainment: 游戏、互动小说与纯娱乐消费场景。
- research: 学术实验、数据科学探索、爬虫采集与非商业化前沿研究。
- personal: 家庭与个人生活管理，如菜谱聚合、私人记账、智能家居物联网控制。
- ecommerce: 商品买卖、库存管理、抢票脚本与价格动态监测。
- other: 确实无法归入上述任何业务场景的极其罕见的边界案例。

5. complexity_level (整数 1 到 5)
评估该项目的业务逻辑复杂程度。1 代表极其简单的单文件脚本或纯文本配置，5 代表涉及多方 API 服务调用并具备完整状态管理和持久化存储的复杂系统。

6. analytical_insight (字符串)
站在行业分析师的角度，用简短的一两句话评价这个项目反映了当下软件开发生态中的哪种微观趋势。

必须输出合法的 JSON 格式，禁止包含任何额外的解释性文本。"""

    def load_progress(self) -> None:
        """加载进度（断点续传）"""
        if not os.path.exists(PROGRESS_FILE):
            return
        
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.processed_ids = set(data.get('processed_ids', []))
                self.failed_ids = set(data.get('failed_ids', []))
                self.stats['processed'] = len(self.processed_ids)
                self.stats['failed'] = len(self.failed_ids)
            print(f"📂 已加载进度: {len(self.processed_ids)} 个已处理, {len(self.failed_ids)} 个失败")
        except Exception as e:
            print(f"⚠️ 加载进度失败: {e}")
    
    def save_progress(self) -> None:
        """保存进度"""
        data = {
            'processed_ids': list(self.processed_ids),
            'failed_ids': list(self.failed_ids),
            'stats': self.stats,
            'category_stats': self.category_stats,
            'saved_at': datetime.now().isoformat()
        }
        try:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存进度失败: {e}")
    
    def load_repos(self) -> List[Dict]:
        """加载仓库数据，只返回 readme 不为 null 且未处理过的"""
        repos = []
        readme_null_count = 0
        already_processed = 0
        
        try:
            with open(INPUT_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        repo = json.loads(line)
                        repo_id = repo.get('id')
                        
                        # 检查是否已处理
                        if repo_id in self.processed_ids:
                            already_processed += 1
                            continue
                        
                        # 检查 README
                        readme = repo.get('readme_content')
                        if readme is None or readme == '':
                            readme_null_count += 1
                            continue
                        
                        repos.append(repo)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"❌ 错误: 输入文件 {INPUT_FILE} 不存在")
            return []
        
        self.stats['total'] = len(repos) + already_processed + readme_null_count
        self.stats['readme_ok'] = len(repos) + already_processed
        
        print(f"📊 数据加载完成:")
        print(f"   总仓库数: {self.stats['total']}")
        print(f"   README有效: {self.stats['readme_ok']} ({readme_null_count} 个为空)")
        print(f"   待处理: {len(repos)} ({already_processed} 个已处理将跳过)")
        
        return repos
    
    def _build_prompt(self, repo: Dict) -> str:
        """构建分析提示词 - 严格按照 LLM提示词 文件要求"""
        # README 截断策略：保留前 10000 字符（约 2500 tokens），足够判断 AI 特征
        readme = repo.get('readme_content', '')
        max_readme_len = 10000
        if len(readme) > max_readme_len:
            readme = readme[:max_readme_len] + "\n\n[README 已截断...]"
        
        # 构建完整的仓库数据 JSON
        repo_data = {
            "repo_name": repo.get('repo_name'),
            "repo_url": repo.get('repo_url'),
            "stars": repo.get('stars'),
            "description": repo.get('description'),
            "language": repo.get('language'),
            "topics": repo.get('topics', []),
            "tier": repo.get('tier'),
            "size_kb": repo.get('size_kb'),
            "forks_count": repo.get('forks_count'),
            "open_issues": repo.get('open_issues'),
            "created_at": repo.get('created_at'),
            "pushed_at": repo.get('pushed_at'),
            "readme_content": readme,
        }
        
        return f"请分析以下 GitHub 仓库的元数据和 README 内容，并严格按照指定 JSON 结构输出分析结果。\n\n【仓库数据】\n```json\n{json.dumps(repo_data, ensure_ascii=False, indent=2)}\n```\n\n【要求】\n1. 必须严格按照系统提示词中的 6 个维度进行分析\n2. ai_generation_score: 1-5 整数，寻找 AI 工作流特征（AGENTS.md, .cursorrules 等）\n3. core_intent: 一句话（≤15字），直击本质，抛弃营销词汇\n4. macro_category: 三选一（个人效能与辅助工具 / 基础设施与底层组件 / 产品与系统原型）\n5. micro_scenario: 十二选一（productivity/content_creation/business_automation/education/social/fintech/health/entertainment/research/personal/ecommerce/other）\n6. complexity_level: 1-5 整数，评估业务逻辑复杂度\n7. analytical_insight: 简短一两句话的行业趋势洞察\n\n只输出合法 JSON，禁止任何额外解释。"
    
    def _parse_response(self, content: str) -> Optional[Dict]:
        """解析 API 响应"""
        try:
            # 清理 markdown 代码块
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # 尝试直接解析
            result = json.loads(content)
            
            # 验证必要字段
            required_fields = [
                'ai_generation_score', 'core_intent', 'macro_category',
                'micro_scenario', 'complexity_level', 'analytical_insight'
            ]
            for field in required_fields:
                if field not in result:
                    print(f"    ⚠️ 缺少字段: {field}")
                    return None
            
            # 验证数值范围
            if not (1 <= result['ai_generation_score'] <= 5):
                result['ai_generation_score'] = max(1, min(5, result.get('ai_generation_score', 3)))
            if not (1 <= result['complexity_level'] <= 5):
                result['complexity_level'] = max(1, min(5, result.get('complexity_level', 3)))
            
            # 验证枚举值
            valid_macro = ["个人效能与辅助工具", "基础设施与底层组件", "产品与系统原型"]
            if result['macro_category'] not in valid_macro:
                result['macro_category'] = "产品与系统原型"  # 默认
            
            valid_micro = [
                "productivity", "content_creation", "business_automation",
                "education", "social", "fintech", "health", "entertainment",
                "research", "personal", "ecommerce", "other"
            ]
            if result['micro_scenario'] not in valid_micro:
                result['micro_scenario'] = "other"
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"    ⚠️ JSON 解析失败: {e}")
            return None
        except Exception as e:
            print(f"    ⚠️ 解析异常: {e}")
            return None
    
    def analyze_single(self, repo: Dict) -> Optional[AnalysisResult]:
        """分析单个仓库"""
        repo_id = repo.get('id')
        repo_name = repo.get('repo_name', 'unknown')
        
        # 检查是否已处理
        if repo_id in self.processed_ids:
            return None
        
        prompt = self._build_prompt(repo)
        
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 600,
            "response_format": {"type": "json_object"}
        }
        
        retry_count = 0
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            if not self.running:
                return None
            
            try:
                response = requests.post(
                    DEEPSEEK_API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # 获取 token 使用量
                usage = result.get("usage", {})
                tokens_input = usage.get("prompt_tokens", 0)
                tokens_output = usage.get("completion_tokens", 0)
                
                # 计算成本 (DeepSeek Chat: 输入 1元/M, 输出 2元/M)
                cost = (tokens_input * 1 + tokens_output * 2) / 1_000_000
                
                # 解析结果
                parsed = self._parse_response(content)
                if parsed is None:
                    retry_count += 1
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY_BASE * (2 ** attempt))
                        continue
                    return None
                
                # 构建结果对象
                analysis = AnalysisResult(
                    repo_id=repo_id,
                    repo_name=repo_name,
                    repo_url=repo.get('repo_url', ''),
                    stars=repo.get('stars', 0),
                    description=repo.get('description'),
                    language=repo.get('language'),
                    topics=repo.get('topics', []),
                    tier=repo.get('tier', ''),
                    size_kb=repo.get('size_kb', 0),
                    ai_generation_score=parsed['ai_generation_score'],
                    core_intent=parsed['core_intent'],
                    macro_category=parsed['macro_category'],
                    micro_scenario=parsed['micro_scenario'],
                    complexity_level=parsed['complexity_level'],
                    analytical_insight=parsed['analytical_insight'],
                    analyzed_at=datetime.now().isoformat(),
                    tokens_input=tokens_input,
                    tokens_output=tokens_output,
                    api_cost_cny=cost,
                    retry_count=retry_count
                )
                
                return analysis
                
            except requests.exceptions.RequestException as e:
                last_error = str(e)
                retry_count += 1
                if attempt < MAX_RETRIES - 1:
                    sleep_time = RETRY_DELAY_BASE * (2 ** attempt)
                    print(f"    🔄 请求失败，{sleep_time}秒后重试 ({attempt+1}/{MAX_RETRIES}): {e}")
                    time.sleep(sleep_time)
                continue
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_BASE)
                continue
        
        # 全部重试失败
        print(f"    ❌ 最终失败: {last_error}")
        self._save_failed(repo, last_error)
        return None
    
    def _save_failed(self, repo: Dict, error: str) -> None:
        """保存失败的记录"""
        with self.lock:
            self.failed_ids.add(repo.get('id'))
        
        failed_data = {
            'repo_id': repo.get('id'),
            'repo_name': repo.get('repo_name'),
            'error': error,
            'failed_at': datetime.now().isoformat()
        }
        with open(FAILED_FILE, 'a', encoding='utf-8') as f:
            json.dump(failed_data, f, ensure_ascii=False)
            f.write('\n')
    
    def _save_result(self, result: AnalysisResult) -> None:
        """保存单个结果"""
        # 保存到 JSONL
        with open(OUTPUT_JSON, 'a', encoding='utf-8') as f:
            json.dump(asdict(result), f, ensure_ascii=False)
            f.write('\n')
        
        # 保存到 CSV (追加模式)
        file_exists = os.path.exists(OUTPUT_CSV)
        with open(OUTPUT_CSV, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=asdict(result).keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(asdict(result))
        
        # 更新统计
        with self.lock:
            self.processed_ids.add(result.repo_id)
            self.stats['success'] += 1
            self.stats['tokens_input'] += result.tokens_input
            self.stats['tokens_output'] += result.tokens_output
            self.stats['total_cost_cny'] += result.api_cost_cny
            
            # 更新分类统计
            self.category_stats['macro_category'][result.macro_category] = \
                self.category_stats['macro_category'].get(result.macro_category, 0) + 1
            self.category_stats['micro_scenario'][result.micro_scenario] = \
                self.category_stats['micro_scenario'].get(result.micro_scenario, 0) + 1
            self.category_stats['ai_generation_score'][result.ai_generation_score] += 1
            self.category_stats['complexity_level'][result.complexity_level] += 1
    
    def _print_progress(self) -> None:
        """打印进度信息"""
        s = self.stats
        total_to_process = s['readme_ok'] - s['processed'] + s['success'] + s['failed']
        progress = (s['success'] + s['failed']) / total_to_process * 100 if total_to_process > 0 else 0
        
        elapsed = time.time() - s['start_time']
        rate = s['success'] / elapsed * 60 if elapsed > 0 else 0  # 每分钟处理数
        
        remaining = total_to_process - s['success'] - s['failed']
        eta_seconds = remaining / (s['success'] / elapsed) if s['success'] > 0 and elapsed > 0 else 0
        eta_minutes = int(eta_seconds / 60)
        
        # 清屏并打印
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 70)
        print("🚀 Vibe Coding 深度分析器 - DeepSeek API")
        print("=" * 70)
        print(f"📊 进度: {s['success'] + s['failed']}/{total_to_process} ({progress:.1f}%)")
        print(f"✅ 成功: {s['success']} | ❌ 失败: {s['failed']} | ⏭️ 跳过: {s['skipped']}")
        print(f"⚡ 速度: {rate:.1f} 个/分钟 | ⏱️ 预计剩余: {eta_minutes} 分钟")
        print("-" * 70)
        print(f"💰 成本统计:")
        print(f"   Token 输入: {s['tokens_input']:,} | 输出: {s['tokens_output']:,}")
        print(f"   总成本: ¥{s['total_cost_cny']:.4f} / 预算: ¥{MAX_BUDGET_CNY}")
        print("-" * 70)
        print("📈 分类分布 (宏观类别):")
        for cat, count in sorted(self.category_stats['macro_category'].items(), key=lambda x: -x[1]):
            pct = count / s['success'] * 100 if s['success'] > 0 else 0
            print(f"   {cat}: {count} ({pct:.1f}%)")
        print("-" * 70)
        print("🎯 AI 生成分数分布:")
        scores = self.category_stats['ai_generation_score']
        score_str = " | ".join([f"{i}★: {scores[i]}" for i in range(1, 6)])
        print(f"   {score_str}")
        print("=" * 70)
    
    def _signal_handler(self, signum, frame):
        """信号处理：优雅退出"""
        print("\n\n🛑 收到中断信号，正在保存进度...")
        self.running = False
        self.save_progress()
        print("✅ 进度已保存，可以安全退出")
        sys.exit(0)
    
    def run(self) -> None:
        """主运行流程"""
        # 检查 API Key
        if not self.api_key:
            print("❌ 错误: 未设置 DEEPSEEK_API_KEY 环境变量")
            print("   请在 .env 文件中添加: DEEPSEEK_API_KEY=your_key")
            return
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # 提示词来源信息
        prompt_source = f"📄 {PROMPT_FILE}" if os.path.exists(PROMPT_FILE) else "⚠️ 内置提示词(文件不存在)"
        
        print("=" * 70)
        print("🚀 Vibe Coding 深度分析器 - DeepSeek API")
        print("=" * 70)
        print(f"📁 输入文件: {INPUT_FILE}")
        print(f"💾 输出文件: {OUTPUT_JSON}, {OUTPUT_CSV}")
        print(f"🔧 并发数: {MAX_WORKERS} | 模型: {DEEPSEEK_MODEL}")
        print(f"💰 预算上限: ¥{MAX_BUDGET_CNY}")
        print(f"📝 提示词来源: {prompt_source}")
        print("=" * 70)
        
        # 加载进度和数据
        self.load_progress()
        repos = self.load_repos()
        
        if not repos:
            print("✅ 没有待处理的数据")
            return
        
        # 检查预算
        estimated_cost = len(repos) * 0.03  # 每个约 3 分钱
        print(f"💡 预计总成本: ¥{estimated_cost:.2f}")
        if estimated_cost > MAX_BUDGET_CNY:
            print(f"⚠️ 警告: 预计成本超过预算，建议调整 MAX_BUDGET_CNY 或减少处理数量")
        
        input("\n按 Enter 开始分析，或 Ctrl+C 退出...")
        
        self.stats['start_time'] = time.time()
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # 提交所有任务
            future_to_repo = {
                executor.submit(self.analyze_single, repo): repo 
                for repo in repos
            }
            
            # 处理结果
            for future in as_completed(future_to_repo):
                if not self.running:
                    break
                
                repo = future_to_repo[future]
                self.stats['processed'] += 1
                
                try:
                    result = future.result()
                    if result:
                        self._save_result(result)
                        
                        # 检查预算
                        if self.stats['total_cost_cny'] >= MAX_BUDGET_CNY:
                            print(f"\n💰 已达到预算上限 ¥{MAX_BUDGET_CNY}，停止处理")
                            self.running = False
                            break
                    else:
                        self.stats['failed'] += 1
                        
                except Exception as e:
                    print(f"    ❌ 处理异常: {e}")
                    self.stats['failed'] += 1
                
                # 每 10 个更新一次进度显示
                if self.stats['processed'] % 10 == 0:
                    self._print_progress()
                    self.save_progress()
                
                # 请求间隔
                time.sleep(REQUEST_DELAY)
        
        # 完成
        self.stats['end_time'] = time.time()
        self.save_progress()
        self._print_final_stats()
    
    def _print_final_stats(self) -> None:
        """打印最终统计"""
        s = self.stats
        elapsed = s['end_time'] - s['start_time'] if s['end_time'] else 0
        
        print("\n" + "=" * 70)
        print("🎉 分析完成!")
        print("=" * 70)
        print(f"📊 处理统计:")
        print(f"   总计: {s['success'] + s['failed']} | 成功: {s['success']} | 失败: {s['failed']}")
        print(f"⏱️  用时: {elapsed/60:.1f} 分钟 | 平均: {s['success']/(elapsed/60):.1f} 个/分钟")
        print(f"💰 总成本: ¥{s['total_cost_cny']:.4f}")
        print(f"📝 Token: 输入 {s['tokens_input']:,} | 输出 {s['tokens_output']:,}")
        print("\n📁 输出文件:")
        print(f"   JSON: {OUTPUT_JSON}")
        print(f"   CSV: {OUTPUT_CSV}")
        if os.path.exists(FAILED_FILE):
            print(f"   失败记录: {FAILED_FILE}")
        print("=" * 70)


def main():
    analyzer = VibeCodingAnalyzer()
    try:
        analyzer.run()
    except KeyboardInterrupt:
        print("\n\n🛑 用户中断")
        analyzer.save_progress()
    except Exception as e:
        print(f"\n❌ 运行时错误: {e}")
        import traceback
        traceback.print_exc()
        analyzer.save_progress()


if __name__ == "__main__":
    main()
