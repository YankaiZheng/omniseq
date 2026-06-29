import React, { useState, useRef, useCallback } from 'react'
import { useAppStore } from '../hooks/useAppStore'

declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}

export const VoiceInput: React.FC<{ onResult: (text: string) => void }> = ({ onResult }) => {
  const [listening, setListening] = useState(false)
  const [interim, setInterim] = useState('')
  const recognitionRef = useRef<any>(null)

  const getRecognition = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return null
    const rec = new SpeechRecognition()
    rec.lang = 'zh-CN'
    rec.interimResults = true
    rec.continuous = false
    rec.maxAlternatives = 1
    return rec
  }, [])

  const startListening = useCallback(() => {
    const rec = getRecognition()
    if (!rec) {
      alert('您的浏览器不支持语音输入，请使用 Chrome 或 Edge。')
      return
    }

    recognitionRef.current = rec
    setListening(true)
    setInterim('')

    rec.onresult = (event: any) => {
      let final = ''
      let interimText = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          final += result[0].transcript
        } else {
          interimText += result[0].transcript
        }
      }
      if (final) {
        onResult(final)
        setListening(false)
        setInterim('')
      }
      if (interimText) {
        setInterim(interimText)
      }
    }

    rec.onerror = (event: any) => {
      console.warn('语音识别错误:', event.error)
      if (event.error === 'no-speech' || event.error === 'aborted') {
        // silent
      } else {
        setInterim(`识别失败: ${event.error}`)
      }
      setListening(false)
    }

    rec.onend = () => {
      setListening(false)
      recognitionRef.current = null
    }

    try {
      rec.start()
    } catch {
      setListening(false)
    }
  }, [getRecognition, onResult])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    setListening(false)
    setInterim('')
  }, [])

  const handleToggle = () => {
    if (listening) {
      stopListening()
    } else {
      startListening()
    }
  }

  return (
    <div className="voice-input">
      {interim && listening && (
        <div className="voice-interim">{interim}</div>
      )}
      <button
        className={`voice-btn ${listening ? 'listening' : ''}`}
        onClick={handleToggle}
        title={listening ? '停止录音' : '语音输入'}
        type="button"
      >
        {listening ? (
          <span className="voice-pulse">🎤</span>
        ) : (
          <span>🎙️</span>
        )}
      </button>
    </div>
  )
}
