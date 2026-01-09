import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from dotenv import load_dotenv

from backend.config import ConfigStore, watch_config_file
from backend.auth import authenticate_and_authorize
from backend.proxy import forward_request
from backend.usage import USAGE_SINK, JSONLUsageWriter

load_dotenv()

USAGE_SINK.add_writer(JSONLUsageWriter())


async def on_startup():
    if not ConfigStore.load():
        raise RuntimeError(
            f"Initial config load failed: {ConfigStore.status()['last_error']}"
        )
    asyncio.create_task(watch_config_file())
    asyncio.create_task(USAGE_SINK.worker())


async def on_shutdown():
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    await on_startup()
    yield
    await on_shutdown()


app = FastAPI(title="LLM Transparent Gateway", lifespan=lifespan)


@app.api_route(
    "/proxy/{provider}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"]
)
async def gateway(provider: str, path: str, request: Request):
    snapshot = ConfigStore.get()
    cfg = snapshot.config

    provider_cfg = cfg.providers[provider]

    body = await authenticate_and_authorize(
        request,
        provider,
        provider_cfg.allowed_models,
        cfg.gateway_keys,
    )

    target_url = f"{provider_cfg.base_url}/{path}"

    return await forward_request(
        request,
        target_url,
        provider_cfg.api_key,
        body,
    )


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/internal/config/status")
async def config_status():
    return ConfigStore.status()


@app.post("/internal/reload-config")
async def reload_config():
    ok = ConfigStore.load()
    status = ConfigStore.status()

    if not ok:
        return {"status": "error", **status}

    return {"status": "ok", **status}
