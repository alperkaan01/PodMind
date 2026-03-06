Explore the PodMind knowledge graph for a topic, concept, person, or question.

## Input: $ARGUMENTS

If the input is empty, show:
```
Usage:
  /explore <topic>        Explore a topic across all episodes
  /explore <person name>  Find everything about a person
  /explore <concept>      Trace a concept through the graph
  /explore <question>     Answer a question from the knowledge base
```
Then stop.

## Exploration Process

1. Use Memory MCP to search for nodes matching the query:
   - Search for the query terms across all node types
   - Follow relations to find connected nodes

2. Traverse the graph:
   - Episodes that discuss this topic
   - Concepts related to this topic
   - People who spoke about it
   - Books referenced in this context
   - Contradictions involving this topic
   - Themes this connects to

3. For each relevant episode, read the full card from `knowledge-base/episodes/`
   to get detailed insights and quotes.

4. Organize results by relevance:
   - Most directly relevant episodes first
   - Key insights from those episodes
   - Notable quotes on this topic
   - Related concepts to explore further
   - Any contradictions across episodes

## Output Format

```
## [Query Topic]

### Key Episodes
- [Episode title] (relevance: X/10) — [one-line summary of relevance]

### Insights
- [Insight] — from [Episode]

### Notable Quotes
> "[Quote]" — [Speaker], [Episode]

### Related Concepts
- [Concept]: [definition]

### Contradictions
- [Episode A] claims X, but [Episode B] claims Y

### Books & Resources
- [Book] referenced in [Episode]
```

Then ask: "Want me to generate a synthesis note on this topic?"
