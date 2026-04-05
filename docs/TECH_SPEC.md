# 智修Agent 技术规格文档

**版本**: v1.0  
**日期**: 2026-04-05  
**文档类型**: 技术实现规格说明书

---

## 1. 系统架构概述

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   CLI 界面   │  │  Web 界面   │  │      API 接口           │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          └────────────────┴─────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LangGraph 编排层                            │
│                    (Multi-Agent 系统)                            │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐     │
│  │  Input   │──▶│Knowledge │──▶│Diagnosis │──▶│ Evidence │     │
│  │  Parser  │   │Retriever │   │  Agent   │   │  Agent   │     │
│  └──────────┘   └──────────┘   └────┬─────┘   └──────────┘     │
│                                     │                           │
│                              ┌──────┴──────┐                   │
│                              ▼             ▼                   │
│                        ┌──────────┐   ┌──────────┐             │
│                        │Escalation│   │  Sink    │             │
│                        │  Agent   │   │  Agent   │             │
│                        └──────────┘   └──────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      数据存储层                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │   Chroma DB     │  │   文件系统       │  │   内存状态       │  │
│  │  (向量数据库)    │  │  (知识文档)      │  │  (Shared State) │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

| 组件 | 技术选择 | 版本 |
|------|----------|------|
| Multi-Agent 框架 | LangGraph | >=0.2.0 |
| LLM 集成 | LangChain + OpenAI | >=0.3.0 |
| 向量数据库 | Chroma | >=0.5.0 |
| Embedding | OpenAI text-embedding-3-small | - |
| LLM 模型 | GPT-4o-mini | - |
| 配置管理 | Pydantic Settings | >=2.0.0 |

---

## 2. 数据模型规范

### 2.1 故障上下文 (FaultContext)

```python
class FaultContext(BaseModel):
    """故障上下文 - InputParser Agent 输出"""
    device_model: Optional[str] = None      # 设备型号: SMT-X100
    fault_code: Optional[str] = None        # 故障代码: E302
    fault_phenomenon: str                   # 故障现象描述
    production_line: Optional[str] = None   # 产线位置: 3号线
    is_stopped: bool = False                # 是否已停机
    downtime_minutes: Optional[int] = None  # 已停机时长
    user_actions: List[str] = []            # 用户已执行动作
```

### 2.2 检索文档 (RetrievedDocument)

```python
class RetrievedDocument(BaseModel):
    """检索到的知识文档"""
    doc_id: str                             # 文档ID
    content: str                            # 文档内容
    metadata: DocumentMetadata              # 元数据
    similarity_score: float                 # 相似度分数

class DocumentMetadata(BaseModel):
    """文档元数据"""
    source_file: str                        # 源文件名
    doc_type: str                           # 文档类型
    device_model: Optional[str] = None      # 设备型号
    fault_code: Optional[str] = None        # 故障代码
    tags: List[str] = []                    # 标签列表
```

### 2.3 诊断结果 (DiagnosisResult)

```python
class DiagnosisResult(BaseModel):
    """故障诊断结果 - Diagnosis Agent 输出"""
    fault_name: str                         # 故障名称
    probable_causes: List[ProbableCause]    # 可能原因排序
    recommended_steps: List[str]            # 推荐排查步骤
    risk_level: str                         # 风险级别: 低/中/高
    should_escalate: bool                   # 是否建议升级
    spare_parts: List[SparePart]            # 建议备件

class ProbableCause(BaseModel):
    """可能原因"""
    rank: int                               # 排序
    cause: str                              # 原因描述
    confidence: str                         # 置信度: 高/中/低
    basis: List[str]                        # 依据来源
```

### 2.4 证据链 (EvidenceChain)

```python
class EvidenceItem(BaseModel):
    """证据项"""
    suggestion: str                         # 建议内容
    source_docs: List[str]                  # 来源文档列表
    original_texts: List[str]               # 原文片段

class EvidenceChain(BaseModel):
    """证据链 - Evidence Agent 输出"""
    items: List[EvidenceItem]               # 证据项列表
    traceable: bool = True                  # 是否可追溯
```

### 2.5 升级信息 (EscalationInfo)

```python
class EscalationInfo(BaseModel):
    """升级信息 - Escalation Agent 输出"""
    should_escalate: bool                   # 是否升级
    reason: Optional[str] = None            # 升级原因
    summary: Optional[str] = None           # 升级摘要
    suggested_expert_focus: List[str] = []  # 建议专家关注点
```

### 2.6 知识沉淀 (KnowledgeSinkOutput)

```python
class KnowledgeSinkOutput(BaseModel):
    """知识沉淀输出 - Sink Agent 输出"""
    fault_code: str                         # 故障代码
    fault_phenomenon: str                   # 故障现象
    root_cause: str                         # 根因分析
    actions_taken: List[str]                # 处理动作
    result: str                             # 处理结果
    time_spent_minutes: Optional[int] = None # 用时
    is_recurring: bool = False              # 是否复发
    applicable_models: List[str] = []       # 适用设备型号
```

---

## 3. Shared State 定义

```python
class FaultState(TypedDict):
    """LangGraph 共享状态"""
    # === 输入 ===
    user_input: str
    
    # === InputParser Agent 输出 ===
    fault_context: Optional[FaultContext]
    parse_error: Optional[str]
    
    # === KnowledgeRetriever Agent 输出 ===
    retrieved_docs: List[RetrievedDocument]
    retrieval_error: Optional[str]
    
    # === Diagnosis Agent 输出 ===
    diagnosis: Optional[DiagnosisResult]
    diagnosis_error: Optional[str]
    
    # === Evidence Agent 输出 ===
    evidence_chain: Optional[EvidenceChain]
    
    # === Escalation Agent 输出 ===
    escalation: Optional[EscalationInfo]
    
    # === 流程控制 ===
    current_step: str                       # 当前步骤
    should_continue: bool                   # 是否继续
    
    # === 最终输出 ===
    final_report: Optional[Dict]
```

---

## 4. Agent 详细设计

### 4.1 InputParser Agent

**职责**: 解析用户输入，提取结构化故障信息

**输入**: 
- `user_input`: str - 用户原始输入

**输出**:
- `fault_context`: FaultContext - 结构化故障上下文
- `parse_error`: Optional[str] - 解析错误信息

**实现逻辑**:
1. 使用 LLM 提取关键信息（设备型号、故障代码、现象等）
2. 正则匹配报警码（如 E302）
3. 标准化故障描述

**Prompt 模板**:
```
从以下用户输入中提取故障信息，输出 JSON 格式：

用户输入: {user_input}

需要提取的字段：
- device_model: 设备型号（如 SMT-X100）
- fault_code: 故障代码（如 E302）
- fault_phenomenon: 故障现象描述
- production_line: 产线位置
- is_stopped: 是否已停机
- downtime_minutes: 停机时长（分钟）
- user_actions: 已执行动作列表
```

### 4.2 KnowledgeRetriever Agent

**职责**: 从 Chroma 向量数据库检索相关知识

**输入**:
- `fault_context`: FaultContext

**输出**:
- `retrieved_docs`: List[RetrievedDocument]

**实现逻辑**:
1. 构建检索查询（结合 fault_code + fault_phenomenon）
2. 向量相似度检索（Top-K）
3. Metadata 过滤（device_model, fault_code 匹配）
4. 重排序（结合相似度和 metadata 匹配度）

**混合检索策略**:
```python
# 1. 关键词过滤
where_clause = {"fault_code": fault_context.fault_code}

# 2. 向量检索
query = f"{fault_context.fault_code} {fault_context.fault_phenomenon}"
results = collection.query(
    query_texts=[query],
    where=where_clause,
    n_results=max_results
)

# 3. 重排序
ranked_results = rerank_by_metadata(results, fault_context)
```

### 4.3 DiagnosisAgent

**职责**: 基于检索结果生成故障诊断和处置建议

**输入**:
- `fault_context`: FaultContext
- `retrieved_docs`: List[RetrievedDocument]

**输出**:
- `diagnosis`: DiagnosisResult

**实现逻辑**:
1. 构建 Prompt（包含检索到的知识）
2. LLM 生成结构化诊断结果
3. 提取原因排序、排查步骤、风险提示

**Prompt 模板**:
```
基于以下故障信息和检索到的知识，生成故障诊断报告：

## 故障信息
设备型号: {device_model}
故障代码: {fault_code}
故障现象: {fault_phenomenon}

## 检索到的知识
{retrieved_knowledge}

## 输出要求
请输出 JSON 格式，包含：
- fault_name: 故障名称
- probable_causes: 可能原因列表（按概率排序）
- recommended_steps: 推荐排查步骤
- risk_level: 风险级别（低/中/高）
- should_escalate: 是否建议升级专家
- spare_parts: 建议备件列表
```

### 4.4 EvidenceAgent

**职责**: 为诊断建议生成证据链

**输入**:
- `diagnosis`: DiagnosisResult
- `retrieved_docs`: List[RetrievedDocument]

**输出**:
- `evidence_chain`: EvidenceChain

**实现逻辑**:
1. 遍历诊断建议的每一项
2. 匹配检索文档中的相关片段
3. 建立建议与来源的映射关系

### 4.5 EscalationAgent

**职责**: 判断是否触发升级，生成升级摘要

**输入**:
- `fault_context`: FaultContext
- `diagnosis`: DiagnosisResult

**输出**:
- `escalation`: EscalationInfo

**升级触发条件**:
1. 诊断结果明确建议升级
2. 风险级别为"高"
3. 处理时间超过阈值（15分钟）
4. 涉及真空泵等核心部件

### 4.6 SinkAgent

**职责**: 将处理结果沉淀为结构化知识

**输入**:
- 完整处理流程的所有信息

**输出**:
- `knowledge_sink`: KnowledgeSinkOutput

**触发时机**:
- 故障处理完成（成功或升级后解决）

---

## 5. LangGraph 工作流

### 5.1 节点定义

```python
def input_parser_node(state: FaultState) -> FaultState:
    """解析用户输入"""
    pass

def knowledge_retriever_node(state: FaultState) -> FaultState:
    """检索知识"""
    pass

def diagnosis_node(state: FaultState) -> FaultState:
    """故障诊断"""
    pass

def evidence_node(state: FaultState) -> FaultState:
    """生成证据链"""
    pass

def escalation_node(state: FaultState) -> FaultState:
    """升级判断"""
    pass

def sink_node(state: FaultState) -> FaultState:
    """知识沉淀"""
    pass

def report_node(state: FaultState) -> FaultState:
    """生成最终报告"""
    pass
```

### 5.2 路由函数

```python
def route_after_diagnosis(state: FaultState) -> str:
    """诊断后路由"""
    if state.get("diagnosis") and state["diagnosis"].should_escalate:
        return "escalation"
    return "evidence"

def should_continue(state: FaultState) -> str:
    """判断是否继续流程"""
    if state.get("parse_error") or state.get("retrieval_error"):
        return "error"
    return "continue"
```

### 5.3 图结构

```python
# 构建图
workflow = StateGraph(FaultState)

# 添加节点
workflow.add_node("input_parser", input_parser_node)
workflow.add_node("retriever", knowledge_retriever_node)
workflow.add_node("diagnosis", diagnosis_node)
workflow.add_node("evidence", evidence_node)
workflow.add_node("escalation", escalation_node)
workflow.add_node("sink", sink_node)
workflow.add_node("report", report_node)

# 添加边
workflow.set_entry_point("input_parser")
workflow.add_edge("input_parser", "retriever")
workflow.add_edge("retriever", "diagnosis")
workflow.add_conditional_edges(
    "diagnosis",
    route_after_diagnosis,
    {"escalation": "escalation", "evidence": "evidence"}
)
workflow.add_edge("escalation", "evidence")
workflow.add_edge("evidence", "sink")
workflow.add_edge("sink", "report")
workflow.add_edge("report", END)

# 编译
app = workflow.compile()
```

---

## 6. Chroma 向量数据库设计

### 6.1 Collection 结构

```python
collection = client.create_collection(
    name="intellifix_kb",
    metadata={"hnsw:space": "cosine"}
)
```

### 6.2 文档存储格式

```python
{
    "ids": ["doc_001", "doc_002", ...],
    "documents": ["文档内容1", "文档内容2", ...],
    "metadatas": [
        {
            "source_file": "AS-MFG-KB-ALARM-SMTX100-E302-VacuumLow-v1.0.md",
            "doc_type": "报警手册",
            "device_model": "SMT-X100",
            "fault_code": "E302",
            "tags": ["真空不足", "吸嘴异常", "抛料"]
        },
        ...
    ]
}
```

### 6.3 检索接口

```python
def retrieve(
    query: str,
    fault_code: Optional[str] = None,
    device_model: Optional[str] = None,
    n_results: int = 5
) -> List[RetrievedDocument]:
    """混合检索接口"""
    pass
```

---

## 7. API 接口定义

### 7.1 故障诊断接口

```python
# POST /api/v1/diagnose
class DiagnoseRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None

class DiagnoseResponse(BaseModel):
    session_id: str
    fault_context: FaultContext
    diagnosis: DiagnosisResult
    evidence_chain: EvidenceChain
    escalation: Optional[EscalationInfo]
    final_report: Dict
```

### 7.2 知识检索接口

```python
# POST /api/v1/retrieve
class RetrieveRequest(BaseModel):
    query: str
    fault_code: Optional[str] = None
    n_results: int = 5

class RetrieveResponse(BaseModel):
    documents: List[RetrievedDocument]
    total: int
```

---

## 8. 错误处理

### 8.1 错误类型

| 错误码 | 说明 | 处理策略 |
|--------|------|----------|
| E001 | 输入解析失败 | 返回提示，要求用户补充信息 |
| E002 | 知识检索失败 | 使用默认知识库，降低置信度 |
| E003 | LLM 调用失败 | 返回错误信息，建议人工处理 |
| E004 | 配置错误 | 启动时检查，记录日志 |

### 8.2 容错机制

1. **降级策略**: LLM 不可用时，基于规则匹配返回结果
2. **超时处理**: 每个 Agent 设置超时时间（默认 30 秒）
3. **重试机制**: 网络请求失败时自动重试 3 次

---

## 9. 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 端到端响应时间 | < 5s | 用户输入到完整报告 |
| 知识检索时间 | < 500ms | Chroma 向量检索 |
| LLM 调用时间 | < 3s | 单次 LLM 调用 |
| 并发处理能力 | 10 QPS | 单实例 |

---

## 10. 扩展规划

### 10.1 短期扩展

1. 支持更多设备类型（CNC、注塑机）
2. 接入真实工单系统 API
3. 添加图片识别能力

### 10.2 长期规划

1. 预测性维护（基于传感器数据）
2. 多轮对话支持
3. 知识库自动更新机制
