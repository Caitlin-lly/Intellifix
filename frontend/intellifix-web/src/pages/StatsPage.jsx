import { useState, useEffect } from 'react'
import { BarChart3, Activity, Database, AlertCircle } from 'lucide-react'
import { getStats, checkHealth } from '../services/api'
import './StatsPage.css'

function StatsPage() {
  const [stats, setStats] = useState(null)
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [statsData, healthData] = await Promise.all([
        getStats(),
        checkHealth()
      ])
      setStats(statsData)
      setHealth(healthData)
    } catch (err) {
      console.error('获取统计失败:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="stats-page loading">
        <div className="spinner"></div>
        <p>加载中...</p>
      </div>
    )
  }

  return (
    <div className="stats-page">
      <header className="page-header">
        <h1><BarChart3 /> 统计信息</h1>
        <p>系统运行状态和知识库统计</p>
      </header>

      {/* 系统状态卡片 */}
      {health && (
        <div className="stats-grid">
          <div className="stat-card status">
            <div className="stat-icon">
              <Activity size={24} />
            </div>
            <div className="stat-content">
              <label>系统状态</label>
              <value className={health.status === 'healthy' ? 'success' : 'error'}>
                {health.status === 'healthy' ? '正常运行' : '异常'}
              </value>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <Database size={24} />
            </div>
            <div className="stat-content">
              <label>知识库文档</label>
              <value>{health.kb_count || 0}</value>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <AlertCircle size={24} />
            </div>
            <div className="stat-content">
              <label>服务版本</label>
              <value>{health.version}</value>
            </div>
          </div>
        </div>
      )}

      {/* 知识库统计 */}
      {stats && (
        <div className="stats-sections">
          {/* 文档类型分布 */}
          {stats.doc_types && Object.keys(stats.doc_types).length > 0 && (
            <div className="stats-section">
              <h3>文档类型分布</h3>
              <div className="chart-bars">
                {Object.entries(stats.doc_types).map(([type, count]) => (
                  <div key={type} className="bar-item">
                    <label>{type}</label>
                    <div className="bar-wrapper">
                      <div 
                        className="bar"
                        style={{ 
                          width: `${(count / Math.max(...Object.values(stats.doc_types))) * 100}%` 
                        }}
                      />
                      <span className="bar-value">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 故障代码分布 */}
          {stats.fault_codes && Object.keys(stats.fault_codes).length > 0 && (
            <div className="stats-section">
              <h3>故障代码分布</h3>
              <div className="tag-cloud">
                {Object.entries(stats.fault_codes).map(([code, count]) => (
                  <span key={code} className="tag-item">
                    {code} ({count})
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 设备型号分布 */}
          {stats.device_models && Object.keys(stats.device_models).length > 0 && (
            <div className="stats-section">
              <h3>设备型号分布</h3>
              <div className="model-list">
                {Object.entries(stats.device_models).map(([model, count]) => (
                  <div key={model} className="model-item">
                    <span className="model-name">{model}</span>
                    <span className="model-count">{count} 个文档</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* API 信息 */}
      <div className="api-info">
        <h3>API 信息</h3>
        <div className="info-grid">
          <div className="info-row">
            <label>API 地址</label>
            <value>http://localhost:8000</value>
          </div>
          <div className="info-row">
            <label>API 文档</label>
            <value>
              <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
                Swagger UI (OpenAPI)
              </a>
            </value>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StatsPage
