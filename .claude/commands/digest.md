Generate a weekly digest of all episodes processed in the last 7 days.

## Process

1. Run `python scripts/weekly_digest.py` to generate the digest
2. Read the generated digest from `knowledge-base/synthesis/`
3. If no episodes were processed in the last 7 days, report that

## What the Digest Includes

- Episodes added this week (with one-line summaries)
- New concepts discovered
- Most connected new concept (from graph analysis)
- Contradictions found this week
- Connection of the week (most surprising cross-episode link)

## Output

Display the full digest contents, then report where it was saved.

If the digest reveals interesting patterns, highlight the top 3 most
surprising findings and ask if the user wants to explore any of them.
