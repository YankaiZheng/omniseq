import React from 'react'
import { useAppStore } from '../hooks/useAppStore'

export const Header: React.FC = () => {
  const {
    activeSessionId, sessions, panelView, setPanelView,
    createSession, darkMode, toggleDarkMode,
    loadDemoData, demoLoaded,
  } = useAppStore()
  const current = sessions.find((s) => s.id === activeSessionId)

  return (
    <header className="app-header">
      <div className="header-left">
        <span className="logo">🧬 生信分析平台</span>
        {current && (
          <span className="session-name" title={current.name}>
            {current.name}
          </span>
        )}
      </div>
      <nav className="header-nav">
        <button
          className={`nav-btn`}
          onClick={loadDemoData}
          style={{ color: demoLoaded ? 'var(--success)' : 'var(--warning)', fontWeight: 600 }}
          title="加载9样本RNA-seq示例分析结果"
        >
          🧪 {demoLoaded ? '示例已加载' : '示例分析'}
        </button>
        <button
          className={`nav-btn ${panelView === 'chat' ? 'active' : ''}`}
          onClick={() => setPanelView('chat')}
        >
          💬 对话
        </button>
        <button
          className={`nav-btn ${panelView === 'files' ? 'active' : ''}`}
          onClick={() => setPanelView('files')}
        >
          📁 文件
        </button>
        <button
          className={`nav-btn ${panelView === 'config' ? 'active' : ''}`}
          onClick={() => setPanelView('config')}
        >
          ⚙️ 配置
        </button>
        <button
          className={`nav-btn ${panelView === 'history' ? 'active' : ''}`}
          onClick={() => setPanelView('history')}
        >
          📋 历史
        </button>
        <button className="nav-btn new-session" onClick={() => createSession()}>
          ＋ 新建会话
        </button>
        <button className="nav-btn theme-toggle" onClick={toggleDarkMode} title={darkMode ? '切换亮色' : '切换暗色'}>
          {darkMode ? '☀️' : '🌙'}
        </button>
      </nav>
    </header>
  )
}
