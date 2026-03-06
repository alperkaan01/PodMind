#!/bin/bash
# Stop hook: regenerate graph visualization when Claude finishes.
# Stop hooks don't receive meaningful stdin — they just run.

cd "$CLAUDE_PROJECT_DIR" 2>/dev/null || exit 0

# Regenerate graph via pixi (silently fail if deps not installed)
pixi run python scripts/graph_analyzer.py 2>/dev/null

exit 0
