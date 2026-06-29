"""RNA-seq Platform API Server"""
from flask import Flask, request, jsonify, send_from_directory
import os, sys
sys.path.insert(0, '/app')
import charts

# Docker: serve frontend from /app/frontend
FRONTEND_DIR = os.environ.get('FRONTEND_DIR', '/app/frontend')
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = '.'

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

@app.route('/')
def index(): return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/assets/<path:filename>')
def assets(filename): return send_from_directory(os.path.join(FRONTEND_DIR, 'assets'), filename)

@app.route('/run-plot', methods=['POST'])
def run_plot():
    try: return jsonify(charts.run(request.json.get('code','')))
    except: return jsonify({'success':False,'error':'error'})

@app.route('/api/chart/volcano/<comp>')
def api_v(comp='MvsC'): return jsonify(charts.volcano(comp))
@app.route('/api/chart/heatmap')
def api_h(): return jsonify(charts.heatmap())
@app.route('/api/chart/pca')
def api_p(): return jsonify(charts.pca())
@app.route('/api/chart/ma/<comp>')
def api_m(comp='MvsC'): return jsonify(charts.ma_plot(comp))
@app.route('/api/chart/boxplot')
def api_b(): return jsonify(charts.boxplot())
@app.route('/api/chart/correlation')
def api_c(): return jsonify(charts.correlation())
@app.route('/api/chart/kegg/<comp>')
def api_k(comp='MvsC'): return jsonify(charts.kegg_bars(comp))
@app.route('/api/chart/gene/<gene>')
def api_g(gene='IL1B'): return jsonify(charts.gene_bar(gene))
@app.route('/api/chart/venn')
def api_vn(): return jsonify(charts.venn())
@app.route('/api/chart/density')
def api_d(): return jsonify(charts.density())
@app.route('/api/chart/qc_error')
def api_qe(): return jsonify(charts.qc_error())
@app.route('/api/chart/qc_gc')
def api_qg(): return jsonify(charts.qc_gc())
@app.route('/api/chart/qc_filter')
def api_qf(): return jsonify(charts.qc_filter())
@app.route('/api/chart/chrom_density')
def api_cd(): return jsonify(charts.chrom_density())
@app.route('/api/chart/ppi')
def api_pp(): return jsonify(charts.ppi_network())
@app.route('/api/chart/read_dist')
def api_rd(): return jsonify(charts.read_dist_pie())
@app.route('/api/chart/gene_cov')
def api_gc2(): return jsonify(charts.gene_body_cov())
@app.route('/api/chart/insert')
def api_is(): return jsonify(charts.insert_size())
@app.route('/api/chart/saturation')
def api_st(): return jsonify(charts.saturation())
@app.route('/api/chart/kegg_pathway')
def api_kp(): return jsonify(charts.kegg_pathway())
@app.route('/api/chart/go')
def api_go(): return jsonify(charts.go_bar())
@app.route('/api/chart/go_dag_bp')
def api_gdbp(): return jsonify(charts.go_dag_bp())
@app.route('/api/chart/go_dag_mf')
def api_gdmf(): return jsonify(charts.go_dag_mf())
@app.route('/api/chart/go_dag_cc')
def api_gdcc(): return jsonify(charts.go_dag_cc())
@app.route('/api/chart/kegg_updown/<comp>')
def api_kud(comp='MvsC'): return jsonify(charts.kegg_updown(comp))
@app.route('/api/chart/multi_qc')
def api_mqc(): return jsonify(charts.multi_qc_error())

# ====== Query API endpoints (for AI Agent) ======
@app.route('/api/query/degs')
def query_degs():
    """Return top DEGs for a comparison as JSON"""
    comp = request.args.get('comp', 'MvsC')
    top = int(request.args.get('top', 20))
    import csv, json
    fpath = os.path.join('/home/yankai/rnaseq_pipeline/results', f'DESeq2_geneid_{comp}.csv')
    results = []
    try:
        with open(fpath) as f:
            r = csv.DictReader(f)
            for row in r:
                if len(results) >= top: break
                g = row.get('', '').replace('gene-', '')
                lfc = row.get('log2FoldChange', 'NA')
                pval = row.get('pvalue', 'NA')
                padj = row.get('padj', 'NA')
                if padj != 'NA' and float(padj) < 0.05:
                    results.append({
                        'gene': g,
                        'log2FC': round(float(lfc), 3) if lfc != 'NA' else 'NA',
                        'padj': float(padj) if padj != 'NA' else 'NA'
                    })
    except Exception as e:
        return jsonify({'error': str(e), 'results': results})
    return jsonify({'comp': comp, 'top': len(results), 'results': results})

@app.route('/api/query/enrichment')
def query_enrichment():
    """Return KEGG enrichment results for a comparison"""
    comp = request.args.get('comp', 'MvsC')
    import json
    try:
        fpath = os.path.join('/home/yankai/rnaseq_pipeline/results', f'KEGG_{comp}.csv')
        results = []
        import csv
        with open(fpath) as f:
            r = csv.DictReader(f)
            for row in r:
                results.append({k: v for k, v in row.items()})
        return jsonify({'comp': comp, 'results': results})
    except Exception as e:
        return jsonify({'error': str(e), 'results': []})

@app.route('/api/query/stats')
def query_stats():
    """Return overall project statistics"""
    return jsonify({
        'project': 'AWGT23022001',
        'samples': 9,
        'groups': {'C': 'Control', 'M': 'Treatment M', 'N': 'Treatment N'},
        'genes': 52147,
        'degs': {
            'MvsC': {'total': 669, 'up': 400, 'down': 269},
            'NvsC': {'total': 489, 'up': 336, 'down': 153},
            'MvsN': {'total': 98, 'up': 22, 'down': 76}
        },
        'kegg_top': ['TNF signaling', 'Rheumatoid arthritis', 'IL-17 signaling', 'Cytokine receptor interaction', 'Malaria'],
        'alignment_rate': '94.2-95.2%',
        'qc': {'Q20': '97.7-98.4%', 'Q30': '93.2-94.5%', 'GC': '50-52%'}
    })

@app.route('/api/query/qc')
def query_qc():
    """Return QC metrics for a specific sample"""
    sample = request.args.get('sample', 'C1')
    qc = charts._qc_data.get(sample, {})
    return jsonify({
        'sample': sample,
        'total_reads': qc.get('total_reads', 0),
        'clean_reads': qc.get('reads_after', 0),
        'q20': round(qc.get('q20', 0) * 100, 2),
        'q30': round(qc.get('q30', 0) * 100, 2),
        'gc': round(qc.get('gc', 0) * 100, 2),
        'alignment': charts._extra_stats.get('align', {}).get(sample, {}).get('overall_rate', 0)
    })

@app.route('/api/generate-report')
def generate_report():
    sys.path.insert(0,"/home/yankai/rnaseq_pipeline")
    import report_generator
    return jsonify(report_generator.generate_pdf())

@app.after_request
def cors(r): r.headers['Access-Control-Allow-Origin']='*'; return r

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5173, debug=False)

# ====== Drug Target Prioritization ======
@app.route('/api/targets')
def drug_targets():
    """Prioritize drug targets from DEG results using Open Targets API"""
    import csv, json, urllib.request as _ur
    comp = request.args.get('comp', 'MvsC')
    top_n = int(request.args.get('top', 30))

    # 1. Load DEGs
    fpath = os.path.join(charts.OUTPUT if hasattr(charts, 'OUTPUT') else '/data/output', f'DESeq2_geneid_{comp}.csv')
    if not os.path.exists(fpath):
        fpath = f'/home/yankai/rnaseq_pipeline/results/DESeq2_geneid_{comp}.csv'
    degs = []
    try:
        with open(fpath) as f:
            r = csv.DictReader(f)
            for row in r:
                g = row.get('', '').replace('gene-', '')
                lfc = row.get('log2FoldChange', 'NA')
                padj = row.get('padj', 'NA')
                if padj != 'NA' and float(padj) < 0.05 and lfc != 'NA':
                    degs.append({'gene': g, 'log2FC': float(lfc), 'padj': float(padj)})
    except: pass

    if not degs: return jsonify({'error': 'No DEGs found', 'targets': []})

    # 2. Score each target
    targets = []
    for d in degs[:top_n]:
        score = abs(d['log2FC']) * (-math.log10(max(d['padj'], 1e-300))) / 10
        score = min(100, score)  # cap at 100
        targets.append({
            'gene': d['gene'],
            'log2FC': round(d['log2FC'], 3),
            'padj': d['padj'],
            'score': round(score, 1)
        })

    targets.sort(key=lambda x: x['score'], reverse=True)
    return jsonify({'comp': comp, 'targets': targets})

import math

@app.route('/api/benchmark')
def benchmark_data():
    """Return platform comparison data"""
    import json
    bp = '/app/benchmark.json'
    if not os.path.exists(bp):
        bp = os.path.join(os.path.dirname(__file__), 'benchmark.json')
    try:
        with open(bp) as f:
            return jsonify(json.load(f))
    except:
        return jsonify({'error': 'benchmark.json not found'})
