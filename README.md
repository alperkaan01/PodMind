# PodMind

PodMind is an interactive, session-persistent podcast knowledge graph agent built with Claude Code. Paste any podcast URL or YouTube link, and it processes the episode through a 5-agent pipeline — extracting insights, quotes, concepts, people, and books — then links them into a persistent knowledge graph you can query conversationally across sessions.

## How It Works

```
                         You paste a URL
                              |
                    +---------v----------+
                    |   /ingest <url>    |
                    +---------+----------+
                              |
              +---------------v----------------+
              |        ingest-agent (Haiku)     |
              |  Fetch transcript, clean text   |
              +---------------+----------------+
                              |
              +---------------v----------------+
              |      extraction-agent (Haiku)   |
              |  Extract insights, quotes,      |
              |  concepts, people, books         |
              +---------------+----------------+
                              |
              +---------------v----------------+
              |       tagging-agent (Haiku)     |
              |  Assign tags, relevance,        |
              |  novelty, complexity scores      |
              +---------------+----------------+
                              |
              +---------------v----------------+
              |       linker-agent (Sonnet)     |
              |  Create Memory MCP nodes,       |
              |  detect contradictions, link     |
              +---------------+----------------+
                              |
              +---------------v----------------+
              |    card-writer-agent (Sonnet)   |
              |  Write polished episode card     |
              +---------------+----------------+
                              |
                    +---------v----------+
                    |  Summary + Graph   |
                    |  "Explore more?"   |
                    +--------------------+
```

## Prerequisites

- [Claude Code](https://claude.com/claude-code) CLI installed
- [pixi](https://pixi.sh) for Python environment management (`curl -fsSL https://pixi.sh/install.sh | sh`)
- `jq` for hook scripts (`brew install jq` on macOS)
- MCP servers:
  - **Memory MCP** — `claude mcp add memory` (persistent knowledge graph)
  - **Fetch MCP** — `claude mcp add fetch` (web scraping)

Optional:
- `yt-dlp` for YouTube transcript extraction (`pixi add --pypi yt-dlp`)

## Setup

```bash
git clone <repo-url> podmind
cd podmind

# Install Python + dependencies (pixi reads pyproject.toml)
pixi install

# Verify it works
pixi run python scripts/graph_analyzer.py

# Add MCP servers
claude mcp add memory
claude mcp add fetch

# Start Claude Code
claude
```

## Usage

### Process an episode

```
/ingest https://www.youtube.com/watch?v=...
```

PodMind fetches the transcript, extracts structured knowledge, tags it,
links it into the graph, and writes an episode card. You get a summary:

```
Episode processed: "How to Build AI Agents"
- Insights extracted: 12
- New concepts: agent loop, tool orchestration, context management
- Connections found: 5
- Contradictions: 1 (vs "LLM Limitations" episode)
- Relevance score: 9/10
- Card saved to: knowledge-base/episodes/yt-how-to-build-ai-20260306.md
```

### Ask cross-episode questions

```
/explore dopamine scheduling
```

Returns all episodes, insights, quotes, and connections related to the topic.

### Generate a weekly digest

```
/digest
```

Summarizes the week's episodes with new concepts, contradictions, and
the most surprising cross-episode connection.

### Process from RSS feed

```
/ingest --rss https://feeds.example.com/podcast.xml
```

Lists unprocessed episodes and asks which to process.

### Process raw text

```
/ingest --text [paste transcript here]
```

## Project Structure — Concept Map

Every file in this project maps to a Claude Code concept:

| File / Directory | Claude Code Concept | Purpose |
|---|---|---|
| `CLAUDE.md` | **Project Memory** | Persistent context loaded every session. Defines personality, taxonomy, interests, commands |
| `.claude/agents/*.md` | **Sub-Agents** | Isolated workers with own context, tools, and model. Each handles one pipeline step |
| `.claude/skills/*/SKILL.md` | **Skills** | Reusable knowledge loaded on demand. Teaches extraction, quoting, cross-referencing |
| `.claude/rules/*.md` | **Rules** | Always-on constraints. No hallucination, extraction fidelity, tag consistency |
| `.claude/commands/*.md` | **Slash Commands** | User-invocable workflows. `/ingest`, `/explore`, `/digest` |
| `.claude/settings.json` | **Hooks** | Deterministic lifecycle callbacks. Validate cards, update state, regenerate graph |
| `.claude/hooks/*.sh` | **Hook Scripts** | Shell scripts that receive JSON stdin, use `jq` to extract fields, exit 2 to block |
| `scripts/*.py` | **Deterministic Scripts** | Python for reliable computation: TF-IDF, graph analysis, validation |
| `knowledge-base/` | **Persistent Storage** | Episode cards, extracted data, state tracking |
| `output/` | **Visualization** | Plotly graph and dashboard HTML |

### Why Haiku vs Sonnet?

| Agent | Model | Reasoning |
|---|---|---|
| ingest-agent | Haiku | Mechanical work: fetch URL, save file. No reasoning needed |
| extraction-agent | Haiku | Pattern matching: text to structured JSON. Fast and accurate |
| tagging-agent | Haiku | Classification against fixed vocabulary. Mechanical scoring |
| linker-agent | Sonnet | Semantic reasoning: contradiction detection, concept relationships |
| card-writer-agent | Sonnet | User-facing prose: writing quality matters |

**Principle:** Match model capability to task complexity. Haiku for mechanical work, Sonnet where reasoning or writing quality matters.

### Why Rules vs Skills vs CLAUDE.md?

- **CLAUDE.md** = "Here's who I am and what I care about" (loaded every session)
- **Rules** = "Never do X" — hard constraints (always enforced)
- **Skills** = "Here's how to do X well" — knowledge loaded on demand

### Why Hooks?

Hooks enforce deterministic behavior in a probabilistic system. Claude might forget to validate a card, but the PostToolUse hook on Write always runs `card_validator.py`. Exit code 2 blocks the write and feeds the error back to Claude to fix.

## Architecture

```
Claude Code Session
    |
    +-- CLAUDE.md (loaded at start)
    +-- .claude/rules/ (always-on constraints)
    |
    +-- /ingest command
    |       |
    |       +-- ingest-agent [Haiku] --> raw transcript
    |       +-- extraction-agent [Haiku] --> structured JSON
    |       +-- tagging-agent [Haiku] --> tagged JSON
    |       +-- linker-agent [Sonnet] --> Memory MCP nodes + edges
    |       +-- card-writer-agent [Sonnet] --> episode card
    |
    +-- /explore command --> Memory MCP queries --> ranked results
    +-- /digest command --> weekly_digest.py --> synthesis note
    |
    +-- Hooks (PostToolUse)
    |       +-- dedup_checker.py (blocks duplicate cards)
    |       +-- card_validator.py (blocks invalid cards)
    |
    +-- Hooks (Stop)
            +-- graph_analyzer.py (regenerates visualization)
```

## Contributing

1. Fork the repo
2. Create a feature branch
3. Follow the existing patterns (agents for pipeline steps, skills for knowledge, rules for constraints)
4. Test that `python scripts/graph_analyzer.py` runs without errors
5. Submit a PR with a description of what Claude Code concept your change uses
