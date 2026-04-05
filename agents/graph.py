"""
LangGraph 工作流定义

构建 Multi-Agent 系统的工作流图
"""
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END

from agents.state import FaultState
from agents.input_parser import InputParserAgent
from agents.retriever import KnowledgeRetrieverAgent
from agents.diagnosis import DiagnosisAgent
from agents.evidence import EvidenceAgent
from agents.escalation import EscalationAgent
from agents.sink import SinkAgent


class IntelliFixAgent:
    """智修Agent - Multi-Agent 系统封装"""
    
    def __init__(self):
        self.workflow = build_workflow()
        self.app = self.workflow.compile()
    
    def diagnose(self, user_input: str) -> Dict[str, Any]:
        """
        执行故障诊断
        
        Args:
            user_input: 用户输入的故障描述
        
        Returns:
            完整的诊断报告
        """
        # 初始化状态
        initial_state: FaultState = {
            "user_input": user_input,
            "fault_context": None,
            "parse_error": None,
            "retrieved_docs": [],
            "retrieval_error": None,
            "diagnosis": None,
            "diagnosis_error": None,
            "evidence_chain": None,
            "escalation": None,
            "knowledge_sink": None,
            "current_step": "start",
            "should_continue": True,
            "final_report": None
        }
        
        # 执行工作流
        result = self.app.invoke(initial_state)
        
        return result.get("final_report", {})
    
    def diagnose_stream(self, user_input: str):
        """
        流式执行故障诊断（用于展示中间步骤）
        
        Args:
            user_input: 用户输入的故障描述
        
        Yields:
            每个步骤的状态更新
        """
        initial_state: FaultState = {
            "user_input": user_input,
            "fault_context": None,
            "parse_error": None,
            "retrieved_docs": [],
            "retrieval_error": None,
            "diagnosis": None,
            "diagnosis_error": None,
            "evidence_chain": None,
            "escalation": None,
            "knowledge_sink": None,
            "current_step": "start",
            "should_continue": True,
            "final_report": None
        }
        
        for state in self.app.stream(initial_state):
            yield state


def build_workflow() -> StateGraph:
    """构建 LangGraph 工作流"""
    
    # 初始化 Agent
    input_parser = InputParserAgent()
    retriever = KnowledgeRetrieverAgent()
    diagnosis = DiagnosisAgent()
    evidence = EvidenceAgent()
    escalation = EscalationAgent()
    sink = SinkAgent()
    
    # 创建状态图
    workflow = StateGraph(FaultState)
    
    # 添加节点
    workflow.add_node("input_parser", input_parser_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("diagnosis", diagnosis_node)
    workflow.add_node("evidence", evidence_node)
    workflow.add_node("escalation", escalation_node)
    workflow.add_node("sink", sink_node)
    workflow.add_node("report", report_node)
    
    # 设置入口点
    workflow.set_entry_point("input_parser")
    
    # 添加边
    workflow.add_edge("input_parser", "retriever")
    workflow.add_edge("retriever", "diagnosis")
    
    # 诊断后条件路由
    workflow.add_conditional_edges(
        "diagnosis",
        route_after_diagnosis,
        {
            "escalation": "escalation",
            "evidence": "evidence"
        }
    )
    
    # 升级后到证据
    workflow.add_edge("escalation", "evidence")
    
    # 证据后到知识沉淀
    workflow.add_edge("evidence", "sink")
    
    # 知识沉淀到报告
    workflow.add_edge("sink", "report")
    
    # 报告到结束
    workflow.add_edge("report", END)
    
    return workflow


# ============ 节点函数 ============

def input_parser_node(state: FaultState) -> FaultState:
    """输入解析节点"""
    agent = InputParserAgent()
    result = agent.parse(state["user_input"])
    
    state["fault_context"] = result.get("fault_context")
    state["parse_error"] = result.get("error")
    state["current_step"] = "input_parsed"
    
    return state


def retriever_node(state: FaultState) -> FaultState:
    """知识检索节点"""
    if state.get("parse_error"):
        state["retrieval_error"] = "跳过检索：输入解析失败"
        return state
    
    agent = KnowledgeRetrieverAgent()
    fault_context = state.get("fault_context")
    
    if not fault_context:
        state["retrieval_error"] = "故障上下文为空"
        return state
    
    docs = agent.retrieve(fault_context)
    state["retrieved_docs"] = docs
    state["current_step"] = "knowledge_retrieved"
    
    return state


def diagnosis_node(state: FaultState) -> FaultState:
    """故障诊断节点"""
    if state.get("retrieval_error") or not state.get("retrieved_docs"):
        # 使用默认诊断
        state["diagnosis"] = DiagnosisAgent().default_diagnosis(
            state.get("fault_context")
        )
        state["current_step"] = "diagnosis_completed"
        return state
    
    agent = DiagnosisAgent()
    diagnosis_result = agent.diagnose(
        state.get("fault_context"),
        state.get("retrieved_docs", [])
    )
    
    state["diagnosis"] = diagnosis_result
    state["current_step"] = "diagnosis_completed"
    
    return state


def evidence_node(state: FaultState) -> FaultState:
    """证据链生成节点"""
    agent = EvidenceAgent()
    
    evidence = agent.generate_evidence(
        state.get("diagnosis"),
        state.get("retrieved_docs", [])
    )
    
    state["evidence_chain"] = evidence
    state["current_step"] = "evidence_generated"
    
    return state


def escalation_node(state: FaultState) -> FaultState:
    """升级判断节点"""
    agent = EscalationAgent()
    
    escalation = agent.evaluate(
        state.get("fault_context"),
        state.get("diagnosis")
    )
    
    state["escalation"] = escalation
    state["current_step"] = "escalation_evaluated"
    
    return state


def sink_node(state: FaultState) -> FaultState:
    """知识沉淀节点"""
    agent = SinkAgent()
    
    sink_output = agent.sink(
        state.get("fault_context"),
        state.get("diagnosis"),
        state.get("escalation")
    )
    
    state["knowledge_sink"] = sink_output
    state["current_step"] = "knowledge_sunk"
    
    return state


def report_node(state: FaultState) -> FaultState:
    """生成最终报告节点"""
    
    fault_context = state.get("fault_context")
    diagnosis = state.get("diagnosis")
    evidence = state.get("evidence_chain")
    escalation = state.get("escalation")
    
    report = {
        "input": state["user_input"],
        "fault_context": fault_context.model_dump() if fault_context else None,
        "diagnosis": diagnosis.model_dump() if diagnosis else None,
        "evidence_chain": evidence.model_dump() if evidence else None,
        "escalation": escalation.model_dump() if escalation else None,
        "summary": _generate_summary(fault_context, diagnosis, escalation),
        "status": "completed"
    }
    
    state["final_report"] = report
    state["current_step"] = "completed"
    
    return state


# ============ 路由函数 ============

def route_after_diagnosis(state: FaultState) -> Literal["escalation", "evidence"]:
    """诊断后路由决策"""
    diagnosis = state.get("diagnosis")
    
    if diagnosis and diagnosis.should_escalate:
        return "escalation"
    
    return "evidence"


# ============ 辅助函数 ============

def _generate_summary(fault_context, diagnosis, escalation):
    """生成报告摘要"""
    summary_parts = []
    
    if fault_context:
        summary_parts.append(f"故障: {fault_context.fault_code or '未知代码'}")
        summary_parts.append(f"现象: {fault_context.fault_phenomenon}")
    
    if diagnosis:
        summary_parts.append(f"风险级别: {diagnosis.risk_level}")
        if diagnosis.probable_causes:
            top_cause = diagnosis.probable_causes[0]
            summary_parts.append(f"最可能原因: {top_cause.cause}")
    
    if escalation and escalation.should_escalate:
        summary_parts.append("【建议升级专家处理】")
    
    return " | ".join(summary_parts)
