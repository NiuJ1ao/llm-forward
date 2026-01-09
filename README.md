# Simple LLM Forward Gateway

## Quick Start
Start gateway proxy
```
uvicorn backend.main:app --host 0.0.0.0 --port 18000
```

Start administration web UI
```
streamlit run webui/app.py
```