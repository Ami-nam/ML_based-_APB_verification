"""Summaries for deterministic APB protocol checks and ML predictions."""

from __future__ import annotations

from apb_ml_verification.preprocessing.trace_parser import TraceParseResult


def verification_metrics(
    result: TraceParseResult,
    anomaly_predictions: list[bool] | None = None,
) -> dict[str, int | float | bool]:
    transactions = result.transactions
    completed = sum(bool(item["completed"]) for item in transactions)
    protocol_errors = sum(bool(item["protocol_error"]) for item in transactions)
    metrics: dict[str, int | float | bool] = {
        "transactions": len(transactions),
        "completed_transactions": completed,
        "incomplete_transactions": len(transactions) - completed,
        "protocol_violations": len(result.violations),
        "transactions_with_protocol_errors": protocol_errors,
        "pslverr_responses": sum(int(item["pslverr"]) for item in transactions),
        "passed_protocol_checks": not result.violations,
    }
    if anomaly_predictions is not None:
        if len(anomaly_predictions) != len(transactions):
            raise ValueError("Anomaly prediction count must match transaction count")
        metrics["ml_anomalies"] = sum(anomaly_predictions)
    return metrics