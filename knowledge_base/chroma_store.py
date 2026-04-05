"""
Chroma 向量数据库存储

提供文档向量化和检索功能
使用阿里百炼 Embedding API
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from pydantic import BaseModel

from config import settings


def get_embeddings_from_dashscope(texts: List[str]) -> List[List[float]]:
    """
    使用阿里百炼 API 获取文本嵌入向量
    
    Args:
        texts: 文本列表
    
    Returns:
        嵌入向量列表
    """
    from openai import OpenAI
    
    client = OpenAI(
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url
    )
    
    # 阿里百炼支持批量，但参数名为 texts
    response = client.embeddings.create(
        model=settings.dashscope_embedding_model,
        input=texts if len(texts) > 1 else texts[0]
    )
    
    return [item.embedding for item in response.data]


class DashScopeEmbeddingFunction:
    """Chroma 嵌入函数适配器 - 使用阿里百炼 API"""
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """调用嵌入函数"""
        return get_embeddings_from_dashscope(input)
    
    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """嵌入文档（用于 add）"""
        return get_embeddings_from_dashscope(documents)
    
    def embed_query(self, input: str, **kwargs) -> List[float]:
        """嵌入查询（用于 query）"""
        result = get_embeddings_from_dashscope([input])
        # 确保返回的是 List[float]
        embedding = result[0]
        if isinstance(embedding, float):
            return [embedding]
        return list(embedding)
    
    @staticmethod
    def name() -> str:
        """返回嵌入函数名称"""
        return "dashscope_embedding"


class RetrievedDocument(BaseModel):
    """检索到的文档"""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float


class ChromaStore:
    """Chroma 向量存储管理器"""
    
    def __init__(self, persist_dir: Optional[Path] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.chroma_path
        self.collection_name = collection_name or settings.chroma_collection_name
        
        # 初始化 Chroma 客户端
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
        
        # 获取或创建集合
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """获取或创建集合（使用阿里百炼 Embedding 函数）"""
        try:
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=DashScopeEmbeddingFunction()
            )
        except Exception:
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
                embedding_function=DashScopeEmbeddingFunction()
            )
        return collection
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """添加文档到向量数据库"""
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[RetrievedDocument]:
        """向量相似度检索"""
        # 使用阿里百炼 API 生成查询向量
        query_embedding = get_embeddings_from_dashscope([query_text])[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        
        return self._format_results(results)
    
    def hybrid_search(
        self,
        query_text: str,
        fault_code: Optional[str] = None,
        device_model: Optional[str] = None,
        n_results: int = 5
    ) -> List[RetrievedDocument]:
        """混合检索：向量检索 + Metadata 过滤"""
        # 使用阿里百炼 API 生成查询向量
        query_embedding = get_embeddings_from_dashscope([query_text])[0]
        
        # 构建过滤条件
        where_clause = {}
        if fault_code:
            where_clause["fault_code"] = fault_code
        if device_model:
            where_clause["device_model"] = device_model
        
        # 执行检索
        if where_clause:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause
            )
        else:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
        
        return self._format_results(results)
    
    def get_by_fault_code(
        self,
        fault_code: str,
        n_results: int = 10
    ) -> List[RetrievedDocument]:
        """按故障代码获取文档"""
        results = self.collection.get(
            where={"fault_code": fault_code},
            limit=n_results
        )
        
        docs = []
        for i, doc_id in enumerate(results["ids"]):
            docs.append(RetrievedDocument(
                doc_id=doc_id,
                content=results["documents"][i],
                metadata=results["metadatas"][i],
                similarity_score=1.0  # get 方法没有相似度分数
            ))
        return docs
    
    def _format_results(self, results: Dict) -> List[RetrievedDocument]:
        """格式化检索结果"""
        docs = []
        if not results["ids"]:
            return docs
        
        for i, doc_id in enumerate(results["ids"][0]):
            docs.append(RetrievedDocument(
                doc_id=doc_id,
                content=results["documents"][0][i],
                metadata=results["metadatas"][0][i],
                similarity_score=results["distances"][0][i] if "distances" in results else 0.0
            ))
        return docs
    
    def count(self) -> int:
        """获取文档总数"""
        return self.collection.count()
    
    def delete_all(self) -> None:
        """删除所有文档"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self._get_or_create_collection()
    
    def peek(self, n: int = 5) -> List[RetrievedDocument]:
        """查看前 n 个文档"""
        results = self.collection.peek(limit=n)
        
        docs = []
        for i, doc_id in enumerate(results["ids"]):
            docs.append(RetrievedDocument(
                doc_id=doc_id,
                content=results["documents"][i],
                metadata=results["metadatas"][i],
                similarity_score=1.0
            ))
        return docs
