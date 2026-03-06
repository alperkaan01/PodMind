#!/bin/bash
# PostToolUse hook: validate episode cards after Write.
# Receives JSON on stdin with tool_input.file_path.
# Exit 2 = block the write and feed error back to Claude.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only validate files in knowledge-base/episodes/
case "$FILE_PATH" in
  */knowledge-base/episodes/*.md)
    # Check for duplicates
    python3 "$CLAUDE_PROJECT_DIR/scripts/dedup_checker.py" "$FILE_PATH"
    if [ $? -eq 2 ]; then
      exit 2
    fi

    # Validate card structure
    python3 "$CLAUDE_PROJECT_DIR/scripts/card_validator.py" "$FILE_PATH"
    if [ $? -eq 2 ]; then
      exit 2
    fi
    ;;
esac

exit 0
