import os
from pathlib import Path

# BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path("config.yaml")
PARQUET_DIR = Path("usage_parquet")

_gateway_host = os.getenv("GATEWAY_HOST", "localhost")
_gateway_port = os.getenv("GATEWAY_PORT", "8080")
GATEWAY_BASE = os.getenv(
    "GATEWAY_BASE",
    f"http://{_gateway_host}:{_gateway_port}",
)
