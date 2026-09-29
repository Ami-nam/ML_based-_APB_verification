"""Prepare numeric transaction features for the ML models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

import pandas as pd


ANOMALY_FEATURES = [
    "address",
    "is_write",
    "write_data",
    "read_data",
    "wait_cycles",
    "pslverr",
    "completed",
    "protocol_error",
]
LATENCY_FEATURES = ["address", "is_write", "write_data"]


def transaction_frame(
    transactions: Sequence[Mapping[str, object]],
) -> pd.DataFrame:
    """Convert parsed transfers to a validated dataframe."""

    if not transactions:
        raise ValueError("No APB transactions were found in the trace")
    frame = pd.DataFrame.from_records(transactions)
    missing = set(ANOMALY_FEATURES) - set(frame.columns)
    if missing:
        raise ValueError(f"Transactions are missing features: {', '.join(sorted(missing))}")
    for column in ANOMALY_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    return frame