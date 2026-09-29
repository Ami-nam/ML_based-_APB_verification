#!/usr/bin/env python3
"""Evaluate APB protocol, anomaly, and wait-state predictions."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
from sklearn.metrics import mean_absolute_error

from apb_ml_verification.preprocessing import load_trace
from apb_ml_verification.preprocessing.features import transaction_frame
from apb_ml_verification.verification import verification_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--model-dir", type=Path, default=Path("models/artifacts"))
    args = parser.parse_args()

    parsed = load_trace(args.trace)
    frame = transaction_frame(parsed.transactions)
    detector = joblib.load(args.model_dir / "anomaly_detector.joblib")
    latency = joblib.load(args.model_dir / "latency_predictor.joblib")
    anomalies = detector.predict(frame)
    predicted_waits = latency.predict(frame)

    for key, value in verification_metrics(parsed, anomalies).items():
        print(f"{key}: {value}")
    mae = mean_absolute_error(frame["wait_cycles"], predicted_waits)
    print(f"wait_state_prediction_mae_cycles: {mae:.3f}")


if __name__ == "__main__":
    main()