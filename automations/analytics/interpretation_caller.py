#!/usr/bin/env python3
"""
The live model caller behind `run_graph(document, caller)`.

One class, three roles, one vendor. Each role gets its own model, effort level
and output ceiling, because the three jobs have genuinely different shapes:

  * **specialists** — bounded slice in, structured findings out. Sonnet 5 at
    medium effort. Four of these run per report, so this is where cost lives.
  * **verifier** — adversarial. Opus 5 at high effort, and deliberately a
    *different model from the specialists*: a verifier that shares the
    specialist's blind spots is a second opinion in name only. Same vendor,
    so the independence is partial and worth stating plainly rather than
    overselling.
  * **synthesis** — one call, highest leverage, and the one that must honour
    the readiness gate rather than reason around it. Opus 5 at high effort.

Every call is constrained by a JSON schema derived from the contract, so the
*shape* of the response is guaranteed by the API rather than hoped for. The
contract validator still runs afterwards, because a schema can guarantee that
`evidence_fact_ids` contains strings but not that those strings name facts the
node was actually shown — which is the invariant that matters.

Token usage is recorded per call and rolled up for the manifest. Thinking is
on by default on both models and is billed as output, so `max_tokens` bounds
thinking plus text together; the ceilings below carry headroom for that, and a
truncated response is reported as truncation rather than left to look like a
model failure.
"""

import json
import os

import interpretation_contracts as ic
import interpretation_graph as ig
import interpretation_prompts as prompts

API_KEY_ENV = "ANTHROPIC_API_KEY"
MODEL_ENV = "INTERPRETATION_MODEL"
SPECIALIST_EFFORT_ENV = "INTERPRETATION_EFFORT_SPECIALIST"

ROLE_SPECIALIST = "specialist"
ROLE_VERIFIER = "verifier"
ROLE_SYNTHESIS = "synthesis"

#: Per-role model, effort and output ceiling.
#:
#: max_tokens bounds thinking + response text together on both models, so
#: these are sized for the response plus adaptive thinking headroom, not for
#: the response alone. They are ceilings, not targets: a specialist answering
#: a thin week uses a small fraction of its allowance.
ROLE_CONFIG = {
    ROLE_SPECIALIST: {"model": "claude-sonnet-5", "effort": "medium",
                      "max_tokens": 8000},
    ROLE_VERIFIER: {"model": "claude-opus-5", "effort": "high",
                    "max_tokens": 4000},
    ROLE_SYNTHESIS: {"model": "claude-opus-5", "effort": "high",
                     "max_tokens": 8000},
}

ROLE_OF_NODE = {
    **{node: ROLE_SPECIALIST for node in ig.SPECIALISTS},
    ig.NODE_VERIFIER: ROLE_VERIFIER,
    ig.NODE_SYNTHESIS: ROLE_SYNTHESIS,
}


class CallerError(RuntimeError):
    """The model could not be called, or returned something unusable."""


def role_config(env=None):
    """Per-role settings, with the two variables that may override them.

    Only the specialist row is tunable from the environment. The verifier and
    synthesis models are the independence and gate-honouring guarantees of
    this design; making them a variable would let the guarantee be switched
    off by editing a setting rather than by changing the design.
    """
    env = os.environ if env is None else env
    config = {role: dict(values) for role, values in ROLE_CONFIG.items()}

    model = (env.get(MODEL_ENV) or "").strip()
    if model:
        config[ROLE_SPECIALIST]["model"] = model

    effort = (env.get(SPECIALIST_EFFORT_ENV) or "").strip()
    if effort:
        if effort not in ("low", "medium", "high", "xhigh", "max"):
            raise CallerError(f"{SPECIALIST_EFFORT_ENV}={effort!r} is not an effort level")
        config[ROLE_SPECIALIST]["effort"] = effort
    return config


def schema_for(node, request):
    """The JSON schema this node's response is constrained to."""
    if node in ig.SPECIALISTS:
        return ic.specialist_schema(node)
    if node == ig.NODE_VERIFIER:
        return ic.verdict_schema(request["finding"]["id"])
    if node == ig.NODE_SYNTHESIS:
        return ic.SYNTHESIS_SCHEMA
    raise CallerError(f"no schema for node {node!r}")


def _text_block(response):
    """The JSON payload, from whichever block carries it.

    Thinking is on by default on both models, so the first content block is
    frequently a thinking block rather than the answer. Indexing content[0]
    would work most of the time and fail exactly when reasoning ran, which is
    the worst kind of intermittent.
    """
    for block in response.content:
        if getattr(block, "type", None) == "text":
            return block.text
    raise CallerError("response contained no text block")


class AnthropicCaller:
    """Callable with the `caller(node, request) -> dict` signature run_graph wants."""

    def __init__(self, client=None, config=None, env=None, out=None):
        self.config = config or role_config(env)
        self._client = client
        self.calls = []          # one record per attempt, including retries
        self._out = out

    # -- client ------------------------------------------------------------
    def client(self):
        if self._client is None:
            env = os.environ
            if not (env.get(API_KEY_ENV) or "").strip():
                raise CallerError(
                    f"{API_KEY_ENV} is not set. The interpretation graph needs "
                    "it; nothing else in the weekly run does.")
            try:
                import anthropic
            except ImportError as exc:  # noqa: BLE001
                raise CallerError(f"the anthropic SDK is not installed: {exc}") from None
            self._client = anthropic.Anthropic()
        return self._client

    # -- the call ----------------------------------------------------------
    def __call__(self, node, request):
        role = ROLE_OF_NODE.get(node)
        if role is None:
            raise CallerError(f"unknown node {node!r}")
        settings = self.config[role]

        response = self.client().messages.create(
            model=settings["model"],
            max_tokens=settings["max_tokens"],
            system=prompts.PROMPTS[node],
            output_config={
                "effort": settings["effort"],
                "format": {"type": "json_schema",
                           "schema": schema_for(node, request)},
            },
            messages=[{"role": "user",
                       "content": json.dumps(request, ensure_ascii=False,
                                             sort_keys=True, default=str)}],
        )

        self._record(node, role, settings, response)

        stop = getattr(response, "stop_reason", None)
        if stop == "refusal":
            raise CallerError(
                f"{node}: the model declined this request "
                f"({getattr(response, 'stop_details', None)})")
        if stop == "max_tokens":
            # Reported as truncation rather than left to surface as unparseable
            # JSON, because the fix is a bigger ceiling, not a retry.
            raise CallerError(
                f"{node}: response hit the {settings['max_tokens']}-token "
                f"ceiling for role {role} and was truncated")

        try:
            return json.loads(_text_block(response))
        except json.JSONDecodeError as exc:
            raise CallerError(f"{node}: response was not valid JSON: {exc}") from None

    # -- usage -------------------------------------------------------------
    def _record(self, node, role, settings, response):
        usage = getattr(response, "usage", None)
        self.calls.append({
            "node": node,
            "role": role,
            "model": settings["model"],
            "effort": settings["effort"],
            "max_tokens": settings["max_tokens"],
            "stop_reason": getattr(response, "stop_reason", None),
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "cache_read_input_tokens": getattr(
                usage, "cache_read_input_tokens", None),
            "cache_creation_input_tokens": getattr(
                usage, "cache_creation_input_tokens", None),
        })

    def usage_summary(self):
        """What actually got spent — measured, not the caps.

        Attempts are counted here rather than taken from the budget counter,
        so a retry shows up in the token total it actually cost. The budget's
        own numbers stay the record of how many *distinct* calls were allowed.
        """
        def total(field):
            return sum(c[field] or 0 for c in self.calls)

        by_role = {}
        for call in self.calls:
            entry = by_role.setdefault(call["role"], {
                "model": call["model"], "effort": call["effort"],
                "attempts": 0, "input_tokens": 0, "output_tokens": 0,
            })
            entry["attempts"] += 1
            entry["input_tokens"] += call["input_tokens"] or 0
            entry["output_tokens"] += call["output_tokens"] or 0

        return {
            "attempts": len(self.calls),
            "input_tokens": total("input_tokens"),
            "output_tokens": total("output_tokens"),
            "cache_read_input_tokens": total("cache_read_input_tokens"),
            "cache_creation_input_tokens": total("cache_creation_input_tokens"),
            "by_role": by_role,
            "truncated_calls": [c["node"] for c in self.calls
                                if c["stop_reason"] == "max_tokens"],
            "per_call": self.calls,
        }
