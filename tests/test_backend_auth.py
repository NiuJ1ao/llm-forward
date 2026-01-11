import httpx
import pytest
from fastapi import FastAPI, Request

from backend.auth import authenticate_and_authorize
from backend.config import GatewayKeyModel


def build_app(provider_allowed_models, gateway_keys):
    app = FastAPI()

    @app.post("/auth/{provider}")
    async def auth_route(provider: str, request: Request):
        await authenticate_and_authorize(
            request,
            provider,
            provider_allowed_models,
            gateway_keys,
        )
        return {
            "owner": request.state.owner,
            "model": request.state.model,
            "stream": request.state.stream,
        }

    return app


@pytest.mark.asyncio
async def test_auth_success_sets_state():
    gateway_keys = {
        "test-key": GatewayKeyModel(
            owner="alice",
            providers=["openai"],
            models=["gpt-ok"],
        )
    }
    app = build_app(["gpt-ok"], gateway_keys)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/auth/openai",
            headers={"authorization": "Bearer test-key"},
            json={"model": "gpt-ok", "stream": True},
        )

    assert resp.status_code == 200
    assert resp.json() == {"owner": "alice", "model": "gpt-ok", "stream": True}


@pytest.mark.asyncio
async def test_auth_missing_key_rejected():
    gateway_keys = {
        "test-key": GatewayKeyModel(
            owner="alice",
            providers=["openai"],
            models=["gpt-ok"],
        )
    }
    app = build_app(["gpt-ok"], gateway_keys)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/auth/openai", json={"model": "gpt-ok"})

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_key_rejected():
    gateway_keys = {
        "test-key": GatewayKeyModel(
            owner="alice",
            providers=["openai"],
            models=["gpt-ok"],
        )
    }
    app = build_app(["gpt-ok"], gateway_keys)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/auth/openai",
            headers={"authorization": "Bearer wrong"},
            json={"model": "gpt-ok"},
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_auth_provider_not_allowed():
    gateway_keys = {
        "test-key": GatewayKeyModel(
            owner="alice",
            providers=["openai"],
            models=["gpt-ok"],
        )
    }
    app = build_app(["gpt-ok"], gateway_keys)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/auth/anthropic",
            headers={"authorization": "Bearer test-key"},
            json={"model": "gpt-ok"},
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_auth_model_not_allowed_by_key():
    gateway_keys = {
        "test-key": GatewayKeyModel(
            owner="alice",
            providers=["openai"],
            models=["gpt-ok"],
        )
    }
    app = build_app(["gpt-ok"], gateway_keys)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/auth/openai",
            headers={"authorization": "Bearer test-key"},
            json={"model": "gpt-bad"},
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_auth_model_not_allowed_by_provider():
    gateway_keys = {
        "test-key": GatewayKeyModel(
            owner="alice",
            providers=["openai"],
            models=["gpt-ok"],
        )
    }
    app = build_app(["gpt-other"], gateway_keys)
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/auth/openai",
            headers={"authorization": "Bearer test-key"},
            json={"model": "gpt-ok"},
        )

    assert resp.status_code == 403
