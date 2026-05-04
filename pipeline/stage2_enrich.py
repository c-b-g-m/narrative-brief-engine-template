"""Stage 2: Enrich prospects with company data and tier scoring.

Takes stage1_archive_signals.json and produces stage2_enriched_prospects.json.

This script is designed to be called by the narrative-brief skill,
which handles the actual web search calls. The skill feeds search
results back through this script's enrichment functions.

Standalone mode reads stage1 signals + raw_enrichment.json from the
client output dir (useful for testing or re-processing).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    client_output_dir,
    load_client_config,
    load_json,
    normalize_name,
    save_json,
)

# Cluster definitions are loaded from client config.
# Each cluster needs: title, thesis, and tags (keywords for matching).
# The skill proposes clusters after Stage 1, then the user approves/edits.
# Format in config:
#   clusters:
#     cluster_key:
#       title: "Display Title"
#       thesis: "One-sentence thesis"
#       tags: ["keyword1", "keyword2", ...]


def assign_cluster(thematic_tags: list[str], clusters: dict) -> str:
    """Assign a prospect to a cluster based on tag overlap scoring.

    Args:
        thematic_tags: Prospect's thematic tags from Stage 1
        clusters: Dict of cluster definitions from config, each with a 'tags' list

    Returns:
        Cluster key with highest tag overlap score.
    """
    if not clusters:
        return "uncategorized"

    tags_lower = [t.lower() for t in thematic_tags]
    scores = {}

    for cluster_key, cluster in clusters.items():
        score = 0
        for keyword in cluster.get("tags", []):
            for tag in tags_lower:
                if keyword.lower() in tag:
                    score += 1
                    break
        scores[cluster_key] = score

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # No match — assign to first cluster as fallback
        return list(clusters.keys())[0]
    return best


def compute_heat(prospect: dict) -> str:
    """Compute heat tier based on hiring signals, change signals, and fit.

    Returns: 'hot', 'med', or 'cold'
    """
    score = 0

    # Fit tier from enrichment
    tier = prospect.get("fit_tier", "C").upper()
    if tier == "A":
        score += 3
    elif tier == "B":
        score += 2
    else:
        score += 1

    # Hiring signal strength
    hiring = prospect.get("hiring_signal", "")
    if any(kw in hiring.lower() for kw in ["hiring", "roles", "headcount", "raise"]):
        score += 2

    # Change signal strength
    change = prospect.get("change_signal", "")
    if any(kw in change.lower() for kw in ["ipo", "transformation", "valuation", "doubled"]):
        score += 1

    # Industry in flux
    industry = prospect.get("industry", "").lower()
    if any(kw in industry for kw in ["ai", "fintech", "health tech"]):
        score += 1

    if score >= 6:
        return "hot"
    elif score >= 4:
        return "med"
    return "cold"


def is_competitor(company: str, competitors: list[str]) -> bool:
    """Check if a company is in the competitor exclusion list."""
    company_lower = company.lower()
    return any(comp.lower() in company_lower for comp in competitors)


def group_signals_by_exec(signals: list[dict]) -> dict:
    """Group stage1 signals by exec_name, collecting all quotes and tags."""
    execs = {}
    for s in signals:
        name = normalize_name(s["exec_name"])
        if name not in execs:
            execs[name] = {
                "exec_name": s["exec_name"],
                "title": s["title"],
                "company": s["company"],
                "source_filename": s["source_filename"],
                "quotes": [],
                "all_tags": [],
            }
        execs[name]["quotes"].append(s["quote_or_signal"])
        execs[name]["all_tags"].extend(s.get("thematic_tag", []))
    return execs


def build_prospect(exec_data: dict, enrichment: dict | None = None, clusters: dict | None = None) -> dict:
    """Build a prospect record from exec signals + optional enrichment data."""
    e = enrichment or {}
    tags = list(set(exec_data["all_tags"]))

    prospect = {
        "exec_name": exec_data["exec_name"],
        "title": e.get("title", exec_data["title"]),
        "company": exec_data["company"],
        "industry": e.get("industry", ""),
        "stage": e.get("stage", ""),
        "change_signal": e.get("change_signal", ""),
        "why_now": e.get("why_now", ""),
        "hiring_signal": e.get("hiring_signal", ""),
        "open_roles_noted": e.get("open_roles_noted", []),
        "fit_tier": e.get("fit_tier", "B"),
        "source_quote": exec_data["quotes"][0] if exec_data["quotes"] else "",
        "thematic_tag": tags,
        "source_filename": exec_data["source_filename"],
    }

    prospect["cluster"] = assign_cluster(tags, clusters or {})
    prospect["heat"] = compute_heat(prospect)

    return prospect


def enrich_prospects(
    signals: list[dict],
    enrichment_data: list[dict] | None = None,
    competitors: list[str] | None = None,
    clusters: dict | None = None,
) -> list[dict]:
    """Full enrichment pipeline: group, enrich, score, filter.

    Args:
        signals: Stage 1 archive signals
        enrichment_data: Optional list of enrichment dicts keyed by exec_name
        competitors: Companies to exclude
        clusters: Cluster definitions from config (with tags for matching)

    Returns:
        List of enriched prospect dicts
    """
    competitors = competitors or []
    enrichment_data = enrichment_data or []
    clusters = clusters or {}

    # Index enrichment by normalized exec name
    enrichment_index = {}
    for e in enrichment_data:
        name = normalize_name(e.get("exec_name", ""))
        enrichment_index[name] = e

    # Group signals by exec
    execs = group_signals_by_exec(signals)

    # Build prospects
    prospects = []
    excluded = []
    for name, exec_data in execs.items():
        if is_competitor(exec_data["company"], competitors):
            excluded.append(exec_data["company"])
            continue
        enrichment = enrichment_index.get(name)
        prospect = build_prospect(exec_data, enrichment, clusters)
        prospects.append(prospect)

    if excluded:
        print(f"  Excluded competitors: {', '.join(set(excluded))}")

    # Sort: hot first, then med, then cold
    heat_order = {"hot": 0, "med": 1, "cold": 2}
    prospects.sort(key=lambda p: heat_order.get(p["heat"], 3))

    print(f"  Stage 2: {len(prospects)} prospects enriched")
    heat_counts = {}
    for p in prospects:
        heat_counts[p["heat"]] = heat_counts.get(p["heat"], 0) + 1
    for h in ["hot", "med", "cold"]:
        if h in heat_counts:
            print(f"    {h}: {heat_counts[h]}")

    return prospects


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 stage2_enrich.py <client-slug>")
        sys.exit(1)

    slug = sys.argv[1]
    out_dir = Path(__file__).resolve().parent.parent / "output" / slug

    signals_path = out_dir / "stage1_archive_signals.json"
    if not signals_path.exists():
        print(f"  stage1_archive_signals.json not found. Run stage 1 first.")
        sys.exit(1)

    signals = load_json(signals_path)

    # Load enrichment if available (created by skill during web search)
    enrichment_path = out_dir / "raw_enrichment.json"
    enrichment = load_json(enrichment_path) if enrichment_path.exists() else []

    # Load config
    competitors = []
    clusters = {}
    try:
        config = load_client_config(slug)
        competitors = config.get("competitors", []) + config.get("known_customers", [])
        clusters = config.get("clusters", {})
    except Exception:
        pass

    if not clusters:
        print("  Warning: No clusters defined in config. Run the skill to propose clusters first.")

    prospects = enrich_prospects(signals, enrichment, competitors, clusters)
    save_json(prospects, out_dir / "stage2_enriched_prospects.json")
    print(f"  Stage 2 complete")


if __name__ == "__main__":
    main()
