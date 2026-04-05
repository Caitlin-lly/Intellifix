"""
文档加载器

负责加载 Markdown 文档并提取元数据
"""
import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    """文档元数据"""
    source_file: str
    doc_type: str = "未知"
    device_model: Optional[str] = None
    fault_code: Optional[str] = None
    tags: List[str] = []
    version: str = "v1.0"


class DocumentChunk(BaseModel):
    """文档片段"""
    content: str
    metadata: DocumentMetadata
    chunk_id: str


class DocumentLoader:
    """Markdown 文档加载器"""
    
    def __init__(self, documents_dir: Path):
        self.documents_dir = documents_dir
    
    def load_all(self) -> List[DocumentChunk]:
        """加载所有文档"""
        chunks = []
        md_files = list(self.documents_dir.glob("*.md"))
        
        for md_file in md_files:
            file_chunks = self._load_file(md_file)
            chunks.extend(file_chunks)
        
        return chunks
    
    def _load_file(self, file_path: Path) -> List[DocumentChunk]:
        """加载单个文件"""
        content = file_path.read_text(encoding="utf-8")
        metadata = self._extract_metadata(content, file_path.name)
        
        # 按标题层级切分文档
        sections = self._split_by_headers(content)
        
        chunks = []
        for idx, section in enumerate(sections):
            chunk_id = f"{file_path.stem}_{idx}"
            chunk = DocumentChunk(
                content=section,
                metadata=metadata,
                chunk_id=chunk_id
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_metadata(self, content: str, filename: str) -> DocumentMetadata:
        """从文档内容提取元数据"""
        metadata = DocumentMetadata(source_file=filename)
        
        # 提取文档类型（从文件名）
        doc_type_map = {
            "ALARM": "报警手册",
            "SOP": "维修SOP",
            "FAQ": "专家经验",
            "WO": "历史工单",
            "PARTS": "备件资料",
            "SAFE": "安全规范",
            "CARD": "知识卡片",
            "INDEX": "知识清单",
        }
        
        for key, value in doc_type_map.items():
            if key in filename.upper():
                metadata.doc_type = value
                break
        
        # 从文件名提取设备型号和故障代码
        # 格式: AS-MFG-KB-{TYPE}-{MODEL}-{CODE}-{DESC}-v{VERSION}.md
        pattern = r'AS-MFG-KB-\w+-(\w+)-(\w+)-'
        match = re.search(pattern, filename)
        if match:
            metadata.device_model = match.group(1)
            metadata.fault_code = match.group(2)
        
        # 从内容提取标签
        tags_match = re.search(r'标签[：:]\s*(.+)', content)
        if tags_match:
            tags_str = tags_match.group(1)
            metadata.tags = [t.strip() for t in tags_str.split(',')]
        
        # 从内容提取设备型号（如果文件名没有）
        if not metadata.device_model:
            device_match = re.search(r'设备型号[：:]\s*(\S+)', content)
            if device_match:
                metadata.device_model = device_match.group(1)
        
        # 从内容提取故障代码（如果文件名没有）
        if not metadata.fault_code:
            fault_match = re.search(r'故障代码[：:]\s*(\S+)', content)
            if fault_match:
                metadata.fault_code = fault_match.group(1)
        
        return metadata
    
    def _split_by_headers(self, content: str) -> List[str]:
        """按 Markdown 标题切分文档"""
        # 按二级标题切分
        pattern = r'(?=\n##\s+)'
        sections = re.split(pattern, content)
        
        # 清理并过滤空片段
        sections = [s.strip() for s in sections if s.strip()]
        
        # 如果文档较短，不切分
        if len(sections) <= 1:
            return [content.strip()]
        
        return sections
    
    def get_document_by_type(self, doc_type: str) -> List[DocumentChunk]:
        """按文档类型获取文档"""
        all_docs = self.load_all()
        return [d for d in all_docs if d.metadata.doc_type == doc_type]
    
    def get_document_by_fault_code(self, fault_code: str) -> List[DocumentChunk]:
        """按故障代码获取文档"""
        all_docs = self.load_all()
        return [d for d in all_docs if d.metadata.fault_code == fault_code]
