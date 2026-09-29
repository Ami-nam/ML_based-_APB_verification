"""Convert cycle-level APB CSV traces into transfer records."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping


REQUIRED_COLUMNS = {
    "cycle",
    "psel",
    "penable",
    "pwrite",
    "paddr",
    "pwdata",
    "prdata",
    "pready",
}


@dataclass(frozen=True)
class TraceParseResult:
    """Parsed transfers and cycle-level protocol violations."""

    transactions: list[dict[str, int | bool]]
    violations: list[dict[str, int | str]]


def _number(value: object, field: str) -> int:
    text = str(value).strip().replace("_", "")
    if not text:
        return 0
    try:
        base = 16 if text.lower().lstrip("+-").startswith("0x") else 10
        return int(text, base)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {field}: {value!r}") from exc


def _bit(value: object, field: str) -> int:
    bit = _number(value, field)
    if bit not in (0, 1):
        raise ValueError(f"{field} must be 0 or 1, got {value!r}")
    return bit


def _normalize_row(row: Mapping[str, object], row_number: int) -> dict[str, int]:
    values = {str(key).strip().lower(): value for key, value in row.items() if key is not None}
    missing = REQUIRED_COLUMNS - values.keys()
    if missing:
        raise ValueError(f"Missing required APB columns: {', '.join(sorted(missing))}")

    normalized = {
        "cycle": _number(values["cycle"], "cycle"),
        "psel": _bit(values["psel"], "psel"),
        "penable": _bit(values["penable"], "penable"),
        "pwrite": _bit(values["pwrite"], "pwrite"),
        "paddr": _number(values["paddr"], "paddr"),
        "pwdata": _number(values["pwdata"], "pwdata"),
        "prdata": _number(values["prdata"], "prdata"),
        "pready": _bit(values["pready"], "pready"),
        "pslverr": _bit(values.get("pslverr", 0) or 0, "pslverr"),
    }
    if normalized["cycle"] < 0:
        raise ValueError(f"cycle must be non-negative (row {row_number})")
    return normalized


def parse_trace_rows(rows: Iterable[Mapping[str, object]]) -> TraceParseResult:
    """Parse sampled APB signals into completed and incomplete transfers.

    A setup phase starts a transfer. The parser checks address, direction, and
    write-data stability until an ACCESS cycle completes with PREADY high.
    """

    transactions: list[dict[str, int | bool]] = []
    violations: list[dict[str, int | str]] = []
    active: dict[str, int | bool] | None = None
    access_cycles = 0

    def report(cycle: int, message: str) -> None:
        violations.append({"cycle": cycle, "message": message})

    def finish(end_cycle: int, completed: bool, row: dict[str, int]) -> None:
        nonlocal active, access_cycles
        assert active is not None
        transactions.append(
            {
                "transaction_id": len(transactions),
                "start_cycle": int(active["start_cycle"]),
                "end_cycle": end_cycle,
                "address": int(active["address"]),
                "is_write": int(active["is_write"]),
                "write_data": int(active["write_data"]),
                "read_data": row["prdata"],
                "wait_cycles": max(access_cycles - 1, 0),
                "pslverr": row["pslverr"],
                "completed": completed,
                "protocol_error": bool(active["protocol_error"]),
            }
        )
        active = None
        access_cycles = 0

    for row_number, source_row in enumerate(rows, start=2):
        row = _normalize_row(source_row, row_number)
        cycle = row["cycle"]
        selected = row["psel"] == 1
        access = row["penable"] == 1

        if access and not selected:
            report(cycle, "PENABLE asserted while PSEL is low")
            if active is not None:
                active["protocol_error"] = True

        if selected and not access:
            if active is not None:
                report(cycle, "New setup phase started before the active transfer completed")
                active["protocol_error"] = True
                finish(cycle, False, row)
            active = {
                "start_cycle": cycle,
                "address": row["paddr"],
                "is_write": row["pwrite"],
                "write_data": row["pwdata"],
                "protocol_error": False,
            }
            access_cycles = 0
            continue

        if selected and access:
            if active is None:
                report(cycle, "ACCESS phase observed without a preceding SETUP phase")
                active = {
                    "start_cycle": cycle,
                    "address": row["paddr"],
                    "is_write": row["pwrite"],
                    "write_data": row["pwdata"],
                    "protocol_error": True,
                }
                access_cycles = 0

            stable_fields = ["paddr", "pwrite"]
            if active["is_write"]:
                stable_fields.append("pwdata")
            active_values = {
                "paddr": int(active["address"]),
                "pwrite": int(active["is_write"]),
                "pwdata": int(active["write_data"]),
            }
            for field in stable_fields:
                if row[field] != active_values[field]:
                    report(cycle, f"{field.upper()} changed during the transfer")
                    active["protocol_error"] = True

            access_cycles += 1
            if row["pready"]:
                finish(cycle, True, row)
            continue

        if active is not None:
            report(cycle, "Transfer returned to IDLE before PREADY completed ACCESS")
            active["protocol_error"] = True
            finish(cycle, False, row)

    if active is not None:
        end_cycle = int(active["start_cycle"])
        report(end_cycle, "Trace ended before the active transfer completed")
        active["protocol_error"] = True
        finish(end_cycle, False, {"prdata": 0, "pslverr": 0})

    return TraceParseResult(transactions=transactions, violations=violations)


def load_trace(path: str | Path) -> TraceParseResult:
    """Load and parse a cycle-level APB trace CSV."""

    with Path(path).open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError("Trace CSV is empty or has no header")
        headers = {name.strip().lower() for name in reader.fieldnames if name}
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise ValueError(f"Missing required APB columns: {', '.join(sorted(missing))}")
        return parse_trace_rows(reader)