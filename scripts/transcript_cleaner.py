#!/usr/bin/env python3
"""Clean a raw transcript file for extraction.

Usage: python scripts/transcript_cleaner.py <file_path>

Removes timestamp artifacts, speaker label noise, filler words at line
boundaries, and duplicate lines from auto-captions. Outputs cleaned text
to the same directory with _clean suffix.
"""

import re
import sys
from pathlib import Path


def clean_transcript(text):
    """Apply all cleaning steps to raw transcript text."""
    lines = text.split("\n")
    cleaned_lines = []

    prev_line = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Remove SRT/VTT timestamp lines (e.g., "00:01:23,456 --> 00:01:25,789")
        if re.match(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->", line):
            continue

        # Remove SRT sequence numbers (standalone integers)
        if re.match(r"^\d+$", line):
            continue

        # Remove VTT header
        if line.startswith("WEBVTT") or line.startswith("Kind:") or line.startswith("Language:"):
            continue

        # Remove inline timestamps like [00:01:23] or (00:01:23)
        line = re.sub(r"[\[\(]\d{1,2}:\d{2}(?::\d{2})?[\]\)]", "", line)

        # Remove HTML tags (from auto-captions)
        line = re.sub(r"<[^>]+>", "", line)

        # Normalize speaker labels: "SPEAKER_01:" -> "Speaker 1:"
        line = re.sub(
            r"^(?:SPEAKER[_\s]?)(\d+)\s*:",
            lambda m: f"Speaker {int(m.group(1))}:",
            line
        )

        # Remove filler words at line boundaries
        # Only remove if they're the entire line or at the very start
        line = re.sub(r"^(?:uh|um|ah|like,?|you know,?|I mean,?)\s+", "", line, flags=re.IGNORECASE)

        # Skip duplicate lines (common in auto-captions)
        if line.lower() == prev_line.lower():
            continue

        line = line.strip()
        if line:
            cleaned_lines.append(line)
            prev_line = line

    return "\n".join(cleaned_lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/transcript_cleaner.py <file_path>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    text = input_path.read_text(encoding="utf-8")
    cleaned = clean_transcript(text)

    # Output to same directory with _clean suffix
    output_path = input_path.parent / f"{input_path.stem}_clean{input_path.suffix}"
    output_path.write_text(cleaned, encoding="utf-8")

    word_count = len(cleaned.split())
    print(f"Cleaned transcript saved to: {output_path}")
    print(f"Word count: {word_count}")


if __name__ == "__main__":
    main()
