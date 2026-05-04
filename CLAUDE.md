# CLAUDE.md — narrative-brief-engine-template

## What This Is

A reusable 5-stage Python pipeline template for generating narrative intelligence briefs. Stages: archive mining → enrichment → LinkedIn signal extraction → merge → HTML artifact. Designed to be forked per client engagement.

## Structure

- `pipeline/` — stage scripts (stage1 through stage5)
- `templates/` — HTML output templates
- `config/client.yaml` — config template, copy + customize per client
- `.env.local` — API keys (gitignored)

## Commands

```bash
python3 pipeline/stage1_archive_mine.py --config config/{your-client}.yaml
# ... continue through stages
```

The `/narrative-brief` Claude Code skill (`.claude/commands/narrative-brief.md`) walks the full pipeline interactively.

## Rules

- **Never fabricate data** in any pipeline stage — all enrichment must be sourced
- **API keys in `.env.local`** — never hardcoded, never committed
- **HTML output is the deliverable** — validate it renders before declaring done
- **Per-client configs** live in `config/{client-slug}.yaml`. Don't commit client configs to a public fork.
