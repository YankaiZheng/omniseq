import React from 'react'
import { useAppStore } from '../hooks/useAppStore'
import { PROVIDER_PRESETS } from '../types'

export const ApiConfigPanel: React.FC = () => {
  const { apiConfig, setApiConfig, systemPrompt, setSystemPrompt } = useAppStore()

  const currentProvider = PROVIDER_PRESETS.find((p) => p.id === apiConfig.providerId)

  const handleProviderChange = (providerId: string) => {
    const preset = PROVIDER_PRESETS.find((p) => p.id === providerId)
    if (!preset) return
    setApiConfig({
      providerId,
      endpoint: preset.endpoint,
      model: preset.models[0] || '',
    })
  }

  return (
    <div className="api-config">
      <h3>⚙️ Agent API 配置</h3>
      <p className="hint">选择 AI 提供商并配置连接信息。支持 OpenAI 兼容接口。</p>

      <div className="config-section">
        <label className="label">AI 提供商</label>
        <div className="provider-grid">
          {PROVIDER_PRESETS.map((p) => (
            <button
              key={p.id}
              className={`provider-card ${apiConfig.providerId === p.id ? 'active' : ''}`}
              onClick={() => handleProviderChange(p.id)}
              title={p.description}
            >
              <span className="provider-name">{p.name}</span>
              <span className="provider-desc">{p.description}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="config-section">
        <label className="label">
          API 端点
          {currentProvider && (
            <span className="label-tag">{currentProvider.name}</span>
          )}
        </label>
        <input
          className="input"
          placeholder="https://api.deepseek.com/v1/chat/completions"
          value={apiConfig.endpoint}
          onChange={(e) => setApiConfig({ endpoint: e.target.value })}
        />
        {currentProvider && !currentProvider.requiresKey && (
          <span className="hint-sm">本地服务无需 API Key</span>
        )}
      </div>

      <div className="config-section">
        <label className="label">API Key</label>
        <input
          className="input"
          type="password"
          placeholder={currentProvider?.apiKeyHint || 'sk-...'}
          value={apiConfig.apiKey}
          onChange={(e) => setApiConfig({ apiKey: e.target.value })}
        />
        <span className="hint-sm">密钥仅存储在浏览器本地，不会上传</span>
      </div>

      <div className="config-section">
        <label className="label">模型名称</label>
        {currentProvider && currentProvider.models.length > 0 ? (
          <div className="model-select-row">
            <select
              className="input select"
              value={apiConfig.model}
              onChange={(e) => setApiConfig({ model: e.target.value })}
            >
              {currentProvider.models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
            <input
              className="input"
              placeholder="或手动输入模型名"
              value={currentProvider.models.includes(apiConfig.model) ? '' : apiConfig.model}
              onChange={(e) => setApiConfig({ model: e.target.value })}
            />
          </div>
        ) : (
          <input
            className="input"
            placeholder="输入模型名称..."
            value={apiConfig.model}
            onChange={(e) => setApiConfig({ model: e.target.value })}
          />
        )}
      </div>

      <h3 style={{ marginTop: 24 }}>🧠 系统提示词</h3>
      <p className="hint">自定义 Agent 的角色和行为指令。</p>
      <textarea
        className="input textarea"
        rows={8}
        value={systemPrompt}
        onChange={(e) => setSystemPrompt(e.target.value)}
      />

      <div className="config-status">
        {apiConfig.apiKey || (currentProvider && !currentProvider.requiresKey) ? (
          <span className="status-ok">
            ✅ {currentProvider?.name} — 已就绪
          </span>
        ) : (
          <span className="status-warn">
            ⚠️ 请填写 {currentProvider?.name} 的 API Key
          </span>
        )}
      </div>
    </div>
  )
}
