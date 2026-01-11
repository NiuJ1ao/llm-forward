from types import SimpleNamespace

import pytest

import backend.proxy as proxy_module
from backend.proxy import forward_request


class FakeResponse:
    def __init__(self, status: int, headers: dict[str, str], body: bytes):
        self.status = status
        self.headers = headers
        self._body = body

    async def read(self):
        return self._body


class FakeContext:
    def __init__(self, response: FakeResponse):
        self._response = response

    async def __aenter__(self):
        return self._response

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, response: FakeResponse, capture: dict, **kwargs):
        self._response = response
        self._capture = capture
        self._capture["session_kwargs"] = kwargs

    def request(self, method, url, headers=None, params=None, data=None):
        self._capture["method"] = method
        self._capture["url"] = url
        self._capture["headers"] = dict(headers or {})
        self._capture["params"] = params
        self._capture["data"] = data
        return FakeContext(self._response)

    async def close(self):
        self._capture["closed"] = True


class FakeUsageSink:
    def __init__(self):
        self.records = []

    async def record(self, usage):
        self.records.append(usage)


@pytest.mark.asyncio
async def test_forward_request_strips_hop_headers_and_records_usage(monkeypatch):
    capture = {}
    response_body = (
        b'{"usage":{"prompt_tokens":1,"completion_tokens":2,"total_tokens":3}}'
    )
    fake_response = FakeResponse(
        status=200,
        headers={"content-type": "application/json", "x-upstream": "1"},
        body=response_body,
    )

    def fake_client_session(**kwargs):
        return FakeSession(fake_response, capture, **kwargs)

    fake_usage = FakeUsageSink()
    monkeypatch.setattr(proxy_module.aiohttp, "ClientSession", fake_client_session)
    monkeypatch.setattr(proxy_module, "USAGE_SINK", fake_usage)

    request = SimpleNamespace(
        method="POST",
        headers={
            "Authorization": "Bearer client-key",
            "Content-Length": "123",
            "Connection": "keep-alive",
            "X-Request-Id": "abc",
        },
        query_params={},
        state=SimpleNamespace(owner="alice", model="gpt-ok", stream=False),
        path_params={"provider": "openai"},
    )
    body = b'{"model":"gpt-ok"}'

    response = await forward_request(
        request=request,
        target_url="http://upstream/v1/chat",
        provider_api_key="provider-key",
        body=body,
    )

    assert response.status_code == 200
    assert response.body == response_body
    assert response.headers.get("x-upstream") == "1"
    assert capture["method"] == "POST"
    assert capture["url"] == "http://upstream/v1/chat"
    assert capture["params"] == {}
    assert capture["data"] == body
    assert capture["headers"]["Authorization"] == "Bearer provider-key"
    assert "Content-Length" not in capture["headers"]
    assert "Connection" not in capture["headers"]
    assert "Authorization" in capture["headers"]
    assert capture.get("closed") is True

    assert len(fake_usage.records) == 1
    record = fake_usage.records[0]
    assert record.owner == "alice"
    assert record.provider == "openai"
    assert record.model == "gpt-ok"
    assert record.status_code == 200
    assert record.bytes_in == len(body)
    assert record.bytes_out == len(response_body)
    assert record.prompt_tokens == 1
    assert record.completion_tokens == 2
    assert record.total_tokens == 3
