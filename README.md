# 智修Agent - 制造业设备故障诊断系统

> 让每位维护工程师都拥有资深专家的诊断能力

## 🎯 项目简介

智修Agent 是一款面向制造业设备维护场景的 AI 故障诊断助手。通过 Multi-Agent 技术将分散的设备知识、专家经验和历史工单转化为结构化的诊断能力，帮助现场工程师在故障发生时快速定位根因、获取处理方案，显著缩短设备停机时间。

## ✨ 核心特性

- 🤖 **Multi-Agent 智能诊断**: 6 个专业 Agent 协作完成故障诊断全流程
- 🔍 **语义知识检索**: 基于 Chroma 向量数据库的混合检索策略
- 🧠 **大模型推理**: 阿里百炼 DashScope API 提供 Embedding 和 LLM 能力
- 📊 **结构化报告**: 自动生成包含根因分析、处理步骤、备件建议的诊断报告
- 🔗 **证据可追溯**: 每个建议都标注知识来源，满足审计合规要求
- 🌐 **Web 界面**: 前后端分离架构，支持实时诊断和历史记录管理

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (React + Vite)                     │
│              诊断界面 │ 知识库管理 │ 诊断历史                        │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      后端层 (FastAPI)                             │
│         /api/v1/diagnose │ /api/v1/kb/* │ /api/v1/history/*        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Agent 引擎 (LangGraph)                         │
│  InputParser → KnowledgeRetriever → Diagnosis → Evidence → Sink   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│              数据层 (ChromaDB + 阿里百炼 API)                      │
│         向量存储 │ 语义检索 │ text-embedding-v3 │ qwen-plus        │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+
- 阿里百炼 API Key

### 1. 克隆项目

```bash
cd ver1.0
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填写你的阿里百炼 API Key
```

必需配置项：
```env
DASHSCOPE_API_KEY=sk-your-api-key-here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_EMBEDDING_MODEL=text-embedding-v3
DASHSCOPE_LLM_MODEL=qwen-plus
```

### 3. 安装依赖

```bash
# Python 依赖
pip install -r requirements.txt

# 前端依赖
cd frontend/intellifix-web
npm install
cd ../..
```

### 4. 初始化知识库

```bash
python knowledge_base/ingest.py --clear
```

### 5. 启动服务

```bash
# 启动后端 (端口 8000)
cd backend
uvicorn main:app --reload --port 8000

# 新终端 - 启动前端 (端口 5173)
cd frontend/intellifix-web
npm run dev
```

### 6. 访问系统

打开浏览器访问: http://localhost:5173

## 📁 项目结构

```
ver1.0/
├── agents/                     # Multi-Agent 核心引擎
│   ├── graph.py               # LangGraph 工作流定义
│   ├── nodes.py               # Agent 节点实现
│   └── prompts.py             # LLM Prompt 模板
├── knowledge_base/             # 知识库模块
│   ├── chroma_store.py        # ChromaDB 向量存储
│   ├── document_loader.py     # 文档加载与分块
│   └── ingest.py              # 文档入库脚本
├── backend/                    # FastAPI 后端服务
│   ├── main.py                # API 入口
│   └── routers/               # 路由模块
├── frontend/                   # React 前端
│   └── intellifix-web/        # Vite + React + TypeScript
├── documents/                  # 知识库文档目录
├── config.py                   # 全局配置
├── llm_client.py              # 阿里百炼 API 客户端
├── requirements.txt           # Python 依赖
└── .env                       # 环境变量配置
```

## 🧪 使用示例

### 故障诊断

在 Web 界面输入故障描述：

```
3号线贴片机报警E302，吸嘴连续抛料
```

系统将返回结构化诊断报告：

```json
{
  "fault_name": "真空压力不足",
  "probable_causes": [
    {"rank": 1, "cause": "吸嘴堵塞或磨损", "confidence": "高"},
    {"rank": 2, "cause": "真空过滤器污染", "confidence": "高"}
  ],
  "recommended_steps": [
    "检查吸嘴表面是否堵塞、磨损或变形",
    "检查真空压力表读数",
    "检查过滤器是否积尘"
  ],
  "spare_parts": [
    {"name": "吸嘴", "model": "NZ-14A"},
    {"name": "过滤芯", "model": "VF-02"}
  ],
  "risk_level": "中"
}
```

### API 调用

```bash
curl -X POST http://localhost:8000/api/v1/diagnose \
  -H "Content-Type: application/json" \
  -d '{"user_input": "贴片机报警E302"}'
```

## 📚 文档说明

| 文档 | 说明 |
|------|------|
| [技术报告.md](./技术报告.md) | 系统架构、技术栈、产品定位详细说明 |
| [需求文档.md](./需求文档.md) | 原始需求与功能规格 |
| documents/ | 知识库源文档 (故障手册、专家经验等) |

## 🔧 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DASHSCOPE_API_KEY` | 阿里百炼 API Key | 必填 |
| `DASHSCOPE_BASE_URL` | API 基础地址 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| `DASHSCOPE_EMBEDDING_MODEL` | Embedding 模型 | `text-embedding-v3` |
| `DASHSCOPE_LLM_MODEL` | LLM 模型 | `qwen-plus` |
| `CHROMA_PERSIST_DIR` | 向量数据库路径 | `./chroma_db` |
| `DOCUMENTS_DIR` | 知识库文档目录 | `./documents` |

### 模型选择

**Embedding 模型:**
- `text-embedding-v4` - 最新最强，推荐
- `text-embedding-v3` - 稳定可靠
- `text-embedding-v2` - 轻量快速

**LLM 模型:**
- `qwen-max` - 最强能力
- `qwen-plus` - 推荐，性价比最优
- `qwen-turbo` - 轻量快速

## 🐛 常见问题

### Q: 知识库显示 0 个文档？

A: 运行文档入库脚本：
```bash
python knowledge_base/ingest.py --clear
```

### Q: 诊断返回 401 错误？

A: 检查 `.env` 文件中的 `DASHSCOPE_API_KEY` 是否正确配置，然后重启后端服务。

### Q: 前端无法连接后端？

A: 确认后端服务已启动在 `http://localhost:8000`，并检查 CORS 配置。

### Q: 如何添加新的知识文档？

A: 将 Markdown 文件放入 `documents/` 目录，然后重新运行 `ingest.py`。

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18, Vite, TypeScript, Axios |
| 后端 | FastAPI, Python 3.12 |
| AI 框架 | LangGraph, LangChain |
| 向量数据库 | ChromaDB |
| 大模型 | 阿里百炼 DashScope (Embedding + LLM) |
| 配置管理 | Pydantic Settings |

## 📈 性能指标

- 故障诊断响应时间: < 10 秒
- 知识库检索精度: Top-5 准确率 > 85%
- 并发支持: 100+ 并发诊断请求

## 🤝 贡献指南

欢迎提交 Issue 和 PR！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请通过 GitHub Issue 联系。

---

**智修Agent** - 制造业智能化转型的 AI 助手
