"""Seeded generator for a synthetic cloud support operation.

Produces the raw tables a support platform would export: customers (with a history of
support-tier changes), agents, cases, case lifecycle events and satisfaction surveys.
The shapes follow what a real ticketing system emits, so the dbt models downstream have
to do the same work they would on production data: reconstruct each case's lifecycle
from events, attribute it to the tier the customer held at the time, and compute SLA
attainment from timestamps.

Behaviour that the metrics are expected to surface is built in deliberately and
documented here, so results can be checked against known causes:

* Case volume follows weekly and daily cycles, grows slowly over the period, and has
  a few incident days where one product's volume spikes.
* First-response time rises with queue load, so SLA attainment drops on busy days.
* Escalation is more likely for P1 and P2 and for late first responses.
* Satisfaction falls when the SLA is missed, when a case is reopened and as resolution
  time grows.

Everything is derived from one ``numpy.random.Generator``, so a seed fully determines
the output.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import numpy as np
import pyarrow as pa

from support_bi.catalog import PRIORITIES, PRODUCTS, REGIONS, TIERS, first_response_target

CHANNELS = ("web", "email", "phone", "chat")
_CHANNEL_SHARE = (0.55, 0.25, 0.08, 0.12)
# Relative case volume by weekday (Mon..Sun) and by hour of day (UTC).
_WEEKDAY = np.array([1.15, 1.1, 1.05, 1.0, 0.95, 0.45, 0.4])
_HOUR = np.array(
    [0.3, 0.25, 0.2, 0.2, 0.25, 0.35, 0.55, 0.8, 1.1, 1.35, 1.45, 1.4,
     1.3, 1.35, 1.4, 1.35, 1.2, 1.0, 0.8, 0.65, 0.55, 0.45, 0.4, 0.35]
)  # fmt: skip


@dataclass(frozen=True)
class GeneratorConfig:
    seed: int = 7
    start: dt.date = dt.date(2025, 1, 1)
    days: int = 365
    customers: int = 1200
    agents: int = 80
    cases_per_day: float = 260.0
    annual_growth: float = 0.18
    incident_days: int = 6
    tier_upgrade_rate: float = 0.08

    def __post_init__(self) -> None:
        if self.days <= 0 or self.customers <= 0 or self.agents <= 0:
            raise ValueError("days, customers and agents must be positive")
        if self.cases_per_day <= 0:
            raise ValueError("cases_per_day must be positive")


@dataclass
class RawTables:
    customers: pa.Table
    customer_tier_history: pa.Table
    agents: pa.Table
    cases: pa.Table
    case_events: pa.Table
    csat_responses: pa.Table
    _order: tuple[str, ...] = field(
        default=(
            "customers",
            "customer_tier_history",
            "agents",
            "cases",
            "case_events",
            "csat_responses",
        ),
        repr=False,
    )

    def items(self) -> list[tuple[str, pa.Table]]:
        return [(name, getattr(self, name)) for name in self._order]


def _ts(start: dt.date, minutes: np.ndarray) -> pa.Array:
    base = np.datetime64(dt.datetime.combine(start, dt.time()), "s")
    secs = np.round(minutes * 60).astype("int64")
    return pa.array(base + secs.astype("timedelta64[s]"), type=pa.timestamp("s", tz="UTC"))


def _customers(cfg: GeneratorConfig, rng: np.random.Generator) -> tuple[pa.Table, pa.Table]:
    n = cfg.customers
    ids = np.array([f"C{i:05d}" for i in range(1, n + 1)])
    tier_idx = rng.choice(len(TIERS), size=n, p=[t.share for t in TIERS])
    region = rng.choice(len(REGIONS), size=n, p=[0.42, 0.12, 0.28, 0.18])
    signup = rng.integers(-900, 0, size=n)
    customers = pa.table(
        {
            "customer_id": ids,
            "customer_name": [f"Customer {i:05d}" for i in range(1, n + 1)],
            "contact_email": [f"support-contact-{i:05d}@example.com" for i in range(1, n + 1)],
            "region": [REGIONS[r] for r in region],
            "signup_date": pa.array(
                [cfg.start + dt.timedelta(days=int(d)) for d in signup], type=pa.date32()
            ),
        }
    )
    rows: list[tuple[str, str, dt.date]] = []
    for cid, t in zip(ids, tier_idx, strict=True):
        rows.append((str(cid), TIERS[t].code, cfg.start))
        if t < len(TIERS) - 1 and rng.random() < cfg.tier_upgrade_rate:
            when = cfg.start + dt.timedelta(days=int(rng.integers(30, cfg.days)))
            rows.append((str(cid), TIERS[t + 1].code, when))
    history = pa.table(
        {
            "customer_id": [r[0] for r in rows],
            "tier": [r[1] for r in rows],
            "effective_from": pa.array([r[2] for r in rows], type=pa.date32()),
        }
    )
    return customers, history


def _agents(cfg: GeneratorConfig, rng: np.random.Generator) -> pa.Table:
    families = sorted({p.family for p in PRODUCTS})
    n = cfg.agents
    return pa.table(
        {
            "agent_id": [f"A{i:04d}" for i in range(1, n + 1)],
            "queue": [families[i % len(families)] for i in range(n)],
            "region": [REGIONS[i % len(REGIONS)] for i in range(n)],
            "hired_on": pa.array(
                [cfg.start - dt.timedelta(days=int(d)) for d in rng.integers(30, 1500, size=n)],
                type=pa.date32(),
            ),
        }
    )


def _case_times(cfg: GeneratorConfig, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Minutes since start for every case, plus the per-day load factor."""
    day = np.arange(cfg.days)
    weekday = (np.datetime64(cfg.start) + day).astype("datetime64[D]").view("int64")
    weekday = (weekday + 3) % 7  # 1970-01-01 was a Thursday
    trend = (1 + cfg.annual_growth) ** (day / 365.0)
    expected = cfg.cases_per_day * _WEEKDAY[weekday] * trend
    counts = rng.poisson(expected)
    load = counts / expected.mean()
    hour_p = _HOUR / _HOUR.sum()
    minutes: list[np.ndarray] = []
    for d, c in enumerate(counts):
        hours = rng.choice(24, size=c, p=hour_p)
        minutes.append(d * 1440 + hours * 60 + rng.uniform(0, 60, size=c))
    return np.concatenate(minutes), load


def generate(cfg: GeneratorConfig | None = None) -> RawTables:
    """Build every raw table for ``cfg``. Identical config gives identical output."""
    cfg = cfg or GeneratorConfig()
    rng = np.random.default_rng(cfg.seed)
    customers, tier_history = _customers(cfg, rng)
    agents = _agents(cfg, rng)

    created, load = _case_times(cfg, rng)
    created.sort()
    n = created.size
    day = (created // 1440).astype(int)

    prod = rng.choice(len(PRODUCTS), size=n, p=[p.share for p in PRODUCTS])
    incidents = rng.choice(cfg.days, size=cfg.incident_days, replace=False)
    for d in incidents:  # an outage day: a burst of extra cases on one product
        mask = day == d
        prod[mask & (rng.random(n) < 0.45)] = rng.integers(len(PRODUCTS))
    prio = rng.choice(len(PRIORITIES), size=n, p=[p.share for p in PRIORITIES])
    cust = rng.integers(0, cfg.customers, size=n)
    channel = rng.choice(len(CHANNELS), size=n, p=_CHANNEL_SHARE)

    tier_at_start = {
        r["customer_id"]: r["tier"]
        for r in tier_history.to_pylist()
        if r["effective_from"] == cfg.start
    }
    upgrades = {
        r["customer_id"]: (r["effective_from"], r["tier"])
        for r in tier_history.to_pylist()
        if r["effective_from"] != cfg.start
    }
    tier_codes = [t.code for t in TIERS]
    cust_ids = customers.column("customer_id").to_pylist()
    tier_idx = np.empty(n, dtype=int)
    for i in range(n):
        cid = cust_ids[cust[i]]
        code = tier_at_start[cid]
        up = upgrades.get(cid)
        if up and cfg.start + dt.timedelta(days=int(day[i])) >= up[0]:
            code = up[1]
        tier_idx[i] = tier_codes.index(code)

    target = np.array(
        [
            first_response_target(PRIORITIES[p], TIERS[t])
            for p, t in zip(prio, tier_idx, strict=True)
        ]
    )
    # First response: lognormal around a share of the target, stretched by queue load.
    frt = (
        target * rng.lognormal(mean=-0.75, sigma=0.65, size=n) * np.clip(load[day], 0.6, 2.5) ** 1.6
    )
    breached = frt > target
    escalate_p = np.array([0.22, 0.12, 0.04, 0.015])[prio] + 0.08 * breached
    escalated = rng.random(n) < escalate_p
    resolve_hours = rng.gamma(shape=1.6, scale=np.array([5.0, 14.0, 30.0, 48.0])[prio])
    resolve_hours *= np.where(escalated, 1.8, 1.0)
    resolved = created + frt + resolve_hours * 60
    reopened = rng.random(n) < 0.06 + 0.04 * escalated
    agent = rng.integers(0, cfg.agents, size=n)

    case_ids = [f"CS{i:07d}" for i in range(1, n + 1)]
    cases = pa.table(
        {
            "case_id": case_ids,
            "customer_id": [cust_ids[c] for c in cust],
            "product_code": [PRODUCTS[p].code for p in prod],
            "priority": [PRIORITIES[p].code for p in prio],
            "channel": [CHANNELS[c] for c in channel],
            "created_at": _ts(cfg.start, created),
            "subject": [f"{PRODUCTS[p].name} issue" for p in prod],
        }
    )

    ev_case: list[str] = []
    ev_type: list[str] = []
    ev_min: list[float] = []
    ev_agent: list[str | None] = []
    agent_ids = agents.column("agent_id").to_pylist()

    def add(i: int, kind: str, minute: float, who: str | None) -> None:
        ev_case.append(case_ids[i])
        ev_type.append(kind)
        ev_min.append(minute)
        ev_agent.append(who)

    for i in range(n):
        who = agent_ids[agent[i]]
        add(i, "created", created[i], None)
        add(i, "assigned", created[i] + min(frt[i] * 0.4, 30.0), who)
        add(i, "first_response", created[i] + frt[i], who)
        if escalated[i]:
            add(i, "escalated", created[i] + frt[i] + resolve_hours[i] * 20, who)
        add(i, "resolved", resolved[i], who)
        if reopened[i]:
            reopen_at = resolved[i] + rng.uniform(60, 2880)
            add(i, "reopened", reopen_at, None)
            add(i, "resolved", reopen_at + rng.gamma(1.5, 240), who)
    events = pa.table(
        {
            "event_id": [f"E{i:08d}" for i in range(1, len(ev_case) + 1)],
            "case_id": ev_case,
            "event_type": ev_type,
            "occurred_at": _ts(cfg.start, np.asarray(ev_min)),
            "agent_id": pa.array(ev_agent, type=pa.string()),
        }
    )

    responded = rng.random(n) < 0.34
    score = (
        4.6
        - 1.1 * breached
        - 0.9 * reopened
        - 0.004 * np.minimum(resolve_hours, 240)
        + rng.normal(0, 0.7, size=n)
    )
    score = np.clip(np.rint(score), 1, 5).astype(int)
    idx = np.flatnonzero(responded)
    csat = pa.table(
        {
            "case_id": [case_ids[i] for i in idx],
            "submitted_at": _ts(cfg.start, resolved[idx] + rng.uniform(30, 4320, size=idx.size)),
            "score": pa.array(score[idx], type=pa.int8()),
        }
    )
    return RawTables(customers, tier_history, agents, cases, events, csat)
