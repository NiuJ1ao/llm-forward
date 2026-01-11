import os

import pytest
from openai import OpenAI


@pytest.mark.integration
def test_qwen_chat_completion_smoke():
    if not os.getenv("RUN_LIVE_TESTS"):
        pytest.skip("Set RUN_LIVE_TESTS=1 to run live integration tests")

    client = OpenAI(
        base_url="http://localhost:8000/proxy/qwen/",
        api_key="fk-test",
    )
    completion = client.chat.completions.create(
        model="qwen3-max",
        messages=[
            {"role": "user", "content": "Hello"},
        ],
    )

    assert completion.choices[0].message is not None
