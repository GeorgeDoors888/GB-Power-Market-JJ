#!/bin/bash
# Quick commit and push without prompts
set -e

if [ -z "$1" ]; then
    echo "Usage: ./quick_commit.sh \"commit message\""
    exit 1
fi

git add -A
git commit -m "$1"
git push

echo "✅ Committed and pushed: $1"
