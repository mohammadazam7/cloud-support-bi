import math

import pytest

from support_bi.catalog import (
    PRIORITIES,
    PRODUCTS,
    REGIONS,
    TIERS,
    by_code,
    first_response_target,
)


@pytest.mark.parametrize("items", [PRIORITIES, PRODUCTS, TIERS])
def test_shares_form_a_distribution(items: tuple) -> None:  # type: ignore[type-arg]
    assert math.isclose(sum(i.share for i in items), 1.0)
    assert all(i.share > 0 for i in items)


@pytest.mark.parametrize("items", [PRIORITIES, PRODUCTS, TIERS])
def test_codes_are_unique(items: tuple) -> None:  # type: ignore[type-arg]
    codes = [i.code for i in items]
    assert len(codes) == len(set(codes))


def test_higher_priority_means_tighter_target() -> None:
    targets = [p.first_response_target_min for p in PRIORITIES]
    assert targets == sorted(targets)


def test_premium_tier_tightens_every_target() -> None:
    std, prem = by_code(TIERS, "STD"), by_code(TIERS, "PREM")
    for p in PRIORITIES:
        assert first_response_target(p, prem) < first_response_target(p, std)


def test_target_never_rounds_to_zero() -> None:
    p1, prem = by_code(PRIORITIES, "P1"), by_code(TIERS, "PREM")
    assert first_response_target(p1, prem) >= 1


def test_unknown_code_raises() -> None:
    with pytest.raises(KeyError):
        by_code(PRODUCTS, "NOPE")


def test_regions_are_distinct() -> None:
    assert len(REGIONS) == len(set(REGIONS))
