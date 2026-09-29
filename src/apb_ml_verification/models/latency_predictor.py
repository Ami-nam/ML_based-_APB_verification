"""Predict APB wait states from request-side transaction features."""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from apb_ml_verification.preprocessing.features import LATENCY_FEATURES


class APBLatencyPredictor:
    def __init__(self, random_state: int = 7):
        self.model = RandomForestRegressor(
            n_estimators=150,
            min_samples_leaf=2,
            random_state=random_state,
        )
        self._fitted = False

    def fit(self, transactions: pd.DataFrame) -> "APBLatencyPredictor":
        self._validate(transactions, require_target=True)
        self.model.fit(transactions[LATENCY_FEATURES], transactions["wait_cycles"])
        self._fitted = True
        return self

    def predict(self, transactions: pd.DataFrame) -> list[float]:
        self._validate(transactions)
        if not self._fitted:
            raise RuntimeError("The latency predictor must be fit before prediction")
        return self.model.predict(transactions[LATENCY_FEATURES]).tolist()

    @staticmethod
    def _validate(transactions: pd.DataFrame, require_target: bool = False) -> None:
        required = set(LATENCY_FEATURES)
        if require_target:
            required.add("wait_cycles")
        missing = required - set(transactions.columns)
        if missing:
            raise ValueError(f"Transactions are missing features: {', '.join(sorted(missing))}")