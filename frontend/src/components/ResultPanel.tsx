import React from 'react'
import { useAppStore } from '../hooks/useAppStore'
import { degData } from '../data/pipelineData'

const statusIcons: Record<string, string> = { pending: '⏳', active: '🔄', completed: '✅', skipped: '⏭️' }

export const ResultPanel: React.FC = () => {
  const { workflow, updateWorkflowStep, resetWorkflow, sessionTokens, files, messages, demoLoaded, demoStats } = useAppStore()
  const completed = workflow.filter((w) => w.status === 'completed').length
  const progress = workflow.length > 0 ? Math.round((completed / workflow.length) * 100) : 0
  const assistantMsgs = messages.filter((m) => m.role === 'assistant' && m.content)

  return (
    <div className="result-panel">
      <div className="result-header"><h3>📊 分析概览</h3></div>

      {demoLoaded && demoStats && (
        <>
          <div className="result-section">
            <h4 className="section-title">管线结果 <span style={{fontSize:10,color:'var(--warning)',marginLeft:4}}>示例数据</span></h4>
            <div className="stats-grid">
              <div className="stat-card"><span className="stat-value">{demoStats.samples}</span><span className="stat-label">样本数</span></div>
              <div className="stat-card"><span className="stat-value">{demoStats.genes}</span><span className="stat-label">定量基因</span></div>
              <div className="stat-card"><span className="stat-value">{demoStats.degsTotal}</span><span className="stat-label">总 DEGs</span></div>
              <div className="stat-card"><span className="stat-value">{demoStats.enrichedPathways}</span><span className="stat-label">KEGG 通路</span></div>
            </div>
          </div>
          <div className="result-section">
            <h4 className="section-title">差异基因</h4>
            {Object.entries(degData).map(([name, d]) => (
              <div key={name} style={{marginBottom:6,fontSize:11}}>
                <b>{name}</b>: {d.total} <span style={{color:'var(--danger)'}}>↑{d.up}</span> <span style={{color:'var(--success)'}}>↓{d.down}</span>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Progress */}
      <div className="result-section">
        <div className="progress-header">
          <span>工作流进度</span>
          <span className="progress-pct">{progress}%</span>
        </div>
        <div className="progress-bar">
          <div className="progress-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>

      {/* Workflow Checklist */}
      <div className="result-section">
        <h4 className="section-title">分析步骤</h4>
        <ul className="workflow-list">
          {workflow.map((step) => (
            <li
              key={step.id}
              className={`workflow-step ${step.status}`}
              onClick={() => {
                const next: Record<string, string> = {
                  pending: 'active',
                  active: 'completed',
                  completed: 'skipped',
                  skipped: 'pending',
                }
                updateWorkflowStep(step.id, next[step.status] as any)
              }}
            >
              <span className="step-icon">{step.icon}</span>
              <span className="step-status">{statusIcons[step.status]}</span>
              <div className="step-info">
                <span className="step-label">{step.label}</span>
                <span className="step-desc">{step.description}</span>
              </div>
            </li>
          ))}
        </ul>
        <button className="btn btn-sm btn-outline reset-btn" onClick={resetWorkflow}>
          重置工作流
        </button>
      </div>

      {/* Stats */}
      <div className="result-section">
        <h4 className="section-title">会话统计</h4>
        <div className="stats-grid">
          <div className="stat-card">
            <span className="stat-value">{files.length}</span>
            <span className="stat-label">关联文件</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{messages.length}</span>
            <span className="stat-label">消息数</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{sessionTokens.toLocaleString()}</span>
            <span className="stat-label">总 Token</span>
          </div>
          <div className="stat-card">
            <span className="stat-value">{assistantMsgs.length}</span>
            <span className="stat-label">AI 回复</span>
          </div>
        </div>
      </div>
    </div>
  )
}
