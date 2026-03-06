---
name: extracting-concepts
description: Extracts key concepts, frameworks, and principles from podcast transcripts. Use when processing any episode transcript to identify reusable knowledge nodes.
---

# Extracting Concepts

A concept is a named idea with explanatory power beyond a single episode.
It should be reusable — something you'd reference when thinking about
other topics.

## What IS a Concept

- Named framework, model, or principle with a specific meaning
- Has explanatory power — helps you understand other things
- Transferable across domains or episodes
- Examples: "dopamine scheduling", "probabilistic thinking", "build in public"

## What is NOT a Concept

- Episode-specific anecdotes or stories
- Generic advice without a name ("work hard", "be consistent")
- Proper nouns without conceptual weight (company names, place names)
- Vague categories ("technology", "success")

## Extraction Process

1. Read transcript looking for named ideas, frameworks, principles
2. For each candidate, ask: "Would this be useful in a different context?"
3. If yes, extract it with a one-sentence definition
4. Check against Memory MCP for existing concepts — link, don't duplicate

## Output Format

Each concept should have:
- `name`: short identifier (2-4 words, lowercase)
- `definition`: one sentence explaining what it means
- `source_context`: the transcript passage where it appeared
- `related_concepts`: links to existing concepts in the graph

For detailed good/bad examples, see [examples.md](examples.md).
