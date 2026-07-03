# Contributing to OmniSeq

Thank you for your interest in contributing! OmniSeq is an early-stage project and we welcome all forms of contribution.

## How to Contribute

### 🐛 Bug Reports

1. Search [existing issues](https://github.com/YankaiZheng/omniseq/issues) to avoid duplicates
2. Use the **Bug Report** template when creating a new issue
3. Include: your environment (OS, Docker version, WSL2 version), steps to reproduce, expected vs actual behavior, and error logs

### ✨ Feature Requests

Use the **Feature Request** template. Be specific about the use case and expected outcome.

### 🛠 Pull Requests

1. **Fork** → **Create branch** (`feature/xxx` or `fix/xxx`) → **Make changes** → **Test** → **Commit** → **Push** → **PR**
2. Verify Docker build: `docker build -t omniseq .`
3. Verify API: `curl http://localhost:5173/api/query/stats`

## Development Setup

```bash
git clone https://github.com/YankaiZheng/omniseq.git && cd omniseq
docker build -t omniseq .
docker-compose up -d
# Frontend: cd frontend && npm install && npm run dev
```

## Adding New Chart Functions

```python
def my_chart(param):
    """What this chart shows"""
    # Use real data only, never np.random
    data = load_real_data()
    lines = ['import matplotlib.pyplot as plt', 'fig,ax=plt.subplots(figsize=(8,6))', ...]
    return run(chr(10).join(lines))
```

Then register in `serve.py`:
```python
@app.route('/api/chart/my_chart')
def api_my_chart(): return jsonify(charts.my_chart())
```
