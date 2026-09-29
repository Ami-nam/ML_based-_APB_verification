"""Prepare numeric transaction features for the ML models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


REQUEST_FEATURES = ["address_region", "is_write"]
ANOMALY_FEATURES = REQUEST_FEATURES
LATENCY_FEATURES = REQUEST_FEATURES


def transaction_frame(
    transactions: Sequence[Mapping[str, object]],
) -> pd.DataFrame:
    """Convert parsed transfers to a validated dataframe."""

    if not transactions:
        raise ValueError("No APB transactions were found in the trace")
    frame = pd.DataFrame.from_records(transactions)
    missing = set(ANOMALY_FEATURES) - set(frame.columns)
    if "address" not in frame.columns:
        missing.add("address")
    if missing:
        raise ValueError(f"Transactions are missing features: {', '.join(sorted(missing))}")
    frame["address_region"] = (pd.to_numeric(frame["address"], errors="raise") >> 8).astype(int)
    for column in set(ANOMALY_FEATURES) | {
        "wait_cycles",
        "completed",
        "protocol_error",
        "pslverr",
    }:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    return frame