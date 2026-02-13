# Vibe Coding 研究项目

> 研究问题：Vibe Coding 火热的当下，个人开发者们到底在用 AI 做什么？

## 项目简介

本项目通过爬取 GitHub 上最近两周创建的新仓库，使用 LLM 对项目进行 AI 参与度分析和场景分类，最终回答「个人开发者用 Vibe Coding 在构建什么」这一核心问题。

---

## 目录结构

```
Vibe_Coding/
├── 01_crawling/              # 阶段1: 数据爬取
│   ├── scripts/
│   │   ├── vibe_coding_crawler.py      # 主爬虫（按天切片、分层抽样）
│   │   └── crawler_vibe_coders.py      # 早期版本爬虫
│   ├── docs/
│   │   └── 爬取需求.md                  # 爬虫设计文档
│   └── data/
│       └── vibe_coding_dataset_2w.jsonl    # 约2万条原始仓库数据
│
├── 02_classification/        # 阶段2: AI分类分析
│   ├── scripts/
│   │   ├── deepseek_analyzer_8cat.py     # 8分类分析器（最终版）
│   │   └── reanalyze_8categories.py      # 重新分析/纠错脚本
│   ├── prompt/
│   │   └── LLM提示词_8分类               # DeepSeek API 提示词
│   ├── data/
│   │   ├── vibe_coding_analysis_8cat.jsonl   # 分类结果（JSONL）
│   │   └── vibe_coding_analysis_8cat.csv     # 分类结果（CSV）
│   └── legacy/               # 旧版本（12分类）
│       ├── deepseek_classifier.py
│       └── 12分类/
│
├── 03_analysis/              # 阶段3: 数据分析
│   ├── scripts/
│   │   ├── analyze_micro_scenarios_v4.py     # 微观场景分析（最终版）
│   │   ├── analyze_stars_distribution.py     # 星级分布分析
│   │   └── generate_analysis_report.py       # 报告生成器
│   ├── legacy/               # 旧版本分析脚本
│   │   ├── analyze_micro_scenarios.py
│   │   ├── analyze_micro_scenarios_v2.py
│   │   └── analyze_micro_scenarios_v3.py
│   ├── micro/                # 细分场景详细分析结果
│   └── output/
│       ├── analysis_output/      # 各类统计图表数据
│       └── analysis_report/      # 最终分析报告数据
│
├── 04_reports/               # 阶段4: 最终报告
│   ├── vibe_coding_pipeline_analysis_8cat.md   # 数据处理流程说明
│   └── advanced_analysis_framework.md          # 深度分析框架
│
├── archive/                  # 归档（临时/测试文件）
│   ├── trial/                    # 爬虫测试文件
│   ├── temp_scripts/             # 临时脚本
│   ├── 其他用途分析/
│   └── 配置文件筛选/
│
├── .env                      # 环境变量（需自行配置）
├── .env.example              # 环境变量模板
├── requirements.txt          # Python依赖
└── README.md                 # 本文件
```

---

## 核心方法论

### 1. 数据采集策略
- **按天切片**：从 2026-01-28 开始按天遍历，避免 GitHub 搜索 1000 条限制
- **负向过滤**：排除作业/教程/配置备份等噪音（9大类过滤规则）
- **分层抽样**：
  - Tier 1 (stars ≤ 20): 随机保留 20%（沉默大多数）
  - Tier 2 (stars > 20): 100% 保留（高价值信号）

### 2. AI 分析维度
使用 DeepSeek API 对每个仓库打 6 个标签：

| 维度 | 说明 |
|------|------|
| `ai_generation_score` | 1-5分，评估 AI 参与程度（找 AGENTS.md/.cursorrules 等特征）|
| `core_intent` | ≤15字，一句话概括核心痛点 |
| `macro_category` | 三选一：个人效能工具 / 基础设施组件 / 产品系统原型 |
| `micro_scenario` | 八选一：企业商业应用/效率工具/技术基础设施/娱乐媒体/教育学习/社交社区/健康医疗/个人生活 |
| `complexity_level` | 1-5分，项目技术复杂度 |
| `analytical_insight` | 1-2句话，行业分析师视角洞察 |

### 3. 8分类体系

| 分类 | 覆盖场景 | 典型示例 |
|------|---------|---------|
| **企业商业应用** | 商业流程自动化、电商、金融科技、CRM、ERP | 洗车店管理、机场航班系统、餐厅外卖、房产租赁 |
| **效率工具** | 个人/团队效率、开发者工具、内容创作、模板 | 在线编译器、电子表格、AI工作空间、视频特效 |
| **技术基础设施** | 技术研究、原型验证、系统工具、硬件/IoT | CRUD生成器、基因分析、多智能体框架、Web原型 |
| **娱乐媒体** | 游戏、娱乐消费、媒体播放 | 符号匹配游戏、VR可视化、IPTV播放器、漫画阅读器 |
| **教育学习** | 教育平台、学习工具、知识传授 | 在线教育平台、闪卡应用、课程材料、编程学习工具 |
| **社交社区** | 社交应用、社区平台、通讯、约会 | 聊天机器人、新闻社交API、社团网站、约会匹配 |
| **健康医疗** | 医疗应用、健康追踪、wellness | AI兽医平台、患者药房连接、AI心理日记、健康监测 |
| **个人生活** | 个人生活管理、作品集、家庭管理 | 电影清单、作品集网站、家庭家务管理、个人食谱 |

---

## 使用指南

### 环境配置
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 GITHUB_TOKEN 和 DEEPSEEK_API_KEY
```

### 重新运行分析

```bash
# 步骤1: 运行分类（如需重新分类）
cd 02_classification/scripts
python deepseek_analyzer_8cat.py

# 步骤2: 运行分析
cd ../../03_analysis/scripts
python analyze_micro_scenarios_v4.py
python analyze_stars_distribution.py
python generate_analysis_report.py
```

---

## 数据规模

| 指标 | 数值 |
|------|------|
| 原始扫描仓库 | ~21,000 个 |
| 通过过滤+抽样后 | ~1,500 个 |
| 有 README 可分析 | ~1,500 个 |
| 时间跨度 | 2026-01-28 至 2026-02-10 (约 2 周) |
| 分析成本 | ~¥46 (DeepSeek API) |

---

## 关键洞察（待验证假设）

1. **Vibe Coding 项目量在 2 月出现明显增长** — 时间序列折线斜率
2. **产品原型类项目的 AI 浓度最高** — 三类平均 AI 分数对比
3. **AI 参与度与复杂度正相关** — 散点图相关系数
4. **效率工具和企业商业应用是主力场景** — 场景分布占比
5. **项目平均质量保持稳定（非泡沫）** — 平均 stars 趋势线

---

## 设计原则

1. **负向过滤优于正向关键词**：不依赖 self-reported 标签，通过排除法找真实项目
2. **分层抽样保证代表性**：既关注"沉默大多数"的实验性项目，也重视"高价值信号"的验证项目
3. **AI 辅助分析规模化**：用 LLM 统一标准分析大量仓库，提取结构化洞察
4. **投资人视角的分类**：从商业价值落地角度定义场景，8分类更聚焦核心赛道

---

*项目创建时间：2026-02*  
*数据更新时间：2026-02-10*
