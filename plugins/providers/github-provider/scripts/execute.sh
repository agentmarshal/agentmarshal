#!/usr/bin/env bash
set -euo pipefail

CAPABILITY="${1:-}"
OPERATION="${2:-}"
echo "github-provider: not implemented: ${CAPABILITY}/${OPERATION}" >&2
exit 3
