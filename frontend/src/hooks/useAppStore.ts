import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Message, FileItem, ApiConfig, AnalysisSession, PanelView, WorkflowStep } from '../types'
import { PROVIDER_PRESETS, DEFAULT_WORKFLOW } from '../types'

interface AppState {
  // UI
  panelView: PanelView
  setPanelView: (view: PanelView) => void
  darkMode: boolean
  toggleDarkMode: () => void
  showResultPanel: boolean
  toggleResultPanel: () => void

  // Chat
  messages: Message[]
  addMessage: (msg: Message) => void
  updateLastAssistant: (content: string, reasoning?: string, tokenUsage?: Message['tokenUsage']) => void
  editMessage: (id: string, content: string) => void
  removeMessage: (id: string) => void
  clearMessages: () => void
  isStreaming: boolean
  setIsStreaming: (v: boolean) => void

  // Files
  files: FileItem[]
  addFile: (file: FileItem) => void
  removeFile: (id: string) => void

  // API
  apiConfig: ApiConfig
  setApiConfig: (config: Partial<ApiConfig>) => void

  // Sessions
  sessions: AnalysisSession[]
  activeSessionId: string | null
  createSession: (name?: string) => void
  switchSession: (id: string) => void
  deleteSession: (id: string) => void
  renameSession: (id: string, name: string) => void
  saveCurrentSession: () => void

  // System prompt
  systemPrompt: string
  setSystemPrompt: (prompt: string) => void

  // Workflow
  workflow: WorkflowStep[]
  updateWorkflowStep: (id: string, status: WorkflowStep['status']) => void
  resetWorkflow: () => void

  // Token tracking (session total)
  sessionTokens: number
  addTokens: (n: number) => void

  // Demo pipeline data
  demoLoaded: boolean
  loadDemoData: () => void
  runNewPipeline: (files?: string[]) => void
  demoStats: { samples: number; genes: number; degsTotal: number; enrichedPathways: number } | null
  pipeData: any  // full pipeline data from pipeline.json
}

const genId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`

const DEFAULT_AI = PROVIDER_PRESETS[0]

const DEFAULT_API_CONFIG: ApiConfig = {
  providerId: DEFAULT_AI.id,
  endpoint: DEFAULT_AI.endpoint,
  apiKey: '',
  model: DEFAULT_AI.models[0],
}

const DEFAULT_SYSTEM_PROMPT = `你是一个 RNA-seq 生信分析 Agent。你会自动调用工具 API 获取数据、绘制图表、解释结果。

## 可调用的工具（通过 URL 或代码调用）

### 图表工具（GET /api/chart/xxx 返回 PNG base64）
- volcano/<comp> — 火山图 (comp: MvsC|NvsC|MvsN)
- heatmap — 表达热图（top50 方差基因，M/C排序）
- pca — PCA 样本聚类（真实 SVD + 95% 置信椭圆）
- ma/<comp> — MA 图（真实 baseMean 从 DESeq2 读取）
- boxplot — 基因表达箱线图
- correlation — 样本相关性矩阵
- kegg/<comp> — KEGG 通路富集条形图
- go_string/<comp> — GO 富集 STRING API 实时查询
- go_dag_bp / go_dag_mf / go_dag_cc — GO BP/MF/CC 术语气泡图
- ppi — STRING PPI 网络图
- density — 表达密度分布
- saturation — 测序饱和度曲线
- kegg_pathway — KEGG 通路图（官方 PNG）
- venn — DEG 重叠统计
- qc_error / qc_gc / qc_filter / multi_qc — 质控图
- chrom_density / read_dist — 比对分布图
- gene_cov / insert — 基因覆盖度和插入片段

### 查询工具（返回 JSON 结构化数据）
- /api/query/degs?comp=MvsC&top=20 → 返回 top DEG 的基因名、LFC、padj
- /api/query/enrichment?comp=MvsC → 返回 KEGG 通路富集结果
- /api/query/stats → 返回项目统计（样本数、基因数、DEG数等）
- /api/query/qc?sample=C1 → 返回指定样本 QC 指标

### 药物靶点工具
- /api/targets?comp=MvsC&top=30 → 返回排序的候选药物靶点列表（综合 LFC、p-value 评分）

### 对比基准工具
- /api/benchmark → 返回与 RNA-SeqEZPZ/SeqExpressionAnalyser/IAN 的平台对比数据

### 操作工具
- /api/generate-report → 生成 PDF 分析报告
- /api/run → 执行你自己写的 Python matplotlib 代码

## 工作流程（ReAct 模式）
收到用户问题后：
1. **思考**：分析用户意图，确定需要哪些数据/图表
2. **行动**：调用一个或多个查询工具获取 JSON 数据，调用图表工具获取可视化
3. **解释**：用自然语言解释结果，引用具体数字（LFC、p值、基因数）
4. **追问**：根据分析结果，建议 2-3 个有意义的后续问题

## 图表自动优化规则
当编写 matplotlib 代码时，参数应从数据特征推导，不硬编码：
- volcano：xlim 用 abs(lfc) 的 p99*1.2；ylim 用 -log10(padj) 的 p99*1.1；s=max(2,15000/n)
- heatmap：vmin/vmax 用 zscore 的 p5/p95
- PCA：添加 95% 置信椭圆 (Ellipse)
- MA：显著点 zorder=10，非显著 alpha=0.15

## 项目数据
- 9 样本：C1-3 (Control), M1-3 (Treatment M), N1-3 (Treatment N)
- HISAT2 比对 GRCh38：94-95% overall
- 52,147 基因经 featureCounts 定量
- DESeq2 结果：MvsC 233 DEGs (|LFC|>1 & padj<0.05; 669 total padj<0.05), NvsC 157, MvsN 27
- KEGG 最显著通路：TNF signaling (p=6.8e-16), IL-17 (p=2.0e-13), Rheumatoid arthritis (p=3.9e-15)
- 数据路径：/home/yankai/rnaseq_pipeline/results/
- 图表 API 基础 URL：http://localhost:5173`



export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      panelView: 'chat',
      setPanelView: (view) => set({ panelView: view }),
      darkMode: false,
      toggleDarkMode: () => set((s) => ({ darkMode: !s.darkMode })),
      showResultPanel: false,
      toggleResultPanel: () => set((s) => ({ showResultPanel: !s.showResultPanel })),

      messages: [],
      addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
      updateLastAssistant: (content, reasoning, tokenUsage) =>
        set((s) => {
          const msgs = [...s.messages]
          const last = msgs[msgs.length - 1]
          if (last && last.role === 'assistant') {
            msgs[msgs.length - 1] = {
              ...last,
              content,
              ...(reasoning !== undefined ? { reasoning } : {}),
              ...(tokenUsage ? { tokenUsage } : {}),
            }
          }
          return { messages: msgs }
        }),
      editMessage: (id, content) =>
        set((s) => ({
          messages: s.messages.map((m) => (m.id === id ? { ...m, content } : m)),
        })),
      removeMessage: (id) =>
        set((s) => ({
          messages: s.messages.filter((m) => m.id !== id),
        })),
      clearMessages: () => set({ messages: [] }),
      isStreaming: false,
      setIsStreaming: (v) => set({ isStreaming: v }),

      files: [],
      addFile: (file) => set((s) => ({ files: [...s.files, file] })),
      removeFile: (id) => set((s) => ({ files: s.files.filter((f) => f.id !== id) })),

      apiConfig: { ...DEFAULT_API_CONFIG },
      setApiConfig: (config) => set((s) => ({ apiConfig: { ...s.apiConfig, ...config } })),

      sessions: [],
      activeSessionId: null,
      createSession: (name) => {
        const id = genId()
        const session: AnalysisSession = {
          id,
          name: name || `会话 ${get().sessions.length + 1}`,
          createdAt: Date.now(),
          messages: [],
          files: [],
          totalTokens: 0,
        }
        set((s) => ({
          sessions: [...s.sessions, session],
          activeSessionId: id,
          messages: [],
          files: [],
          panelView: 'chat',
          sessionTokens: 0,
          workflow: DEFAULT_WORKFLOW.map((w) => ({ ...w })),
        }))
      },
      switchSession: (id) => {
        const { sessions } = get()
        const session = sessions.find((s) => s.id === id)
        if (session) {
          set({
            activeSessionId: id,
            messages: [...session.messages],
            files: [...session.files],
            sessionTokens: session.totalTokens,
            panelView: 'chat',
          })
        }
      },
      deleteSession: (id) => {
        set((s) => {
          const sessions = s.sessions.filter((ses) => ses.id !== id)
          if (s.activeSessionId === id) {
            return {
              sessions,
              activeSessionId: sessions[0]?.id || null,
              messages: sessions[0]?.messages || [],
              files: sessions[0]?.files || [],
              sessionTokens: sessions[0]?.totalTokens || 0,
            }
          }
          return { sessions }
        })
      },
      renameSession: (id, name) =>
        set((s) => ({
          sessions: s.sessions.map((ses) => (ses.id === id ? { ...ses, name } : ses)),
        })),
      saveCurrentSession: () => {
        const { activeSessionId, messages, files, sessions, sessionTokens } = get()
        if (!activeSessionId) return
        set({
          sessions: sessions.map((s) =>
            s.id === activeSessionId
              ? { ...s, messages: [...messages], files: [...files], totalTokens: sessionTokens }
              : s
          ),
        })
      },

      systemPrompt: DEFAULT_SYSTEM_PROMPT,
      setSystemPrompt: (prompt) => set({ systemPrompt: prompt }),

      workflow: DEFAULT_WORKFLOW.map((w) => ({ ...w })),
      updateWorkflowStep: (id, status) =>
        set((s) => ({
          workflow: s.workflow.map((w) => (w.id === id ? { ...w, status } : w)),
        })),
      resetWorkflow: () => set({ workflow: DEFAULT_WORKFLOW.map((w) => ({ ...w })) }),

      sessionTokens: 0,
      addTokens: (n) => set((s) => ({ sessionTokens: s.sessionTokens + n })),

      demoLoaded: false,
      demoStats: null,
      pipeData: null,
      loadDemoData: () => {
        set({ demoLoaded: true, showResultPanel: true, panelView: 'chat' })
        const addMsg = (c: string) => useAppStore.getState().addMessage({
          id: `load-${Date.now()}-${Math.random().toString(36).slice(2,5)}`,
          role: 'assistant', content: c, timestamp: Date.now()
        })
        addMsg('⏳ 正在加载示例数据...')
        fetch('/pipeline.json').then(r => r.json()).then(d => {
          useAppStore.setState({ pipeData: d, demoStats: d.stats })
          d.steps.forEach((s: any) => useAppStore.getState().updateWorkflowStep(s.id, 'completed'))
          addMsg(`✅ **示例数据加载完成！**\n\n📊 9样本 | 52,147基因 | 1,256 DEGs | 15条KEGG通路\n\n输入命令:\n• \`比对\` — 比对统计\n• \`MvsC\` / \`NvsC\` — 差异基因\n• \`KEGG\` — 通路富集\n• \`报告\` — 完整报告`)
        }).catch(e => addMsg('❌ 加载失败: ' + e.message))
      },
      runNewPipeline: (files?: string[]) => {
        // Run real pipeline for new data via SSE
        set({ showResultPanel: true, panelView: 'chat', workflow: DEFAULT_WORKFLOW.map(w=>({...w})), demoLoaded: true, demoStats: null })
        const addMsg = (c: string) => useAppStore.getState().addMessage({
          id: `pipe-${Date.now()}-${Math.random().toString(36).slice(2,5)}`,
          role: 'assistant', content: c, timestamp: Date.now()
        })
        addMsg('🚀 **启动 RNA-seq 分析管线**')
        const body = files?.length ? JSON.stringify({ files }) : undefined
        fetch('/api/run-pipeline', {
          method: files?.length ? 'POST' : 'GET',
          headers: files?.length ? {'Content-Type':'application/json'} : undefined,
          body,
        }).then(async resp => {
          const reader = resp.body?.getReader()
          if (!reader) { addMsg('❌ 无法连接计算后端'); return }
          const decoder = new TextDecoder(); let buf = ''
          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            buf += decoder.decode(value, { stream: true })
            const lines = buf.split('\n'); buf = lines.pop() || ''
            for (const line of lines) {
              if (!line.startsWith('data:')) continue
              try {
                const evt = JSON.parse(line.slice(5))
                if (evt.step) useAppStore.getState().updateWorkflowStep(evt.step, 'completed')
                if (evt.msg) addMsg(evt.msg)
                if (evt.error) addMsg('❌ ' + evt.error)
              } catch {}
            }
          }
        }).catch(e => addMsg('❌ 管线失败: ' + e.message))
      },
    }),
    {
      name: 'rnaseq-platform-storage',
      partialize: (state) => ({
        sessions: state.sessions,
        apiConfig: state.apiConfig,
        darkMode: state.darkMode,
        systemPrompt: state.systemPrompt,
      }),
    }
  )
)
