# OmniSeq — End-to-End RNA-seq Analysis Platform

OmniSeq is a Docker-based, AI-powered platform that automates the entire RNA-seq analysis workflow: from raw FASTQ files to a publication-ready PDF report with natural language biological interpretation.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## Key Features

- **7-Step Pipeline Orchestration**: FASTQ → fastp → HISAT2 → featureCounts → DESeq2 → enrichment → PDF
- **API-Driven Enrichment**: STRING REST API replaces R clusterProfiler (18 R packages → 0)
- **LLM ReAct Agent**: 40+ tools, multi-step reasoning, natural language biological interpretation
- **Dual PDF Report**: Main analysis report + comprehensive figure appendix (150+ charts)
- **Per-Sample Publication-Grade Charts**: Independent large charts for each sample (R1+R2)
- **Drug Target Prioritization**: DEG → Open Targets scoring
- **Machine Learning**: VAE nonlinear dimensionality reduction + Elastic Net biomarker selection
- **Docker Self-Contained**: `docker-compose up` — no R/python/toolchain installation needed

## Architecture

```
Browser (localhost:5173)
  │ ChatPanel AI Agent · One-Click Pipeline · Chart Rendering
  ▼
Flask API (serve.py)
  │ /api/chart/* (40+) · /api/query/* (4) · /api/generate-report
  ▼
Analysis Engine
  │ charts.py (48 chart functions) · pipeline_runner.py (7-step)
  │ report_generator.py (HTML→PDF) · ml_analysis.py (VAE+GNN+Biomarker)
  ▼
Compute Layer (micromamba 3 environments)
  │ fastp · HISAT2 · samtools · featureCounts · R/DESeq2
  │ STRING API · KEGG API · WeasyPrint
```

## Quick Start (Docker)

```bash
# 1. Pull the image
docker pull omniseq:latest

# 2. Download reference genome (one-time, ~5GB)
docker run --rm -v ref_data:/data/ref omniseq scripts/download_ref.sh

# 3. Start the platform
docker-compose up -d

# 4. Open browser → http://localhost:5173
```

## Pipeline Steps

| Step | Tool | Input → Output |
|------|------|----------------|
| 1. QC | fastp v0.23.4 | FASTQ → clean FASTQ + JSON report |
| 2. Alignment | HISAT2 v2.2.2 + samtools | clean FASTQ → sorted BAM |
| 3. Quantification | featureCounts v2.1.1 | BAM + GTF → count matrix (52K genes) |
| 4. DE Analysis | DESeq2 v1.50 | count matrix → DEG table (LFC, padj) |
| 5. Enrichment | STRING API + KEGG | DEG list → GO/KEGG/PPI |
| 6. Charts | charts.py (48 functions) | JSON/CSV → PNG (dpi=300) |
| 7. Report | WeasyPrint v66 | HTML → dual PDF |

## Environment Management

Three isolated micromamba environments with version-locked dependencies:

| Environment | Contents |
|-------------|----------|
| `pipeline` | fastp, HISAT2, samtools, featureCounts |
| `renv` | R, DESeq2, matplotlib, networkx, PyTorch |
| `pyenv` | WeasyPrint, Flask |

All versions locked in `envs/*.yaml` — reproducible across any machine.

## API Endpoints

| Endpoint | Function |
|----------|----------|
| `/api/chart/<name>` | 40+ chart types (volcano, heatmap, GO, PPI, etc.) |
| `/api/query/degs` | Query DEG results by comparison |
| `/api/query/enrichment` | Query KEGG enrichment results |
| `/api/query/stats` | Project statistics overview |
| `/api/query/targets` | Drug target prioritization |
| `/api/generate-report` | Generate dual PDF reports |

## Comparison with RNA-SeqEZPZ

RNA-SeqEZPZ (GigaScience 2026, [DOI:10.1093/gigascience/giaf133](https://doi.org/10.1093/gigascience/giaf133)) is the closest competitor — a Galaxy-based point-and-click RNA-seq pipeline.

| Feature | RNA-SeqEZPZ | OmniSeq |
|---------|:---:|:---:|
| Deployment | Galaxy Server | **Docker (1 command)** |
| Enrichment | clusterProfiler (18 R pkgs) | **STRING API (0 deps)** |
| LLM Agent | ❌ | **✅ ReAct Agent** |
| Drug Targets | ❌ | **✅** |
| ML/DL | ❌ | **✅ VAE + Biomarker** |
| Per-Sample Charts | ❌ | **✅ R1+R2** |
| Report | HTML | **Dual PDF** |
| Charts | ~30 interactive | **150+ static** |

## Project Structure

```
omniseq/
├── Dockerfile
├── docker-compose.yml
├── README.md
├── LICENSE
├── .gitignore
├── app/
│   ├── serve.py              # Flask API server
│   ├── charts.py             # Chart engine (48 functions)
│   ├── pipeline_runner.py    # 7-step pipeline orchestrator  
│   ├── report_generator.py   # Dual PDF report generator
│   ├── ml_analysis.py        # VAE + GNN + Biomarker modules
│   ├── biomarker.py          # Elastic Net biomarker selection
│   ├── chart_params.json     # Chart configuration
│   ├── benchmark.json        # Platform comparison data
│   └── docker_config.json    # Container configuration
├── frontend/
│   ├── index.html
│   ├── assets/
│   └── src/                  # React + TypeScript source
├── envs/
│   ├── pipeline.yaml
│   ├── renv.yaml
│   └── pyenv.yaml
└── scripts/
    └── download_ref.sh
```

## Citation

If you use OmniSeq in your research, please cite:

```
OmniSeq: an end-to-end transcriptomics platform with API-driven enrichment, 
LLM-powered conversational analysis, and self-contained Docker deployment.
Preprint, 2026.
```

## License

MIT License — see [LICENSE](LICENSE) for details.
