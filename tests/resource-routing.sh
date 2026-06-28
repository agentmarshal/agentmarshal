#!/usr/bin/env bash
# resource-routing.sh — bash+jq tests for deterministic resource-aware routing.
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$TEST_DIR/../scripts" && -d "$TEST_DIR/../schemas" ]]; then
  FRAMEWORK_ROOT="$(cd "$TEST_DIR/.." && pwd)"
else
  FRAMEWORK_ROOT="$(cd "$TEST_DIR/../.." && pwd)/agentmarshal"
fi
SCRIPT="$FRAMEWORK_ROOT/scripts/resolve-resource-route.sh"
SCHEMA="$FRAMEWORK_ROOT/schemas/resource-routing.schema.json"

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

pass=0
fail=0

ok() {
  printf '  ✅ %s\n' "$1"
  pass=$((pass + 1))
}

bad() {
  printf '  ❌ %s\n' "$1"
  fail=$((fail + 1))
}

assert_ok() {
  local desc="$1"
  shift
  if "$@" >/tmp/resource-routing.$$ 2>&1; then
    ok "$desc"
  else
    bad "$desc"
    sed 's/^/      /' /tmp/resource-routing.$$ | tail -8
  fi
}

assert_fail() {
  local desc="$1"
  shift
  if "$@" >/tmp/resource-routing.$$ 2>&1; then
    bad "$desc"
    sed 's/^/      /' /tmp/resource-routing.$$ | tail -8
  else
    ok "$desc"
  fi
}

test -x "$SCRIPT"
test -f "$SCHEMA"

policy="$tmpdir/policy.json"
cat > "$policy" <<'EOF'
{
  "schema": 1,
  "blocked_tier": "operator/blocked",
  "escalation": {
    "chain": ["economy", "standard", "critical", "operator/blocked"],
    "triggers": [
      "failed_acceptance",
      "pipeline_failed",
      "blocking_finding",
      "retry_budget_exhausted",
      "repeated_ambiguity",
      "scope_provenance_violation",
      "insufficient_confidence",
      "quality_gate_failed"
    ]
  },
  "vendors": {
    "codex": {
      "tiers": {
        "economy": {
          "model": "fixture-codex-economy",
          "reasoning_effort": "low"
        },
        "standard": {
          "model": "fixture-codex-standard",
          "reasoning_effort": "medium"
        },
        "critical": {
          "model": "fixture-codex-critical",
          "reasoning_effort": "high"
        }
      }
    },
    "claude": {
      "tiers": {
        "economy": {
          "model": "fixture-claude-economy",
          "reasoning_effort": "low"
        },
        "standard": {
          "model": "fixture-claude-standard",
          "reasoning_effort": "medium"
        },
        "critical": {
          "model": "fixture-claude-critical",
          "reasoning_effort": "max"
        }
      }
    }
  },
  "routes": [
    {
      "vendor": "codex",
      "activity": "documentation",
      "task_class": "documentation",
      "difficulty": 1,
      "risk_level": "low",
      "tier": "economy"
    },
    {
      "vendor": "codex",
      "activity": "implementation",
      "task_class": "backend",
      "difficulty": 3,
      "risk_level": "medium",
      "tier": "standard"
    },
    {
      "vendor": "claude",
      "activity": "review",
      "task_class": "security",
      "difficulty": 5,
      "risk_level": "critical",
      "tier": "critical"
    }
  ]
}
EOF

request1="$tmpdir/request1.json"
cat > "$request1" <<'EOF'
{
  "schema": 1,
  "vendor": "codex",
  "activity": "documentation",
  "task_class": "documentation",
  "difficulty": 1,
  "risk_level": "low"
}
EOF

request2="$tmpdir/request2.json"
cat > "$request2" <<'EOF'
{
  "schema": 1,
  "vendor": "codex",
  "activity": "implementation",
  "task_class": "backend",
  "difficulty": 3,
  "risk_level": "medium"
}
EOF

request3="$tmpdir/request3.json"
cat > "$request3" <<'EOF'
{
  "schema": 1,
  "vendor": "claude",
  "activity": "review",
  "task_class": "security",
  "difficulty": 5,
  "risk_level": "critical"
}
EOF

assert_ok "policy schema is present" jq -e '
  .schema == 1
  and .blocked_tier == "operator/blocked"
  and .escalation.chain == ["economy","standard","critical","operator/blocked"]
  and .vendors.codex.tiers.standard.model == "fixture-codex-standard"
' "$policy"

out1="$tmpdir/out1.json"
if bash "$SCRIPT" --policy "$policy" < "$request1" > "$out1"; then
  ok "economy route resolves from stdin"
else
  bad "economy route resolves from stdin"
  sed 's/^/      /' /tmp/resource-routing.$$ | tail -8
fi
jq -e '
  .schema == 1
  and .route.tier == "economy"
  and .route.model == "fixture-codex-economy"
  and .route.reasoning_effort == "low"
  and .requested.model == "fixture-codex-economy"
  and .requested.reasoning_effort == "low"
  and .escalation.current_tier == "economy"
  and .escalation.next_tier == "standard"
  and .escalation.policy == ["economy","standard","critical","operator/blocked"]
' "$out1" >/dev/null && ok "economy output carries route + requested + escalation"

out2="$tmpdir/out2.json"
if bash "$SCRIPT" --policy "$policy" --request "$request2" > "$out2"; then
  ok "standard route resolves from file input"
else
  bad "standard route resolves from file input"
  sed 's/^/      /' /tmp/resource-routing.$$ | tail -8
fi
jq -e '
  .route.tier == "standard"
  and .route.model == "fixture-codex-standard"
  and .route.reasoning_effort == "medium"
  and .requested.model == "fixture-codex-standard"
  and .escalation.next_tier == "critical"
' "$out2" >/dev/null && ok "standard output uses the policy model and effort"

out3="$tmpdir/out3.json"
if bash "$SCRIPT" --policy "$policy" --request "$request3" > "$out3"; then
  ok "critical route resolves with max effort"
else
  bad "critical route resolves with max effort"
  sed 's/^/      /' /tmp/resource-routing.$$ | tail -8
fi
jq -e '
  .route.tier == "critical"
  and .route.model == "fixture-claude-critical"
  and .route.reasoning_effort == "max"
  and .requested.reasoning_effort == "max"
  and .escalation.next_tier == "operator/blocked"
' "$out3" >/dev/null && ok "critical output marks blocked escalation target"

missing_route="$tmpdir/missing-route.json"
cat > "$missing_route" <<'EOF'
{
  "schema": 1,
  "vendor": "codex",
  "activity": "analysis",
  "task_class": "analysis",
  "difficulty": 2,
  "risk_level": "low"
}
EOF
assert_fail "unknown route is rejected" bash "$SCRIPT" --policy "$policy" --request "$missing_route"

bad_request="$tmpdir/bad-request.json"
cat > "$bad_request" <<'EOF'
{
  "schema": 1,
  "vendor": "codex",
  "activity": "implementation",
  "task_class": "backend",
  "difficulty": 6,
  "risk_level": "medium"
}
EOF
assert_fail "invalid request difficulty is rejected" bash "$SCRIPT" --policy "$policy" --request "$bad_request"

bad_policy_tier="$tmpdir/bad-policy-tier.json"
cat > "$bad_policy_tier" <<'EOF'
{
  "schema": 1,
  "blocked_tier": "operator/blocked",
  "escalation": {
    "chain": ["economy", "standard", "critical", "operator/blocked"],
    "triggers": ["quality_gate_failed"]
  },
  "vendors": {
    "codex": {
      "tiers": {
        "economy": {"model": "fixture", "reasoning_effort": "low"},
        "standard": {"model": "fixture", "reasoning_effort": "medium"},
        "critical": {"model": "fixture", "reasoning_effort": "high"}
      }
    }
  },
  "routes": [
    {
      "vendor": "codex",
      "activity": "implementation",
      "task_class": "backend",
      "difficulty": 3,
      "risk_level": "medium",
      "tier": "economy"
    },
    {
      "vendor": "codex",
      "activity": "implementation",
      "task_class": "backend",
      "difficulty": 4,
      "risk_level": "high",
      "tier": "experimental"
    }
  ]
}
EOF
assert_fail "policy with invalid tier is rejected" bash "$SCRIPT" --policy "$bad_policy_tier" --request "$request2"

bad_policy_dupe="$tmpdir/bad-policy-dupe.json"
cat > "$bad_policy_dupe" <<'EOF'
{
  "schema": 1,
  "blocked_tier": "operator/blocked",
  "escalation": {
    "chain": ["economy", "standard", "critical", "operator/blocked"],
    "triggers": ["quality_gate_failed"]
  },
  "vendors": {
    "codex": {
      "tiers": {
        "economy": {"model": "fixture", "reasoning_effort": "low"},
        "standard": {"model": "fixture", "reasoning_effort": "medium"},
        "critical": {"model": "fixture", "reasoning_effort": "high"}
      }
    }
  },
  "routes": [
    {
      "vendor": "codex",
      "activity": "implementation",
      "task_class": "backend",
      "difficulty": 3,
      "risk_level": "medium",
      "tier": "standard"
    },
    {
      "vendor": "codex",
      "activity": "implementation",
      "task_class": "backend",
      "difficulty": 3,
      "risk_level": "medium",
      "tier": "critical"
    }
  ]
}
EOF
assert_fail "duplicate route key is rejected" bash "$SCRIPT" --policy "$bad_policy_dupe" --request "$request2"

printf 'resource-routing: %d passed, %d failed\n' "$pass" "$fail"
[[ $fail -eq 0 ]]
