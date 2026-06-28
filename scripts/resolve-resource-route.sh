#!/usr/bin/env bash
# resolve-resource-route.sh — deterministic resource-tier resolver.
# Reads a host-owned routing policy and a task request, validates both
# fail-closed, and emits the selected route plus the concrete model/effort.
set -euo pipefail

usage() {
  cat >&2 <<'EOF'
usage: resolve-resource-route.sh --policy POLICY.json [--request REQUEST.json]

If --request is omitted, the request is read from stdin.
Output is JSON on stdout.
EOF
  exit 2
}

die() {
  echo "resolve-resource-route: $*" >&2
  exit 1
}

POLICY=""
REQUEST_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --policy)
      POLICY="${2:-}"
      [[ -n "$POLICY" ]] || usage
      shift 2
      ;;
    --request)
      REQUEST_FILE="${2:-}"
      [[ -n "$REQUEST_FILE" ]] || usage
      shift 2
      ;;
    -h|--help)
      usage
      ;;
    *)
      usage
      ;;
  esac
done

[[ -n "$POLICY" ]] || usage
[[ -f "$POLICY" ]] || die "policy not found: $POLICY"
command -v jq >/dev/null 2>&1 || die "jq is required"

request_tmp=""
cleanup() {
  if [[ -n "$request_tmp" && -f "$request_tmp" ]]; then
    rm -f "$request_tmp"
  fi
  return 0
}
trap cleanup EXIT

if [[ -n "$REQUEST_FILE" ]]; then
  [[ -f "$REQUEST_FILE" ]] || die "request not found: $REQUEST_FILE"
  request_src="$REQUEST_FILE"
else
  request_tmp="$(mktemp)"
  cat > "$request_tmp"
  request_src="$request_tmp"
fi

validate_json() {
  local file="$1" label="$2"
  jq -e . "$file" >/dev/null 2>&1 || die "$label is not valid JSON: $file"
}

validate_json "$POLICY" "policy"
validate_json "$request_src" "request"

jq_check() {
  local expr="$1" message="$2"
  jq -e "$expr" "$POLICY" >/dev/null || die "$message"
}

jq_check 'type == "object" and (keys_unsorted | sort == ["blocked_tier","escalation","routes","schema","vendors"])' \
  "policy failed validation: unexpected root keys"
jq_check '.schema == 1 and .blocked_tier == "operator/blocked"' \
  "policy failed validation: schema or blocked tier mismatch"
jq_check '.escalation | type == "object"' \
  "policy failed validation: escalation block is not an object"
jq_check '.escalation | keys_unsorted | sort == ["chain","triggers"]' \
  "policy failed validation: escalation block has unexpected keys"
jq_check '.escalation.chain == ["economy","standard","critical","operator/blocked"]' \
  "policy failed validation: escalation chain is invalid"
jq_check '.escalation.triggers | type == "array" and length > 0' \
  "policy failed validation: escalation triggers are invalid"
jq_check '(.escalation.triggers | length) == (.escalation.triggers | unique | length)' \
  "policy failed validation: escalation triggers are not unique"
jq_check '(.vendors | type == "object" and length > 0 and all(to_entries[]; (.key | type == "string" and test("^[a-z][a-z0-9-]*$")) and (.value | type == "object" and (keys_unsorted | sort == ["tiers"])) and (.value.tiers | type == "object" and (keys_unsorted | sort == ["critical","economy","standard"]))))' \
  "policy failed validation: vendor block is invalid"
jq_check 'all(.vendors | to_entries[]; all(.value.tiers | to_entries[]; (.key | IN("economy","standard","critical")) and (.value | type == "object" and (keys_unsorted | sort == ["model","reasoning_effort"])) and (.value.model | type == "string" and length > 0) and (.value.reasoning_effort | IN("low","medium","high","max"))))' \
  "policy failed validation: tier specs are invalid"
jq_check '(.routes | type == "array" and length > 0 and all(.[]; (.vendor | type == "string" and test("^[a-z][a-z0-9-]*$")) and (.activity | IN("implementation","review","operations","analysis","documentation","release")) and (.task_class | IN("documentation","ci","frontend","backend","review","operations","security","release","analysis")) and (.difficulty | type == "number" and floor == . and . >= 1 and . <= 5) and (.risk_level | IN("low","medium","high","critical")) and (.tier | IN("economy","standard","critical"))))' \
  "policy failed validation: routes are invalid"
jq_check '((.routes | map([.vendor,.activity,.task_class,.difficulty,.risk_level]) | unique | length) == (.routes | length))' \
  "policy failed validation: duplicate route key"
jq_check '(. as $p | all($p.routes[]; ($p.vendors[.vendor] and $p.vendors[.vendor].tiers[.tier])))' \
  "policy failed validation: route references unknown vendor or tier"

request_check='
  def vendor_name: type == "string" and test("^[a-z][a-z0-9-]*$");
  type == "object"
  and (keys_unsorted | sort == ["activity","difficulty","risk_level","schema","task_class","vendor"])
  and (.schema == 1)
  and (.vendor | vendor_name)
  and (.activity | IN("implementation","review","operations","analysis","documentation","release"))
  and (.task_class | IN("documentation","ci","frontend","backend","review","operations","security","release","analysis"))
  and (.difficulty | type == "number" and floor == . and . >= 1 and . <= 5)
  and (.risk_level | IN("low","medium","high","critical"))
'

jq -e "$request_check" "$request_src" >/dev/null || die "request failed validation"

jq -n --slurpfile policy "$POLICY" --slurpfile request "$request_src" '
  def match_route($request):
    .routes[]
    | select(
        .vendor == $request.vendor
        and .activity == $request.activity
        and .task_class == $request.task_class
        and .difficulty == $request.difficulty
        and .risk_level == $request.risk_level
      );

  ($policy[0]) as $policy
  | ($request[0]) as $request
  | [$policy | match_route($request)] as $matches
  | if ($matches | length) != 1 then
      error("no deterministic route matched the request")
    else
      $matches[0] as $route
      | $policy.vendors[$route.vendor].tiers[$route.tier] as $tier
      | ($policy.escalation.chain | index($route.tier)) as $tier_idx
      | {
          schema: 1,
          route: {
            vendor: $route.vendor,
            activity: $route.activity,
            task_class: $route.task_class,
            difficulty: $route.difficulty,
            risk_level: $route.risk_level,
            tier: $route.tier,
            model: $tier.model,
            reasoning_effort: $tier.reasoning_effort
          },
          requested: {
            model: $tier.model,
            reasoning_effort: $tier.reasoning_effort
          },
          escalation: {
            policy: $policy.escalation.chain,
            blocked_tier: $policy.blocked_tier,
            current_tier: $route.tier,
            next_tier: (
              if $tier_idx == null or ($tier_idx + 1) >= ($policy.escalation.chain | length) then
                $policy.blocked_tier
              else
                $policy.escalation.chain[$tier_idx + 1]
              end
            ),
            required: false,
            trigger: "none"
          }
        }
    end
'
