# usage_jsonl_writer.py
import json
from pathlib import Path
from datetime import date
from backend.usage import UsageRecord

USAGE_DIR = Path("usage")
USAGE_DIR.mkdir(exist_ok=True)


class JSONLUsageWriter:
    async def write(self, usage: UsageRecord):
        path = USAGE_DIR / f"usage-{date.today().isoformat()}.jsonl"
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(usage.__dict__, default=str) + "\n")
