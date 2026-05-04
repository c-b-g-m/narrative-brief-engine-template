"""Stage 3: Generate Chrome extension prompts for LinkedIn research.

Reads stage2b_buying_committees.json (per-company with nested executives)
and produces a markdown file with prompts for each committee member.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import load_json, save_text

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


# Role-specific keyword additions for non-signal-source execs
ROLE_KEYWORDS = {
    "ceo": ["strategy", "transformation", "company direction", "AI investment"],
    "cfo": ["headcount", "workforce cost", "budget", "planning", "efficiency"],
    "chro": ["talent", "people strategy", "retention", "workforce planning", "employee experience"],
}


def build_keywords_signal(exec_data: dict, company: dict) -> str:
    """Build keywords for a signal source exec (from Lenny's archive)."""
    base = ["hiring", "talent", "team building", "AI", "organizational change", "culture"]
    tags = exec_data.get("thematic_tag", [])
    all_kw = list(dict.fromkeys(base + tags))
    return ", ".join(all_kw)


def build_keywords_role(exec_data: dict, company: dict) -> str:
    """Build keywords for a looked-up committee member (CEO/CFO/CHRO)."""
    role = exec_data.get("committee_role", "")
    role_kw = ROLE_KEYWORDS.get(role, [])
    # Pull signal words from company-level change_signal
    change = company.get("change_signal", "")
    change_kw = []
    for term in ["reorg", "restructur", "AI", "headcount", "layoff", "hiring", "workforce", "flattening"]:
        if term.lower() in change.lower():
            change_kw.append(term)
    all_kw = list(dict.fromkeys(role_kw + change_kw))
    return ", ".join(all_kw) if all_kw else "leadership, strategy, workforce"


def generate_prompts(
    companies: list[dict],
    template: str,
) -> str:
    """Generate Chrome extension prompts for all committee members.

    Args:
        companies: List of company dicts with nested executives
        template: Prompt template with {{NAME}}, {{COMPANY}}, {{TITLE}}, {{KEYWORDS}}, {{TYPE}} slots

    Returns:
        Markdown string with all prompts grouped by company
    """
    lines = [
        "# Chrome Extension Prompts — Buying Committee Research\n",
        "Instructions: Navigate to LinkedIn.com first. Then paste ONE prompt below "
        "into the Claude Chrome extension. Each prompt is self-contained.\n",
        "After each prompt completes, copy the output table and paste it into a "
        "spreadsheet or text file. When all prompts are done, save the combined "
        "table as `stage4_linkedin_signals.csv`.\n",
        "---\n",
    ]

    prompt_num = 0
    skipped = 0

    for company in companies:
        co_name = company["company"]
        heat = company.get("heat", "med")
        execs = company.get("executives", [])

        lines.append(f"\n## {co_name} ({heat.upper()})\n")
        lines.append("---\n")

        for ex in execs:
            name = ex["exec_name"]

            # Skip unidentified committee members
            if name == "Not identified":
                skipped += 1
                lines.append(f"*{ex['committee_role'].upper()}: Not identified — skip*\n")
                continue

            prompt_num += 1
            title = ex.get("title", "")
            role = ex.get("committee_role", "signal_source")
            is_signal = ex.get("is_signal_source", False)

            # Build role label for display
            role_label = role.upper()
            if is_signal and role != "signal_source":
                role_label = f"{role.upper()} + SIGNAL SOURCE"

            # Choose keyword strategy
            if is_signal:
                keywords = build_keywords_signal(ex, company)
            else:
                keywords = build_keywords_role(ex, company)

            prompt_type = "signal_source" if is_signal else role

            prompt = template.replace("{{NAME}}", name)
            prompt = prompt.replace("{{COMPANY}}", co_name)
            prompt = prompt.replace("{{TITLE}}", title)
            prompt = prompt.replace("{{KEYWORDS}}", keywords)
            prompt = prompt.replace("{{TYPE}}", prompt_type)

            lines.append(f"### Prompt {prompt_num} — {name} [{role_label}]\n")
            lines.append(f"```\n{prompt}\n```\n")
            lines.append("---\n")

    lines.append(f"\n**Total: {prompt_num} prompts generated, {skipped} committee members not identified.**\n")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 stage3_linkedin_prompts.py <client-slug>")
        sys.exit(1)

    slug = sys.argv[1]
    out_dir = Path(__file__).resolve().parent.parent / "output" / slug

    # Read buying committees (new schema)
    committees_path = out_dir / "stage2b_buying_committees.json"
    if not committees_path.exists():
        print("  stage2b_buying_committees.json not found. Run stage 2b first.")
        sys.exit(1)

    template_path = TEMPLATES_DIR / "chrome_prompt_template.md"
    if not template_path.exists():
        print(f"  Template not found: {template_path}")
        sys.exit(1)

    companies = load_json(committees_path)
    template = template_path.read_text(encoding="utf-8")

    output = generate_prompts(companies, template)
    save_text(output, out_dir / "stage3_chrome_prompts.md")

    total_execs = sum(len(c.get("executives", [])) for c in companies)
    identified = sum(1 for c in companies for e in c.get("executives", []) if e["exec_name"] != "Not identified")
    print(f"  Stage 3 complete: {identified} prompts across {len(companies)} companies ({total_execs - identified} not identified)")


if __name__ == "__main__":
    main()
