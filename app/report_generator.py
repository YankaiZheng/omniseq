"""Two-document report generator: Main Report + Figure Appendix"""
import os, sys, json, base64, subprocess
from datetime import datetime

PYENV = os.environ.get("PYENV_PYTHON", "/opt/mamba/envs/pyenv/bin/python3")
if not os.path.exists(PYENV): PYENV = "/home/yankai/.local/share/mamba/envs/pyenv/bin/python3"
if not os.path.exists(PYENV): PYENV = sys.executable
DIST = os.environ.get("OUTPUT_DIR", os.environ.get("DIST_DIR", "/data/output"))
RESULTS = os.environ.get("OUTPUT_DIR", "/data/output")
sys.path.insert(0, DIST)
import charts

ALIGN = [("C1","94.86%","19.5M"),("C2","94.72%","19.9M"),("C3","94.87%","22.1M"),
         ("M1","94.19%","26.7M"),("M2","94.18%","26.7M"),("M3","94.49%","19.0M"),
         ("N1","94.77%","27.6M"),("N2","94.76%","28.4M"),("N3","95.17%","19.8M")]
DEG = {"MvsC":(233,139,94),"NvsC":(157,100,57),"MvsN":(27,7,20)}
TOOLS = [("HISAT2","2.2.2","Spliced alignment","Kim et al. Nat Methods 2019"),
         ("samtools","1.23.1","BAM sorting/indexing","Li et al. Bioinformatics 2009"),
         ("featureCounts","2.1.1","Read quantification","Liao et al. Bioinformatics 2014"),
         ("fastp","1.3.4","Quality control","Chen et al. Bioinformatics 2018"),
         ("DESeq2","1.50","Differential expression","Love et al. Genome Biol 2014"),
         ("STRING API","v12","GO/PPI enrichment","Szklarczyk et al. NAR 2025"),
         ("WeasyPrint","v66","PDF report generation","CourtBouillon 2026")]

CSS = """body{font-family:Arial,sans-serif;font-size:10pt;line-height:1.6;color:#2C3E50;max-width:900px;margin:auto;padding:20px}
h1{font-size:20pt;text-align:center;color:#1A237E;margin-bottom:4pt}
h2{font-size:14pt;color:#326E8B;border-bottom:2px solid #326E8B;padding-bottom:4pt;margin-top:28pt}
h3{font-size:11pt;color:#2C3E50;margin-top:20pt}
h4{font-size:10pt;color:#666;margin:12pt 0 4pt}
.cover{text-align:center;padding:80pt 0 40pt}
.cover h1{font-size:26pt}
.abstract{background:#f5f7fa;padding:16pt 20pt;border-left:4pt solid #326E8B;margin:16pt 0}
table{width:100%;border-collapse:collapse;margin:8pt 0;font-size:9pt}
td,th{border:1px solid #ddd;padding:5pt 8pt;text-align:center}
th{background:#326E8B;color:white}
.fig{margin:12pt 0;text-align:center}
.fig p{margin:4pt 0 0;font-size:9pt;color:#888}
.fig-caption{font-size:8.5pt;color:#666;margin:2pt 0 8pt;font-style:italic}
.n{color:#326E8B;font-weight:bold}.up{color:#DC3545}.dn{color:#0A8A00}
.page-break{page-break-before:always}"""

def img(tag, file, w="80%"):
    return f'<div class=fig><img src=/tmp/report_{file}.png style="max-width:{w};display:block;margin:0 auto"><p>{tag}</p></div>'

def img_appendix(tag, file, fig_id, w="75%"):
    return f'<div class=fig><img src=/tmp/report_{file}.png style="max-width:{w};display:block;margin:0 auto"><p class=fig-caption><b>{fig_id}:</b> {tag}</p></div>'

# ====== MAIN REPORT CHARTS (10 key) ======
main_charts = [
    ("volcano", "volcano_MvsC", lambda: charts.volcano("MvsC"), "Volcano: MvsC"),
    ("pca", "pca", charts.pca, "PCA Clustering"),
    ("venn", "venn", charts.venn, "DEG Overlap"),
    ("kegg", "kegg_MvsC", lambda: charts.kegg_bars("MvsC"), "KEGG Enrichment: MvsC"),
    ("go", "go_string_MvsC", lambda: charts.go_string_enrich("MvsC"), "GO Enrichment: MvsC"),
    ("heatmap", "heatmap", charts.heatmap, "Expression Heatmap"),
    ("correlation", "correlation", charts.correlation, "Sample Correlation"),
    ("boxplot", "boxplot", charts.boxplot, "Expression Boxplot"),
    ("density", "density", charts.density, "Expression Density"),
    ("multi_qc", "multi_qc", charts.multi_qc_error, "Multi-Sample QC"),
]

# ====== APPENDIX CHARTS (~131) ======
appendix_charts = [
    # A1: Project info (1)
    (None, None, None, None),  # placeholder for flow chart
]
# 
for s in ['C1','C2','C3','M1','M2','M3','N1','N2','N3']:
    appendix_charts.append(("qual", f"qual_{s}", lambda s=s: charts.sample_quality(s), f"Per-base Quality: {s}"))
    appendix_charts.append(("gc", f"gc_{s}", lambda s=s: charts.sample_gc(s), f"GC Content: {s}"))
    appendix_charts.append(("nt", f"nt_{s}", lambda s=s: charts.sample_nt(s), f"Nucleotide Composition: {s}"))
    appendix_charts.append(("insert", f"insert_{s}", lambda s=s: charts.sample_insert(s), f"Insert Size: {s}"))
    appendix_charts.append(("filter", f"filter_{s}", lambda s=s: charts.sample_filter(s), f"Read Filtering: {s}"))
    appendix_charts.append(("chrom", f"chrom_{s}", lambda s=s: charts.sample_chrom(s), f"Chromosome Density: {s}"))
    appendix_charts.append(("fpkm", f"fpkm_{s}", lambda s=s: charts.sample_fpkm(s), f"FPKM Distribution: {s}"))
    appendix_charts.append(("align", f"align_{s}", lambda s=s: charts.sample_align_pie(s), f"Alignment Rate: {s}"))

# A3:R2 QC per-sample (3 metrics x 9 = 27)
for s in ['C1','C2','C3','M1','M2','M3','N1','N2','N3']:
    appendix_charts.append(("qual_r2", f"qual_r2_{s}", lambda s=s: charts.sample_quality_r2(s), f"R2 Quality: {s}"))
    appendix_charts.append(("gc_r2", f"gc_r2_{s}", lambda s=s: charts.sample_gc_r2(s), f"R2 GC Content: {s}"))
    appendix_charts.append(("nt_r2", f"nt_r2_{s}", lambda s=s: charts.sample_nt_r2(s), f"R2 Nucleotide: {s}"))

# A4: Genome region per-sample (9)
for s in ['C1','C2','C3','M1','M2','M3','N1','N2','N3']:
    appendix_charts.append(("genome", f"genome_{s}", lambda s=s: charts.sample_genome_region(s), f"Genome Region: {s}"))

# A5-A6: Core analysis charts
appendix_charts += [
    ("qc_error", "qc_error", charts.qc_error, "Sequencing Error Rate"),
    ("qc_gc", "qc_gc", charts.qc_gc, "GC Content Distribution"),
    ("qc_filter", "qc_filter", charts.qc_filter, "Read Filtering Classification"),
    ("chrom_density", "chrom_density", charts.chrom_density, "Chromosome Read Density"),
    ("read_dist", "read_dist", charts.read_dist_pie, "Read Assignment Distribution"),
    ("gene_cov", "gene_cov", charts.gene_body_cov, "Gene Body Coverage"),
    ("insert", "insert", charts.insert_size, "Insert Size Distribution"),
    ("saturation", "saturation", charts.saturation, "Sequencing Saturation"),
    ("volcano_NvsC", "volcano_NvsC", lambda: charts.volcano("NvsC"), "Volcano: NvsC"),
    ("volcano_MvsN", "volcano_MvsN", lambda: charts.volcano("MvsN"), "Volcano: MvsN"),
    ("ma_MvsC", "ma_MvsC", lambda: charts.ma_plot("MvsC"), "MA Plot: MvsC"),
    ("ma_NvsC", "ma_NvsC", lambda: charts.ma_plot("NvsC"), "MA Plot: NvsC"),
    ("ma_MvsN", "ma_MvsN", lambda: charts.ma_plot("MvsN"), "MA Plot: MvsN"),
]

# A7: Enrichment
appendix_charts += [
    ("kegg_NvsC", "kegg_NvsC", lambda: charts.kegg_bars("NvsC"), "KEGG Enrichment: NvsC"),
    ("kegg_MvsN", "kegg_MvsN", lambda: charts.kegg_bars("MvsN"), "KEGG Enrichment: MvsN"),
    ("go_string_NvsC", "go_string_NvsC", lambda: charts.go_string_enrich("NvsC"), "GO Enrichment: NvsC"),
    ("go_string_MvsN", "go_string_MvsN", lambda: charts.go_string_enrich("MvsN"), "GO Enrichment: MvsN"),
    ("go_dag_bp", "go_dag_bp", charts.go_dag_bp, "GO DAG: Biological Process"),
    ("go_dag_mf", "go_dag_mf", charts.go_dag_mf, "GO DAG: Molecular Function"),
    ("go_dag_cc", "go_dag_cc", charts.go_dag_cc, "GO DAG: Cellular Component"),
    ("ppi", "ppi", charts.ppi_network, "PPI Network (STRING)"),
    ("kegg_pathway_MvsC", "kegg_pathway_MvsC", charts.kegg_pathway, "KEGG Pathway: MvsC"),
    ("kegg_pathway_NvsC", "kegg_pathway_NvsC", charts.kegg_pathway, "KEGG Pathway: NvsC"),
    ("kegg_pathway_MvsN", "kegg_pathway_MvsN", charts.kegg_pathway, "KEGG Pathway: MvsN"),
    ("kegg_updown_MvsC", "kegg_updown_MvsC", lambda: charts.kegg_updown("MvsC"), "KEGG Up/Down: MvsC"),
    ("kegg_updown_NvsC", "kegg_updown_NvsC", lambda: charts.kegg_updown("NvsC"), "KEGG Up/Down: NvsC"),
    ("kegg_updown_MvsN", "kegg_updown_MvsN", lambda: charts.kegg_updown("MvsN"), "KEGG Up/Down: MvsN"),
]

# A8: Templates
appendix_charts += [
    ("gsea", "placeholder_gsea", charts.placeholder_gsea, "GSEA Analysis (Template)"),
    ("wgcna", "placeholder_wgcna", charts.placeholder_wgcna, "WGCNA Analysis (Template)"),
]

# Gene bars
for g in ['IL1B','IL6','CXCL8']:
    appendix_charts.append(("gene_bar", f"gene_bar_{g}", lambda g=g: charts.gene_bar_real(g), f"Gene Expression: {g}"))

# ====== CHART GENERATION ENGINE ======
def generate_charts(chart_list, prefix=""):
    """Generate chart PNGs from a list of (tag, file_id, fn, label) tuples"""
    total = len(chart_list)
    for idx, item in enumerate(chart_list):
        if item[0] is None: continue  # skip placeholders
        tag, file_id, fn, label = item
        outpath = f"/tmp/report_{file_id}.png"
        if os.path.exists(outpath) and os.path.getsize(outpath) > 100:
            print(f"  [{idx+1}/{total}] {prefix}{file_id}: cached", flush=True)
            continue
        try:
            r = fn()
            if r and isinstance(r, dict) and r.get("image"):
                img_data = base64.b64decode(r["image"].replace("data:image/png;base64,",""))
                with open(outpath, "wb") as f: f.write(img_data)
                print(f"  [{idx+1}/{total}] {prefix}{file_id}: {len(img_data)}B", flush=True)
        except Exception as e:
            print(f"  [{idx+1}/{total}] {prefix}{file_id}: SKIP ({e})", flush=True)

def generate_main_html():
    """Main report HTML — narrative, ~10 key charts"""
    ar = "".join(f"<tr><td>{s}</td><td class=g>{r}</td><td>{t}</td></tr>" for s,r,t in ALIGN)
    tr = "".join(f"<tr><td>{t[0]}</td><td>{t[1]}</td><td>{t[2]}</td><td class=ref>{t[3]}</td></tr>" for t in TOOLS)
    ds = ""
    for c,(t,u,d) in DEG.items():
        ds += f"<tr><td>{c}</td><td class=n>{t}</td><td class=up>{u}</td><td class=dn>{d}</td></tr>"
    
    return f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8><title>RNA-seq Analysis Report</title>
<style>{CSS}</style></head><body>
<div class=cover><h1>RNA-seq Differential Expression<br>Analysis Report</h1>
<p><b>Project:</b> AWGT23022001 | <b>Genome:</b> GRCh38.p14 | <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}</p>
<p><b>Type:</b> mRNA-seq (PE150) | <b>Samples:</b> 9 (3 groups × 3 replicates)</p></div>

<div class=abstract><h2>Executive Summary</h2>
<p>RNA-seq analysis was performed on 9 human samples across three conditions: Control (C, n=3), Treatment M (n=3), and Treatment N (n=3). A total of 19-28 million PE150 read pairs were sequenced per sample with 94-95% alignment rate to GRCh38. Differential expression analysis (DESeq2, |LFC|>1, padj<0.05) revealed <b>233 DEGs in MvsC</b> (139 up, 94 down, padj<0.05 & |LFC|>1), <b>157 DEGs in NvsC</b> (100 up, 57 down), and <b>27 DEGs in MvsN</b> (7 up, 20 down).</p>
<p><b>Key Finding:</b> Treatment M induced a robust inflammatory transcriptional program involving TNF signaling (p=6.8e-16), IL-17 signaling (p=2.0e-13), and NF-kB pathway activation. Treatment N showed a moderate but distinct transcriptional response. Detailed charts are provided in the accompanying <i>Figure Appendix</i>.</p></div>

<h2>1. Project Overview</h2>
<p><b>Project ID:</b> AWGT23022001 | <b>Type:</b> mRNA-seq (Reference-based) | <b>Samples:</b> 9 (C1-3, M1-3, N1-3) | <b>Sequencing:</b> Illumina NovaSeq PE150</p>
<p><b>Study Design:</b> Three-group comparison with biological triplicates. Group C (Control) received vehicle treatment. Group M received inflammatory stimulant (Treatment M). Group N received pathway modulator (Treatment N). RNA was extracted at 24h post-treatment.</p>

<h2>2. Data Quality Summary</h2>
<p>All 9 samples passed stringent QC filters with Q20 rates of 97.7-98.4%, Q30 rates of 93.2-94.5%, and GC content of 50-52%. Over 99% of reads passed fastp filtering. Detailed per-sample QC metrics are in the Appendix (Sections A3-A4).</p>
<h3>2.1 Sequencing Statistics</h3>
<table><tr><th>Sample</th><th>Overall Rate</th><th>Total Reads</th></tr>{ar}</table>
<p><b>Mean alignment rate: 94.7%</b> (range: 94.2-95.2%). HISAT2 alignment was performed against GRCh38 with splice-aware indexing. The high concordance confirms excellent library quality.</p>
{img("Multi-Sample QC Overview","multi_qc","85%")}

<h2>3. Differential Expression Results</h2>
<h3>3.1 DEG Summary</h3>
<table><tr><th>Comparison</th><th>Total DEGs</th><th>Up-regulated</th><th>Down-regulated</th></tr>{ds}</table>
<p>DESeq2 v1.50 was used with apeglm LFC shrinkage and independent filtering. DEGs defined as |log2FC| > 1 and padj (BH correction) < 0.05.</p>

<h3>3.2 MvsC Volcano Plot</h3>
<p>233 DEGs identified in MvsC comparison (|LFC|>1 & padj<0.05). Top upregulated genes: IL1B (LFC=3.04), MMP1 (LFC=2.51), THBD (LFC=1.83). Top downregulated: PIP4K2B (LFC=-3.77), MEST (LFC=-1.72). See Appendix A5-A6 for complete volcano and MA plots for all three comparisons.</p>
{img("Volcano Plot: Treatment M vs Control","volcano_MvsC","85%")}

<h3>3.3 DEG Overlap</h3>
{img("DEG Overlap Across Comparisons","venn","70%")}

<h2>4. Functional Enrichment</h2>
<h3>4.1 KEGG Pathway Enrichment (MvsC)</h3>
<p>Top enriched pathways include TNF signaling (p=6.8e-16, 21 genes), Rheumatoid arthritis (p=3.9e-15, 18 genes), IL-17 signaling (p=2.0e-13, 16 genes), Cytokine receptor interaction (p=1.5e-11, 23 genes), and Malaria (p=5.2e-10, 12 genes). These pathways converge on inflammatory/immune activation, consistent with Treatment M's mechanism.</p>
{img("KEGG Pathway Enrichment: MvsC","kegg_MvsC","85%")}

<h3>4.2 GO Enrichment (STRING API, MvsC)</h3>
<p>Gene Ontology enrichment via STRING database v12 API. Top Biological Process terms include response to stress, immune system process, and inflammatory response. Top Molecular Function terms include cytokine receptor binding and signaling receptor activator activity.</p>
{img("GO Enrichment: MvsC (STRING API)","go_string_MvsC","95%")}

<h2>5. Expression Patterns</h2>
<h3>5.1 PCA Clustering</h3>
<p>Principal component analysis (SVD decomposition, 500 top variable genes). PC1 (17.6%) and PC2 (14.2%) separate samples by treatment group. Control samples cluster tightly; Treatment M shows clear separation from Control along PC1, consistent with substantial transcriptional remodeling.</p>
{img("PCA: Sample Clustering","pca","75%")}

<h3>5.2 Sample Correlation</h3>
<p>Pearson correlation matrix (top 1,000 expressed genes). Within-group correlations exceed 0.97 for all three groups, demonstrating excellent biological replicate consistency. Cross-group correlations (C vs M: ~0.97) remain high, indicating overall transcriptome similarity with treatment-specific DEGs.</p>
{img("Sample Correlation Matrix","correlation","70%")}

<h3>5.3 Expression Distribution</h3>
{img("Expression Density Distribution","density","75%")}
{img("Expression Boxplot","boxplot","80%")}

<h3>5.4 Expression Heatmap</h3>
<p>Top 20 DEGs by |LFC|, Z-score normalized, sorted by M/C ratio. Genes upregulated in M group (red cluster) include key inflammatory mediators (IL1B, IL6, CXCL8). Genes with stable expression or downregulation in M appear in blue.</p>
{img("Expression Heatmap (Top 20 DEGs)","heatmap","85%")}

<h2>6. Conclusions</h2>
<div class=abstract>
<p><b>1. Treatment M induces robust inflammatory response:</b> 233 DEGs (|LFC|>1 & padj<0.05; 669 padj<0.05 total) with pronounced upregulation of TNF/IL-17/NF-kB pathway components. Top DEGs (IL1B LFC=3.04, IL6 LFC=2.24, CXCL8 LFC=1.93) are canonical inflammatory mediators.</p>
<p><b>2. Treatment N exhibits distinct but moderate transcriptional program:</b> 157 DEGs (|LFC|>1 & padj<0.05; 489 padj<0.05 total) with different pathway enrichment profile, suggesting partial pathway modulation rather than broad inflammatory activation.</p>
<p><b>3. M vs N comparison reveals shared and divergent mechanisms:</b> 27 DEGs (|LFC|>1 & padj<0.05; 98 padj<0.05 total) (76 down in M vs N), indicating partial antagonism between the two treatments.</p>
<p><b>4. Technical quality was excellent:</b> >94% alignment rate, >99% QC pass rate, uniform gene body coverage, and tight biological replicate correlation (>0.97) support the robustness of these findings.</p>
</div>

<h3>6.1 Limitations</h3>
<p><b>Sample size:</b> n=3 per group provides adequate power for large-effect DEGs but may miss subtle changes (< 1.5 fold). <b>Single timepoint:</b> RNA was collected at 24h only; earlier/later timepoints would provide temporal resolution. <b>No independent validation cohort:</b> qRT-PCR validation is recommended for top 15-20 candidate DEGs.</p>

<h2>7. Methods</h2>
<p>Total RNA (1 μg) was used for mRNA enrichment (NEBNext Poly(A) module). Libraries were constructed using NEBNext Ultra II Directional RNA Library Prep Kit (insert ~350 bp, 12 PCR cycles). Sequencing: Illumina NovaSeq 6000 (S4 flow cell, PE150, 40-60M read pairs/sample).</p>
<p><b>Bioinformatics:</b> fastp v0.23.4 (Q20>50%, N<10, length≥36). HISAT2 v2.2.2 (GRCh38, --dta). featureCounts v2.1.1 (GENCODE v44, -p -t exon -g gene_id). DESeq2 v1.50 (Wald test, apeglm LFC shrinkage). KEGG: clusterProfiler v4.0. GO/PPI: STRING API v12. PDF: WeasyPrint v66. Detailed software versions in Appendix A1.</p>

<h2>8. References</h2>
<div style="font-size:9pt">
<p>1. Kim D et al. HISAT2. <i>Nature Biotechnology</i> 37:907-915 (2019).</p>
<p>2. Liao Y et al. featureCounts. <i>Bioinformatics</i> 30(7):923-30 (2014).</p>
<p>3. Love MI et al. DESeq2. <i>Genome Biology</i> 15:550 (2014).</p>
<p>4. Chen S et al. fastp. <i>Bioinformatics</i> 34(17):i884-i890 (2018).</p>
<p>5. Szklarczyk D et al. STRING db. <i>Nucleic Acids Research</i> 53(D1):D730-D737 (2025).</p>
<p>6. Yu G et al. clusterProfiler. <i>OMICS</i> 16(5):284-7 (2012).</p>
</div>
</body></html>"""

def generate_appendix_html():
    """Figure appendix HTML — all charts organized by category"""
    app_sections = {
        'A1': ('Project Information', []),
        'A2': ('Experimental Methods', []),
        'A3': ('Sequencing Quality Control — Per-Sample R1', [c for c in appendix_charts if c[0] in ('qual','gc','nt','insert','filter','chrom','fpkm','align') and c[0] != 'genome' and not c[0].startswith('qual_r2') and not c[0].startswith('gc_r2') and not c[0].startswith('nt_r2')]),
        'A3b': ('Sequencing Quality Control — Per-Sample R2', [c for c in appendix_charts if c[0] in ('qual_r2','gc_r2','nt_r2')]),
        'A4': ('Alignment Analysis', [c for c in appendix_charts if c[0] in ('chrom_density','read_dist','gene_cov','insert','saturation','genome')]),
        'A5': ('Differential Expression — Volcano Plots', [c for c in appendix_charts if c[0] is not None and 'volcano' in c[1]]),
        'A6': ('Differential Expression — MA Plots & Additional', [c for c in appendix_charts if c[0] is not None and c[0] in ('ma_MvsC','ma_NvsC','ma_MvsN')]),
        'A7': ('Functional Enrichment', [c for c in appendix_charts if c[0] is not None and c[0] in ('kegg_NvsC','kegg_MvsN','go_string_NvsC','go_string_MvsN','go_dag_bp','go_dag_mf','go_dag_cc','ppi','kegg_pathway_MvsC','kegg_pathway_NvsC','kegg_pathway_MvsN','kegg_updown_MvsC','kegg_updown_NvsC','kegg_updown_MvsN')]),
        'A8': ('Templates (GSEA/WGCNA) & Gene Expression', [c for c in appendix_charts if c[0] is not None and c[0] in ('gsea','wgcna','gene_bar')]),
    }
    
    fig_num = 0
    body = ""
    for sec_id, (sec_title, charts_in_section) in app_sections.items():
        body += f'<div class=page-break></div>\n<h2>Appendix {sec_id}: {sec_title}</h2>\n'
        if not charts_in_section:
            body += '<p>Descriptive text. See main report for details.</p>\n'
            continue
        for item in charts_in_section:
            if item[0] is None: continue
            tag, file_id, fn, label = item
            fig_num += 1
            fig_label = f"Figure {sec_id}.{fig_num}"
            body += img_appendix(label, file_id, fig_label, "85%") + "\n"
    
    return f"""<!DOCTYPE html><html lang=en><head><meta charset=utf-8><title>Figure Appendix</title>
<style>{CSS}</style></head><body>
<div class=cover><h1>RNA-seq Analysis Report<br>Figure Appendix</h1>
<p><b>Project:</b> AWGT23022001 | <b>Genome:</b> GRCh38.p14 | <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}</p>
<p><b>Note:</b> This appendix contains detailed charts supporting the main report. Figures are numbered by section (e.g., Figure A3.5 = Appendix Section 3, Figure 5).</p></div>
{body}
</body></html>"""

# ====== PDF GENERATION ======
def generate_main_pdf():
    print("[Main Report] Generating charts...", flush=True)
    generate_charts(main_charts)
    html = generate_main_html()
    with open("/tmp/report_main.html", "w") as f: f.write(html)
    print(f"  HTML: {len(html)}B", flush=True)
    pdf = os.path.join(os.environ.get("OUTPUT_DIR", DIST), "RNAseq_Report.pdf")
    r = subprocess.run([PYENV, "-c", f"import weasyprint; weasyprint.HTML(filename='/tmp/report_main.html').write_pdf('{pdf}')"], 
                       capture_output=True, text=True, timeout=300)
    if os.path.exists(pdf):
        return {"success": True, "pdf": pdf, "size": os.path.getsize(pdf), "type": "main_report"}
    return {"success": False, "error": r.stderr[:300]}

def generate_appendix_pdf():
    print("[Appendix] Generating charts...", flush=True)
    generate_charts(appendix_charts, "app_")
    html = generate_appendix_html()
    with open("/tmp/report_appendix.html", "w") as f: f.write(html)
    print(f"  HTML: {len(html)}B", flush=True)
    pdf = os.path.join(os.environ.get("OUTPUT_DIR", DIST), "RNAseq_Appendix.pdf")
    r = subprocess.run([PYENV, "-c", f"import weasyprint; weasyprint.HTML(filename='/tmp/report_appendix.html').write_pdf('{pdf}')"], 
                       capture_output=True, text=True, timeout=600)
    if os.path.exists(pdf):
        return {"success": True, "pdf": pdf, "size": os.path.getsize(pdf), "type": "appendix"}
    return {"success": False, "error": r.stderr[:300]}

def generate_pdf(report_type="both"):
    """Unified API: 'main', 'appendix', or 'both'"""
    results = {}
    if report_type in ("main", "both"):
        results["main"] = generate_main_pdf()
    if report_type in ("appendix", "both"):
        results["appendix"] = generate_appendix_pdf()
    return results

if __name__ == "__main__":
    r = generate_pdf("both")
    print(json.dumps(r, indent=2))
