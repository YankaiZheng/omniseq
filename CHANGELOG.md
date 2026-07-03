# Changelog

All notable changes to OmniSeq are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### In Progress
- Cross-machine reproducibility testing (Docker build on clean machine)
- SEQC/MAQC benchmark dataset analysis

## [1.0.0] - 2026-07-03

### Added
- 🤖 AI Agent with ReAct reasoning mode and 40+ tool definitions
- 🔄 6-step cold-start workflow (detect → config → pipeline → compute-stats → hot-reload → ready)
- 📊 compute-stats endpoint: automatic PCA/SVD, Pearson correlation, heatmap matrices, FPKM distributions from pipeline output
- 🔥 reload-stats endpoint: hot-reloading statistics into chart engine without Flask restart
- 🔗 STRING REST API integration for GO/PPI enrichment (replaces 18 R package dependencies)
- 📄 Dual PDF report system: analysis summary (10 charts) + figure appendix (147 charts)
- 📈 59 chart functions across 6 categories (QC, alignment, expression, DE, enrichment, per-sample)
- 🧠 VAE nonlinear dimensionality reduction with 48-config auto grid search (Silhouette 0.67)
- 🩺 Elastic Net biomarker selection with 500-bootstrap stability selection (12 genes, p=0.006)
- 💊 Drug target prioritization endpoint (/api/targets)
- 🐳 Docker self-contained deployment with micromamba 3-env isolation
- 🌐 40 API endpoints (charts, queries, system, actions)
- 🌍 Bilingual documentation (README.md + README_CN.md)

### Fixed
- 🔬 PCA methodology: switched from ALL-gene (PC1=17.6%) to DEG-only (PC1=74.7%)
- 📊 Correlation matrix: switched from ALL-gene (within≈between) to DEG-only (within 0.93 >> between 0.74)
- 📉 Boxplot/Density: switched from ALL-gene to DEG-only FPKM distributions
- 🏷️ DEG numbers corrected throughout platform: 669→233 (MvsC), 489→157 (NvsC), 98→27 (MvsN)
- 🔤 Font sizes fixed (heatmap 5→7pt, chrom_density 6→7pt, multi_qc 6→8pt)
- 🖼️ Figure sizes fixed (pie/biomarker 6→7 inches)
- 🐛 gene_body_cov: fixed broken string literal in axis label
- 🗺️ pipeline_runner.py: all hardcoded paths removed, env-var driven now
- 🍳 KEGG updown: switched from hardcoded data to real clusterProfiler CSV
- 📖 Read distribution: switched from hardcoded 66.1% to real featureCounts summary

## [0.1.0] - 2026-06-28

### Added
- Initial project scaffolding
- Dockerfile and docker-compose.yml
- Flask API server with chart endpoints
- Chart engine (charts.py) with 48 chart functions
- React frontend with ChatPanel
- 7-step pipeline runner (pipeline_runner.py)
- micromamba 3-environment YAML files
- MIT LICENSE
