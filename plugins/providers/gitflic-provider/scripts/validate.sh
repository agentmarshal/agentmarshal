#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$HERE/../../../.." && pwd)"
HOST_ROOT="$(cd "$FRAMEWORK_ROOT/.." && pwd)"
MANIFEST="$HERE/../plugin.json"
jq -e '
  .schema == 1
  and .api_version == "1"
  and .type == "provider"
  and (.capabilities | index("provider.compare") != null)
  and (.capabilities | index("provider.pipeline") != null)
' "$MANIFEST" >/dev/null
default_ci="$FRAMEWORK_ROOT/scripts/gitflic-ci.sh"
default_scope="$FRAMEWORK_ROOT/scripts/scope-guard-gitflic.sh"
[[ -f "$default_ci" || ! -f "$HOST_ROOT/agentmarshal/scripts/gitflic-ci.sh" ]] \
  || default_ci="$HOST_ROOT/agentmarshal/scripts/gitflic-ci.sh"
[[ -f "$default_scope" || ! -f "$HOST_ROOT/agentmarshal/scripts/scope-guard-gitflic.sh" ]] \
  || default_scope="$HOST_ROOT/agentmarshal/scripts/scope-guard-gitflic.sh"
[[ -f "${AGENTMARSHAL_PROVIDER_GITFLIC_CI_SCRIPT:-$default_ci}" ]] \
  || { echo "gitflic-provider validate: gitflic-ci transport script is missing" >&2; exit 1; }
[[ -f "${AGENTMARSHAL_PROVIDER_GITFLIC_SCOPE_SCRIPT:-$default_scope}" ]] \
  || { echo "gitflic-provider validate: scope-guard transport script is missing" >&2; exit 1; }
echo "gitflic-provider validate: ok"
