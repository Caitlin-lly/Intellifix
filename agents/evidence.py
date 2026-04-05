"""
证据链 Agent

为诊断建议生成证据链，增强可解释性
"""
from typing import List, Dict, Any, Optional

from agents.state import DiagnosisResult, EvidenceChain, EvidenceItem


class EvidenceAgent:
    """证据链 Agent"""
    
    def generate_evidence(
        self,
        diagnosis: Optional[DiagnosisResult],
        retrieved_docs: List[Dict[str, Any]]
    ) -> EvidenceChain:
        """
        生成证据链
        
        Args:
            diagnosis: 诊断结果
            retrieved_docs: 检索到的知识文档
        
        Returns:
            证据链
        """
        if not diagnosis:
            return EvidenceChain(
                items=[],
                traceable=False
            )
        
        evidence_items = []
        
        # 为每个可能原因生成证据
        for cause in diagnosis.probable_causes:
            item = self._generate_cause_evidence(cause.cause, retrieved_docs)
            if item:
                evidence_items.append(item)
        
        # 为排查步骤生成证据
        for step in diagnosis.recommended_steps[:3]:  # 只为前3个步骤生成证据
            item = self._generate_step_evidence(step, retrieved_docs)
            if item:
                evidence_items.append(item)
        
        # 为备件建议生成证据
        for part in diagnosis.spare_parts:
            item = self._generate_part_evidence(part.name, part.model, retrieved_docs)
            if item:
                evidence_items.append(item)
        
        return EvidenceChain(
            items=evidence_items,
            traceable=len(evidence_items) > 0
        )
    
    def _generate_cause_evidence(
        self,
        cause: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> Optional[EvidenceItem]:
        """为原因生成证据"""
        source_docs = []
        original_texts = []
        
        # 从检索文档中查找相关证据
        for doc in retrieved_docs:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source = metadata.get("source_file", "未知")
            doc_type = metadata.get("doc_type", "")
            
            # 检查文档是否包含原因关键词
            if self._is_related(cause, content):
                if source not in source_docs:
                    source_docs.append(f"{source} ({doc_type})")
                
                # 提取相关原文片段
                excerpt = self._extract_excerpt(cause, content)
                if excerpt and excerpt not in original_texts:
                    original_texts.append(excerpt)
        
        if source_docs:
            return EvidenceItem(
                suggestion=f"可能原因: {cause}",
                source_docs=source_docs[:3],  # 最多3个来源
                original_texts=original_texts[:2]  # 最多2个原文片段
            )
        
        return None
    
    def _generate_step_evidence(
        self,
        step: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> Optional[EvidenceItem]:
        """为步骤生成证据"""
        source_docs = []
        original_texts = []
        
        for doc in retrieved_docs:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source = metadata.get("source_file", "未知")
            doc_type = metadata.get("doc_type", "")
            
            if self._is_related(step, content):
                if source not in source_docs:
                    source_docs.append(f"{source} ({doc_type})")
                
                excerpt = self._extract_excerpt(step, content)
                if excerpt and excerpt not in original_texts:
                    original_texts.append(excerpt)
        
        if source_docs:
            return EvidenceItem(
                suggestion=f"排查步骤: {step}",
                source_docs=source_docs[:2],
                original_texts=original_texts[:1]
            )
        
        return None
    
    def _generate_part_evidence(
        self,
        part_name: str,
        part_model: str,
        retrieved_docs: List[Dict[str, Any]]
    ) -> Optional[EvidenceItem]:
        """为备件生成证据"""
        source_docs = []
        original_texts = []
        
        # 构建备件查询关键词
        query_terms = [part_name, part_model]
        
        for doc in retrieved_docs:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source = metadata.get("source_file", "未知")
            doc_type = metadata.get("doc_type", "")
            
            # 检查是否包含备件信息
            if any(term in content for term in query_terms):
                if source not in source_docs:
                    source_docs.append(f"{source} ({doc_type})")
                
                excerpt = self._extract_excerpt(part_model, content)
                if excerpt and excerpt not in original_texts:
                    original_texts.append(excerpt)
        
        if source_docs:
            return EvidenceItem(
                suggestion=f"建议备件: {part_name} ({part_model})",
                source_docs=source_docs[:2],
                original_texts=original_texts[:1]
            )
        
        return None
    
    def _is_related(self, query: str, content: str) -> bool:
        """检查查询是否与内容相关"""
        # 提取关键词
        keywords = self._extract_keywords(query)
        
        # 计算匹配的关键词数量
        match_count = sum(1 for kw in keywords if kw in content)
        
        # 如果匹配超过一半关键词，认为相关
        return match_count >= len(keywords) / 2 or match_count >= 2
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取：过滤掉停用词和短词
        stop_words = {'的', '了', '是', '在', '和', '或', '与', '及', '等'}
        words = []
        
        # 按非中文字符分割
        import re
        tokens = re.findall(r'[\u4e00-\u9fa5]+|\w+', text)
        
        for token in tokens:
            if len(token) >= 2 and token not in stop_words:
                words.append(token)
        
        return words
    
    def _extract_excerpt(self, keyword: str, content: str, max_length: int = 150) -> Optional[str]:
        """提取包含关键词的原文片段"""
        # 查找关键词位置
        idx = content.find(keyword)
        if idx == -1:
            # 尝试查找部分匹配
            keywords = self._extract_keywords(keyword)
            for kw in keywords:
                idx = content.find(kw)
                if idx != -1:
                    break
        
        if idx == -1:
            return None
        
        # 提取上下文
        start = max(0, idx - 50)
        end = min(len(content), idx + len(keyword) + 50)
        
        excerpt = content[start:end]
        
        # 清理并截断
        excerpt = excerpt.replace('\n', ' ').strip()
        if len(excerpt) > max_length:
            excerpt = excerpt[:max_length] + "..."
        
        return excerpt
    
    def format_evidence_for_display(self, evidence_chain: EvidenceChain) -> str:
        """
        格式化证据链用于展示
        
        Args:
            evidence_chain: 证据链
        
        Returns:
            格式化的字符串
        """
        if not evidence_chain.items:
            return "暂无证据链信息"
        
        lines = ["证据链:"]
        
        for i, item in enumerate(evidence_chain.items, 1):
            lines.append(f"\n{i}. {item.suggestion}")
            
            if item.source_docs:
                lines.append(f"   来源: {', '.join(item.source_docs)}")
            
            if item.original_texts:
                for text in item.original_texts:
                    lines.append(f"   原文: \"{text}\"")
        
        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    from agents.state import DiagnosisResult, ProbableCause, SparePart
    
    agent = EvidenceAgent()
    
    # 模拟诊断结果
    diagnosis = DiagnosisResult(
        fault_name="真空压力不足",
        probable_causes=[
            ProbableCause(rank=1, cause="吸嘴堵塞", confidence="高", basis=[]),
            ProbableCause(rank=2, cause="过滤器污染", confidence="高", basis=[]),
        ],
        recommended_steps=["检查吸嘴", "检查过滤器"],
        risk_level="中",
        should_escalate=False,
        spare_parts=[SparePart(name="吸嘴", model="NZ-14A")]
    )
    
    # 模拟检索文档
    retrieved_docs = [
        {
            "content": "吸嘴堵塞是最常见的原因。过滤器污染也会导致真空不足。",
            "metadata": {"source_file": "alarm_manual.md", "doc_type": "报警手册"}
        },
        {
            "content": "建议备件：吸嘴 NZ-14A，过滤芯 VF-02",
            "metadata": {"source_file": "parts_list.md", "doc_type": "备件表"}
        }
    ]
    
    evidence = agent.generate_evidence(diagnosis, retrieved_docs)
    print(agent.format_evidence_for_display(evidence))
