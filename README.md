# Narrative Brief Engine

Reusable pipeline for generating narrative intelligence signal briefs — prospecting artifacts that surface qualitative hiring signals from executive conversations, enrich with LinkedIn activity, assemble buying committees, and produce a polished HTML brief.

## Quick Start

```
/narrative-brief
```

The Claude Code skill walks you through the full pipeline interactively.

## Architecture

```
narrative-brief-engine/
├── pipeline/
│   ├── stage1_archive_mine.py       # Query Lenny MCP, extract signals + episode titles
│   ├── stage2_enrich.py             # Web search enrichment, tier scoring, customer exclusion
│   ├── stage2b_buying_committee.py  # Assemble buying committees (CEO/CFO/CHRO/Signal Source)
│   ├── stage3_apify_linkedin.py     # Automated LinkedIn research via Apify (no cookies)
│   ├── stage3_linkedin_prompts.py   # Manual fallback: Chrome extension prompts
│   ├── stage4_merge.py              # Merge LinkedIn signals into buying committees
│   ├── stage5_build_artifact.py     # Generate HTML from template + data + logos
│   └── utils.py                     # Shared helpers (JSON I/O, BOM-safe CSV, name/company matching)
├── templates/
│   ├── artifact_template.html       # Glassmorphism HTML/CSS/JS with data placeholders
│   └── chrome_prompt_template.md    # Parameterized Chrome extension prompt (manual fallback)
├── config/
│   └── client.yaml                  # Config template — copy per client
├── output/
│   └── {client-slug}/               # Generated files per client (gitignored)
├── docs/
│   ├── artifact-layout-spec.md      # Visual spec for the HTML artifact
│   └── build-log.md                 # What was built, what broke, tech debt
├── .claude/commands/
│   └── narrative-brief.md           # Claude Code skill — interactive pipeline driver
├── LICENSE                          # MIT
└── README.md
```

## Pipeline Stages

| Stage | What | Automated? | Human? |
|-------|------|------------|--------|
| 0 | Client setup | Config template | Provides client details, search angles |
| 1 | Archive mining | Python + Lenny MCP | — |
| **PAUSE** | Cluster proposal | Skill proposes | Reviews, approves |
| 2 | Company enrichment | Python + web search | — |
| 2b | Buying committee | Python + web search | Reviews committee, fills gaps |
| **PAUSE** | Prospect review | — | Adjusts tiers, clusters, exclusions |
| 3 | LinkedIn research | **Apify** (automated) | Reviews resolved profiles |
| 4 | LinkedIn merge | Python | Reviews discoveries |
| **PAUSE** | Framing copy | — | Writes/approves header copy |
| 5 | HTML artifact build | Python from template | Reviews in browser |
| Deploy | Netlify | Manual | Approves |

## Config

Each client gets a YAML config file (copy `config/client.yaml` and customize). All themes, clusters, search angles, solution mappings, and framing are client-specific — nothing is hardcoded.

```yaml
# CLIENT — the recipient of the brief
client_name: "Acme Corp"
industry: "B2B SaaS"
target_buyer: "Jane Doe, CMO"
competitors: ["CompetitorA", "CompetitorB"]
known_customers: ["CustomerA", "CustomerB"]  # Auto-excluded

# YOUR FIRM — used in hero header + footer attribution
brand_name: "Your Firm"
brand_url: "https://yourfirm.com"
solution_label: "Your Solution"   # Column 3 header on signal panel

# DISCOVERY
search_angles:
  - "hiring for cross-functional judgment"
  - "AI transformation in B2B SaaS"

# CLUSTERS (populated after Stage 1 review)
clusters: {}
solution_mapping:
  cluster_key: "Product Name + description"

# FRAMING (written after clusters established)
framing: {}

recency_cutoff: "2025-10-01"
buying_committee:
  roles: [ceo, cfo, chro, signal_source]
  company_aliases: {}
apify:
  posts_actor: "harvestapi/linkedin-profile-posts"
  max_posts_per_profile: 10
```

## Branding

The default theme uses an indigo-purple accent (`#5B21B6`). To rebrand, change three CSS variables in `templates/artifact_template.html` and find-replace the `rgba(91,33,182,...)` instances with your brand RGB. See `docs/artifact-layout-spec.md` for the full color system.

## Design

The HTML artifact uses a glassmorphism + soft UI design language:
- Light mode with frosted glass panels
- Per-company account cards with "WHY THIS ACCOUNT" signal panel
- Narrative chain: Topic Signal → Why Now → Client Solution
- Buying committee grid with role badges (CEO/CFO/CHRO/Signal)
- LinkedIn posts: max 2/exec, one-sentence summary + date + blue hyperlink
- Sticky filter bar, summary stats, expand chevrons

Full visual spec: `docs/artifact-layout-spec.md`

## Dependencies

- Python 3.9+
- PyYAML (`pip install pyyaml`)
- requests (`pip install requests`) — for Apify integration
- Lenny's Podcast MCP (for Stage 1)
- Apify account + API token (for Stage 3)
- Web search access (for Stage 2 enrichment + LinkedIn URL resolution)

## Environment Variables

Create a `.env.local` (gitignored) at the repo root with the following:

```
# Apify (Stage 3 — LinkedIn research)
# Get a token at https://console.apify.com/account/integrations
APIFY_API_TOKEN=

# Web search provider for Stage 2 enrichment
# (e.g., Brave Search API, or another provider you wire into stage2_enrich.py)
BRAVE_SEARCH_API_KEY=
```

The Lenny's Podcast MCP server is configured separately via a `.mcp.json` file (also gitignored) with a personal bearer token from https://www.lennysdata.com.

## Future Improvements

- [ ] `stage2c_recency_filter.py` — automated recency validation against configurable cutoff
- [ ] `stage2d_lookalikes.py` — automated lookalike account sourcing from web research
- [ ] `stage3_resolve_profiles.py` — dedicated LinkedIn URL resolution step
- [ ] Batch committee lookup via org chart API (replace 18+ individual web searches)
- [ ] Print/PDF stylesheet (`@media print`)
