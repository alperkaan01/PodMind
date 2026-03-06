#!/usr/bin/env python3
"""Validate an episode card has all required sections and content.

Usage: python scripts/card_validator.py <card_path>

Exit code 0 = valid card
Exit code 2 = invalid (blocks the write, feeds error to Claude)
"""

import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "Summary",
    "Key Insights",
    "Notable Quotes",
    "Concepts Covered",
    "Cross-Episode Connections",
]

# Minimum 3 insights required
MIN_INSIGHTS = 3
# Minimum 1 quote required
MIN_QUOTES = 1
# Minimum 2 tags required
MIN_TAGS = 2


def extract_frontmatter(card_text):
    """Extract frontmatter key-value pairs."""
    if not card_text.startswith("---"):
        return {}
    end = card_text.find("---", 3)
    if end == -1:
        return {}
    fm = card_text[3:end].strip()
    result = {}
    for line in fm.split("\n"):
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


def find_sections(card_text):
    """Find all ## sections and their content."""
    sections = {}
    current_section = None
    current_content = []

    for line in card_text.split("\n"):
        if line.startswith("## "):
            if current_section:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = line[3:].strip()
            current_content = []
        elif current_section:
            current_content.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def count_list_items(section_text):
    """Count bullet points or numbered items in a section."""
    items = re.findall(r"^\s*(?:[-*]|\d+\.)\s+.+", section_text, re.MULTILINE)
    return len(items)


def count_blockquotes(section_text):
    """Count blockquote entries in a section."""
    quotes = re.findall(r"^>\s+.+", section_text, re.MULTILINE)
    return len(quotes)


def validate(card_path):
    """Validate card and return list of errors."""
    errors = []
    card_text = card_path.read_text(encoding="utf-8")

    # Check frontmatter exists
    if not card_text.startswith("---"):
        errors.append("Missing YAML frontmatter (must start with ---)")
        return errors

    frontmatter = extract_frontmatter(card_text)

    # Check tags
    tags_str = frontmatter.get("tags", "")
    # Parse tags from YAML list format: [tag1, tag2] or tag1, tag2
    tags_str = tags_str.strip("[]")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else []
    if len(tags) < MIN_TAGS:
        errors.append(f"Need at least {MIN_TAGS} tags in frontmatter, found {len(tags)}")

    # Check required sections
    sections = find_sections(card_text)
    for required in REQUIRED_SECTIONS:
        if required not in sections:
            errors.append(f"Missing required section: ## {required}")
        elif not sections[required].strip():
            errors.append(f"Section '## {required}' is empty")

    # Check minimum insights
    if "Key Insights" in sections:
        insight_count = count_list_items(sections["Key Insights"])
        if insight_count < MIN_INSIGHTS:
            errors.append(f"Need at least {MIN_INSIGHTS} insights, found {insight_count}")

    # Check minimum quotes
    if "Notable Quotes" in sections:
        quote_count = count_blockquotes(sections["Notable Quotes"])
        if quote_count < MIN_QUOTES:
            errors.append(f"Need at least {MIN_QUOTES} quote, found {quote_count}")

    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/card_validator.py <card_path>", file=sys.stderr)
        sys.exit(1)

    card_path = Path(sys.argv[1])

    if not card_path.exists():
        print(f"Error: File not found: {card_path}", file=sys.stderr)
        sys.exit(2)

    errors = validate(card_path)

    if errors:
        print("Card validation FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)

    print(f"Card validation passed: {card_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
