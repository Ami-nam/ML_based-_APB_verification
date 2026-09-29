#!/usr/bin/env python3
"""Train the APB anomaly detector and wait-state predictor."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib

from apb_ml_verification.models import APBAnomalyDetector, APBLatencyPredictor
from apb_ml_verification.preprocessing import load_trace
from apb_ml_verification.preprocessing.features import transaction_frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=Path("models/artifacts"))
    parser.add_argument("--contamination", type=float, default=0.05)
    args = parser.parse_args()

    parsed = load_trace(args.trace)
    if parsed.violations:
        print(f"Warning: training trace contains {len(parsed.violations)} protocol violations")
    frame = transaction_frame(parsed.transactions)
    detector = APBAnomalyDetector(contamination=args.contamination).fit(frame)
    latency = APBLatencyPredictor().fit(frame)

    args.model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(detector, args.model_dir / "anomaly_detector.joblib")
    joblib.dump(latency, args.model_dir / "latency_predictor.joblib")
    print(f"Trained on {len(frame)} transactions; models saved to {args.model_dir}")


if __name__ == "__main__":
    main()