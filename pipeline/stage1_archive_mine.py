"""Stage 1: Mine Lenny's Podcast/Newsletter archive for hiring signals.

This script is designed to be called by the narrative-brief skill,
which has access to the Lenny's Podcast MCP tools. The skill runs
each search angle and feeds results back through this script for
structuring and deduplication.

Usage (from skill context):
    python3 pipeline/stage1_archive_mine.py <client-slug>

The skill is responsible for:
1. Loading client config to get search angles
2. Calling the Lenny MCP search_content tool for each angle
3. Calling read_content/read_excerpt for promising results
4. Passing raw results to this script's process_results() for structuring

Standalone mode reads raw_results.json from the client output dir
(useful for testing or re-processing).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow imports when run as script
sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import client_output_dir, load_client_config, load_json, save_json


# No default search angles — these must be defined per client in config.
# The skill will prompt the user to provide angles before running Stage 1.


def extract_signal(content: dict, source_filename: str) -> dict | None:
    """Extract a structured signal from a Lenny archive content item.

    Args:
        content: Dict with at minimum 'title' and 'text' or 'excerpt' fields
                 from the Lenny MCP read_content/read_excerpt response.
        source_filename: The filename from the MCP (e.g., 'podcasts/karri-saarinen.md')

    Returns:
        A signal dict, or None if no hiring signal found.
    """
    return {
        "exec_name": content.get("exec_name", ""),
        "title": content.get("title", ""),
        "company": content.get("company", ""),
        "source_type": "podcast" if "podcasts/" in source_filename else "newsletter",
        "source_filename": source_filename,
        "episode_title": content.get("episode_title", ""),
        "quote_or_signal": content.get("quote", ""),
        "inferred_hiring_need": content.get("inferred_hiring_need", ""),
        "thematic_tag": content.get("thematic_tags", []),
        "date": content.get("date", ""),
    }


def deduplicate_signals(signals: list[dict]) -> list[dict]:
    """Remove duplicate signals based on exec_name + quote substring."""
    seen = set()
    unique = []
    for s in signals:
        # Key on exec name + first 80 chars of quote
        key = (s["exec_name"].lower(), s["quote_or_signal"][:80].lower())
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def process_results(raw_results: list[dict]) -> list[dict]:
    """Process raw MCP results into structured, deduplicated signals.

    Args:
        raw_results: List of dicts, each with 'source_filename' and content fields.

    Returns:
        Deduplicated list of signal dicts.
    """
    signals = []
    for item in raw_results:
        signal = extract_signal(item, item.get("source_filename", ""))
        if signal and signal["quote_or_signal"]:
            signals.append(signal)

    signals = deduplicate_signals(signals)
    print(f"  Stage 1: {len(signals)} unique signals extracted")
    return signals


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 stage1_archive_mine.py <client-slug>")
        print("  Reads raw_results.json from client output dir, produces stage1_archive_signals.json")
        sys.exit(1)

    client_slug = sys.argv[1]
    out_dir = Path(__file__).resolve().parent.parent / "output" / client_slug
    raw_path = out_dir / "raw_results.json"

    if not raw_path.exists():
        print(f"  No raw_results.json found at {raw_path}")
        print("  This file is created by the narrative-brief skill during MCP queries.")
        print("  Run the skill instead: /narrative-brief")
        sys.exit(1)

    raw = load_json(raw_path)
    signals = process_results(raw)
    save_json(signals, out_dir / "stage1_archive_signals.json")
    print(f"  Stage 1 complete: {len(signals)} signals saved")


if __name__ == "__main__":
    main()
