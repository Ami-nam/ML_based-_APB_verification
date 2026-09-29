"""Unsupervised detection of unusual APB transaction features."""

from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from apb_ml_verification.preprocessing.features import ANOMALY_FEATURES


class APBAnomalyDetector:
    def __init__(self, contamination: float = 0.05, random_state: int = 7):
        if not 0.0 < contamination <= 0.5:
            raise ValueError("contamination must be greater than 0 and at most 0.5")
        self.model = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            random_state=random_state,
        )
        self._fitted = False

    def fit(self, transactions: pd.DataFrame) -> "APBAnomalyDetector":
        self._validate(transactions)
        if len(transactions) < 5:
            raise ValueError("At least 5 transactions are required to train the anomaly detector")
        self.model.fit(transactions[ANOMALY_FEATURES])
        self._fitted = True
        return self

    def predict(self, transactions: pd.DataFrame) -> list[bool]:
        self._validate(transactions)
        if not self._fitted:
            raise RuntimeError("The anomaly detector must be fit before prediction")
        return (self.model.predict(transactions[ANOMALY_FEATURES]) == -1).tolist()

    @staticmethod
    def _validate(transactions: pd.DataFrame) -> None:
        missing = set(ANOMALY_FEATURES) - set(transactions.columns)
        if missing:
            raise ValueError(f"Transactions are missing features: {', '.join(sorted(missing))}")