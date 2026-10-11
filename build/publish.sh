#!/usr/bin/env bash
# Veröffentlicht dist/release/ als neues GitHub-Release (braucht die GitHub CLI: gh auth login).
# VOID Studio lädt immer aus dem neuesten Release: …/releases/latest/download/index.json
set -euo pipefail
cd "$(dirname "$0")"
V=$(python3 -c "import json;print(json.load(open('versions.json'))['studio'])")
TAG="v$V-$(date +%Y%m%d%H%M)"
gh release create "$TAG" dist/release/* --title "VOID Studio $V" --notes-file dist/release/CHANGELOG.md --latest
