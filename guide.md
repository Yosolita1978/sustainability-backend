Option 2: Using uv (Python 3.11+ recommended)
```bash
rm -rf .venv outputs/
pyenv local 3.11.9  # or your preferred Python 3.11+
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
python main.py
```