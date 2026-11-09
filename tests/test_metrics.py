from pathlib import Path

import pytest

from support_bi import metrics
from support_bi.cli import main
from support_bi.metrics import Kind, Metric, MetricError, load, sql

DOCS = Path(__file__).resolve().parents[1] / "docs" / "metric_dictionary.md"


def test_spec_loads_and_covers_the_core_metrics() -> None:
    defined = load()
    for name in [
        "first_response_sla_attainment",
        "mean_resolution_hours",
        "escalation_rate",
        "reopen_rate",
        "csat_score",
        "open_backlog",
    ]:
        assert name in defined


def test_committed_dictionary_matches_the_spec() -> None:
    assert DOCS.read_text(encoding="utf-8") == metrics.dictionary(load()), "run `make metrics`"


@pytest.mark.parametrize(
    "fields",
    [
        {"kind": Kind.RATIO, "numerator": "nope", "denominator": "cases"},
        {"kind": Kind.RATIO, "numerator": "cases", "denominator": "nope"},
        {"kind": Kind.QUANTILE, "column": "first_response_minutes", "q": 1.5},
        {"kind": Kind.LEVEL, "column": "cases"},
    ],
)
def test_invalid_definitions_are_rejected(fields: dict[str, object]) -> None:
    base: dict[str, object] = {
        "name": "x",
        "label": "X",
        "unit": "u",
        "better": "higher",
        "owner": "o",
        "description": "d",
    }
    with pytest.raises(MetricError):
        Metric(**{**base, **fields}).validate()  # type: ignore[arg-type]


def test_ratio_sql_divides_sums_and_quotes_filters() -> None:
    m = load()["first_response_sla_attainment"]
    q = sql(m, group_by=["priority"], where={"product_code": "BQ'; drop"})
    assert "sum(first_response_sla_met_cases)" in q and "nullif(sum(cases), 0)" in q
    assert "'BQ''; drop'" in q
    assert q.endswith("group by priority order by priority")


def test_unsupported_grouping_is_rejected() -> None:
    with pytest.raises(MetricError):
        sql(load()["open_backlog"], group_by=["channel"])
    with pytest.raises(MetricError):
        sql(load()["csat_score"], where={"colour": "red"})


def test_cli_prints_sql(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["metric", "escalation_rate", "--by", "month"]) == 0
    assert "agg_support_daily" in capsys.readouterr().out
    assert main(["metric", "nope"]) == 2


def test_metrics_run_on_duckdb(tmp_path: Path) -> None:
    duckdb = pytest.importorskip("duckdb")
    db = tmp_path / "w.duckdb"
    with duckdb.connect(str(db)) as con:
        con.execute("create schema marts")
        con.execute(
            "create table marts.agg_support_daily as select * from (values "
            "(date '2025-01-01', 'BQ', 'P1', 'STD', 'web', 10, 8, 300.0, 50.0, 1, 1, 4, 18, 3),"
            "(date '2025-01-02', 'BQ', 'P1', 'STD', 'web', 30, 15, 900.0, 90.0, 3, 2, 6, 24, 4)"
            ") t(created_date, product_code, priority, tier, channel, cases, "
            "first_response_sla_met_cases, first_response_minutes_sum, resolution_hours_sum, "
            "escalated_cases, reopened_cases, csat_responses, csat_score_sum, "
            "csat_satisfied_responses)"
        )
        con.execute(
            "create table marts.fct_cases as select * from (values "
            "(date '2025-01-01', 'BQ', 'P1', 'STD', 'web', 10.0, 2.0, 5),"
            "(date '2025-01-01', 'BQ', 'P1', 'STD', 'web', 30.0, 4.0, null)"
            ") t(created_date, product_code, priority, tier_at_open, channel, "
            "first_response_minutes, resolution_hours, csat_score)"
        )
        con.execute(
            "create table marts.fct_backlog_daily as select * from (values "
            "(date '2025-01-01', 'BQ', 'P1', 4), (date '2025-01-01', 'GCE', 'P1', 2),"
            "(date '2025-01-02', 'BQ', 'P1', 6), (date '2025-01-02', 'GCE', 'P1', 0)"
            ") t(backlog_date, product_code, priority, open_cases)"
        )
        defined = load()

        def value(name: str, **kw: object) -> float:
            return float(con.execute(sql(defined[name], **kw)).fetchall()[0][-1])  # type: ignore[arg-type]

        # 23 of 40 cases met the SLA: pooled, not the mean of 0.8 and 0.5.
        assert value("first_response_sla_attainment") == pytest.approx(23 / 40)
        assert value("csat_score") == pytest.approx(42 / 10)
        assert value("median_first_response_minutes") == pytest.approx(20.0)
        # Daily totals 6 and 6, so the mean level is 6.
        assert value("open_backlog") == pytest.approx(6.0)
        assert value("open_backlog", where={"product_code": "BQ"}) == pytest.approx(5.0)
    assert main(["metric", "case_volume", "--warehouse", str(db)]) == 0
