# Contributing

This template is forked per engagement. Most contributions land in your
private fork (with client-specific config, data, and deployed artifacts);
the public template stays generic.

## What belongs in the public template

- Pipeline stage improvements (better prompts, error handling, schema cleanup)
- HTML template / design system improvements
- New configurable options (don't hardcode anything client-specific)
- Documentation, examples, dependency hygiene

## What does NOT belong here

- Client-specific configs (`config/{slug}.yaml`)
- Generated outputs or research data
- Session logs that mention specific clients, names, or accounts
- Hardcoded brand colors, logos, or footer attributions
- API keys, bearer tokens, or any secret material

## Local setup

```bash
git clone https://github.com/c-b-g-m/narrative-brief-engine-template.git
cd narrative-brief-engine-template
python3 -m venv .venv && source .venv/bin/activate
pip install pyyaml requests
# Add ANTHROPIC_API_KEY, APIFY_API_TOKEN, etc. to .env.local (gitignored)
```

## Sending a PR

1. Fork the repo, create a feature branch
2. Run `python -m py_compile pipeline/*.py` before pushing — CI runs the same check
3. Update `docs/build-log.md` with what changed and why
4. Confirm no client identifiers slipped in: `grep -rEi "<your-client>" .`
5. Open the PR with a focused description (what, why, how to verify)

## Default brand

The HTML template ships with a neutral indigo-purple accent (`#5B21B6`).
To rebrand for your fork: change `--brand`, `--brand-light`, `--brand-dark`
in `templates/artifact_template.html` and find-replace the `rgba(91,33,182,...)`
instances. See `docs/artifact-layout-spec.md` Color System section.

## Questions

File an issue. Be specific about what's not working — paste the command
you ran and the output, including stack traces.
