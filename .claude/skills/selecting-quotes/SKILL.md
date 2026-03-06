---
name: selecting-quotes
description: Selects high-value verbatim quotes from podcast transcripts with timestamps. Use when a transcript contains direct speech worth preserving precisely.
---

# Selecting Quotes

Select quotes that capture a complete, surprising, or precisely stated idea
in 1-2 sentences. The quote should be worth saving on its own — no context needed.

## Quality Bar

A good quote is:
- A complete idea in 1-2 sentences
- Surprising, counter-intuitive, or precisely stated
- Defines a concept clearly, or makes a bold claim
- Stands alone without needing episode context

A bad quote is:
- Requires surrounding context to make sense
- Motivational filler ("believe in yourself")
- Over 3 sentences long
- A question without the answer

## Selection Process

1. Scan transcript for moments of clarity, surprise, or precision
2. Extract the exact text — verbatim, no paraphrasing
3. Include speaker name and timestamp (if available)
4. Validate: does this quote pass the quality bar above?
5. If borderline, skip it — fewer good quotes beats many mediocre ones

## Output Format

Each quote requires:
- `text`: verbatim quote (1-2 sentences)
- `speaker`: who said it
- `timestamp`: MM:SS or null if unavailable
- `context`: one-line note on what prompted the quote

For detailed good/bad examples, see [examples.md](examples.md).
