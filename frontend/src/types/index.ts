export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  reasoning?: string
  timestamp: number
  tokenUsage?: TokenUsage
}

export interface TokenUsage {
  prompt: number
  completion: number
  total: number
}

export interface FileItem {
  id: string
  name: string
  path: string
  type: 'fastq' | 'bam' | 'txt' | 'csv' | 'gff' | 'other'
  size?: string
}

export interface ProviderPreset {
  id: string
  name: string
  endpoint: string
  models: string[]
  apiKeyHint: string
  requiresKey: boolean
  description: string
}

export interface ApiConfig {
  providerId: string
  endpoint: string
  apiKey: string
  model: string
}

export interface AnalysisSession {
  id: string
  name: string
  createdAt: number
  messages: Message[]
  files: FileItem[]
  totalTokens: number
}

export interface WorkflowStep {
  id: string
  label: string
  description: string
  status: 'pending' | 'active' | 'completed' | 'skipped'
  icon: string
}

export type PanelView = 'chat' | 'files' | 'config' | 'history'

export const PROVIDER_PRESETS: ProviderPreset[] = [
  {
    id: 'deepseek',
    name: 'DeepSeek',
    endpoint: 'https://api.deepseek.com/v1/chat/completions',
    models: ['deepseek-chat', 'deepseek-reasoner'],
    apiKeyHint: 'sk-...',
    requiresKey: true,
    description: 'DeepSeek 官方 API',
  },
  {
    id: 'openai',
    name: 'OpenAI',
    endpoint: 'https://api.openai.com/v1/chat/completions',
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'o1', 'o3-mini'],
    apiKeyHint: 'sk-...',
    requiresKey: true,
    description: 'OpenAI 官方 API',
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    endpoint: 'https://api.anthropic.com/v1/messages',
    models: ['claude-sonnet-4-6', 'claude-opus-4-1', 'claude-haiku-4-5'],
    apiKeyHint: 'sk-ant-...',
    requiresKey: true,
    description: 'Anthropic（需用兼容代理）',
  },
  {
    id: 'google',
    name: 'Google Gemini',
    endpoint: 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
    models: ['gemini-2.5-flash', 'gemini-2.5-pro'],
    apiKeyHint: 'AIza...',
    requiresKey: true,
    description: 'Google AI Studio',
  },
  {
    id: 'groq',
    name: 'Groq',
    endpoint: 'https://api.groq.com/openai/v1/chat/completions',
    models: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it', 'deepseek-r1-distill-llama-70b'],
    apiKeyHint: 'gsk_...',
    requiresKey: true,
    description: 'Groq 高通量推理（免费额度）',
  },
  {
    id: 'siliconflow',
    name: 'SiliconFlow',
    endpoint: 'https://api.siliconflow.cn/v1/chat/completions',
    models: ['deepseek-ai/DeepSeek-V3', 'Qwen/Qwen2.5-72B-Instruct', 'Pro/Qwen/Qwen2.5-7B-Instruct'],
    apiKeyHint: 'sk-...',
    requiresKey: true,
    description: '国产平台',
  },
  {
    id: 'ollama',
    name: 'Ollama (本地)',
    endpoint: 'http://localhost:11434/v1/chat/completions',
    models: ['llama3', 'qwen2.5', 'deepseek-r1:8b', 'codellama'],
    apiKeyHint: 'ollama（可不填）',
    requiresKey: false,
    description: '本地运行，无需 Key',
  },
  {
    id: 'custom',
    name: '自定义',
    endpoint: '',
    models: [],
    apiKeyHint: '',
    requiresKey: false,
    description: '任意 OpenAI 兼容接口',
  },
]

export const DEFAULT_WORKFLOW: WorkflowStep[] = [
  { id: 'data', label: '数据准备', description: '指定 FASTQ/BAM 文件路径', status: 'pending', icon: '📁' },
  { id: 'qc', label: '质量控制', description: 'FastQC 质量评估', status: 'pending', icon: '🔍' },
  { id: 'align', label: '序列比对', description: 'HISAT2/STAR 比对到参考基因组', status: 'pending', icon: '🧬' },
  { id: 'quant', label: '基因定量', description: 'featureCounts 表达矩阵', status: 'pending', icon: '📊' },
  { id: 'deg', label: '差异分析', description: 'DESeq2 差异表达基因筛选', status: 'pending', icon: '🔥' },
  { id: 'enrich', label: '富集分析', description: 'GO/KEGG/GSEA 功能注释', status: 'pending', icon: '📈' },
  { id: 'vis', label: '可视化', description: '火山图/热图/PCA 图', status: 'pending', icon: '🎨' },
  { id: 'report', label: '生成报告', description: 'HTML/PDF 分析报告', status: 'pending', icon: '📋' },
]
