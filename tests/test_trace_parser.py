import unittest

from apb_ml_verification.preprocessing import parse_trace_rows


class TraceParserTests(unittest.TestCase):
    def test_parses_wait_state_transfer(self):
        result = parse_trace_rows(
            [
                {"cycle": 1, "psel": 1, "penable": 0, "pwrite": 1,
                 "paddr": "0x20", "pwdata": "0xAB", "prdata": 0, "pready": 0},
                {"cycle": 2, "psel": 1, "penable": 1, "pwrite": 1,
                 "paddr": "0x20", "pwdata": "0xAB", "prdata": 0, "pready": 0},
                {"cycle": 3, "psel": 1, "penable": 1, "pwrite": 1,
                 "paddr": "0x20", "pwdata": "0xAB", "prdata": 0, "pready": 1},
            ]
        )

        self.assertEqual(len(result.transactions), 1)
        self.assertEqual(result.transactions[0]["address"], 0x20)
        self.assertEqual(result.transactions[0]["wait_cycles"], 1)
        self.assertTrue(result.transactions[0]["completed"])
        self.assertFalse(result.violations)

    def test_detects_access_without_setup(self):
        result = parse_trace_rows(
            [
                {"cycle": 7, "psel": 1, "penable": 1, "pwrite": 0,
                 "paddr": 4, "pwdata": 0, "prdata": 9, "pready": 1},
            ]
        )

        self.assertTrue(result.transactions[0]["protocol_error"])
        self.assertIn("without a preceding SETUP", result.violations[0]["message"])

    def test_detects_changed_address_in_access(self):
        result = parse_trace_rows(
            [
                {"cycle": 1, "psel": 1, "penable": 0, "pwrite": 0,
                 "paddr": 4, "pwdata": 0, "prdata": 0, "pready": 0},
                {"cycle": 2, "psel": 1, "penable": 1, "pwrite": 0,
                 "paddr": 8, "pwdata": 0, "prdata": 9, "pready": 1},
            ]
        )

        self.assertTrue(result.transactions[0]["protocol_error"])
        self.assertEqual(result.violations[0]["message"], "PADDR changed during the transfer")


if __name__ == "__main__":
    unittest.main()