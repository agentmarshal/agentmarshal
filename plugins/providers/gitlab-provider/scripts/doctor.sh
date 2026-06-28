#!/usr/bin/env bash
set -euo pipefail
for cmd in bash jq; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "gitlab-provider doctor: required command not found: $cmd" >&2; exit 1; }
done
echo "gitlab-provider doctor: stub"
