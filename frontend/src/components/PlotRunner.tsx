import React, { useState, useEffect } from 'react'

interface Props {
  code: string
  language?: string
  onImageReady?: (imageUrl: string) => void
}

const PLOT_KEYWORDS = ['matplotlib', 'plt.', 'seaborn', 'sns.', 'plotly', 'ggplot', 'geom_']

function isPlotCode(code: string): boolean {
  return PLOT_KEYWORDS.some((kw) => code.toLowerCase().includes(kw))
}

export const PlotRunner: React.FC<Props> = ({ code, language, onImageReady }) => {
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<{ image?: string; error?: string } | null>(null)
  const [expanded, setExpanded] = useState(false)

  // Auto-run plotting code once when detected in AI messages
  useEffect(() => {
    if (isPlotCode(code) && !running && !result) {
      handleRun()
    }
  }, [code])

  const handleRun = async () => {
    setRunning(true)
    setResult(null)
    setExpanded(true)
    try {
      const resp = await fetch('/run-plot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      })
      const data = await resp.json()
      if (data.success && data.image) {
        setResult(data)
        onImageReady?.(data.image)
      } else {
        setResult(data)
      }
    } catch (e: any) {
      setResult({ error: e.message })
    } finally {
      setRunning(false)
    }
  }

  if (!isPlotCode(code) && !expanded) return null

  return (
    <div className="plot-result">
      <div className="plot-result-header">
        <span>📊 绘图输出</span>
        <div className="plot-result-actions">
          {result?.image && (
            <button className="plot-action-btn" onClick={() => {
              const link = document.createElement('a')
              link.href = result.image!
              link.download = 'plot.png'
              link.click()
            }} title="下载图片">💾</button>
          )}
          <button className="plot-action-btn" onClick={() => setExpanded(false)} title="收起">✕</button>
        </div>
      </div>
      {running && (
        <div className="plot-loading">
          <div className="plot-spinner" />
          <span>正在执行绘图代码...</span>
        </div>
      )}
      {result?.image && (
        <img src={result.image!} alt="绘图结果" className="plot-image" />
      )}
      {result?.error && (
        <div className="plot-error">
          <strong>绘图错误:</strong>
          <pre>{result.error}</pre>
        </div>
      )}
      {!running && !result && (
        <button className="run-plot-btn" onClick={handleRun}>📊 运行绘图</button>
      )}
    </div>
  )
}
