"""
智修Agent - FastAPI 后端服务

提供 RESTful API 接口供前端调用
"""
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.graph import IntelliFixAgent
from knowledge_base.chroma_store import ChromaStore
from knowledge_base.document_loader import DocumentLoader
from config import settings

# 创建 FastAPI 应用
app = FastAPI(
    title="智修Agent API",
    description="制造业设备故障诊断 Multi-Agent 系统 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 Agent 实例
agent = IntelliFixAgent()
chroma_store = ChromaStore()

# ============ 数据模型 ============

class DiagnoseRequest(BaseModel):
    """诊断请求"""
    user_input: str = Field(..., description="用户输入的故障描述")
    session_id: Optional[str] = Field(None, description="会话ID")


class DiagnoseResponse(BaseModel):
    """诊断响应"""
    success: bool
    session_id: str
    data: Dict[str, Any]
    timestamp: str


class KnowledgeDoc(BaseModel):
    """知识文档"""
    doc_id: str
    source_file: str
    doc_type: str
    device_model: Optional[str]
    fault_code: Optional[str]
    tags: List[str]
    content_preview: str


class KnowledgeListResponse(BaseModel):
    """知识列表响应"""
    total: int
    documents: List[KnowledgeDoc]


class RetrieveRequest(BaseModel):
    """检索请求"""
    query: str
    fault_code: Optional[str] = None
    device_model: Optional[str] = None
    n_results: int = 5


class RetrieveResponse(BaseModel):
    """检索响应"""
    query: str
    results: List[Dict[str, Any]]
    total: int


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    version: str
    timestamp: str
    kb_count: int


class IngestRequest(BaseModel):
    """入库请求"""
    clear_existing: bool = False


class IngestResponse(BaseModel):
    """入库响应"""
    success: bool
    message: str
    document_count: int
    timestamp: str


# ============ API 路由 ============

@app.get("/", tags=["根路径"])
async def root():
    """根路径"""
    return {
        "service": "智修Agent API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["健康检查"])
async def health_check():
    """健康检查"""
    return HealthResponse(
        status="healthy",
        service="智修Agent",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
        kb_count=chroma_store.count()
    )


@app.post("/api/v1/diagnose", response_model=DiagnoseResponse, tags=["故障诊断"])
async def diagnose(request: DiagnoseRequest):
    """
    执行故障诊断
    
    - **user_input**: 故障描述，例如 "3号线贴片机报警E302，吸嘴连续抛料"
    - **session_id**: 可选的会话ID，用于追踪
    """
    try:
        # 生成会话ID
        session_id = request.session_id or str(uuid.uuid4())[:8]
        
        # 执行诊断
        report = agent.diagnose(request.user_input)
        
        return DiagnoseResponse(
            success=True,
            session_id=session_id,
            data=report,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/retrieve", response_model=RetrieveResponse, tags=["知识检索"])
async def retrieve_knowledge(request: RetrieveRequest):
    """
    检索知识库
    
    - **query**: 检索查询
    - **fault_code**: 可选的故障代码过滤
    - **device_model**: 可选的设备型号过滤
    - **n_results**: 返回结果数量
    """
    try:
        results = chroma_store.hybrid_search(
            query_text=request.query,
            fault_code=request.fault_code,
            device_model=request.device_model,
            n_results=request.n_results
        )
        
        return RetrieveResponse(
            query=request.query,
            results=[
                {
                    "doc_id": r.doc_id,
                    "content": r.content[:500] + "..." if len(r.content) > 500 else r.content,
                    "metadata": r.metadata,
                    "similarity_score": r.similarity_score
                }
                for r in results
            ],
            total=len(results)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge", response_model=KnowledgeListResponse, tags=["知识库管理"])
async def list_knowledge(
    fault_code: Optional[str] = None,
    doc_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """
    获取知识库文档列表
    
    - **fault_code**: 按故障代码过滤
    - **doc_type**: 按文档类型过滤
    - **skip**: 分页偏移
    - **limit**: 每页数量
    """
    try:
        # 从 Chroma 获取文档
        if fault_code:
            results = chroma_store.get_by_fault_code(fault_code, n_results=limit)
        else:
            results = chroma_store.peek(n=limit)
        
        # 过滤文档类型
        if doc_type:
            results = [r for r in results if r.metadata.get("doc_type") == doc_type]
        
        documents = []
        for r in results[skip:skip+limit]:
            metadata = r.metadata
            documents.append(KnowledgeDoc(
                doc_id=r.doc_id,
                source_file=metadata.get("source_file", "Unknown"),
                doc_type=metadata.get("doc_type", "Unknown"),
                device_model=metadata.get("device_model") or None,
                fault_code=metadata.get("fault_code") or None,
                tags=metadata.get("tags", "").split(",") if metadata.get("tags") else [],
                content_preview=r.content[:200] + "..." if len(r.content) > 200 else r.content
            ))
        
        return KnowledgeListResponse(
            total=len(results),
            documents=documents
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/knowledge/{doc_id}", tags=["知识库管理"])
async def get_knowledge_detail(doc_id: str):
    """获取知识文档详情"""
    try:
        # 这里简化处理，实际应该从 Chroma 查询特定ID
        results = chroma_store.peek(n=100)
        for r in results:
            if r.doc_id == doc_id:
                return {
                    "doc_id": r.doc_id,
                    "content": r.content,
                    "metadata": r.metadata
                }
        
        raise HTTPException(status_code=404, detail="文档不存在")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/knowledge/ingest", response_model=IngestResponse, tags=["知识库管理"])
async def ingest_knowledge(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    执行知识库文档入库
    
    - **clear_existing**: 是否清空现有数据
    """
    try:
        from knowledge_base.ingest import ingest_documents
        
        # 在后台执行入库
        count = ingest_documents(clear_existing=request.clear_existing)
        
        return IngestResponse(
            success=True,
            message=f"成功导入 {count} 个文档片段",
            document_count=count,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/stats", tags=["统计信息"])
async def get_stats():
    """获取系统统计信息"""
    try:
        # 获取文档统计
        total_docs = chroma_store.count()
        
        # 获取样本文档分析类型分布
        samples = chroma_store.peek(n=min(50, total_docs))
        
        doc_types = {}
        fault_codes = {}
        device_models = {}
        
        for r in samples:
            metadata = r.metadata
            
            # 统计文档类型
            doc_type = metadata.get("doc_type", "Unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            # 统计故障代码
            fault_code = metadata.get("fault_code")
            if fault_code:
                fault_codes[fault_code] = fault_codes.get(fault_code, 0) + 1
            
            # 统计设备型号
            device_model = metadata.get("device_model")
            if device_model:
                device_models[device_model] = device_models.get(device_model, 0) + 1
        
        return {
            "total_documents": total_docs,
            "doc_types": doc_types,
            "fault_codes": fault_codes,
            "device_models": device_models,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 启动服务 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
