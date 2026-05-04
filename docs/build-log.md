# Build Log

## 2026-05-03 — Public template release (sanitized + genericized)

Sanitized fork of the internal narrative-brief-engine. All client configs, session logs, and instance-specific data removed. This is the canonical public template; private forks hold per-client work.

**Sanitization (removed):**
- Client configs (`config/{slug}.yaml`)
- Session export logs
- `docs/knowledge-base.md` (contained client-specific findings and competitor lists)
- `.mcp.json` bearer tokens (gitignored)
- Generated outputs (`output/`)

**Genericization (refactored from client-coupled code):**
- `templates/artifact_template.html`: replaced "Visier Solution" label with `{{SOLUTION_LABEL}}` placeholder; renamed `visierSolutions` JS variable to `solutions`; replaced hardcoded Cazimi Marketing branding (logo alt, footer attribution, link to cazimimarketing.com) with `{{FOOTER_LOGO_BLOCK}}` and `{{FOOTER_ATTRIBUTION}}` placeholders; changed brand color from Cazimi purple `#b63ab4` to neutral indigo-purple `#5B21B6` (and rgba equivalents)
- `pipeline/stage5_build_artifact.py`: changed hardcoded `visier_logo_b64.txt` path to generic `client_logo_b64.txt`; removed Cazimi-specific framing HTML hardcoding; reads brand name/url/solution_label from config; computes footer attribution dynamically
- `config/client.yaml`: added `brand_name`, `brand_url`, `solution_label` fields plus `known_customers`, `solution_mapping`, `recency_cutoff`, `buying_committee`, `apify` sections that were missing from the template
- `docs/artifact-layout-spec.md`: replaced Cazimi-specific design language description with configurable-brand framing; removed Visier-specific examples; added rebranding instructions

**Included:**
- Pipeline stages 1–5 + helpers
- HTML artifact template (genericized)
- Config template (`config/client.yaml`)
- `/narrative-brief` Claude Code skill
- LICENSE (MIT), README, SOUL.md, CLAUDE.md
- `docs/artifact-layout-spec.md`

**Note:** Environment variable documentation is in the README rather than a `.env.local.example` file — the global secrets-guard hook (correctly) treats all `.env*` files as suspect, so the template avoids them entirely.

