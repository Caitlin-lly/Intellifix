"""
共享状态定义

定义 LangGraph 工作流中各 Agent 共享的状态结构
"""
from typing import List, Optional, Dict, Any, TypedDict
from pydantic import BaseModel


class FaultContext(BaseModel):
    """故障上下文 - InputParser Agent 输出"""
    device_model: Optional[str] = None      # 设备型号: SMT-X100
    fault_code: Optional[str] = None        # 故障代码: E302
    fault_phenomenon: str                   # 故障现象描述
    production_line: Optional[str] = None   # 产线位置: 3号线
    is_stopped: bool = False                # 是否已停机
    downtime_minutes: Optional[int] = None  # 已停机时长
    user_actions: List[str] = []            # 用户已执行动作


class ProbableCause(BaseModel):
    """可能原因"""
    rank: int                               # 排序
    cause: str                              # 原因描述
    confidence: str                         # 置信度: 高/中/低
    basis: List[str] = []                   # 依据来源


class SparePart(BaseModel):
    """建议备件"""
    name: str                               # 备件名称
    model: str                              # 备件型号
    quantity: int = 1                       # 建议数量


class DiagnosisResult(BaseModel):
    """故障诊断结果 - Diagnosis Agent 输出"""
    fault_name: str = ""                    # 故障名称
    probable_causes: List[ProbableCause] = []  # 可能原因排序
    recommended_steps: List[str] = []       # 推荐排查步骤
    risk_level: str = "中"                  # 风险级别: 低/中/高
    should_escalate: bool = False           # 是否建议升级
    spare_parts: List[SparePart] = []       # 建议备件


class EvidenceItem(BaseModel):
    """证据项"""
    suggestion: str                         # 建议内容
    source_docs: List[str] = []             # 来源文档列表
    original_texts: List[str] = []          # 原文片段


class EvidenceChain(BaseModel):
    """证据链 - Evidence Agent 输出"""
    items: List[EvidenceItem] = []          # 证据项列表
    traceable: bool = True                  # 是否可追溯


class EscalationInfo(BaseModel):
    """升级信息 - Escalation Agent 输出"""
    should_escalate: bool = False           # 是否升级
    reason: Optional[str] = None            # 升级原因
    summary: Optional[str] = None           # 升级摘要
    suggested_expert_focus: List[str] = []  # 建议专家关注点


class KnowledgeSinkOutput(BaseModel):
    """知识沉淀输出 - Sink Agent 输出"""
    fault_code: str = ""                    # 故障代码
    fault_phenomenon: str = ""              # 故障现象
    root_cause: str = ""                    # 根因分析
    actions_taken: List[str] = []           # 处理动作
    result: str = ""                        # 处理结果
    time_spent_minutes: Optional[int] = None # 用时
    is_recurring: bool = False              # 是否复发
    applicable_models: List[str] = []       # 适用设备型号


class FaultState(TypedDict, total=False):
    """LangGraph 共享状态"""
    # === 输入 ===
    user_input: str
    
    # === InputParser Agent 输出 ===
    fault_context: Optional[FaultContext]
    parse_error: Optional[str]
    
    # === KnowledgeRetriever Agent 输出 ===
    retrieved_docs: List[Dict[str, Any]]
    retrieval_error: Optional[str]
    
    # === Diagnosis Agent 输出 ===
    diagnosis: Optional[DiagnosisResult]
    diagnosis_error: Optional[str]
    
    # === Evidence Agent 输出 ===
    evidence_chain: Optional[EvidenceChain]
    
    # === Escalation Agent 输出 ===
    escalation: Optional[EscalationInfo]
    
    # === Sink Agent 输出 ===
    knowledge_sink: Optional[KnowledgeSinkOutput]
    
    # === 流程控制 ===
    current_step: str                       # 当前步骤
    should_continue: bool                   # 是否继续
    
    # === 最终输出 ===
    final_report: Optional[Dict[str, Any]]
