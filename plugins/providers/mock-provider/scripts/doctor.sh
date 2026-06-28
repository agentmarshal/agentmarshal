#!/usr/bin/env bash
set -euo pipefail

command -v bash >/dev/null 2>&1 || { echo "mock-provider doctor: bash is required" >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "mock-provider doctor: jq is required" >&2; exit 1; }
echo "mock-provider doctor: ok"
