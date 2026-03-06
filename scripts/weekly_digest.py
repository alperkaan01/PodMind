#!/usr/bin/env python3
"""Generate a weekly digest of recently processed episodes.

Usage: python scripts/weekly_digest.py

Reads state.json for episodes from the last 7 days, generates a
digest markdown file in knowledge-base/synthesis/.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from state_utils import load_state

EPISODES_DIR = Path("knowledge-base/episodes")
TAGGED_DIR = Path("knowledge-base/tagged")
SYNTHESIS_DIR = Path("knowledge-base/synthesis")


def get_recent_episodes(state, days=7):
    """Find episodes processed in the last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    recent = []

    for ep in state.get("processed_episodes", []):
        date_str = ep.get("processed_date")
        if not date_str:
            continue
        try:
            ep_date = datetime.strptime(date_str, "%Y-%m-%d")
            if ep_date >= cutoff:
                recent.append(ep)
        except ValueError:
            continue

    return recent


def load_tagged_data(episode_id):
    """Load tagged JSON for an episode."""
    path = TAGGED_DIR / f"{episode_id}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def load_card(episode_id):
    """Load episode card text."""
    path = EPISODES_DIR / f"{episode_id}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


def extract_summary_from_card(card_text):
    """Extract summary section from card."""
    in_summary = False
    lines = []
    for line in card_text.split("\n"):
        if line.startswith("## Summary"):
            in_summary = True
            continue
        if in_summary and line.startswith("## "):
            break
        if in_summary and line.strip():
            lines.append(line.strip())
    return " ".join(lines) if lines else "No summary available"


def generate_digest(recent_episodes, state):
    """Generate digest markdown content."""
    today = datetime.now().strftime("%Y-%m-%d")
    all_new_concepts = []
    all_contradictions = []
    all_tags = []

    lines = [
        f"# PodMind Weekly Digest — {today}",
        "",
        f"**Episodes processed this week:** {len(recent_episodes)}",
        "",
    ]

    # Episodes section
    if recent_episodes:
        lines.append("## Episodes Added")
        lines.append("")
        for ep in recent_episodes:
            ep_id = ep.get("episode_id", "unknown")
            title = ep.get("title", ep_id)
            card_text = load_card(ep_id)
            summary = extract_summary_from_card(card_text) if card_text else "No card found"
            lines.append(f"- **{title}** — {summary[:150]}")

            # Collect concepts and tags
            tagged = load_tagged_data(ep_id)
            if tagged:
                for concept in tagged.get("concepts", []):
                    all_new_concepts.append(concept)
                all_tags.extend(tagged.get("tags", []))
                # Check for contradictions in linked data
        lines.append("")

    # New concepts
    if all_new_concepts:
        lines.append("## New Concepts Discovered")
        lines.append("")
        seen = set()
        for concept in all_new_concepts:
            name = concept.get("name", "")
            if name not in seen:
                defn = concept.get("definition", "")
                lines.append(f"- **{name}**: {defn}")
                seen.add(name)
        lines.append("")

    # Most connected concept (from graph stats)
    graph_stats = state.get("graph_stats", {})
    hub_concepts = graph_stats.get("hub_concepts", [])
    if hub_concepts:
        lines.append("## Most Connected Concept")
        lines.append("")
        if isinstance(hub_concepts[0], str):
            lines.append(f"**{hub_concepts[0]}** — central hub in the knowledge graph")
        else:
            lines.append(f"**{hub_concepts[0]}**")
        lines.append("")

    # Tag frequency
    if all_tags:
        lines.append("## Topic Distribution")
        lines.append("")
        from collections import Counter
        tag_counts = Counter(all_tags)
        for tag, count in tag_counts.most_common(5):
            lines.append(f"- `{tag}` ({count} episode{'s' if count > 1 else ''})")
        lines.append("")

    # Connection of the week placeholder
    lines.append("## Connection of the Week")
    lines.append("")
    if len(recent_episodes) >= 2:
        lines.append("Run `python scripts/graph_analyzer.py` and check the graph for")
        lines.append("the most surprising cross-episode connection this week.")
    else:
        lines.append("Need at least 2 episodes to find cross-episode connections.")
    lines.append("")

    return "\n".join(lines)


def main():
    SYNTHESIS_DIR.mkdir(parents=True, exist_ok=True)

    state = load_state()
    recent = get_recent_episodes(state)

    if not recent:
        print("No episodes processed in the last 7 days.")
        # Still generate an empty digest
        today = datetime.now().strftime("%Y-%m-%d")
        digest = f"# PodMind Weekly Digest — {today}\n\nNo new episodes this week.\n"
    else:
        digest = generate_digest(recent, state)

    today = datetime.now().strftime("%Y-%m-%d")
    output_path = SYNTHESIS_DIR / f"digest-{today}.md"
    output_path.write_text(digest, encoding="utf-8")

    print(f"Digest saved to: {output_path}")
    print(f"Episodes this week: {len(recent)}")


if __name__ == "__main__":
    main()
