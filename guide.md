Option 2: Using uv (Python 3.11+ recommended)
```bash
rm -rf .venv outputs/
pyenv local 3.11.9  # or your preferred Python 3.11+
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
python main.py
```

For testing the POST
```bash
curl -X POST "http://localhost:8000/api/training/start" \
  -H "Content-Type: application/json" \
  -d '{"industry_focus": "Agriculture", "regulatory_framework": "EU", "training_level": "Begginer"}'
  ```

```bash
curl -X POST "http://localhost:8000/api/training/start" \
  -H "Content-Type: application/json" \
  -d '{"industry_focus": "Technology", "regulatory_framework": "EU", "training_level": "Intermediate"}'
  ```