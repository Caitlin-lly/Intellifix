"""
升级协同 Agent

判断是否触发升级，生成升级摘要
"""
from typing import Optional

from agents.state import FaultContext, DiagnosisResult, EscalationInfo


class EscalationAgent:
    """升级协同 Agent"""
    
    # 升级触发规则
    ESCALATION_RULES = {
        "risk_level_high": {
            "condition": lambda ctx, diag: diag and diag.risk_level == "高",
            "reason": "风险级别为高，需要专家介入"
        },
        "diagnosis_recommends": {
            "condition": lambda ctx, diag: diag and diag.should_escalate,
            "reason": "诊断结果建议升级处理"
        },
        "downtime_threshold": {
            "condition": lambda ctx, diag: ctx and ctx.downtime_minutes and ctx.downtime_minutes > 15,
            "reason": "停机时间超过15分钟阈值"
        },
        "complex_fault": {
            "condition": lambda ctx, diag: diag and len(diag.probable_causes) > 4,
            "reason": "故障原因复杂，涉及多个可能性"
        },
        "core_component": {
            "condition": lambda ctx, diag: diag and any(
                keyword in str(diag.model_dump())
                for keyword in ["真空泵", "主轴", "控制系统"]
            ),
            "reason": "涉及核心部件，需要专业判断"
        }
    }
    
    def evaluate(
        self,
        fault_context: Optional[FaultContext],
        diagnosis: Optional[DiagnosisResult]
    ) -> EscalationInfo:
        """
        评估是否需要升级
        
        Args:
            fault_context: 故障上下文
            diagnosis: 诊断结果
        
        Returns:
            升级信息
        """
        # 检查各项升级规则
        triggered_rules = []
        
        for rule_name, rule in self.ESCALATION_RULES.items():
            if rule["condition"](fault_context, diagnosis):
                triggered_rules.append(rule["reason"])
        
        should_escalate = len(triggered_rules) > 0
        
        # 生成升级摘要
        summary = None
        expert_focus = []
        
        if should_escalate:
            summary = self._generate_summary(fault_context, diagnosis, triggered_rules)
            expert_focus = self._generate_expert_focus(fault_context, diagnosis)
        
        return EscalationInfo(
            should_escalate=should_escalate,
            reason="; ".join(triggered_rules) if triggered_rules else None,
            summary=summary,
            suggested_expert_focus=expert_focus
        )
    
    def _generate_summary(
        self,
        fault_context: Optional[FaultContext],
        diagnosis: Optional[DiagnosisResult],
        reasons: list
    ) -> str:
        """生成升级摘要"""
        parts = []
        
        # 故障基本信息
        if fault_context:
            parts.append(f"故障代码: {fault_context.fault_code or '未提供'}")
            parts.append(f"故障现象: {fault_context.fault_phenomenon}")
            if fault_context.production_line:
                parts.append(f"产线位置: {fault_context.production_line}")
            if fault_context.device_model:
                parts.append(f"设备型号: {fault_context.device_model}")
            if fault_context.downtime_minutes:
                parts.append(f"已停机: {fault_context.downtime_minutes}分钟")
        
        # 诊断结果
        if diagnosis:
            parts.append(f"故障名称: {diagnosis.fault_name}")
            parts.append(f"风险级别: {diagnosis.risk_level}")
            
            if diagnosis.probable_causes:
                top_causes = [c.cause for c in diagnosis.probable_causes[:3]]
                parts.append(f"可能原因: {', '.join(top_causes)}")
        
        # 升级原因
        parts.append(f"升级原因: {'; '.join(reasons)}")
        
        return "\n".join(parts)
    
    def _generate_expert_focus(
        self,
        fault_context: Optional[FaultContext],
        diagnosis: Optional[DiagnosisResult]
    ) -> list:
        """生成建议专家关注点"""
        focus_points = []
        
        if not diagnosis:
            return ["需要进一步诊断"]
        
        # 基于风险级别
        if diagnosis.risk_level == "高":
            focus_points.append("优先评估安全风险")
        
        # 基于可能原因
        for cause in diagnosis.probable_causes[:2]:
            if "真空泵" in cause.cause:
                focus_points.append("重点检查真空泵状态")
            elif "电磁阀" in cause.cause:
                focus_points.append("检查电磁阀响应")
            elif "气路" in cause.cause:
                focus_points.append("排查气路泄漏点")
        
        # 基于已执行动作
        if fault_context and fault_context.user_actions:
            focus_points.append(f"现场已执行: {', '.join(fault_context.user_actions)}")
        
        # 基于停机时间
        if fault_context and fault_context.downtime_minutes and fault_context.downtime_minutes > 10:
            focus_points.append("停机时间较长，建议优先恢复生产")
        
        if not focus_points:
            focus_points.append("请根据现场情况综合判断")
        
        return focus_points
    
    def format_escalation_for_display(self, escalation: EscalationInfo) -> str:
        """
        格式化升级信息用于展示
        
        Args:
            escalation: 升级信息
        
        Returns:
            格式化的字符串
        """
        if not escalation.should_escalate:
            return "当前故障可在现场处理，无需升级"
        
        lines = ["【建议升级专家处理】"]
        
        if escalation.reason:
            lines.append(f"升级原因: {escalation.reason}")
        
        if escalation.summary:
            lines.append(f"\n升级摘要:\n{escalation.summary}")
        
        if escalation.suggested_expert_focus:
            lines.append("\n建议专家关注点:")
            for i, focus in enumerate(escalation.suggested_expert_focus, 1):
                lines.append(f"  {i}. {focus}")
        
        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    from agents.state import FaultContext, DiagnosisResult, ProbableCause
    
    agent = EscalationAgent()
    
    # 测试场景1: 需要升级
    context1 = FaultContext(
        fault_code="E302",
        fault_phenomenon="真空压力不足",
        production_line="3号线",
        downtime_minutes=20
    )
    diagnosis1 = DiagnosisResult(
        fault_name="真空压力不足",
        probable_causes=[
            ProbableCause(rank=1, cause="吸嘴堵塞", confidence="高", basis=[]),
            ProbableCause(rank=2, cause="过滤器污染", confidence="高", basis=[]),
            ProbableCause(rank=3, cause="气路漏气", confidence="中", basis=[]),
            ProbableCause(rank=4, cause="电磁阀异常", confidence="中", basis=[]),
            ProbableCause(rank=5, cause="真空泵故障", confidence="低", basis=[]),
        ],
        risk_level="高",
        should_escalate=True
    )
    
    result1 = agent.evaluate(context1, diagnosis1)
    print(agent.format_escalation_for_display(result1))
    
    # 测试场景2: 不需要升级
    print("\n" + "="*50 + "\n")
    context2 = FaultContext(
        fault_code="E302",
        fault_phenomenon="真空压力不足",
        downtime_minutes=5
    )
    diagnosis2 = DiagnosisResult(
        fault_name="真空压力不足",
        probable_causes=[
            ProbableCause(rank=1, cause="吸嘴堵塞", confidence="高", basis=[]),
        ],
        risk_level="中",
        should_escalate=False
    )
    
    result2 = agent.evaluate(context2, diagnosis2)
    print(agent.format_escalation_for_display(result2))
