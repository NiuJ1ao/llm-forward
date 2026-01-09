import requests
from .paths import GATEWAY_BASE


def reload_gateway():
    return requests.post(
        f"{GATEWAY_BASE}/internal/reload-config",
        timeout=5,
    )


def get_status():
    return requests.get(
        f"{GATEWAY_BASE}/internal/config/status",
        timeout=5,
    )
