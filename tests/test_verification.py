import unittest

from apb_ml_verification.data.synthetic import generate_trace
from apb_ml_verification.preprocessing import parse_trace_rows
from apb_ml_verification.verification import verification_metrics


class VerificationTests(unittest.TestCase):
    def test_clean_generated_trace_passes_protocol_checks(self):
        parsed = parse_trace_rows(generate_trace(transactions=10, seed=11))
        metrics = verification_metrics(parsed)

        self.assertEqual(metrics["transactions"], 10)
        self.assertEqual(metrics["protocol_violations"], 0)
        self.assertTrue(metrics["passed_protocol_checks"])

    def test_injected_address_change_fails_protocol_checks(self):
        parsed = parse_trace_rows(
            generate_trace(transactions=30, seed=11, inject_anomalies=True)
        )
        metrics = verification_metrics(parsed)

        self.assertGreater(metrics["protocol_violations"], 0)
        self.assertFalse(metrics["passed_protocol_checks"])


if __name__ == "__main__":
    unittest.main()