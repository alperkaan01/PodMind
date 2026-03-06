Process a podcast episode through the full PodMind pipeline.

## Input: $ARGUMENTS

If the input is empty, show these instructions:
```
Usage:
  /ingest <youtube-url>      Process a YouTube video
  /ingest <podcast-url>      Process a podcast episode page
  /ingest --text <text>      Process pasted transcript text
  /ingest --rss <feed-url>   Find new episodes from RSS feed
```
Then stop.

If input starts with `--rss`, run `python scripts/rss_parser.py <feed-url>` to find
unprocessed episodes, show the list, and ask which to process.

If input starts with `--text`, treat the remaining text as a raw transcript.

Otherwise, treat the input as a URL.

## Pipeline

Run the full 7-agent pipeline in order:

### Step 1: Ingest
Use the **ingest-agent** to fetch and clean the transcript.
Wait for it to report the cleaned file path and episode ID.

### Step 2: Extract
Use the **extraction-agent** with the cleaned transcript path.
Wait for it to report the extracted JSON path and item counts.

### Step 3: Summarize
Use the **summarizer-agent** with the raw transcript and extracted JSON.
This creates a focused summary and deletes the raw transcript.
Wait for it to report the summary path.

### Step 4: Tag
Use the **tagging-agent** with the extracted JSON path.
Wait for it to report the tagged JSON path and scores.

### Step 5: Link
Use the **linker-agent** with the tagged JSON path.
IMPORTANT: This must run sequentially, not in parallel with other linker runs.
Wait for it to report nodes/edges created and contradictions found.

### Step 6: Write Card
Use the **card-writer-agent** with the tagged JSON and linker output paths.
Wait for it to report the card path.

### Step 7: Synthesize
Use the **synthesis-agent** with the episode ID.
This creates/updates concept notes in the knowledge base.
Wait for it to report concepts created/updated.

## After Pipeline Completes

Show a summary:
```
Episode processed: [title]
- Insights extracted: [count]
- New concepts: [list]
- Connections found: [count]
- Contradictions: [count or "none"]
- Relevance score: [score]/10
- Card saved to: [path]
- Concept notes: [X] created, [Y] updated
```

Then ask: "Want to explore any of these connections?"
