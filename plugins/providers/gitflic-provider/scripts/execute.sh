#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$HERE/../../../.." && pwd)"
HOST_ROOT="$(cd "$FRAMEWORK_ROOT/.." && pwd)"
default_ci="$FRAMEWORK_ROOT/scripts/gitflic-ci.sh"
default_scope="$FRAMEWORK_ROOT/scripts/scope-guard-gitflic.sh"
[[ -f "$default_ci" || ! -f "$HOST_ROOT/agentmarshal/scripts/gitflic-ci.sh" ]] \
  || default_ci="$HOST_ROOT/agentmarshal/scripts/gitflic-ci.sh"
[[ -f "$default_scope" || ! -f "$HOST_ROOT/agentmarshal/scripts/scope-guard-gitflic.sh" ]] \
  || default_scope="$HOST_ROOT/agentmarshal/scripts/scope-guard-gitflic.sh"
CI_SCRIPT="${AGENTMARSHAL_PROVIDER_GITFLIC_CI_SCRIPT:-$default_ci}"
SCOPE_SCRIPT="${AGENTMARSHAL_PROVIDER_GITFLIC_SCOPE_SCRIPT:-$default_scope}"

die() {
  echo "gitflic-provider: $*" >&2
  exit 1
}

not_impl() {
  echo "gitflic-provider: capability not implemented: $1/$2" >&2
  exit 3
}

CAPABILITY="${1:-}"
OPERATION="${2:-}"
shift $(( $# >= 2 ? 2 : $# ))

case "$CAPABILITY/$OPERATION" in
  provider.pipeline/list)
    exec bash "$CI_SCRIPT" list "$@"
    ;;
  provider.pipeline/pipeline)
    exec bash "$CI_SCRIPT" pipeline "$@"
    ;;
  provider.pipeline/by-sha)
    exec bash "$CI_SCRIPT" sha "$@"
    ;;
  provider.pipeline/jobs)
    exec bash "$CI_SCRIPT" jobs "$@"
    ;;
  provider.pipeline/job)
    exec bash "$CI_SCRIPT" job "$@"
    ;;
  provider.pipeline/wait)
    exec bash "$CI_SCRIPT" wait "$@"
    ;;
  provider.pipeline/diagnose)
    exec bash "$CI_SCRIPT" diagnose "$@"
    ;;
  provider.compare/scope-guard)
    exec bash "$SCOPE_SCRIPT" "$@"
    ;;
  *)
    not_impl "$CAPABILITY" "$OPERATION"
    ;;
esac
