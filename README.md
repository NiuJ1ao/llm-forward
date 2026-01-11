# A Naive LLM API Forward Gateway

Small gateway service that forwards LLM API requests and exposes a simple admin UI.

## What it does
- Routes requests to upstream providers.
- Centralizes provider API keys in one place.
- Issues gateway keys with per-key provider/model allowlists and optional expiration.
- Provides a lightweight UI to manage keys and configs.

## Setup
1. Create your config: copy `config_example.yaml` to `config.yaml` and edit as needed.
2. Install dependencies (for example, with `pip` or `uv`).
```
uv pip install -e .
```

## Run
Start the gateway proxy:
```
uvicorn backend.main:app --host 0.0.0.0 --port <port>
```

Start the administration web UI:
```
streamlit run webui/app.py
```
