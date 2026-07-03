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
    """Generate RNA-seq analysis reports (main + appendix)"""
    sys.path.insert(0, os.path.dirname(__file__))
    import report_generator
    rtype = request.args.get('type', 'both')
    return jsonify(report_generator.generate_pdf(rtype))

@app.route('/api/generate-report/main')
def generate_main():
    sys.path.insert(0, os.path.dirname(__file__))
    import report_generator
    return jsonify(report_generator.generate_main_pdf())

@app.route('/api/generate-report/appendix')
def generate_appendix():
    sys.path.insert(0, os.path.dirname(__file__))
    import report_generator
    return jsonify(report_generator.generate_appendix_pdf())

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

@app.route('/api/compute-stats')
def compute_stats():
    """Agent-triggered: compute extra_stats.json from pipeline output"""
    import csv, json, math, os, re, numpy as np
    
    output_dir = os.environ.get('OUTPUT_DIR', '/data/output')
    cnt_file = os.path.join(output_dir, 'gene_counts_geneid.txt')
    
    # Check if count matrix exists
    if not os.path.exists(cnt_file):
        cnt_file = os.path.expanduser('~/rnaseq_pipeline/results/gene_counts_geneid.txt')
    
    if not os.path.exists(cnt_file):
        return jsonify({'success': False, 'error': 'Count matrix not found. Run pipeline first.'})
    
    try:
        # Load count matrix
        samples = []; counts = {}; gene_names = []
        with open(cnt_file) as f:
            in_data = False; samples_raw = []
            for line in f:
                line = line.rstrip('\r\n')
                if line.startswith('#'): continue
                if line.startswith('Geneid'):
                    parts = line.split('\t'); samples_raw = parts[6:]
                    for sp in samples_raw:
                        m = re.search(r'/([CMN]\d+)\.bam', sp)
                        samples.append(m.group(1) if m else sp)
                    counts = {s: [] for s in samples}
                    in_data = True; continue
                if not in_data: continue
                parts = line.split('\t')
                gene_names.append(parts[0].replace('gene-',''))
                for j, sp in enumerate(samples_raw):
                    m = re.search(r'/([CMN]\d+)\.bam', sp)
                    sname = m.group(1) if m else sp
                    try: counts[sname].append(int(parts[j+6]))
                    except: counts[sname].append(0)
        
        n_genes = len(gene_names); n_samples = len(samples)
        
        # 1. Top 500 variable genes → PCA
        variances = []
        for i in range(n_genes):
            row = [counts[s][i] for s in samples]
            if max(row) > 10:
                log_row = [math.log2(v+1) for v in row]
                mean_val = sum(log_row)/len(log_row)
                var = sum((v-mean_val)**2 for v in log_row)/len(log_row)
                variances.append((var, i))
        variances.sort(reverse=True)
        top500_idx = [i for v,i in variances[:500]]
        
        data_matrix = []
        for i in top500_idx:
            log_row = [math.log2(counts[s][i]+1) for s in samples]
            mean_val = sum(log_row)/len(log_row)
            std_val = (sum((v-mean_val)**2 for v in log_row)/len(log_row))**0.5
            data_matrix.append([(v-mean_val)/std_val for v in log_row] if std_val > 0 else [0.0]*n_samples)
        
        data_matrix = np.array(data_matrix)
        U, S, Vt = np.linalg.svd(data_matrix - data_matrix.mean(axis=0), full_matrices=False)
        pca_x = [float(Vt[0][i]) for i in range(n_samples)]
        pca_y = [float(Vt[1][i]) for i in range(n_samples)]
        var_ratio = (S**2)/(S**2).sum()
        pca_var = [float(var_ratio[0]*100), float(var_ratio[1]*100)]
        
        # 2. Correlation matrix
        corr = np.zeros((n_samples, n_samples))
        for i in range(n_samples):
            for j in range(n_samples):
                xi = [math.log2(counts[s][k]+1) for k in range(min(500, n_genes)) if counts[samples[i]][k] > 0 or counts[samples[j]][k] > 0]
                xj = [math.log2(counts[s][k]+1) for k in range(min(500, n_genes)) if counts[samples[i]][k] > 0 or counts[samples[j]][k] > 0]
                n_min = min(len(xi), len(xj), 500)
                if n_min < 10: corr[i,j] = 0.85; continue
                mi = sum(xi[:n_min])/n_min; mj = sum(xj[:n_min])/n_min
                num = sum((xi[k]-mi)*(xj[k]-mj) for k in range(n_min))
                den = math.sqrt(sum((xi[k]-mi)**2 for k in range(n_min))*sum((xj[k]-mj)**2 for k in range(n_min)))
                corr[i,j] = round(num/den, 4) if den > 0 else 0.85
        corr = [[float(corr[i,j]) for j in range(n_samples)] for i in range(n_samples)]
        
        # 3. Top 20 heatmap data
        top20_idx = [i for v,i in variances[:20]]
        hmap = []; hmap_genes = []
        for i in top20_idx:
            log_row = [math.log2(counts[s][i]+1) for s in samples]
            mean_val = sum(log_row)/len(log_row)
            std_val = (sum((v-mean_val)**2 for v in log_row)/len(log_row))**0.5
            hmap.append([round((v-mean_val)/std_val,3) for v in log_row] if std_val > 0 else [0.0]*n_samples)
            hmap_genes.append(gene_names[i])
        
        # 4. FPKM per sample
        fpkm = {}
        for s in samples:
            vals = [math.log2(counts[s][i]+1) for i in range(n_genes) if counts[s][i] > 0]
            fpkm[s] = vals[::max(1, len(vals)//200)]
        
        # 5. Alignment data (from logs if available)
        align = {}
        log_dir = os.path.join(output_dir, 'logs')
        if not os.path.exists(log_dir):
            log_dir = os.environ.get('INPUT_DIR', '/data/input')
        for s in samples:
            logf = os.path.join(log_dir, f'{s}.log')
            if os.path.exists(logf):
                with open(logf) as f: text = f.read()
                m = re.search(r'([\d.]+)%\s+overall alignment rate', text)
                if m:
                    c1 = re.search(r'exactly 1 time[\s\S]*?([\d.]+)%', text)
                    cN = re.search(r'>1 times[\s\S]*?([\d.]+)%', text)
                    align[s] = {
                        'overall_rate': float(m.group(1)),
                        'concordant_1_pct': float(c1.group(1)) if c1 else 80,
                        'concordant_N_pct': float(cN.group(1)) if cN else 5,
                        'concordant_0_pct': round(100-float(m.group(1)), 1)
                    }
        
        # Save
        extra = {
            'pca_x': pca_x, 'pca_y': pca_y, 'pca_var': pca_var,
            'corr_matrix': corr, 'top50_data': hmap, 'top50_genes': hmap_genes,
            'fpkm_sample': fpkm, 'align': align, 'samples': samples,
            'col_labels': samples, 'col_order': list(range(n_samples)),
            'pca_note': 'From pipeline output, auto-computed by /api/compute-stats'
        }
        
        out_path = os.path.join(output_dir, 'extra_stats.json')
        with open(out_path, 'w') as f: json.dump(extra, f)
        
        return jsonify({
            'success': True, 
            'path': out_path,
            'pca_var_pc1': round(pca_var[0], 1),
            'samples': n_samples,
            'genes': n_genes
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/reload-stats')
def reload_stats():
    """Agent-triggered: hot-reload extra_stats after pipeline completes"""
    import json, os
    output_dir = os.environ.get('OUTPUT_DIR', '/data/output')
    epath = os.path.join(output_dir, 'extra_stats.json')
    
    if not os.path.exists(epath):
        epath = os.path.expanduser('~/rnaseq_pipeline/results/extra_stats.json')
    
    if not os.path.exists(epath):
        return jsonify({'success': False, 'error': f'extra_stats.json not found at {epath}'})
    
    try:
        with open(epath) as f:
            charts._extra_stats = json.load(f)
        charts._extra_loaded = len(charts._extra_stats.get('samples', [])) >= 6
        
        return jsonify({
            'success': True,
            'samples': len(charts._extra_stats.get('samples', [])),
            'pca_available': 'pca_x' in charts._extra_stats,
            'corr_available': 'corr_matrix' in charts._extra_stats,
            'fpkm_available': 'fpkm_sample' in charts._extra_stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
