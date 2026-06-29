import React, { useState, useRef, useEffect } from 'react'
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter'
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs'

interface Props {
  language?: string
  value: string
}

const PLOT_KW = ['matplotlib', 'plt.', 'seaborn', 'sns.', 'ggplot', 'geom_']

function isPlot(value: string): boolean {
  return PLOT_KW.some(kw => value.toLowerCase().includes(kw))
}

export const CodeBlock: React.FC<Props> = ({ language, value }) => {
  const [copied, setCopied] = useState(false)
  const [image, setImage] = useState<string | null>(null)
  const [imgLoading, setImgLoading] = useState(false)
  const [imgError, setImgError] = useState<string | null>(null)
  const showPlot = (language === 'python' || language === 'r' || language === 'R') && isPlot(value)
  const timerRef = useRef<ReturnType<typeof setTimeout>>()
  const lastValRef = useRef('')

  // Track value changes and schedule plot run after code stabilizes
  if (showPlot && !image && !imgLoading && value !== lastValRef.current) {
    lastValRef.current = value
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => {
      setImgLoading(true)
      setImgError(null)
      fetch('/run-plot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: value }),
      })
        .then(r => r.json())
        .then(d => {
          if (d.success && d.image) setImage(d.image)
          else setImgError(d.error || 'fail')
        })
        .catch(e => setImgError(e.message))
        .finally(() => setImgLoading(false))
    }, 500)  // Wait 500ms of no code changes
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // If image is ready, show it instead of code
  if (image) {
    return (
      <div className="code-block">
        <div className="code-header">
          <span className="code-lang">📊 绘图结果</span>
          <div className="code-header-right">
            <button className="copy-btn" onClick={() => {
              const a = document.createElement('a'); a.href = image; a.download = 'plot.png'; a.click()
            }}>💾 下载</button>
            <button className="copy-btn" onClick={() => setImage(null)} style={{marginLeft: 4}}>📝 显示代码</button>
          </div>
        </div>
        <img src={image} alt="Plot" style={{ display: 'block', maxWidth: '100%', maxHeight: '600px', margin: '0 auto', padding: '12px' }} />
      </div>
    )
  }

  // Loading state
  if (imgLoading) {
    return (
      <div className="code-block">
        <div className="code-header">
          <span className="code-lang">{language || 'text'}</span>
          <button className="copy-btn" onClick={handleCopy}>{copied ? 'Copied' : 'Copy'}</button>
        </div>
        <SyntaxHighlighter language={language || 'text'} style={atomOneDark}
          customStyle={{ margin: 0, borderRadius: '0', fontSize: 13, lineHeight: 1.5, opacity: 0.6 }}>
          {value}
        </SyntaxHighlighter>
        <div style={{ padding: '20px', textAlign: 'center', color: '#888', fontSize: 13 }}>
          <div className="plot-spinner" style={{ margin: '0 auto 10px' }} />
          Generating plot...
        </div>
      </div>
    )
  }

  return (
    <div className="code-block">
      <div className="code-header">
        <span className="code-lang">{language || 'text'}</span>
        <button className="copy-btn" onClick={handleCopy}>
          {copied ? '✅ 已复制' : '📋 复制'}
        </button>
      </div>
      <SyntaxHighlighter
        language={language || 'text'}
        style={atomOneDark}
        customStyle={{
          margin: 0,
          borderRadius: showPlot ? '0' : '0 0 8px 8px',
          fontSize: 13,
          lineHeight: 1.5,
        }}
      >
        {value}
      </SyntaxHighlighter>
      {imgError && <div style={{ padding: '10px', color: '#dc3545', fontSize: 12 }}>Error: {imgError}</div>}
      {showPlot && isPlot(value) && !image && !imgLoading && (
        <button className="run-plot-btn" onClick={() => { setImage(null); setImgError(null); }}>
          📊 运行绘图
        </button>
      )}
    </div>
  )
}
