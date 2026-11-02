import datetime as dt

import numpy as np
import pyarrow.compute as pc
import pytest

from support_bi.catalog import PRIORITIES, PRODUCTS, TIERS
from support_bi.generator import GeneratorConfig, generate

SMALL = GeneratorConfig(seed=11, days=60, customers=200, agents=12, cases_per_day=80)


@pytest.fixture(scope="module")
def tables():  # type: ignore[no-untyped-def]
    return generate(SMALL)


def test_same_seed_same_output() -> None:
    a, b = generate(SMALL), generate(SMALL)
    for (name, ta), (_, tb) in zip(a.items(), b.items(), strict=True):
        assert ta.equals(tb), name


def test_different_seed_changes_output() -> None:
    other = generate(GeneratorConfig(seed=12, days=60, customers=200, agents=12, cases_per_day=80))
    assert not other.cases.equals(generate(SMALL).cases)


def test_keys_are_unique(tables) -> None:  # type: ignore[no-untyped-def]
    for table, key in [
        (tables.customers, "customer_id"),
        (tables.agents, "agent_id"),
        (tables.cases, "case_id"),
        (tables.case_events, "event_id"),
    ]:
        col = table.column(key)
        assert len(pc.unique(col)) == len(col)


def test_foreign_keys_resolve(tables) -> None:  # type: ignore[no-untyped-def]
    customers = set(tables.customers.column("customer_id").to_pylist())
    cases = set(tables.cases.column("case_id").to_pylist())
    agents = set(tables.agents.column("agent_id").to_pylist())
    assert set(tables.cases.column("customer_id").to_pylist()) <= customers
    assert set(tables.case_events.column("case_id").to_pylist()) <= cases
    assert set(tables.csat_responses.column("case_id").to_pylist()) <= cases
    event_agents = {a for a in tables.case_events.column("agent_id").to_pylist() if a}
    assert event_agents <= agents


def test_codes_come_from_the_catalog(tables) -> None:  # type: ignore[no-untyped-def]
    assert set(tables.cases.column("priority").to_pylist()) <= {p.code for p in PRIORITIES}
    assert set(tables.cases.column("product_code").to_pylist()) <= {p.code for p in PRODUCTS}
    assert set(tables.customer_tier_history.column("tier").to_pylist()) <= {t.code for t in TIERS}


def test_every_case_has_a_complete_ordered_lifecycle(tables) -> None:  # type: ignore[no-untyped-def]
    rows = tables.case_events.select(["case_id", "event_type", "occurred_at"]).to_pylist()
    by_case: dict[str, list[tuple[dt.datetime, str]]] = {}
    for r in rows:
        by_case.setdefault(r["case_id"], []).append((r["occurred_at"], r["event_type"]))
    assert len(by_case) == tables.cases.num_rows
    for events in by_case.values():
        kinds = [k for _, k in events]
        assert kinds[0] == "created"
        assert {"assigned", "first_response", "resolved"} <= set(kinds)
        times = [t for t, _ in events]
        assert times == sorted(times)


def test_every_customer_starts_with_one_tier(tables) -> None:  # type: ignore[no-untyped-def]
    first = [
        r["customer_id"]
        for r in tables.customer_tier_history.to_pylist()
        if r["effective_from"] == SMALL.start
    ]
    assert sorted(first) == sorted(tables.customers.column("customer_id").to_pylist())


def test_weekends_are_quieter(tables) -> None:  # type: ignore[no-untyped-def]
    days = [t.weekday() for t in tables.cases.column("created_at").to_pylist()]
    counts = np.bincount(days, minlength=7)
    assert counts[:5].mean() > 1.5 * counts[5:].mean()


def test_scores_and_response_rate_are_plausible(tables) -> None:  # type: ignore[no-untyped-def]
    scores = tables.csat_responses.column("score").to_numpy()
    assert scores.min() >= 1 and scores.max() <= 5
    rate = tables.csat_responses.num_rows / tables.cases.num_rows
    assert 0.25 < rate < 0.45


@pytest.mark.parametrize("field", ["days", "customers", "agents", "cases_per_day"])
def test_invalid_config(field: str) -> None:
    with pytest.raises(ValueError):
        GeneratorConfig(**{field: 0})
