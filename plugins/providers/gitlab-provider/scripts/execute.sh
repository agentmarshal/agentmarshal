#!/usr/bin/env bash
set -euo pipefail

CAPABILITY="${1:-}"
OPERATION="${2:-}"
echo "gitlab-provider: not implemented: ${CAPABILITY}/${OPERATION}" >&2
exit 3
