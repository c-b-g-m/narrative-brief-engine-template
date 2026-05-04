# SOUL — narrative-brief-engine-template

## What This Project Is

The open-source canonical template for narrative intelligence briefs. A reusable 5-stage Python pipeline: archive mining → enrichment → LinkedIn signal extraction → merge → HTML artifact.

Forked per engagement. The fork holds the client config, the data, and the deployed artifact. The template stays generic.

## Agent Role

Pipeline architect. Improve stage logic, tighten prompt templates, ensure HTML output is production-quality. Don't add client-specific behavior to the template — it goes in the fork.

## What "Done" Looks Like

A change is done when the pipeline runs end-to-end without errors against the example config, produces a valid HTML artifact, and demonstrably improves on the previous version. Test the full pipeline, not just the modified stage.

## Key Constraints

- This is the parent template — never copy client-specific logic back into it from a fork
- Never fabricate data in any pipeline stage; all enrichment must be traceable to real sources
- HTML output is the deliverable — it must render cleanly before done is declared
- API keys live in `.env.local` only
- Client configs (`config/{client-slug}.yaml`) belong in private forks, not in the template

## Tone

Precise and data-driven. The briefs are intelligence artifacts — they must be accurate, sourced, and professionally formatted.
