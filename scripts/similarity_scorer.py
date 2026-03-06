#!/usr/bin/env python3
"""Compute TF-IDF cosine similarity between a new episode and existing ones.

Usage: python scripts/similarity_scorer.py <episode_id>

Loads extracted JSON for the episode and compares against all existing
episode cards. Returns top 5 most similar episodes with scores.
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

EPISODES_DIR = Path("knowledge-base/episodes")
EXTRACTED_DIR = Path("knowledge-base/extracted")

# Common English stop words to exclude from TF-IDF
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "that", "this", "was", "are",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "can", "not", "no", "so", "if",
    "as", "about", "into", "than", "then", "they", "them", "their", "its",
    "he", "she", "we", "you", "i", "my", "me", "our", "your", "his", "her",
    "what", "which", "who", "when", "where", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "only", "very",
    "just", "also", "like", "know", "think", "really", "going", "one", "get",
}


def tokenize(text):
    """Split text into lowercase tokens, removing stop words."""
    words = re.findall(r"[a-z]+", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]


def extract_text_from_json(data):
    """Extract all text content from an extracted JSON structure."""
    parts = []
    for insight in data.get("insights", []):
        parts.append(insight.get("text", ""))
    for concept in data.get("concepts", []):
        parts.append(concept.get("name", ""))
        parts.append(concept.get("definition", ""))
    for quote in data.get("quotes", []):
        parts.append(quote.get("text", ""))
    meta = data.get("episode_metadata", {})
    if meta.get("title"):
        parts.append(meta["title"])
    return " ".join(parts)


def extract_text_from_card(card_text):
    """Extract content from a markdown episode card."""
    # Remove YAML frontmatter
    if card_text.startswith("---"):
        end = card_text.find("---", 3)
        if end != -1:
            card_text = card_text[end + 3:]
    return card_text


def compute_tfidf(documents):
    """Compute TF-IDF vectors for a list of (id, token_list) pairs."""
    # Document frequency: how many documents contain each term
    doc_freq = Counter()
    for _, tokens in documents:
        unique_tokens = set(tokens)
        for token in unique_tokens:
            doc_freq[token] += 1

    n_docs = len(documents)
    vectors = {}

    for doc_id, tokens in documents:
        tf = Counter(tokens)
        total = len(tokens) if tokens else 1
        vector = {}
        for term, count in tf.items():
            # TF: normalized term frequency
            tf_val = count / total
            # IDF: inverse document frequency with smoothing
            idf_val = math.log((1 + n_docs) / (1 + doc_freq[term])) + 1
            vector[term] = tf_val * idf_val
        vectors[doc_id] = vector

    return vectors


def cosine_similarity(vec_a, vec_b):
    """Compute cosine similarity between two sparse vectors (dicts)."""
    # Dot product
    common_terms = set(vec_a.keys()) & set(vec_b.keys())
    dot = sum(vec_a[t] * vec_b[t] for t in common_terms)

    # Magnitudes
    mag_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    mag_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/similarity_scorer.py <episode_id>", file=sys.stderr)
        sys.exit(1)

    episode_id = sys.argv[1]

    # Load the new episode's extracted JSON
    extracted_path = EXTRACTED_DIR / f"{episode_id}.json"
    if not extracted_path.exists():
        print(f"Error: Extracted JSON not found: {extracted_path}", file=sys.stderr)
        sys.exit(1)

    with open(extracted_path) as f:
        new_episode_data = json.load(f)

    new_text = extract_text_from_json(new_episode_data)
    new_tokens = tokenize(new_text)

    if not new_tokens:
        print(json.dumps({"episode_id": episode_id, "similar_episodes": []}))
        return

    # Load all existing episode cards
    documents = [("__new__", new_tokens)]

    if EPISODES_DIR.exists():
        for card_path in EPISODES_DIR.glob("*.md"):
            card_id = card_path.stem
            if card_id == episode_id:
                continue
            card_text = card_path.read_text(encoding="utf-8")
            tokens = tokenize(extract_text_from_card(card_text))
            if tokens:
                documents.append((card_id, tokens))

    if len(documents) < 2:
        print(json.dumps({
            "episode_id": episode_id,
            "similar_episodes": [],
            "message": "No existing episodes to compare against"
        }))
        return

    # Compute TF-IDF and similarities
    vectors = compute_tfidf(documents)
    new_vec = vectors["__new__"]

    similarities = []
    for doc_id, vec in vectors.items():
        if doc_id == "__new__":
            continue
        score = cosine_similarity(new_vec, vec)
        similarities.append({"episode_id": doc_id, "similarity": round(score, 4)})

    # Sort by similarity, take top 5
    similarities.sort(key=lambda x: x["similarity"], reverse=True)
    top_5 = similarities[:5]

    print(json.dumps({
        "episode_id": episode_id,
        "compared_against": len(documents) - 1,
        "similar_episodes": top_5
    }, indent=2))


if __name__ == "__main__":
    main()
