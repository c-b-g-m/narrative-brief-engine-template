# Build Log

## 2026-05-03 — Public template release (sanitized + genericized)

Sanitized fork of an internal pipeline. All instance-specific configs, session logs, and competitive intelligence have been removed. This is the canonical public template; private forks hold per-client work.

**Sanitization (removed):**
- Per-instance configs (`config/{slug}.yaml`)
- Session export logs (`docs/sessions/`)
- Internal knowledge base (contained client-specific findings and excluded-account lists)
- MCP bearer tokens (gitignored)
- Generated outputs (`output/`)

**Genericization (refactored from instance-coupled code):**
- `templates/artifact_template.html`: column-3 label is now `{{SOLUTION_LABEL}}`; renamed instance-specific JS variable to `solutions`; replaced hardcoded sender branding (logo alt, footer attribution, footer link) with `{{FOOTER_LOGO_BLOCK}}` and `{{FOOTER_ATTRIBUTION}}` placeholders; brand color set to neutral indigo-purple `#5B21B6` (with matching rgba values throughout)
- `pipeline/stage5_build_artifact.py`: logo file path is now generic `client_logo_b64.txt`; removed hardcoded sender attribution from framing HTML; reads `brand_name`, `brand_url`, `solution_label` from config; computes footer attribution dynamically
- `config/client.yaml`: added `brand_name`, `brand_url`, `solution_label` plus the `known_customers`, `solution_mapping`, `recency_cutoff`, `buying_committee`, `apify` sections
- `docs/artifact-layout-spec.md`: replaced sender-brand language with "configurable brand"; added rebranding instructions

**Included:**
- Pipeline stages 1–5 + helpers
- HTML artifact template
- Config template (`config/client.yaml`)
- `/narrative-brief` Claude Code skill
- LICENSE (MIT), README, SOUL.md, CLAUDE.md
- `docs/artifact-layout-spec.md`

**Note:** Environment variable documentation lives in the README rather than a `.env.local.example` file — the global secrets-guard hook (correctly) treats all `.env*` files as suspect, so the template avoids them.
