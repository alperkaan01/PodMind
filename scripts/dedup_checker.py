#!/usr/bin/env python3
"""Check if an episode card is a duplicate.

Usage: python scripts/dedup_checker.py <card_path>

Exit code 0 = new episode (OK to proceed)
Exit code 2 = duplicate (blocks the write, feeds error to Claude)
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from state_utils import load_state


def extract_frontmatter(card_text):
    """Extract YAML frontmatter from a markdown card."""
    if not card_text.startswith("---"):
        return {}

    end = card_text.find("---", 3)
    if end == -1:
        return {}

    frontmatter = card_text[3:end].strip()
    result = {}
    for line in frontmatter.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/dedup_checker.py <card_path>", file=sys.stderr)
        sys.exit(1)

    card_path = Path(sys.argv[1])

    if not card_path.exists():
        # File doesn't exist yet — not a duplicate
        sys.exit(0)

    card_text = card_path.read_text(encoding="utf-8")
    frontmatter = extract_frontmatter(card_text)

    episode_id = frontmatter.get("episode_id", "")
    source_url = frontmatter.get("source_url", "")

    # Load state
    state = load_state()

    processed = state.get("processed_episodes", [])

    # Check by episode ID
    for ep in processed:
        if ep.get("episode_id") == episode_id and episode_id:
            print(
                f"DUPLICATE: Episode ID '{episode_id}' already processed "
                f"on {ep.get('processed_date', 'unknown date')}.",
                file=sys.stderr,
            )
            sys.exit(2)

    # Check by source URL
    for ep in processed:
        if ep.get("source_url") == source_url and source_url:
            print(
                f"DUPLICATE: URL '{source_url}' already processed "
                f"as episode '{ep.get('episode_id', 'unknown')}'.",
                file=sys.stderr,
            )
            sys.exit(2)

    # Not a duplicate
    sys.exit(0)


if __name__ == "__main__":
    main()
