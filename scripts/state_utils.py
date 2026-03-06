"""Shared utility for loading knowledge-base/state.json.

If state.json doesn't exist, copies it from state.json.example.
"""

import json
import shutil
from pathlib import Path

STATE_FILE = Path("knowledge-base/state.json")
STATE_EXAMPLE = Path("knowledge-base/state.json.example")

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


def load_state():
    """Load state.json, creating from example if needed."""
    if not STATE_FILE.exists():
        if STATE_EXAMPLE.exists():
            shutil.copy(STATE_EXAMPLE, STATE_FILE)
        else:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps(DEFAULT_STATE, indent=2))

    with open(STATE_FILE) as f:
        return json.load(f)


def save_state(state):
    """Write state back to state.json."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)
