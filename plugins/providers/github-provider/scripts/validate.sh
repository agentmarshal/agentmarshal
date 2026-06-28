#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
jq -e '.schema == 1 and .api_version == "1" and .type == "provider"' \
  "$HERE/../plugin.json" >/dev/null
jq -e '
  (.capabilities | index("provider.refs") != null)
  and (.capabilities | index("provider.merge_request") != null)
  and (.capabilities | index("provider.compare") != null)
  and (.capabilities | index("provider.pipeline") != null)
' "$HERE/../plugin.json" >/dev/null
echo "github-provider validate: stub"
