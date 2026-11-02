"""Write generated tables to the raw zone as Parquet, with a manifest.

Layout: ``<root>/<table>/<table>.parquet`` plus ``<root>/_manifest.json`` recording the
generator settings, row counts and a SHA-256 per file. Writing is atomic per file (write
to a temporary name, then rename), so an interrupted run never leaves a half-written
table that dbt would read as valid.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from support_bi.generator import GeneratorConfig, RawTables

log = logging.getLogger(__name__)

MANIFEST = "_manifest.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_raw_zone(tables: RawTables, root: Path, config: GeneratorConfig) -> dict[str, Any]:
    """Write every table under ``root`` and return the manifest that was saved."""
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, dict[str, Any]] = {}
    for name, table in tables.items():
        target = root / name / f"{name}.parquet"
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".parquet.tmp")
        pq.write_table(table, tmp, compression="zstd")
        os.replace(tmp, target)
        files[name] = {
            "path": str(target.relative_to(root)),
            "rows": table.num_rows,
            "sha256": _sha256(target),
        }
        log.info("wrote %s rows=%d", target, table.num_rows)
    manifest = {
        "generator": {k: str(v) for k, v in dataclasses.asdict(config).items()},
        "synthetic": True,
        "tables": files,
    }
    (root / MANIFEST).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def verify_raw_zone(root: Path) -> list[str]:
    """Problems found when checking files against the manifest; empty means consistent."""
    path = root / MANIFEST
    if not path.exists():
        return [f"missing {MANIFEST}"]
    manifest = json.loads(path.read_text())
    problems = []
    for name, meta in manifest["tables"].items():
        file = root / meta["path"]
        if not file.exists():
            problems.append(f"{name}: file missing")
        elif _sha256(file) != meta["sha256"]:
            problems.append(f"{name}: checksum mismatch")
        elif pq.ParquetFile(file).metadata.num_rows != meta["rows"]:
            problems.append(f"{name}: row count mismatch")
    return problems
