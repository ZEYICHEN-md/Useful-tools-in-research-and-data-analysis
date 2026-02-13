#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用新的8分类体系重新分析 Vibe Coding 项目

新分类体系:
1. enterprise_business - 企业商业应用
2. productivity_tools - 效率工具  
3. tech_infrastructure - 技术基础设施
4. entertainment_media - 娱乐媒体
5. education_learning - 教育学习
6. social_community - 社交社区
7. health_wellness - 健康医疗
8. personal_life - 个人生活

作者: AI Assistant
日期: 2026-02-11
"""

import os
import json
import time
import sys
from datetime import datetime
from typing import Optional, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from dotenv import load_dotenv
import requests

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

# ========== 配置常量 ==========
INPUT_FILE = "vibe_coding_dataset_2w.jsonl"
OUTPUT_JSON = "vibe_coding_analysis_8categories.jsonl"
OUTPUT_CSV = "vibe_coding_analysis_8categories.csv"
PROGRESS_FILE = "analyzer_progress_8cat.json"
FAILED_FILE = "analyzer_failed_8cat.jsonl"

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# 并发和速率控制
MAX_WORKERS = 5
REQUEST_DELAY = 0.5
MAX_RETRIES = 3
RETRY_DELAY_BASE = 2

# 成本控制
MAX_BUDGET_CNY = 50

# 新的系统提示词
SYSTEM_PROMPT = """你是一位深谙科技行业与风险投资趋势的数据分析师。你的任务是分析 GitHub 仓库的元数据和 README 内容，从中提炼出开发者的真实构建意图、行业落地场景以及 AI 参与编程的浓度。

请阅读提供的单个 GitHub 项目数据（JSON 格式），并严格按照以下 JSON 结构输出你的分析结果。必须输出合法的 JSON 格式，禁止包含任何额外的解释性文本。

分析维度与输出字段说明：

1. ai_generation_score (整数 1 到 5)
评估该项目借助 AI 辅助生成（Vibe Coding）的程度。
- 1: 极低。明确的传统人工手写痕迹，缺乏任何 AI 配置文件。
- 3: 中等。混合开发，可能使用了 AI 辅助补全代码。
- 5: 极高。具备明显的 AI 原生特征，如 AGENTS.md, .cursorrules 文件，或官方 AI 模板生成的项目。

2. core_intent (字符串)
用一句话（不超过 15 个字）极其精炼地概括该项目解决的核心痛点或业务逻辑。

3. macro_category (字符串)
必须从以下 3 个选项中精确选择其一：
- 个人效能与辅助工具
- 基础设施与底层组件  
- 产品与系统原型

4. micro_scenario (字符串)
必须从以下 8 个选项中精确选择其一：

- enterprise_business: 企业商业应用。商业流程自动化、电商、金融科技、CRM、ERP、企业管理系统。
  示例：洗车店管理、机场航班系统、餐厅外卖、房产租赁、投资可视化、支付网关

- productivity_tools: 效率工具。个人/团队效率、开发者工具、内容创作工具、模板/脚手架。
  示例：在线编译器、电子表格、AI工作空间、视频特效、CMS、Next.js模板

- tech_infrastructure: 技术基础设施。技术研究、原型验证、系统工具、硬件/IoT、操作系统、网络协议。
  示例：CRUD生成器、基因分析、多智能体框架、Web原型、固件、嵌入式系统

- entertainment_media: 娱乐媒体。游戏、娱乐消费、媒体播放、内容消费。
  示例：符号匹配游戏、VR可视化、IPTV播放器、漫画阅读器

- education_learning: 教育学习。教育平台、学习工具、知识传授、技能提升。
  示例：在线教育平台、闪卡应用、课程材料、编程学习工具

- social_community: 社交社区。社交应用、社区平台、通讯工具、约会匹配、论坛。
  示例：聊天机器人、新闻社交API、社团网站、约会匹配

- health_wellness: 健康医疗。医疗应用、健康追踪、wellness、心理健康、健身管理。
  示例：AI兽医平台、患者药房连接、AI心理日记、医疗病历

- personal_life: 个人生活。个人生活管理、作品集展示、家庭管理、个人品牌、生活助手。
  示例：电影清单、作品集网站、家庭家务管理、个人食谱

5. complexity_level (整数 1 到 5)
1 代表极其简单的单文件脚本，5 代表涉及多方 API 和完整状态管理的复杂系统。

6. analytical_insight (字符串)
用简短的一两句话评价这个项目反映了当下软件开发生态中的哪种微观趋势。

必须输出合法的 JSON 格式，禁止包含任何额外的解释性文本。"""


class VibeCodingAnalyzer8Cat:
    """Vibe Coding 8分类分析器"""
    
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        self.stats = {
            "total": 0,
            "readme_ok": 0,
            "processed": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "tokens_input": 0,
            "tokens_output": 0,
            "total_cost_cny": 0.0,
            "start_time": None,
            "end_time": None,
        }
        
        self.category_stats = {
            "micro_scenario": {},
            "ai_generation_score": {i: 0 for i in range(1, 6)},
        }
        
        self.processed_ids: Set[int] = set()
        self.failed_ids: Set[int] = set()
        self.lock = Lock()
        self.running = True
    
    def load_progress(self) -> None:
        """加载进度"""
        if os.path.exists(PROGRESS_FILE):
            try:
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get("processed_ids", []))
                    self.failed_ids = set(data.get("failed_ids", []))
                    self.stats["tokens_input"] = data.get("tokens_input", 0)
                    self.stats["tokens_output"] = data.get("tokens_output", 0)
                    self.stats["total_cost_cny"] = data.get("total_cost_cny", 0.0)
                    print(f"📂 已加载进度: {len(self.processed_ids)} 已处理, {len(self.failed_ids)} 失败")
            except Exception as e:
                print(f"⚠️ 加载进度失败: {e}")
    
    def save_progress(self) -> None:
        """保存进度"""
        data = {
            "processed_ids": list(self.processed_ids),
            "failed_ids": list(self.failed_ids),
            "tokens_input": self.stats["tokens_input"],
            "tokens_output": self.stats["tokens_output"],
            "total_cost_cny": self.stats["total_cost_cny"],
            "last_update": datetime.now().isoformat()
        }
        try:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 保存进度失败: {e}")
    
    def analyze_project(self, repo: dict) -> Optional[dict]:
        """使用 DeepSeek API 分析单个项目"""
        if not self.api_key:
            print("❌ 错误: 未设置 DEEPSEEK_API_KEY")
            return None
        
        # 构建提示词
        prompt = self._build_prompt(repo)
        
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(
                    DEEPSEEK_API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=60
                )
                response.raise_for_status()
                result = response.json()
                
                # 解析结果
                content = result["choices"][0]["message"]["content"]
                analysis = json.loads(content)
                
                # 统计 token
                tokens_in = result.get("usage", {}).get("prompt_tokens", 0)
                tokens_out = result.get("usage", {}).get("completion_tokens", 0)
                cost = (tokens_in * 1 + tokens_out * 2) / 1000000  # 元
                
                return {
                    "analysis": analysis,
                    "tokens_input": tokens_in,
                    "tokens_output": tokens_out,
                    "cost": cost
                }
                
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY_BASE * (2 ** attempt)
                    print(f"  请求失败，{wait_time}秒后重试... ({e})")
                    time.sleep(wait_time)
                else:
                    print(f"  请求失败，已达最大重试次数: {e}")
                    return None
            except json.JSONDecodeError as e:
                print(f"  JSON解析失败: {e}")
                return None
            except Exception as e:
                print(f"  未知错误: {e}")
                return None
        
        return None
    
    def _build_prompt(self, repo: dict) -> str:
        """构建分析提示词"""
        readme_content = repo.get("readme_content", "")
        if readme_content:
            readme_preview = readme_content[:3000] + "..." if len(readme_content) > 3000 else readme_content
        else:
            readme_preview = "无 README 内容"
        
        return f"""请分析以下 GitHub 仓库：

【基本信息】
仓库名称: {repo.get("name", "N/A")}
描述: {repo.get("description", "N/A")}
语言: {repo.get("language", "N/A")}
Topics: {', '.join(repo.get("topics", []))}
Stars: {repo.get("stars", 0)}

【README 内容预览】
{readme_preview}

请输出 JSON 格式的分析结果。"""
    
    def process_single_repo(self, repo: dict) -> Optional[dict]:
        """处理单个仓库"""
        repo_id = repo.get("id")
        
        with self.lock:
            if repo_id in self.processed_ids:
                return None
        
        # 检查是否有README
        if not repo.get("readme_content"):
            with self.lock:
                self.stats["readme_ok"] += 1
                self.processed_ids.add(repo_id)
            return None
        
        # 调用API分析
        result = self.analyze_project(repo)
        
        with self.lock:
            self.stats["processed"] += 1
            
            if result:
                self.stats["success"] += 1
                self.stats["tokens_input"] += result["tokens_input"]
                self.stats["tokens_output"] += result["tokens_output"]
                self.stats["total_cost_cny"] += result["cost"]
                self.processed_ids.add(repo_id)
                
                # 更新分类统计
                micro = result["analysis"].get("micro_scenario", "unknown")
                self.category_stats["micro_scenario"][micro] = self.category_stats["micro_scenario"].get(micro, 0) + 1
                
                score = result["analysis"].get("ai_generation_score", 3)
                self.category_stats["ai_generation_score"][score] = self.category_stats["ai_generation_score"].get(score, 0) + 1
                
                return result
            else:
                self.stats["failed"] += 1
                self.failed_ids.add(repo_id)
                return None
    
    def save_result(self, repo: dict, analysis: dict) -> None:
        """保存分析结果"""
        result = {
            "repo_id": repo.get("id"),
            "repo_name": repo.get("name"),
            "repo_url": repo.get("url"),
            "stars": repo.get("stars"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "topics": repo.get("topics", []),
            "ai_generation_score": analysis.get("ai_generation_score"),
            "core_intent": analysis.get("core_intent"),
            "macro_category": analysis.get("macro_category"),
            "micro_scenario": analysis.get("micro_scenario"),
            "complexity_level": analysis.get("complexity_level"),
            "analytical_insight": analysis.get("analytical_insight"),
            "analyzed_at": datetime.now().isoformat(),
        }
        
        with open(OUTPUT_JSON, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    def run(self) -> None:
        """主运行函数"""
        print("=" * 70)
        print("Vibe Coding 8分类分析器")
        print("=" * 70)
        
        # 检查API密钥
        if not self.api_key:
            print("❌ 错误: 未设置 DEEPSEEK_API_KEY 环境变量")
            return
        
        # 加载进度
        self.load_progress()
        
        # 加载待处理数据
        print(f"\n📂 加载数据: {INPUT_FILE}")
        repos = []
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    repo = json.loads(line)
                    repos.append(repo)
                except:
                    pass
        
        self.stats["total"] = len(repos)
        print(f"   总共 {len(repos)} 个仓库")
        
        # 过滤已处理的
        pending_repos = [r for r in repos if r.get("id") not in self.processed_ids]
        print(f"   待处理: {len(pending_repos)} 个")
        
        if not pending_repos:
            print("\n✅ 所有项目已处理完成")
            return
        
        # 预估成本
        estimated_cost = len(pending_repos) * 0.03
        print(f"\n💰 预估成本: ¥{estimated_cost:.2f} (约 {len(pending_repos) * 2500} tokens)")
        
        if estimated_cost > MAX_BUDGET_CNY:
            print(f"⚠️ 警告: 预估成本 ¥{estimated_cost:.2f} 超过预算上限 ¥{MAX_BUDGET_CNY}")
            return
        
        input("\n按 Enter 键开始分析，或按 Ctrl+C 取消...")
        
        self.stats["start_time"] = datetime.now()
        
        # 并发处理
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(self.process_single_repo, repo): repo for repo in pending_repos}
            
            for future in as_completed(futures):
                repo = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.save_result(repo, result["analysis"])
                        
                        # 打印进度
                        if self.stats["success"] % 10 == 0:
                            self.print_progress()
                            self.save_progress()
                            
                except Exception as e:
                    print(f"❌ 处理 {repo.get('name')} 时出错: {e}")
                
                time.sleep(REQUEST_DELAY)
        
        self.stats["end_time"] = datetime.now()
        self.save_progress()
        
        print("\n" + "=" * 70)
        print("分析完成!")
        print("=" * 70)
        self.print_final_stats()
    
    def print_progress(self) -> None:
        """打印进度"""
        processed = self.stats["success"]
        total = self.stats["total"]
        pct = processed / total * 100 if total > 0 else 0
        cost = self.stats["total_cost_cny"]
        
        print(f"\n📊 进度: {processed}/{total} ({pct:.1f}%) | 💰 成本: ¥{cost:.2f}")
        print(f"   分类分布: {dict(sorted(self.category_stats['micro_scenario'].items(), key=lambda x: -x[1])[:5])}")
    
    def print_final_stats(self) -> None:
        """打印最终统计"""
        duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds() / 60
        
        print(f"\n总处理: {self.stats['total']} 个仓库")
        print(f"成功: {self.stats['success']} | 失败: {self.stats['failed']} | 跳过: {self.stats['skipped']}")
        print(f"耗时: {duration:.1f} 分钟")
        print(f"总成本: ¥{self.stats['total_cost_cny']:.2f}")
        print(f"\n8分类分布:")
        for cat, count in sorted(self.category_stats["micro_scenario"].items(), key=lambda x: -x[1]):
            pct = count / self.stats["success"] * 100 if self.stats["success"] > 0 else 0
            print(f"  {cat}: {count} ({pct:.1f}%)")
        
        print(f"\n输出文件:")
        print(f"  JSON: {OUTPUT_JSON}")
        print(f"  进度: {PROGRESS_FILE}")


if __name__ == "__main__":
    analyzer = VibeCodingAnalyzer8Cat()
    analyzer.run()
