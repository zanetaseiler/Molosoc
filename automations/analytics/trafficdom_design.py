"""
The TrafficDom reporting design system — VENDORED, DO NOT EDIT.

Generated from the Growth Engine at fingerprint 631893774867b19e.
Regenerate with:

    python3 -m growth_engine design --export <this file>

One visual identity for every TrafficDom report. Editing this copy makes the two
reports diverge silently, which is the one failure this file exists to prevent —
a test in this repository hashes it against the fingerprint above and fails if it
has been touched.

To change the design, change it in the Growth Engine and re-export. To change
what THIS report says, edit the report — the components take labels and data,
and none of the wording is in here.
"""

DESIGN_FINGERPRINT = "631893774867b19e"

"""
Brand configuration — deliberately separate from the design system.

The design system in ``design.py`` owns the *language*: the scale, the rhythm,
the component vocabulary, the way a status is expressed. This module owns the
handful of values a brand is allowed to change: its name, its wordmark, its one
accent colour, and the line at the foot of the page.

The split is the point. A client cannot restyle a TrafficDom report — there is
no hook for it to do so, because the components take a ``Theme`` and a ``Theme``
has exactly these fields. The first client to receive one of these reports is
not the owner of how they look, and nothing in this package carries any client's
name, colours or typography — a test enforces that.

``TRAFFICDOM`` is the default and the only theme defined here. A future
white-label engagement would add one more instance, not a second stylesheet.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """The brand values a report may vary. Everything else is fixed.

    ``accent`` is used sparingly and on purpose: one accent, applied to the
    wordmark rule, the active status and the score indicator. A palette that
    accents everything accents nothing, and a client report that looks busy
    reads as less considered than one that does not.
    """

    name: str = "TrafficDom"
    #: The small line above the title. Says which system produced the document.
    wordmark: str = "TrafficDom Growth Engine"
    #: One accent, and the tint of it used for fills.
    accent: str = "#0f6f63"
    accent_soft: str = "#e8f2f0"
    accent_ink: str = "#0a4f46"
    #: The brand mark, as a ``data:`` URI. ``None`` renders the typographic
    #: wordmark instead — which is a complete design, not a placeholder, so a
    #: report is never broken by a missing asset.
    #:
    #: A URI rather than a path or a URL: a report must stay self-contained, and
    #: a logo fetched from a host at open time would tell that host who read the
    #: report and when. Produce one with ``python3 -m growth_engine.reporting
    #: .brandkit <file>``.
    logo: str = None
    logo_alt: str = "TrafficDom"
    #: The standing statement at the foot of every report.
    footer: str = (
        "Produced by the TrafficDom Growth Engine from verified, published "
        "evidence. This engine reads evidence; it does not collect data and "
        "does not change anything in the account."
    )

    def tokens(self):
        """The brand half of the CSS custom properties."""
        return {
            "--td-accent": self.accent,
            "--td-accent-soft": self.accent_soft,
            "--td-accent-ink": self.accent_ink,
        }


#: The brand, as exported. One mark for every TrafficDom report.
TRAFFICDOM = Theme()


"""
The TrafficDom reporting design system.

The visual language for every report this engine produces — Growth today, and
Analytics, Paid Ads, Email, Social, CRO, Retention, Commerce and Market as they
arrive. It is a system rather than a stylesheet: a set of tokens, and a fixed
vocabulary of components that consume them. A new report composes components; it
does not write markup or CSS of its own, and there is a test that says so.

**What the language is.** A strategy consultancy's weekly briefing, not a
developer's dashboard. Soft off-white ground, charcoal ink, one restrained
accent, hairline rules. A serif display face carries the headline and the
conclusion; a sans stack carries every interface element and every number.
Whitespace does the separating. Nothing is rounded like an app, nothing
gradients, and no surface is black.

**Scannable in ten seconds.** That is a layout requirement, and it is why the
conclusion is one card at the top with four sentences in it, why the metrics are
a single hairline band, and why priorities are numbered rows rather than a stack
of paragraphs. Anything a reader would have to *study* belongs in the technical
drawer at the bottom — present, complete, and out of the reading path.

**Why tokens.** Every colour, size and rhythm value is a custom property. A
component references a token; nothing references a literal. That is what makes
"the same design language" a checkable claim across nine future reports rather
than an intention.

**Components.** The full vocabulary, in the order a report uses them:

    page                    the document shell
    report_header           masthead: wordmark, title, period, key facts
    conclusion_card         the week in four sentences
    metric_band / metric    the headline figures, one hairline row
    section                 eyebrow, title, optional lede
    channel_card / grid     per-channel health: state, one observation, figures
    priority_row            a ranked opportunity — the scannable unit
    idea_card               an exploratory idea, visibly not a finding
    action_group            focus now / continue / wait
    insight_card            one short learning
    status_chip             what may be done with an item
    confidence_meter        evidence strength, as three segments
    score_meter             a deterministic score on a fixed track
    technical_drawer        everything technical, behind one disclosure
    empty_state             an honest nothing-here

Nothing here knows what a readiness state is. Components take labels and tones
the view model has already decided, which is what keeps presentation rules in
one place and out of the markup.
"""

import html as _html


#: The five tones a component may carry. A tone is a *meaning*, not a colour:
#: ``ready`` is the only one that takes the accent, and ``waiting`` is a warm
#: neutral rather than red, because "not yet known" is not a failure.
TONES = ("ready", "waiting", "idea", "blocked", "off")

#: Structural tokens. The brand contributes three more (see ``theme.Theme``).
TOKENS = {
    # ---- ground and ink -------------------------------------------------
    "--td-page": "#f7f6f3",
    "--td-surface": "#fffefc",
    "--td-surface-sunk": "#f2f1ed",
    "--td-ink": "#1b1c1a",
    "--td-ink-soft": "#55574f",
    "--td-ink-faint": "#8d8f86",
    "--td-rule": "#e3e2dc",
    "--td-rule-soft": "#eeede8",
    # ---- status, all desaturated ---------------------------------------
    "--td-wait": "#8a6a35",
    "--td-wait-soft": "#f6f1e6",
    "--td-idea": "#4f5361",
    "--td-idea-soft": "#eeeff2",
    "--td-stop": "#94453b",
    "--td-stop-soft": "#f7ece9",
    "--td-off": "#9a9c93",
    "--td-off-soft": "#f0efea",
    # ---- type ------------------------------------------------------------
    "--td-display": ('ui-serif, Georgia, "Iowan Old Style", "Palatino Linotype", '
                     '"Times New Roman", serif'),
    "--td-sans": ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
                  '"Helvetica Neue", Arial, sans-serif'),
    "--td-mono": ('ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, '
                  "monospace"),
    # ---- rhythm ----------------------------------------------------------
    "--td-measure": "68rem",
    "--td-section": "4rem",
    "--td-radius": "4px",
    "--td-shadow": "0 1px 2px rgba(27, 28, 26, .04)",
}


def escape(value):
    return _html.escape("" if value is None else str(value), quote=True)


def tone_class(name):
    return name if name in TONES else "waiting"


def _token_block(theme):
    values = dict(TOKENS)
    values.update(theme.tokens())
    body = "\n".join(f"  {name}: {value};" for name, value in sorted(values.items()))
    return ":root {\n" + body + "\n}"


STYLESHEET = """
*, *::before, *::after { box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

body {
  margin: 0;
  background: var(--td-page);
  color: var(--td-ink);
  font-family: var(--td-sans);
  font-size: 16px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.td-wrap { max-width: var(--td-measure); margin: 0 auto; padding: 0 2.5rem; }

/* ---------------------------------------------------------------- type -- */

.td-eyebrow {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--td-ink-faint);
  margin: 0;
}

.td-title {
  font-family: var(--td-display);
  font-weight: 400;
  font-size: clamp(2rem, 4.2vw, 2.875rem);
  line-height: 1.1;
  letter-spacing: -0.02em;
  margin: 1rem 0 0;
}

.td-section-title {
  font-family: var(--td-display);
  font-weight: 400;
  font-size: 1.5rem;
  line-height: 1.25;
  letter-spacing: -0.015em;
  margin: 0.625rem 0 0;
}

.td-lede { color: var(--td-ink-soft); margin: 0.5rem 0 0; max-width: 60ch; }

/* -------------------------------------------------------------- header -- */

.td-header { padding: 3.5rem 0 2.25rem; }

.td-wordmark {
  display: flex; align-items: center; gap: 0.75rem;
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.2em;
  text-transform: uppercase; color: var(--td-ink-soft); margin: 0;
}

.td-wordmark::before {
  content: ""; width: 1.75rem; height: 2px;
  background: var(--td-accent); flex: none;
}

.td-facts {
  display: flex; flex-wrap: wrap; gap: 0.5rem 2rem;
  margin: 1.5rem 0 0; padding: 0; list-style: none;
  font-size: 0.8125rem; color: var(--td-ink-faint);
}

.td-facts b { color: var(--td-ink-soft); font-weight: 600; }

/* The brand mark, when one is installed. Height-constrained rather than
   width-constrained: a wordmark and a square mark should sit on the same
   baseline whatever their aspect ratio. */
.td-wordmark--mark { gap: 0.875rem; }
.td-wordmark--mark::before { display: none; }

.td-wordmark img {
  height: 1.75rem; width: auto; max-width: 12rem; display: block;
}

.td-wordmark--mark span {
  padding-left: 0.875rem; border-left: 1px solid var(--td-rule);
}

/* ---------------------------------------------------------- conclusion -- */

.td-conclusion {
  background: var(--td-surface);
  border: 1px solid var(--td-rule);
  border-radius: var(--td-radius);
  box-shadow: var(--td-shadow);
  padding: 2.5rem 2.75rem 2.25rem;
}

.td-conclusion-top {
  display: flex; flex-wrap: wrap; align-items: center;
  justify-content: space-between; gap: 1rem;
  padding: 0 0 1.5rem; border-bottom: 1px solid var(--td-rule-soft);
}

.td-conclusion-statement {
  font-family: var(--td-display);
  font-size: clamp(1.375rem, 2.6vw, 1.75rem);
  line-height: 1.4; letter-spacing: -0.01em;
  margin: 1.75rem 0 0; max-width: 46ch; color: var(--td-ink);
}

.td-directives {
  display: grid; gap: 1.75rem 3rem; margin: 2rem 0 0;
  grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
}

.td-directive dt {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--td-ink-faint); margin: 0 0 0.5rem;
  padding: 0 0 0.5rem; border-bottom: 1px solid var(--td-rule-soft);
}

.td-directive dd { margin: 0; color: var(--td-ink-soft); max-width: 42ch; }

.td-directive--focus dt { color: var(--td-accent-ink); }

/* ------------------------------------------------------------- metrics -- */

.td-metrics {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr));
  gap: 1px; margin: 1.25rem 0 0;
  background: var(--td-rule); border: 1px solid var(--td-rule);
  border-radius: var(--td-radius); overflow: hidden;
}

.td-metric { background: var(--td-surface); padding: 1.5rem 1.5rem 1.25rem; }

.td-metric-value {
  font-family: var(--td-display); font-size: 2.5rem; line-height: 1;
  font-variant-numeric: tabular-nums; margin: 0; letter-spacing: -0.02em;
}

.td-metric--muted .td-metric-value { color: var(--td-ink-faint); }

.td-metric-label {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--td-ink-faint); margin: 0.875rem 0 0;
}

.td-metric-note {
  font-size: 0.8125rem; color: var(--td-ink-soft); margin: 0.375rem 0 0;
}

/* Direction, not judgement: down is not red, because whether down is bad
   depends on the metric and this component does not know which one it holds. */
.td-metric-change {
  font-size: 0.8125rem; font-weight: 600; margin: 0.5rem 0 0;
  color: var(--td-ink-soft);
}

.td-metric-change--up { color: var(--td-accent-ink); }
.td-metric-change--down { color: var(--td-wait); }
.td-metric-change--unknown { color: var(--td-ink-faint); font-weight: 400; }

.td-metric .td-sparkline { display: block; margin: 0.75rem 0 0; color: var(--td-rule); }
.td-metric--trend .td-sparkline { color: var(--td-accent); }

/* --------------------------------------------------------------- tables -- */

.td-table-wrap {
  overflow-x: auto; border: 1px solid var(--td-rule);
  border-radius: var(--td-radius); background: var(--td-surface);
}

.td-table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }

.td-table caption {
  text-align: left; padding: 1.125rem 1.25rem 0;
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--td-ink-faint);
}

.td-table th, .td-table td {
  text-align: left; padding: 0.75rem 1.25rem;
  border-bottom: 1px solid var(--td-rule-soft);
}

.td-table thead th {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.12em;
  text-transform: uppercase; color: var(--td-ink-faint);
  border-bottom-color: var(--td-rule);
}

.td-table tbody tr:last-child td { border-bottom: 0; }
.td-table td { color: var(--td-ink-soft); }
.td-table .td-numeric {
  text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap;
}
.td-table tbody .td-numeric { color: var(--td-ink); }

/* ------------------------------------------------------------ sparkline -- */

.td-sparkline { display: inline-block; line-height: 0; color: var(--td-ink-faint); }
.td-sparkline svg { width: 100%; height: auto; max-width: 100%; }

/* ---------------------------------------------------------------- note -- */

.td-note {
  background: var(--td-surface-sunk); border-radius: var(--td-radius);
  padding: 1.25rem 1.5rem; border-left: 2px solid var(--td-rule);
}

.td-note p {
  margin: 0.5rem 0 0; color: var(--td-ink-soft); font-size: 0.875rem;
  max-width: 78ch;
}

.td-note .td-eyebrow { margin: 0; }

/* ------------------------------------------------------------ sections -- */

.td-section { padding: var(--td-section) 0 0; }
.td-section-head { margin: 0 0 1.5rem; }

/* ------------------------------------------------------------ channels -- */

/* Individually bordered rather than a hairline mesh: the channel count is
   whatever a client has declared, and a mesh leaves a ragged empty cell on the
   last row the day that count is not a multiple of the column count. */
.td-channels {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(15rem, 1fr));
  gap: 1rem;
}

.td-channel {
  background: var(--td-surface); padding: 1.375rem 1.375rem 1.25rem;
  border: 1px solid var(--td-rule); border-radius: var(--td-radius);
  display: flex; flex-direction: column; gap: 0.75rem;
}

.td-channel--off {
  background: transparent; border-style: dashed; box-shadow: none;
}

.td-channel-top {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 0.75rem;
}

.td-channel-name {
  font-size: 0.9375rem; font-weight: 600; margin: 0; line-height: 1.3;
}

.td-channel-top { min-height: 2.4em; }

.td-channel-note {
  font-size: 0.8125rem; line-height: 1.5; color: var(--td-ink-soft);
  margin: 0; max-width: 34ch;
}

.td-channel--off .td-channel-note { color: var(--td-ink-faint); }

.td-channel-figures {
  display: flex; flex-wrap: wrap; gap: 0.25rem 1.5rem; margin: auto 0 0;
  padding: 0.875rem 0 0; border-top: 1px solid var(--td-rule-soft);
}

.td-figure { font-size: 0.8125rem; color: var(--td-ink-faint); }
.td-figure b {
  display: block; font-family: var(--td-display); font-size: 1.25rem;
  color: var(--td-ink); font-weight: 400; font-variant-numeric: tabular-nums;
}

/* ---------------------------------------------------------- priorities -- */

.td-priorities { border-top: 1px solid var(--td-rule); }

.td-priority {
  display: grid; gap: 0.375rem 1.75rem; align-items: start;
  grid-template-columns: 3.5rem 1fr auto;
  padding: 1.75rem 0; border-bottom: 1px solid var(--td-rule);
}

.td-priority-rank {
  font-family: var(--td-display); font-size: 1.75rem; line-height: 1;
  color: var(--td-rule); font-variant-numeric: tabular-nums;
  grid-row: 1 / span 3;
}

.td-priority--opportunity .td-priority-rank { color: var(--td-accent); }

.td-priority-channel {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--td-ink-faint);
}

.td-priority-title {
  font-family: var(--td-display); font-weight: 400; font-size: 1.25rem;
  line-height: 1.3; margin: 0; letter-spacing: -0.01em;
}

.td-priority-why { color: var(--td-ink-soft); margin: 0; max-width: 58ch; }

.td-priority-state { grid-column: 3; grid-row: 1 / span 2; text-align: right; }

.td-priority-meta {
  grid-column: 3; grid-row: 3; text-align: right;
  display: flex; flex-direction: column; align-items: flex-end; gap: 0.375rem;
}

/* --------------------------------------------------------------- ideas -- */

.td-ideas {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(19rem, 1fr));
  gap: 1.25rem;
}

.td-card--idea {
  border: 1px dashed var(--td-rule); border-radius: var(--td-radius);
  padding: 1.5rem 1.625rem; background: transparent;
}

.td-card--idea h3 {
  font-family: var(--td-display); font-weight: 400; font-size: 1.125rem;
  line-height: 1.3; margin: 0.875rem 0 0;
}

.td-card--idea p {
  font-size: 0.875rem; color: var(--td-ink-soft); margin: 0.625rem 0 0;
}

/* ------------------------------------------------------------- actions -- */

.td-actions {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr));
  gap: 1px; background: var(--td-rule);
  border: 1px solid var(--td-rule); border-radius: var(--td-radius);
  overflow: hidden;
}

.td-action-group { background: var(--td-surface); padding: 1.75rem 1.625rem; }

.td-action-group h3 {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; margin: 0 0 1rem; color: var(--td-ink-faint);
}

.td-action-group--focus h3 { color: var(--td-accent-ink); }

.td-action-group ul { margin: 0; padding: 0; list-style: none; }

.td-action-group li {
  padding: 0.625rem 0 0.625rem 1rem; position: relative;
  border-top: 1px solid var(--td-rule-soft); color: var(--td-ink-soft);
  font-size: 0.9375rem;
}

.td-action-group li:first-child { border-top: 0; padding-top: 0; }

.td-action-group li::before {
  content: ""; position: absolute; left: 0; top: 1.0625rem;
  width: 4px; height: 4px; border-radius: 50%; background: var(--td-rule);
}

.td-action-group li:first-child::before { top: 0.5rem; }
.td-action-group--focus li::before { background: var(--td-accent); }

.td-action-empty { color: var(--td-ink-faint); font-size: 0.9375rem; margin: 0; }

/* ------------------------------------------------------------ insights -- */

.td-insights {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(17rem, 1fr));
  gap: 1.25rem;
}

.td-insight {
  background: var(--td-surface); border: 1px solid var(--td-rule);
  border-radius: var(--td-radius); padding: 1.5rem 1.625rem;
  box-shadow: var(--td-shadow);
}

.td-insight p { margin: 0.75rem 0 0; color: var(--td-ink-soft); font-size: 0.9375rem; }
.td-insight p:first-of-type { color: var(--td-ink); font-size: 1rem; }

/* --------------------------------------------------------------- chips -- */

.td-chip {
  display: inline-flex; align-items: center; gap: 0.4375rem;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.02em;
  white-space: nowrap; color: var(--td-ink-soft);
}

.td-chip::before {
  content: ""; width: 0.375rem; height: 0.375rem; border-radius: 50%;
  background: currentColor; flex: none;
}

.td-chip--ready   { color: var(--td-accent-ink); }
.td-chip--waiting { color: var(--td-wait); }
.td-chip--idea    { color: var(--td-idea); }
.td-chip--blocked { color: var(--td-stop); }
.td-chip--off     { color: var(--td-off); }

.td-chip--solid {
  padding: 0.3125rem 0.75rem; border-radius: 999px;
  background: var(--td-off-soft);
}
.td-chip--solid.td-chip--ready   { background: var(--td-accent-soft); }
.td-chip--solid.td-chip--waiting { background: var(--td-wait-soft); }
.td-chip--solid.td-chip--idea    { background: var(--td-idea-soft); }
.td-chip--solid.td-chip--blocked { background: var(--td-stop-soft); }

/* ------------------------------------------------------------- meters -- */

.td-meter {
  display: inline-flex; align-items: center; gap: 0.5rem;
  font-size: 0.75rem; color: var(--td-ink-faint);
}

.td-meter-track { display: inline-flex; gap: 2px; }

.td-meter-track i {
  width: 0.875rem; height: 2px; border-radius: 1px;
  background: var(--td-rule); display: block;
}

.td-meter-track i.on { background: var(--td-ink-faint); }

.td-score { display: inline-flex; align-items: center; gap: 0.5rem;
            font-size: 0.75rem; color: var(--td-ink-faint); }

.td-score-track {
  position: relative; width: 4.5rem; height: 2px; border-radius: 1px;
  background: var(--td-rule); overflow: hidden;
}

.td-score-fill {
  position: absolute; inset: 0 auto 0 0; background: var(--td-ink-faint);
}

.td-priority--opportunity .td-score-fill { background: var(--td-accent); }

.td-score-value { font-variant-numeric: tabular-nums; color: var(--td-ink-soft); }

/* --------------------------------------------------------------- empty -- */

.td-empty {
  border: 1px dashed var(--td-rule); border-radius: var(--td-radius);
  padding: 2rem; color: var(--td-ink-soft); max-width: 60ch;
}

/* -------------------------------------------------------------- onward -- */

/* The only link the system draws, and it is drawn as a destination rather
   than as a button. A report is a document; a button in one implies something
   will happen, and the only thing that happens here is that a different
   document opens. */
.td-onward {
  display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.75rem 1.25rem;
  margin: 1.5rem 0 0;
}
.td-onward a {
  color: var(--td-accent-ink); font-weight: 600; text-decoration: none;
  border-bottom: 1px solid var(--td-accent); padding-bottom: 0.15rem;
}
.td-onward a:hover, .td-onward a:focus { border-bottom-width: 2px; }
.td-onward p {
  margin: 0; color: var(--td-ink-soft); font-size: 0.875rem; max-width: 60ch;
}

/* ---------------------------------------------------------- disclosure -- */

.td-technical {
  margin: var(--td-section) 0 0; border-top: 1px solid var(--td-rule);
  padding: 1.25rem 0 0;
}

.td-technical summary {
  cursor: pointer; font-size: 0.6875rem; font-weight: 600;
  letter-spacing: 0.14em; text-transform: uppercase; color: var(--td-ink-faint);
}

.td-technical summary::marker { color: var(--td-rule); }

.td-technical h3 {
  font-size: 0.6875rem; font-weight: 600; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--td-ink-faint);
  margin: 2rem 0 0.75rem;
}

.td-technical ul { margin: 0; padding-left: 1.125rem; }

.td-technical li, .td-technical td, .td-technical th {
  font-size: 0.8125rem; color: var(--td-ink-soft); line-height: 1.55;
}

.td-technical table { width: 100%; border-collapse: collapse; margin: 0.5rem 0 0; }

.td-technical th, .td-technical td {
  text-align: left; vertical-align: top; font-weight: 400;
  padding: 0.4375rem 1rem 0.4375rem 0; border-bottom: 1px solid var(--td-rule-soft);
}

.td-technical th { width: 34%; color: var(--td-ink); font-weight: 600; }
.td-technical code { font-family: var(--td-mono); font-size: 0.75rem; word-break: break-all; }

/* -------------------------------------------------------------- footer -- */

.td-footer {
  margin: var(--td-section) 0 0; padding: 1.5rem 0 4rem;
  border-top: 1px solid var(--td-rule); font-size: 0.8125rem;
  color: var(--td-ink-faint);
}

.td-footer p { margin: 0; max-width: 64ch; }

.td-signature { margin: 0 0 1rem !important; }
.td-signature img { height: 1.5rem; width: auto; max-width: 10rem; opacity: 0.7; }

/* -------------------------------------------------------- small screen -- */

@media (max-width: 48rem) {
  .td-wrap { padding: 0 1.25rem; }
  .td-header { padding: 2.5rem 0 1.5rem; }
  .td-section { padding: 2.75rem 0 0; }
  .td-conclusion { padding: 1.75rem 1.5rem; }
  .td-metrics { grid-template-columns: repeat(2, 1fr); }
  .td-metric { padding: 1.25rem; }
  .td-metric-value { font-size: 2rem; }
  .td-channels, .td-actions { grid-template-columns: 1fr; }
  .td-table th, .td-table td { padding: 0.625rem 0.875rem; }
  .td-priority { grid-template-columns: 2.25rem 1fr; }
  .td-priority-state, .td-priority-meta {
    grid-column: 2; grid-row: auto; text-align: left; align-items: flex-start;
  }
}

@media print {
  body { background: #fff; }
  .td-technical { display: none; }
  .td-conclusion, .td-insight, .td-channel { box-shadow: none; }
  .td-priority, .td-channel, .td-insight { break-inside: avoid; }
}
"""


# --------------------------------------------------------------------------
# Shell
# --------------------------------------------------------------------------

def page(title, body, theme=TRAFFICDOM, lang="en"):
    """The document shell. Self-contained: no external stylesheet, font or script.

    A client report that depends on a CDN renders differently depending on where
    and when it is opened, and quietly tells a third party who opened it.
    """
    return "\n".join([
        "<!DOCTYPE html>",
        f'<html lang="{escape(lang)}">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="robots" content="noindex, nofollow">',
        f"<title>{escape(title)}</title>",
        f"<style>{_token_block(theme)}\n{STYLESHEET}</style>",
        "</head>",
        "<body>",
        body,
        "</body>",
        "</html>",
        "",
    ])


def wrap(parts):
    """The measured column every section sits in."""
    return f'<div class="td-wrap">{"".join(part for part in parts if part)}</div>'


# --------------------------------------------------------------------------
# Chips and meters — the small shared vocabulary
# --------------------------------------------------------------------------

def status_chip(label, tone="waiting", solid=False):
    """What may be done with an item, as one unambiguous mark.

    One component for every "may I act on this?" answer in every report, so the
    answer looks the same everywhere and cannot be softened by styling.
    """
    classes = f"td-chip td-chip--{tone_class(tone)}"
    if solid:
        classes += " td-chip--solid"
    return f'<span class="{classes}">{escape(label)}</span>'


def confidence_meter(label, level=0):
    """Evidence strength, as three segments plus its name.

    Segments rather than a percentage: the judgement is ordinal, and rendering
    it as a number would invite arithmetic it cannot support.
    """
    segments = "".join(
        f'<i class="{"on" if index < level else ""}"></i>' for index in range(3))
    return ('<span class="td-meter">'
            f'<span class="td-meter-track">{segments}</span>'
            f"<span>{escape(label)}</span></span>")


def score_meter(score, label="Score", maximum=1.0):
    """A deterministic score on a fixed track — the same scale on every row.

    Deliberately small and grey: the number is secondary to the ranking it
    produced, and a chart that shouted would invert that.
    """
    if score is None:
        return ""
    try:
        fraction = max(0.0, min(1.0, float(score) / float(maximum)))
    except (TypeError, ValueError, ZeroDivisionError):
        return ""
    return ('<span class="td-score">'
            f"<span>{escape(label)}</span>"
            '<span class="td-score-track">'
            f'<span class="td-score-fill" style="width: {fraction * 100:.1f}%"></span>'
            "</span>"
            f'<span class="td-score-value">{escape(score)}</span></span>')


# --------------------------------------------------------------------------
# Header and conclusion
# --------------------------------------------------------------------------

def brand_mark(theme=TRAFFICDOM, wordmark=None):
    """The logo when one is installed, the typographic wordmark otherwise.

    Both are finished designs. The fallback is not a placeholder waiting for an
    asset: a report whose brand mark is a letterspaced line of type is a report
    that still looks deliberate, and one that cannot break because a file is
    missing.
    """
    label = wordmark or theme.wordmark
    if theme.logo:
        return ('<p class="td-wordmark td-wordmark--mark">'
                f'<img src="{escape(theme.logo)}" alt="{escape(theme.logo_alt)}">'
                f"<span>{escape(label)}</span></p>")
    return f'<p class="td-wordmark">{escape(label)}</p>'


def report_header(title, eyebrow=None, facts=(), theme=TRAFFICDOM,
                  wordmark=None):
    """Masthead: brand mark, report title, and the facts that date it.

    ``wordmark`` names which report this is — "Growth Engine", "Weekly
    Analytics" — under the same mark. That is the whole trick to making two
    reports feel like one suite: identical furniture, one line of difference.
    """
    rows = "".join(
        f"<li>{escape(label)} <b>{escape(value)}</b></li>"
        for label, value in facts if value
    )
    return (
        '<header class="td-header">'
        f"{brand_mark(theme, wordmark)}"
        f'<h1 class="td-title">{escape(title)}</h1>'
        + (f'<p class="td-lede">{escape(eyebrow)}</p>' if eyebrow else "")
        + (f'<ul class="td-facts">{rows}</ul>' if rows else "")
        + "</header>"
    )


def conclusion_card(status_label, tone, period, statement, directives=()):
    """The week in four sentences: state, conclusion, and what to do about it.

    The size of this component is the argument. A reader who stops here should
    have the correct impression of the week, so there is room for one statement
    and a short list of directives — and no room for anything else.
    """
    entries = "".join(
        f'<div class="td-directive{" td-directive--focus" if emphasis else ""}">'
        f"<dt>{escape(term)}</dt><dd>{escape(value)}</dd></div>"
        for term, value, emphasis in directives if value
    )
    return (
        '<div class="td-conclusion">'
        '<div class="td-conclusion-top">'
        f"{status_chip(status_label, tone, solid=True)}"
        + (f'<p class="td-eyebrow">{escape(period)}</p>' if period else "")
        + "</div>"
        f'<p class="td-conclusion-statement">{escape(statement)}</p>'
        + (f'<dl class="td-directives">{entries}</dl>' if entries else "")
        + "</div>"
    )


def sparkline(points, width=200, height=40, label=None):
    """A trend, drawn small. The only chart in the system, and it earns it.

    A series of numbers is nearly unreadable as text and immediate as a line, so
    this exists — but it carries no axis, no gridlines and no tooltip, because a
    sparkline that grows those has become a chart and belongs in a tool rather
    than a briefing.
    """
    values = [value for value in (points or ()) if isinstance(value, (int, float))]
    if len(values) < 2:
        return ""
    low, high = min(values), max(values)
    span = (high - low) or 1.0
    step = width / (len(values) - 1)
    coordinates = " ".join(
        f"{index * step:.1f},{height - ((value - low) / span) * (height - 4) - 2:.1f}"
        for index, value in enumerate(values)
    )
    return (
        '<span class="td-sparkline">'
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'role="img" aria-label="{escape(label or "trend")}" '
        'preserveAspectRatio="none" focusable="false">'
        f'<polyline points="{coordinates}" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>'
        "</svg></span>"
    )


#: How a figure moved. ``flat`` is a real answer, not a missing one, and
#: ``unknown`` is the honest state when there is nothing to compare against —
#: which must never render as a zero.
DIRECTIONS = {
    "up": "\u2191", "down": "\u2193", "flat": "\u2192", "unknown": "",
}


def metric(value, label, note=None, muted=False, change=None, direction=None,
           trend=None, trend_label=None):
    """One headline figure, optionally with how it moved.

    The change is the reason the Analytics report exists, so it sits directly
    under the number rather than in a caption. The arrow is a direction, never a
    judgement: down is not styled as bad, because whether down is bad depends on
    the metric and this component does not know which one it is holding.
    """
    classes = "td-metric td-metric--muted" if muted else "td-metric"
    arrow = DIRECTIONS.get(direction or "unknown", "")
    movement = ""
    if change:
        movement = (f'<p class="td-metric-change td-metric-change--'
                    f'{escape(direction or "unknown")}">'
                    + (f'<span aria-hidden="true">{arrow}</span> ' if arrow else "")
                    + f"{escape(change)}</p>")
    line = sparkline(trend, width=180, height=32, label=trend_label) if trend else ""
    if line:
        classes += " td-metric--trend"
    return (
        f'<div class="{classes}">'
        f'<p class="td-metric-value">{escape(value)}</p>'
        f"{movement}"
        f'<p class="td-metric-label">{escape(label)}</p>'
        + (f'<p class="td-metric-note">{escape(note)}</p>' if note else "")
        + line
        + "</div>"
    )


def metric_band(cards):
    """The headline figures, as one hairline-separated row.

    Takes rendered cards, like every other container here — ``channel_grid``,
    ``priority_list``, ``idea_grid``. One convention across the system means a
    report never has to remember which containers build their own children.
    """
    cells = "".join(cards)
    return f'<div class="td-metrics">{cells}</div>' if cells else ""


def section(title, body, eyebrow=None, lede=None, anchor=None):
    """A titled block. The eyebrow labels it; the lede sets expectations.

    ``anchor`` gives the section a stable id, so a report can be linked to by
    part — "see the recommendations" in an email should land on them.
    """
    head = "".join([
        f'<p class="td-eyebrow">{escape(eyebrow)}</p>' if eyebrow else "",
        f'<h2 class="td-section-title">{escape(title)}</h2>',
        f'<p class="td-lede">{escape(lede)}</p>' if lede else "",
    ])
    identity = f' id="{escape(anchor)}"' if anchor else ""
    return (f'<section class="td-section"{identity}>'
            f'<div class="td-section-head">{head}</div>{body}</section>')


# --------------------------------------------------------------------------
# Channels
# --------------------------------------------------------------------------

def channel_card(name, state_label, tone, observation=None, figures=()):
    """One channel's health: state, one sentence, and at most a figure or two.

    No gap lists and no technical detail. The question a reader has here is
    "can this report see my email programme?", and that is answered by a state
    and a sentence.
    """
    stats = "".join(
        f'<span class="td-figure"><b>{escape(value)}</b>{escape(label)}</span>'
        for label, value in figures if value not in (None, "")
    )
    classes = "td-channel td-channel--off" if tone == "off" else "td-channel"
    return (
        f'<div class="{classes}">'
        '<div class="td-channel-top">'
        f'<h3 class="td-channel-name">{escape(name)}</h3>'
        f"{status_chip(state_label, tone)}"
        "</div>"
        + (f'<p class="td-channel-note">{escape(observation)}</p>'
           if observation else "")
        + (f'<div class="td-channel-figures">{stats}</div>' if stats else "")
        + "</div>"
    )


def channel_grid(cards):
    return f'<div class="td-channels">{"".join(cards)}</div>' if cards else ""


# --------------------------------------------------------------------------
# Priorities, ideas, actions, insights
# --------------------------------------------------------------------------

def priority_row(rank, channel, title, why, state_label, tone,
                 recommended=False, priority_label=None, score=None,
                 confidence_label=None, confidence_level=0):
    """One ranked opportunity — the unit this section is scanned by.

    ``recommended`` is the only thing that changes the row's class, and the view
    model refuses to set it under a closed gate. So a withheld item cannot be
    styled as an approved action; it is a different row, not the same row with a
    softer adjective.
    """
    kind = "opportunity" if recommended else "monitoring"
    meta = "".join(part for part in (
        score_meter(score),
        confidence_meter(confidence_label, confidence_level)
        if confidence_label else "",
    ) if part)
    return (
        f'<article class="td-priority td-priority--{kind} td-card--{kind}">'
        f'<div class="td-priority-rank">{escape(rank)}</div>'
        f'<div class="td-priority-channel">{escape(channel)}</div>'
        f'<h3 class="td-priority-title">{escape(title)}</h3>'
        f'<p class="td-priority-why">{escape(why)}</p>'
        '<div class="td-priority-state">'
        f"{status_chip(state_label, tone, solid=True)}"
        + (f"<br>{status_chip(priority_label, 'off')}" if priority_label else "")
        + "</div>"
        + (f'<div class="td-priority-meta">{meta}</div>' if meta else "")
        + "</article>"
    )


def priority_list(rows):
    return f'<div class="td-priorities">{"".join(rows)}</div>' if rows else ""


def idea_card(title, statement, state_label, tone="idea"):
    """An exploratory idea. No score, no priority, no confidence.

    Those fields are absent because the thing itself lacks them, and an empty
    field invites a reader to fill it in. The dashed outline does real work: it
    says at a glance that this is not a finding.
    """
    return (
        '<article class="td-card--idea">'
        f"{status_chip(state_label, tone)}"
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(statement)}</p>"
        "</article>"
    )


def idea_grid(cards):
    return f'<div class="td-ideas">{"".join(cards)}</div>' if cards else ""


def action_group(title, items, emphasis=False, empty="Nothing in this group."):
    """One of the three answers to "what do we do on Monday?"."""
    classes = "td-action-group td-action-group--focus" if emphasis \
        else "td-action-group"
    if items:
        body = "<ul>" + "".join(f"<li>{escape(item)}</li>" for item in items) + "</ul>"
    else:
        body = f'<p class="td-action-empty">{escape(empty)}</p>'
    return f'<div class="{classes}"><h3>{escape(title)}</h3>{body}</div>'


def action_columns(groups):
    return f'<div class="td-actions">{"".join(groups)}</div>' if groups else ""


def insight_card(headline, detail=None):
    """One short learning. Two sentences at most, by construction."""
    return (
        '<article class="td-insight">'
        f'<p>{escape(headline)}</p>'
        + (f"<p>{escape(detail)}</p>" if detail else "")
        + "</article>"
    )


def insight_grid(cards):
    return f'<div class="td-insights">{"".join(cards)}</div>' if cards else ""


def data_table(columns, rows, caption=None):
    """A ranked list of entities — top pages, top queries, top anything.

    Deliberately plain: hairlines, tabular numerals, no zebra striping and no
    borders around cells. A table earns its place when the reader wants to
    compare rows, and everything else in it is noise.
    """
    if not rows:
        return ""
    numeric_class = ' class="td-numeric"'
    head = "".join(
        f"<th{numeric_class if numeric else ''}>{escape(name)}</th>"
        for name, numeric in columns
    )
    body = "".join(
        "<tr>" + "".join(
            f"<td{numeric_class if numeric else ''}>{escape(cell)}</td>"
            for cell, (_, numeric) in zip(row, columns)
        ) + "</tr>"
        for row in rows
    )
    return (
        '<div class="td-table-wrap"><table class="td-table">'
        + (f"<caption>{escape(caption)}</caption>" if caption else "")
        + f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>"
    )


def note_panel(title, body):
    """A short explanation that qualifies the figures above it.

    Sunk rather than raised: it is context, not a finding, and a caveat styled
    like a card competes with the results it is qualifying.
    """
    if not body:
        return ""
    return ('<div class="td-note">'
            + (f'<h3 class="td-eyebrow">{escape(title)}</h3>' if title else "")
            + f"<p>{escape(body)}</p></div>")


def empty_state(text):
    """An honest nothing-here. Says why, so it does not read as a failure."""
    return f'<div class="td-empty">{escape(text)}</div>'


def onward_link(label, href, note=None):
    """A link to the report that continues this one.

    The only link component in the system, and deliberately not a button. A
    button promises that something will happen; the only thing that happens
    here is that another document opens, and a summary card that looked
    clickable-into-an-action would be making a promise the page cannot keep.

    ``href`` is escaped like any other value. A report's own composition
    supplies it, never a document — a URL that arrived inside an artifact would
    be untrusted input pointing wherever it liked.
    """
    if not (label or "").strip() or not (href or "").strip():
        return ""
    return ('<div class="td-onward">'
            f'<a href="{escape(href)}">{escape(label)}</a>'
            + (f"<p>{escape(note)}</p>" if note else "")
            + "</div>")


# --------------------------------------------------------------------------
# The drawer
# --------------------------------------------------------------------------

def technical_drawer(blocks, summary="Technical evidence"):
    """Everything technical, behind one disclosure the reader must open.

    Nothing is removed — the internal states, the fingerprints, the full gap
    lists and the refusals are all the audit trail, and someone will need them.
    Fencing them here is what lets the report above be written in business
    language while the exact machine state stays recoverable, and lets a test
    check the first claim by scanning everything outside this block.
    """
    body = "".join(part for part in blocks if part)
    if not body:
        return ""
    return ('<details class="td-technical">'
            f"<summary>{escape(summary)}</summary>{body}</details>")


def technical_table(title, rows):
    body = "".join(
        f"<tr><th>{escape(term)}</th><td><code>{escape(value)}</code></td></tr>"
        for term, value in rows if value not in (None, "", [], {})
    )
    if not body:
        return ""
    return f"<h3>{escape(title)}</h3><table><tbody>{body}</tbody></table>"


def technical_list(title, items):
    entries = "".join(f"<li>{escape(item)}</li>" for item in items if item)
    if not entries:
        return ""
    return f"<h3>{escape(title)}</h3><ul>{entries}</ul>"


def footer(theme=TRAFFICDOM, statement=None):
    """The standing statement, under the brand signature."""
    signature = ""
    if theme.logo:
        signature = ('<p class="td-signature">'
                     f'<img src="{escape(theme.logo)}" '
                     f'alt="{escape(theme.logo_alt)}"></p>')
    return ('<footer class="td-footer">'
            f"{signature}<p>{escape(statement or theme.footer)}</p></footer>")


# --- integrity ---
# sha256 of every byte above this marker, first 16 hex characters. A consumer
# splits on the marker, hashes what precedes it, and compares — needing to know
# nothing about how this file was assembled.
CONTENT_HASH = "a640e8cb62bbfcda"
