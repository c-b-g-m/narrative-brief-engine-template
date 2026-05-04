"""Shared helpers for the narrative-brief-engine pipeline."""

from __future__ import annotations

import csv
import json
import os
import re
import unicodedata
from pathlib import Path


ENGINE_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ENGINE_ROOT / "output"
CONFIG_DIR = ENGINE_ROOT / "config"
TEMPLATES_DIR = ENGINE_ROOT / "templates"


def client_slug(name: str) -> str:
    """Convert a client name to a filesystem-safe slug."""
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")
    name = re.sub(r"[^\w\s-]", "", name.lower())
    return re.sub(r"[-\s]+", "-", name).strip("-")


def client_output_dir(client_name: str) -> Path:
    """Return (and create) the output directory for a client."""
    out = OUTPUT_DIR / client_slug(client_name)
    out.mkdir(parents=True, exist_ok=True)
    return out


def load_json(path: Path) -> list | dict:
    """Load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path: Path) -> None:
    """Save data as pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved: {path}")


def load_csv_bom_safe(path: Path) -> list[dict]:
    """Load a CSV file, handling UTF-8 BOM in headers."""
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_text(text: str, path: Path) -> None:
    """Write a text/markdown/html file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  Saved: {path}")


def load_client_config(client_name: str | None = None) -> dict:
    """Load client config YAML. Falls back to client.yaml if no name given."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML required: pip install pyyaml")

    if client_name:
        config_path = CONFIG_DIR / f"{client_slug(client_name)}.yaml"
        if not config_path.exists():
            config_path = CONFIG_DIR / "client.yaml"
    else:
        config_path = CONFIG_DIR / "client.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_company(name: str, aliases: dict | None = None) -> str:
    """Normalize a company name for grouping.

    Strips suffixes (Inc., Corp., Ltd.), applies alias map, lowercases for matching.
    Returns the canonical display name (not lowercased).
    """
    aliases = aliases or {}
    # Check alias map first (case-insensitive)
    for variant, canonical in aliases.items():
        if name.strip().lower() == variant.strip().lower():
            return canonical
    # Strip common suffixes
    import re as _re
    cleaned = _re.sub(r'\s*,?\s*(Inc\.?|Corp\.?|Ltd\.?|LLC|Co\.?)$', '', name.strip(), flags=_re.IGNORECASE)
    return cleaned


def normalize_name(name: str) -> str:
    """Normalize an executive name for matching: lowercase, strip whitespace."""
    return " ".join(name.lower().split())


def match_exec_name(name_a: str, name_b: str) -> bool:
    """Match two executive names, handling minor variations."""
    a = normalize_name(name_a)
    b = normalize_name(name_b)
    if a == b:
        return True
    # Handle "First Last" matching "First M. Last" or similar
    a_parts = a.split()
    b_parts = b.split()
    if len(a_parts) >= 2 and len(b_parts) >= 2:
        return a_parts[0] == b_parts[0] and a_parts[-1] == b_parts[-1]
    return False
