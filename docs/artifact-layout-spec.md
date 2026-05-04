# Narrative Intelligence Brief — Artifact Layout Spec

## Design Language

**Glassmorphism + Soft UI with a configurable brand accent.**

- Light mode with subtle radial gradients on background
- Frosted glass panels (`backdrop-filter: blur`, translucent white surfaces)
- Soft shadows, generous white space, Inter font (Google Fonts)
- Single brand accent color drives borders, headers, badges, attribution (default indigo-purple `#5B21B6`)
- No dark mode — these artifacts are CMO-facing prospecting assets and read better in light

## Overall Structure

1. **Hero Header** (full-width, outside content wrap)
   - Brand logo + name (hyperlinked to your URL) — top left
   - "Prepared for" block — top right: recipient name, title, company name + company logo
   - Title (2.2rem, bold)
   - Subtitle (1rem, mid-tone)
   - Framing paragraphs (0.85rem, dim)
   - Brand accent line (48px wide, 3px tall)

2. **Filters** (sticky, near-opaque frosted glass bar, two rows)
   - Row 1: Heat — All / Hot / Medium
   - Row 2: Signal — All / [cluster names with account counts]
   - Background: `rgba(248,246,251,0.97)` with `blur(24px)` and drop shadow
   - Must not allow content bleed-through when scrolling

3. **Summary Stats Bar** — Single line of metrics: accounts researched, hot count, medium count, buying committee members, LinkedIn activity count. Bold numbers, dim labels, dot separators.

4. **Signal Groups** — Sections grouped by cluster
   - Header: cluster title + account count in parentheses (e.g., "Companies Restructuring Without Data (6)")
   - Thesis text spans full content width (no max-width cap)

5. **Account Cards** — Per-company, glassmorphism panels

6. **Footer** — CTA question + brand attribution link + fine print

## Account Card Layout

### Card Header (clickable to expand)
- Company name (1.15rem, bold)
- Industry + Stage (dim)
- Heat badge pill (top-right: "HOT" green / "MEDIUM" amber)

### Signal Panel — "WHY THIS ACCOUNT"

The centerpiece of each card. Its own frosted sub-panel with brand-accent tint, showing the narrative chain of why this account was surfaced.

- **Floating label**: "WHY THIS ACCOUNT" positioned on the top border of the panel (absolute, negative top offset, background matches page `--bg`)
- **Top margin**: 12px minimum to prevent overlap with account meta text above
- **Background**: `linear-gradient(135deg, rgba(91,33,182,0.06), rgba(108,124,255,0.04))` (uses brand RGB)
- **Border**: `1px solid rgba(91,33,182,0.15)` with `border-radius: 10px`
- **3-column layout** with arrow connectors (→) between columns

| Column | Label Style | Content |
|---|---|---|
| Topic Signal | `TOPIC SIGNAL` — 0.78rem, uppercase, brand-dark, bold 700, brand-accent glowing dot before label | Quote (~140 chars), exec name attribution, source citation in brand color |
| → arrow | 1.4rem, brand at 30% opacity, centered vertically below label | |
| Why Now | `WHY NOW` — same label style | Company-level urgency signal |
| → arrow | same | |
| **{Solution Label}** | Configurable label (e.g., "Acme Solution", "How We Help") — same label style | Mapped product/solution per cluster |

On mobile (<700px): arrows hide, columns stack vertically.

### Buying Committee Grid

- Label: `BUYING COMMITTEE` (uppercase, dim, 0.68rem)
- Background: `rgba(248,246,251,0.4)` — slightly tinted behind committee
- Grid: `auto-fill, minmax(230px, 1fr)`, 10px gap
- Each exec card: white glass (`rgba(255,255,255,0.6)`), subtle border, soft shadow, 14px padding

Exec card contents:
- **Role badge** — colored pill: CEO (purple `#6d28d9`), CFO (amber `#b45309`), CHRO (teal `#0e7490`), Signal (green `#16a34a`). Dual-role: "CEO + Signal"
- **LI indicator** — "LI" in link-blue, top-right, only if LinkedIn data exists
- **Name** (0.84rem, bold)
- **Title** (0.72rem, dim)
- **Signal source quote** (italic, mid-tone, max 2 lines with clamp) — only on signal sources
- **Source attribution** (0.66rem, brand color) — only on signal sources
- **LinkedIn posts** (max 2 per exec):
  - Summary: one sentence, 0.73rem, mid-tone
  - Meta line: `YYYY-MM-DD · LinkedIn` where "LinkedIn" is a **blue hyperlink** (`#4f46e5`)
  - Separated from content above by thin `border-top`

### Expand Chevron + Detail

- Small downward triangle chevron between committee and detail section
- Rotates 180deg when card is open
- Subtle opacity (0.4 default, 0.7 on hover/open)
- Expandable detail contains: Change Signal + Hiring Signal (full text)

## Visual Rules

- **Hyperlinks are always blue** (`--link: #4f46e5`), never green
- **LinkedIn posts max 2 per exec** — most recent only
- **Post summaries are one sentence** — first sentence break or ~80 char truncation
- **"LinkedIn" is the only hyperlinked text** on post entries
- **No raw timestamps** — dates as `YYYY-MM-DD`
- **No wall of text** — clear hierarchy through font size, weight, color, and spacing
- **Sticky filter bar must be near-opaque** (`0.97` alpha + `blur(24px)` + drop shadow)
- **Signal group thesis text spans full width** — no max-width constraint

## Color System

| Token | Value | Usage |
|---|---|---|
| `--bg` | `#f8f6fb` | Page background |
| `--surface` | `rgba(255,255,255,0.6)` | Card glass panels |
| `--surface-hover` | `rgba(255,255,255,0.8)` | Card hover state |
| `--surface2` | `rgba(255,255,255,0.45)` | Nested panels |
| `--border` | `rgba(91,33,182,0.12)` | Brand-tinted borders |
| `--border-subtle` | `rgba(0,0,0,0.06)` | Neutral subtle borders |
| `--text` | `#1a1225` | Primary text |
| `--text-mid` | `#4a3d5c` | Secondary text |
| `--text-dim` | `#8b7fa0` | Tertiary/label text |
| `--brand` | `#5B21B6` | Brand primary (configurable — change this and the related rgba values to rebrand) |
| `--brand-light` | `#7C3AED` | Brand light variant |
| `--brand-dark` | `#4C1D95` | Brand dark variant (signal labels) |
| `--hot` | `#16a34a` | Hot badge |
| `--med` | `#d97706` | Medium badge |
| `--link` | `#4f46e5` | All hyperlinks (indigo-blue) |
| `--ceo` | `#6d28d9` | CEO badge (violet) |
| `--cfo` | `#b45309` | CFO badge (amber) |
| `--chro` | `#0e7490` | CHRO badge (teal) |
| `--signal` | `#16a34a` | Signal badge (green) |

**Rebranding:** to swap the accent color, change `--brand`, `--brand-light`, `--brand-dark` and find-replace the `rgba(91,33,182,...)` instances throughout the template with your brand RGB.

## Data Flow

```
stage1_archive_signals.json (per-exec, with episode_title + date)
  → stage2_enriched_prospects.json (per-exec, with web enrichment)
    → stage2b_buying_committees.json (per-company, nested executives)
      → stage4_merge (LinkedIn posts merged as structured_posts: [{summary, date, url}])
        → stage5_build_artifact (HTML generation with logo injection)
```

## Template Placeholders

| Placeholder | Source |
|---|---|
| `{{FRAMING}}` | Built by `build_framing_html()` from config framing + target_buyer |
| `{{CLUSTERS_JS}}` | JSON from config clusters |
| `{{PROSPECTS_JS}}` | JSON array of company card objects |
| `{{FILTER_BUTTONS}}` | HTML buttons from config cluster keys |
| `{{SOLUTIONS_JS}}` | JSON object mapping cluster → solution string |
| `{{SOLUTION_LABEL}}` | Column 3 header label from config (e.g., "Acme Solution"). Default: "Solution" |
| `{{LOGO_SRC}}` | Brand logo base64 from `output/{slug}/logo_b64.txt` |
| `{{CLIENT_LOGO_SRC}}` | Recipient/client logo base64 from `output/{slug}/client_logo_b64.txt` |
| `{{CLIENT_NAME}}` | From config `client_name` |
| `{{BRAND_NAME}}` | From config `brand_name` (your firm name; defaults to `client_name`) |
| `{{BRAND_URL}}` | From config `brand_url` (your firm URL; optional) |
| `{{FOOTER_TEXT}}` | From config `footer` |

## Key Schema Fields for Rendering

**Company level:** `co`, `ind`, `stg`, `h` (heat), `c` (cluster), `why`, `chg`, `hire`, `execs` (array)

**Exec level:** `n` (name), `t` (title), `role`, `role_label`, `sig` (boolean: is signal source), `q` (quote), `src` (source attribution string), `li` (boolean: has LinkedIn data), `li_posts` (array of `{summary, date, url}`)
