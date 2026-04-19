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

Run on `https://www.summerfridays.com`, April 2026.

**Score: 5/9 — Early Stage**

| Area | Score | Passed |
|---|---|---|
| 1. Crawlability | 2/3 | C1, C3 |
| 2. Structured data | 2/4 | C5, C7 |
| 3. Content quality | 1/2 | C8 |

**What works:**
- ✅ **C1 Crawler access** — robots.txt explicitly allows all 8 tested AI
  bots (GPTBot, PerplexityBot, ClaudeBot, Google-Extended, Amazonbot,
  CCBot, FacebookBot). Nothing blocked.
- ✅ **C3 Sitemap freshness** — 110 URLs with `<lastmod>` within the past
  90 days. Sitemap actively maintained.
- ✅ **C5 Review schema** — all 3 sampled PDPs ship valid
  `AggregateRating` JSON-LD with real review counts and ratings.
- ✅ **C7 Organization schema** — homepage has complete `Organization`
  JSON-LD with 5 `sameAs` social profiles.
- ✅ **C8 PDP titles** — 4 of 5 sampled titles include specific use
  cases ("Cloud Dew Gel Cream **Moisturizer**", "**Tatyana's** Lip
  Combo").

**What's missing:**
- ❌ **C2 PDP SSR** — 1 of 3 sampled PDPs
  (`/products/mini-cloud-dew-gel-cream`) doesn't include the product
  title in raw HTML. Price and description are present, but the
  agent won't confidently associate them with the right product.
  **Fix**: audit the product-template Liquid for that variant and
  ensure `{{ product.title }}` renders above the fold, not lazy-loaded.
- ❌ **C4 Product schema** — 1 of 3 PDPs
  (`/products/softline-lip-liner-sugar`) is missing `Product` JSON-LD
  entirely. The other two have complete schema with identifiers.
  **Fix**: this PDP likely uses a newer template variant that dropped
  the schema block. Re-apply the theme's product schema snippet. See
  [Shopify's docs on product-page structured data](https://shopify.dev/docs/storefronts/themes/seo/product-pages).
- ❌ **C6 FAQ / HowTo schema** — no `FAQPage` or `HowTo` JSON-LD
  detected on homepage, product pages, or about/how-to-use pages.
  Summer Fridays publishes rich how-to content; it's just not marked
  up.
  **Fix**: add `FAQPage` JSON-LD to the "How to use" section on each
  PDP, and `HowTo` JSON-LD to any routine / tutorial posts. This is
  the highest-leverage missing schema for skincare, because ChatGPT
  queries like "how do I use a jet lag mask" match HowTo schema
  directly.
- ❌ **C9 PDP descriptions** — 0 of 5 sampled product descriptions
  cover 3+ of: target skin type, ingredient rationale, comparison to
  similar products, sizing reasoning, counter-indications. The copy
  is on-brand but agent-hostile.
  **Fix**: expand each PDP with a "Who it's for" block (skin type /
  concern), a "How it compares" block (vs. your other SKUs or the
  category norm), and a "What it isn't" block (counter-indications).
  This is the single biggest lever on the 9-point scale because C9
  touches every product.

**Priority top 3 (biggest leverage first):**

1. **Add C9 context blocks to every PDP description.** Expands
   agent-answerability across the entire catalog. Estimated effort:
   1-2 weeks with copywriter support.
2. **Fix the one PDP missing `Product` JSON-LD** (C4). 15-minute theme
   fix. Brings C4 to full 3/3.
3. **Add `FAQPage` + `HowTo` schema** (C6). Maps onto the "how do I
   use X" query surface where Summer Fridays already has strong
   organic content — just needs the markup.

Shipping 1-3 would take Summer Fridays from 5/9 (Early Stage) to 8/9
(Agent-Ready) in one quarter.

*Disclosure: this audit scores the 9 Edition-1 criteria. It does not
audit uniqueness (C10, deferred) or geographic / local retrieval (GEO,
future edition).*

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
