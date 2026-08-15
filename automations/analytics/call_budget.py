#!/usr/bin/env python3
"""
Clarity API call accounting, persisted.

Clarity allows 10 calls per project per day, shared with everything else that
reads the project. An in-process counter is not enough: each collector run is a
fresh process, so the count has to live in the store or the limit is
unenforceable in practice.

The automated cap sits deliberately below the hard limit. Leaving headroom
means a human can still investigate something manually on a day the collector
has already run, which is the situation the limit actually bites in.
"""

import datetime as dt

from storage import StorageError, state_key

HARD_DAILY_LIMIT = 10
DEFAULT_AUTOMATED_CAP = 3

BUDGET_NAME = "clarity_call_budget"


class BudgetExhausted(RuntimeError):
    """The day's allowance is spent. Never retried — see the module docstring."""


class ClarityCallBudget:
    def __init__(self, store, automated_cap=DEFAULT_AUTOMATED_CAP, hard_limit=HARD_DAILY_LIMIT):
        if automated_cap > hard_limit:
            raise ValueError(
                f"automated cap ({automated_cap}) cannot exceed Clarity's hard "
                f"limit of {hard_limit} calls per project per day"
            )
        self.store = store
        self.automated_cap = automated_cap
        self.hard_limit = hard_limit

    @staticmethod
    def _utc_date(now=None):
        now = now or dt.datetime.now(dt.timezone.utc)
        return now.date().isoformat()

    def _read(self, date):
        try:
            return self.store.get_json(state_key(BUDGET_NAME, date))
        except StorageError:
            return {"date": date, "calls_used": 0, "entries": []}

    def used(self, now=None):
        return self._read(self._utc_date(now))["calls_used"]

    def remaining(self, now=None):
        """Against the automated cap, not the hard limit — the headroom above
        the cap is reserved for humans."""
        return max(0, self.automated_cap - self.used(now))

    def reserve(self, count=1, reason="", now=None):
        """Record `count` calls about to be made, or refuse.

        Reserve before calling, not after: a crash between the call and the
        bookkeeping must lose the budget, not the limit.
        """
        date = self._utc_date(now)
        state = self._read(date)
        proposed = state["calls_used"] + count

        if proposed > self.automated_cap:
            raise BudgetExhausted(
                f"Clarity automated budget for {date} is spent: "
                f"{state['calls_used']}/{self.automated_cap} used, {count} more requested. "
                f"Clarity's hard limit is {self.hard_limit} per project per day and the "
                "headroom is reserved for manual investigation. This resets on Clarity's "
                "daily schedule — do not retry in a loop."
            )

        state["calls_used"] = proposed
        state["entries"].append({
            "at": (now or dt.datetime.now(dt.timezone.utc)).replace(microsecond=0).isoformat(),
            "count": count,
            "reason": reason,
        })
        self.store.put_json(state_key(BUDGET_NAME, date), state, overwrite=True)
        return proposed

    def status(self, now=None):
        date = self._utc_date(now)
        state = self._read(date)
        return {
            "date": date,
            "used": state["calls_used"],
            "automated_cap": self.automated_cap,
            "hard_limit": self.hard_limit,
            "remaining": max(0, self.automated_cap - state["calls_used"]),
        }
