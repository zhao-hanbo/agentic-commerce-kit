# `/audit-agent-readiness`

Score an ecommerce store against the 9-criterion **Agentic Commerce
Readiness Index**. Works on any storefront; tuned for Shopify.

## What it does

Runs the same audit methodology used in the [Nohi Readiness Index
Edition 1](https://github.com/zhao-hanbo/agentic-commerce-kit#the-rubric)
(Premium DTC Beauty, 50 brands, April 2026). Given one store URL, it:

1. Checks robots.txt for AI-crawler access (C1)
2. Samples 3 product pages from the sitemap and verifies they render
   server-side (C2) and carry complete `Product`/`Review` JSON-LD
   (C4, C5)
3. Confirms sitemap freshness (C3)
4. Checks homepage + auxiliary pages for `FAQPage`/`HowTo` (C6) and
   `Organization` (C7) schema
5. LLM-evaluates 5 PDP titles and descriptions for use-case specificity
   and comparison context (C8, C9)

Output: score / 9, tier label, per-criterion findings with specific
fixes, and a ranked top-3 priority list.

## Install

Copy `command.md` into your project at:

```
.claude/commands/audit-agent-readiness.md
```

Or for user-level install (available across all projects):

```
~/.claude/commands/audit-agent-readiness.md
```

## Run

In Claude Code:

```
/audit-agent-readiness https://www.summerfridays.com
```

Takes ~60-90 seconds. Claude fetches the store, parses JSON-LD, and
returns the structured report.

## Sample output

See [the kit's root README](../../README.md#sample-audit-summer-fridays)
for a full audit of Summer Fridays (5/9 — Early Stage).

## Why this exists

Most "SEO audit" tools score for Google's organic ranking signals.
Agentic commerce (ChatGPT Shopping, Perplexity Buy with Pro, Google
AI Mode, Claude's forthcoming commerce capabilities) uses a **different
retrieval stack**:

- They respect `robots.txt` for their specific bots
- They rely on structured data (JSON-LD) far more than web search did
- They cannot execute JavaScript on arbitrary merchant sites
- They favor pages where title + description + schema together answer
  "does this product match what the shopper is asking for?"

This skill operationalizes what "ready for agents" actually means,
criterion-by-criterion.

## Limits

- C10 (content uniqueness) is deferred — not in this skill
- Non-Shopify platforms: C2-C5 still work, but PDP path detection
  assumes `/products/*` (the standard Shopify pattern). For BigCommerce
  / Adobe Commerce / custom stacks, you may need to adjust the sitemap
  parsing logic
- Rate limit: Claude Code's WebFetch rate-limits; auditing a large
  catalog is fine for a single store but don't loop this over 100s

## License

MIT.
