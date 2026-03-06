#!/usr/bin/env python3
"""Analyze the knowledge graph and generate visualizations.

Usage: python scripts/graph_analyzer.py

Loads episode data from knowledge-base/, builds a NetworkX graph,
computes centrality metrics, and generates interactive Plotly
visualizations in output/.
"""

import json
import sys
from pathlib import Path

try:
    import networkx as nx
    import plotly.graph_objects as go
except ImportError:
    print("Missing dependencies. Run: pixi install", file=sys.stderr)
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from state_utils import STATE_FILE, load_state, save_state
EPISODES_DIR = Path("knowledge-base/episodes")
TAGGED_DIR = Path("knowledge-base/tagged")
LINKED_DIR = Path("knowledge-base/linked")
OUTPUT_DIR = Path("output")


def load_graph_data():
    """Load all tagged and linked JSON files to build graph."""
    nodes = []  # (id, type, label, metadata)
    edges = []  # (source, target, relation)

    # Load from tagged files
    if TAGGED_DIR.exists():
        for tagged_file in TAGGED_DIR.glob("*.json"):
            with open(tagged_file) as f:
                data = json.load(f)

            ep_id = data.get("episode_id", tagged_file.stem)
            title = data.get("episode_metadata", {}).get("title", ep_id)
            tags = data.get("tags", [])

            nodes.append((ep_id, "Episode", title, {"tags": tags}))

            for concept in data.get("concepts", []):
                c_id = f"concept:{concept['name']}"
                nodes.append((c_id, "Concept", concept["name"], {"definition": concept.get("definition", "")}))
                edges.append((ep_id, c_id, "contains"))

            for i, insight in enumerate(data.get("insights", [])):
                i_id = f"insight:{ep_id}:{i}"
                nodes.append((i_id, "Insight", insight["text"][:50], {}))
                edges.append((ep_id, i_id, "contains"))

    # Load from linked files for additional relations
    if LINKED_DIR.exists():
        for linked_file in LINKED_DIR.glob("*.json"):
            with open(linked_file) as f:
                data = json.load(f)

            for conn in data.get("new_connections", []):
                if "source" in conn and "target" in conn:
                    edges.append((conn["source"], conn["target"], conn.get("relation", "relates_to")))

            for contradiction in data.get("contradictions_found", []):
                c_id = f"contradiction:{linked_file.stem}:{contradiction.get('id', 0)}"
                nodes.append((c_id, "Contradiction", contradiction.get("summary", "")[:50], {}))

    return nodes, edges


def build_graph(nodes, edges):
    """Build a NetworkX DiGraph from nodes and edges."""
    G = nx.DiGraph()

    # Deduplicate nodes by ID
    seen = set()
    for node_id, node_type, label, metadata in nodes:
        if node_id not in seen:
            G.add_node(node_id, type=node_type, label=label, **metadata)
            seen.add(node_id)

    for source, target, relation in edges:
        if source in G.nodes and target in G.nodes:
            G.add_edge(source, target, relation=relation)

    return G


def compute_stats(G):
    """Compute graph statistics."""
    stats = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "node_types": {},
        "hub_concepts": [],
        "contradictions": 0,
    }

    # Count by type
    for _, data in G.nodes(data=True):
        t = data.get("type", "Unknown")
        stats["node_types"][t] = stats["node_types"].get(t, 0) + 1

    stats["contradictions"] = stats["node_types"].get("Contradiction", 0)

    # Find hub concepts (highest degree)
    if G.number_of_nodes() > 0:
        degree = dict(G.degree())
        concept_degrees = [
            (node, deg) for node, deg in degree.items()
            if G.nodes[node].get("type") == "Concept"
        ]
        concept_degrees.sort(key=lambda x: x[1], reverse=True)
        stats["hub_concepts"] = [
            {"name": G.nodes[n].get("label", n), "connections": d}
            for n, d in concept_degrees[:5]
        ]

    # Betweenness centrality for top nodes
    if G.number_of_nodes() > 1:
        try:
            bc = nx.betweenness_centrality(G)
            top_bc = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:5]
            stats["top_betweenness"] = [
                {"name": G.nodes[n].get("label", n), "score": round(s, 4)}
                for n, s in top_bc
            ]
        except Exception:
            stats["top_betweenness"] = []

    return stats


def generate_graph_html(G, output_path):
    """Generate interactive Plotly graph visualization."""
    if G.number_of_nodes() == 0:
        output_path.write_text(
            "<html><body><h1>PodMind Knowledge Graph</h1>"
            "<p>No nodes yet. Process some episodes first!</p></body></html>"
        )
        return

    # Layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

    # Color map by node type
    color_map = {
        "Episode": "#9b59b6",      # purple
        "Concept": "#f39c12",      # amber
        "Person": "#2ecc71",       # green
        "Book": "#e74c3c",         # red
        "Insight": "#3498db",      # blue
        "Quote": "#1abc9c",        # teal
        "Contradiction": "#e67e22", # orange
        "Theme": "#2980b9",        # dark blue
    }

    # Edge relation colors
    edge_color_map = {
        "contains": "#cccccc",
        "features": "#2ecc71",
        "references": "#e74c3c",
        "relates_to": "#f39c12",
        "contradicts": "#e67e22",
        "supports": "#3498db",
        "extends": "#9b59b6",
    }

    # Build edge traces
    edge_traces = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        relation = data.get("relation", "relates_to")
        color = edge_color_map.get(relation, "#cccccc")
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=0.5, color=color),
            hoverinfo="none",
            showlegend=False,
        ))

    # Build node traces (one per type for legend)
    node_traces = {}
    degree_dict = dict(G.degree())

    for node, data in G.nodes(data=True):
        node_type = data.get("type", "Unknown")
        if node_type not in node_traces:
            node_traces[node_type] = {"x": [], "y": [], "text": [], "size": []}

        x, y = pos[node]
        label = data.get("label", node)
        degree = degree_dict.get(node, 1)
        # Node size: base 8, scaled by degree (more connections = bigger)
        size = 8 + min(degree * 3, 40)  # cap at 48

        node_traces[node_type]["x"].append(x)
        node_traces[node_type]["y"].append(y)
        node_traces[node_type]["text"].append(f"{label}<br>Type: {node_type}<br>Connections: {degree}")
        node_traces[node_type]["size"].append(size)

    fig = go.Figure()

    for trace in edge_traces:
        fig.add_trace(trace)

    for node_type, trace_data in node_traces.items():
        color = color_map.get(node_type, "#95a5a6")
        fig.add_trace(go.Scatter(
            x=trace_data["x"],
            y=trace_data["y"],
            mode="markers",
            marker=dict(size=trace_data["size"], color=color, line=dict(width=1, color="#ffffff")),
            text=trace_data["text"],
            hoverinfo="text",
            name=node_type,
        ))

    fig.update_layout(
        title="PodMind Knowledge Graph",
        showlegend=True,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#1a1a2e",
        paper_bgcolor="#1a1a2e",
        font=dict(color="#e0e0e0"),
        legend=dict(bgcolor="rgba(0,0,0,0.5)"),
        margin=dict(l=0, r=0, t=40, b=0),
    )

    fig.write_html(str(output_path), include_plotlyjs="cdn")


def generate_dashboard_html(G, stats, output_path):
    """Generate a dashboard HTML with graph stats and lists."""
    node_types = stats.get("node_types", {})
    hub_concepts = stats.get("hub_concepts", [])

    # Collect lists
    concepts = sorted([
        G.nodes[n].get("label", n)
        for n in G.nodes if G.nodes[n].get("type") == "Concept"
    ])
    people = sorted([
        G.nodes[n].get("label", n)
        for n in G.nodes if G.nodes[n].get("type") == "Person"
    ])
    episodes = sorted([
        G.nodes[n].get("label", n)
        for n in G.nodes if G.nodes[n].get("type") == "Episode"
    ])

    concepts_html = "".join(f"<li>{c}</li>" for c in concepts) or "<li>None yet</li>"
    people_html = "".join(f"<li>{p}</li>" for p in people) or "<li>None yet</li>"
    episodes_html = "".join(f"<li>{e}</li>" for e in episodes) or "<li>None yet</li>"
    hubs_html = "".join(
        f"<li><strong>{h['name']}</strong> ({h['connections']} connections)</li>"
        for h in hub_concepts
    ) or "<li>None yet</li>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<title>PodMind Dashboard</title>
<style>
  body {{ font-family: -apple-system, sans-serif; background: #1a1a2e; color: #e0e0e0; margin: 0; padding: 20px; }}
  .grid {{ display: grid; grid-template-columns: 250px 1fr; gap: 20px; height: calc(100vh - 40px); }}
  .sidebar {{ overflow-y: auto; }}
  .main {{ display: flex; flex-direction: column; }}
  .graph-frame {{ flex: 1; border: 1px solid #333; border-radius: 8px; overflow: hidden; }}
  .graph-frame iframe {{ width: 100%; height: 100%; border: none; }}
  h1 {{ color: #f39c12; margin-top: 0; }}
  h2 {{ color: #9b59b6; font-size: 14px; text-transform: uppercase; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ padding: 4px 0; border-bottom: 1px solid #333; font-size: 13px; }}
  .stat {{ display: inline-block; background: #16213e; padding: 8px 16px; border-radius: 6px; margin: 4px; }}
  .stat-value {{ font-size: 24px; font-weight: bold; color: #f39c12; }}
  .stat-label {{ font-size: 11px; text-transform: uppercase; color: #888; }}
</style>
</head>
<body>
<h1>PodMind Dashboard</h1>
<div style="margin-bottom:16px">
  <span class="stat"><span class="stat-value">{stats['total_nodes']}</span><br><span class="stat-label">Nodes</span></span>
  <span class="stat"><span class="stat-value">{stats['total_edges']}</span><br><span class="stat-label">Edges</span></span>
  <span class="stat"><span class="stat-value">{node_types.get('Episode', 0)}</span><br><span class="stat-label">Episodes</span></span>
  <span class="stat"><span class="stat-value">{node_types.get('Concept', 0)}</span><br><span class="stat-label">Concepts</span></span>
  <span class="stat"><span class="stat-value">{stats['contradictions']}</span><br><span class="stat-label">Contradictions</span></span>
</div>
<div class="grid">
  <div class="sidebar">
    <h2>Hub Concepts</h2>
    <ul>{hubs_html}</ul>
    <h2>All Concepts ({len(concepts)})</h2>
    <ul>{concepts_html}</ul>
    <h2>People ({len(people)})</h2>
    <ul>{people_html}</ul>
    <h2>Episodes ({len(episodes)})</h2>
    <ul>{episodes_html}</ul>
  </div>
  <div class="main">
    <div class="graph-frame">
      <iframe src="graph.html"></iframe>
    </div>
  </div>
</div>
</body>
</html>"""

    output_path.write_text(html)


def update_state(stats):
    """Update state.json with latest graph stats."""
    state = load_state()

    state["graph_stats"] = {
        "total_nodes": stats["total_nodes"],
        "total_edges": stats["total_edges"],
        "hub_concepts": [h["name"] for h in stats.get("hub_concepts", [])],
    }

    save_state(state)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TAGGED_DIR.mkdir(parents=True, exist_ok=True)
    LINKED_DIR.mkdir(parents=True, exist_ok=True)

    nodes, edges = load_graph_data()
    G = build_graph(nodes, edges)
    stats = compute_stats(G)

    generate_graph_html(G, OUTPUT_DIR / "graph.html")
    generate_dashboard_html(G, stats, OUTPUT_DIR / "dashboard.html")
    update_state(stats)

    print(f"Graph stats:")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  Total edges: {stats['total_edges']}")
    for node_type, count in stats.get("node_types", {}).items():
        print(f"  {node_type}: {count}")
    if stats.get("hub_concepts"):
        print(f"  Top hub concepts: {', '.join(h['name'] for h in stats['hub_concepts'])}")
    print(f"  Contradictions: {stats['contradictions']}")
    print(f"\nGenerated: output/graph.html, output/dashboard.html")


if __name__ == "__main__":
    main()
