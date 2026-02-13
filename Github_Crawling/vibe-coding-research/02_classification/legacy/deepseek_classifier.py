#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 DeepSeek API 对 Vibe Coding 项目进行智能分类

分类维度:
1. 项目类型 (project_type) - 这是什么类型的项目?
2. 应用领域 (application_domain) - 用于什么场景/领域?
3. 技术栈 (tech_stack) - 主要使用了哪些技术?
4. 完成度 (maturity) - 项目成熟度评估
5.  vibe_coding_score - Vibe Coding 特征评分 (1-10)
"""

import os
import csv
import json
import time
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 分类提示词模板
CLASSIFICATION_PROMPT = """你是一个专业的技术项目分析师，擅长识别和分类软件开发项目。

请分析以下 GitHub 仓库信息，这是一个可能通过 AI Coding Agent (Vibe Coding) 方式创建的项目。

【仓库信息】
名称: {name}
描述: {description}
语言: {language}
Topics: {topics}
来源信号: {source}
配置文件: {config_file}
置信度: {confidence}

请输出以下分类结果（JSON格式）:
{{
  "project_type": "项目类型",
  "project_type_reason": "判断理由（50字以内）",
  "application_domain": "应用领域",
  "application_domain_reason": "判断理由（50字以内）",
  "tech_stack": ["技术1", "技术2", "技术3"],
  "maturity": "mature|prototype|experimental|unknown",
  "maturity_reason": "成熟度判断理由",
  "vibe_coding_score": 8,
  "vibe_coding_signals": ["信号1", "信号2"],
  "key_features": ["功能1", "功能2"],
  "target_users": "目标用户群体"
}}

分类标准:

【项目类型 project_type】
- web_app: Web 应用/SaaS/平台
- web_service: Web API/后端服务
- mobile_app: 移动应用
- desktop_app: 桌面应用
- browser_extension: 浏览器插件
- cli_tool: 命令行工具
- ai_agent: AI Agent/智能机器人
- ai_tool: AI/ML 工具或平台
- automation: 自动化/爬虫/工作流工具
- dev_tool: 开发者工具/IDE插件
- data_tool: 数据处理/分析/可视化工具
- game: 游戏
- content_platform: 内容平台/CMS/社区
- ecommerce: 电商/支付系统
- infra_tool: 基础设施/DevOps工具
- personal_tool: 个人工具/脚本
- library: 开源库/框架/SDK
- template: 模板/脚手架/Boilerplate
- other: 其他

【应用领域 application_domain】
- productivity: 生产力/效率工具
- content_creation: 内容创作/媒体
- business_automation: 业务自动化/企业
- education: 教育/学习
- social: 社交/通讯
- fintech: 金融/支付/加密
- health: 健康/医疗/wellness
- entertainment: 娱乐/游戏
- research: 研究/实验/原型
- personal: 个人生活管理
- ecommerce: 电商/零售
- other: 其他

【成熟度 maturity】
- mature: 功能完整，可生产使用
- prototype: 原型/MVP阶段
- experimental: 实验性/概念验证
- unknown: 无法判断

【Vibe Coding 评分 1-10】
基于以下信号评分:
- 包含 AI 配置文件 (+2)
- 项目描述提及 AI/Agent (+1)
- 代码生成痕迹明显 (+1)
- 单文件/快速原型特征 (+1)
- 项目较新但功能较完整 (+2)
- README 有 AI 生成特征 (+1)
- 项目名/描述有 vibe coding 相关 (+2)

请只返回 JSON，不要其他解释。"""


class DeepSeekClassifier:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.results = []
        
    def classify_project(self, repo: dict) -> dict:
        """使用 DeepSeek API 分类单个项目"""
        if not self.api_key:
            print("❌ 错误: 未设置 DEEPSEEK_API_KEY")
            return None
        
        prompt = CLASSIFICATION_PROMPT.format(
            name=repo.get("name", ""),
            description=repo.get("description", "") or "无描述",
            language=repo.get("language", "Unknown"),
            topics=repo.get("topics", ""),
            source=repo.get("source", ""),
            config_file=repo.get("config_file", "无"),
            confidence=repo.get("confidence", "medium")
        )
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的技术项目分析师。请只返回JSON格式的分析结果，不要其他文字。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        }
        
        max_retries = 3
        for attempt in range(max_retries):
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
                
                # 清理可能的 markdown 代码块
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                # 解析 JSON
                classification = json.loads(content)
                
                # 添加原始数据
                classification.update({
                    "repo_id": repo.get("repo_id"),
                    "full_name": repo.get("full_name"),
                    "html_url": repo.get("html_url"),
                    "stars": repo.get("stars", 0),
                    "language": repo.get("language"),
                    "original_description": repo.get("description"),
                    "confidence": repo.get("confidence"),
                    "classified_at": datetime.now().isoformat(),
                })
                
                return classification
                
            except json.JSONDecodeError as e:
                print(f"    ⚠️ JSON解析失败: {e}")
                print(f"    内容: {content[:200]}")
                if attempt == max_retries - 1:
                    return self._fallback_classification(repo)
                    
            except Exception as e:
                print(f"    ⚠️ API请求失败 ({attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    return self._fallback_classification(repo)
        
        return None
    
    def _fallback_classification(self, repo: dict) -> dict:
        """失败时的默认分类"""
        return {
            "repo_id": repo.get("repo_id"),
            "full_name": repo.get("full_name"),
            "html_url": repo.get("html_url"),
            "project_type": "unknown",
            "project_type_reason": "API调用失败",
            "application_domain": "unknown",
            "application_domain_reason": "API调用失败",
            "tech_stack": [repo.get("language", "Unknown")],
            "maturity": "unknown",
            "maturity_reason": "分类失败",
            "vibe_coding_score": 0,
            "vibe_coding_signals": [],
            "key_features": [],
            "target_users": "unknown",
            "error": True,
        }
    
    def process_csv(self, input_file: str, output_file: str = None, limit: int = None):
        """处理 CSV 文件"""
        if not output_file:
            base = input_file.replace(".csv", "")
            output_file = f"{base}_classified_{datetime.now().strftime('%Y%m%d')}.csv"
        
        # 读取 CSV
        repos = []
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            repos = list(reader)
        
        if limit:
            repos = repos[:limit]
        
        total = len(repos)
        print(f"\n📊 开始分类 {total} 个项目...")
        print("="*70)
        
        classified = []
        for idx, repo in enumerate(repos, 1):
            print(f"\n[{idx}/{total}] {repo.get('full_name', 'Unknown')}")
            
            result = self.classify_project(repo)
            if result:
                classified.append(result)
                score = result.get('vibe_coding_score', 0)
                ptype = result.get('project_type', 'unknown')
                domain = result.get('application_domain', 'unknown')
                print(f"  ✓ 类型: {ptype} | 领域: {domain} | Vibe评分: {score}/10")
            
            # 保存中间结果
            if idx % 10 == 0:
                self._save_intermediate(classified, output_file)
                print(f"  💾 已保存中间结果 ({len(classified)} 条)")
            
            # 避免速率限制
            time.sleep(1)
        
        # 最终结果
        self._save_final(classified, output_file)
        
        # 生成统计报告
        self.generate_report(classified, output_file.replace(".csv", "_report.json"))
        
        return classified
    
    def _save_intermediate(self, results: list, filename: str):
        """保存中间结果"""
        self._save_to_csv(results, filename.replace(".csv", "_temp.csv"))
    
    def _save_final(self, results: list, filename: str):
        """保存最终结果"""
        self._save_to_csv(results, filename)
        print(f"\n✅ 分类完成！结果保存至: {filename}")
    
    def _save_to_csv(self, results: list, filename: str):
        """保存为 CSV"""
        if not results:
            return
        
        # 扁平化 tech_stack 和 key_features
        for r in results:
            if isinstance(r.get("tech_stack"), list):
                r["tech_stack"] = "|".join(r["tech_stack"])
            if isinstance(r.get("key_features"), list):
                r["key_features"] = "|".join(r["key_features"])
            if isinstance(r.get("vibe_coding_signals"), list):
                r["vibe_coding_signals"] = "|".join(r["vibe_coding_signals"])
        
        fieldnames = [
            "repo_id", "full_name", "html_url", "stars", "language",
            "project_type", "project_type_reason",
            "application_domain", "application_domain_reason",
            "tech_stack", "maturity", "maturity_reason",
            "vibe_coding_score", "vibe_coding_signals",
            "key_features", "target_users",
            "confidence", "original_description",
        ]
        
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)
    
    def generate_report(self, results: list, filename: str):
        """生成统计报告"""
        from collections import Counter
        
        # 统计
        types = Counter([r.get("project_type", "unknown") for r in results])
        domains = Counter([r.get("application_domain", "unknown") for r in results])
        maturities = Counter([r.get("maturity", "unknown") for r in results])
        
        # 平均 vibe coding score
        scores = [r.get("vibe_coding_score", 0) for r in results if r.get("vibe_coding_score")]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # 高评分项目
        high_score_projects = [
            {
                "name": r["full_name"],
                "score": r["vibe_coding_score"],
                "type": r["project_type"],
                "domain": r["application_domain"],
                "url": r["html_url"]
            }
            for r in results
            if r.get("vibe_coding_score", 0) >= 7
        ]
        high_score_projects.sort(key=lambda x: x["score"], reverse=True)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_classified": len(results),
            "vibe_coding_score": {
                "average": round(avg_score, 2),
                "distribution": dict(Counter(scores))
            },
            "project_type_distribution": dict(types.most_common()),
            "application_domain_distribution": dict(domains.most_common()),
            "maturity_distribution": dict(maturities.most_common()),
            "high_vibe_score_projects": high_score_projects[:20],
        }
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📈 统计报告: {filename}")
        
        # 控制台摘要
        print("\n" + "="*70)
        print("📊 分类结果摘要")
        print("="*70)
        print(f"\n  总项目数: {len(results)}")
        print(f"  平均 Vibe Score: {avg_score:.1f}/10")
        
        print(f"\n  📂 项目类型 Top 5:")
        for t, c in types.most_common(5):
            print(f"     {t}: {c}")
        
        print(f"\n  🎯 应用领域 Top 5:")
        for d, c in domains.most_common(5):
            print(f"     {d}: {c}")
        
        print(f"\n  🏆 Vibe Score 最高的项目:")
        for p in high_score_projects[:5]:
            print(f"     • {p['name']} (Score: {p['score']}/10)")
            print(f"       {p['type']} | {p['domain']}")


def main():
    print("="*70)
    print("🤖 DeepSeek Vibe Coding 项目智能分类")
    print("="*70)
    
    # 检查 API Key
    if not DEEPSEEK_API_KEY:
        print("\n❌ 错误: 未设置 DEEPSEEK_API_KEY")
        print("   请在 .env 文件中添加: DEEPSEEK_API_KEY=your_key")
        return
    
    # 查找最新的 vibe coding CSV 文件
    import glob
    csv_files = glob.glob("vibe_coding_*.csv")
    
    if not csv_files:
        print("\n❌ 错误: 未找到 vibe coding CSV 文件")
        print("   请先运行: python vibe_coding_crawler.py")
        return
    
    # 显示文件列表
    print("\n📁 找到以下数据文件:")
    for i, f in enumerate(csv_files, 1):
        print(f"   {i}. {f}")
    
    # 选择文件
    choice = input("\n请选择要分类的文件编号 (默认 1): ").strip()
    if not choice:
        choice = "1"
    
    try:
        input_file = csv_files[int(choice) - 1]
    except (ValueError, IndexError):
        input_file = csv_files[0]
    
    print(f"\n📂 选择文件: {input_file}")
    
    # 询问是否限制数量
    limit_input = input("\n限制处理数量? (直接回车处理全部, 或输入数字): ").strip()
    limit = int(limit_input) if limit_input.isdigit() else None
    
    # 开始分类
    classifier = DeepSeekClassifier(DEEPSEEK_API_KEY)
    classifier.process_csv(input_file, limit=limit)


if __name__ == "__main__":
    main()
