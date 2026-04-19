---
description: Score an ecommerce store against the 9-criterion Agentic Commerce Readiness Index
argument-hint: <store-url> [--confidence=high] [--full]
---

You are running the **Agentic Commerce Readiness Index** audit on the store
at `$ARGUMENTS`.

The question this audit answers: **When ChatGPT, Claude, Perplexity, or
Gemini's commerce agents decide which brand to recommend for a user's
query, does this store show up with enough structured information to be
picked?**

The 9 criteria are organized into 3 areas. Each criterion scores 0 or 1.
Maximum total: 9.

## Sampling and flags

**Default sampling** (kept identical to the Nohi Readiness Index so scores
are comparable across brands): 3 PDPs sampled from the sitemap for
C2/C4/C5, and 5 PDPs for C8/C9.

**Optional flags** in `$ARGUMENTS`:
- `--confidence=high`: score on the 3/5 default sample, PLUS run an
  extended check on 15 PDPs for C4/C5/C8 and report a confidence
  delta. The Index score does not change — this is a stability signal
  ("3-sample C4=FAIL; 15-sample C4 pass rate 3/15 → finding holds").
- `--full`: score on ALL PDPs listed in the sitemap (cap at 200). Slow
  and expensive, for paid engagements where the audit is the deliverable.
  Changes the language from "sampled" to "sitewide."

If neither flag is present, default sampling applies and all findings
must use **sample-based language** (see language guardrails below).

## How to verify JSON-LD — use `Bash curl`, not WebFetch

**CRITICAL METHODOLOGY NOTE.** WebFetch converts HTML to markdown before
returning content, which strips `<script type="application/ld+json">`
blocks and hands you an LLM-summarized view. You cannot reliably check
structured data through WebFetch alone.

**Primary path for C4/C5/C6/C7** (schema checks): use Bash with curl to
fetch raw HTML, then parse JSON-LD blocks:

```bash
UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
curl -sL -A "$UA" "<page-url>" | python3 -c "
import re, sys, json
html = sys.stdin.read()
blocks = re.findall(r'<script[^>]*application/ld\+json[^>]*>(.+?)</script>', html, re.S)
for b in blocks:
    try:
        obj = json.loads(b)
        print(json.dumps(obj, indent=2)[:2000])
        print('---')
    except Exception as e:
        print(f'PARSE ERROR: {e}', b[:500])
"
```

Do this for: each sampled PDP (C4, C5), the homepage (C7), and the FAQ
page (C6). Parse the returned JSON-LD and check required fields.

**Fallback**: if `curl` is blocked by the host or returns a JS shell
(Shopify and most modern sites do not — they ship JSON-LD in the initial
HTML), fall back to WebFetch but **explicitly flag the finding** as
"not source-verified; rendered-response only."

**Use WebFetch only for**: robots.txt check (C1), sitemap check (C3),
and visible-text evaluation for PDP SSR (C2) / titles (C8) / descriptions
(C9) where rendered markdown is what you actually need.

---

## Area 1 — Crawlability & access (3 points)

### C1. AI crawler access
- Fetch `{root}/robots.txt` via WebFetch or `curl`.
- **PASS** if robots.txt explicitly allows at least 4 of: `GPTBot`,
  `PerplexityBot`, `ClaudeBot`, `anthropic-ai` (legacy name),
  `Google-Extended`, `Amazonbot`, `CCBot`, `FacebookBot`. "Allowed" means
  no matching `Disallow: /` block for that user agent.
- **FAIL** if 4+ are blocked, OR if robots.txt is missing.

### C2. PDP server-side render
- Fetch `{root}/sitemap.xml` (follow sitemap index if present), pick 3
  PDP URLs.
- For each PDP, use `curl` to fetch raw HTML. Verify the raw HTML (before
  any JS execution) contains: (a) product title/name, (b) price, (c)
  description. Confirm by grepping for these strings in the body.
- **PASS** if 3/3 PDPs have all three in raw HTML.
- **FAIL** if any PDP is a JS shell (empty `<body>`, skeleton loader,
  or requires hydration).

### C3. Sitemap freshness
- Parse `{root}/sitemap.xml` via `curl`.
- **PASS** if sitemap is valid XML, contains product URLs, AND has at
  least one `<lastmod>` within the past 90 days.
- **FAIL** if missing, invalid, or all stale.

## Area 2 — Structured data (4 points)

Extract JSON-LD using the `curl` pattern above. Handle both single-object
blocks and `@graph` arrays. Some sites ship multiple Product blocks per
PDP (one per SKU/variant) — evaluate all of them, not just the first.

### C4. Product schema on PDPs
- Same 3 PDPs from C2.
- **PASS** if 3/3 have at least one valid `schema.org/Product` JSON-LD
  block containing commonly-recommended minimum fields per Google's
  rich-results guidance: `name`, `image`, `brand`, `offers` (with `price`
  AND `availability`), AND at least one of `gtin`, `mpn`, `sku`.
- Flag but do not fail for: malformed duplicate blocks (e.g. a second
  Product block where `brand.@type` is set to the brand name instead of
  `"Brand"`, or the product name is mangled). Report these as schema
  hygiene issues separate from the criterion pass/fail.

### C5. Review / AggregateRating schema
- Same 3 PDPs.
- **PASS** if 3/3 have `aggregateRating` (or `review` array) inside the
  Product block with a real `ratingValue` AND `reviewCount > 0`.
- **FAIL** if rating data is absent or values look like placeholders.

### C6. FAQPage / HowTo schema
- Fetch the homepage plus discoverable FAQ / help / how-to-use pages
  using `curl`.
- **PASS** if at least one page emits valid `FAQPage` or `HowTo` JSON-LD.
- **FAIL** if none observed at the source level.

### C7. Organization schema
- Fetch the homepage via `curl`.
- **PASS** if a valid `Organization` JSON-LD block contains at minimum:
  `name`, `url`, AND `sameAs` array with at least 2 social-profile URLs.
- Partial cases to flag: Organization schema exists but is minimal (only
  `url` + `logo`, missing `sameAs` or `name`). Still FAIL for the
  criterion but surface in findings as "minimal Organization schema
  present — missing `sameAs`."

## Area 3 — Content quality (2 points)

### C8. PDP titles include use case / differentiator
- Sample up to 5 PDP titles from the sitemap.
- For each title, judge: does it include a specific use case, target
  audience, fabric/ingredient, fit/neckline/silhouette, or any
  differentiator beyond brand + generic category?
  - PASS example: "Retinol Alternative Night Serum for Sensitive Skin"
  - FAIL example: "Brand Name Face Cream"
- **PASS** if 4+ of 5 titles pass.

### C9. Descriptions: spec-heavy vs buyer-context-rich
- Same 5 PDPs, full visible description text.
- Judge each: does the description go beyond spec listing (material,
  dimensions, care) and include buyer context — any of: who it's for
  vs. who it isn't, comparison to similar products in this brand or
  category, rationale for ingredient/material choice, sizing/volume
  reasoning, when or how to use, what it is NOT designed for?
- **PASS** if 4+ of 5 descriptions include at least 3 buyer-context cues.
- Describe failing descriptions as "spec-heavy, limited buyer context"
  rather than "bad" or "useless."

---

## Language guardrails (apply to every finding)

This is an audit, not a sales pitch. Follow these rules in every line:

1. **Evidence scoping**: when a finding is based on sampled PDPs, write
   "across the 3 sampled PDPs" (or 15 with `--confidence=high`, etc.).
   NEVER "on any PDP" or "sitewide" unless `--full` was run. For
   homepage / about / FAQ, "on the fetched homepage" is accurate.
2. **Evidence quality — schema**:
   - If found via `curl` + JSON parse: "source-level verified: {finding}"
   - If `curl` failed and WebFetch used: "no JSON-LD observed in
     rendered response; source-level verification unavailable"
   - NEVER "zero JSON-LD" or "no schema anywhere" without source checks.
3. **Effort estimates**: NEVER give specific durations ("10 minutes",
   "2 weeks"). Use conditional phrasing: "lightweight if these fields
   already exist server-side; heavier if the data layer needs expansion."
4. **Impact claims**: describe schema changes as "improves machine
   readability and the odds of parsing, attribution, and surfacing
   across AI-assisted shopping and search." NEVER "unlocks citations,"
   "becomes a known entity," or "turns a blank result into a citation."
5. **Field requirements**: use "commonly recommended minimum fields per
   Google's rich-results guidance" — NOT "required fields" (which
   conflates schema.org and Google layers).
6. **Score trajectories**: never write "4/9 → 8/9 in one quarter."
   Instead: "implementing fixes 1-3 would move this brand materially
   upward on the framework. Final score depends on implementation
   quality and broader content improvements."
7. **Anti-hallucination**: quote only text you actually fetched through a
   tool. Never invent specific quotes, social-profile lists, or page
   content from general knowledge about the brand. If you didn't fetch
   the about page, don't describe what's on it.

---

## Output format

Produce a structured report with:

1. **Score**: `{total}/9` with a **shape-describing label** (not a
   single-word tier). Choose the phrasing that matches the distribution:
   - 8-9 → "Agent-Ready"
   - 6-7, balanced across areas → "Partially Ready"
   - 6-7, one area dominant → "Strong {area}, Weak {gap-area}"
     (e.g. "Strong Structured Data, Weak Content Layer")
   - 3-5, Area 1 strong, Area 2 weak → "Strong Foundations, Missing
     Structured Layer"
   - 3-5, Area 2 or 3 weak → "Accessible but Under-Structured"
   - 0-2 → "Not Ready — multiple foundation gaps"

2. **Area breakdown table**:
   | Area | Score | Criteria passed |
   |---|---|---|
   | 1. Crawlability | X/3 | C1, C3 |
   | 2. Structured data | X/4 | C5, C7 |
   | 3. Content quality | X/2 | C8 |

3. **Per-criterion findings**: for each FAILED criterion, state what was
   checked (with sampling scope), what was missing (with evidence
   source), AND a specific fix. Link to schema.org or Google rich-results
   docs where relevant. For each PASSED criterion, one line with the
   supporting evidence.

4. **Schema hygiene flags** (separate section): surface duplicate /
   malformed JSON-LD blocks, deprecated fields, or conflicting data
   across blocks even if they don't change pass/fail. These often
   matter more than the headline score — a brand with "PASS" on C4 but
   a malformed second Product block emitting garbage may actually
   perform worse in agent retrieval than a brand with "FAIL" but clean
   absence.

5. **Fix priority list** (top 3): ranked by impact on agent
   discoverability. Use conditional effort language.

6. **Disclosure block**: state the sampling scope explicitly:
   "This audit scored {N} PDPs / {M} auxiliary pages via source-level
   curl fetches on {date}. Findings are sample-based unless `--full`
   was specified. It does not audit uniqueness (C10, deferred) or GEO
   (geographic/local retrieval). Schema absence in sampled pages does
   not guarantee absence sitewide — rerun with `--confidence=high` or
   `--full` for broader coverage."

Be specific. "Fix product schema" is useless. "Across the 3 sampled
PDPs, the second JSON-LD block on each page has `brand.@type = 'Cider'`
(should be `'Brand'`) and a mangled product name. Google's Rich Results
parser may pick this malformed block over the clean first block. Fix:
remove the duplicate block emission in the PDP template, or fix
`@type`." is useful.

The merchant running this audit on their own store will pipe the report
into a Jira ticket. Write it so they can.
