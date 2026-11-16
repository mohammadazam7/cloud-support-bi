from dataclasses import replace
from pathlib import Path

import lkml
import pytest

from support_bi import lookml
from support_bi.cli import main
from support_bi.metrics import COMPONENTS, Kind, load

LOOKER = Path(__file__).resolve().parents[1] / "looker"


@pytest.fixture(scope="module")
def files() -> dict[str, str]:
    return lookml.render(load())


def _measures(text: str) -> dict[str, dict[str, str]]:
    [view] = lkml.load(text)["views"]
    return {m["name"]: m for m in view["measures"]}


def test_committed_lookml_matches_the_spec(files: dict[str, str]) -> None:
    for name, content in files.items():
        assert (LOOKER / name).read_text(encoding="utf-8") == content, "run `make lookml`"
    committed = {p.relative_to(LOOKER).as_posix() for p in LOOKER.rglob("*.lkml")}
    assert committed == set(files)


def test_every_file_parses_as_lookml(files: dict[str, str]) -> None:
    for content in files.values():
        assert lkml.load(content)


def test_every_metric_is_a_measure_in_exactly_one_view(files: dict[str, str]) -> None:
    defined = load()
    seen: list[str] = []
    for kind in Kind:
        measures = _measures(lookml.view(kind, defined))
        names = [n for n in measures if not n.endswith("_total")]
        assert names == [m.name for m in defined.values() if m.kind is kind]
        seen += names
    assert sorted(seen) == sorted(defined)


def test_ratio_measures_divide_sums_and_guard_against_zero() -> None:
    measures = _measures(lookml.view(Kind.RATIO, load()))
    rate = measures["escalation_rate"]
    assert rate["type"] == "number"
    assert rate["sql"] == "1.0 * ${escalated_cases_total} / NULLIF(${cases_total}, 0)"
    assert rate["value_format"] == "0.0%"
    assert measures["case_volume"]["sql"] == "${cases_total}"
    for component in COMPONENTS:
        assert measures[f"{component}_total"]["type"] == "sum"


def test_quantile_and_level_measures_use_the_right_aggregate() -> None:
    median = _measures(lookml.view(Kind.QUANTILE, load()))["median_first_response_minutes"]
    assert (median["type"], median["percentile"]) == ("percentile", "50")
    backlog = _measures(lookml.view(Kind.LEVEL, load()))["open_backlog"]
    # The backlog mart has a row per product and priority per day, so a plain average of
    # rows would understate it: sum within the day, then average over days.
    assert backlog["type"] == "number"
    assert backlog["sql"] == (
        "1.0 * SUM(${TABLE}.open_cases) / NULLIF(COUNT(DISTINCT ${TABLE}.backlog_date), 0)"
    )


def test_views_expose_only_dimensions_their_mart_has() -> None:
    def dims(kind: Kind) -> set[str]:
        [view] = lkml.load(lookml.view(kind, load()))["views"]
        return {d["name"] for d in view["dimensions"]}

    assert dims(Kind.RATIO) == {"product_code", "priority", "tier", "channel"}
    assert dims(Kind.LEVEL) == {"product_code", "priority"}


def test_model_has_one_explore_per_view(files: dict[str, str]) -> None:
    parsed = lkml.load(files["support_bi.model.lkml"])
    assert [e["name"] for e in parsed["explores"]] == [
        "agg_support_daily",
        "fct_cases",
        "fct_backlog_daily",
    ]


def test_labels_with_quotes_stay_valid() -> None:
    odd = replace(load()["csat_score"], label='The "CSAT"')
    [view] = lkml.load(lookml.view(Kind.RATIO, {"csat_score": odd}))["views"]
    assert view["measures"][-1]["label"] == 'The \\"CSAT\\"'


def test_cli_writes_the_project(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["lookml", "--out", str(tmp_path)]) == 0
    written = capsys.readouterr().out.split()
    assert len(written) == 4 and all(Path(p).exists() for p in written)
