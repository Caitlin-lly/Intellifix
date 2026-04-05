"""
智修Agent 配置管理
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 阿里百炼平台配置
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    dashscope_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1", alias="DASHSCOPE_BASE_URL")
    dashscope_embedding_model: str = Field(default="text-embedding-v4", alias="DASHSCOPE_EMBEDDING_MODEL")
    dashscope_llm_model: str = Field(default="qwen-plus", alias="DASHSCOPE_LLM_MODEL")
    
    # Chroma 配置
    chroma_persist_dir: str = Field(default="./chroma_db", alias="CHROMA_PERSIST_DIR")
    chroma_collection_name: str = Field(default="intellifix_kb", alias="CHROMA_COLLECTION_NAME")
    
    # 知识库配置
    documents_dir: str = Field(default="./documents", alias="DOCUMENTS_DIR")
    chunk_size: int = Field(default=500, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")
    
    # 应用配置
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # 诊断配置
    max_retrieval_docs: int = Field(default=5, alias="MAX_RETRIEVAL_DOCS")
    similarity_threshold: float = Field(default=0.7, alias="SIMILARITY_THRESHOLD")
    escalation_timeout_minutes: int = Field(default=15, alias="ESCALATION_TIMEOUT_MINUTES")
    
    class Config:
        # 支持从任意目录启动，自动定位项目根目录的 .env
        env_file = str(Path(__file__).parent / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"
    
    @property
    def project_root(self) -> Path:
        """项目根目录"""
        return Path(__file__).parent.absolute()
    
    @property
    def chroma_path(self) -> Path:
        """Chroma 数据存储路径"""
        path = self.project_root / self.chroma_persist_dir
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @property
    def docs_path(self) -> Path:
        """文档目录路径"""
        return self.project_root / self.documents_dir
    
    def validate(self) -> bool:
        """验证配置有效性"""
        if not self.dashscope_api_key:
            print("警告: DASHSCOPE_API_KEY 未设置，部分功能可能无法使用")
            return False
        return True


# 全局配置实例
settings = Settings()
