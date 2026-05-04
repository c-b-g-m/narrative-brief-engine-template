---
name: narrative-brief
description: Run the narrative intelligence signal brief pipeline for a client prospect. Orchestrates 5 stages from archive mining through HTML artifact generation.
trigger: when the user says "/narrative-brief" or asks to build a narrative intelligence brief
---

# Narrative Brief Pipeline

You are orchestrating the narrative intelligence signal brief pipeline. This produces a professional prospecting artifact that surfaces qualitative hiring signals from executive conversations.

**Engine location:** `~/Library/CloudStorage/OneDrive-Personal/Desktop/ClaudeProjects/narrative-brief-engine/`

## Prerequisites

- Lenny's Podcast MCP tools available (search_content, read_content, read_excerpt)
- Web search available for company enrichment
- PyYAML installed (`pip install pyyaml`)

## Pipeline Flow

### Step 0 — Client Setup

1. Ask for: client name, industry, target buyer persona
2. Ask for: competitor exclusions (companies to filter out of prospect list)
3. Ask for: search angles — what themes should we mine the archive for? These are specific to this client's industry, product positioning, and the story we're building.
4. Create `config/{client-slug}.yaml` with the provided values (copy from client.yaml template)
5. Create `output/{client-slug}/` directory

### Step 1 — Archive Mining

1. Load search angles from client config
2. For each angle, call `search_content` via Lenny MCP
3. For promising results, call `read_content` or `read_excerpt` to get full quotes
4. For each result, extract: exec_name, title, company, quote, inferred hiring need, thematic tags, date
5. Save raw results to `output/{client-slug}/raw_results.json`
6. Run `python3 pipeline/stage1_archive_mine.py {client-slug}` to deduplicate and structure
7. Output: `output/{client-slug}/stage1_archive_signals.json`

### Step 2 — PAUSE: Cluster Proposal

Before enrichment, review the signals and **propose thematic clusters**.

1. Analyze all signals from Stage 1 — look for recurring themes, patterns, and groupings
2. Propose 2-4 clusters, each with: key, title, thesis (one sentence), and matching tags
3. Present the proposed clusters to the user for review
4. Take feedback: user may rename, merge, split, add, or drop clusters
5. Update `config/{client-slug}.yaml` with approved clusters (including tags)

**Do not proceed until clusters are approved.**

### Step 3 — Enrichment

1. For each unique company in the signals, run a web search for: recent funding, valuation, headcount, hiring news, leadership changes, AI/transformation signals
2. Save raw enrichment to `output/{client-slug}/raw_enrichment.json`
3. Run `python3 pipeline/stage2_enrich.py {client-slug}` to score, tier, and cluster-assign
4. Output: `output/{client-slug}/stage2_enriched_prospects.json`

### Step 4 — PAUSE: Prospect Review

Present the enriched prospect list to the user.

1. Show: exec name, company, heat tier, cluster assignment, why now
2. Group by cluster, sorted by heat within each cluster
3. Ask: any prospects to remove? Any heat adjustments? Any cluster reassignments?
4. Cold-tier prospects with quote value but low actionability → flag as "thought leaders" (separate section in the artifact, not mixed into main prospect list)
5. Apply feedback and re-save stage2 JSON

**Do not proceed until prospect list is approved.**

### Step 5 — LinkedIn Prompts

1. Run `python3 pipeline/stage3_linkedin_prompts.py {client-slug}`
2. Output: `output/{client-slug}/stage3_chrome_prompts.md`
3. Tell the user: "Chrome prompts are ready. Open stage3_chrome_prompts.md and run each prompt in the Claude Chrome extension on LinkedIn. Save the combined results as stage4_linkedin_signals.csv in the output/{client-slug}/ folder."

### Step 6 — PAUSE: Wait for LinkedIn Data

**Stop here.** The user must manually run the Chrome extension prompts and save the CSV. Resume when they confirm the CSV is ready.

### Step 7 — LinkedIn Merge

1. Run `python3 pipeline/stage4_merge.py {client-slug}`
2. Review any "LinkedIn Discoveries" (execs found on LinkedIn not in the original prospect list)
3. Ask user: add any discoveries to the prospect list?
4. If yes, add them and re-run merge

### Step 8 — PAUSE: Framing Copy

Before building the artifact, the framing copy must be written. This positions the entire brief.

1. Ask the user to provide or approve: title, subtitle, 2-3 framing paragraphs
2. The framing should connect the client's product to the signals in the brief
3. Update `config/{client-slug}.yaml` with approved framing
4. Also confirm the footer text

**Do not proceed until framing is approved.**

### Step 9 — Build Artifact

1. Run `python3 pipeline/stage5_build_artifact.py {client-slug}`
2. Output: `output/{client-slug}/narrative_intelligence_brief.html`
3. Tell user to open in browser for review
4. Take any final feedback on the HTML artifact

### Step 10 — Deploy (on approval)

1. Ask: "Ready to deploy to Netlify?"
2. On approval, deploy via Netlify Drop or CLI
3. Return the live URL

## Key Rules

- **No fabricated data.** All quotes must come from the Lenny archive. All company data from web search.
- **No hardcoded themes.** Clusters, search angles, and framing are all client-specific.
- **Name-based matching** for LinkedIn merge — match on exec name, verify company. Never substring match.
- **BOM-safe CSV** — always use `encoding='utf-8-sig'` for CSV files.
- **Green = hot, amber = medium, slate = cold.** Never red for positive signals.
- **Thought leaders** (cold-tier with quote value) get a separate section, not mixed into the main prospect cards.
