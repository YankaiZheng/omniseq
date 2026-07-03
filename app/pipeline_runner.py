#!/usr/bin/env python3
"""
pipeline_runner.py — 端到端 RNA-seq 管线编排器
用法:
  python pipeline_runner.py --fastq /path/to/fastq/ --output /path/to/output/
  python pipeline_runner.py --fastq /path/ --output /path/ --compare C,M,N  # 三组对比

被 serve.py 调用时通过 SSE 流式推送进度。
也支持独立命令行运行。
"""
import subprocess, os, sys, json, time, csv, math, queue, threading
from pathlib import Path
from collections import defaultdict

# ============================================================
# 默认配置
# ============================================================
# Load env-based overrides (Docker or local)
_ENV = os.environ
_REF = _ENV.get("REF_DIR", "/data/ref")
_INP = _ENV.get("INPUT_DIR", "/data/input")
_OUT = _ENV.get("OUTPUT_DIR", "/data/output")
_REMOTE = _ENV.get("REMOTE_SERVER", "")  # Empty = local only
_BAM_DIR = _ENV.get("BAM_DIR", _OUT)

DEFAULT_CONFIG = {
    "tools": {
        "fastp": _ENV.get("FASTP_PATH", "fastp"),
        "hisat2": _ENV.get("HISAT2_PATH", "hisat2"),
        "samtools": _ENV.get("SAMTOOLS_PATH", "samtools"),
        "featureCounts": _ENV.get("FEATURECOUNTS_PATH", "featureCounts"),
        "Rscript": _ENV.get("RSCRIPT_PATH", "Rscript"),
        "python": _ENV.get("PYTHON_PATH", "python3")
    },
    "reference": {
        "hisat2_index": _ENV.get("HISAT2_INDEX", os.path.join(_REF, "grch38_index")),
        "gtf": _ENV.get("GTF_FILE", os.path.join(_REF, "gencode.v44.annotation.gtf")),
        "genome": _ENV.get("GENOME", "GRCh38"),
        "remote_server": _REMOTE,
        "remote_align": bool(_ENV.get("REMOTE_ALIGN", "")) if _ENV.get("REMOTE_ALIGN") else False
    },
    "threads": int(_ENV.get("THREADS", "8")),
    "bam_dir": _BAM_DIR,
    "DESeq2_script": None,
    "kegg_offline_db": _ENV.get("KEGG_DB", os.path.join(_OUT, "kegg_offline.json"))
}

# ============================================================
# SSE 事件发送器
# ============================================================
class SSEEmitter:
    def __init__(self, callback=None):
        self.callback = callback  # 供 serve.py 注入的回调函数
        self.events = []          # 命令行模式存储事件
    
    def emit(self, step, status, msg="", extra=None):
        event = {"step": step, "status": status, "msg": msg, "timestamp": time.time()}
        if extra: event.update(extra)
        self.events.append(event)
        if self.callback:
            self.callback(event)
        else:
            print(f"[{status.upper()}] {step}: {msg}")
    
    def get_events(self):
        return self.events

# ============================================================
# 管线步骤实现
# ============================================================

class PipelineRunner:
    def __init__(self, fastq_dir, output_dir, config=None, emitter=None):
        self.fastq_dir = Path(fastq_dir)
        self.output_dir = Path(output_dir)
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.emitter = emitter or SSEEmitter()
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _find_fastq_pairs(self):
        """自动发现 FASTQ 配对文件"""
        fq_dir = self.fastq_dir
        pairs = []
        # 找所有 _1.clean.fq.gz 或 _1.fq.gz
        for f in sorted(fq_dir.glob("*_1*.fq.gz")):
            r2 = str(f).replace("_1.", "_2.")
            if os.path.exists(r2):
                sample = f.name.split("_")[0]
                pairs.append((sample, str(f), r2))
        if not pairs:
            for f in sorted(fq_dir.glob("*_1*.fastq.gz")):
                r2 = str(f).replace("_1.", "_2.")
                if os.path.exists(r2):
                    sample = f.name.split("_")[0]
                    pairs.append((sample, str(f), r2))
        return pairs
    
    def _index_exists(self):
        """检测 HISAT2 索引是否存在"""
        idx = self.config["reference"]["hisat2_index"]
        return os.path.exists(str(idx) + ".1.ht2") or os.path.exists(str(idx) + ".8.ht2")

    def _find_existing_bams(self, fastq_pairs):
        """在 output_dir、bam_dir 或 fastq 同级目录搜索已有 BAM"""
        bams = []
        search_dirs = [
            str(self.output_dir),
            self.config.get("bam_dir", ""),
            str(self.fastq_dir),
            os.environ.get("BAM_DIR", ""),
            os.path.join(os.environ.get("OUTPUT_DIR", "/data/output"), "bam"),
        ]
        for sample, _, _ in fastq_pairs:
            found = False
            for d in search_dirs:
                if not d: continue
                bam = Path(d) / f"{sample}.bam"
                if bam.exists():
                    bams.append(bam)
                    found = True
                    break
            if not found:
                # Try symlinked locations
                for d in search_dirs:
                    if not d: continue
                    for pat in [f"{sample}*.bam", f"{sample}*.sorted.bam"]:
                        matches = list(Path(d).glob(pat))
                        if matches and not str(matches[0]).endswith(".tmp."):
                            bams.append(matches[0])
                            found = True
                            break
                    if found: break
            if not found:
                self.emitter.emit("warn", "warn", f"{sample}: 未找到已有 BAM 文件")
        return bams

    def run(self):
        """执行完整管线"""
        self.emitter.emit("start", "running", "启动 RNA-seq 分析管线")
        
        # Step 1: 发现数据
        fastq_pairs = self._find_fastq_pairs()
        if not fastq_pairs:
            self.emitter.emit("error", "error", "未找到 FASTQ 文件")
            return False
        self.emitter.emit("data", "done", f"发现 {len(fastq_pairs)} 个样本: {', '.join(p[0] for p in fastq_pairs)}")
        
        # Step 2: 质控 (fastp) — skip if not needed
        if not self.config.get("skip_qc"):
            for sample, r1, r2 in fastq_pairs:
                self.emitter.emit("qc", "running", f"{sample}: fastp 质控中...")
                ok = self._run_fastp(sample, r1, r2)
                if ok: self.emitter.emit("qc", "done", f"{sample}: 质控完成")
        else:
            self.emitter.emit("qc", "done", "跳过质控（使用已有数据）")
        
        # Step 3: 比对 + 定量 (支持远程执行)
        counts_file = None
        if not self._index_exists() and self.config["reference"].get("remote_server"):
            # 尝试远程执行比对+定量
            self.emitter.emit("align", "info", "本地无索引,尝试远程服务器执行...")
            counts_file = self._run_remote_pipeline(fastq_pairs)
            if counts_file:
                n_genes = self._count_genes(counts_file)
                self.emitter.emit("align", "done", f"远程完成: {n_genes} 基因")
        else:
            # 本地执行比对
            bams = []
            if self._index_exists():
                for sample, r1, r2 in fastq_pairs:
                    self.emitter.emit("align", "running", f"{sample}: HISAT2 比对中...")
                    bam = self._run_hisat2(sample, r1, r2)
                    if bam:
                        bams.append(bam)
                        rate = self._get_alignment_rate(sample)
                        self.emitter.emit("align", "done", f"{sample}: {rate}", {"rate": rate})
            else:
                self.emitter.emit("align", "info", "搜索已有 BAM...")
                bams = self._find_existing_bams(fastq_pairs)
                if bams:
                    self.emitter.emit("align", "done", f"使用已有 {len(bams)} BAM", {"bams": len(bams)})
            
            if bams:
                self.emitter.emit("quant", "running", "featureCounts 定量中...")
                counts_file = self._run_featurecounts(bams)
                n_genes = self._count_genes(counts_file) if counts_file else 0
                self.emitter.emit("quant", "done", f"{n_genes} 个基因定量完成")
        
        if not counts_file or not os.path.exists(str(counts_file)):
            self.emitter.emit("error", "error", "定量失败,无法继续")
            return False
        
        n_genes = self._count_genes(counts_file)
        
        # Step 5: DESeq2
        self.emitter.emit("deg", "running", "DESeq2 差异分析中...")
        deg_files = self._run_deseq2(counts_file)
        deg_summary = self._summarize_degs(deg_files) if deg_files else {}
        msg = "  ".join(f"{k}:{v['total']}DEGs" for k,v in deg_summary.items())
        self.emitter.emit("deg", "done", msg, {"degs": deg_summary})
        
        # Step 6: KEGG
        self.emitter.emit("enrich", "running", "KEGG 富集中...")
        kegg_result = self._run_kegg(deg_files)
        n_pathways = sum(len(v) for v in (kegg_result or {}).values())
        self.emitter.emit("enrich", "done", f"{n_pathways} 条通路富集", {"kegg": kegg_result})
        
        # Step 7: 报告
        self.emitter.emit("report", "running", "生成 HTML 报告...")
        report_path = self._generate_report(fastq_pairs, bams, deg_summary, kegg_result)
        self.emitter.emit("report", "done", f"报告已生成: {report_path}")
        self.emitter.emit("complete", "done", "全部分析完成", {"report": str(report_path)})
        return True
    
    # ========== 质控 ==========
    def _run_fastp(self, sample, r1, r2):
        out1 = self.output_dir / f"{sample}_1.fastq.gz"
        out2 = self.output_dir / f"{sample}_2.fastq.gz"
        html = self.output_dir / f"{sample}_fastp.html"
        cmd = [
            self.config["tools"]["fastp"],
            "-i", r1, "-I", r2,
            "-o", str(out1), "-O", str(out2),
            "-h", str(html),
            "-j", str(self.output_dir / f"{sample}_fastp.json"),
            "-w", "4"
        ]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            return r.returncode == 0
        except:
            return False
    
    # ========== 比对 ==========
    def _run_hisat2(self, sample, r1, r2):
        index = self.config["reference"]["hisat2_index"]
        bam = self.output_dir / f"{sample}.bam"
        log = self.output_dir / f"{sample}_hisat2.log"
        cmd = f'{self.config["tools"]["hisat2"]} -p {self.config["threads"]} --dta -x {index} -1 {r1} -2 {r2} --summary-file {log} 2>/dev/null | {self.config["tools"]["samtools"]} sort -@ 4 -o {bam} -'
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=7200)
            if r.returncode == 0 and bam.exists():
                subprocess.run([self.config["tools"]["samtools"], "index", str(bam)], timeout=300)
                return bam
        except:
            pass
        return None
    
    def _get_alignment_rate(self, sample):
        log = self.output_dir / f"{sample}_hisat2.log"
        if log.exists():
            for line in log.read_text().split('\n'):
                if 'overall alignment rate' in line:
                    return line.split('%')[0] + '%'
        return "N/A"
    
    # ========== 定量 ==========
    def _run_featurecounts(self, bams):
        gtf = self.config["reference"]["gtf"]
        counts = self.output_dir / "counts.txt"
        # Filter GTF for gene_id lines
        fgtf = self.output_dir / "filtered.gtf"
        os.system(f"grep 'gene_id ' {gtf} > {fgtf}")
        
        cmd = [self.config["tools"]["featureCounts"], "-T", str(self.config["threads"]),
               "-p", "-t", "exon", "-g", "gene_id",
               "-a", str(fgtf), "-o", str(counts)] + [str(b) for b in bams]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            return counts if r.returncode == 0 else None
        except subprocess.TimeoutExpired:
            self.emitter.emit("quant", "error", "featureCounts 超时(2h)")
            return None
        except Exception as e:
            self.emitter.emit("quant", "error", f"featureCounts 异常: {str(e)[:100]}")
            return None
    
    def _count_genes(self, counts_file):
        n = 0
        with open(counts_file) as f:
            for line in f:
                if not line.startswith('#') and not line.startswith('!') and 'Geneid' not in line and '\t' in line:
                    n += 1
        return n
    
    # ========== 差异分析 ==========
    def _run_deseq2(self, counts_file):
        if not counts_file or not counts_file.exists():
            return None
        
        # 从 BAM 文件名自动推断分组 (C, M, N...)
        bams_in_counts = []
        with open(counts_file) as f:
            for line in f:
                if 'Geneid' in line:
                    bams_in_counts = [p.split('/')[-1].replace('.bam','') for p in line.strip().split('\t')[6:]]
                    break
        
        # 自动分组：按首字母
        groups = set()
        for b in bams_in_counts:
            prefix = b[0].upper()
            groups.add(prefix)
        groups = sorted(groups)
        
        rscript = f'''
library(DESeq2)
counts <- read.table("{counts_file}", header=TRUE, row.names=1, comment.char="#")
cc <- grep("bam$", colnames(counts))
cm <- as.matrix(round(counts[, cc]))
snames <- c({', '.join(f'"{b}"' for b in bams_in_counts)})
colnames(cm) <- snames
group_chars <- c({', '.join(f'"{b[0].upper()}"' for b in bams_in_counts)})
group <- factor(group_chars)
dds <- DESeqDataSetFromMatrix(countData=cm, colData=data.frame(row.names=snames, group=group), design=~group)
dds <- DESeq(dds)
'''
        # 生成所有组间对比
        deg_files = {}
        for i in range(len(groups)):
            for j in range(i+1, len(groups)):
                g1, g2 = groups[i], groups[j]
                rscript += f'''
res <- results(dds, contrast=c("group","{g1}","{g2}"))
res <- res[order(res$padj),]
write.csv(as.data.frame(res), "{self.output_dir}/DESeq2_{g1}vs{g2}.csv")
cat(sprintf("{g1}vs{g2}: %d DEGs\\n", sum(res$padj < 0.05, na.rm=TRUE)))
'''
                deg_files[f"{g1}vs{g2}"] = self.output_dir / f"DESeq2_{g1}vs{g2}.csv"
        
        # 写入并执行 R 脚本
        rscript_path = self.output_dir / "run_deseq2.R"
        with open(rscript_path, 'w') as f: f.write(rscript)
        
        try:
            r = subprocess.run([self.config["tools"]["Rscript"], str(rscript_path)],
                             capture_output=True, text=True, timeout=600,
                             env={**os.environ, "RENV_PYTHON": os.environ.get("RENV_PYTHON", "")})
            for line in r.stdout.split('\n'):
                if 'DEGs' in line:
                    self.emitter.emit("deg", "info", line.strip())
            return deg_files if r.returncode == 0 else None
        except:
            return None
    
    def _summarize_degs(self, deg_files):
        summary = {}
        for name, f in deg_files.items():
            if not f.exists(): continue
            total = up = down = 0
            with open(f) as fh:
                for row in csv.DictReader(fh):
                    try:
                        if float(row['padj']) < 0.05:
                            total += 1
                            if float(row['log2FoldChange']) > 0: up += 1
                            else: down += 1
                    except: pass
            summary[name] = {"total": total, "up": up, "down": down}
        return summary
    
    # ========== KEGG ==========
    def _run_kegg(self, deg_files):
        """使用离线 KEGG 数据库做富集分析"""
        db_path = self.config.get("kegg_offline_db") or os.path.join(os.path.dirname(__file__), "kegg_offline.json")
        if not os.path.exists(db_path):
            db_path = os.path.join(self.output_dir, "kegg_offline.json")
        if not os.path.exists(db_path):
            db_path = os.path.join(os.environ.get("OUTPUT_DIR", "/data/output"), "kegg_offline.json")
        if not os.path.exists(db_path):
            self.emitter.emit("enrich", "warn", "KEGG 离线数据库未找到")
            return {}
        
        with open(db_path) as f:
            db = json.load(f)
        
        # 读取每个对比的 top 200 DEGs
        results = {}
        for name, f in (deg_files or {}).items():
            if not f.exists(): continue
            genes = []
            with open(f) as fh:
                for row in csv.DictReader(fh):
                    try:
                        if float(row['padj']) < 0.05:
                            g = row[''].replace('gene-','').upper()
                            parts = g.split('-')
                            if len(parts)>1 and parts[-1].isdigit():
                                g = '-'.join(parts[:-1])
                            genes.append(g)
                            if len(genes) >= 200: break
                    except: pass
            
            deg_kegg = set()
            for g in genes:
                if g in db.get('symbol2kegg', {}):
                    deg_kegg.add(db['symbol2kegg'][g])
            
            # 统计每个通路的重叠
            pathway_hits = {}
            all_pathway_genes = db.get('pathway_genes', {})
            for pid, pgenes in all_pathway_genes.items():
                k = len(deg_kegg & set(pgenes))
                if k >= 2:
                    pathway_hits[pid] = k
            
            # 用超几何近似算 p 值
            enriched = []
            M = len(deg_kegg)
            N = db.get('total_genes', 20000)
            pathways = db.get('pathways', {})
            for pid, k in sorted(pathway_hits.items(), key=lambda x: -x[1]):
                n = len(all_pathway_genes.get(pid, []))
                a,b = k, n-k
                c,d = M-k, N-M-n+k
                if c<0 or d<0: continue
                try:
                    chi2 = N*(a*d-b*c)**2/(M*n*(N-M)*(N-n))
                    pv = math.exp(-chi2/2) if chi2>0 else 1.0
                except: pv = 1.0
                enriched.append({"pathway": pathways.get(pid, pid), "overlap": f"{k}/{n}", "pvalue": f"{pv:.1e}"})
            
            results[name] = enriched[:10]
        
        return results
    
    # ========== 远程执行 ==========
    def _run_remote_pipeline(self, fastq_pairs):
        """在远程服务器上运行 HISAT2 + featureCounts，下载 count 矩阵"""
        server = self.config["reference"].get("remote_server", "")
        if not server:
            return None
        
        idx = self.config["reference"]["hisat2_index"]
        gtf = self.config["reference"]["gtf"]
        remote_out = f"/tmp/rnaseq_e2e_{os.getpid()}"
        
        # Map local paths to server paths (configurable via env)
        remote_data_dir = os.environ.get("REMOTE_DATA_DIR", "/data/input")
        path_map = {}
        for sample, r1, r2 in fastq_pairs:
            for local, remote in [
                (os.environ.get("INPUT_DIR", "/data/input") + "/", remote_data_dir + "/"),
            ]:
                if local in r1:
                    path_map[r1] = remote + r1.split("/")[-1]
                    path_map[r2] = remote + r2.split("/")[-1]
        
        # Build remote commands
        ssh_cmds = f"mkdir -p {remote_out}\n"
        for sample, r1, r2 in fastq_pairs:
            r1_srv = path_map.get(r1, r1)
            r2_srv = path_map.get(r2, r2)
            ssh_cmds += f"source ~/miniconda3/etc/profile.d/conda.sh && conda activate hisat2 && echo '[{sample}] HISAT2...' && hisat2 -p 12 --dta -x {idx} -1 {r1_srv} -2 {r2_srv} --summary-file {remote_out}/{sample}.log 2>/dev/null | samtools sort -@ 4 -o {remote_out}/{sample}.bam - && echo '[{sample}] DONE' &\n"
        ssh_cmds += "wait\n"
        ssh_cmds += f"grep 'gene_id ' {gtf} > {remote_out}/filtered.gtf\n"
        ssh_cmds += f"/home/stu2/miniconda3/bin/featureCounts -T 16 -p -t exon -g gene_id -a {remote_out}/filtered.gtf -o {remote_out}/counts.txt"
        ssh_cmds += " " + " ".join(f"{remote_out}/{s}.bam" for s, _, _ in fastq_pairs)
        ssh_cmds += "\necho 'FEATURECOUNTS_DONE'\n"
        
        try:
            self.emitter.emit("align", "info", f"SSH 连接服务器,执行比对+定量 ({len(fastq_pairs)} 样本)...")
            r = subprocess.run(["ssh", server, "bash -s"], input=ssh_cmds,
                             capture_output=True, text=True, timeout=14400)
            
            if "FEATURECOUNTS_DONE" in r.stdout:
                counts_file = self.output_dir / "counts.txt"
                subprocess.run(["scp", f"{server}:{remote_out}/counts.txt", str(counts_file)], timeout=300)
                if counts_file.exists():
                    self.emitter.emit("quant", "done", "远程定量完成,counts已下载")
                    # Also get alignment logs for rates
                    for sample, _, _ in fastq_pairs:
                        try:
                            subprocess.run(["scp", f"{server}:{remote_out}/{sample}.log", 
                                          str(self.output_dir / f"{sample}_hisat2.log")], timeout=30)
                        except: pass
                    return counts_file
            self.emitter.emit("error", "error", f"远程管线失败: {r.stderr[:300] if r.stderr else 'no output'}")
        except Exception as e:
            self.emitter.emit("error", "error", f"远程异常: {e}")
        return None

    # ========== 报告 ==========
    def _generate_report(self, fastq_pairs, bams, deg_summary, kegg_result):
        """生成 HTML 报告"""
        samples_html = ""
        for s, r1, r2 in sorted(fastq_pairs):
            rate = self._get_alignment_rate(s)
            samples_html += f"<tr><td>{s}</td><td>{self._file_size(r1)}</td><td>{self._file_size(r2)}</td><td>{rate}</td></tr>"
        
        deg_html = ""
        for name, d in (deg_summary or {}).items():
            deg_html += f"<div class=m><div class=v>{d['total']}</div><div class=l>{name} DEGs</div></div>"
        
        kegg_html = ""
        for name, items in (kegg_result or {}).items():
            kegg_html += f"<h3>{name}</h3><table><tr><th>Pathway</th><th>Overlap</th><th>P-value</th></tr>"
            for r in (items or [])[:5]:
                kegg_html += f"<tr><td>{r['pathway']}</td><td>{r['overlap']}</td><td>{r['pvalue']}</td></tr>"
            kegg_html += "</table>"
        
        html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>RNA-seq Analysis Report</title>
<style>body{{font-family:Arial;max-width:1100px;margin:auto;padding:20px;background:#f9f9f9;color:#333}}
h1{{color:#326e8b}}h2{{color:#0a8a00;margin-top:30px}}table{{border-collapse:collapse;width:100%;background:white}}
td,th{{border:1px solid #ddd;padding:6px 10px;text-align:center;font-size:13px}}th{{background:#326e8b;color:#fff}}
.m{{display:inline-block;margin:8px 15px;padding:12px 18px;background:#f0f4f8;border-radius:8px;text-align:center}}
.v{{font-size:28px;font-weight:bold;color:#326e8b}}.l{{font-size:11px;color:#666}}</style></head><body>
<h1>RNA-seq Analysis Report</h1>
<h2>1. Samples & Alignment</h2>
<table><tr><th>Sample</th><th>Read1</th><th>Read2</th><th>Alignment</th></tr>{samples_html}</table>
<h2>2. Differential Expression</h2>{deg_html}
<h2>3. KEGG Enrichment</h2>{kegg_html}
<p style="margin-top:30px;font-size:11px;color:#999">Generated by pipeline_runner.py</p>
</body></html>'''
        
        report_path = self.output_dir / "report.html"
        with open(report_path, 'w') as f: f.write(html)
        return report_path
    
    def _file_size(self, path):
        try: sz = os.path.getsize(path)
        except: sz = 0
        if sz > 1e9: return f"{sz/1e9:.1f}GB"
        if sz > 1e6: return f"{sz/1e6:.0f}MB"
        return f"{sz}B"

# ============================================================
# 命令行入口
# ============================================================
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='RNA-seq Pipeline Runner')
    p.add_argument('--fastq', required=True, help='FASTQ directory')
    p.add_argument('--output', required=True, help='Output directory')
    p.add_argument('--config', help='Config JSON file')
    p.add_argument('--bam-dir', help='Directory with existing BAM files (skip alignment)')
    args = p.parse_args()
    
    config = DEFAULT_CONFIG
    if args.config and os.path.exists(args.config):
        with open(args.config) as f:
            config.update(json.load(f))
    if args.bam_dir:
        config['bam_dir'] = args.bam_dir
    
    runner = PipelineRunner(args.fastq, args.output, config)
    success = runner.run()
    sys.exit(0 if success else 1)
