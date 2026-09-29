#!/usr/bin/env python3
"""Generate a reproducible APB waveform CSV for training or evaluation."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from apb_ml_verification.data.synthetic import TRACE_COLUMNS, generate_trace


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--transactions", type=int, default=200)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--inject-anomalies", action="store_true")
    args = parser.parse_args()

    rows = generate_trace(args.transactions, args.seed, args.inject_anomalies)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=TRACE_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} sampled cycles to {args.output}")


if __name__ == "__main__":
    main()