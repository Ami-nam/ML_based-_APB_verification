# ML-Based APB Verification

An offline analysis toolkit for cycle-level AMBA APB traces. It combines deterministic protocol checks with lightweight machine-learning models for transaction anomaly detection and wait-state prediction.

## Trace format

Input is a CSV with one row per sampled clock cycle. Required columns are `cycle`, `psel`, `penable`, `pwrite`, `paddr`, `pwdata`, `prdata`, and `pready`. `pslverr` is optional. Signal names are case-insensitive; addresses and data may be decimal or `0x`-prefixed hexadecimal.

The parser extracts completed transfers and flags malformed setup/access sequences, changed controls, incomplete transfers, and access without setup. The ML anomaly model is a secondary signal; deterministic protocol violations remain independently reported.

## Quick start

Requires Python 3.10 or newer. On Ubuntu, if `venv` or `pip` is missing, install them first:

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
python scripts/generate_sample.py --output data/eval_trace.csv --seed 29
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

Models are trained on generated data by default; replace it with representative, correctly sampled APB traces before using predictions for engineering decisions. This toolkit does not replace simulation assertions or protocol sign-off.
