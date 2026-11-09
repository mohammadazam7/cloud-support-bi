"""The governed metric layer.

Every support metric is defined once, in ``metrics/metrics.yml``. This module loads and
validates those definitions, turns a metric request into SQL against the marts, and
renders the metric dictionary, so dashboards, reports and ad hoc analysis all compute a
metric the same way.

Ratio metrics read the additive components in ``agg_support_daily`` and divide sums,
which is correct at any grain. Quantiles read ``fct_cases`` directly because they cannot
be built from sums.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

SPEC_PATH = Path(__file__).resolve().parents[2] / "metrics" / "metrics.yml"

# Columns a ratio metric may reference, and the dimensions a query may group or filter by.
COMPONENTS = frozenset(
    {
        "cases",
        "first_response_sla_met_cases",
        "first_response_minutes_sum",
        "resolution_hours_sum",
        "escalated_cases",
        "reopened_cases",
        "csat_responses",
        "csat_score_sum",
        "csat_satisfied_responses",
    }
)
CASE_COLUMNS = frozenset({"first_response_minutes", "resolution_hours", "csat_score"})
BACKLOG_COLUMNS = frozenset({"open_cases"})
DIMENSIONS: Mapping[str, Mapping[str, str]] = {
    # dimension -> column name in each source relation
    "date": {"ratio": "created_date", "quantile": "created_date", "level": "backlog_date"},
    "month": {
        "ratio": "date_trunc('month', created_date)",
        "quantile": "date_trunc('month', created_date)",
        "level": "date_trunc('month', backlog_date)",
    },
    "product_code": {"ratio": "product_code", "quantile": "product_code", "level": "product_code"},
    "priority": {"ratio": "priority", "quantile": "priority", "level": "priority"},
    "tier": {"ratio": "tier", "quantile": "tier_at_open"},
    "channel": {"ratio": "channel", "quantile": "channel"},
}
_NAME = re.compile(r"^[a-z][a-z0-9_]*$")


class Kind(Enum):
    RATIO = "ratio"
    QUANTILE = "quantile"
    LEVEL = "level"


class MetricError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Metric:
    name: str
    label: str
    kind: Kind
    unit: str
    better: str
    owner: str
    description: str
    numerator: str | None = None
    denominator: str | None = None
    column: str | None = None
    q: float | None = None

    def validate(self) -> None:
        if not _NAME.match(self.name):
            raise MetricError(f"{self.name!r}: names are lower_snake_case")
        if self.better not in {"higher", "lower", "neutral"}:
            raise MetricError(f"{self.name}: better must be higher, lower or neutral")
        if self.kind is Kind.RATIO:
            if self.numerator not in COMPONENTS:
                raise MetricError(f"{self.name}: unknown numerator {self.numerator!r}")
            if self.denominator is not None and self.denominator not in COMPONENTS:
                raise MetricError(f"{self.name}: unknown denominator {self.denominator!r}")
        elif self.kind is Kind.QUANTILE:
            if self.column not in CASE_COLUMNS or self.q is None or not 0 < self.q < 1:
                raise MetricError(f"{self.name}: quantile needs a case column and 0 < q < 1")
        elif self.column not in BACKLOG_COLUMNS:
            raise MetricError(f"{self.name}: level needs a backlog column")


def load(path: Path = SPEC_PATH) -> dict[str, Metric]:
    """Every metric in the spec, validated, keyed by name."""
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    metrics: dict[str, Metric] = {}
    for entry in raw["metrics"]:
        fields = dict(entry)
        fields["kind"] = Kind(fields["kind"])
        fields["description"] = " ".join(str(fields["description"]).split())
        metric = Metric(**fields)
        metric.validate()
        if metric.name in metrics:
            raise MetricError(f"duplicate metric {metric.name}")
        metrics[metric.name] = metric
    return metrics


def _literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def sql(
    metric: Metric,
    *,
    group_by: Sequence[str] = (),
    where: Mapping[str, str] | None = None,
    schema: str = "marts",
) -> str:
    """SQL returning one row per group with the metric in a column named ``value``.

    ``where`` maps a dimension to one value; values are quoted, never interpolated raw.
    """
    kind = metric.kind.value
    columns: list[str] = []
    for dim in group_by:
        if dim not in DIMENSIONS or kind not in DIMENSIONS[dim]:
            raise MetricError(f"{metric.name} cannot be grouped by {dim!r}")
        columns.append(f"{DIMENSIONS[dim][kind]} as {dim}")
    filters: list[str] = []
    for dim, value in (where or {}).items():
        if dim not in DIMENSIONS or kind not in DIMENSIONS[dim]:
            raise MetricError(f"{metric.name} cannot be filtered by {dim!r}")
        filters.append(f"{DIMENSIONS[dim][kind]} = {_literal(value)}")

    if metric.kind is Kind.RATIO:
        relation = f"{schema}.agg_support_daily"
        value = f"sum({metric.numerator})"
        if metric.denominator:
            value = f"cast({value} as double) / nullif(sum({metric.denominator}), 0)"
    elif metric.kind is Kind.QUANTILE:
        relation = f"{schema}.fct_cases"
        value = f"quantile_cont({metric.column}, {metric.q})"
    else:
        daily = [*columns, "backlog_date", f"sum({metric.column}) as level"]
        inner_where = f" where {' and '.join(filters)}" if filters else ""
        inner_group = ", ".join([*group_by, "backlog_date"])
        relation = (
            f"(select {', '.join(daily)} from {schema}.fct_backlog_daily{inner_where} "
            f"group by {inner_group}) as daily"
        )
        columns = list(group_by)
        filters = []
        value = "avg(level)"

    select = ", ".join([*columns, f"{value} as value"])
    query = f"select {select} from {relation}"
    if filters:
        query += " where " + " and ".join(filters)
    if group_by:
        keys = ", ".join(group_by)
        query += f" group by {keys} order by {keys}"
    return query


def dictionary(metrics: Mapping[str, Metric]) -> str:
    """The metric dictionary as Markdown, written to docs/metric_dictionary.md."""
    lines = [
        "# Metric dictionary",
        "",
        "Every support metric, its owner and exactly how it is computed. This page is",
        "written by `support-bi metrics` from `metrics/metrics.yml`; edit the YAML, not",
        "this file.",
        "",
        "| Metric | Definition | Computed as | Unit | Better | Owner |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for m in metrics.values():
        if m.kind is Kind.RATIO:
            how = f"sum({m.numerator})" + (f" / sum({m.denominator})" if m.denominator else "")
            how += " over agg_support_daily"
        elif m.kind is Kind.QUANTILE:
            how = f"{m.q:g} quantile of {m.column} in fct_cases"
        else:
            how = f"mean over days of daily sum({m.column}) in fct_backlog_daily"
        lines.append(
            f"| **{m.label}** (`{m.name}`) | {m.description} | {how} | {m.unit} "
            f"| {m.better} | {m.owner} |"
        )
    groupings = ", ".join(f"`{d}`" for d in DIMENSIONS)
    lines.append("")
    lines.append(f"Every metric can be grouped and filtered by {groupings}, except that")
    lines.append("`tier` and `channel` do not apply to the backlog.")
    lines.append("")
    return "\n".join(lines)
