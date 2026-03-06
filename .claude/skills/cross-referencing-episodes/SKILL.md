---
name: cross-referencing-episodes
description: Finds non-obvious connections between episodes in the knowledge graph. Use when linking a new episode to the Memory MCP knowledge graph.
---

# Cross-Referencing Episodes

Find connections that aren't obvious from keywords alone. The goal is to
surface surprising links — two episodes that discuss the same underlying
principle from completely different angles.

## What Counts as a Genuine Connection

- Same concept applied in different domains
- Contradicting claims about the same topic
- Same person referenced in different contexts
- Complementary frameworks that combine into something richer
- A claim in one episode that provides evidence for another

## What is NOT a Genuine Connection

- Both episodes mention a common word ("AI", "growth", "learning")
- Same guest appeared on both podcasts
- Both episodes are about the same broad topic
- Surface-level keyword overlap without conceptual link

## How to Find Connections

1. Use `Memory:search_nodes` to find concepts related to the new episode
2. For each matching concept, use `Memory:open_nodes` to get full context
3. Compare the new episode's claims/insights with existing ones
4. Run `python scripts/similarity_scorer.py [episode_id]` for TF-IDF similarity
5. Use `Memory:create_relations` to link nodes with descriptive edge labels

## Edge Labels

Use descriptive relation types:
- `supports` — evidence reinforces an existing claim
- `contradicts` — directly conflicts with an existing claim
- `extends` — builds on an existing concept
- `applies_in` — same concept used in a different domain
- `references` — mentions the same person/book/idea

## Phrasing Connections in Cards

In episode cards, phrase connections as insights:
- "This contradicts [Person]'s claim in [Episode] that..."
- "This extends the concept of [X] first discussed in [Episode]..."
- "Surprising link: [Episode A]'s framework for X applies directly to Y in this episode"
