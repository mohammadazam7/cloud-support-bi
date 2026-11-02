import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from support_bi.cli import main
from support_bi.generator import GeneratorConfig, generate
from support_bi.raw_zone import MANIFEST, verify_raw_zone, write_raw_zone

CFG = GeneratorConfig(seed=3, days=14, customers=40, agents=5, cases_per_day=30)


def test_write_then_verify_round_trip(tmp_path: Path) -> None:
    tables = generate(CFG)
    manifest = write_raw_zone(tables, tmp_path, CFG)
    assert verify_raw_zone(tmp_path) == []
    assert manifest["synthetic"] is True
    for name, table in tables.items():
        assert pq.read_table(tmp_path / name / f"{name}.parquet").equals(table)
        assert manifest["tables"][name]["rows"] == table.num_rows
    assert not list(tmp_path.rglob("*.tmp"))


def test_verify_detects_tampering(tmp_path: Path) -> None:
    write_raw_zone(generate(CFG), tmp_path, CFG)
    victim = tmp_path / "agents" / "agents.parquet"
    victim.write_bytes(victim.read_bytes() + b"x")
    assert verify_raw_zone(tmp_path) == ["agents: checksum mismatch"]
    (tmp_path / "cases" / "cases.parquet").unlink()
    assert "cases: file missing" in verify_raw_zone(tmp_path)


def test_verify_without_manifest(tmp_path: Path) -> None:
    assert verify_raw_zone(tmp_path) == [f"missing {MANIFEST}"]


def test_cli_generate_and_verify(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = tmp_path / "raw"
    code = main(
        ["generate", "--out", str(out), "--days", "7", "--customers", "20", "--agents", "4"]
    )
    assert code == 0
    assert "cases" in capsys.readouterr().out
    assert json.loads((out / MANIFEST).read_text())["generator"]["days"] == "7"
    assert main(["verify", "--out", str(out)]) == 0
    (out / MANIFEST).unlink()
    assert main(["verify", "--out", str(out)]) == 1
