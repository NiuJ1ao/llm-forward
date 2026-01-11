import os

import pytest
from openai import OpenAI


@pytest.mark.integration
def test_seed_chat_completion_smoke():
    if not os.getenv("RUN_LIVE_TESTS"):
        pytest.skip("Set RUN_LIVE_TESTS=1 to run live integration tests")

    endpoint = "http://localhost:8000/proxy/seed"
    deployment_name = "doubao-seed-1-6-251015"
    api_key = "fk-test"

    client = OpenAI(base_url=f"{endpoint}", api_key=api_key)

    completion = client.chat.completions.create(
        model=deployment_name,
        messages=[
            {
                "role": "user",
                "content": "Hello",
            }
        ],
    )

    assert completion.choices[0].message is not None
