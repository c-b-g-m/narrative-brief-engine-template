"""Stage 5: Build the HTML artifact from template + buying committee data.

Reads stage2b_buying_committees.json (per-company with nested executives),
injects data into artifact_template.html, produces the final brief.
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import load_client_config, load_json, save_text

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


def source_display_name(filename: str) -> str:
    """Convert a Lenny's archive filename to a readable source name."""
    if not filename:
        return ""
    # "podcasts/howie-liu.md" → "Lenny's Podcast: Howie Liu"
    # "newsletters/general-management-..." → "Lenny's Newsletter: General Management..."
    name = filename.replace(".md", "")
    if name.startswith("podcasts/"):
        slug = name.replace("podcasts/", "")
        readable = slug.replace("-", " ").title()
        # Truncate long newsletter titles
        if len(readable) > 50:
            readable = readable[:47] + "..."
        return f"Lenny's Podcast: {readable}"
    elif name.startswith("newsletters/"):
        slug = name.replace("newsletters/", "")
        readable = slug.replace("-", " ").title()
        if len(readable) > 50:
            readable = readable[:47] + "..."
        return f"Lenny's Newsletter: {readable}"
    return filename


def company_to_card_data(company: dict) -> dict:
    """Convert a company record with buying committee to the card format used in HTML."""
    heat = company.get("heat", "med")
    cluster = company.get("cluster", "uncategorized")

    execs = []
    for ex in company.get("executives", []):
        role = ex.get("committee_role", "signal_source")
        is_signal = ex.get("is_signal_source", False)

        # Build display role label
        if is_signal and role != "signal_source":
            role_label = f"{role.upper()} + Signal"
        elif role == "signal_source":
            role_label = "Signal"
        else:
            role_label = role.upper()

        # Build rich source attribution
        src_label = ""
        if is_signal and ex.get("episode_title"):
            ep = ex["episode_title"]
            dt = ex.get("source_date", "")
            src_type = "Podcast" if "podcasts/" in (ex.get("source_filename") or "") else "Newsletter"
            src_label = f"Lenny's {src_type}: \"{ep}\" ({dt})" if dt else f"Lenny's {src_type}: \"{ep}\""

        execs.append({
            "n": ex.get("exec_name", ""),
            "t": ex.get("title", ""),
            "role": role,
            "role_label": role_label,
            "sig": is_signal,
            "q": ex.get("source_quote", "") or "",
            "src": src_label,
            "li": bool(ex.get("linkedin_posts") or ex.get("linkedin_signal")),
            "li_posts": ex.get("linkedin_posts", []),
            "lookup": ex.get("lookup_source", ""),
        })

    return {
        "co": company.get("company", ""),
        "ind": company.get("industry", ""),
        "stg": company.get("stage", ""),
        "h": heat,
        "c": cluster,
        "why": company.get("why_now", ""),
        "chg": company.get("change_signal", ""),
        "hire": company.get("hiring_signal", ""),
        "execs": execs,
    }


def build_clusters_js(config: dict) -> str:
    """Build the clusters JS object from config."""
    clusters = config.get("clusters", {})
    # Simplify for JS — just title and thesis
    simplified = {}
    for key, val in clusters.items():
        simplified[key] = {
            "title": val.get("title", key),
            "thesis": val.get("thesis", ""),
        }
    return json.dumps(simplified, ensure_ascii=False, indent=2)


def build_framing_html(config: dict) -> str:
    """Build the header framing copy from config."""
    framing = config.get("framing", {})
    title = html.escape(framing.get("title", "") or "Narrative Intelligence Signal Brief")
    subtitle = html.escape(framing.get("subtitle", "") or "Qualitative signals from executive conversations, enriched with real-time research.")

    paragraphs = framing.get("paragraphs", [])
    if not paragraphs:
        paragraphs = [
            "This brief surfaces companies whose leaders are publicly discussing challenges "
            "that align with your product offerings \u2014 org design, workforce planning, and "
            "AI-human augmentation.",
            "Each company card includes the buying committee: CEO, CFO, CHRO, plus the "
            "executive whose public signal triggered inclusion.",
        ]

    para_html = "\n".join(f"    <p>{html.escape(p)}</p>" for p in paragraphs)

    # Build "prepared for" section from config
    target = config.get("target_buyer", "")
    client_name = html.escape(config.get("client_name", ""))

    prepared_html = ""
    if target:
        # Expects "Name, Title" format (e.g. "Jane Doe, CMO")
        parts = [p.strip() for p in target.split(",", 1)]
        buyer_name = html.escape(parts[0])
        buyer_title = html.escape(parts[1]) if len(parts) > 1 else ""
        prepared_html = f"""<div class="hero-prepared">
      <div class="hero-prepared-label">Prepared for</div>
      <div class="hero-prepared-name">{buyer_name}</div>
      {f'<div class="hero-prepared-title">{buyer_title}</div>' if buyer_title else ''}
      <div class="hero-prepared-co">
        <img src="{{{{CLIENT_LOGO_SRC}}}}" alt="{client_name}" style="height:22px">
        <span>{client_name}</span>
      </div>
    </div>"""

    # Brand block — your firm's logo + name (configurable; falls back to client_name if unset)
    brand_name_raw = config.get("brand_name") or config.get("client_name", "")
    brand_name = html.escape(brand_name_raw)
    brand_url = config.get("brand_url", "").strip()
    if brand_url:
        brand_link = f'<a href="{html.escape(brand_url)}" target="_blank" rel="noopener">{brand_name}</a>'
    else:
        brand_link = brand_name

    return f"""<header>
  <div class="hero-top">
    <div class="hero-from">
      <img class="hero-logo" src="{{{{LOGO_SRC}}}}" alt="{brand_name}">
      <span class="hero-brand">{brand_link}</span>
    </div>
    {prepared_html}
  </div>
  <h1>{title}</h1>
  <div class="sub">{subtitle}</div>
  <div class="frame">
{para_html}
  </div>
  <div class="header-line"></div>
</header>"""


def build_filter_buttons(config: dict) -> str:
    """Build cluster filter buttons from config."""
    clusters = config.get("clusters", {})
    buttons = ""
    for key, val in clusters.items():
        label = val.get("title", key).replace("\u201c", "").replace("\u201d", "")
        buttons += f'  <button class="fbtn" data-f="cluster" data-v="{key}">{label}</button>\n'
    return buttons


def build_artifact(companies: list[dict], config: dict, out_dir: Path | None = None) -> str:
    """Build the complete HTML artifact.

    Args:
        companies: Buying committee records (per-company with nested execs)
        config: Client config dict
        out_dir: Output directory (for loading logo_b64.txt)

    Returns:
        Complete HTML string
    """
    template_path = TEMPLATES_DIR / "artifact_template.html"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    template = template_path.read_text(encoding="utf-8")

    # Build card data
    cards = [company_to_card_data(c) for c in companies]
    cards_js = json.dumps(cards, ensure_ascii=False, indent=2)

    # Build clusters JS
    clusters_js = build_clusters_js(config)

    # Build framing HTML
    framing_html = build_framing_html(config)

    # Build filter buttons
    filter_buttons = build_filter_buttons(config)

    # Load brand (your firm) logo as base64
    logo_path = out_dir / "logo_b64.txt" if out_dir else None
    logo_src = ""
    if logo_path and logo_path.exists():
        logo_src = logo_path.read_text(encoding="utf-8").strip()

    # Load client (recipient) logo as base64
    client_logo_path = out_dir / "client_logo_b64.txt" if out_dir else None
    client_logo_src = ""
    if client_logo_path and client_logo_path.exists():
        client_logo_src = client_logo_path.read_text(encoding="utf-8").strip()

    # Brand metadata for footer
    brand_name_raw = config.get("brand_name") or config.get("client_name", "")
    brand_name = html.escape(brand_name_raw)
    brand_url = config.get("brand_url", "").strip()
    if brand_url:
        brand_link = f'<a href="{html.escape(brand_url)}" target="_blank" rel="noopener">{brand_name}</a>'
    else:
        brand_link = brand_name

    if logo_src:
        footer_logo_block = f'<img class="footer-logo" src="{logo_src}" alt="{brand_name}">'
    else:
        footer_logo_block = ""

    footer_attribution = f"This brief was built with narrative intelligence by {brand_link}." if brand_name_raw else "Built with narrative intelligence."

    # Solution column label (configurable; default "Solution")
    solution_label = html.escape(config.get("solution_label", "Solution"))

    # Inject into template
    output = template.replace("{{FRAMING}}", framing_html)
    output = output.replace("{{CLUSTERS_JS}}", clusters_js)
    output = output.replace("{{PROSPECTS_JS}}", cards_js)
    # Build solution mapping JS from config
    solutions = config.get("solution_mapping", {})
    solutions_js = json.dumps(solutions, ensure_ascii=False, indent=2)

    output = output.replace("{{FILTER_BUTTONS}}", filter_buttons)
    output = output.replace("{{SOLUTIONS_JS}}", solutions_js)
    output = output.replace("{{SOLUTION_LABEL}}", solution_label)
    output = output.replace("{{LOGO_SRC}}", logo_src)
    output = output.replace("{{CLIENT_LOGO_SRC}}", client_logo_src)
    output = output.replace("{{CLIENT_NAME}}", html.escape(config.get("client_name", "")))
    output = output.replace("{{BRAND_NAME}}", brand_name)
    output = output.replace("{{BRAND_URL}}", html.escape(brand_url))
    output = output.replace("{{FOOTER_LOGO_BLOCK}}", footer_logo_block)
    output = output.replace("{{FOOTER_ATTRIBUTION}}", footer_attribution)
    output = output.replace("{{FOOTER_TEXT}}", html.escape(config.get("footer", "Built with narrative intelligence.")))

    return output


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 stage5_build_artifact.py <client-slug>")
        sys.exit(1)

    slug = sys.argv[1]
    out_dir = Path(__file__).resolve().parent.parent / "output" / slug

    # Read buying committees (new schema)
    committees_path = out_dir / "stage2b_buying_committees.json"
    if not committees_path.exists():
        print("  stage2b_buying_committees.json not found. Run stage 2b first.")
        sys.exit(1)

    companies = load_json(committees_path)

    # Load config
    try:
        config = load_client_config(slug)
    except Exception:
        config = {"client_name": slug}

    artifact_html = build_artifact(companies, config, out_dir)
    output_path = out_dir / "narrative_intelligence_brief.html"
    save_text(artifact_html, output_path)

    total_execs = sum(len(c.get("execs", c.get("executives", []))) for c in companies)
    print(f"  Stage 5 complete: {len(companies)} companies, {total_execs} committee members")
    print(f"  Open in browser: {output_path}")


if __name__ == "__main__":
    main()
