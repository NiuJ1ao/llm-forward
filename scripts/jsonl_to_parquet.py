import json
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path

USAGE_DIR = Path("usage")
PARQUET_DIR = Path("usage_parquet")
PARQUET_DIR.mkdir(exist_ok=True)


def convert(jsonl_path: Path):
    rows = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))

    if not rows:
        return

    df = pd.DataFrame(rows)

    table = pa.Table.from_pandas(df)
    parquet_path = PARQUET_DIR / jsonl_path.with_suffix(".parquet").name

    pq.write_table(
        table,
        parquet_path,
        compression="zstd",
    )

    print(f"✔ wrote {parquet_path}")


def main():
    for jsonl in USAGE_DIR.glob("usage-*.jsonl"):
        parquet = PARQUET_DIR / jsonl.with_suffix(".parquet").name
        if parquet.exists():
            continue
        convert(jsonl)


if __name__ == "__main__":
    main()
