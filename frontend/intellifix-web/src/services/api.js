import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 健康检查
export const checkHealth = async () => {
  const response = await axios.get('http://localhost:8000/health')
  return response.data
}

// 故障诊断
export const diagnoseFault = async (userInput, sessionId = null) => {
  const response = await api.post('/diagnose', {
    user_input: userInput,
    session_id: sessionId
  })
  return response.data
}

// 知识检索
export const retrieveKnowledge = async (query, faultCode = null, deviceModel = null, nResults = 5) => {
  const response = await api.post('/retrieve', {
    query,
    fault_code: faultCode,
    device_model: deviceModel,
    n_results: nResults
  })
  return response.data
}

// 获取知识库列表
export const getKnowledgeList = async (params = {}) => {
  const response = await api.get('/knowledge', { params })
  return response.data
}

// 获取知识文档详情
export const getKnowledgeDetail = async (docId) => {
  const response = await api.get(`/knowledge/${docId}`)
  return response.data
}

// 执行知识库入库
export const ingestKnowledge = async (clearExisting = false) => {
  const response = await api.post('/knowledge/ingest', {
    clear_existing: clearExisting
  })
  return response.data
}

// 获取统计信息
export const getStats = async () => {
  const response = await api.get('/stats')
  return response.data
}

export default api
