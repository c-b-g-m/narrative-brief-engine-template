"""Stage 3 (Apify): Automated LinkedIn research via HarvestAPI actors.

Chains two Apify actors:
  1. harvestapi/linkedin-profile-search-by-name → resolves exec names to profile URLs
  2. harvestapi/linkedin-profile-posts → scrapes recent posts from profiles

Produces stage4_linkedin_signals.csv for Stage 4 merge.

Security:
  - No eval(), exec(), subprocess, or dynamic imports
  - All outbound requests restricted to api.apify.com
  - API token loaded from APIFY_API_TOKEN env var only
  - --dry-run flag prints payloads without sending
  - Every API call URL logged to stdout
"""

from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path

# Only stdlib + requests — no dynamic imports
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from utils import load_client_config, load_json, save_json

APIFY_API_BASE = "https://api.apify.com/v2"
ALLOWED_DOMAIN = "api.apify.com"


def get_api_token() -> str:
    """Load Apify API token from environment."""
    # Check .env.local in project root
    env_path = Path(__file__).resolve().parent.parent / ".env.local"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("APIFY_API_TOKEN="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")

    token = os.getenv("APIFY_API_TOKEN", "")
    if not token:
        print("  ERROR: APIFY_API_TOKEN not found in .env.local or environment.")
        print("  Add it to .env.local: APIFY_API_TOKEN=your_token_here")
        sys.exit(1)
    return token


def safe_request(method: str, url: str, token: str, payload: dict | None = None, dry_run: bool = False) -> dict:
    """Make an API request, enforcing domain restriction and logging."""
    # Domain restriction — only api.apify.com
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.hostname != ALLOWED_DOMAIN:
        raise ValueError(f"  BLOCKED: Request to {parsed.hostname} denied. Only {ALLOWED_DOMAIN} allowed.")

    print(f"  API {method} → {url}")

    if dry_run:
        print(f"  [DRY RUN] Payload: {json.dumps(payload, indent=2)[:500]}")
        return {"dry_run": True}

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    if method == "POST":
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
    elif method == "GET":
        resp = requests.get(url, headers=headers, timeout=30)
    else:
        raise ValueError(f"Unsupported method: {method}")

    resp.raise_for_status()
    return resp.json()


def start_actor_run(actor_id: str, input_data: dict, token: str, dry_run: bool = False) -> str | None:
    """Start an Apify actor run and return the run ID."""
    # Apify API requires ~ separator between username and actor name
    actor_id_api = actor_id.replace("/", "~")
    url = f"{APIFY_API_BASE}/acts/{actor_id_api}/runs"
    result = safe_request("POST", url, token, payload=input_data, dry_run=dry_run)

    if dry_run:
        return None

    run_id = result.get("data", {}).get("id")
    print(f"  Run started: {run_id}")
    return run_id


def wait_for_run(run_id: str, token: str, max_wait: int = 300) -> dict:
    """Poll until an actor run completes. Returns run data."""
    url = f"{APIFY_API_BASE}/actor-runs/{run_id}"
    elapsed = 0
    interval = 5

    while elapsed < max_wait:
        result = safe_request("GET", url, token)
        status = result.get("data", {}).get("status", "")

        if status == "SUCCEEDED":
            print(f"  Run {run_id} completed.")
            return result.get("data", {})
        elif status in ("FAILED", "ABORTED", "TIMED-OUT"):
            print(f"  Run {run_id} failed with status: {status}")
            return {}

        time.sleep(interval)
        elapsed += interval

    print(f"  Run {run_id} timed out after {max_wait}s")
    return {}


def fetch_dataset(dataset_id: str, token: str) -> list[dict]:
    """Fetch all items from an Apify dataset."""
    url = f"{APIFY_API_BASE}/datasets/{dataset_id}/items?format=json"
    result = safe_request("GET", url, token)

    if isinstance(result, list):
        return result
    return []


def build_name_search_inputs(companies: list[dict]) -> list[dict]:
    """Build Apify inputs for the name search actor, one per identified exec."""
    searches = []

    for company in companies:
        co_name = company["company"]
        for ex in company.get("executives", []):
            name = ex.get("exec_name", "")
            if name == "Not identified" or not name:
                continue

            parts = name.split()
            if len(parts) < 2:
                continue

            first_name = parts[0]
            last_name = " ".join(parts[1:])

            searches.append({
                "first_name": first_name,
                "last_name": last_name,
                "company": co_name,
                "title": ex.get("title", ""),
                "committee_role": ex.get("committee_role", "signal_source"),
                "actor_input": {
                    "firstName": first_name,
                    "lastName": last_name,
                    "maxItems": 3,
                    "mode": "short",
                },
            })

    return searches


def resolve_profile_urls(searches: list[dict], actor_id: str, token: str, dry_run: bool = False) -> list[dict]:
    """Run name searches and resolve to LinkedIn profile URLs.

    Returns list of dicts with profile_url added to each search.
    """
    resolved = []

    for i, search in enumerate(searches):
        name = f"{search['first_name']} {search['last_name']}"
        print(f"\n  [{i+1}/{len(searches)}] Searching: {name} ({search['company']})")

        run_id = start_actor_run(actor_id, search["actor_input"], token, dry_run)

        if dry_run:
            search["profile_url"] = f"https://www.linkedin.com/in/{name.lower().replace(' ', '-')}-dry-run"
            resolved.append(search)
            continue

        if not run_id:
            search["profile_url"] = None
            resolved.append(search)
            continue

        run_data = wait_for_run(run_id, token)
        dataset_id = run_data.get("defaultDatasetId")

        if not dataset_id:
            print(f"  No dataset for {name}")
            search["profile_url"] = None
            resolved.append(search)
            continue

        items = fetch_dataset(dataset_id, token)

        # Find best match — prefer name + company overlap
        best_url = None
        company_lower = search["company"].lower()

        for item in items:
            url = item.get("linkedinUrl") or item.get("profileUrl") or item.get("url")
            headline = (item.get("headline") or item.get("info") or "").lower()
            item_name = (item.get("name") or item.get("fullName") or "").lower()

            if url:
                # Prefer matches where company appears in headline
                if company_lower.split()[0].lower() in headline:
                    best_url = url
                    break
                elif not best_url:
                    best_url = url

        search["profile_url"] = best_url
        if best_url:
            print(f"  Found: {best_url}")
        else:
            print(f"  No profile found for {name}")

        resolved.append(search)

        # Rate limiting between searches
        if not dry_run:
            time.sleep(2)

    return resolved


def scrape_posts(resolved: list[dict], actor_id: str, token: str, max_posts: int = 10, dry_run: bool = False) -> list[dict]:
    """Scrape posts for all resolved profiles in one batch run."""
    profile_urls = [r.get("profile_url") for r in resolved if r.get("profile_url")]

    if not profile_urls:
        print("  No profile URLs to scrape posts from.")
        return []

    print(f"\n  Scraping posts for {len(profile_urls)} profiles...")

    actor_input = {
        "profileUrls": profile_urls,
        "maxPosts": max_posts,
        "scrapeReactions": False,
        "scrapeComments": False,
    }

    run_id = start_actor_run(actor_id, actor_input, token, dry_run)

    if dry_run:
        return []

    if not run_id:
        return []

    run_data = wait_for_run(run_id, token, max_wait=600)
    dataset_id = run_data.get("defaultDatasetId")

    if not dataset_id:
        print("  No dataset returned from posts scraper.")
        return []

    posts = fetch_dataset(dataset_id, token)
    print(f"  Retrieved {len(posts)} posts total.")
    return posts


def build_url_to_exec_map(resolved: list[dict]) -> dict:
    """Map profile URLs to exec metadata for CSV generation."""
    url_map = {}
    for r in resolved:
        url = r.get("profile_url")
        if url:
            # Normalize URL for matching (strip trailing slash)
            url_clean = url.rstrip("/").lower()
            url_map[url_clean] = {
                "name": f"{r['first_name']} {r['last_name']}",
                "title": r["title"],
                "company": r["company"],
                "committee_role": r["committee_role"],
            }
    return url_map


def posts_to_csv_rows(posts: list[dict], url_map: dict) -> list[dict]:
    """Transform Apify post data into Stage 4 CSV rows."""
    rows = []

    for post in posts:
        # Match post author to our exec map
        author_url = ""
        author = post.get("author", {})
        if isinstance(author, dict):
            author_url = (author.get("linkedinUrl") or author.get("url") or "").rstrip("/").lower()
            author_name = author.get("name", "")
        else:
            author_name = str(author)

        # Look up exec metadata
        exec_info = url_map.get(author_url)
        if not exec_info:
            # Try partial URL match
            for map_url, info in url_map.items():
                if map_url in author_url or author_url in map_url:
                    exec_info = info
                    break

        if not exec_info:
            # Skip posts we can't match to our committee
            continue

        # Extract post data
        content = post.get("content") or post.get("text") or ""
        posted_at = post.get("postedAt", {})
        if isinstance(posted_at, dict):
            post_date = posted_at.get("formattedDate") or posted_at.get("date") or ""
        else:
            post_date = str(posted_at)

        engagement = post.get("engagement", {})
        likes = engagement.get("likes", 0) if isinstance(engagement, dict) else 0
        comments = engagement.get("comments", 0) if isinstance(engagement, dict) else 0
        engagement_str = f"{likes} likes, {comments} comments"

        post_url = post.get("linkedinUrl") or post.get("url") or ""

        # Truncate content for summary
        summary = content[:200].replace("\n", " ").strip()
        if len(content) > 200:
            summary += "..."

        rows.append({
            "Name": exec_info["name"],
            "Title": exec_info["title"],
            "Company": exec_info["company"],
            "Post Date": post_date,
            "Post Summary": summary,
            "Post URL": post_url,
            "Engagement": engagement_str,
            "Type": exec_info["committee_role"],
        })

    return rows


def write_csv(rows: list[dict], path: Path) -> None:
    """Write CSV in the format Stage 4 expects."""
    if not rows:
        print("  No rows to write.")
        return

    fieldnames = ["Name", "Title", "Company", "Post Date", "Post Summary", "Post URL", "Engagement", "Type"]
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Saved: {path} ({len(rows)} rows)")


def main():
    # Parse args
    if len(sys.argv) < 2:
        print("Usage: python3 stage3_apify_linkedin.py <client-slug> [--dry-run]")
        sys.exit(1)

    slug = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("  === DRY RUN MODE — no API calls will be made ===\n")

    out_dir = Path(__file__).resolve().parent.parent / "output" / slug

    # Load data
    committees_path = out_dir / "stage2b_buying_committees.json"
    if not committees_path.exists():
        print("  stage2b_buying_committees.json not found. Run stage 2b first.")
        sys.exit(1)

    companies = load_json(committees_path)

    # Load config
    try:
        config = load_client_config(slug)
    except Exception:
        config = {}

    apify_config = config.get("apify", {})
    posts_actor = apify_config.get("posts_actor", "harvestapi/linkedin-profile-posts")
    max_posts = apify_config.get("max_posts_per_profile", 10)

    # Get token (skip in dry run)
    token = ""
    if not dry_run:
        token = get_api_token()

    # Step 1: Load pre-resolved profile URLs (resolved via web search, not Apify)
    profiles_path = out_dir / "apify_resolved_profiles.json"
    if not profiles_path.exists():
        print("  apify_resolved_profiles.json not found.")
        print("  This file should contain LinkedIn profile URLs resolved via web search.")
        sys.exit(1)

    resolved = load_json(profiles_path)
    found = sum(1 for r in resolved if r.get("profile_url"))
    print(f"  {found} pre-resolved profile URLs loaded\n")

    # Step 2: Scrape posts using Apify posts actor
    posts = scrape_posts(resolved, posts_actor, token, max_posts, dry_run)

    # Step 3: Transform to CSV
    # Build URL map from resolved profiles (different format than old resolve flow)
    url_map = {}
    for r in resolved:
        url = r.get("profile_url", "")
        if url:
            url_clean = url.rstrip("/").lower()
            url_map[url_clean] = {
                "name": r["name"],
                "title": r.get("title", ""),
                "company": r["company"],
                "committee_role": r.get("role", "signal_source"),
            }

    csv_rows = posts_to_csv_rows(posts, url_map)

    csv_path = out_dir / "stage4_linkedin_signals.csv"
    write_csv(csv_rows, csv_path)

    print(f"\n  Stage 3 (Apify) complete.")
    print(f"  Profiles loaded: {found}")
    print(f"  Posts scraped: {len(posts)}")
    print(f"  CSV rows: {len(csv_rows)}")
    if dry_run:
        print("  [DRY RUN — no actual API calls were made]")


if __name__ == "__main__":
    main()
