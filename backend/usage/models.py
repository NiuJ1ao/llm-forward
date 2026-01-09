from dataclasses import dataclass
from typing import Optional


@dataclass
class UsageRecord:
    timestamp: float
    owner: str
    provider: str
    model: Optional[str]
    status_code: int
    duration_ms: int
    bytes_in: int
    bytes_out: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
