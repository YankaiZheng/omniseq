import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { CodeBlock } from './CodeBlock'
import type { Message } from '../types'

interface Props {
  message: Message
  onEdit?: (id: string, content: string) => void
  onResend?: (content: string) => void
  onDeleteFrom?: (id: string) => void
  isLastUser?: boolean
}

export const MessageBubble: React.FC<Props> = ({
  message, onEdit, onResend, onDeleteFrom, isLastUser,
}) => {
  const isUser = message.role === 'user'
  const isAssistant = message.role === 'assistant'
  const [reasoningOpen, setReasoningOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(message.content)
  const [hover, setHover] = useState(false)

  const handleEditSubmit = () => {
    if (editValue.trim() && editValue !== message.content) {
      onEdit?.(message.id, editValue)
    }
    setEditing(false)
  }

  const handleEditKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleEditSubmit()
    }
    if (e.key === 'Escape') {
      setEditing(false)
      setEditValue(message.content)
    }
  }

  return (
    <div
      className={`message ${isUser ? 'message-user' : 'message-assistant'}`}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
    >
      <div className="message-avatar">
        {isUser ? '👤' : isAssistant ? '🤖' : '📋'}
      </div>
      <div className="message-content">
        <div className="message-role">
          {isUser ? '你' : isAssistant ? 'Agent' : '系统'}
          {message.tokenUsage && (
            <span className="token-badge" title={`Prompt: ${message.tokenUsage.prompt} | Completion: ${message.tokenUsage.completion}`}>
              {message.tokenUsage.total.toLocaleString()} tokens
            </span>
          )}
        </div>

        {/* Reasoning (DeepSeek) */}
        {message.reasoning && (
          <div className="reasoning-block">
            <button
              className="reasoning-toggle"
              onClick={() => setReasoningOpen(!reasoningOpen)}
            >
              {reasoningOpen ? '🔽' : '▶️'} 思考过程
            </button>
            {reasoningOpen && (
              <div className="reasoning-content">{message.reasoning}</div>
            )}
          </div>
        )}

        {/* Message body */}
        {editing ? (
          <div className="edit-area">
            <textarea
              className="edit-textarea"
              value={editValue}
              onChange={(e) => setEditValue(e.target.value)}
              onKeyDown={handleEditKeyDown}
              autoFocus
              rows={3}
            />
            <div className="edit-actions">
              <button className="btn btn-sm btn-primary" onClick={handleEditSubmit}>发送</button>
              <button className="btn btn-sm btn-outline" onClick={() => { setEditing(false); setEditValue(message.content) }}>取消</button>
            </div>
          </div>
        ) : (
          <div className={`message-body ${isAssistant ? 'markdown-body' : ''}`}>
            {isAssistant ? (
              <ReactMarkdown
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const isInline = !match && !String(children).includes('\n')
                    if (isInline) {
                      return <code className={className} {...props}>{children}</code>
                    }
                    return (
                      <CodeBlock
                        language={match?.[1]}
                        value={String(children).replace(/\n$/, '')}
                      />
                    )
                  },
                  img({ src, alt }) {
                    if (!src) return null
                    return (
                      <img
                        src={src}
                        alt={alt || '图片'}
                        style={{ maxWidth: '100%', borderRadius: '8px', margin: '8px 0', cursor: 'pointer' }}
                        onClick={() => window.open(src, '_blank')}
                        loading="lazy"
                      />
                    )
                  },
                }}
              >
                {message.content || '...'}
              </ReactMarkdown>
            ) : (
              <p>{message.content}</p>
            )}
          </div>
        )}

        <div className="message-footer">
          <span className="message-time">
            {new Date(message.timestamp).toLocaleTimeString('zh-CN')}
          </span>

          {/* Message actions */}
          {hover && !editing && (
            <span className="message-actions">
              {isUser && (
                <>
                  <button
                    className="action-btn"
                    title="编辑"
                    onClick={() => { setEditing(true); setEditValue(message.content) }}
                  >
                    ✏️
                  </button>
                  <button
                    className="action-btn"
                    title="重新发送"
                    onClick={() => onResend?.(message.content)}
                  >
                    🔄
                  </button>
                </>
              )}
              {isUser && isLastUser && (
                <button
                  className="action-btn"
                  title="从此处重新开始"
                  onClick={() => onDeleteFrom?.(message.id)}
                >
                  ↩️
                </button>
              )}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
