"""Tier selection and payout arithmetic."""

from dataclasses import replace

import pytest

from refunds import policy
from refunds.models import utc


def test_a_week_ahead_returns_the_whole_price_as_booked(booking, cancellation):
    request = cancellation(utc(2026, 3, 1, 14, 0))
    assert policy.tier_for(booking, request).name == "full"
    assert policy.refund_cents(booking, request) == 12000


def test_three_days_ahead_settles_at_the_standard_tier(booking, cancellation):
    request = cancellation(utc(2026, 3, 7, 14, 0))
    assert policy.refund_percent(booking, request) == 75
    assert policy.refund_cents(booking, request) == 9000


def test_the_day_before_settles_at_the_reduced_tier(booking, cancellation):
    request = cancellation(utc(2026, 3, 9, 0, 0))
    assert policy.tier_for(booking, request).name == "reduced"
    assert policy.refund_cents(booking, request) == 6000


def test_four_hours_ahead_settles_at_the_minimal_tier(booking, cancellation):
    request = cancellation(utc(2026, 3, 10, 10, 0))
    assert policy.tier_for(booking, request).name == "minimal"
    assert policy.refund_cents(booking, request) == 3000


def test_half_an_hour_ahead_pays_nothing(booking, cancellation):
    request = cancellation(utc(2026, 3, 10, 13, 30))
    assert policy.tier_for(booking, request).name == "none"
    assert policy.refund_cents(booking, request) == 0


@pytest.mark.parametrize("when", [utc(2026, 3, 10, 14, 0), utc(2026, 3, 10, 15, 0)])
def test_a_no_show_pays_zero_cents(booking, cancellation, when):
    assert policy.refund_cents(booking, cancellation(when)) == 0


def test_a_waived_reason_returns_the_whole_price_as_booked(booking, cancellation):
    request = cancellation(utc(2026, 3, 10, 13, 30), reason="room-closed")
    assert policy.tier_for(booking, request).name == "waived"
    assert policy.refund_percent(booking, request) == 100
    assert policy.refund_cents(booking, request) == 12000


def test_a_payout_under_the_processing_floor_is_not_issued(booking, cancellation):
    cheap = replace(booking, price_as_booked_cents=300)
    assert policy.refund_cents(cheap, cancellation(utc(2026, 3, 10, 10, 0))) == 0


def test_the_published_table_reads_from_the_longest_lead_down_and_rounds_down():
    rows = policy.published_table()
    assert len(rows) == 5
    assert rows[0].startswith("full")
    assert policy.tier_for_lead(10080).name == "full"
    assert policy.tier_for_lead(2880).name == "standard"
    assert policy.tier_for_lead(0).name == "none"
    assert policy.percent_of(999, 25) == 249
    assert policy.percent_of(0, 100) == 0
