#!/usr/bin/env python3
"""
render.py — Agentic Commerce Readiness Index HTML renderer

Takes a structured audit JSON file and emits a self-contained HTML report.
Single file, stdlib only, no external dependencies.

Usage:
    python3 render.py audit-<slug>.json
    python3 render.py audit-<slug>.json --output custom.html

Input JSON structure is documented in schema.json (see same directory).

Part of agentic-commerce-kit v1.2+.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from html import escape as html_escape
from pathlib import Path
from typing import Any

# ─────────────────────────────────────────────────────────────────────────────
# CSS — kept verbatim with the hand-crafted Cider v2 template for parity.
# ─────────────────────────────────────────────────────────────────────────────

CSS = """
:root {
  --ink: #0f1419;
  --ink-soft: #3c4853;
  --ink-muted: #6b7680;
  --pass: #0d8577;
  --pass-bg: #e8f5f2;
  --fail: #b5412d;
  --fail-bg: #fbece7;
  --warn: #b87520;
  --warn-bg: #fdf3e4;
  --bg: #fbfaf7;
  --card: #ffffff;
  --border: #e5e1d8;
  --code-bg: #f4f1ec;
  --accent: #2b4a5c;
  --stripe-1: #f0ece2;
  --stripe-2: #e5e1d8;
}
[data-theme="dark"] {
  --ink: #e8eaed;
  --ink-soft: #b8bdc4;
  --ink-muted: #7d848d;
  --pass: #4dbfad;
  --pass-bg: #143027;
  --fail: #e08774;
  --fail-bg: #3a1f17;
  --warn: #e5b46a;
  --warn-bg: #3a2d15;
  --bg: #0f1419;
  --card: #1a2028;
  --border: #2a3139;
  --code-bg: #1e252e;
  --accent: #8fb4c9;
  --stripe-1: #252c35;
  --stripe-2: #2a3139;
}
* { box-sizing: border-box; }
html { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  color: var(--ink);
  background: var(--bg);
  margin: 0;
  line-height: 1.55;
  font-size: 16px;
}
main { max-width: 820px; margin: 0 auto; padding: 48px 24px 80px; }
.header { margin-bottom: 40px; }
.eyebrow { font-size: 12px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 8px; }
h1 { font-size: 32px; line-height: 1.2; font-weight: 700; margin: 0 0 8px; letter-spacing: -0.01em; }
.store-url { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 14px; color: var(--accent); }
.meta { display: flex; gap: 16px; margin-top: 20px; padding-top: 20px; border-top: 1px solid var(--border); font-size: 13px; color: var(--ink-muted); flex-wrap: wrap; }
.meta-item strong { color: var(--ink-soft); font-weight: 600; }
.hero { display: grid; grid-template-columns: auto 1fr; gap: 32px; align-items: center; padding: 32px; margin-bottom: 32px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; }
.score-ring { width: 140px; height: 140px; position: relative; }
.score-ring svg { display: block; }
.score-ring .number { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }
.score-ring .number .big { font-size: 40px; font-weight: 700; line-height: 1; letter-spacing: -0.02em; }
.score-ring .number .small { font-size: 15px; color: var(--ink-muted); margin-top: 2px; }
.hero-label { font-size: 22px; font-weight: 600; letter-spacing: -0.01em; margin-bottom: 6px; }
.hero-sublabel { color: var(--ink-muted); font-size: 14px; line-height: 1.5; }
.areas { margin-bottom: 40px; }
.section-label { font-size: 11px; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--ink-muted); margin-bottom: 16px; }
.area-row { display: grid; grid-template-columns: 180px 1fr 56px; align-items: center; gap: 16px; padding: 14px 0; border-bottom: 1px solid var(--border); font-size: 14px; }
.area-row:last-child { border-bottom: none; }
.area-name { font-weight: 600; }
.area-name .area-num { display: inline-block; width: 22px; color: var(--ink-muted); font-weight: 500; }
.bar { position: relative; height: 28px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; display: flex; }
.segment { flex: 1; border-right: 1px solid var(--border); }
.segment:last-child { border-right: none; }
.segment.pass { background: var(--pass); }
.segment.fail { background: repeating-linear-gradient(45deg, var(--stripe-1), var(--stripe-1) 4px, var(--stripe-2) 4px, var(--stripe-2) 8px); }
.area-score { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-weight: 600; text-align: right; color: var(--ink-soft); }
.criteria-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 48px; }
.criterion-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; position: relative; border-left: 3px solid var(--border); }
.criterion-card.pass { border-left-color: var(--pass); }
.criterion-card.fail { border-left-color: var(--fail); }
.crit-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.crit-icon { width: 18px; height: 18px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; color: white; flex-shrink: 0; }
.crit-icon.pass { background: var(--pass); }
.crit-icon.fail { background: var(--fail); }
.crit-id { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 12px; font-weight: 600; color: var(--ink-muted); }
.crit-title { font-size: 14px; font-weight: 600; line-height: 1.3; margin: 0 0 4px; }
.crit-finding { font-size: 13px; color: var(--ink-soft); line-height: 1.45; }
.detail-section { margin-bottom: 48px; }
h2 { font-size: 22px; font-weight: 700; letter-spacing: -0.01em; margin: 0 0 16px; }
h3 { font-size: 17px; font-weight: 600; margin: 24px 0 8px; display: flex; align-items: center; gap: 10px; }
.pill { display: inline-flex; align-items: center; gap: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; }
.pill.pass { background: var(--pass-bg); color: var(--pass); }
.pill.fail { background: var(--fail-bg); color: var(--fail); }
.pill.warn { background: var(--warn-bg); color: var(--warn); }
p { margin: 0 0 12px; }
.detail-section p { color: var(--ink-soft); }
code, .code-inline { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 13px; background: var(--code-bg); padding: 1px 5px; border-radius: 3px; color: var(--accent); }
pre { background: var(--code-bg); border: 1px solid var(--border); border-radius: 6px; padding: 14px 16px; overflow-x: auto; font-size: 12.5px; line-height: 1.5; margin: 12px 0; }
pre code { background: none; padding: 0; color: var(--ink); }
table { width: 100%; border-collapse: collapse; margin: 12px 0; font-size: 13.5px; }
th, td { text-align: left; padding: 8px 12px; border-bottom: 1px solid var(--border); }
th { font-weight: 600; color: var(--ink-muted); font-size: 12px; letter-spacing: 0.02em; text-transform: uppercase; background: var(--bg); }
td.num { font-family: ui-monospace, "SF Mono", Menlo, monospace; }
.finding { background: var(--card); border: 1px solid var(--border); border-left: 3px solid var(--fail); border-radius: 10px; padding: 20px 22px; margin-bottom: 14px; }
.finding.warn { border-left-color: var(--warn); background: var(--warn-bg); border-color: #e7c07e; }
.finding-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.finding-header .crit-id { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size: 13px; font-weight: 700; color: var(--ink-muted); }
.finding-header .finding-title { font-size: 16px; font-weight: 600; color: var(--ink); }
.finding-grid { display: grid; grid-template-columns: 90px 1fr; gap: 6px 16px; margin: 0; }
.finding-grid dt { font-size: 11px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; color: var(--ink-muted); padding-top: 3px; }
.finding-grid dd { margin: 0; font-size: 14px; color: var(--ink-soft); line-height: 1.5; }
.finding-grid dd + dt { margin-top: 8px; }
.finding-grid code { font-size: 12.5px; }
.finding-grid a { color: var(--accent); text-decoration: underline; text-decoration-color: rgba(43,74,92,0.3); text-underline-offset: 2px; }
details.check-log { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 0; margin: 24px 0; }
details.check-log summary { cursor: pointer; padding: 14px 20px; font-size: 14px; font-weight: 600; color: var(--ink-soft); list-style: none; display: flex; justify-content: space-between; align-items: center; }
details.check-log summary::-webkit-details-marker { display: none; }
details.check-log summary::after { content: "▸"; color: var(--ink-muted); font-size: 12px; transition: transform 0.15s; }
details.check-log[open] summary::after { transform: rotate(90deg); }
details.check-log[open] summary { border-bottom: 1px solid var(--border); }
.check-log-body { padding: 8px 0; }
.check-log-row { display: grid; grid-template-columns: 32px 40px 1fr; gap: 12px; align-items: baseline; padding: 8px 20px; font-size: 13.5px; }
.check-log-row .crit-icon { width: 16px; height: 16px; font-size: 10px; }
.check-log-row .crit-id { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-weight: 700; font-size: 12px; color: var(--ink-muted); }
.check-log-row .log-text { color: var(--ink-soft); }
.check-log-row .log-text strong { color: var(--ink); font-weight: 600; }
.fix-list { counter-reset: fix; list-style: none; padding: 0; margin: 0; }
.fix-list li { counter-increment: fix; background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px 18px 64px; margin-bottom: 12px; position: relative; }
.fix-list li::before { content: counter(fix); position: absolute; left: 20px; top: 18px; width: 32px; height: 32px; background: var(--accent); color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 15px; }
.fix-list strong { display: block; margin-bottom: 6px; font-size: 15px; }
.fix-list p { margin: 0; font-size: 13.5px; color: var(--ink-soft); }
.real-story { background: linear-gradient(180deg, var(--bg) 0%, var(--card) 100%); border: 1px solid var(--border); border-radius: 12px; padding: 28px; margin-bottom: 32px; }
.real-story h2 { margin-top: 0; }
.real-story p { font-size: 15px; color: var(--ink); line-height: 1.6; }
footer { margin-top: 48px; padding-top: 24px; border-top: 1px solid var(--border); font-size: 12px; color: var(--ink-muted); line-height: 1.6; }
footer a { color: var(--accent); }
[data-compact] main { padding: 28px 20px 40px; }
[data-compact] h1 { font-size: 24px; }
[data-compact] .header { margin-bottom: 24px; }
[data-compact] .hero { padding: 20px; margin-bottom: 20px; gap: 24px; }
[data-compact] .score-ring { width: 96px; height: 96px; }
[data-compact] .score-ring svg { width: 96px; height: 96px; }
[data-compact] .score-ring .number .big { font-size: 30px; }
[data-compact] .hero-label { font-size: 18px; }
[data-compact] .hero-sublabel { font-size: 13px; }
[data-compact] .areas { margin-bottom: 24px; }
[data-compact] .area-row { padding: 10px 0; font-size: 13px; }
[data-compact] .bar { height: 22px; }
[data-compact] .criteria-grid { gap: 8px; margin-bottom: 32px; }
[data-compact] .criterion-card { padding: 12px; }
[data-compact] .crit-title { font-size: 13px; }
[data-compact] .crit-finding { font-size: 12.5px; }
[data-compact] h2 { font-size: 18px; }
[data-compact] .finding { padding: 14px 16px; margin-bottom: 10px; }
[data-compact] .finding-header .finding-title { font-size: 15px; }
[data-compact] .finding-grid dd { font-size: 13px; }
[data-compact] .fix-list li { padding: 14px 16px 14px 56px; }
[data-compact] .fix-list li::before { left: 16px; top: 14px; width: 28px; height: 28px; font-size: 13px; }
[data-compact] .real-story { padding: 20px; margin-bottom: 20px; }
[data-compact] .real-story p { font-size: 14px; }
[data-compact] .detail-section { margin-bottom: 28px; }
[data-compact] footer { margin-top: 28px; font-size: 11px; }
@media print {
  body { background: white; }
  main { padding: 24px; max-width: none; }
  .hero, .finding, .real-story, .criterion-card, .fix-list li { break-inside: avoid; }
  details.check-log { display: none; }
  footer { break-before: avoid; }
}
@media (max-width: 640px) {
  main { padding: 32px 16px 60px; }
  h1 { font-size: 26px; }
  .hero { grid-template-columns: 1fr; text-align: center; padding: 24px; }
  .score-ring { margin: 0 auto; }
  .criteria-grid { grid-template-columns: 1fr; }
  .area-row { grid-template-columns: 120px 1fr 44px; }
}
"""

# ─────────────────────────────────────────────────────────────────────────────
# Section renderers
#
# Content fields in the JSON are treated as **HTML-safe fragments** — the user
# may include inline <code>, <strong>, <em>, <a> tags for emphasis. Plain text
# is fine too (we don't escape). The producer (Claude) is responsible for not
# emitting unsafe content; this is a developer tool, not a public form.
# ─────────────────────────────────────────────────────────────────────────────


def render_header(meta: dict, score: dict) -> str:
    store_name = html_escape(meta["store_name"])
    store_url = html_escape(meta["store_url"])
    audit_date = html_escape(meta["audit_date"])
    sampling = html_escape(meta.get("sampling_scope", ""))
    evidence = meta.get("evidence_method", "source-level <code>curl</code>")
    title = meta.get("audit_title", "Agentic Commerce Readiness Audit")

    return f"""
<header class="header">
  <div class="eyebrow">{html_escape(title)}</div>
  <h1>{store_name}</h1>
  <a class="store-url" href="{store_url}">{store_url}</a>
  <div class="meta">
    <div class="meta-item"><strong>Audit date:</strong> {audit_date}</div>
    <div class="meta-item"><strong>Sampling:</strong> {sampling}</div>
    <div class="meta-item"><strong>Evidence:</strong> {evidence}</div>
  </div>
</header>
"""


def render_score_hero(score: dict) -> str:
    total = score["total"]
    max_score = score["max"]
    label = html_escape(score["shape_label"])
    description = score.get("description", "")  # HTML-safe fragment

    circumference = 2 * math.pi * 60
    filled = (total / max_score) * circumference
    empty = circumference - filled

    return f"""
<section class="hero">
  <div class="score-ring">
    <svg width="140" height="140" viewBox="0 0 140 140">
      <circle cx="70" cy="70" r="60" fill="none" stroke="#e5e1d8" stroke-width="14"/>
      <circle cx="70" cy="70" r="60" fill="none"
        stroke="#0d8577" stroke-width="14"
        stroke-dasharray="{filled:.2f} {circumference:.2f}"
        stroke-dashoffset="0"
        transform="rotate(-90 70 70)"
        stroke-linecap="round"/>
    </svg>
    <div class="number">
      <div class="big">{total}<span style="color:var(--ink-muted);font-weight:500;">/{max_score}</span></div>
      <div class="small">score</div>
    </div>
  </div>
  <div>
    <div class="hero-label">{label}</div>
    <div class="hero-sublabel">{description}</div>
  </div>
</section>
"""


def render_area_bars(areas: list[dict]) -> str:
    rows = []
    for area in areas:
        num = area["num"]
        name = html_escape(area["name"])
        score = area["score"]
        max_score = area["max"]

        segments = []
        for i in range(max_score):
            cls = "pass" if i < score else "fail"
            segments.append(f'<div class="segment {cls}"></div>')

        rows.append(f"""
  <div class="area-row">
    <div class="area-name"><span class="area-num">{num}.</span> {name}</div>
    <div class="bar">{"".join(segments)}</div>
    <div class="area-score">{score}/{max_score}</div>
  </div>""")

    return f"""
<section class="areas">
  <div class="section-label">Area breakdown</div>
  {"".join(rows)}
</section>
"""


def render_criterion_grid(criteria: list[dict]) -> str:
    cards = []
    for c in criteria:
        cid = html_escape(c["id"])
        title = html_escape(c["title"])
        status = c["status"]  # "pass" | "fail"
        one_liner = c["one_liner"]  # HTML-safe fragment
        icon = "✓" if status == "pass" else "✗"

        cards.append(f"""
    <div class="criterion-card {status}">
      <div class="crit-header">
        <span class="crit-icon {status}">{icon}</span>
        <span class="crit-id">{cid}</span>
      </div>
      <div class="crit-title">{title}</div>
      <div class="crit-finding">{one_liner}</div>
    </div>""")

    return f"""
<section>
  <div class="section-label">The 9 criteria</div>
  <div class="criteria-grid">{"".join(cards)}
  </div>
</section>
"""


def render_findings(findings: list[dict]) -> str:
    if not findings:
        return ""

    cards = []
    for f in findings:
        cid = html_escape(f["id"])
        title = html_escape(f["title"])
        pill_type = f.get("pill", "fail")  # "fail" | "warn"
        pill_label = html_escape(f.get("pill_label", "Fail" if pill_type == "fail" else "Flag"))
        finding_cls = "finding warn" if pill_type == "warn" else "finding"

        rows = []
        for field in f["fields"]:
            label = html_escape(field["label"])
            content = field["content"]  # HTML-safe fragment
            rows.append(f"      <dt>{label}</dt>\n      <dd>{content}</dd>")

        cards.append(f"""
  <div class="{finding_cls}">
    <div class="finding-header">
      <span class="crit-id">{cid}</span>
      <span class="finding-title">{title}</span>
      <span class="pill {pill_type}">{pill_label}</span>
    </div>
    <dl class="finding-grid">
{chr(10).join(rows)}
    </dl>
  </div>""")

    intro = "The top 9-criterion grid shows all checks. Detail below covers only items that need action."

    return f"""
<section class="detail-section">
  <h2>What needs fixing</h2>
  <p style="color:var(--ink-muted);font-size:14px;">{intro}</p>
  {"".join(cards)}
</section>
"""


def render_check_log(criteria: list[dict]) -> str:
    rows = []
    for c in criteria:
        cid = html_escape(c["id"])
        status = c["status"]
        icon = "✓" if status == "pass" else "✗"
        log_text = c.get("log_summary", c["one_liner"])  # HTML-safe fragment

        rows.append(f"""
    <div class="check-log-row">
      <span class="crit-icon {status}">{icon}</span>
      <span class="crit-id">{cid}</span>
      <span class="log-text">{log_text}</span>
    </div>""")

    return f"""
<details class="check-log">
  <summary>View complete check log (all {len(criteria)} criteria)</summary>
  <div class="check-log-body">{"".join(rows)}
  </div>
</details>
"""


def render_fixes(fixes: list[dict]) -> str:
    if not fixes:
        return ""

    items = []
    for fix in fixes:
        title = fix["title"]  # HTML-safe fragment
        description = fix["description"]  # HTML-safe fragment
        items.append(f"""    <li>
      <strong>{title}</strong>
      <p>{description}</p>
    </li>""")

    epilogue = fixes[0].get(
        "_epilogue",
        "Implementing the top fixes would move this brand materially upward on this framework. Final score depends on implementation quality and broader content improvements.",
    )
    # allow the caller to override via a top-level field later; for now accept
    # _epilogue passed on the first fix as a pragmatic convention, else default

    return f"""
<section class="detail-section">
  <h2>Fix priority</h2>
  <p style="color:var(--ink-muted);font-size:14px;">Ranked by leverage on agent discoverability, highest first.</p>
  <ol class="fix-list">
{chr(10).join(items)}
  </ol>
  <p style="font-size:14px;color:var(--ink-muted);margin-top:16px;">{epilogue}</p>
</section>
"""


def render_real_story(real_story: dict) -> str:
    if not real_story:
        return ""

    heading = html_escape(real_story.get("heading", "The real story"))
    paragraphs = real_story.get("paragraphs", [])
    if not paragraphs:
        return ""

    para_html = "".join(f"\n  <p>{p}</p>" for p in paragraphs)

    return f"""
<section class="real-story">
  <h2>{heading}</h2>{para_html}
</section>
"""


def render_footer(disclosure: str) -> str:
    return f"""
<footer>
  <p>{disclosure}</p>
  <p style="margin-top:12px;">Generated by <a href="https://github.com/zhao-hanbo/agentic-commerce-kit">agentic-commerce-kit</a> / <code>/audit-agentic-commerce</code> — a Claude Code skill scoring stores against the Nohi Agentic Commerce Readiness Index methodology.</p>
</footer>
"""


# ─────────────────────────────────────────────────────────────────────────────
# Top-level render
# ─────────────────────────────────────────────────────────────────────────────

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{css}</style>
</head>
<body{body_attrs}>
<main>
{header}
{hero}
{areas}
{grid}
{findings}
{check_log}
{fixes}
{real_story}
{footer}
</main>
</body>
</html>
"""


def render(
    audit: dict[str, Any],
    theme: str = "light",
    compact: bool = False,
) -> str:
    """Render an audit dict (loaded from JSON) to a complete HTML string.

    Args:
        audit: the parsed JSON audit dict.
        theme: "light" (default) or "dark".
        compact: if True, apply compact spacing/fonts (good for print or embed).
    """
    meta = audit["meta"]
    store_name = meta["store_name"]
    page_title = f"Agentic Commerce Readiness Audit — {store_name}"

    body_attrs = ""
    if theme == "dark":
        body_attrs += ' data-theme="dark"'
    if compact:
        body_attrs += " data-compact"

    return PAGE_TEMPLATE.format(
        title=html_escape(page_title),
        css=CSS,
        body_attrs=body_attrs,
        header=render_header(meta, audit["score"]),
        hero=render_score_hero(audit["score"]),
        areas=render_area_bars(audit["areas"]),
        grid=render_criterion_grid(audit["criteria"]),
        findings=render_findings(audit.get("findings", [])),
        check_log=render_check_log(audit["criteria"]),
        fixes=render_fixes(audit.get("fixes", [])),
        real_story=render_real_story(audit.get("real_story", {})),
        footer=render_footer(audit.get("disclosure", "")),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render an agentic-commerce-kit audit JSON to self-contained HTML.",
    )
    parser.add_argument("input", type=Path, help="Path to audit JSON file")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output HTML path (default: same basename as input with .html)",
    )
    parser.add_argument(
        "--theme",
        choices=["light", "dark"],
        default="light",
        help="Color theme (default: light)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Compact spacing and fonts (good for print or embed)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 1

    with args.input.open() as f:
        audit = json.load(f)

    html = render(audit, theme=args.theme, compact=args.compact)

    output = args.output or args.input.with_suffix(".html")
    output.write_text(html, encoding="utf-8")

    print(f"Wrote {output} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
