#!/usr/bin/env python3
"""Initialize the knowledge-base directory structure for a new user.

Usage: python scripts/init_kb.py
"""

import json
from pathlib import Path

DIRS = [
    "knowledge-base/episodes",
    "knowledge-base/concepts",
    "knowledge-base/summaries",
    "knowledge-base/extracted",
    "knowledge-base/tagged",
    "knowledge-base/linked",
    "knowledge-base/raw",
]

DEFAULT_STATE = {
    "last_updated": None,
    "processed_episodes": [],
    "total_episodes": 0,
    "total_concepts": 0,
    "total_insights": 0,
    "graph_stats": {
        "total_nodes": 0,
        "total_edges": 0,
        "hub_concepts": [],
    },
}


def main():
    for d in DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)

    state_path = Path("knowledge-base/state.json")
    if not state_path.exists():
        state_path.write_text(json.dumps(DEFAULT_STATE, indent=2))
        print("Created knowledge-base/state.json")

    print("Knowledge base initialized:")
    for d in DIRS:
        print(f"  {d}/")


if __name__ == "__main__":
    main()
