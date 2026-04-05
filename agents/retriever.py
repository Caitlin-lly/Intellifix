"""
知识检索 Agent

从 Chroma 向量数据库检索相关知识
"""
from typing import List, Dict, Any, Optional

from config import settings
from knowledge_base.chroma_store import ChromaStore
from agents.state import FaultContext


class KnowledgeRetrieverAgent:
    """知识检索 Agent"""
    
    def __init__(self):
        self.store = ChromaStore()
    
    def retrieve(self, fault_context: FaultContext) -> List[Dict[str, Any]]:
        """
        检索相关知识
        
        Args:
            fault_context: 故障上下文
        
        Returns:
            检索到的文档列表
        """
        # 构建检索查询
        query = self._build_query(fault_context)
        
        # 执行混合检索
        results = self.store.hybrid_search(
            query_text=query,
            fault_code=fault_context.fault_code,
            device_model=fault_context.device_model,
            n_results=settings.max_retrieval_docs
        )
        
        # 转换为字典列表
        docs = []
        for r in results:
            docs.append({
                "doc_id": r.doc_id,
                "content": r.content,
                "metadata": r.metadata,
                "similarity_score": r.similarity_score
            })
        
        return docs
    
    def _build_query(self, fault_context: FaultContext) -> str:
        """构建检索查询"""
        query_parts = []
        
        # 添加故障代码
        if fault_context.fault_code:
            query_parts.append(fault_context.fault_code)
        
        # 添加故障现象
        if fault_context.fault_phenomenon:
            query_parts.append(fault_context.fault_phenomenon)
        
        # 添加设备型号
        if fault_context.device_model:
            query_parts.append(fault_context.device_model)
        
        # 如果没有有效查询，使用默认查询
        if not query_parts:
            return "设备故障 维修"
        
        return " ".join(query_parts)
    
    def retrieve_by_fault_code(self, fault_code: str) -> List[Dict[str, Any]]:
        """
        按故障代码检索
        
        Args:
            fault_code: 故障代码
        
        Returns:
            相关文档列表
        """
        results = self.store.get_by_fault_code(fault_code)
        
        docs = []
        for r in results:
            docs.append({
                "doc_id": r.doc_id,
                "content": r.content,
                "metadata": r.metadata,
                "similarity_score": r.similarity_score
            })
        
        return docs
    
    def format_retrieved_context(self, docs: List[Dict[str, Any]]) -> str:
        """
        格式化检索结果用于 Prompt
        
        Args:
            docs: 检索到的文档列表
        
        Returns:
            格式化的上下文字符串
        """
        if not docs:
            return "未检索到相关知识。"
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            metadata = doc.get("metadata", {})
            source = metadata.get("source_file", "未知来源")
            doc_type = metadata.get("doc_type", "未知类型")
            
            context_parts.append(
                f"【知识{i}】来源: {source} ({doc_type})\n"
                f"{doc['content'][:800]}..."  # 限制长度
            )
        
        return "\n\n".join(context_parts)


# 测试代码
if __name__ == "__main__":
    from agents.state import FaultContext
    
    agent = KnowledgeRetrieverAgent()
    
    # 测试检索
    context = FaultContext(
        fault_code="E302",
        fault_phenomenon="真空压力不足，吸嘴抛料",
        device_model="SMT-X100"
    )
    
    print("检索查询:", agent._build_query(context))
    results = agent.retrieve(context)
    
    print(f"\n检索到 {len(results)} 条知识:")
    for r in results:
        print(f"  - {r['metadata'].get('source_file')} ({r['metadata'].get('doc_type')})")
