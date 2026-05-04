"""Stage 2b: Assemble buying committees per company.

Reads stage2_enriched_prospects.json (per-exec) and produces
stage2b_buying_committees.json (per-company with nested executives).

For each company, the buying committee includes:
  - CEO
  - CFO
  - CHRO (or Head of HR / Chief People Officer)
  - Signal Source(s) — execs who appeared in the Lenny's archive

An exec can fill both a structural role AND be a signal source
(e.g., a CEO who was on Lenny's podcast). In that case:
  committee_role = "ceo", is_signal_source = True

The skill layer is responsible for web-searching missing committee
members and feeding them into this script via raw_committee.json.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import load_client_config, load_json, normalize_company, save_json


ROLE_PATTERNS = {
    "ceo": [r"\bceo\b", r"\bchief executive\b", r"\bfounder and ceo\b", r"\bco-founder and ceo\b"],
    "cfo": [r"\bcfo\b", r"\bchief financial\b"],
    "chro": [r"\bchro\b", r"\bchief people\b", r"\bchief human\b", r"\bhead of hr\b",
             r"\bvp.{0,5}people\b", r"\bhead of people\b", r"\bchief talent\b"],
}


def detect_committee_role(title: str) -> str | None:
    """Detect if an exec's title maps to a structural committee role."""
    title_lower = title.lower()
    for role, patterns in ROLE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, title_lower):
                return role
    return None


def group_by_company(prospects: list[dict], aliases: dict) -> dict:
    """Group prospects by normalized company name."""
    companies = {}
    for p in prospects:
        canonical = normalize_company(p["company"], aliases)
        if canonical not in companies:
            companies[canonical] = {
                "company": canonical,
                "original_names": set(),
                "execs": [],
            }
        companies[canonical]["original_names"].add(p["company"])
        companies[canonical]["execs"].append(p)
    return companies


def build_company_record(canonical_name: str, group: dict, committee_lookups: dict) -> dict:
    """Build a company-level record with nested buying committee."""
    execs = group["execs"]

    # Determine company-level fields from hottest signal source
    heat_order = {"hot": 0, "med": 1, "cold": 2}
    execs_sorted = sorted(execs, key=lambda e: heat_order.get(e.get("heat", "cold"), 3))
    primary = execs_sorted[0]

    # Build executive records
    committee = []
    filled_roles = set()

    for ex in execs:
        role = detect_committee_role(ex["title"])
        if role:
            filled_roles.add(role)

        committee.append({
            "exec_name": ex["exec_name"],
            "title": ex["title"],
            "committee_role": role or "signal_source",
            "is_signal_source": True,
            "source_quote": ex.get("source_quote", ""),
            "episode_title": ex.get("episode_title", ""),
            "thematic_tag": ex.get("thematic_tag", []),
            "source_filename": ex.get("source_filename", ""),
            "source_date": ex.get("date", ""),
            "linkedin_signal": ex.get("linkedin_signal"),
        })

    # Add looked-up committee members for missing roles
    lookups = committee_lookups.get(canonical_name, {})
    for role in ["ceo", "cfo", "chro"]:
        if role not in filled_roles:
            lookup = lookups.get(role, {})
            committee.append({
                "exec_name": lookup.get("exec_name", "Not identified"),
                "title": lookup.get("title", role.upper()),
                "committee_role": role,
                "is_signal_source": False,
                "source_quote": None,
                "thematic_tag": [],
                "source_filename": None,
                "lookup_source": "web_search",
                "linkedin_signal": None,
            })

    # Role order for display: ceo, cfo, chro, then signal sources
    role_order = {"ceo": 0, "cfo": 1, "chro": 2, "signal_source": 3}
    committee.sort(key=lambda e: role_order.get(e["committee_role"], 4))

    return {
        "company": canonical_name,
        "industry": primary.get("industry", ""),
        "stage": primary.get("stage", ""),
        "cluster": primary.get("cluster", ""),
        "heat": primary.get("heat", "med"),
        "fit_tier": primary.get("fit_tier", "B"),
        "why_now": primary.get("why_now", ""),
        "change_signal": primary.get("change_signal", ""),
        "hiring_signal": primary.get("hiring_signal", ""),
        "executives": committee,
    }


def assemble_committees(
    prospects: list[dict],
    aliases: dict,
    committee_lookups: dict | None = None,
) -> list[dict]:
    """Full pipeline: group by company, detect roles, merge lookups."""
    committee_lookups = committee_lookups or {}
    groups = group_by_company(prospects, aliases)

    companies = []
    for canonical, group in groups.items():
        record = build_company_record(canonical, group, committee_lookups)
        companies.append(record)

    # Sort by heat
    heat_order = {"hot": 0, "med": 1, "cold": 2}
    companies.sort(key=lambda c: heat_order.get(c["heat"], 3))

    print(f"  Stage 2b: {len(companies)} companies assembled")
    for c in companies:
        roles = [e["committee_role"] for e in c["executives"]]
        signals = sum(1 for e in c["executives"] if e["is_signal_source"])
        print(f"    {c['heat']:4s} | {c['company']:20s} | {len(c['executives'])} members ({signals} signal sources) | roles: {', '.join(roles)}")

    return companies


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 stage2b_buying_committee.py <client-slug>")
        sys.exit(1)

    slug = sys.argv[1]
    out_dir = Path(__file__).resolve().parent.parent / "output" / slug

    prospects_path = out_dir / "stage2_enriched_prospects.json"
    if not prospects_path.exists():
        print(f"  stage2_enriched_prospects.json not found. Run stage 2 first.")
        sys.exit(1)

    prospects = load_json(prospects_path)

    # Load config
    config = {}
    aliases = {}
    try:
        config = load_client_config(slug)
        aliases = config.get("buying_committee", {}).get("company_aliases", {})
    except Exception:
        pass

    # Load committee lookups if available
    lookups_path = out_dir / "raw_committee_lookups.json"
    lookups = load_json(lookups_path) if lookups_path.exists() else {}

    companies = assemble_committees(prospects, aliases, lookups)
    save_json(companies, out_dir / "stage2b_buying_committees.json")
    print(f"  Stage 2b complete")


if __name__ == "__main__":
    main()
