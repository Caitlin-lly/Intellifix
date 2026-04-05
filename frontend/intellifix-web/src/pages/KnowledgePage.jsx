import { useState, useEffect } from 'react'
import { Database, Search, RefreshCw, FileText, Tag } from 'lucide-react'
import { getKnowledgeList, ingestKnowledge } from '../services/api'
import './KnowledgePage.css'

function KnowledgePage() {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [ingesting, setIngesting] = useState(false)
  const [filter, setFilter] = useState('')
  const [stats, setStats] = useState({ total: 0 })

  const fetchDocuments = async () => {
    setLoading(true)
    try {
      const data = await getKnowledgeList({ limit: 50 })
      setDocuments(data.documents || [])
      setStats({ total: data.total })
    } catch (err) {
      console.error('获取知识库失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleIngest = async () => {
    if (!confirm('确定要重新导入知识库吗？')) return
    
    setIngesting(true)
    try {
      const result = await ingestKnowledge(true)
      alert(result.message)
      fetchDocuments()
    } catch (err) {
      alert('导入失败: ' + err.message)
    } finally {
      setIngesting(false)
    }
  }

  useEffect(() => {
    fetchDocuments()
  }, [])

  const filteredDocs = documents.filter(doc => 
    doc.source_file?.toLowerCase().includes(filter.toLowerCase()) ||
    doc.fault_code?.toLowerCase().includes(filter.toLowerCase()) ||
    doc.doc_type?.toLowerCase().includes(filter.toLowerCase())
  )

  const docTypeColors = {
    '报警手册': '#ff6b6b',
    '维修SOP': '#4ecdc4',
    '专家经验': '#45b7d1',
    '历史工单': '#96ceb4',
    '备件资料': '#feca57',
    '安全规范': '#ff9ff3',
    '知识卡片': '#54a0ff'
  }

  return (
    <div className="knowledge-page">
      <header className="page-header">
        <h1><Database /> 知识库管理</h1>
        <p>管理系统中的知识文档，支持向量化检索</p>
      </header>

      {/* 工具栏 */}
      <div className="toolbar">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="搜索文档..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
        <div className="actions">
          <button 
            className="btn-secondary"
            onClick={fetchDocuments}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? 'spin' : ''} />
            刷新
          </button>
          <button 
            className="btn-primary"
            onClick={handleIngest}
            disabled={ingesting}
          >
            {ingesting ? '导入中...' : '重新导入'}
          </button>
        </div>
      </div>

      {/* 统计 */}
      <div className="stats-bar">
        <span>共 <strong>{stats.total}</strong> 个文档片段</span>
        <span>显示 <strong>{filteredDocs.length}</strong> 个</span>
      </div>

      {/* 文档列表 */}
      <div className="documents-grid">
        {filteredDocs.map((doc) => (
          <div key={doc.doc_id} className="document-card">
            <div className="doc-header">
              <FileText size={20} />
              <span 
                className="doc-type-badge"
                style={{ backgroundColor: docTypeColors[doc.doc_type] || '#ccc' }}
              >
                {doc.doc_type}
              </span>
            </div>
            <h4 className="doc-title">{doc.source_file}</h4>
            <div className="doc-meta">
              {doc.fault_code && (
                <span className="meta-item">
                  <Tag size={12} />
                  {doc.fault_code}
                </span>
              )}
              {doc.device_model && (
                <span className="meta-item">{doc.device_model}</span>
              )}
            </div>
            <p className="doc-preview">{doc.content_preview}</p>
            {doc.tags?.length > 0 && (
              <div className="doc-tags">
                {doc.tags.map((tag, idx) => (
                  <span key={idx} className="tag">{tag}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredDocs.length === 0 && !loading && (
        <div className="empty-state">
          <Database size={48} />
          <p>暂无知识文档</p>
          <button className="btn-primary" onClick={handleIngest}>
            导入知识库
          </button>
        </div>
      )}
    </div>
  )
}

export default KnowledgePage
