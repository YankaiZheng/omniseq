#!/bin/bash
# Download reference genome for RNA-seq platform
# Run once: docker run --rm -v ref_data:/data/ref rnaseq-platform scripts/download_ref.sh
set -e

REF_DIR="${REF_DIR:-/data/ref}"
echo "Downloading GRCh38 reference to $REF_DIR ..."

# GRCh38 primary assembly
if [ ! -f "$REF_DIR/GRCh38.fa" ]; then
    echo "Downloading GRCh38 FASTA..."
    curl -L -o "$REF_DIR/GRCh38.fa.gz" \
        "https://genome-idx.s3.amazonaws.com/hisat/grch38_genome.tar.gz"
    tar -xzf "$REF_DIR/GRCh38.fa.gz" -C "$REF_DIR/"
fi

# GENCODE v44 GTF  
if [ ! -f "$REF_DIR/gencode.v44.annotation.gtf" ]; then
    echo "Downloading GENCODE v44 GTF..."
    curl -L -o "$REF_DIR/gencode.v44.annotation.gtf.gz" \
        "ftp://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_44/gencode.v44.annotation.gtf.gz"
    gunzip "$REF_DIR/gencode.v44.annotation.gtf.gz"
fi

# Create gene BED from GTF for RSeQC
if [ ! -f "$REF_DIR/human.bed" ]; then
    echo "Creating gene BED..."
    python3 -c "
gtf = '$REF_DIR/gencode.v44.annotation.gtf'
bed = '$REF_DIR/human.bed'
with open(gtf) as f, open(bed, 'w') as out:
    for line in f:
        if line.startswith('#'): continue
        parts = line.strip().split('\t')
        if len(parts) < 9: continue
        if parts[2] == 'exon':
            chrom, _, feat, start, end, _, strand, _, attr = parts
            gid = ''
            for kv in attr.split(';'):
                kv = kv.strip()
                if kv.startswith('gene_id '):
                    gid = kv.split('\"')[1] if '\"' in kv else kv.split()[1]
            if gid:
                out.write(f'{chrom}\t{int(start)-1}\t{end}\t{gid}\t0\t{strand}\n')
    "
fi

echo "Reference preparation complete."
ls -lh "$REF_DIR/"
