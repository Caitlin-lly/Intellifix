"""
文档入库脚本

将 Markdown 文档导入 Chroma 向量数据库
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import settings
from knowledge_base.document_loader import DocumentLoader
from knowledge_base.chroma_store import ChromaStore


def ingest_documents(documents_dir: Path = None, clear_existing: bool = False) -> int:
    """
    将文档导入向量数据库
    
    Args:
        documents_dir: 文档目录，默认使用配置中的路径
        clear_existing: 是否清空现有数据
    
    Returns:
        导入的文档片段数量
    """
    # 初始化
    docs_dir = documents_dir or settings.docs_path
    loader = DocumentLoader(docs_dir)
    store = ChromaStore()
    
    print(f"📁 文档目录: {docs_dir}")
    print(f"💾 Chroma 存储: {settings.chroma_path}")
    
    # 清空现有数据（可选）
    if clear_existing:
        print("🗑️  清空现有数据...")
        store.delete_all()
    
    # 加载所有文档
    print("📖 加载文档...")
    chunks = loader.load_all()
    print(f"✅ 加载完成: {len(chunks)} 个文档片段")
    
    if not chunks:
        print("⚠️  没有找到文档，请检查 documents 目录")
        return 0
    
    # 准备数据
    documents = []
    metadatas = []
    ids = []
    
    for chunk in chunks:
        documents.append(chunk.content)
        metadatas.append({
            "source_file": chunk.metadata.source_file,
            "doc_type": chunk.metadata.doc_type,
            "device_model": chunk.metadata.device_model or "",
            "fault_code": chunk.metadata.fault_code or "",
            "tags": ",".join(chunk.metadata.tags),
            "version": chunk.metadata.version
        })
        ids.append(chunk.chunk_id)
    
    # 使用阿里百炼 API 生成向量并存储
    print("🔮 使用阿里百炼 API 生成向量并存储...")
    print(f"   模型: {settings.dashscope_embedding_model}")
    
    # 分批处理，避免 API 限制
    batch_size = 10
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_meta = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        store.add_documents(batch_docs, batch_meta, batch_ids)
        print(f"   已处理 {min(i+batch_size, len(documents))}/{len(documents)}...")
    
    
    # 统计
    total = store.count()
    print(f"✅ 导入完成！当前共有 {total} 个文档片段")
    
    # 显示统计信息
    _show_stats(store)
    
    return len(chunks)


def _show_stats(store: ChromaStore):
    """显示统计信息"""
    print("\n📊 知识库统计:")
    
    # 查看部分文档
    samples = store.peek(n=3)
    for doc in samples:
        print(f"\n  📄 {doc.metadata.get('source_file', 'Unknown')}")
        print(f"     类型: {doc.metadata.get('doc_type', 'Unknown')}")
        print(f"     设备: {doc.metadata.get('device_model', 'N/A')}")
        print(f"     故障: {doc.metadata.get('fault_code', 'N/A')}")


def test_retrieval():
    """测试检索功能"""
    store = ChromaStore()
    
    print("\n🔍 测试检索功能:")
    
    # 测试 1: 按故障代码检索
    print("\n1. 按故障代码 E302 检索:")
    results = store.get_by_fault_code("E302", n_results=3)
    for r in results:
        print(f"   - {r.metadata.get('source_file')}: {r.metadata.get('doc_type')}")
    
    # 测试 2: 向量检索
    print("\n2. 向量检索 '真空压力不足':")
    results = store.query("真空压力不足", n_results=3)
    for r in results:
        print(f"   - {r.metadata.get('source_file')}: 相似度 {r.similarity_score:.3f}")
    
    # 测试 3: 混合检索
    print("\n3. 混合检索 '吸嘴堵塞':")
    results = store.hybrid_search(
        query_text="吸嘴堵塞",
        fault_code="E302",
        n_results=3
    )
    for r in results:
        print(f"   - {r.metadata.get('source_file')}: 相似度 {r.similarity_score:.3f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="知识库文档入库工具")
    parser.add_argument("--clear", action="store_true", help="清空现有数据")
    parser.add_argument("--test", action="store_true", help="测试检索功能")
    
    args = parser.parse_args()
    
    if args.test:
        test_retrieval()
    else:
        count = ingest_documents(clear_existing=args.clear)
        
        if count > 0:
            print("\n" + "="*50)
            test_retrieval()
