import React, { useState } from 'react'
import { useAppStore } from '../hooks/useAppStore'
import type { FileItem } from '../types'

function genId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

function detectType(name: string): FileItem['type'] {
  const n = name.toLowerCase()
  if (n.endsWith('.fq.gz') || n.endsWith('.fastq.gz') || n.endsWith('.fq') || n.endsWith('.fastq')) return 'fastq'
  if (n.endsWith('.bam')) return 'bam'
  if (n.endsWith('.txt') || n.endsWith('.tsv')) return 'txt'
  if (n.endsWith('.csv')) return 'csv'
  if (n.endsWith('.gff') || n.endsWith('.gtf') || n.endsWith('.gff3')) return 'gff'
  return 'other'
}

export const FileSelector: React.FC = () => {
  const { files, addFile, removeFile } = useAppStore()
  const [name, setName] = useState('')
  const [path, setPath] = useState('')
  const [dragOver, setDragOver] = useState(false)

  const handleAdd = () => {
    if (!name.trim() || !path.trim()) return
    addFile({
      id: genId(),
      name: name.trim(),
      path: path.trim(),
      type: detectType(name),
    })
    setName('')
    setPath('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleAdd()
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = () => setDragOver(false)

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    // On Windows, drag-and-drop may expose file paths via dataTransfer
    const droppedFiles = e.dataTransfer.files
    if (droppedFiles.length > 0) {
      for (let i = 0; i < droppedFiles.length; i++) {
        const f = droppedFiles[i]
        const filePath = (f as any).path || f.name
        addFile({
          id: genId(),
          name: f.name,
          path: filePath,
          type: detectType(f.name),
        })
      }
    }
  }

  const typeLabel: Record<string, string> = {
    fastq: '📦 FASTQ', bam: '📊 BAM', txt: '📄 TXT',
    csv: '📈 CSV', gff: '🧬 GFF', other: '📎 其他',
  }

  return (
    <div className="file-selector">
      <h3>📁 分析文件</h3>
      <p className="hint">指定本地待分析文件的路径，Agent 将自动识别并处理。</p>

      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <div className="drop-hint">拖拽文件到此处，或手动输入路径</div>
      </div>

      <div className="file-input-row">
        <input
          className="input"
          placeholder="文件名（如 M1_1.clean.fq.gz）"
          value={name}
          onChange={(e) => setName(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <input
          className="input input-path"
          placeholder="完整路径（如 D:\HuNan\M1_1.clean.fq.gz）"
          value={path}
          onChange={(e) => setPath(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button className="btn btn-primary btn-sm" onClick={handleAdd}>添加</button>
      </div>

      {files.length > 0 && (
        <ul className="file-list">
          {files.map((f) => (
            <li key={f.id} className="file-item">
              <span className="file-type-badge">{typeLabel[f.type]}</span>
              <span className="file-name" title={f.path}>{f.name}</span>
              <span className="file-path" title={f.path}>{f.path}</span>
              <button className="btn-icon" onClick={() => removeFile(f.id)} title="移除">✕</button>
            </li>
          ))}
        </ul>
      )}

      {files.length === 0 && (
        <div className="empty-hint">尚未添加文件，添加后 Agent 将能看到这些文件信息。</div>
      )}
    </div>
  )
}
