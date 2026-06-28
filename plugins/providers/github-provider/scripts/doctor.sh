#!/usr/bin/env bash
set -euo pipefail
for cmd in bash jq; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "github-provider doctor: required command not found: $cmd" >&2; exit 1; }
done
echo "github-provider doctor: stub"
