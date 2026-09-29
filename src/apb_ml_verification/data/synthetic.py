"""Reproducible cycle-level APB trace generator for demos and tests."""

from __future__ import annotations

import random


TRACE_COLUMNS = [
    "cycle",
    "psel",
    "penable",
    "pwrite",
    "paddr",
    "pwdata",
    "prdata",
    "pready",
    "pslverr",
]


def generate_trace(
    transactions: int = 200,
    seed: int = 7,
    inject_anomalies: bool = False,
) -> list[dict[str, int]]:
    """Generate legal APB transfers, optionally adding latency outliers."""

    if transactions < 1:
        raise ValueError("transactions must be at least 1")

    rng = random.Random(seed)
    rows: list[dict[str, int]] = []
    cycle = 0

    def append(
        psel: int = 0,
        penable: int = 0,
        pwrite: int = 0,
        paddr: int = 0,
        pwdata: int = 0,
        prdata: int = 0,
        pready: int = 0,
        pslverr: int = 0,
    ) -> None:
        nonlocal cycle
        rows.append(
            {
                "cycle": cycle,
                "psel": psel,
                "penable": penable,
                "pwrite": pwrite,
                "paddr": paddr,
                "pwdata": pwdata,
                "prdata": prdata,
                "pready": pready,
                "pslverr": pslverr,
            }
        )
        cycle += 1

    for index in range(transactions):
        paddr = rng.randrange(256) * 4
        pwrite = rng.randrange(2)
        pwdata = rng.getrandbits(32) if pwrite else 0
        prdata = 0 if pwrite else rng.getrandbits(32)
        wait_cycles = (paddr // 256 + pwrite) % 4
        if inject_anomalies and index % 29 == 0:
            wait_cycles += 6
        pslverr = int(index > 0 and index % 97 == 0)

        append()
        append(1, 0, pwrite, paddr, pwdata, prdata, 0, pslverr)
        for access_index in range(wait_cycles + 1):
            append(
                1,
                1,
                pwrite,
                paddr,
                pwdata,
                prdata,
                int(access_index == wait_cycles),
                pslverr,
            )

    append()
    return rows