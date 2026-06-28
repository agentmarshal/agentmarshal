#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib/runtime-config.sh"
aops_config_init "$ROOT"

case "${1:-show}" in
  show)
    for key in "${!AOPS_CONFIG[@]}"; do
      printf '%s=%s\n' "$key" "${AOPS_CONFIG[$key]}"
    done | sort
    ;;
  get)
    [[ -n "${2:-}" ]] || { echo "usage: agentmarshal-config.sh get <key>" >&2; exit 2; }
    aops_config_get "$2"
    ;;
  path)
    [[ -n "${2:-}" ]] || { echo "usage: agentmarshal-config.sh path <key>" >&2; exit 2; }
    aops_config_path "$2"
    ;;
  *)
    echo "usage: agentmarshal-config.sh {show|get <key>|path <key>}" >&2
    exit 2
    ;;
esac
