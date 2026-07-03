# Contributing to OmniSeq

Thank you for your interest in contributing! OmniSeq is an early-stage project and we welcome all forms of contribution.

## How to Contribute

### 🐛 Bug Reports

1. Search [existing issues](https://github.com/YankaiZheng/omniseq/issues) to avoid duplicates
2. Use the **Bug Report** template when creating a new issue
3. Include:
   - Your environment (OS, Docker version, WSL2 version)
   - Steps to reproduce
   - Expected vs actual behavior
   - Error logs if available

### ✨ Feature Requests

Use the **Feature Request** template. Be specific about the use case and expected outcome.

### 🛠 Pull Requests

1. **Fork** the repository
2. **Create a branch**: `feature/your-feature` or `fix/your-bug`
3. **Make changes** following the code style below
4. **Test your changes**:
   ```bash
   # Verify Docker build
   docker build -t omniseq .
   
   # Start and verify the Flask API
   docker-compose up -d
   curl http://localhost:5173/api/query/stats
   ```
5. **Commit** with clear messages: `fix: ...` or `feat: ...` (Conventional Commits)
6. **Push** and create a Pull Request

### 📝 Code Style

- Python: Follow PEP 8
- TypeScript/React: 2-space indentation
- Commit messages: [Conventional Commits](https://www.conventionalcommits.org/)

### 🔬 Adding New Chart Functions

To add a new chart to `charts.py`:

```python
def my_chart(param1, param2):
    """Brief description of what this chart shows"""
    # 1. Load real data (never use np.random!)
    data = load_from_file('/path/to/real/data')
    
    # 2. Build matplotlib code string
    lines = [
        'import matplotlib.pyplot as plt',
        'fig,ax=plt.subplots(figsize=(8,6))',
        # ... plotting code
        'plt.tight_layout()',
    ]
    code = chr(10).join(lines)
    return run(code)
```

Then register it in `serve.py`:
```python
@app.route('/api/chart/my_chart')
def api_my_chart():
    return jsonify(charts.my_chart())
```

### 🧪 Testing

```bash
# Test chart generation
curl http://localhost:5173/api/chart/volcano/MvsC | python3 -c "import sys,json; print(json.load(sys.stdin)['success'])"

# Test query endpoint
curl http://localhost:5173/api/query/stats

# Test pipeline (requires FASTQ data)
# curl -X POST http://localhost:5173/api/run-pipeline
```

## Development Setup

```bash
# Clone with submodules
git clone https://github.com/YankaiZheng/omniseq.git && cd omniseq

# Build and start
docker build -t omniseq .
docker-compose up -d

# For frontend development:
cd frontend && npm install && npm run dev
```

## Questions?

Open a [GitHub Discussion](https://github.com/YankaiZheng/omniseq/discussions) or start an issue.
