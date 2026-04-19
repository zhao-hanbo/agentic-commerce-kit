# `/audit-agentic-commerce`

Score an ecommerce store against the 9-criterion **Agentic Commerce
Readiness Index**. Works on any storefront; tuned for Shopify.

## What it does

Runs the same audit methodology used in the [Nohi Readiness Index
Edition 1](https://github.com/zhao-hanbo/agentic-commerce-kit#the-rubric)
(Premium DTC Beauty, 50 brands, April 2026). Given one store URL, it:

1. Checks `robots.txt` for AI-crawler access (C1)
2. Samples 3 product pages from the sitemap, verifies server-side
   rendering (C2), and checks JSON-LD for `Product` (C4) and
   `AggregateRating` (C5) via **source-level `curl` fetch** (not
   WebFetch — see methodology note below)
3. Confirms sitemap freshness (C3)
4. Checks homepage + auxiliary pages for `FAQPage`/`HowTo` (C6) and
   `Organization` (C7) schema, source-level
5. LLM-evaluates 5 PDP titles and descriptions for use-case specificity
   and buyer context (C8, C9)

Output: score / 9, shape-describing label, per-criterion findings with
sample-scope caveats and specific fixes, schema-hygiene flags for
malformed-but-present JSON-LD, and a ranked top-3 priority list.

## Install

Copy `command.md` into your project at:

```
.claude/commands/audit-agentic-commerce.md
```

Or for user-level install (available across all projects):

```
~/.claude/commands/audit-agentic-commerce.md
```

Requires [Claude Code](https://claude.com/product/claude-code) with
`Bash` tool access enabled (for `curl`) and Python 3.9+ on PATH
(for the HTML renderer; only needed if you use `--output=html`). No
other dependencies.

## Run

```
/audit-agentic-commerce https://www.summerfridays.com
```

Takes ~60-90 seconds.

### Flags

**Sampling**
- `--confidence=high` — keeps the 3-PDP Index score but adds a 15-PDP
  stability check and reports a confidence delta. Use when the base
  sample might be unlucky.
- `--full` — audits every PDP in the sitemap (capped at 200). Slow and
  more expensive in tool calls. Intended for paid audit engagements
  where "sample-based" isn't enough.

**Output** (v1.2+)
- `--output=md` (default) — Markdown report only.
- `--output=html` — ALSO emit a self-contained, shareable HTML report
  (rendered by `render.py`, no browser deps).
- `--output=json` — JSON only, for downstream pipelines / dashboards /
  cross-brand aggregation.
- `--output=both` — Markdown + HTML.

Examples:

```
# Default: markdown only
/audit-agentic-commerce https://www.shopcider.com

# Stakeholder share: HTML artifact
/audit-agentic-commerce https://www.shopcider.com --output=html

# Higher-confidence audit + HTML share
/audit-agentic-commerce https://www.shopcider.com --confidence=high --output=both

# Data pipeline: JSON only
/audit-agentic-commerce https://www.shopcider.com --output=json
```

## Architecture (v1.2)

```
skills/audit-agentic-commerce/
├── command.md      Claude Code slash command — orchestrates the audit
├── render.py       Stdlib-only HTML renderer (input: JSON, output: HTML)
├── example.json    Canonical example audit (Cider) — use as schema reference
└── README.md       You are here
```

Claude does the audit work and emits a structured JSON dict. `render.py`
transforms JSON into a self-contained HTML file with score ring, area
gauges, criterion grid, finding cards, and a collapsible check log. The
separation means:

- Claude focuses on judgement (what passes, what doesn't, why)
- Rendering is deterministic — same JSON always produces same HTML
- JSON output can feed dashboards or cross-brand comparisons without
  re-parsing prose

## Methodology notes

### Why `curl`, not WebFetch, for schema

Claude Code's `WebFetch` converts HTML to markdown before returning
it to the model — this strips `<script type="application/ld+json">`
blocks. If you only use WebFetch, you cannot reliably check whether a
page has schema; you can only check what made it through the markdown
conversion (the visible text).

This skill uses `Bash` + `curl` + a Python `json.loads` parser as the
**primary path** for C4/C5/C6/C7. WebFetch is used only for:
- `robots.txt` (C1) — plain text, no schema issue
- `sitemap.xml` (C3) — XML, structured naturally
- Visible-text evaluation for SSR (C2), titles (C8), descriptions (C9)

If `curl` is blocked (rare — most stores ship JSON-LD in initial HTML),
findings fall back to WebFetch with an explicit "not source-verified"
caveat in the report.

### Sample-based vs. sitewide

Default audit samples **3 PDPs** for C2/C4/C5 and **5 PDPs** for
C8/C9. This keeps the score directly comparable to the [Nohi
Readiness Index](https://nohi.ai/research/agentic-readiness-index-edition-1)
scoring methodology. All findings in the default mode use sample-based
language ("across the 3 sampled PDPs") — never "sitewide" unless you
run with `--full`.

`--confidence=high` runs the 3-PDP score first (for comparability),
then a 15-PDP extended check (for stability). The report includes a
"confidence delta" section showing whether the extended sample
confirms, weakens, or overturns the headline score.

### Anti-hallucination

The skill is instructed to quote only text actually returned by a tool
call. It will not describe "what's on the about page" unless it
fetched the about page.

## Sample output

See [the kit's root README](../../README.md#sample-audit-summer-fridays)
for a sample audit of Summer Fridays with source-level evidence.

## Why this exists

Most "SEO audit" tools score for Google's organic ranking signals.
Agentic commerce (ChatGPT Shopping, Perplexity Buy with Pro, Google
AI Mode, Claude's forthcoming commerce capabilities) uses a **different
retrieval stack**:

- They respect `robots.txt` for their specific user agents
- They rely on structured data (JSON-LD) more heavily than web search
- They cannot execute JavaScript on arbitrary merchant sites
- They favor pages where title + description + schema together answer
  "does this product match what the shopper is asking for?"

This skill operationalizes what "ready for agents" actually means,
criterion-by-criterion, with source-level evidence.

## Limits

- **C10 (content uniqueness)** is deferred — not in this skill
- **Non-standard URL patterns**: default sitemap parsing assumes
  `/products/*` (Shopify) or the sitemap has `<url>` entries for PDPs.
  For custom URL patterns (e.g. Cider uses `/goods/{slug}-{id}`), the
  skill adapts but may need manual PDP URL hints for edge cases
- **Rate limits**: Claude Code's `Bash` and `WebFetch` each have rate
  limits. A single-store audit is fine. `--full` on a 200-PDP catalog
  may take several minutes
- **Geography / local retrieval** is out of scope — a future "GEO
  Readiness Index" will cover retrieval for local/regional queries

## License

MIT.
