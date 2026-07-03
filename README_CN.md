# OmniSeq — 端到端 RNA-seq 全自动化分析平台

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED.svg)](https://www.docker.com/)
[![R 4.5+](https://img.shields.io/badge/R-4.5%2B-276DC3.svg)](https://www.r-project.org/)

**从 FASTQ 到可发表 PDF — 一行命令，零人工干预**

[English](README.md) · [快速开始](#快速开始) · [核心功能](#核心功能) · [系统架构](#系统架构) · [API 文档](#api-端点) · [基准结果](#实验结果)

</div>

---

## 项目简介

OmniSeq 是一个**以 AI Agent 为核心**、**基于 Docker** 的端到端 RNA-seq 全自动化分析平台。它将 7 个相互独立的命令行工具（fastp → HISAT2 → samtools → featureCounts → DESeq2 → 功能富集 → PDF 报告）编排为一个无缝的自动化系统，用户通过浏览器中的自然语言 ChatPanel 即可完成从 FASTQ 原始文件到双文档学术 PDF 报告的完整分析流程。

首次使用时，内置的 **LLM ReAct Agent** 自动执行 6 步冷启动引导流程：环境检测 → 数据配置 → 管线调度 → 统计自动计算 → 热加载 → 就绪通知，全程零命令行操作。分析就绪后，用户可直接用自然语言提问——*"处理组 M 比对照组 C 有哪些关键通路差异？"*——Agent 自主推理、调用 40+ API 工具、返回图表和生物学解释。

> **创新点**: 在已发表的 RNA-seq 管线中首次使用 STRING REST API 程序化完成功能富集分析。将 R clusterProfiler 的 18 个包依赖链替换为单次 HTTP 请求（PubMed 检索确认此方向为空白）。同时设计了 compute-stats（统计自动计算）和 reload-stats（模块级热加载）两个端点，解决了传统 Flask 应用中"数据更新必须重启进程"的工程难题。

---

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/YankaiZheng/omniseq.git && cd omniseq

# 2. 构建镜像（一次性）
docker build -t omniseq .

# 3. 下载参考基因组（一次性，约 5GB）
docker run --rm -v ref_data:/data/ref omniseq scripts/download_ref.sh

# 4. 启动平台
docker-compose up -d

# 5. 打开浏览器 → http://localhost:5173
#    AI Agent 会自动引导首次设置
```

---

## 核心功能

| 功能 | 说明 |
|------|------|
| 🤖 **AI Agent** | ReAct 推理模式，40+ 工具定义。6 步冷启动引导：检测 → 配置 → 管线 → 统计计算 → 热加载 → 就绪 |
| 🔗 **API 驱动富集** | STRING REST API 替代 clusterProfiler — 18 个 R 包 → 0 个依赖。离线 KEGG JSON 降级方案 |
| 📊 **150+ 出版级图表** | 59 个 chart 函数，dpi=300，100% 真实数据。DEG-only PCA (PC1=74.7%)，DEG-only 相关性矩阵 (组内 0.93 vs 组间 0.74)，每样本 R1+R2 独立大图 |
| 📄 **双文档 PDF 报告** | 分析总结报告（约 15 页，叙事型）+ 图表附录（约 100 页，147 张编号图，Figure A3.5 格式） |
| 🐳 **Docker 自包含部署** | 3 个 micromamba 环境，YAML 精确版本锁定。一行 `docker-compose up` 启动 |
| 🧠 **机器学习模块** | VAE 非线性降维（48 种配置自动网格搜索，Silhouette 0.67），弹性网络生物标志物筛选（500 次 Bootstrap 稳定性选择，12 基因面板，置换检验 p=0.006） |
| 💊 **药物靶点优先排序** | DEG 列表 → LFC × 显著性综合评分 → 候选靶点排序 |
| 🌐 **40 个 API 端点** | 图表生成、数据查询、管线控制、统计计算、热加载 |

---

## 系统架构

OmniSeq 采用四层分离架构，每层职责明确，层间通过标准化接口通信：

```
┌──────────────────────────────────────────────────────┐
│  前端层: React + TypeScript + Vite + Zustand         │
│  ChatPanel AI Agent · 一键分析 · 图表渲染             │
├──────────────────────────────────────────────────────┤
│  API 网关层: Flask (Python) · 40 个端点               │
│  /api/chart/* (28) · /api/query/* (4) · /api/system/* (2) │
├──────────────────────────────────────────────────────┤
│  分析引擎层: Python                                   │
│  charts.py (59 个 chart 函数)                         │
│  pipeline_runner.py (7 步编排，零硬编码路径)           │
│  ml_analysis.py (VAE + GNN)                          │
│  biomarker.py (Elastic Net 生物标志物筛选)             │
│  report_generator.py (双文档 PDF 报告)                 │
├──────────────────────────────────────────────────────┤
│  计算层: micromamba 三环境隔离                        │
│  pipeline (fastp, HISAT2, samtools, featureCounts)    │
│  renv (R, DESeq2, matplotlib, PyTorch)                │
│  pyenv (WeasyPrint, Flask)                            │
│  外部 API: STRING REST API · KEGG REST API             │
└──────────────────────────────────────────────────────┘
```

### 设计要点

- **四层分离**：前端、API、引擎、计算层独立部署，互不干扰
- **路径参数化**：所有文件路径通过环境变量配置（$INPUT_DIR / $OUTPUT_DIR / $REF_DIR），无本地硬编码
- **三环境隔离**：pipeline、renv、pyenv 三个 micromamba 环境，通过 YAML 文件精确锁定版本号
- **Agent 闭环**：compute-stats 端点自动计算 PCA（numpy.linalg.svd）、相关性（Pearson r）、热图矩阵、FPKM 分布；reload-stats 端点将结果注入图表引擎内存，无需重启 Flask

---

## 7 步分析管线

| 步骤 | 工具 | 功能 | 输出 |
|------|------|------|------|
| **1. 质控** | fastp v0.23.4 | 去接头、去低质量（Q<20）、去高 N、最小长度过滤 | JSON 质控报告（每样本 ~130KB） |
| **2. 比对** | HISAT2 v2.2.2 + samtools | 剪接感知比对（GRCh38, --dta）、排序索引 | Sorted BAM（每样本 ~2.5GB） |
| **3. 定量** | featureCounts v2.1.1 | 基因水平 fragment 计数（GENCODE v44, -p -t exon -g gene_id） | 计数矩阵（52,147 genes × 9 samples, 78MB） |
| **4. 差异分析** | DESeq2 v1.50 (R) | Wald test + apeglm LFC shrinkage + 独立过滤 | DEG 表（gene_id, baseMean, LFC, lfcSE, pvalue, padj） |
| **5. 功能富集** | STRING API + clusterProfiler | KEGG 通路超几何检验+BH校正 / GO BP/MF/CC / PPI 边列表 | JSON + CSV |
| **6. 图表生成** | charts.py (59 函数) | 从 4 层真数据源自动生成全部可视化 | PNG（dpi=300, base64） |
| **7. PDF 报告** | WeasyPrint v66 | HTML 模板 → CSS 学术排版 → 双文档 PDF | 分析报告（1.7MB）+ 图表附录（15MB） |

---

## API 端点

### 图表端点（28 个）

```bash
GET /api/chart/volcano/<comp>      # 火山图（comp: MvsC/NvsC/MvsN）
GET /api/chart/heatmap             # 表达热图（Top 20 DEG）
GET /api/chart/pca                 # PCA（DEG-only SVD, PC1=74.7%）
GET /api/chart/kegg/<comp>         # KEGG 通路富集（clusterProfiler 离线数据）
GET /api/chart/go_string/<comp>    # GO 富集（STRING API 实时查询）
GET /api/chart/ppi                 # PPI 蛋白互作网络（STRING API）
GET /api/chart/kegg_pathway        # KEGG 通路图（KEGG API 官方 PNG）
# ... 共 59 个 chart 函数
```

### 查询端点（4 个）

```bash
GET /api/query/degs?comp=MvsC&top=20    # 返回 Top DEG 的基因名、LFC、padj
GET /api/query/enrichment?comp=MvsC     # 返回 KEGG 通路富集结果
GET /api/query/stats                     # 返回项目统计（样本数、DEG 数等）
GET /api/query/qc?sample=C1             # 返回指定样本的 QC 指标
```

### 系统端点（2 个）—— Agent 冷启动核心

```bash
GET /api/compute-stats    # 从 pipeline 输出自动计算 PCA / 相关性 / 热图 / FPKM 分布
GET /api/reload-stats     # 将计算结果热加载到图表引擎内存，无需重启 Flask
```

### 操作端点（2 个）

```bash
POST /api/run-pipeline     # 执行 7 步管线，SSE 实时推送进度
GET /api/generate-report   # 生成双文档 PDF 报告
```

---

## 实验结果

在 9 样本 3 组对照实验（Control / Treatment M / Treatment N，各 n=3）上验证：

| 指标 | 结果 |
|------|------|
| **严格 DEGs (|LFC|>1 & padj<0.05)** | MvsC: 233 (139↑ 94↓), NvsC: 157 (100↑ 57↓), MvsN: 27 (7↑ 20↓) |
| **DEG-only PCA** | PC1 = 74.7%（vs 全局 PCA 17.6%），Silhouette = 0.53（vs 全局 PCA 0.036） |
| **VAE（48 配置自动网格搜索）** | Silhouette = 0.67（超过 PCA 的 0.53），最优配置 lr=0.0001, beta=0.01, 233→32→16→2 |
| **生物标志物面板** | 12 基因（含 IL1B/IL33/IL36B/CSF2），3 折 CV 准确率 100%，置换检验 p=0.006 |
| **KEGG 通路富集** | TNF signaling (p=6.8e-16), IL-17 signaling (p=2.0e-13), Rheumatoid arthritis (p=3.9e-15) |
| **比对率** | 94.2%–95.2%（HISAT2, GRCh38） |
| **QC 指标** | Q20 = 97.7–98.4%, Q30 = 93.2–94.5%, GC = 50-52% |

---

## 环境管理

| 环境 | 内容 | 包数量 |
|------|------|:--:|
| `pipeline` | fastp, HISAT2, samtools, featureCounts | 4 |
| `renv` | R, DESeq2, matplotlib, networkx, PyTorch | ~30 |
| `pyenv` | WeasyPrint, Flask | ~5 |

所有版本通过 `envs/*.yaml` 文件**精确锁定**。通过 `micromamba create -f env.yaml` 可精确复现，保证跨机器一致性。

---

## 与同类平台对比

| 维度 | RNA-SeqEZPZ (GigaScience 2026) | IAN (Cell Rep Methods 2026) | **OmniSeq** |
|------|:---:|:---:|:---:|
| 部署方式 | Galaxy 服务器 | 计算后端 | **Docker（一行命令）** |
| 富集引擎 | clusterProfiler（18 个 R 包） | 未公开 | **STRING API（0 个依赖）** |
| AI Agent | ❌ | ✅（通用） | **✅ RNA-seq 专用（40+ 工具）** |
| 冷启动引导 | ❌ | ❌ | **✅ 6 步 AI 引导** |
| 统计自动计算 | ❌ | ❌ | **✅ compute-stats** |
| 热加载 | ❌ | ❌ | **✅ reload-stats** |
| 药物靶点 | ❌ | ❌ | **✅** |
| 机器学习 | ❌ | ❌ | **✅ VAE + 弹性网络** |
| 每样本独立图 | ❌ | ❌ | **✅ R1+R2 per-sample** |
| PDF 报告 | HTML | 交互界面 | **双文档 PDF** |

---

## 项目结构

```
omniseq/
├── Dockerfile                    # 55 行 Docker 镜像定义
├── docker-compose.yml            # 三层分离卷挂载
├── README.md                     # 英文文档
├── README_CN.md                  # 中文文档
├── LICENSE                       # MIT 许可证
├── .gitignore
├── app/
│   ├── serve.py                  # Flask API 服务器（40 个端点）
│   ├── charts.py                 # 图表引擎（59 个函数）
│   ├── pipeline_runner.py        # 7 步编排器（零硬编码路径）
│   ├── report_generator.py       # 双文档 PDF 报告生成器
│   ├── ml_analysis.py            # VAE + GNN 模块
│   ├── biomarker.py              # 弹性网络生物标志物筛选
│   └── docker_config.json        # 容器配置
├── frontend/                     # React + TypeScript（ChatPanel Agent）
├── envs/                         # micromamba YAML 环境文件
│   ├── pipeline.yaml
│   ├── renv.yaml
│   └── pyenv.yaml
└── scripts/
    └── download_ref.sh           # 一次性参考基因组下载脚本
```

---

## 引用格式

```
@software{omniseq2026,
  author = {Zheng, Yankai},
  title = {OmniSeq: An AI Agent-Driven End-to-End RNA-seq Analysis Platform},
  year = {2026},
  url = {https://github.com/YankaiZheng/omniseq}
}
```

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

---

## 参考文献

1. Taslim C et al. RNA-SeqEZPZ: a point-and-click pipeline for comprehensive transcriptomics analysis with interactive visualizations. *GigaScience*, 2026. [doi:10.1093/gigascience/giaf133](https://doi.org/10.1093/gigascience/giaf133)
2. Nagarajan V et al. IAN, an intelligent system for omics data analysis and discovery. *Cell Reports Methods*, 2026. [doi:10.1016/j.crmeth.2026.101503](https://doi.org/10.1016/j.crmeth.2026.101503)
3. Jiang A et al. ICARUS, an interactive web server for single cell RNA-seq analysis. *Nucleic Acids Research*, 2022;50(W1):W427-W433. [doi:10.1093/nar/gkac322](https://doi.org/10.1093/nar/gkac322)
4. Kim D et al. Graph-based genome alignment and genotyping with HISAT2. *Nature Biotechnology*, 2019;37:907-915.
5. Love MI et al. DESeq2. *Genome Biology*, 2014;15:550.
6. Szklarczyk D et al. STRING database in 2025. *Nucleic Acids Research*, 2025;53(D1):D730-D737.

---

<div align="center">Made with ❤️ for reproducible science</div>
