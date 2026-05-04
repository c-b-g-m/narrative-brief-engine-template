"""Stage 4: Merge LinkedIn CSV signals into buying committee records.

Reads stage2b_buying_committees.json + stage4_linkedin_signals.csv,
matches on exec name + company verification, merges LinkedIn data
into the nested executive records.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import (
    load_csv_bom_safe,
    load_json,
    match_exec_name,
    normalize_name,
    save_json,
)


def parse_linkedin_csv(rows: list[dict]) -> dict:
    """Group LinkedIn CSV rows by exec name, building signal strings.

    Returns:
        Dict mapping normalized exec name -> {company, signals: str, posts: list}
    """
    execs = {}
    for row in rows:
        name = row.get("name", row.get("Name", "")).strip()
        if not name:
            continue

        norm = normalize_name(name)
        if norm not in execs:
            execs[norm] = {
                "name": name,
                "company": row.get("company", row.get("Company", "")),
                "posts": [],
            }

        post_date = row.get("post_date", row.get("Post Date", ""))
        summary = row.get("post_summary", row.get("Post Summary", ""))
        engagement = row.get("engagement", row.get("Engagement", ""))

        if summary:
            post_url = row.get("post_url", row.get("Post URL", ""))
            signal_parts = []
            if post_date:
                signal_parts.append(f"[{post_date}]")
            signal_parts.append(summary)
            if engagement:
                signal_parts.append(f"({engagement})")

            execs[norm]["posts"].append({
                "text": " ".join(signal_parts),
                "url": post_url,
                "summary": summary,
                "date": post_date,
            })

    # Build structured post list (JSON-serializable) for template rendering
    # Limit to 2 most recent posts per exec
    for data in execs.values():
        recent = data["posts"][:2]
        data["structured_posts"] = []
        for post in recent:
            # Clean summary: first sentence or ~80 chars
            summary = post["summary"]
            # Try to cut at first sentence end
            for sep in [". ", "! ", "? "]:
                idx = summary.find(sep)
                if 0 < idx < 100:
                    summary = summary[:idx + 1]
                    break
            else:
                if len(summary) > 80:
                    summary = summary[:77] + "..."
            data["structured_posts"].append({
                "summary": summary,
                "date": post["date"][:10] if post["date"] else "",
                "url": post["url"],
            })
        # Keep backward-compat flat signal string
        data["signals"] = " | ".join(p["text"] for p in recent)

    return execs


def merge_linkedin_committees(
    companies: list[dict],
    linkedin_data: dict,
) -> tuple[list[dict], int]:
    """Merge LinkedIn signals into buying committee executive records.

    Iterates over companies -> executives (nested), matching by name + company.

    Returns:
        (updated companies, count of matches)
    """
    matched = 0

    for company in companies:
        co_name = company["company"].lower()

        for ex in company.get("executives", []):
            if ex["exec_name"] == "Not identified":
                continue

            ex_name = normalize_name(ex["exec_name"])

            for li_name, li_data in linkedin_data.items():
                li_company = li_data["company"].lower()

                if match_exec_name(ex_name, li_name):
                    # Company verification: at least one word overlap
                    co_words = set(co_name.split())
                    li_words = set(li_company.split())
                    if co_words & li_words or co_name in li_company or li_company in co_name:
                        ex["linkedin_signal"] = li_data["signals"]
                        ex["linkedin_posts"] = li_data.get("structured_posts", [])
                        matched += 1
                        break

    return companies, matched


def find_new_discoveries(
    linkedin_data: dict,
    companies: list[dict],
) -> list[dict]:
    """Find LinkedIn execs not already in any buying committee.

    Returns list of dicts with basic info for human review.
    """
    # Collect all known exec names across all companies
    known_names = set()
    for company in companies:
        for ex in company.get("executives", []):
            if ex["exec_name"] != "Not identified":
                known_names.add(normalize_name(ex["exec_name"]))

    discoveries = []
    for li_name, li_data in linkedin_data.items():
        found = False
        for known in known_names:
            if match_exec_name(li_name, known):
                found = True
                break

        if not found and li_data["posts"]:
            discoveries.append({
                "name": li_data["name"],
                "company": li_data["company"],
                "post_count": len(li_data["posts"]),
                "sample": li_data["posts"][0][:200] if li_data["posts"] else "",
            })

    return discoveries


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 stage4_merge.py <client-slug>")
        sys.exit(1)

    slug = sys.argv[1]
    out_dir = Path(__file__).resolve().parent.parent / "output" / slug

    committees_path = out_dir / "stage2b_buying_committees.json"
    csv_path = out_dir / "stage4_linkedin_signals.csv"

    if not committees_path.exists():
        print("  stage2b_buying_committees.json not found. Run stage 2b first.")
        sys.exit(1)

    if not csv_path.exists():
        print(f"  stage4_linkedin_signals.csv not found at {csv_path}")
        print("  Place your LinkedIn research CSV there and re-run.")
        sys.exit(1)

    companies = load_json(committees_path)
    csv_rows = load_csv_bom_safe(csv_path)

    print(f"  LinkedIn CSV: {len(csv_rows)} rows loaded")
    linkedin_data = parse_linkedin_csv(csv_rows)
    print(f"  Unique execs in CSV: {len(linkedin_data)}")

    companies, match_count = merge_linkedin_committees(companies, linkedin_data)
    total_execs = sum(1 for c in companies for e in c.get("executives", []) if e["exec_name"] != "Not identified")
    print(f"  Matched: {match_count}/{total_execs} committee members")

    # Check for new discoveries
    discoveries = find_new_discoveries(linkedin_data, companies)
    if discoveries:
        print(f"\n  LinkedIn Discoveries (not in any committee):")
        for d in discoveries:
            print(f"    - {d['name']} ({d['company']}) — {d['post_count']} posts")
        save_json(discoveries, out_dir / "linkedin_discoveries.json")

    save_json(companies, out_dir / "stage2b_buying_committees.json")
    print(f"  Stage 4 complete: LinkedIn signals merged")


if __name__ == "__main__":
    main()
