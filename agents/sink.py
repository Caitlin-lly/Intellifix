"""
知识沉淀 Agent

将处理结果沉淀为结构化知识案例
"""
from typing import Optional
from datetime import datetime

from agents.state import (
    FaultContext, DiagnosisResult, EscalationInfo, KnowledgeSinkOutput
)


class SinkAgent:
    """知识沉淀 Agent"""
    
    def sink(
        self,
        fault_context: Optional[FaultContext],
        diagnosis: Optional[DiagnosisResult],
        escalation: Optional[EscalationInfo]
    ) -> KnowledgeSinkOutput:
        """
        生成知识沉淀
        
        Args:
            fault_context: 故障上下文
            diagnosis: 诊断结果
            escalation: 升级信息
        
        Returns:
            知识沉淀输出
        """
        output = KnowledgeSinkOutput()
        
        # 提取故障代码
        if fault_context:
            output.fault_code = fault_context.fault_code or "未知"
            output.fault_phenomenon = fault_context.fault_phenomenon
            
            # 记录停机时间
            if fault_context.downtime_minutes:
                output.time_spent_minutes = fault_context.downtime_minutes
            
            # 记录已执行动作
            if fault_context.user_actions:
                output.actions_taken = fault_context.user_actions
        
        # 提取诊断信息
        if diagnosis:
            # 根因分析：取最可能的原因
            if diagnosis.probable_causes:
                top_cause = diagnosis.probable_causes[0]
                output.root_cause = top_cause.cause
            
            # 处理动作：使用推荐步骤
            if diagnosis.recommended_steps:
                output.actions_taken.extend(diagnosis.recommended_steps)
            
            # 适用设备型号
            if fault_context and fault_context.device_model:
                output.applicable_models.append(fault_context.device_model)
        
        # 处理结果
        if escalation:
            if escalation.should_escalate:
                output.result = "已升级专家处理"
            else:
                output.result = "现场处理完成"
        else:
            output.result = "待确认"
        
        # 去重处理动作
        output.actions_taken = list(dict.fromkeys(output.actions_taken))
        
        return output
    
    def generate_case_document(self, sink_output: KnowledgeSinkOutput) -> str:
        """
        生成案例文档（Markdown 格式）
        
        Args:
            sink_output: 知识沉淀输出
        
        Returns:
            Markdown 格式文档
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        case_id = f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        lines = [
            f"# 历史案例 {case_id}",
            f"文档编号: AS-MFG-KB-CASE-{case_id}",
            f"文档版本: v1.0",
            f"文档类型: 历史案例",
            f"生成时间: {timestamp}",
            f"标签: 自动沉淀, {sink_output.fault_code}",
            "",
            "## 故障信息",
            f"- 故障代码: {sink_output.fault_code}",
            f"- 故障现象: {sink_output.fault_phenomenon}",
            "",
            "## 根因分析",
            sink_output.root_cause or "待补充",
            "",
            "## 处理动作",
        ]
        
        for action in sink_output.actions_taken:
            lines.append(f"- {action}")
        
        lines.extend([
            "",
            "## 处理结果",
            sink_output.result,
            "",
        ])
        
        if sink_output.time_spent_minutes:
            lines.append(f"## 处理用时")
            lines.append(f"{sink_output.time_spent_minutes} 分钟")
            lines.append("")
        
        if sink_output.applicable_models:
            lines.append("## 适用设备型号")
            for model in sink_output.applicable_models:
                lines.append(f"- {model}")
            lines.append("")
        
        lines.extend([
            "## 经验总结",
            "（待处理完成后补充）",
            "",
            "## 可复用结论",
            "（待处理完成后补充）",
        ])
        
        return "\n".join(lines)
    
    def save_case_document(self, sink_output: KnowledgeSinkOutput, output_dir: str = "./cases") -> str:
        """
        保存案例文档到文件
        
        Args:
            sink_output: 知识沉淀输出
            output_dir: 输出目录
        
        Returns:
            保存的文件路径
        """
        import os
        from pathlib import Path
        
        # 确保目录存在
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        fault_code = sink_output.fault_code or "UNKNOWN"
        filename = f"AS-MFG-KB-CASE-{fault_code}-{timestamp}-v1.0.md"
        filepath = os.path.join(output_dir, filename)
        
        # 生成并保存文档
        content = self.generate_case_document(sink_output)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        
        return filepath


# 测试代码
if __name__ == "__main__":
    from agents.state import FaultContext, DiagnosisResult, ProbableCause, EscalationInfo
    
    agent = SinkAgent()
    
    # 模拟处理完成场景
    context = FaultContext(
        fault_code="E302",
        fault_phenomenon="真空压力不足，吸嘴抛料",
        production_line="3号线",
        device_model="SMT-X100",
        downtime_minutes=15,
        user_actions=["已清洁吸嘴"]
    )
    
    diagnosis = DiagnosisResult(
        fault_name="真空压力不足",
        probable_causes=[
            ProbableCause(rank=1, cause="过滤器污染", confidence="高", basis=[]),
        ],
        recommended_steps=["更换过滤芯 VF-02", "清洁真空管路"],
        risk_level="中",
        should_escalate=False
    )
    
    escalation = EscalationInfo(
        should_escalate=False,
        reason=None
    )
    
    sink_output = agent.sink(context, diagnosis, escalation)
    
    print("知识沉淀输出:")
    print(f"  故障代码: {sink_output.fault_code}")
    print(f"  故障现象: {sink_output.fault_phenomenon}")
    print(f"  根因分析: {sink_output.root_cause}")
    print(f"  处理结果: {sink_output.result}")
    print(f"  处理用时: {sink_output.time_spent_minutes}分钟")
    
    print("\n生成的案例文档:")
    print("="*50)
    print(agent.generate_case_document(sink_output))
