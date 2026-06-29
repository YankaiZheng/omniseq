"""ML/DL modules for RNA-seq platform: VAE + GNN"""
import os, json, csv, math, re
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

def load_count_matrix(path=None):
    """Load count matrix, return (counts, sample_names, gene_names)"""
    if path is None:
        path = os.path.expanduser('~/rnaseq_pipeline/results/gene_counts_geneid.txt')
    counts_matrix = []
    short_names = []
    gene_names = []
    samples_raw = []
    with open(path) as f:
        in_data = False
        for line in f:
            line = line.rstrip('\r\n')
            if line.startswith('#'): continue
            if line.startswith('Geneid'):
                parts = line.split('\t')
                samples_raw = parts[6:]
                for sp in samples_raw:
                    m = re.search(r'/([CMN]\d+)\.bam', sp)
                    short_names.append(m.group(1) if m else sp)
                in_data = True; continue
            if not in_data: continue
            parts = line.split('\t')
            gene_names.append(parts[0].replace('gene-',''))
            row = [int(parts[j+6]) for j in range(len(samples_raw))]
            counts_matrix.append(row)
    
    counts = np.array(counts_matrix, dtype=np.float32)
    # log2 transform, pick top 500 variable genes
    log_counts = np.log2(counts + 1)
    variances = np.var(log_counts, axis=1)
    top_idx = np.argsort(variances)[-500:]
    data = log_counts[top_idx]
    # Z-score normalize
    data = (data - data.mean(axis=1, keepdims=True)) / (data.std(axis=1, keepdims=True) + 1e-8)
    return data.T, short_names, [gene_names[i] for i in top_idx]

# ============================================================
# Module 1: VAE Autoencoder
# ============================================================
class VAE(nn.Module):
    def __init__(self, input_dim, latent_dim=2, hidden_dims=None):
        super().__init__()
        if hidden_dims is None:
            hidden_dims = [max(32, input_dim//4), max(16, input_dim//8)]
        
        # Encoder
        encoder_layers = []
        prev_dim = input_dim
        for h in hidden_dims:
            encoder_layers.append(nn.Linear(prev_dim, h))
            encoder_layers.append(nn.BatchNorm1d(h))
            encoder_layers.append(nn.ReLU())
            prev_dim = h
        self.encoder = nn.Sequential(*encoder_layers)
        self.mu = nn.Linear(prev_dim, latent_dim)
        self.logvar = nn.Linear(prev_dim, latent_dim)
        
        # Decoder
        decoder_layers = []
        prev_dim = latent_dim
        for h in reversed(hidden_dims):
            decoder_layers.append(nn.Linear(prev_dim, h))
            decoder_layers.append(nn.BatchNorm1d(h))
            decoder_layers.append(nn.ReLU())
            prev_dim = h
        decoder_layers.append(nn.Linear(prev_dim, input_dim))
        self.decoder = nn.Sequential(*decoder_layers)
    
    def encode(self, x):
        h = self.encoder(x)
        return self.mu(h), self.logvar(h)
    
    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decoder(z), mu, logvar

def vae_loss(recon_x, x, mu, logvar, beta=1.0):
    """VAE loss: reconstruction + KL divergence"""
    recon_loss = F.mse_loss(recon_x, x, reduction='sum')
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_loss + beta * kl_loss

def run_vae_analysis(data=None, auto_tune=True):
    """
    VAE dimensionality reduction with auto grid search.
    Input: (n_samples, n_genes) numpy array
    Output: dict with latent coords, reconstruction error, training curve, best config
    """
    if data is None:
        data, sample_names, _ = load_count_matrix()
    else:
        sample_names = [f'S{i+1}' for i in range(len(data))]
    
    n_samples, n_genes = data.shape
    latent_dim = 2
    X_tensor = torch.tensor(data, dtype=torch.float32)
    
    if auto_tune and n_samples >= 6:
        # Grid search for best hyperparams
        configs = []
        for lr in [0.0001, 0.0005, 0.001]:
            for beta in [0.01, 0.1, 0.5, 1.0]:
                for h1 in [32, 64]:
                    for h2 in [8, 16]:
                        configs.append((lr, beta, h1, h2))
        
        best_loss = float('inf'); best_config = None; best_state = None
        for i, (lr, beta, h1, h2) in enumerate(configs[:96]):  # limit 96 configs
            torch.manual_seed(42)
            
            class SearchVAE(nn.Module):
                def __init__(self):
                    super().__init__()
                    self.enc = nn.Sequential(nn.Linear(n_genes,h1), nn.BatchNorm1d(h1), nn.ReLU(), 
                                            nn.Linear(h1,h2), nn.BatchNorm1d(h2), nn.ReLU())
                    self.mu_l = nn.Linear(h2,2); self.lv_l = nn.Linear(h2,2)
                    self.dec = nn.Sequential(nn.Linear(2,h2), nn.ReLU(), nn.Linear(h2,h1), nn.ReLU(), nn.Linear(h1,n_genes))
                def forward(self, x):
                    h = self.enc(x); m = self.mu_l(h); l = self.lv_l(h)
                    z = m + torch.randn_like(m) * torch.exp(0.5 * torch.clamp(l, -10, 10))
                    return self.dec(z), m, l
            
            m = SearchVAE(); opt = torch.optim.Adam(m.parameters(), lr=lr)
            for e in range(1000):
                opt.zero_grad()
                rec, mu, lv = m(X_tensor)
                loss = F.mse_loss(rec, X_tensor, reduction='sum') + beta * (-0.5 * torch.sum(1 + torch.clamp(lv,-10,10) - mu.pow(2) - torch.clamp(lv,-10,10).exp()))
                loss.backward(); opt.step()
            
            final_loss = loss.item()
            if final_loss < best_loss:
                best_loss = final_loss; best_config = (lr, beta, h1, h2)
                best_state = {k: v.clone() for k, v in m.state_dict().items()}
    else:
        best_config = (0.0001, 0.01, 32, 16)
    
    # Train final model with best config
    lr, beta, h1, h2 = best_config
    
    class FinalVAE(nn.Module):
        def __init__(self):
            super().__init__()
            self.enc = nn.Sequential(nn.Linear(n_genes,h1), nn.BatchNorm1d(h1), nn.ReLU(), 
                                    nn.Linear(h1,h2), nn.BatchNorm1d(h2), nn.ReLU())
            self.mu_l = nn.Linear(h2,2); self.lv_l = nn.Linear(h2,2)
            self.dec = nn.Sequential(nn.Linear(2,h2), nn.ReLU(), nn.Linear(h2,h1), nn.ReLU(), nn.Linear(h1,n_genes))
        def forward(self, x):
            h = self.enc(x); m = self.mu_l(h); l = self.lv_l(h)
            z = m + torch.randn_like(m) * torch.exp(0.5 * torch.clamp(l, -10, 10))
            return self.dec(z), m, l
    
    torch.manual_seed(42)
    model = FinalVAE()
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    losses = []
    n_epochs = min(5000, max(1000, 50000 // n_samples))
    
    for epoch in range(n_epochs):
        opt.zero_grad()
        rec, mu, lv = model(X_tensor)
        recon_loss = F.mse_loss(rec, X_tensor, reduction='sum')
        kl_loss = -0.5 * torch.sum(1 + torch.clamp(lv,-10,10) - mu.pow(2) - torch.clamp(lv,-10,10).exp())
        loss = recon_loss + beta * kl_loss
        loss.backward(); opt.step()
        losses.append(loss.item())
    
    with torch.no_grad():
        z = model.mu_l(model.enc(X_tensor)).numpy()
        recon_error = float(F.mse_loss(model(X_tensor)[0], X_tensor).item())
    
    return {
        'latent': [[float(z[i,0]), float(z[i,1])] for i in range(len(z))],
        'recon_error': round(recon_error, 4),
        'sample_names': sample_names,
        'latent_dim': 2,
        'architecture': f'{n_genes}->{h1}->{h2}->2',
        'epochs': n_epochs,
        'final_loss': round(losses[-1], 2),
        'loss_curve': [round(l, 2) for l in losses[::max(1, len(losses)//50)]],
        'config': {'lr': lr, 'beta': beta, 'h1': h1, 'h2': h2},
        'auto_tuned': auto_tune
    }

# ============================================================
# Module 2: GNN on PPI + Expression
# ============================================================
class GCNLayer(nn.Module):
    def __init__(self, in_dim, out_dim):
        super().__init__()
        self.linear = nn.Linear(in_dim, out_dim)
        self.bn = nn.BatchNorm1d(out_dim)
    
    def forward(self, x, adj):
        # x: (n_nodes, in_dim), adj: (n_nodes, n_nodes)
        support = self.linear(x)
        out = torch.mm(adj, support)
        return F.relu(self.bn(out))

class GeneGNN(nn.Module):
    def __init__(self, in_dim, hidden=32, out_dim=1):
        super().__init__()
        self.gcn1 = GCNLayer(in_dim, hidden)
        self.gcn2 = GCNLayer(hidden, hidden//2)
        self.scorer = nn.Linear(hidden//2, out_dim)
    
    def forward(self, x, adj):
        h = self.gcn1(x, adj)
        h = self.gcn2(h, adj)
        return self.scorer(h).squeeze(-1)

def load_ppi_expression(comp='MvsC', data=None, top_genes=100):
    """Load PPI network + expression data for GNN training"""
    import urllib.request
    
    # 1. Get top DEGs
    csv_path = os.path.expanduser(f'~/rnaseq_pipeline/results/DESeq2_geneid_{comp}.csv')
    degs = []
    with open(csv_path) as f:
        r = csv.DictReader(f)
        for row in r:
            g = row.get('', '').replace('gene-','')
            p = row.get('padj','NA')
            if p != 'NA' and float(p) < 0.05:
                degs.append(g)
    degs = degs[:top_genes]
    
    # 2. Get PPI edges from STRING
    ids = '%0d'.join(degs[:50])
    url = f'https://string-db.org/api/json/network?identifiers={ids}&species=9606&required_score=700'
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            ppi_data = json.loads(resp.read().decode())
    except:
        ppi_data = []
    
    # Build gene -> index mapping
    gene_to_idx = {g: i for i, g in enumerate(degs)}
    
    # Build adjacency + feature matrix
    n = len(degs)
    adj = np.zeros((n, n), dtype=np.float32)
    for item in ppi_data:
        a = item.get('preferredName_A','')
        b = item.get('preferredName_B','')
        score = float(item.get('score', 0)) / 1000.0
        if a in gene_to_idx and b in gene_to_idx:
            i, j = gene_to_idx[a], gene_to_idx[b]
            adj[i,j] = score
            adj[j,i] = score
    
    # Normalize adjacency
    deg = adj.sum(axis=1) + 1
    adj_norm = adj / np.sqrt(deg[:,None] * deg[None,:])
    
    # Expression features: log2FC + -log10(padj) from DESeq2
    features = np.zeros((n, 2))
    with open(csv_path) as f:
        r = csv.DictReader(f)
        for row in r:
            g = row.get('', '').replace('gene-','')
            if g in gene_to_idx:
                idx = gene_to_idx[g]
                lfc = float(row.get('log2FoldChange', 0)) if row.get('log2FoldChange','NA') != 'NA' else 0
                padj = float(row.get('padj', 1)) if row.get('padj','NA') != 'NA' else 1
                features[idx, 0] = np.clip(lfc, -6, 6)
                features[idx, 1] = -np.log10(max(padj, 1e-300))
    
    # Normalize features
    features = (features - features.mean(axis=0)) / (features.std(axis=0) + 1e-8)
    
    return degs, adj_norm, features

def run_gnn_analysis(comp='MvsC', data=None):
    """GNN gene prioritization on PPI + expression"""
    genes, adj, features = load_ppi_expression(comp, data)
    
    n_genes = len(genes)
    if n_genes < 5:
        return {'error': 'Too few genes for GNN', 'n_genes': n_genes}
    
    # Pseudo-labels: top 20% of |LFC| as "important"
    lfc_abs = np.abs(features[:, 0])
    threshold = np.percentile(lfc_abs, 80)
    labels = (lfc_abs >= threshold).astype(np.float32)
    
    # Train GNN
    X = torch.tensor(features, dtype=torch.float32)
    A = torch.tensor(adj, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.float32)
    
    model = GeneGNN(in_dim=features.shape[1], hidden=32, out_dim=1)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    
    losses = []
    model.train()
    for epoch in range(500):
        optimizer.zero_grad()
        scores = model(X, A)
        loss = F.binary_cross_entropy_with_logits(scores, y)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    
    # Get final scores
    model.eval()
    with torch.no_grad():
        final_scores = torch.sigmoid(model(X, A)).numpy()
    
    # Rank genes
    ranked = sorted(zip(genes, final_scores), key=lambda x: x[1], reverse=True)
    
    return {
        'top_genes': [(g, round(float(s), 4)) for g, s in ranked[:20]],
        'n_genes': n_genes,
        'n_edges': int(np.sum(adj > 0) // 2),
        'final_loss': round(losses[-1], 4),
        'loss_curve': [round(l, 4) for l in losses[::20]]
    }

if __name__ == '__main__':
    print("=== VAE Analysis ===")
    data, samples, genes = load_count_matrix()
    vae_result = run_vae_analysis(data)
    print(f"Latent dims: {vae_result['latent_dim']}")
    print(f"Recon error: {vae_result['recon_error']}")
    print(f"Latent coords: {vae_result['latent']}")
    
    print("\n=== GNN Analysis ===")
    gnn_result = run_gnn_analysis('MvsC')
    print(f"Genes: {gnn_result['n_genes']}, Edges: {gnn_result['n_edges']}")
    print(f"Top 5: {gnn_result['top_genes'][:5]}")
