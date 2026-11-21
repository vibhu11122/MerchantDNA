"""Make the generated data small enough to commit for Streamlit Community Cloud.

GitHub rejects files over 100 MB. The raw transactions table is ~103 MB, so it is rewritten
sorted by merchant with zstd compression (~96 MB, identical contents, and faster per-merchant
reads in the app). Run after `make all`, before committing the deploy data:

    .venv/bin/python tools/prepare_deploy.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LIMIT_MB = 99


def main() -> None:
    path = ROOT / "data" / "transactions.parquet"
    df = pd.read_parquet(path).sort_values(["merchant_id", "timestamp"], kind="stable")
    tmp = path.with_suffix(".tmp")
    df.to_parquet(tmp, index=False, compression="zstd", compression_level=19, row_group_size=100_000)
    tmp.replace(path)
    big = [(p.relative_to(ROOT), p.stat().st_size / 1e6) for d in ("data", "artifacts")
           for p in (ROOT / d).iterdir() if p.is_file() and p.stat().st_size / 1e6 > LIMIT_MB]
    for p, mb in big:
        print(f"WARNING: {p} is {mb:.0f} MB (GitHub limit 100 MB)")
    print(f"transactions.parquet: {path.stat().st_size / 1e6:.1f} MB")
    sys.exit(1 if big else 0)


if __name__ == "__main__":
    main()
