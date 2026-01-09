from fastapi import Request, HTTPException
from datetime import datetime, timezone
import json

from backend.config import GatewayKeyModel


async def authenticate_and_authorize(
    request: Request,
    provider: str,
    provider_allowed_models: list[str],
    gateway_keys: dict[str, GatewayKeyModel],
) -> bytes:
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing API key")

    api_key = auth.split(" ", 1)[1]
    key_cfg = gateway_keys.get(api_key)

    if not key_cfg:
        raise HTTPException(403, "Invalid API key")

    # ⏰ Expiration check
    if key_cfg.expires_at:
        if datetime.now(timezone.utc) >= key_cfg.expires_at:
            raise HTTPException(403, "API key expired")

    # 🔒 Provider allowlist
    if provider not in key_cfg.providers:
        raise HTTPException(403, "Provider not allowed")

    body = await request.body()

    # 🧠 Best-effort model extraction
    model = None
    stream = False
    try:
        payload = json.loads(body)
        model = payload.get("model")
        stream = bool(payload.get("stream", False))

        if model:
            if "*" not in key_cfg.models and model not in key_cfg.models:
                raise HTTPException(403, "Model not allowed")

            if (
                "*" not in provider_allowed_models
                and model not in provider_allowed_models
            ):
                raise HTTPException(403, "Model not supported by provider")
    except json.JSONDecodeError:
        pass  # opaque forward

    # 📎 Attach identity for usage metering / logging
    request.state.owner = key_cfg.owner
    request.state.model = model
    request.state.stream = stream

    return body
