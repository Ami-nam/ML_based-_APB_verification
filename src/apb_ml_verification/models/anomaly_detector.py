"""Unsupervised detection of unusual APB transaction features."""

from __future__ import annotations

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

from apb_ml_verification.preprocessing.features import ANOMALY_FEATURES


class APBAnomalyDetector:
    """Flag transfers whose wait states exceed a learned request baseline."""

    def __init__(self, quantile: float = 0.99, random_state: int = 7):
        if not 0.5 <= quantile < 1.0:
            raise ValueError("quantile must be at least 0.5 and less than 1.0")
        self.quantile = quantile
        self.random_state = random_state
        self.model = RandomForestRegressor(
            n_estimators=200,
            min_samples_leaf=2,
            random_state=random_state,
        )
        self.threshold: float | None = None
        self._fitted = False

    def fit(self, transactions: pd.DataFrame) -> "APBAnomalyDetector":
        self._validate(transactions, require_target=True)
        if len(transactions) < 20:
            raise ValueError("At least 20 baseline transactions are required to calibrate the detector")
        features = transactions[ANOMALY_FEATURES]
        target = transactions["wait_cycles"]
        train_x, calibration_x, train_y, calibration_y = train_test_split(
            features,
            target,
            test_size=0.25,
            random_state=self.random_state,
        )
        calibration_model = RandomForestRegressor(
            n_estimators=200,
            min_samples_leaf=2,
            random_state=self.random_state,
        )
        calibration_model.fit(train_x, train_y)
        residuals = np.abs(calibration_y.to_numpy() - calibration_model.predict(calibration_x))
        self.threshold = max(1.0, float(np.quantile(residuals, self.quantile)))
        self.model.fit(features, target)
        self._fitted = True
        return self

    def predict(self, transactions: pd.DataFrame) -> list[bool]:
        self._validate(transactions, require_target=True)
        if not self._fitted:
            raise RuntimeError("The anomaly detector must be fit before prediction")
        expected_wait = self.model.predict(transactions[ANOMALY_FEATURES])
        residuals = np.abs(transactions["wait_cycles"].to_numpy() - expected_wait)
        assert self.threshold is not None
        return (residuals > self.threshold).tolist()

    @staticmethod
    def _validate(transactions: pd.DataFrame, require_target: bool = False) -> None:
        missing = set(ANOMALY_FEATURES) - set(transactions.columns)
        if require_target and "wait_cycles" not in transactions.columns:
            missing.add("wait_cycles")
        if missing:
            raise ValueError(f"Transactions are missing features: {', '.join(sorted(missing))}")