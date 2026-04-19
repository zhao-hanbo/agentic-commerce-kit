---
description: Score an ecommerce store against the 9-criterion Agentic Commerce Readiness Index
argument-hint: <store-url>
---

You are running the **Agentic Commerce Readiness Index** audit on the store at
`$ARGUMENTS`.

The question this audit answers: **When ChatGPT, Claude, Perplexity, or
Gemini's commerce agents decide which brand to recommend for a user's query,
does this store show up with enough structured information to be picked?**

The 9 criteria are organized into 3 areas. Each criterion scores 0 or 1.
Maximum total: 9. Audit the store systematically — do not skip steps.

## Area 1 — Crawlability & access (3 points)

### C1. AI crawler access
- Fetch `{root}/robots.txt` via WebFetch.
- **PASS** if robots.txt explicitly allows at least 4 of: `GPTBot`,
  `PerplexityBot`, `ClaudeBot`, `anthropic-ai` (legacy name), `Google-Extended`,
  `Amazonbot`, `CCBot`, `FacebookBot`. "Allowed" means not listed under a
  matching `Disallow: /` block for that user agent.
- **FAIL** if 4+ of these are blocked, OR if robots.txt is missing.

### C2. PDP server-side render
- Fetch `{root}/sitemap.xml` and pick 3 product detail page URLs (paths
  containing `/products/` for Shopify, or product-like segments for others).
- WebFetch each PDP. For each, ask: does the raw HTML contain (a) a
  product title, (b) a price, (c) a description — **without** requiring JS
  execution? WebFetch gives you rendered HTML, so look for product data
  in the actual returned content, not in a skeleton loader.
- **PASS** if 3/3 PDPs include all three elements.
- **FAIL** if any PDP requires JS (empty shell, placeholder text).

### C3. Sitemap freshness
- Parse `{root}/sitemap.xml` (follow sitemap index if present).
- **PASS** if sitemap is valid XML, contains product URLs, AND has at least
  one `<lastmod>` timestamp within the past 90 days.
- **FAIL** if sitemap missing, invalid, or all timestamps stale.

## Area 2 — Structured data (4 points)

Parse `<script type="application/ld+json">` blocks on each page fetched
below. Handle both single-object and `@graph` arrays.

### C4. Product schema on PDPs
- Same 3 PDPs from C2.
- **PASS** if 3/3 have valid `schema.org/Product` JSON-LD containing: `name`,
  `image`, `brand`, `offers` (with `price` AND `availability`), AND at least
  one of `gtin`, `mpn`, `sku`.
- **FAIL** if missing any required field on any of the 3.

### C5. Review / AggregateRating schema
- Same 3 PDPs.
- **PASS** if 3/3 have `AggregateRating` (or `Review`) with a `ratingValue`
  AND `reviewCount > 0` (real counts, not placeholders).
- **FAIL** if any PDP lacks actual review data.

### C6. FAQPage / HowTo schema
- Fetch the homepage plus any discoverable "FAQ", "How to use", "About" pages.
- **PASS** if at least one page emits valid `FAQPage` or `HowTo` JSON-LD.
- **FAIL** if none.

### C7. Organization schema
- Fetch the homepage.
- **PASS** if valid `Organization` JSON-LD with at minimum: `name`, `url`,
  AND `sameAs` array containing at least 2 social-profile URLs.
- **FAIL** if missing or incomplete.

## Area 3 — Content quality (2 points)

### C8. PDP titles include use case / differentiator
- Sample up to 5 PDP titles from the sitemap.
- For each title, ask: does it include a specific use case, target audience,
  or differentiator beyond "{brand} {product name}"?
  - PASS example: "Retinol Alternative Night Serum for Sensitive Skin"
  - FAIL example: "Summer Fridays Jet Lag Mask"
- **PASS** if 4+ of 5 titles pass.

### C9. Descriptions answer comparison / context questions
- Same 5 PDPs, full description text.
- For each, ask: does the description explicitly address at least 3 of:
  target skin/hair type, comparison to similar products, ingredient
  rationale, sizing/volume reasoning, when/how to use, what it is NOT
  meant for?
- **PASS** if 4+ of 5 descriptions pass.

---

## Output format

Produce a structured report with:

1. **Score**: `{total}/9` with tier label:
   - 8-9 → **Agent-Ready**
   - 6-7 → **Partially Ready**
   - 3-5 → **Early Stage**
   - 0-2 → **Not Ready**

2. **Area breakdown table**:
   | Area | Score | Criteria passed |
   |---|---|---|
   | 1. Crawlability | X/3 | C1, C3 |
   | 2. Structured data | X/4 | C5, C7 |
   | 3. Content quality | X/2 | C8 |

3. **Per-criterion findings**: for each FAILED criterion, state what was
   checked, what was missing, AND the specific fix the brand should ship.
   Link to schema.org docs or Shopify docs for actionable remediation.
   For each PASSED criterion, one line acknowledging the strength.

4. **Fix priority list** (top 3): ranked by impact on agent discoverability.
   Order = biggest-win-first, not criterion-order.

5. **Disclosure**: "This audit scores the 9 Edition-1 criteria from the
   Nohi Agentic Commerce Readiness Index. It does not audit uniqueness
   (C10, deferred) or GEO (geographic/local retrieval)."

Be specific. "Fix product schema" is useless. "Add `gtin` or `sku` to the
`Product` JSON-LD on /products/* — currently missing on all 3 sampled PDPs
— follow [Shopify Liquid example](https://shopify.dev/docs/storefronts/
themes/seo/product-pages#add-product-schema)" is useful.

The merchant running this audit on their own store will pipe the report
into a Jira ticket. Write it so they can.
