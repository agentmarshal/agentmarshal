#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$HERE/../plugin.json"
jq -e '
  .schema == 1
  and .api_version == "1"
  and .type == "provider"
  and (.capabilities | index("provider.refs") != null)
  and (.capabilities | index("provider.merge_request") != null)
  and (.capabilities | index("provider.compare") != null)
  and (.capabilities | index("provider.pipeline") != null)
' "$MANIFEST" >/dev/null
echo "mock-provider validate: ok"
