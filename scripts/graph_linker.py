#!/usr/bin/env python3
"""Build knowledge graph nodes, edges, and contradiction checks for an episode.

Usage: python scripts/graph_linker.py <episode_id>

Reads tagged JSON, builds all nodes and relations, detects contradictions
against existing episodes, runs similarity scoring, saves linked output,
and updates state.json. Designed to be a single-command automation for
the linker agent.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from state_utils import load_state, save_state

TAGGED_DIR = Path("knowledge-base/tagged")
LINKED_DIR = Path("knowledge-base/linked")
EXTRACTED_DIR = Path("knowledge-base/extracted")


def load_tagged(episode_id: str) -> dict:
    path = TAGGED_DIR / f"{episode_id}.json"
    if not path.exists():
        print(f"Error: Tagged JSON not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path) as f:
        return json.load(f)


def load_existing_insights() -> list[dict]:
    """Load all insights from previously linked episodes."""
    insights = []
    if not LINKED_DIR.exists():
        return insights
    for linked_file in LINKED_DIR.glob("*.json"):
        with open(linked_file) as f:
            data = json.load(f)
        ep_id = data.get("episode_id", linked_file.stem)
        for node in data.get("nodes", []):
            if node.get("type") == "Insight":
                insights.append({
                    "text": node.get("label", ""),
                    "episode_id": ep_id,
                })
    return insights


def build_nodes(data: dict, episode_id: str) -> list[dict]:
    """Build all graph nodes from tagged episode data."""
    nodes = []
    meta = data.get("episode_metadata", {})

    # Episode node
    nodes.append({
        "id": episode_id,
        "type": "Episode",
        "label": meta.get("title", episode_id),
        "metadata": {
            "date": meta.get("date"),
            "url": meta.get("source_url"),
            "host": meta.get("host"),
            "guest": meta.get("guest"),
            "tags": data.get("tags", []),
            "relevance_score": data.get("relevance_score"),
            "novelty_score": data.get("novelty_score"),
            "complexity_score": data.get("complexity_score"),
        },
    })

    # Concept nodes
    for concept in data.get("concepts", []):
        nodes.append({
            "id": f"concept:{concept['name']}",
            "type": "Concept",
            "label": concept["name"],
            "metadata": {
                "definition": concept.get("definition", ""),
                "source_episode": episode_id,
            },
        })

    # Insight nodes
    for i, insight in enumerate(data.get("insights", [])):
        short_label = insight["text"][:60].rstrip()
        nodes.append({
            "id": f"insight:{episode_id}:{i}",
            "type": "Insight",
            "label": short_label,
            "metadata": {
                "full_text": insight["text"],
                "speaker": insight.get("speaker"),
                "timestamp": insight.get("timestamp"),
                "source_episode": episode_id,
            },
        })

    # Quote nodes
    for i, quote in enumerate(data.get("quotes", [])):
        short_label = " ".join(quote["text"].split()[:7])
        nodes.append({
            "id": f"quote:{episode_id}:{i}",
            "type": "Quote",
            "label": short_label,
            "metadata": {
                "full_text": quote["text"],
                "speaker": quote.get("speaker"),
                "timestamp": quote.get("timestamp"),
                "context": quote.get("context"),
                "source_episode": episode_id,
            },
        })

    return nodes


def build_edges(data: dict, episode_id: str) -> list[dict]:
    """Build all graph edges from tagged episode data."""
    edges = []

    # Episode -> contains -> Concepts
    for concept in data.get("concepts", []):
        edges.append({
            "source": episode_id,
            "target": f"concept:{concept['name']}",
            "relation": "contains",
        })

    # Episode -> contains -> Insights
    for i in range(len(data.get("insights", []))):
        edges.append({
            "source": episode_id,
            "target": f"insight:{episode_id}:{i}",
            "relation": "contains",
        })

    # Episode -> contains -> Quotes
    for i in range(len(data.get("quotes", []))):
        edges.append({
            "source": episode_id,
            "target": f"quote:{episode_id}:{i}",
            "relation": "contains",
        })

    # Concept -> relates_to -> Concept (based on shared tags / co-occurrence)
    concepts = data.get("concepts", [])
    for i, c1 in enumerate(concepts):
        for c2 in concepts[i + 1:]:
            edges.append({
                "source": f"concept:{c1['name']}",
                "target": f"concept:{c2['name']}",
                "relation": "relates_to",
                "note": f"Co-occur in episode {episode_id}",
            })

    return edges


def detect_contradictions(data: dict, episode_id: str, existing_insights: list[dict]) -> list[dict]:
    """Simple keyword-overlap contradiction detection.

    Finds existing insights that share significant vocabulary with new insights,
    which the linker agent can then review for actual contradictions.
    """
    if not existing_insights:
        return []

    candidates = []
    new_insights = data.get("insights", [])

    for i, new_ins in enumerate(new_insights):
        new_words = set(new_ins["text"].lower().split())
        for existing in existing_insights:
            if existing["episode_id"] == episode_id:
                continue
            existing_words = set(existing["text"].lower().split())
            overlap = new_words & existing_words
            # Filter out stop words for meaningful overlap
            meaningful = {w for w in overlap if len(w) > 3}
            if len(meaningful) >= 3:
                candidates.append({
                    "new_insight": new_ins["text"],
                    "new_insight_id": f"insight:{episode_id}:{i}",
                    "existing_insight": existing["text"],
                    "existing_episode": existing["episode_id"],
                    "shared_terms": sorted(meaningful),
                })

    return candidates


def run_similarity_scorer(episode_id: str) -> dict:
    """Run the similarity scorer script and return results."""
    try:
        result = subprocess.run(
            ["pixi", "run", "python", "scripts/similarity_scorer.py", episode_id],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass
    return {"episode_id": episode_id, "similar_episodes": []}


def update_project_state(episode_id: str, data: dict, nodes: list, edges: list):
    """Update knowledge-base/state.json with this episode."""
    state = load_state()
    if episode_id not in state.get("processed_episodes", []):
        state.setdefault("processed_episodes", []).append(episode_id)
    state["total_episodes"] = len(state["processed_episodes"])
    state["total_concepts"] = state.get("total_concepts", 0) + len(data.get("concepts", []))
    state["total_insights"] = state.get("total_insights", 0) + len(data.get("insights", []))
    state["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_state(state)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/graph_linker.py <episode_id>", file=sys.stderr)
        sys.exit(1)

    episode_id = sys.argv[1]
    data = load_tagged(episode_id)

    # Build graph structure
    nodes = build_nodes(data, episode_id)
    edges = build_edges(data, episode_id)

    # Count by type
    nodes_by_type = {}
    for node in nodes:
        t = node["type"]
        nodes_by_type[t] = nodes_by_type.get(t, 0) + 1

    edges_by_type = {}
    for edge in edges:
        key = edge["relation"]
        edges_by_type[key] = edges_by_type.get(key, 0) + 1

    # Detect contradiction candidates
    existing_insights = load_existing_insights()
    contradiction_candidates = detect_contradictions(data, episode_id, existing_insights)

    # Run similarity scoring
    similarity = run_similarity_scorer(episode_id)

    # Build linked output
    linked_output = {
        "episode_id": episode_id,
        "nodes_created": len(nodes),
        "nodes_by_type": nodes_by_type,
        "edges_created": len(edges),
        "edges_by_type": edges_by_type,
        "nodes": nodes,
        "edges": edges,
        "contradictions_found": [],
        "contradiction_candidates": contradiction_candidates,
        "similar_episodes": similarity.get("similar_episodes", []),
    }

    # Save
    LINKED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = LINKED_DIR / f"{episode_id}.json"
    with open(output_path, "w") as f:
        json.dump(linked_output, f, indent=2)

    # Update state
    update_project_state(episode_id, data, nodes, edges)

    # Print summary
    print(f"Linked: {episode_id}")
    print(f"  Nodes: {len(nodes)} ({', '.join(f'{v} {k}' for k, v in nodes_by_type.items())})")
    print(f"  Edges: {len(edges)} ({', '.join(f'{v} {k}' for k, v in edges_by_type.items())})")
    print(f"  Contradiction candidates: {len(contradiction_candidates)}")
    print(f"  Similar episodes: {len(similarity.get('similar_episodes', []))}")
    print(f"  Saved to: {output_path}")


if __name__ == "__main__":
    main()
