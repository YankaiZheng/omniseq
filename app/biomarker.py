"""Biomarker selection: Elastic Net + Stability Selection + Permutation Test"""
import os, csv, re, json
import numpy as np

def load_deg_matrix():
    """Load DEG-only log2 expression matrix (233 genes x 9 samples)"""
    deg_file = os.path.expanduser('~/rnaseq_pipeline/results/DESeq2_geneid_MvsC.csv')
    cnt_file = os.path.expanduser('~/rnaseq_pipeline/results/gene_counts_geneid.txt')
    
    deg_genes = set()
    with open(deg_file) as f:
        r = csv.DictReader(f)
        for row in r:
            g = row.get('','').replace('gene-','')
            lfc = row.get('log2FoldChange','NA'); padj = row.get('padj','NA')
            if padj != 'NA' and lfc != 'NA' and float(padj) < 0.05 and abs(float(lfc)) > 1:
                deg_genes.add(g)
    
    samples = []; deg_expr = {}
    with open(cnt_file) as f:
        for line in f:
            if line.startswith('#'): continue
            if line.startswith('Geneid'):
                parts = line.strip().split('\t')
                for sp in parts[6:]:
                    m = re.search(r'/([CMN]\d+)\.bam', sp)
                    samples.append(m.group(1) if m else sp)
                continue
            parts = line.strip().split('\t')
            gname = parts[0].replace('gene-','')
            if gname in deg_genes:
                deg_expr[gname] = [int(parts[j+6]) for j in range(len(samples))]
    
    gene_list = sorted(deg_expr.keys())
    X = np.array([deg_expr[g] for g in gene_list], dtype=float)  # (233, 9)
    X = np.log2(X + 1)  # log2 transform
    # Standardize: each gene across 9 samples
    X = (X - X.mean(axis=1, keepdims=True)) / (X.std(axis=1, keepdims=True) + 1e-8)
    X = X.T  # (9, 233) — samples x genes
    y = np.array([0,0,0,1,1,1,2,2,2])  # C=0, M=1, N=2
    return X, y, gene_list, samples

def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))

def elastic_net_coordinate_descent(X, y, alpha, l1_ratio, n_iter=2000):
    """
    Multi-class one-vs-rest elastic net via coordinate descent.
    Returns coefficient matrix (n_classes, n_features)
    """
    n_samples, n_features = X.shape
    classes = sorted(set(y.tolist() if hasattr(y,'tolist') else list(y)))
    n_classes = len(classes)
    
    W = np.zeros((n_classes, n_features))
    
    for k in range(n_classes):
        yk = (y == classes[k]).astype(float)
        # If all samples are in/not in this class, skip
        if yk.sum() == 0 or yk.sum() == n_samples:
            W[k, :] = 0
            continue
        
        w = np.zeros(n_features)
        for iteration in range(n_iter):
            w_old = w.copy()
            max_change = 0
            for j in range(n_features):
                # Compute residual without feature j
                r = yk - sigmoid(X @ w)
                # Add back feature j's contribution
                r = r + sigmoid(X[:, j] * w[j]) * w[j]
                # Gradient of logistic loss wrt w[j]
                grad = -np.dot(X[:, j], r) / n_samples
                # Elastic net update: soft thresholding with ridge penalty
                w_j_new = w[j] - 0.01 * grad  # learning rate = 0.01
                # Soft thresholding (L1)
                w_j_new = np.sign(w_j_new) * max(0, abs(w_j_new) - alpha * l1_ratio * 0.01)
                # Ridge (L2) shrinkage
                w_j_new = w_j_new / (1 + alpha * (1 - l1_ratio) * 0.01)
                change = abs(w_j_new - w[j])
                w[j] = w_j_new
                max_change = max(max_change, change)
            if max_change < 1e-5 and iteration > 100:
                break
        W[k, :] = w
    
    return W

def stability_selection(X, y, alphas, l1_ratio=0.5, n_bootstraps=500):
    """Stability selection: bootstrap + count how often each gene is selected"""
    n_samples, n_features = X.shape
    selection_counts = np.zeros(n_features)
    all_coefs = np.zeros(n_features)
    
    for b in range(n_bootstraps):
        # Bootstrap: sample 8/9 rows with replacement
        idx = np.random.choice(n_samples, size=max(3, n_samples-1), replace=True)
        Xb, yb = X[idx], y[idx]
        
        # Run elastic net with a few alphas
        best_alpha = alphas[len(alphas)//2]
        W = elastic_net_coordinate_descent(Xb, yb, best_alpha, l1_ratio, n_iter=500)
        
        # Count genes with non-zero coef in any class
        coef_mag = np.abs(W).sum(axis=0)  # sum across classes
        selected = coef_mag > 1e-6
        selection_counts += selected
        all_coefs += coef_mag
    
    # Frequency of selection
    freq = selection_counts / n_bootstraps
    avg_coef = all_coefs / max(n_bootstraps, 1)
    return freq, avg_coef

def loo_cv_elastic_net(X, y, alphas, l1_ratio=0.5):
    """
    Leave-one-out CV for elastic net.
    Returns best alpha, CV accuracy, and coefficients at best alpha
    """
    n_samples, n_features = X.shape
    best_acc = 0; best_alpha = alphas[0]; best_coef = None
    
    for alpha in alphas:
        correct = 0
        for i in range(n_samples):
            X_train = np.delete(X, i, axis=0)
            y_train = np.delete(y, i)
            X_test = X[i:i+1]
            y_test = y[i]
            
            W = elastic_net_coordinate_descent(X_train, y_train, alpha, l1_ratio, n_iter=1000)
            logits = X_test @ W.T
            pred = np.argmax(logits, axis=1)
            if pred[0] == y_test:
                correct += 1
        
        acc = correct / n_samples
        if acc > best_acc:
            best_acc = acc; best_alpha = alpha
            # Refit on all data
            best_coef = elastic_net_coordinate_descent(X, y, alpha, l1_ratio, n_iter=2000)
    
    return best_alpha, best_acc, best_coef

def permutation_test(X, y, best_alpha, l1_ratio, n_perm=500):
    """Permutation test: shuffle labels, see if real CV accuracy exceeds random"""
    n_samples = X.shape[0]
    
    # Real accuracy
    real_correct = 0
    for i in range(n_samples):
        X_train = np.delete(X, i, axis=0)
        y_train = np.delete(y, i)
        X_test = X[i:i+1]
        W = elastic_net_coordinate_descent(X_train, y_train, best_alpha, l1_ratio, n_iter=1000)
        logits = X_test @ W.T
        if np.argmax(logits) == y[i]:
            real_correct += 1
    real_acc = real_correct / n_samples
    
    # Permuted accuracies
    perm_accs = []
    for p in range(n_perm):
        y_perm = np.random.permutation(y.copy())
        correct = 0
        for i in range(n_samples):
            X_train = np.delete(X, i, axis=0)
            y_train = np.delete(y_perm, i)
            X_test = X[i:i+1]
            W = elastic_net_coordinate_descent(X_train, y_train, best_alpha, l1_ratio, n_iter=500)
            logits = X_test @ W.T
            if np.argmax(logits) == y_perm[i]:
                correct += 1
        perm_accs.append(correct / n_samples)
    
    perm_accs = np.array(perm_accs)
    p_value = (perm_accs >= real_acc).mean()
    return real_acc, perm_accs, p_value

def run_biomarker_analysis():
    print("Loading DEG data...")
    X, y, genes, samples = load_deg_matrix()
    print(f"  {X.shape[0]} samples, {X.shape[1]} genes ({len(set(y))} groups)")
    
    # 1. Elastic Net LOO CV
    alphas = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
    l1_ratio = 0.7  # 70% L1 (sparsity), 30% L2 (stability)
    
    print("\nRunning LOO CV Elastic Net...")
    best_alpha, cv_acc, best_coef = loo_cv_elastic_net(X, y, alphas, l1_ratio)
    coef_mag = np.abs(best_coef).sum(axis=0)
    n_selected = int((coef_mag > 1e-6).sum())
    print(f"  Best alpha: {best_alpha}, CV accuracy: {cv_acc:.2%}")
    print(f"  Selected genes: {n_selected}")
    
    # 2. Stability Selection
    print("\nRunning Stability Selection (500 bootstraps)...")
    freq, avg_coef = stability_selection(X, y, alphas[:4], l1_ratio, n_bootstraps=500)
    stable_genes = np.where(freq >= 0.8)[0]
    print(f"  Stable (>80%): {len(stable_genes)} genes")
    
    # 3. Permutation test
    print(f"\nRunning Permutation Test (500 permutations)...")
    real_acc, perm_accs, p_val = permutation_test(X, y, best_alpha, l1_ratio, n_perm=500)
    print(f"  Real LOO accuracy: {real_acc:.2%}")
    print(f"  Permuted mean: {perm_accs.mean():.2%}")
    print(f"  Permutation p-value: {p_val:.4f}")
    
    # Select final panel
    if len(stable_genes) >= 5:
        panel_idx = stable_genes
        panel_method = "stability_selection"
    else:
        # Fall back to top coef genes
        top_idx = np.argsort(coef_mag)[-15:]
        threshold = coef_mag[top_idx[0]]
        panel_idx = np.where(coef_mag >= threshold)[0]
        panel_method = "top_coefficient"
    
    panel_genes = [genes[i] for i in panel_idx]
    print(f"\nFinal biomarker panel ({panel_method}): {len(panel_genes)} genes")
    for i, g in enumerate(panel_genes):
        print(f"  {i+1}. {g} (coef={coef_mag[panel_idx[i]]:.4f}, freq={freq[panel_idx[i]]:.2%})")
    
    # Generate coef paths for visualization
    path_alphas = np.logspace(-3, -0.3, 20)
    coef_paths = []
    for alpha in path_alphas:
        W = elastic_net_coordinate_descent(X, y, alpha, l1_ratio, n_iter=1000)
        coef_paths.append(np.abs(W).sum(axis=0))
    coef_paths = np.array(coef_paths)  # (n_alphas, n_features)
    
    # LOO predictions for confusion matrix
    loo_preds = []; loo_true = []
    for i in range(X.shape[0]):
        Xt = np.delete(X, i, axis=0); yt = np.delete(y, i)
        Xv = X[i:i+1]
        W = elastic_net_coordinate_descent(Xt, yt, best_alpha, l1_ratio, n_iter=1000)
        logits = Xv @ W.T
        loo_preds.append(int(np.argmax(logits))); loo_true.append(int(y[i]))
    
    result = {
        'panel_genes': panel_genes,
        'n_panel': len(panel_genes),
        'cv_accuracy': round(float(cv_acc), 4),
        'permutation_p': round(float(p_val), 4),
        'stability_freq': {genes[i]: round(float(freq[i]), 3) for i in panel_idx},
        'best_alpha': float(best_alpha),
        'l1_ratio': l1_ratio,
        'panel_idx': panel_idx.tolist(),
        'coef_magnitudes': [round(float(coef_mag[i]), 4) for i in panel_idx],
        'coef_paths': coef_paths.tolist() if len(path_alphas) < 30 else coef_paths[::2].tolist(),
        'alphas': path_alphas.tolist() if len(path_alphas) < 30 else path_alphas[::2].tolist(),
        'loo_preds': loo_preds,
        'loo_true': loo_true,
        'samples': samples,
        'perm_accs': perm_accs.tolist(),
        'real_acc': float(real_acc),
    }
    
    with open('/tmp/biomarker_results.json', 'w') as f:
        json.dump(result, f)
    print(f"\nSaved /tmp/biomarker_results.json")
    return result

if __name__ == '__main__':
    run_biomarker_analysis()
