# 智能投标工作台 (Bid Workbench)

> 基于 DeepSeek 大模型的智能招投标文档生成平台 —— 上传招标文件，一键生成完整投标书。

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?logo=fastapi)
![DeepSeek](https://img.shields.io/badge/DeepSeek-V3-orange?logo=deepseek&logoColor=white)


## 项目背景

在传统招投标流程中，标书撰写是最耗时、最重复的环节之一——一份完整的技术投标书通常需要 3-5 天人工编写，且容易出现**遗漏技术条款、格式不规范、内容与招标文件不匹配**等痛点问题。

**智能投标工作台** 通过 AI 技术将这一过程自动化：上传招标文件 PDF/Word → 自动提取全部技术要求 → AI 逐条扩充为专业方案 → 一键导出格式规范的 Word 标书。整个过程从数天压缩到 **30 分钟内**。

## 功能特性

### 🎯 核心功能

| 功能 | 说明 |
|------|------|
| **招标文件解析** | 支持 PDF / Word 格式招标文件上传，自动提取全文文本 |
| **AI 智能提取** | 基于大模型精准识别技术要求、系统功能、技术指标等核心条款 |
| **方案自动扩充** | 按"四步法"（设计选型→实现路径→高可用保障→交付验收）逐条生成详细技术方案 |
| **商务报价调整** | 自动根据招标文件要求调整商务承诺书和报价说明 |
| **Word 导出** | 一键生成符合国标格式的 `.docx` 文件，可直接用于正式投标 |

### ✨ 产品亮点

- 🚀 **全链路自动化** — 从原始招标文件到可提交的投标文档，全程无需人工干预
- 💰 **低成本运行** — 采用 DeepSeek API，单次完整标书生成成本不到 ¥1
- 📱 **简洁优雅的 UI** — 苹果风格界面设计，四步向导引导，零学习成本
- 🔒 **安全可控** — 所有数据处理在服务端完成，文件不持久存储
- 🐳 **一键部署** — Docker 容器化部署，支持 Railway / Render 等平台

## 技术架构

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│         静态 HTML + CSS + JS (Apple Style)   │
└──────────────────┬──────────────────────────┘
                   │ HTTP / SSE Stream
┌──────────────────▼──────────────────────────┐
│              FastAPI Backend                 │
│   ┌─────────┐ ┌──────────┐ ┌─────────────┐ │
│   │ 文件解析 │ │ LLM 调用 │ │  Word 生成  │ │
│   │ pdfminer│ │DeepSeek  │ │ python-docx │ │
│   └─────────┘ └──────────┘ └─────────────┘ │
└─────────────────────────────────────────────┘
```

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **后端框架** | Python + FastAPI | 高性能异步 API 框架 |
| **AI 引擎** | DeepSeek Chat (V3) | 64K 上下文窗口，中文能力强 |
| **文档处理** | python-docx / pdfminer | Word 生成 & PDF 解析 |
| **前端** | 纯静态 HTML + CSS + JavaScript | 苹果风格 UI，SSE 流式输出 |
| **部署** | Docker + Railway | 容器化部署，公网访问 |

## 快速开始

### 本地运行

```bash
# 1. 克隆项目
git clone https://github.com/samzhao84-code/bid-workbench.git
cd bid-workbench

# 2. 创建虚拟环境并安装依赖
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env  # 编辑 .env 填入你的 DeepSeek API Key

# 4. 启动服务
uvicorn main:app --host 0.0.0.0 --port 8001

# 5. 浏览器访问
open http://localhost:8001
```

### 环境变量配置

```bash
# .env 文件
LLM_API_KEY=sk-your-deepseek-api-key      # 必填：DeepSeek API 密钥
LLM_BASE_URL=https://api.deepseek.com/v1   # API 端点地址
LLM_MODEL=deepseek-chat                     # 模型名称
LLM_TEMPERATURE=0.3                         # 温度参数（越低越确定）
LLM_MAX_TOKENS=8192                         # 最大输出 token 数
```

### Railway 一键部署

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=...)

> 部署后在 Railway Variables 中添加上述环境变量即可使用。

## 使用流程

1. **上传招标文件** — 拖拽或点击上传 PDF/Word 格式的招标文件
2. **提取技术要求** — 点击"开始提取"，AI 自动识别并结构化所有技术条款
3. **生成投标书** — 确认提取结果后点击"生成"，AI 逐条扩充为完整方案（流式实时显示）
4. **下载文档** — 生成完成后下载格式规范的 `.docx` 文件

<details>
<summary>📸 界面截图</summary>

<!-- 可在此处添加截图 -->
- 主界面：四步向导式操作流程
- 流式生成：实时展示 AI 输出内容
- 文档下载：一键导出标准格式 Word 文件

</details>

## 项目结构

```
bid-workbench/
├── main.py                 # FastAPI 入口，路由定义
├── requirements.txt        # Python 依赖
├── Dockerfile              # Docker 构建文件
├── railway.toml            # Railway 部署配置
├── static/
│   └── index.html          # 前端页面（Apple 风格 UI）
├── services/
│   ├── llm_service.py      # DeepSeek LLM 封装（流式/非流式）
│   ├── tech_extractor.py   # 技术要求提取 + 方案扩充 Prompt
│   ├── doc_parser.py       # PDF/Word 文档解析
│   ├── docx_builder.py     # Word 文档生成器
│   └── task_manager.py     # 任务状态管理
├── template/
│   └── 商务+报价.docx       # 商务报价模板（占位符替换）
└── data/                   # 运行时数据目录
    ├── uploads/            # 用户上传文件
    ├── tasks/              # 任务状态记录
    └── outputs/            # 生成的输出文件
```

## 设计思路

### 为什么选择 DeepSeek？

- **中文理解能力强** — 招投标场景涉及大量专业术语和法规引用，DeepSeek 在中文长文理解和生成方面表现优异
- **成本极低** — 相比 GPT-4，DeepSeek API 价格降低约 95%，单次完整标书生成成本不足 ¥1
- **长上下文支持** — `deepseek-chat` 支持 64K token 上下文窗口，可一次性处理超长招标文件
- **响应速度快** — 平均首字延迟 < 2 秒，适合交互式应用

### Prompt 工程策略

本项目采用**多阶段 Prompt 设计**：

1. **提取阶段** — 结构化 JSON 输出，确保信息不遗漏
2. **扩充阶段** — "四步法"框架（选型→实现→保障→验收），保证内容深度和专业性
3. **商务阶段** — 占位符精确匹配，保持模板格式一致性

每个阶段的 Prompt 都经过多次迭代优化，针对实际招投标文件的典型结构和术语特点进行了专项调优。

## 待办计划

- [ ] 支持更多模型接入（GPT-4o、Claude 等）
- [ ] 添加用户系统与历史任务管理
- [ ] 接入 RAG 知识库，支持企业私有知识增强
- [ ] 支持批量处理多个招标文件
- [ ] 增加投标书质量评分与优化建议


## 作者

Sam

> 如果这个项目对你有帮助，欢迎给个 ⭐！也欢迎通过 Issue 提交建议或反馈问题。
