"""
故障诊断 Agent

基于检索结果生成故障诊断和处置建议
"""
from typing import List, Dict, Any, Optional

from agents.state import (
    FaultContext, DiagnosisResult, ProbableCause, SparePart
)
from agents.retriever import KnowledgeRetrieverAgent


class DiagnosisAgent:
    """故障诊断 Agent"""
    
    # 常见故障模式与建议
    FAULT_PATTERNS = {
        "E302": {
            "name": "真空压力不足",
            "causes": [
                ("吸嘴堵塞或磨损", "高"),
                ("真空过滤器污染", "高"),
                ("气路接头松动漏气", "中"),
                ("真空电磁阀动作异常", "中"),
                ("真空泵性能下降", "低"),
            ],
            "steps": [
                "检查吸嘴表面是否堵塞、磨损或变形",
                "检查真空压力表读数",
                "检查过滤器是否积尘",
                "检查气路接头及软管是否漏气",
                "检查真空电磁阀响应",
                "检查真空泵输出",
            ],
            "spare_parts": [
                ("吸嘴", "NZ-14A"),
                ("过滤芯", "VF-02"),
                ("电磁阀", "SV-11"),
            ],
            "risk_level": "中",
        }
    }
    
    def diagnose(
        self,
        fault_context: Optional[FaultContext],
        retrieved_docs: List[Dict[str, Any]]
    ) -> DiagnosisResult:
        """
        执行故障诊断
        
        Args:
            fault_context: 故障上下文
            retrieved_docs: 检索到的知识文档
        
        Returns:
            诊断结果
        """
        if not fault_context:
            return self._empty_diagnosis()
        
        fault_code = fault_context.fault_code
        
        # 如果有已知故障模式，使用模式匹配
        if fault_code and fault_code in self.FAULT_PATTERNS:
            return self._pattern_based_diagnosis(fault_code, retrieved_docs)
        
        # 否则基于检索知识生成诊断
        return self._knowledge_based_diagnosis(fault_context, retrieved_docs)
    
    def default_diagnosis(self, fault_context: Optional[FaultContext]) -> DiagnosisResult:
        """生成默认诊断（当检索失败时使用）"""
        if not fault_context:
            return self._empty_diagnosis()
        
        fault_code = fault_context.fault_code
        
        if fault_code and fault_code in self.FAULT_PATTERNS:
            return self._pattern_based_diagnosis(fault_code, [])
        
        return DiagnosisResult(
            fault_name=f"未知故障 ({fault_code or '无代码'})",
            probable_causes=[
                ProbableCause(rank=1, cause="需要进一步检查", confidence="低", basis=[])
            ],
            recommended_steps=[
                "查看设备报警手册",
                "联系设备厂商技术支持",
                "记录故障现象并上报"
            ],
            risk_level="中",
            should_escalate=True,
            spare_parts=[]
        )
    
    def _pattern_based_diagnosis(
        self,
        fault_code: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> DiagnosisResult:
        """基于已知模式生成诊断"""
        pattern = self.FAULT_PATTERNS[fault_code]
        
        # 构建可能原因列表
        causes = []
        for i, (cause_desc, confidence) in enumerate(pattern["causes"], 1):
            # 从检索文档中查找依据
            basis = self._find_basis(cause_desc, retrieved_docs)
            causes.append(ProbableCause(
                rank=i,
                cause=cause_desc,
                confidence=confidence,
                basis=basis
            ))
        
        # 构建备件列表
        spare_parts = [
            SparePart(name=name, model=model)
            for name, model in pattern["spare_parts"]
        ]
        
        # 判断是否建议升级
        should_escalate = pattern["risk_level"] == "高"
        
        return DiagnosisResult(
            fault_name=pattern["name"],
            probable_causes=causes,
            recommended_steps=pattern["steps"],
            risk_level=pattern["risk_level"],
            should_escalate=should_escalate,
            spare_parts=spare_parts
        )
    
    def _knowledge_based_diagnosis(
        self,
        fault_context: FaultContext,
        retrieved_docs: List[Dict[str, Any]]
    ) -> DiagnosisResult:
        """基于检索知识生成诊断"""
        # 从检索文档中提取信息
        causes = []
        steps = []
        spare_parts = []
        risk_level = "中"
        
        for doc in retrieved_docs:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            doc_type = metadata.get("doc_type", "")
            
            # 提取可能原因
            if "可能原因" in content or "高概率原因" in content:
                extracted_causes = self._extract_causes_from_content(content)
                causes.extend(extracted_causes)
            
            # 提取排查步骤
            if "排查" in content or "步骤" in content or "SOP" in doc_type:
                extracted_steps = self._extract_steps_from_content(content)
                steps.extend(extracted_steps)
            
            # 提取备件信息
            if "备件" in doc_type or "BOM" in content:
                extracted_parts = self._extract_spare_parts_from_content(content)
                spare_parts.extend(extracted_parts)
            
            # 提取风险级别
            if "风险" in content:
                if "高" in content:
                    risk_level = "高"
        
        # 去重并排序
        causes = self._deduplicate_causes(causes)
        steps = list(dict.fromkeys(steps))  # 保持顺序去重
        spare_parts = self._deduplicate_spare_parts(spare_parts)
        
        # 如果没有提取到原因，添加默认原因
        if not causes:
            causes = [ProbableCause(
                rank=1,
                cause="需要进一步检查",
                confidence="中",
                basis=[]
            )]
        
        # 如果没有提取到步骤，添加默认步骤
        if not steps:
            steps = ["查看相关技术文档", "联系技术支持"]
        
        # 判断是否建议升级
        should_escalate = risk_level == "高" or len(causes) > 3
        
        return DiagnosisResult(
            fault_name=fault_context.fault_phenomenon or "未知故障",
            probable_causes=causes[:5],  # 最多5个原因
            recommended_steps=steps[:8],  # 最多8个步骤
            risk_level=risk_level,
            should_escalate=should_escalate,
            spare_parts=spare_parts[:5]  # 最多5个备件
        )
    
    def _find_basis(self, cause_desc: str, retrieved_docs: List[Dict[str, Any]]) -> List[str]:
        """查找原因的依据来源"""
        basis = []
        for doc in retrieved_docs:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source = metadata.get("source_file", "未知")
            
            # 简单匹配：如果文档内容包含原因关键词
            cause_keywords = cause_desc.replace("或", " ").replace("、", " ").split()
            if any(kw in content for kw in cause_keywords if len(kw) > 1):
                basis.append(source)
        
        return list(set(basis))[:3]  # 最多3个来源
    
    def _extract_causes_from_content(self, content: str) -> List[ProbableCause]:
        """从内容中提取可能原因"""
        causes = []
        lines = content.split("\n")
        
        for line in lines:
            # 匹配列表项，如 "1. 吸嘴堵塞" 或 "- 吸嘴堵塞"
            match = re.search(r'^[\s]*[\d\-\*\.]\s*[\)\.]?\s*(.+)', line)
            if match:
                cause_desc = match.group(1).strip()
                # 过滤掉太短的项
                if len(cause_desc) > 3:
                    causes.append(ProbableCause(
                        rank=len(causes) + 1,
                        cause=cause_desc,
                        confidence="中",
                        basis=[]
                    ))
        
        return causes
    
    def _extract_steps_from_content(self, content: str) -> List[str]:
        """从内容中提取排查步骤"""
        steps = []
        lines = content.split("\n")
        in_step_section = False
        
        for line in lines:
            # 检测步骤相关章节
            if any(kw in line for kw in ["步骤", "排查", "检查", "操作"]):
                in_step_section = True
            
            if in_step_section:
                match = re.search(r'^[\s]*[\d\-\*\.]\s*[\)\.]?\s*(.+)', line)
                if match:
                    step_desc = match.group(1).strip()
                    if len(step_desc) > 3:
                        steps.append(step_desc)
        
        return steps
    
    def _extract_spare_parts_from_content(self, content: str) -> List[SparePart]:
        """从内容中提取备件信息"""
        parts = []
        lines = content.split("\n")
        
        for line in lines:
            # 匹配备件格式：名称 型号 或 名称：型号
            match = re.search(r'([\u4e00-\u9fa5\w]+)[：:\s]+([A-Z]?\d+[\-\w]*)', line)
            if match:
                name = match.group(1).strip()
                model = match.group(2).strip()
                if name and model and len(name) < 20:
                    parts.append(SparePart(name=name, model=model))
        
        return parts
    
    def _deduplicate_causes(self, causes: List[ProbableCause]) -> List[ProbableCause]:
        """去重原因列表"""
        seen = set()
        unique_causes = []
        
        for cause in causes:
            key = cause.cause
            if key not in seen:
                seen.add(key)
                cause.rank = len(unique_causes) + 1
                unique_causes.append(cause)
        
        return unique_causes
    
    def _deduplicate_spare_parts(self, parts: List[SparePart]) -> List[SparePart]:
        """去重备件列表"""
        seen = set()
        unique_parts = []
        
        for part in parts:
            key = f"{part.name}:{part.model}"
            if key not in seen:
                seen.add(key)
                unique_parts.append(part)
        
        return unique_parts
    
    def _empty_diagnosis(self) -> DiagnosisResult:
        """空诊断结果"""
        return DiagnosisResult(
            fault_name="无法诊断",
            probable_causes=[
                ProbableCause(rank=1, cause="故障信息不足", confidence="低", basis=[])
            ],
            recommended_steps=["请提供更多信息"],
            risk_level="低",
            should_escalate=True,
            spare_parts=[]
        )


import re  # 放在文件末尾避免循环导入问题


# 测试代码
if __name__ == "__main__":
    agent = DiagnosisAgent()
    
    # 测试已知故障模式
    from agents.state import FaultContext
    
    context = FaultContext(
        fault_code="E302",
        fault_phenomenon="真空压力不足"
    )
    
    result = agent.diagnose(context, [])
    print(f"故障名称: {result.fault_name}")
    print(f"风险级别: {result.risk_level}")
    print(f"建议升级: {result.should_escalate}")
    print("\n可能原因:")
    for cause in result.probable_causes:
        print(f"  {cause.rank}. {cause.cause} (置信度: {cause.confidence})")
