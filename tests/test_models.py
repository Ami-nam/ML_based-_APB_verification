import unittest

from apb_ml_verification.data.synthetic import generate_trace
from apb_ml_verification.models import APBAnomalyDetector, APBLatencyPredictor
from apb_ml_verification.preprocessing import parse_trace_rows
from apb_ml_verification.preprocessing.features import ANOMALY_FEATURES, transaction_frame


class ModelTests(unittest.TestCase):
    def test_latency_prediction_generalizes_to_holdout_trace(self):
        train = parse_trace_rows(generate_trace(transactions=240, seed=3))
        evaluation = parse_trace_rows(generate_trace(transactions=80, seed=19))
        train_frame = transaction_frame(train.transactions)
        evaluation_frame = transaction_frame(evaluation.transactions)

        latency = APBLatencyPredictor().fit(train_frame)
        predictions = latency.predict(evaluation_frame.drop(columns=["wait_cycles"]))

        errors = [
            abs(actual - predicted)
            for actual, predicted in zip(evaluation_frame["wait_cycles"], predictions)
        ]
        self.assertLessEqual(sum(errors) / len(errors), 0.5)

    def test_detector_finds_legal_latency_outliers_without_label_leakage(self):
        baseline = parse_trace_rows(generate_trace(transactions=240, seed=5))
        anomalous_trace = parse_trace_rows(
            generate_trace(transactions=60, seed=17, inject_anomalies=True)
        )
        baseline_frame = transaction_frame(baseline.transactions)
        anomalous_frame = transaction_frame(anomalous_trace.transactions)

        detector = APBAnomalyDetector().fit(baseline_frame)
        predictions = detector.predict(anomalous_frame)
        expected_wait = (
            anomalous_frame["address_region"] + anomalous_frame["is_write"]
        ) % 4
        injected = anomalous_frame["wait_cycles"] > expected_wait + 1

        self.assertNotIn("protocol_error", ANOMALY_FEATURES)
        self.assertTrue(any(prediction and is_injected for prediction, is_injected in zip(predictions, injected)))
        self.assertTrue(all(anomalous_frame.loc[injected, "protocol_error"] == 0))


if __name__ == "__main__":
    unittest.main()