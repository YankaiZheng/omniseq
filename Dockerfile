FROM ubuntu:24.04
LABEL description="RNA-seq End-to-End Analysis Platform"
LABEL version="1.0"

ENV DEBIAN_FRONTEND=noninteractive \
    MAMBA_ROOT_PREFIX=/opt/mamba \
    PATH=/opt/mamba/bin:$PATH

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential \
    libcurl4-openssl-dev libxml2-dev libssl-dev libcairo2-dev \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
    libffi-dev libgirepository-1.0-1 \
    && rm -rf /var/lib/apt/lists/*

# Install micromamba
RUN curl -Ls https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xj -C /usr/local bin/micromamba \
    && micromamba shell init -s bash -q

# Copy env definitions (layer caching - only rebuild if yaml changes)
COPY envs/pipeline.yaml /tmp/envs/
COPY envs/renv.yaml /tmp/envs/
COPY envs/pyenv.yaml /tmp/envs/

# Create environments
RUN micromamba create -n pipeline -f /tmp/envs/pipeline.yaml -y \
    && micromamba clean -a -y -q
RUN micromamba create -n renv -f /tmp/envs/renv.yaml -y \
    && micromamba clean -a -y -q
RUN micromamba create -n pyenv -f /tmp/envs/pyenv.yaml -y \
    && micromamba clean -a -y -q

# Ensure R packages are available in renv
RUN micromamba run -n renv R -e 'library(DESeq2); library(ggplot2); library(pheatmap)' 2>/dev/null || true

# Install Python deps not in conda
RUN micromamba run -n renv pip install --no-cache-dir matplotlib-venn 2>/dev/null || true

# App directory
WORKDIR /app
COPY app/ .

# Reference / input / output volumes
RUN mkdir -p /data/ref /data/input /data/output
VOLUME ["/data/ref", "/data/input", "/data/output"]

ENV REF_DIR=/data/ref \
    INPUT_DIR=/data/input \
    OUTPUT_DIR=/data/output \
    PYTHONUNBUFFERED=1

EXPOSE 5173

CMD ["micromamba", "run", "-n", "pyenv", "python3", "serve.py"]
