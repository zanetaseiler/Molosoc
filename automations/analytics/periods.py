#!/usr/bin/env python3
"""
Comparison-period logic.

Search Console finalises data on a 2-3 day lag, and that lag sets the anchor
for the whole report. Using a different as-of date per source would mean
comparing last Tuesday's Clarity against last Friday's search data and calling
it one picture.

Periods are always whole weeks. A consumer product has strong weekday
structure, so comparing a 5-day stretch against a 9-day one produces a
weekday-mix artifact that looks exactly like a trend.
"""

import datetime as dt

# Search Console's finalisation lag. The last day all three sources can
# describe is this many days back.
GSC_LAG_DAYS = 3

DEFAULT_PERIOD_DAYS = 7
DEFAULT_BASELINE_DAYS = 28

PERIOD = "period"
PRIOR = "prior"
BASELINE = "baseline"
SEASONAL = "seasonal"


class Window:
    """An inclusive [start, end] date window."""

    __slots__ = ("name", "start", "end")

    def __init__(self, name, start, end):
        self.name = name
        self.start = start if isinstance(start, str) else start.isoformat()
        self.end = end if isinstance(end, str) else end.isoformat()

    @property
    def days(self):
        return (dt.date.fromisoformat(self.end) - dt.date.fromisoformat(self.start)).days + 1

    def dates(self):
        start = dt.date.fromisoformat(self.start)
        return [(start + dt.timedelta(days=i)).isoformat() for i in range(self.days)]

    def contains(self, date):
        return self.start <= str(date) <= self.end

    def to_dict(self):
        return {"name": self.name, "start": self.start, "end": self.end, "days": self.days}

    def __eq__(self, other):
        return (isinstance(other, Window) and self.name == other.name
                and self.start == other.start and self.end == other.end)

    def __repr__(self):
        return f"Window({self.name}, {self.start}..{self.end})"


def anchor_date(today=None, lag_days=GSC_LAG_DAYS):
    """The last day every source can describe."""
    today = today or dt.date.today()
    if isinstance(today, str):
        today = dt.date.fromisoformat(today)
    return today - dt.timedelta(days=lag_days)


def build_windows(today=None, period_days=DEFAULT_PERIOD_DAYS,
                  baseline_days=DEFAULT_BASELINE_DAYS, lag_days=GSC_LAG_DAYS):
    """Return the current period plus every comparison window.

    period   — the window under analysis, ending at the anchor
    prior    — the immediately preceding equal-length window
    baseline — the trailing window ending where `prior` ends, for a stable mean
    seasonal — the same calendar window one year earlier
    """
    if period_days % 7 != 0:
        raise ValueError(
            f"period_days must be a whole number of weeks, got {period_days}. "
            "Partial weeks produce weekday-mix artifacts that look like trends."
        )

    as_of = anchor_date(today, lag_days)
    period_start = as_of - dt.timedelta(days=period_days - 1)

    prior_end = period_start - dt.timedelta(days=1)
    prior_start = prior_end - dt.timedelta(days=period_days - 1)

    baseline_start = prior_end - dt.timedelta(days=baseline_days - 1)

    seasonal_start = period_start - dt.timedelta(days=364)  # 52 whole weeks
    seasonal_end = as_of - dt.timedelta(days=364)

    return {
        PERIOD: Window(PERIOD, period_start, as_of),
        PRIOR: Window(PRIOR, prior_start, prior_end),
        BASELINE: Window(BASELINE, baseline_start, prior_end),
        SEASONAL: Window(SEASONAL, seasonal_start, seasonal_end),
    }


def ledger_coverage(available_dates, windows):
    """What the stored Clarity ledger actually supports.

    Clarity has no historical API — its history is only what Phase 1 collected —
    so a report must state its coverage rather than quietly comparing against a
    window that is half empty.
    """
    dates = sorted(set(available_dates))
    if not dates:
        return {
            "days_available": 0, "first_date": None, "last_date": None,
            "period_days_present": 0, "prior_days_present": 0,
            "supports_period": False, "supports_comparison": False,
            "supports_seasonal": False,
        }

    period, prior = windows[PERIOD], windows[PRIOR]
    in_period = [d for d in dates if period.contains(d)]
    in_prior = [d for d in dates if prior.contains(d)]

    return {
        "days_available": len(dates),
        "first_date": dates[0],
        "last_date": dates[-1],
        "period_days_present": len(in_period),
        "prior_days_present": len(in_prior),
        # A window is usable only if it is complete: a partial window compared
        # against a full one reads as a decline that never happened.
        "supports_period": len(in_period) == period.days,
        "supports_comparison": len(in_period) == period.days and len(in_prior) == prior.days,
        "supports_seasonal": len(dates) >= 365,
    }


def describe_coverage(coverage):
    """One sentence a human can act on."""
    if not coverage["days_available"]:
        return ("No Clarity history stored yet — collection has not run. "
                "Clarity cannot be backfilled, so comparisons begin once it does.")
    if not coverage["supports_period"]:
        return (f"Clarity ledger holds {coverage['days_available']} day(s) "
                f"({coverage['first_date']} to {coverage['last_date']}); the current "
                "period is not yet fully covered, so Clarity figures are partial.")
    if not coverage["supports_comparison"]:
        return (f"Clarity ledger holds {coverage['days_available']} day(s); the current "
                "period is covered but the comparison period is not, so Clarity "
                "trends are not yet available.")
    if not coverage["supports_seasonal"]:
        return (f"Clarity ledger holds {coverage['days_available']} day(s) — enough for "
                "period-over-period, not yet for year-over-year.")
    return f"Clarity ledger holds {coverage['days_available']} day(s), including a year ago."
