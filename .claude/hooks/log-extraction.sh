#!/bin/bash
# PostToolUse hook: log extracted/tagged file writes to state.json.
# Receives JSON on stdin with tool_input.file_path.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only log files in extracted/ or tagged/ directories
case "$FILE_PATH" in
  */knowledge-base/extracted/*.json|*/knowledge-base/tagged/*.json)
    python3 -c "
import json, sys
from datetime import datetime
from pathlib import Path

sf = Path('$CLAUDE_PROJECT_DIR/knowledge-base/state.json')
s = json.loads(sf.read_text()) if sf.exists() else {}
log = s.get('file_log', [])
log.append({'file': '$FILE_PATH', 'timestamp': datetime.now().isoformat()})
s['file_log'] = log
sf.write_text(json.dumps(s, indent=2))
"
    ;;
esac

exit 0
