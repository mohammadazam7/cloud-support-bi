"""Reference data for the support operation: products, priorities, tiers and regions.

These are the fixed dimensions the case generator samples from and the dbt models join
to. SLA targets live here, next to the priorities they belong to, so the generator and
the metric layer cannot disagree about what "met the SLA" means.

The values describe a plausible cloud support operation. They are not taken from any
real provider's published SLAs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeVar


@dataclass(frozen=True, slots=True)
class Priority:
    """A case priority with its first-response target in business minutes."""

    code: str
    label: str
    first_response_target_min: int
    share: float


@dataclass(frozen=True, slots=True)
class Product:
    code: str
    name: str
    family: str
    share: float


@dataclass(frozen=True, slots=True)
class Tier:
    """A customer support tier. ``response_multiplier`` scales every SLA target."""

    code: str
    name: str
    response_multiplier: float
    share: float


PRIORITIES: tuple[Priority, ...] = (
    Priority("P1", "Critical: production down", 15, 0.04),
    Priority("P2", "High: production impaired", 60, 0.16),
    Priority("P3", "Medium: non-production issue", 240, 0.45),
    Priority("P4", "Low: question or guidance", 480, 0.35),
)

PRODUCTS: tuple[Product, ...] = (
    Product("GCE", "Compute Engine", "Compute", 0.22),
    Product("GKE", "Kubernetes Engine", "Compute", 0.16),
    Product("BQ", "BigQuery", "Data analytics", 0.18),
    Product("SQL", "Cloud SQL", "Databases", 0.12),
    Product("GCS", "Cloud Storage", "Storage", 0.10),
    Product("IAM", "Identity and Access Management", "Security", 0.08),
    Product("NET", "Cloud Networking", "Networking", 0.09),
    Product("BILL", "Billing", "Account", 0.05),
)

TIERS: tuple[Tier, ...] = (
    Tier("STD", "Standard", 1.0, 0.55),
    Tier("ENH", "Enhanced", 0.75, 0.33),
    Tier("PREM", "Premium", 0.5, 0.12),
)

REGIONS: tuple[str, ...] = ("NA", "LATAM", "EMEA", "APAC")


def first_response_target(priority: Priority, tier: Tier) -> int:
    """Business minutes allowed before the first response, rounded to whole minutes."""
    return max(1, round(priority.first_response_target_min * tier.response_multiplier))


_Coded = TypeVar("_Coded", Priority, Product, Tier)


def by_code(items: tuple[_Coded, ...], code: str) -> _Coded:
    """The item whose ``code`` matches; raises ``KeyError`` if there is none."""
    for item in items:
        if item.code == code:
            return item
    raise KeyError(code)
