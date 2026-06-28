#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/provider-spi.sh"

usage() {
  cat <<'EOF'
Usage: agentmarshal/providers/dispatch.sh [--provider <name>] --capability <capability> --operation <operation> [args...]

If --provider is omitted, dispatch reads provider.default from host
.agentmarshal/project.json.
EOF
}

PROVIDER=""
CAPABILITY=""
OPERATION=""
PROJECT_ROOT_ARG=""
PROJECT_CONFIG_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider) PROVIDER="${2:?}"; shift 2 ;;
    --capability) CAPABILITY="${2:?}"; shift 2 ;;
    --operation) OPERATION="${2:?}"; shift 2 ;;
    --project-root) PROJECT_ROOT_ARG="${2:?}"; shift 2 ;;
    --project-config) PROJECT_CONFIG_ARG="${2:?}"; shift 2 ;;
    -h|--help|help)
      usage
      exit 0
      ;;
    --)
      shift
      break
      ;;
    *)
      break
      ;;
  esac
done

if [[ -z "$PROVIDER" ]]; then
  PROVIDER="$(aops_provider_default_from_project "$PROJECT_ROOT_ARG" "$PROJECT_CONFIG_ARG")"
fi

[[ -n "$PROVIDER" && -n "$CAPABILITY" && -n "$OPERATION" ]] || {
  usage >&2
  exit 2
}

aops_provider_dispatch "$PROVIDER" "$CAPABILITY" "$OPERATION" "$@"
