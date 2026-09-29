# ML-Based APB Verification

![CI](https://github.com/Ami-nam/ML_based-_APB_verification/actions/workflows/tests.yml/badge.svg)

An offline analysis toolkit for cycle-level AMBA APB traces. It combines deterministic protocol checks with lightweight machine-learning models for transaction anomaly detection and wait-state prediction.

## Trace format

Input is a CSV with one row per sampled clock cycle. Required columns are `cycle`, `psel`, `penable`, `pwrite`, `paddr`, `pwdata`, `prdata`, and `pready`. `pslverr` is optional. Signal names are case-insensitive; addresses and data may be decimal or `0x`-prefixed hexadecimal.

The parser extracts completed transfers and flags malformed setup/access sequences, changed controls, incomplete transfers, and access without setup. The ML anomaly model is a secondary signal; deterministic protocol violations remain independently reported.

## Quick start

Requires Python 3.8 or newer. On Ubuntu, if `venv` or `pip` is missing, install them first:

```bash
sudo apt update
sudo apt install python3-venv python3-pip
```

Then create the environment and install the project:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/generate_sample.py --output data/train_trace.csv --seed 7
python scripts/generate_sample.py --output data/eval_trace.csv --seed 29 --inject-anomalies
python scripts/train.py --trace data/train_trace.csv --model-dir models/artifacts
python scripts/evaluate.py --trace data/eval_trace.csv --model-dir models/artifacts
python scripts/predict.py --trace data/eval_trace.csv --model-dir models/artifacts
python -m pytest
```

## Commands

- `scripts/generate_sample.py`: create a reproducible synthetic APB waveform CSV.
- `scripts/train.py`: fit and save an Isolation Forest anomaly detector and a wait-state regressor.
- `scripts/evaluate.py`: print protocol and anomaly metrics for a trace.
- `scripts/predict.py`: analyze a trace and write transaction-level predictions to CSV.

## What is checked

The cycle parser reports ACCESS without SETUP, PENABLE without PSEL, control changes during ACCESS, transfers abandoned before PREADY, and traces that end mid-transfer. It also rejects malformed signal values and non-increasing cycle numbers. Each completed transfer records direction, byte address, data, wait-state count, and PSLVERR.

The automated tests cover legal transfers with wait states, common protocol violations, clean generated traces, and legal high-latency outliers. GitHub Actions runs the test suite and the train/evaluate/predict demo on supported Python versions.

## Verification and ML methodology

The deterministic trace checker owns APB protocol verdicts. The ML detector does not use `protocol_error`, completion status, or any other checker output as an input. Instead, a random-forest baseline predicts wait states from request-side features (address region and transfer direction); unusually large held-out latency residuals are flagged as behavioral anomalies. The latency model is evaluated on a separately generated trace, not its training data.

The included synthetic generator makes the demonstration reproducible and can inject legal transfers with unusually long ACCESS waits. Those should be reported as ML anomalies while still passing APB protocol checks. This is a methodology demo, not evidence of performance on silicon. Replace synthetic traces with representative simulator or hardware traces and report their provenance before drawing engineering conclusions. ML results supplement, and never replace, assertions, scoreboards, or protocol sign-off.
