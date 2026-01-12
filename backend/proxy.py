from time import time
import json
import aiohttp
from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from backend.usage import UsageRecord, USAGE_SINK

HOP_BY_HOP_HEADERS = {
    "host",
    "content-length",
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


async def forward_request(
    request: Request,
    target_url: str,
    provider_api_key: str,
    body: bytes,
):
    start = time()
    bytes_in = len(body)

    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS and k.lower() != "authorization"
    }
    headers["Authorization"] = f"Bearer {provider_api_key}"

    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=None),
        auto_decompress=False,
    )

    # 🔀 NON-STREAMING: buffer once, parse usage
    if not getattr(request.state, "stream", False):
        async with session.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=request.query_params,
            data=body,
        ) as resp:
            raw = await resp.read()
            bytes_out = len(raw)

            prompt_tokens = None
            completion_tokens = None
            total_tokens = None
            try:
                data = json.loads(raw)
                usage = data.get("usage")
                if usage:
                    prompt_tokens = usage.get("prompt_tokens")
                    completion_tokens = usage.get("completion_tokens")
                    total_tokens = usage.get("total_tokens")
            except Exception:
                pass  # never break the response

            duration_ms = int((time() - start) * 1000)

            await USAGE_SINK.record(
                UsageRecord(
                    timestamp=time(),
                    owner=request.state.owner,
                    provider=request.path_params["provider"],
                    model=request.state.model,
                    status_code=resp.status,
                    duration_ms=duration_ms,
                    bytes_in=bytes_in,
                    bytes_out=bytes_out,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                )
            )

            await session.close()

            return Response(
                content=raw,
                status_code=resp.status,
                headers=dict(resp.headers),
                media_type=resp.headers.get("content-type"),
            )

    # STREAMING: do NOT attempt token tracking
    bytes_out = 0

    async def stream(resp):
        nonlocal bytes_out
        try:
            async for chunk in resp.content.iter_any():
                bytes_out += len(chunk)
                yield chunk
        except aiohttp.ClientConnectionError:
            # Upstream closed mid-stream; treat as EOF to avoid noisy TaskGroup errors.
            pass
        finally:
            duration_ms = int((time() - start) * 1000)

            await USAGE_SINK.record(
                UsageRecord(
                    timestamp=time(),
                    owner=request.state.owner,
                    provider=request.path_params["provider"],
                    model=request.state.model,
                    status_code=resp.status,
                    duration_ms=duration_ms,
                    bytes_in=bytes_in,
                    bytes_out=bytes_out,
                    prompt_tokens=None,
                    completion_tokens=None,
                    total_tokens=None,
                )
            )
            resp.close()
            await session.close()


    resp = await session.request(
        method=request.method,
        url=target_url,
        headers=headers,
        params=request.query_params,
        data=body
    )
    
    return StreamingResponse(
        stream(resp),
        status_code=resp.status,
        headers=dict(resp.headers),
        media_type=resp.headers.get("content-type")
    )
