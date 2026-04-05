"""
智修Agent - Web 应用接口

基于 Flask/FastAPI 的 RESTful API 接口（简化版使用函数模拟）
"""
import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.graph import IntelliFixAgent


@dataclass
class DiagnoseRequest:
    """诊断请求"""
    user_input: str
    session_id: Optional[str] = None


@dataclass
class DiagnoseResponse:
    """诊断响应"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    session_id: Optional[str] = None


class IntelliFixApp:
    """智修Agent 应用封装"""
    
    def __init__(self):
        self.agent = IntelliFixAgent()
        self.sessions = {}
    
    def diagnose(self, request: DiagnoseRequest) -> DiagnoseResponse:
        """
        执行故障诊断
        
        Args:
            request: 诊断请求
        
        Returns:
            诊断响应
        """
        try:
            # 执行诊断
            report = self.agent.diagnose(request.user_input)
            
            # 生成会话ID
            import uuid
            session_id = request.session_id or str(uuid.uuid4())[:8]
            
            # 保存会话
            self.sessions[session_id] = {
                "user_input": request.user_input,
                "report": report,
                "timestamp": import_time()
            }
            
            return DiagnoseResponse(
                success=True,
                data=report,
                session_id=session_id
            )
            
        except Exception as e:
            return DiagnoseResponse(
                success=False,
                error=str(e)
            )
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息"""
        return self.sessions.get(session_id)
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "service": "智修Agent",
            "version": "1.0.0",
            "active_sessions": len(self.sessions)
        }


def import_time():
    """获取当前时间"""
    from datetime import datetime
    return datetime.now().isoformat()


def format_diagnosis_for_web(response: DiagnoseResponse) -> Dict[str, Any]:
    """
    格式化诊断结果为 Web 友好的格式
    
    Args:
        response: 诊断响应
    
    Returns:
        Web 友好的格式
    """
    if not response.success:
        return {
            "success": False,
            "error": response.error
        }
    
    report = response.data or {}
    
    # 构建结构化输出
    formatted = {
        "success": True,
        "session_id": response.session_id,
        "input": report.get("input"),
        "fault_summary": _extract_summary(report),
        "diagnosis": _format_diagnosis(report.get("diagnosis")),
        "evidence": _format_evidence(report.get("evidence_chain")),
        "escalation": _format_escalation(report.get("escalation")),
        "actions": _extract_actions(report)
    }
    
    return formatted


def _extract_summary(report: Dict[str, Any]) -> str:
    """提取故障摘要"""
    parts = []
    
    fault_context = report.get("fault_context")
    if fault_context:
        if fault_context.get("fault_code"):
            parts.append(fault_context["fault_code"])
        if fault_context.get("fault_phenomenon"):
            parts.append(fault_context["fault_phenomenon"])
    
    diagnosis = report.get("diagnosis")
    if diagnosis:
        if diagnosis.get("risk_level"):
            parts.append(f"风险:{diagnosis['risk_level']}")
    
    return " | ".join(parts) if parts else "未知故障"


def _format_diagnosis(diagnosis: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """格式化诊断结果"""
    if not diagnosis:
        return {}
    
    return {
        "fault_name": diagnosis.get("fault_name"),
        "risk_level": diagnosis.get("risk_level"),
        "should_escalate": diagnosis.get("should_escalate"),
        "causes": [
            {
                "rank": c.get("rank"),
                "description": c.get("cause"),
                "confidence": c.get("confidence")
            }
            for c in diagnosis.get("probable_causes", [])
        ],
        "steps": diagnosis.get("recommended_steps", []),
        "spare_parts": [
            {
                "name": p.get("name"),
                "model": p.get("model"),
                "quantity": p.get("quantity", 1)
            }
            for p in diagnosis.get("spare_parts", [])
        ]
    }


def _format_evidence(evidence_chain: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """格式化证据链"""
    if not evidence_chain:
        return []
    
    return [
        {
            "suggestion": item.get("suggestion"),
            "sources": item.get("source_docs", [])
        }
        for item in evidence_chain.get("items", [])
    ]


def _format_escalation(escalation: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """格式化升级信息"""
    if not escalation:
        return {"should_escalate": False}
    
    return {
        "should_escalate": escalation.get("should_escalate", False),
        "reason": escalation.get("reason"),
        "expert_focus": escalation.get("suggested_expert_focus", [])
    }


def _extract_actions(report: Dict[str, Any]) -> Dict[str, Any]:
    """提取建议动作"""
    actions = {
        "immediate": [],
        "investigation": [],
        "preparation": []
    }
    
    diagnosis = report.get("diagnosis")
    if diagnosis:
        steps = diagnosis.get("recommended_steps", [])
        
        # 分类动作
        for i, step in enumerate(steps):
            if i < 2:
                actions["immediate"].append(step)
            elif i < 5:
                actions["investigation"].append(step)
            else:
                actions["preparation"].append(step)
    
    return actions


# 模拟 API 端点
def api_diagnose(user_input: str, session_id: Optional[str] = None) -> str:
    """
    API: 执行诊断
    
    Args:
        user_input: 用户输入
        session_id: 会话ID（可选）
    
    Returns:
        JSON 字符串
    """
    app = IntelliFixApp()
    request = DiagnoseRequest(user_input=user_input, session_id=session_id)
    response = app.diagnose(request)
    
    formatted = format_diagnosis_for_web(response)
    return json.dumps(formatted, ensure_ascii=False, indent=2)


def api_health() -> str:
    """API: 健康检查"""
    app = IntelliFixApp()
    health = app.health_check()
    return json.dumps(health, ensure_ascii=False, indent=2)


# CLI 接口
def run_cli():
    """运行命令行接口"""
    print("="*60)
    print("智修Agent - RESTful API 模拟")
    print("="*60)
    print()
    
    app = IntelliFixApp()
    
    # 健康检查
    print("📊 健康检查:")
    print(api_health())
    print()
    
    # 示例诊断
    print("🔧 示例诊断:")
    user_input = "3号线贴片机报警E302，吸嘴连续抛料，已停机5分钟"
    print(f"输入: {user_input}")
    print()
    print("输出:")
    print(api_diagnose(user_input))


if __name__ == "__main__":
    run_cli()
