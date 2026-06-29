import React, { useEffect } from 'react'
import { Header } from './components/Header'
import { ChatPanel } from './components/ChatPanel'
import { FileSelector } from './components/FileSelector'
import { ApiConfigPanel } from './components/ApiConfig'
import { SessionHistory } from './components/SessionHistory'
import { ResultPanel } from './components/ResultPanel'
import { useAppStore } from './hooks/useAppStore'

const App: React.FC = () => {
  const { panelView, sessions, activeSessionId, createSession, darkMode, showResultPanel } = useAppStore()

  useEffect(() => {
    if (sessions.length === 0) {
      createSession()
    }
  }, [])

  useEffect(() => {
    document.documentElement.classList.toggle('dark', darkMode)
  }, [darkMode])

  return (
    <div className="app">
      <Header />
      <main className="app-main">
        {panelView === 'chat' && (
          <div className="chat-layout">
            <ChatPanel />
            {showResultPanel && <ResultPanel />}
          </div>
        )}
        {panelView === 'files' && <FileSelector />}
        {panelView === 'config' && <ApiConfigPanel />}
        {panelView === 'history' && <SessionHistory />}
      </main>
    </div>
  )
}

export default App
