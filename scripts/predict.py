#!/usr/bin/env python3
"""Write transaction-level APB protocol and ML results to CSV."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd

from apb_ml_verification.preprocessing import load_trace
from apb_ml_verification.preprocessing.features import transaction_frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=Path("models/artifacts"))
    parser.add_argument("--output", type=Path, default=Path("predictions.csv"))
    args = parser.parse_args()

    parsed = load_trace(args.trace)
    frame = transaction_frame(parsed.transactions)
    detector = joblib.load(args.model_dir / "anomaly_detector.joblib")
    latency = joblib.load(args.model_dir / "latency_predictor.joblib")
    frame["ml_anomaly"] = detector.predict(frame)
    frame["predicted_wait_cycles"] = latency.predict(frame)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False)
    print(f"Wrote {len(frame)} transaction predictions to {args.output}")
    if parsed.violations:
        print(f"Protocol violations: {len(parsed.violations)}")


if __name__ == "__main__":
    main()