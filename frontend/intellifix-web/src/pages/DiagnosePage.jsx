import { useState } from 'react'
import { Search, AlertTriangle, CheckCircle, Wrench, FileText, ArrowRight } from 'lucide-react'
import { diagnoseFault } from '../services/api'
import './DiagnosePage.css'

function DiagnosePage() {
  const [userInput, setUserInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!userInput.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await diagnoseFault(userInput)
      setResult(data)
    } catch (err) {
      setError('诊断失败: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const exampleInputs = [
    '3号线贴片机报警E302，吸嘴连续抛料，已停机5分钟',
    'SMT-X100真空值偏低，吸不住料',
    '贴片机过滤器堵塞，真空压力不足'
  ]

  return (
    <div className="diagnose-page">
      <header className="page-header">
        <h1><Wrench /> 故障诊断</h1>
        <p>输入设备故障描述，AI 将为您提供诊断建议和处置方案</p>
      </header>

      {/* 输入区域 */}
      <div className="input-section">
        <form onSubmit={handleSubmit} className="input-form">
          <div className="input-wrapper">
            <Search className="input-icon" />
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              placeholder="请描述故障现象，例如：3号线贴片机报警E302，吸嘴连续抛料..."
              rows={3}
            />
          </div>
          <button 
            type="submit" 
            className="submit-btn"
            disabled={loading || !userInput.trim()}
          >
            {loading ? '诊断中...' : '开始诊断'}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        {/* 示例输入 */}
        <div className="examples">
          <span>示例：</span>
          {exampleInputs.map((example, idx) => (
            <button
              key={idx}
              className="example-btn"
              onClick={() => setUserInput(example)}
            >
              {example.length > 20 ? example.substring(0, 20) + '...' : example}
            </button>
          ))}
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="error-message">
          <AlertTriangle />
          {error}
        </div>
      )}

      {/* 诊断结果 */}
      {result && result.data && (
        <div className="result-section">
          <DiagnosisResult data={result.data} />
        </div>
      )}
    </div>
  )
}

function DiagnosisResult({ data }) {
  const { fault_context, diagnosis, evidence_chain, escalation } = data

  return (
    <div className="diagnosis-result">
      {/* 故障信息卡片 */}
      {fault_context && (
        <div className="result-card fault-info">
          <h3><FileText size={20} /> 故障解析</h3>
          <div className="info-grid">
            <div className="info-item">
              <label>设备型号</label>
              <value>{fault_context.device_model || 'N/A'}</value>
            </div>
            <div className="info-item">
              <label>故障代码</label>
              <value className="fault-code">{fault_context.fault_code || 'N/A'}</value>
            </div>
            <div className="info-item">
              <label>产线位置</label>
              <value>{fault_context.production_line || 'N/A'}</value>
            </div>
            <div className="info-item">
              <label>停机状态</label>
              <value>{fault_context.is_stopped ? '已停机' : '运行中'}</value>
            </div>
          </div>
          <div className="phenomenon">
            <label>故障现象</label>
            <p>{fault_context.fault_phenomenon}</p>
          </div>
        </div>
      )}

      {/* 诊断结果卡片 */}
      {diagnosis && (
        <div className="result-card diagnosis-info">
          <h3><Wrench size={20} /> 诊断结果</h3>
          <div className="diagnosis-header">
            <span className="fault-name">{diagnosis.fault_name}</span>
            <span className={`risk-badge ${diagnosis.risk_level}`}>
              {diagnosis.risk_level}风险
            </span>
          </div>

          {/* 可能原因 */}
          <div className="section">
            <h4>可能原因排序</h4>
            <ul className="cause-list">
              {diagnosis.probable_causes?.map((cause, idx) => (
                <li key={idx} className={`cause-item ${cause.confidence}`}>
                  <span className="rank">{cause.rank}</span>
                  <span className="cause">{cause.cause}</span>
                  <span className={`confidence ${cause.confidence}`}>{cause.confidence}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* 排查步骤 */}
          <div className="section">
            <h4>推荐排查步骤</h4>
            <ol className="step-list">
              {diagnosis.recommended_steps?.map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ol>
          </div>

          {/* 建议备件 */}
          {diagnosis.spare_parts?.length > 0 && (
            <div className="section">
              <h4>建议备件</h4>
              <div className="spare-parts">
                {diagnosis.spare_parts.map((part, idx) => (
                  <span key={idx} className="part-tag">
                    {part.name} ({part.model})
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 升级建议 */}
      {escalation && escalation.should_escalate && (
        <div className="result-card escalation-warning">
          <h3><AlertTriangle size={20} /> 升级建议</h3>
          <p className="escalation-reason">{escalation.reason}</p>
          {escalation.suggested_expert_focus?.length > 0 && (
            <div className="expert-focus">
              <h4>建议专家关注点</h4>
              <ul>
                {escalation.suggested_expert_focus.map((focus, idx) => (
                  <li key={idx}>{focus}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {escalation && !escalation.should_escalate && (
        <div className="result-card success">
          <h3><CheckCircle size={20} /> 处理建议</h3>
          <p>当前故障可在现场处理，无需升级专家</p>
        </div>
      )}

      {/* 证据链 */}
      {evidence_chain?.items?.length > 0 && (
        <div className="result-card evidence-chain">
          <h3>证据链</h3>
          <div className="evidence-list">
            {evidence_chain.items.slice(0, 3).map((item, idx) => (
              <div key={idx} className="evidence-item">
                <p className="suggestion">{item.suggestion}</p>
                {item.source_docs?.length > 0 && (
                  <p className="sources">
                    来源: {item.source_docs.slice(0, 2).join(', ')}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default DiagnosePage
