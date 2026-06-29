import React from 'react'
import { useAppStore } from '../hooks/useAppStore'

export const SessionHistory: React.FC = () => {
  const { sessions, activeSessionId, switchSession, deleteSession, createSession } = useAppStore()

  return (
    <div className="session-history">
      <h3>📋 历史会话</h3>

      {sessions.length === 0 && (
        <div className="empty-hint">暂无历史会话，点击上方「新建会话」开始。</div>
      )}

      <ul className="session-list">
        {sessions.map((s) => (
          <li
            key={s.id}
            className={`session-item ${s.id === activeSessionId ? 'active' : ''}`}
            onClick={() => switchSession(s.id)}
          >
            <span className="session-name">{s.name}</span>
            <span className="session-meta">
              {s.messages.length} 条消息 · {new Date(s.createdAt).toLocaleString('zh-CN')}
            </span>
            <button
              className="btn-icon"
              onClick={(e) => { e.stopPropagation(); deleteSession(s.id) }}
              title="删除会话"
            >
              🗑
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
