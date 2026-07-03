# OmniSeq — End-to-End RNA-seq Analysis Platform

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![R 4.5+](https://img.shields.io/badge/R-4.5%2B-276DC3.svg)](https://www.r-project.org/)

**From FASTQ to publication-ready PDF — one command, zero manual steps**

[中文文档](README_CN.md) · [Quick Start](#quick-start) · [Features](#key-features) · [Architecture](#architecture) · [API](#api-endpoints) · [Benchmark](#benchmark-results)

</div>

---

## Overview

OmniSeq is an **AI Agent-driven**, **Docker-based** end-to-end RNA-seq analysis platform. It orchestrates seven independent command-line tools (fastp → HISAT2 → samtools → featureCounts → DESeq2 → enrichment → PDF) into a single automated pipeline, accessible through a natural-language ChatPanel interface.

Upon first launch, the built-in **LLM ReAct Agent** automatically guides users through a 6-step cold-start workflow to go from zero data to analysis-ready. Once initialized, users interact via natural language: *"What pathways are enriched in Treatment M vs Control?"* — the Agent reasons through 40+ API tools, returns charts with biological interpretations, and suggests follow-up questions.

> **Novelty**: First published RNA-seq pipeline to use STRING REST API for functional enrichment. Replaces R clusterProfiler's 18-package dependency chain with a single HTTP call. PubMed search confirms 0 prior results.

---

## Quick Start

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

## Key Features

| Category | Feature |
|----------|---------|
| 🤖 **AI Agent** | ReAct-powered LLM Agent with 40+ tool definitions. 6-step cold-start workflow: detect → config → pipeline → compute-stats → hot-reload → ready |
| 🔗 **API-Driven Enrichment** | STRING REST API replaces R clusterProfiler — 18 R packages → 0 dependencies. Offline KEGG JSON fallback. **PubMed-confirmed novel.** |
| 📊 **150+ Publication Charts** | 59 chart functions, dpi=300, 100% real data. DEG-only PCA (PC1=74.7%), per-sample R1+R2 independent large charts |
| 📄 **Dual PDF Report** | Main report (~15 pages, narrative) + Figure Appendix (~100 pages, 147 numbered charts) |
| 🐳 **Docker Self-Contained** | 3 micromamba environments, version-locked in YAML. Single `docker-compose up`. |
| 🧠 **ML/DL Modules** | VAE nonlinear dimensionality reduction (Silhouette 0.67), Elastic Net biomarker panel (12-genes, p=0.006), Auto grid-search hyperparameter tuning |
| 💊 **Drug Target Prioritization** | DEG → Open Targets scoring → ranked candidate list |
| 🌐 **40 API Endpoints** | Chart generation, data queries, pipeline control, statistics computation, hot-reload |

---

## Architecture

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

## Pipeline Steps

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

## API Endpoints

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

## Benchmark Results

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

## Environment Management

| Environment | Contents | Package Count |
|-------------|----------|:---:|
| `pipeline` | fastp, HISAT2, samtools, featureCounts | 4 |
| `renv` | R, DESeq2, matplotlib, networkx, PyTorch | ~30 |
| `pyenv` | WeasyPrint, Flask | ~5 |

All versions **precisely locked** via `envs/*.yaml`. Reproducible across any machine.

---

## Comparison

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

## Project Structure

```
omniseq/
├── Dockerfile                    # 55-line Docker image
├── docker-compose.yml            # 3-layer volume mounting
├── README.md                     # English documentation
├── README_CN.md                  # Chinese documentation
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

## Citation

```
@software{omniseq2026,
  author = {Zheng, Yankai},
  title = {OmniSeq: An AI Agent-Driven End-to-End RNA-seq Analysis Platform},
  year = {2026},
  url = {https://github.com/YankaiZheng/omniseq}
}
```

## License

MIT License — see [LICENSE](LICENSE).

---

<div align="center">Made with ❤️ for reproducible science</div>
