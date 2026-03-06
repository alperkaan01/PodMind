#!/usr/bin/env python3
"""Fetch a YouTube transcript with video metadata and save as plain text.

Usage: python scripts/fetch_transcript.py <youtube-url-or-id> [output-path]

If output-path is omitted, prints to stdout.
Output includes a metadata header (title, channel, description) followed by
the transcript text, so downstream agents can identify speakers.
"""

import json
import re
import sys
import urllib.request
import urllib.error

from youtube_transcript_api import YouTubeTranscriptApi


def extract_video_id(url_or_id: str) -> str:
    """Extract video ID from various YouTube URL formats or a bare ID."""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/embed/)([a-zA-Z0-9_-]{11})",
        r"^([a-zA-Z0-9_-]{11})$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from: {url_or_id}")


def fetch_metadata(video_id: str) -> dict:
    """Fetch video metadata via YouTube oEmbed (no API key needed)."""
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PodMind/0.1"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return {
                "title": data.get("title", "Unknown"),
                "channel": data.get("author_name", "Unknown"),
            }
    except (urllib.error.URLError, json.JSONDecodeError):
        return {"title": "Unknown", "channel": "Unknown"}


def fetch_transcript(video_id: str, lang: str = "en") -> str:
    """Fetch transcript and return as plain text."""
    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id, languages=[lang, "en"])
    lines = [entry.text for entry in transcript]
    return "\n".join(lines)


def build_output(metadata: dict, transcript: str) -> str:
    """Combine metadata header with transcript text."""
    header = (
        f"--- METADATA ---\n"
        f"Title: {metadata['title']}\n"
        f"Channel: {metadata['channel']}\n"
        f"--- TRANSCRIPT ---\n"
    )
    return header + transcript


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/fetch_transcript.py <youtube-url-or-id> [output-path]", file=sys.stderr)
        sys.exit(1)

    video_id = extract_video_id(sys.argv[1])
    metadata = fetch_metadata(video_id)
    transcript = fetch_transcript(video_id)
    output = build_output(metadata, transcript)

    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        word_count = len(transcript.split())
        print(f"Transcript saved to: {output_path}")
        print(f"Title: {metadata['title']}")
        print(f"Channel: {metadata['channel']}")
        print(f"Video ID: {video_id}")
        print(f"Word count: {word_count}")
    else:
        print(output)


if __name__ == "__main__":
    main()
