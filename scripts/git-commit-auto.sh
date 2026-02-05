#!/bin/bash
# Auto-retry git commit after pre-commit hooks modify files
# Usage: ./git-commit-auto.sh "commit message"

MESSAGE="$1"
if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 \"commit message\""
    exit 1
fi

# First attempt
git add -A
if git commit -m "$MESSAGE"; then
    echo "Commit successful!"
    exit 0
fi

# If pre-commit modified files, add them and try again
echo ""
echo "Pre-commit hooks modified files, re-adding and committing..."
git add -A
if git commit -m "$MESSAGE"; then
    echo "Commit successful on retry!"
    exit 0
else
    echo "Commit still failed - check the errors above"
    exit 1
fi
