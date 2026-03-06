#!/usr/bin/env python3
"""Parse an RSS feed and find unprocessed episodes.

Usage: python scripts/rss_parser.py <feed_url>

Compares episodes against knowledge-base/state.json to find new ones.
Outputs JSON list of unprocessed episodes to stdout.
"""

import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from state_utils import load_state


def parse_feed(url):
    """Fetch and parse an RSS feed, returning episode list."""
    req = urllib.request.Request(url, headers={"User-Agent": "PodMind/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        xml_data = resp.read()

    root = ET.fromstring(xml_data)

    # Handle common RSS namespaces
    ns = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}

    episodes = []
    channel = root.find("channel")
    if channel is None:
        print("Error: No <channel> element found in RSS feed.", file=sys.stderr)
        sys.exit(1)

    for item in channel.findall("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        pub_date_el = item.find("pubDate")
        duration_el = item.find("itunes:duration", ns)
        desc_el = item.find("description")

        # Get enclosure URL as fallback for episode link
        enclosure = item.find("enclosure")
        enclosure_url = enclosure.get("url") if enclosure is not None else None

        episode = {
            "title": title_el.text.strip() if title_el is not None and title_el.text else "Untitled",
            "url": link_el.text.strip() if link_el is not None and link_el.text else enclosure_url,
            "date": pub_date_el.text.strip() if pub_date_el is not None and pub_date_el.text else None,
            "duration": duration_el.text.strip() if duration_el is not None and duration_el.text else None,
            "description": desc_el.text.strip()[:500] if desc_el is not None and desc_el.text else None,
        }
        episodes.append(episode)

    return episodes


def filter_unprocessed(episodes, state):
    """Return only episodes not already in state.json."""
    processed_urls = {ep.get("source_url") for ep in state.get("processed_episodes", [])}
    processed_titles = {ep.get("title") for ep in state.get("processed_episodes", [])}

    return [
        ep for ep in episodes
        if ep["url"] not in processed_urls and ep["title"] not in processed_titles
    ]


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/rss_parser.py <feed_url>", file=sys.stderr)
        sys.exit(1)

    feed_url = sys.argv[1]
    state = load_state()

    try:
        episodes = parse_feed(feed_url)
    except Exception as e:
        print(f"Error fetching feed: {e}", file=sys.stderr)
        sys.exit(1)

    new_episodes = filter_unprocessed(episodes, state)

    print(json.dumps({
        "total_in_feed": len(episodes),
        "new_episodes": len(new_episodes),
        "episodes": new_episodes
    }, indent=2))


if __name__ == "__main__":
    main()
