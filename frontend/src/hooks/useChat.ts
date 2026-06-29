import { useCallback, useRef } from 'react'
import { useAppStore } from './useAppStore'
import type { Message } from '../types'

function genId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function useChat() {
  const {
    messages, addMessage, updateLastAssistant, setIsStreaming,
    apiConfig, systemPrompt, files, saveCurrentSession, addTokens, sessionTokens,
    editMessage, removeMessage,
  } = useAppStore()
  const abortRef = useRef<AbortController | null>(null)
  const contentRef = useRef('')

  const buildContext = useCallback((): string => {
    if (files.length === 0) return ''
    return `\n\n[用户已指定的本地文件]\n${files.map((f) => `- ${f.name}: ${f.path} (${f.type})`).join('\n')}\n`
  }, [files])

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || useAppStore.getState().isStreaming) return

    const userMsg: Message = {
      id: genId(),
      role: 'user',
      content: content.trim(),
      timestamp: Date.now(),
    }
    addMessage(userMsg)

    const assistantMsg: Message = {
      id: genId(),
      role: 'assistant',
      content: '',
      timestamp: Date.now(),
    }
    addMessage(assistantMsg)

    setIsStreaming(true)
    abortRef.current = new AbortController()
    contentRef.current = ''

    const ctx = buildContext()
    const fullContent = ctx ? `${content}${ctx}` : content

    const payload = {
      model: apiConfig.model,
      messages: [
        { role: 'system', content: systemPrompt },
        ...useAppStore.getState().messages.filter((m) => m.role !== 'system').map((m) => ({ role: m.role, content: m.content })),
        { role: 'user', content: fullContent },
      ],
      stream: true,
    }

    let reasoningAcc = ''

    try {
      const resp = await fetch(apiConfig.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiConfig.apiKey}`,
        },
        body: JSON.stringify(payload),
        signal: abortRef.current.signal,
      })

      if (!resp.ok) {
        const errText = await resp.text().catch(() => 'Unknown error')
        throw new Error(`API 错误 (${resp.status}): ${errText.slice(0, 300)}`)
      }

      const reader = resp.body?.getReader()
      if (!reader) throw new Error('无法读取响应流')

      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6).trim()
          if (data === '[DONE]') continue

          try {
            const json = JSON.parse(data)
            const choice = json.choices?.[0]

            // DeepSeek reasoning_content
            const reasoningDelta = choice?.delta?.reasoning_content
            if (reasoningDelta) {
              reasoningAcc += reasoningDelta
              updateLastAssistant(contentRef.current, reasoningAcc)
            }

            // Normal content
            const delta = choice?.delta?.content
            if (delta) {
              contentRef.current += delta
              updateLastAssistant(contentRef.current, reasoningAcc || undefined)
            }

            // Token usage in final chunk
            const usage = json.usage
            if (usage?.total_tokens) {
              updateLastAssistant(contentRef.current, reasoningAcc || undefined, {
                prompt: usage.prompt_tokens || 0,
                completion: usage.completion_tokens || 0,
                total: usage.total_tokens,
              })
              addTokens(usage.total_tokens)
            }
          } catch {
            // skip malformed JSON lines
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        // Keep whatever content was streamed so far
        if (contentRef.current) {
          updateLastAssistant(contentRef.current, reasoningAcc || undefined)
        }
        return
      }
      updateLastAssistant(
        `**请求失败**: ${err.message || '未知错误'}\n\n请检查 API 配置和网络连接。`,
        reasoningAcc || undefined
      )
    } finally {
      setIsStreaming(false)
      abortRef.current = null
      saveCurrentSession()
    }
  }, [apiConfig, systemPrompt, files, addMessage, setIsStreaming, buildContext, saveCurrentSession, updateLastAssistant, addTokens])

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const resendMessage = useCallback((content: string) => {
    sendMessage(content)
  }, [sendMessage])

  const editAndResend = useCallback((messageId: string, newContent: string) => {
    // Remove the message and all subsequent messages, then resend
    const state = useAppStore.getState()
    const idx = state.messages.findIndex((m) => m.id === messageId)
    if (idx === -1) return
    // Remove from this message onwards
    const toRemove = state.messages.slice(idx).map((m) => m.id)
    toRemove.forEach((id) => removeMessage(id))
    sendMessage(newContent)
  }, [sendMessage, removeMessage])

  return { sendMessage, stopStreaming, resendMessage, editAndResend }
}
