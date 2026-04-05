import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { Wrench, Database, BarChart3, Home } from 'lucide-react'
import DiagnosePage from './pages/DiagnosePage'
import KnowledgePage from './pages/KnowledgePage'
import StatsPage from './pages/StatsPage'
import './App.css'

function App() {
  return (
    <Router>
      <div className="app">
        {/* 侧边导航 */}
        <nav className="sidebar">
          <div className="logo">
            <Wrench size={32} />
            <h1>智修Agent</h1>
          </div>
          <ul className="nav-links">
            <li>
              <Link to="/" className="nav-link">
                <Home size={20} />
                <span>故障诊断</span>
              </Link>
            </li>
            <li>
              <Link to="/knowledge" className="nav-link">
                <Database size={20} />
                <span>知识库</span>
              </Link>
            </li>
            <li>
              <Link to="/stats" className="nav-link">
                <BarChart3 size={20} />
                <span>统计信息</span>
              </Link>
            </li>
          </ul>
          <div className="version">v1.0.0</div>
        </nav>

        {/* 主内容区 */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<DiagnosePage />} />
            <Route path="/knowledge" element={<KnowledgePage />} />
            <Route path="/stats" element={<StatsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
