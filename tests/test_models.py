import unittest

from apb_ml_verification.data.synthetic import generate_trace
from apb_ml_verification.models import APBAnomalyDetector, APBLatencyPredictor
from apb_ml_verification.preprocessing import parse_trace_rows
from apb_ml_verification.preprocessing.features import transaction_frame


class ModelTests(unittest.TestCase):
    def test_models_fit_and_predict(self):
        parsed = parse_trace_rows(generate_trace(transactions=20, seed=3))
        frame = transaction_frame(parsed.transactions)

        detector = APBAnomalyDetector().fit(frame)
        latency = APBLatencyPredictor().fit(frame)

        self.assertEqual(len(detector.predict(frame)), 20)
        self.assertEqual(len(latency.predict(frame)), 20)


if __name__ == "__main__":
    unittest.main()