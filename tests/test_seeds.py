from pathlib import Path

from support_bi.cli import main
from support_bi.seeds import render

SEEDS = Path(__file__).resolve().parents[1] / "dbt" / "seeds"


def test_committed_seeds_match_the_catalog() -> None:
    for name, text in render().items():
        assert (SEEDS / name).read_text(encoding="utf-8") == text, f"run `make seeds` ({name})"


def test_sla_targets_cover_every_pair() -> None:
    rows = render()["sla_targets.csv"].strip().splitlines()[1:]
    assert len(rows) == 12
    assert "P1,PREM,8" in rows and "P4,STD,480" in rows


def test_seeds_command_writes_files(tmp_path: Path) -> None:
    assert main(["seeds", "--out", str(tmp_path)]) == 0
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(render())
