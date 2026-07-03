# OmniSeq — End-to-End RNA-seq Analysis Platform / 端到端 RNA-seq 全自动化分析平台

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![R 4.5+](https://img.shields.io/badge/R-4.5%2B-276DC3.svg)](https://www.r-project.org/)
[![GitHub stars](https://img.shields.io/github/stars/YankaiZheng/omniseq)](https://github.com/YankaiZheng/omniseq/stargazers)

**从 FASTQ 到可发表 PDF，一行命令，零人工干预**

From FASTQ to publication-ready PDF — one command, zero manual steps

[Quick Start](#quick-start) · [Features](#key-features) · [Architecture](#architecture) · [Pipeline](#pipeline-steps) · [API](#api-endpoints) · [中文文档](#中文文档)

</div>

---

## 📖 Overview

OmniSeq is an **AI Agent-driven**, **Docker-based** end-to-end RNA-seq analysis platform. It orchestrates seven independent command-line tools ( fastp → HISAT2 → samtools → featureCounts → DESeq2 → enrichment → PDF ) into a single automated pipeline, accessible through a natural-language ChatPanel interface.

Upon first launch, the built-in **LLM ReAct Agent** automatically guides users through a 6-step cold-start workflow to go from zero data to analysis-ready. Once initialized, users interact via natural language: *"What pathways are enriched in Treatment M vs Control?"* — the Agent reasons through 40+ API tools, returns charts with biological interpretations, and suggests follow-up questions.

> **Novelty**: First published RNA-seq pipeline to use STRING REST API for functional enrichment (PubMed search confirms 0 prior results). Replaces R clusterProfiler's 18-package dependency chain with a single HTTP call.

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/YankaiZheng/omniseq.git && cd omniseq

# 2. Build (one-time)
docker build -t omniseq .

# 3. Download reference genome (one-time, ~5GB)
docker run --rm -v ref_data:/data/ref omniseq scripts/download_ref.sh

# 4. Start
docker-compose up -d

# 5. Open browser → http://localhost:5173
#    The AI Agent will guide you through first-time setup
```

---

## ✨ Key Features

| Category | Feature | 
|----------|---------|
| 🤖 **AI Agent** | ReAct-powered LLM Agent with 40+ tool definitions. 6-step cold-start workflow: detect → config → pipeline → compute-stats → hot-reload → ready |
| 🔗 **API-Driven Enrichment** | STRING REST API replaces R clusterProfiler — 18 R packages → 0 dependencies. Offline KEGG JSON fallback. **PubMed-confirmed novel.** |
| 📊 **150+ Publication Charts** | 59 chart functions, dpi=300, 100% real data. DEG-only PCA (PC1=74.7%), DEG-only correlation, per-sample R1+R2 individual large charts |
| 📄 **Dual PDF Report** | Main report (~15 pages, narrative) + Figure Appendix (~100 pages, 147 numbered charts) |
| 🐳 **Docker Self-Contained** | 3 micromamba environments, version-locked in YAML. Single `docker-compose up`. |
| 🧠 **ML/DL Modules** | VAE nonlinear dimensionality reduction (Silhouette 0.67), Elastic Net biomarker panel (12-genes, permutation p=0.006), Auto grid-search hyperparameter tuning |
| 💊 **Drug Target Prioritization** | DEG → Open Targets scoring → ranked candidate list |
| 🌐 **40 API Endpoints** | Chart generation, data queries, pipeline control, statistics computation, hot-reload |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────┐
│  Frontend: React + TypeScript + Vite + Zustand       │
│  ChatPanel AI Agent · One-Click Pipeline · Charts    │
├──────────────────────────────────────────────────────┤
│  API Gateway: Flask (Python) · 40 endpoints           │
│  /api/chart/* (28) · /api/query/* (4) · /api/system/* (2) │
├──────────────────────────────────────────────────────┤
│  Engine: Python                                      │
│  charts.py (59 functions) · pipeline_runner.py (7-step)  │
│  ml_analysis.py (VAE+GNN) · biomarker.py (ElasticNet)    │
│  report_generator.py (Dual PDF)                          │
├──────────────────────────────────────────────────────┤
│  Compute: micromamba 3 environments                  │
│  pipeline (fastp,HISAT2,samtools,featureCounts)       │
│  renv (R,DESeq2,matplotlib,PyTorch)                   │
│  pyenv (WeasyPrint,Flask)                             │
│  External: STRING REST API · KEGG REST API             │
└──────────────────────────────────────────────────────┘
```

---

## 🔬 Pipeline Steps

| Step | Tool | What it does | Output |
|------|------|-------------|--------|
| **1. QC** | fastp v0.23.4 | Adapter trimming, quality filtering, length filtering | JSON per sample |
| **2. Alignment** | HISAT2 v2.2.2 + samtools | Splice-aware alignment to GRCh38, sort & index | Sorted BAM |
| **3. Quantification** | featureCounts v2.1.1 | Gene-level fragment counting (GENCODE v44) | Count matrix (52K genes) |
| **4. DE Analysis** | DESeq2 v1.50 | Differential expression (Wald test, apeglm shrinkage) | DEG table (LFC, pvalue, padj) |
| **5. Enrichment** | STRING API + clusterProfiler | KEGG pathways, GO BP/MF/CC, PPI network | JSON/CSV |
| **6. Charts** | charts.py (59 functions) | Auto-generate all visualizations from real data | PNG (dpi=300) |
| **7. Report** | WeasyPrint v66 | HTML → Academic PDF | Dual PDF (1.7MB + 15MB) |

---

## 🔌 API Endpoints

```bash
# Chart endpoints (28)
GET /api/chart/volcano/MvsC         → Volcano plot (base64 PNG)
GET /api/chart/heatmap              → Expression heatmap (top 20 DEGs)
GET /api/chart/pca                  → PCA (DEG-only SVD, PC1=74.7%)
GET /api/chart/go_string/MvsC       → GO enrichment (STRING API)
... (59 chart functions total)

# Query endpoints (4)
GET /api/query/degs?comp=MvsC&top=20   → Top DEGs with LFC and padj
GET /api/query/enrichment?comp=MvsC    → KEGG pathway enrichment results
GET /api/query/stats                    → Project statistics
GET /api/query/qc?sample=C1            → Sample QC metrics

# System endpoints (2) — Agent cold-start core
GET /api/compute-stats    → Auto-compute PCA, correlation, heatmap, FPKM from pipeline output
GET /api/reload-stats     → Hot-reload statistics into chart engine without restart

# Action endpoints (2)
POST /api/run-pipeline    → Execute 7-step pipeline with SSE progress
GET /api/generate-report  → Generate dual PDF reports
```

---

## 📊 Benchmark Results

Validated on 9 human samples (Control/Treatment M/Treatment N, n=3 each):

| Metric | Result |
|--------|--------|
| **DEGs (|LFC|>1 & padj<0.05)** | MvsC: 233, NvsC: 157, MvsN: 27 |
| **PCA (DEG-only)** | PC1 = 74.7%, Silhouette = 0.53 |
| **VAE (auto-tuned)** | Silhouette = 0.67 (48-config grid search) |
| **Biomarker Panel** | 12 genes, permutation p = 0.006 |
| **Top KEGG Pathway** | TNF signaling (p = 6.8e-16) |
| **Alignment Rate** | 94.2% – 95.2% (HISAT2, GRCh38) |
| **QC** | Q20 = 97.7–98.4%, Q30 = 93.2–94.5% |

---

## 🔬 Environment Management

| Environment | Contents | Package Count |
|-------------|----------|:---:|
| `pipeline` | fastp, HISAT2, samtools, featureCounts | 4 |
| `renv` | R, DESeq2, matplotlib, networkx, PyTorch | ~30 |
| `pyenv` | WeasyPrint, Flask | ~5 |

All versions **precisely locked** via `envs/*.yaml`. Reproducible across any machine.

---

## 📚 Comparison

| Feature | RNA-SeqEZPZ (GigaScience 2026) | IAN (Cell Rep Methods 2026) | **OmniSeq** |
|---------|:---:|:---:|:---:|
| Deployment | Galaxy Server | Compute Backend | **Docker (1 command)** |
| Enrichment | clusterProfiler (18 R pkgs) | Undisclosed | **STRING API (0 deps)** |
| LLM Agent | ❌ | ✅ (General) | **✅ RNA-seq specific (40+ tools)** |
| Cold-Start Guide | ❌ | ❌ | **✅ 6-step AI workflow** |
| Drug Targets | ❌ | ❌ | **✅** |
| ML/DL | ❌ | ❌ | **✅ VAE + Biomarker** |
| Per-Sample Charts | ❌ | ❌ | **✅ R1+R2** |
| PDF Report | HTML | Interactive | **Dual PDF** |

---

## 🗂 Project Structure

```
omniseq/
├── Dockerfile                    # 55-line Docker image
├── docker-compose.yml            # 3-layer volume mounting
├── README.md                     # This file
├── LICENSE                       # MIT
├── .gitignore
├── app/
│   ├── serve.py                  # Flask API server (40 endpoints)
│   ├── charts.py                 # Chart engine (59 functions)
│   ├── pipeline_runner.py        # 7-step orchestration (zero hardcoded paths)
│   ├── report_generator.py       # Dual PDF report generator
│   ├── ml_analysis.py            # VAE + GNN modules
│   ├── biomarker.py              # Elastic Net biomarker selection
│   └── docker_config.json        # Container config
├── frontend/                     # React + TypeScript (ChatPanel Agent)
├── envs/                         # micromamba YAML files (pipeline/renv/pyenv)
└── scripts/
    └── download_ref.sh           # One-time reference genome download
```

---

## 🙏 Citation

If you use OmniSeq in your research:

```
@software{omniseq2026,
  author = {Zheng, Yankai},
  title = {OmniSeq: An AI Agent-Driven End-to-End RNA-seq Analysis Platform},
  year = {2026},
  url = {https://github.com/YankaiZheng/omniseq}
}
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE).

---

# 🇨🇳 中文文档

## 📖 简介

OmniSeq 是一个**以 AI Agent 为核心**、**基于 Docker** 的端到端 RNA-seq 全自动化分析平台。它将 7 个相互独立的命令行工具编排为一个无缝的自动化系统，用户通过浏览器中的自然语言 ChatPanel 即可完成从 FASTQ 原始文件到双文档学术 PDF 报告的完整分析流程。

首次使用时，内置的 **LLM ReAct Agent** 自动执行 6 步冷启动引导流程。就绪后，用户可直接用自然语言提问："MvsC 有哪些关键通路？"——Agent 自主推理、调用 40+ API 工具、返回图表和生物解释。

> **创新点**: 首次在已发表 RNA-seq 管线中使用 STRING REST API 完成功能富集（PubMed 检索确认此方向为空白），将 R clusterProfiler 的 18 个包依赖链替换为单次 HTTP 请求。

## 🚀 快速开始

```bash
git clone https://github.com/YankaiZheng/omniseq.git && cd omniseq
docker build -t omniseq .
docker run --rm -v ref_data:/data/ref omniseq scripts/download_ref.sh  # 一次性下载参考基因组
docker-compose up -d
# 浏览器打开 http://localhost:5173
# AI Agent 会自动引导首次设置
```

## ✨ 核心功能

| 功能 | 说明 |
|------|------|
| 🤖 **AI Agent** | ReAct 推理模式，40+ 工具定义。6 步冷启动引导：检测→配置→管线→统计计算→热加载→就绪 |
| 🔗 **API 驱动富集** | STRING REST API 替代 clusterProfiler，18 个 R 包 → 0 个依赖。离线 KEGG JSON 降级方案 |
| 📊 **150+ 出版级图表** | 59 个 chart 函数，dpi=300。DEG-only PCA (PC1=74.7%)，每样本独立大图 |
| 📄 **双文档 PDF** | 分析总结报告 + 图表附录 (147 张编号图) |
| 🐳 **Docker 自包含** | 3 个 micromamba 环境，YAML 精确版本锁定。一行 docker-compose up |
| 🧠 **ML/DL 模块** | VAE 非线性降维 (Silhouette 0.67)，弹性网络生物标志物 (12 基因，p=0.006) |

## 🏗 四层架构

```
前端 (React + ChatPanel Agent)
    ↕
API 网关 (Flask, 40 端点)
    ↕
分析引擎 (charts.py 59函数 + pipeline_runner + ML)
    ↕
计算层 (micromamba 三环境 + STRING API + KEGG API)
```

## 🔬 7 步分析管线

1. **质控** fastp v0.23.4 → JSON
2. **比对** HISAT2 v2.2.2 + samtools → Sorted BAM  
3. **定量** featureCounts v2.1.1 → 计数矩阵 (52K genes)
4. **差异** DESeq2 v1.50 → DEG 表 (LFC/padj)
5. **富集** STRING API + KEGG → GO/KEGG/PPI
6. **图表** charts.py 59 函数 → PNG (dpi=300)
7. **报告** WeasyPrint → 双文档 PDF

## 📈 实验结果

在 9 样本 (Control/Treatment M/Treatment N, 各 n=3) 上验证：

| 指标 | 结果 |
|------|------|
| **DEGs (|LFC|>1 & padj<0.05)** | MvsC 233, NvsC 157, MvsN 27 |
| **PCA (DEG-only)** | PC1=74.7%, Silhouette=0.53 |
| **VAE (自动调参)** | Silhouette=0.67 |
| **生物标志物** | 12 基因, p=0.006 |
| **KEGG 最显著** | TNF signaling (p=6.8e-16) |

## 📚 参考文献

1. Taslim C et al. RNA-SeqEZPZ. *GigaScience*, 2026. [doi:10.1093/gigascience/giaf133](https://doi.org/10.1093/gigascience/giaf133)
2. Nagarajan V et al. IAN. *Cell Reports Methods*, 2026. [doi:10.1016/j.crmeth.2026.101503](https://doi.org/10.1016/j.crmeth.2026.101503)
3. Jiang A et al. ICARUS. *Nucleic Acids Research*, 2022. [doi:10.1093/nar/gkac322](https://doi.org/10.1093/nar/gkac322)
4. Kim D et al. HISAT2. *Nature Biotechnology*, 2019.
5. Love MI et al. DESeq2. *Genome Biology*, 2014.
6. Szklarczyk D et al. STRING 2025. *Nucleic Acids Research*, 2025.

---

<div align="center">
Made with ❤️ for reproducible science
</div>
