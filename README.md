# agentic-commerce-kit

A Claude Code skill that audits an ecommerce store for **agentic commerce
readiness** — whether ChatGPT, Claude, Perplexity, and Gemini's commerce
agents can find, parse, and recommend its products.

```
/audit-agentic-commerce https://your-store.com
```

Output: score / 9, per-criterion findings, ranked fix list.

---

## Why

Agentic commerce already routes billions of shopping queries. The agents
that do the routing (ChatGPT Shopping, Perplexity Buy with Pro, Google
AI Mode) use a different stack than classic SEO:

- They identify themselves via specific user agents (`GPTBot`,
  `PerplexityBot`, `ClaudeBot`, etc.) that a merchant's `robots.txt`
  might silently block
- They rely heavily on structured data — `Product`, `AggregateRating`,
  `FAQPage`, `Organization` JSON-LD
- They cannot execute arbitrary JavaScript on a merchant's PDPs
- They favor pages where title, description, and schema together
  answer "does this product match what the shopper is asking for?"

The rubric this kit uses was developed for the [Nohi Agentic Commerce
Readiness Index Edition 1](https://nohi.ai/research/agentic-readiness-index-edition-1)
(50 Premium DTC Beauty brands, April 2026). **Median score: 3/9. Zero
brands scored 7+.** This tool lets you audit yours.

## Install

```bash
# Clone and place the skill in your project:
git clone https://github.com/zhao-hanbo/agentic-commerce-kit.git
cp agentic-commerce-kit/skills/audit-agentic-commerce/command.md \
   ./.claude/commands/audit-agentic-commerce.md

# Or install globally (user scope):
mkdir -p ~/.claude/commands/
cp agentic-commerce-kit/skills/audit-agentic-commerce/command.md \
   ~/.claude/commands/audit-agentic-commerce.md
```

Requires [Claude Code](https://claude.com/product/claude-code). No
other dependencies.

## Use

```
/audit-agentic-commerce https://www.summerfridays.com
```

Takes ~60-90 seconds.

## The rubric

Nine criteria, each binary (0 or 1). Maximum 9.

| # | Criterion | Area |
|---|---|---|
| C1 | AI-crawler access in robots.txt | Crawlability |
| C2 | PDP server-side renders (no JS required) | Crawlability |
| C3 | Sitemap exists, fresh (<90d), lists products | Crawlability |
| C4 | `Product` JSON-LD on PDPs (name, image, brand, offers, identifier) | Structured data |
| C5 | `AggregateRating` or `Review` JSON-LD with real counts | Structured data |
| C6 | `FAQPage` or `HowTo` JSON-LD on at least one page | Structured data |
| C7 | `Organization` JSON-LD on homepage (with `sameAs` socials) | Structured data |
| C8 | PDP titles include use case or differentiator | Content quality |
| C9 | PDP descriptions answer ≥3 of: skin type, comparisons, ingredient rationale, sizing, usage, counter-indications | Content quality |

**Tier labels:**
- 8-9 → **Agent-Ready**
- 6-7 → **Partially Ready**
- 3-5 → **Early Stage**
- 0-2 → **Not Ready**

Full methodology: [Nohi Readiness Index — Edition 1 Methodology](https://nohi.ai/research/agentic-readiness-index-edition-1/methodology).

## Sample audit: Summer Fridays

Run on `https://www.summerfridays.com`, April 2026. Default 3-PDP
sample. Schema checks via source-level `curl` fetch of raw HTML.

**Score: 5/9 — Strong Foundations, Variable Schema Coverage**

| Area | Score | Criteria passed |
|---|---|---|
| 1. Crawlability | 3/3 | C1, C2, C3 |
| 2. Structured data | 1/4 | C7 |
| 3. Content quality | 1/2 | C8 |

**What works** (source-level verified):

- ✅ **C1 Crawler access** — `robots.txt` allows all 8 tested AI bots
  (GPTBot, PerplexityBot, ClaudeBot, `anthropic-ai`, Google-Extended,
  Amazonbot, CCBot, FacebookBot). No matching `Disallow` rules.
- ✅ **C2 PDP server-side render** — across the 3 sampled PDPs, raw
  HTML contains product title, price, and description without requiring
  JS.
- ✅ **C3 Sitemap freshness** — valid sitemap index with `<lastmod>`
  within the past 90 days.
- ✅ **C7 Organization schema** — homepage ships a complete
  `Organization` JSON-LD block: `name="Summer Fridays"`, `url`, and
  `sameAs` array with 5 social-profile URLs.
- ✅ **C8 PDP titles** — across the 5 sampled titles, 4+ include
  specific use cases or differentiators ("Jet Lag Mask", "Cloud Dew
  Gel Cream Moisturizer Deluxe Sample").

**What's missing** (source-level verified):

- ❌ **C4 Product schema** — across the 3 sampled PDPs, 1 of 3
  (`/products/cloud-dew`) has no `Product` JSON-LD at all — only
  `Organization` schema ships on that page. The other PDPs sampled
  (e.g. `/products/jet-lag-mask`) ship a valid `Product` block with
  `name`, `image`, `brand`, `offers.price`, `offers.availability`,
  `sku`, and `gtin`. The finding is variance between templates, not
  absence everywhere.
  **Fix**: audit the PDP Liquid templates to identify which variant
  ships without Product schema and restore the schema snippet. Verify
  across a broader sample with `--confidence=high`.
- ❌ **C5 AggregateRating schema** — across the 3 sampled PDPs,
  `aggregateRating` presence varies. On `/products/jet-lag-mask` it
  appears in a separate Product block (ratingValue 4.5, reviewCount
  2771) rather than inside the main Product block — machine parsers
  may or may not associate them. On `/products/cloud-dew` no
  aggregateRating is emitted.
  **Fix**: consolidate the split Product blocks so ratings live on the
  same `Product` as the product fields, and ensure aggregateRating
  emits on every PDP where the review count is non-zero.
- ❌ **C6 FAQPage / HowTo schema** — `/pages/faq` was fetched and
  contains only `Organization` schema, no `FAQPage`. Homepage and
  other auxiliary pages also lack FAQ/HowTo markup.
  **Fix**: Summer Fridays publishes extensive "How to use" content
  per product — wrap this content in `HowTo` JSON-LD on PDPs and
  `FAQPage` JSON-LD on `/pages/faq`. See
  [schema.org/HowTo](https://schema.org/HowTo).
- ❌ **C9 PDP descriptions** (evaluated on visible-text via WebFetch)
  — across the 5 sampled PDPs, descriptions are largely marketing-led
  with limited buyer-context cues (comparison to adjacent SKUs, skin-
  type rationale, counter-indications). This finding is based on
  rendered-response text; the descriptions may include these cues
  below the fold or in expandable sections that weren't fetched.
  **Fix**: expand PDP descriptions with explicit buyer-context blocks
  (who it's for / how it compares / when to use / what it isn't).

**Schema hygiene flags** (present but malformed / worth fixing):

- Split Product blocks on `/products/jet-lag-mask` — one block holds
  product fields (name, sku, gtin), a separate block holds
  aggregateRating. Google's Rich Results parser may not associate the
  rating with the product. Recommended: consolidate into a single
  block.

**Priority top 3** (biggest leverage first):

1. **Restore Product + AggregateRating schema on every PDP.**
   Consolidating the split blocks and adding Product schema to the
   PDPs currently missing it would move C4 and C5 toward PASS across
   the sample. Lightweight if the Liquid template already has the
   fields; heavier if the missing-schema PDPs use a different template
   variant.
2. **Add `FAQPage` / `HowTo` schema** (C6). Summer Fridays has strong
   how-to content on PDPs; the markup layer is the gap. Effort depends
   on whether how-to content is structured in a reusable page section.
3. **Expand PDP descriptions with buyer-context cues** (C9). The
   highest-leverage change because it affects every product, but also
   the only one that requires editorial rather than template work.

Implementing 1-3 would move this brand materially upward on the
framework. Final score depends on implementation quality and broader
content improvements.

*Disclosure: this audit scored 3 PDPs (via source-level `curl` fetches
on 2026-04-19), 2 auxiliary pages (homepage, `/pages/faq`), plus
`robots.txt` and `sitemap.xml`. Findings are sample-based. It does
not audit uniqueness (C10, deferred) or GEO (geographic/local
retrieval). Schema variance in sampled PDPs does not guarantee absence
sitewide — rerun with `--confidence=high` or `--full` for broader
coverage.*

## Related work

- **[Nohi Readiness Index — Edition 1](https://nohi.ai/research/agentic-readiness-index-edition-1)**
  — full 50-brand scoring + notable findings.
- **[Finland Agent Test](https://nohi.ai/research/finland-agent-test)**
  — the qualitative counterpart: what ChatGPT actually returns when
  you ask it to shop in an underserved market.
- **[Nohi blog](https://nohi.ai/blog)** — ongoing research on
  agentic commerce infrastructure.

## Further reading on the agentic commerce stack

The protocols and surfaces this audit targets:

- [OpenAI Agentic Commerce Protocol (ACP)](https://openai.com/blog/acp)
- [Google Agent Payments Protocol (AP2)](https://github.com/google-agentic-commerce/AP2)
- [A2A — Agent-to-Agent protocol](https://github.com/a2aproject/A2A)
- [Stripe Agent Toolkit](https://github.com/stripe/agent-toolkit)
- [Shopify Roast — Shopify's agent workflow framework](https://github.com/Shopify/roast)
- [MCP specification](https://github.com/modelcontextprotocol/specification)

## Contributing

This is v1: one skill, one flagship use case. Planned additions
(depending on community feedback):

- `/fix-product-schema` — walks the user through applying C4 fixes in
  their Shopify theme
- `/generate-faq-jsonld` — takes a store's existing FAQ page and
  produces `FAQPage` JSON-LD ready to paste
- Cursor and Cline rule variants of the readiness audit

File an issue with what you'd find useful. No CONTRIBUTING.md yet —
reach out directly.

## License

MIT. See [LICENSE](./LICENSE).

## Author

Built by [Zhao Hanbo](https://www.linkedin.com/in/hanbozhao) while
building [Nohi](https://nohi.ai) — the marketplace connecting DTC
merchants to agentic commerce surfaces.
