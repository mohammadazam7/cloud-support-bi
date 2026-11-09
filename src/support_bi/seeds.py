"""Write the catalog as dbt seed files.

The dimensions for products, priorities and tiers, and the first-response target for
every priority and tier pair, are seeded into the warehouse from :mod:`support_bi.catalog`.
Writing them from the catalog, rather than editing CSV files by hand, keeps the generator
and the metric layer on one definition of each SLA target. A test fails if the committed
seed files drift from the catalog.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from pathlib import Path

from support_bi.catalog import PRIORITIES, PRODUCTS, TIERS, first_response_target


def render() -> dict[str, str]:
    """File name to CSV text for every seed."""
    tables: dict[str, Sequence[Sequence[object]]] = {
        "products.csv": [["product_code", "product_name", "product_family"]]
        + [[p.code, p.name, p.family] for p in PRODUCTS],
        "priorities.csv": [["priority", "priority_label", "base_target_minutes", "priority_rank"]]
        + [[p.code, p.label, p.first_response_target_min, i] for i, p in enumerate(PRIORITIES, 1)],
        "tiers.csv": [["tier", "tier_name", "response_multiplier", "tier_rank"]]
        + [[t.code, t.name, t.response_multiplier, i] for i, t in enumerate(TIERS, 1)],
        "sla_targets.csv": [["priority", "tier", "first_response_target_minutes"]]
        + [[p.code, t.code, first_response_target(p, t)] for p in PRIORITIES for t in TIERS],
    }
    out: dict[str, str] = {}
    for name, rows in tables.items():
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerows(rows)
        out[name] = buf.getvalue()
    return out


def write_seeds(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in render().items():
        path = directory / name
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written
