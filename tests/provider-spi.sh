#!/usr/bin/env bash
set -uo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$TEST_DIR/../providers" && -d "$TEST_DIR/../plugins" ]]; then
  FRAMEWORK_ROOT="$(cd "$TEST_DIR/.." && pwd)"
  HOST_ROOT="$FRAMEWORK_ROOT"
else
  HOST_ROOT="$(cd "$TEST_DIR/../.." && pwd)"
  FRAMEWORK_ROOT="$HOST_ROOT/agentmarshal"
fi
DISPATCH="$FRAMEWORK_ROOT/providers/dispatch.sh"
SCHEMA="$FRAMEWORK_ROOT/schemas/plugin-manifest.schema.json"

pass=0
fail=0
TMP_FILES=()

cleanup() {
  local path
  for path in "${TMP_FILES[@]}"; do
    rm -rf "$path"
  done
}
trap cleanup EXIT

mktemp_dir() {
  local dir
  dir="$(mktemp -d)"
  TMP_FILES+=("$dir")
  printf '%s\n' "$dir"
}

mktemp_file() {
  local file
  file="$(mktemp)"
  TMP_FILES+=("$file")
  printf '%s\n' "$file"
}

assert_ok() {
  local desc="$1"
  shift
  local out rc=0
  out="$(mktemp_file)"
  "$@" >"$out" 2>&1 || rc=$?
  if [[ $rc -eq 0 ]]; then
    echo "  OK  $desc"
    ((pass++))
  else
    echo "  FAIL $desc (exit=$rc)"
    sed 's/^/      /' "$out" | tail -20
    ((fail++))
  fi
}

assert_fail() {
  local want="$1" desc="$2"
  shift 2
  local out rc=0
  out="$(mktemp_file)"
  "$@" >"$out" 2>&1 || rc=$?
  if [[ $rc -ne 0 ]] && { [[ -z "$want" ]] || grep -Fq "$want" "$out"; }; then
    echo "  OK  $desc"
    ((pass++))
  else
    echo "  FAIL $desc (exit=$rc)"
    sed 's/^/      /' "$out" | tail -20
    ((fail++))
  fi
}

assert_json() {
  local desc="$1" jq_filter="$2"
  shift 2
  local out rc=0
  out="$(mktemp_file)"
  "$@" >"$out" 2>&1 || rc=$?
  if [[ $rc -eq 0 ]] && jq -e "$jq_filter" "$out" >/dev/null 2>&1; then
    echo "  OK  $desc"
    ((pass++))
  else
    echo "  FAIL $desc (exit=$rc)"
    sed 's/^/      /' "$out" | tail -20
    ((fail++))
  fi
}

validate_manifest_shape() {
  local manifest="$1"
  jq -e '
    .schema == 1
    and .api_version == "1"
    and .type == "provider"
    and (.id | type == "string")
    and (.version | type == "string")
    and (.description | type == "string")
    and (.capabilities | type == "array" and length > 0)
    and (.entrypoints.execute | type == "string")
    and (.permissions.network | type == "boolean")
    and (.permissions.git_write | type == "boolean")
    and (.permissions.secrets | type == "array")
    and (.requires.agentmarshal | type == "string")
    and (.requires.commands | type == "array")
  ' "$manifest" >/dev/null
}

echo "== provider manifests =="
assert_ok "schema file is present" test -f "$SCHEMA"

while IFS= read -r manifest; do
  plugin_dir="$(dirname "$manifest")"
  label="${plugin_dir#$FRAMEWORK_ROOT/}"
  assert_ok "$label shape matches provider manifest contract" validate_manifest_shape "$manifest"
  while IFS= read -r rel; do
    assert_ok "$label entrypoint exists: $rel" test -x "$plugin_dir/$rel"
  done < <(jq -r '.entrypoints[]' "$manifest")
done < <(find "$FRAMEWORK_ROOT/plugins/providers" -name plugin.json | sort)

echo "== plugin checks =="
for provider in mock github gitlab; do
  plugin_dir="$FRAMEWORK_ROOT/plugins/providers/$provider-provider"
  assert_ok "$provider validate passes" "$plugin_dir/scripts/validate.sh"
  assert_ok "$provider doctor passes" "$plugin_dir/scripts/doctor.sh"
done
gitflic_plugin_dir="$FRAMEWORK_ROOT/plugins/providers/gitflic-provider"
assert_ok "gitflic validate passes" "$gitflic_plugin_dir/scripts/validate.sh"
assert_fail "none of declared secret env vars found" "gitflic doctor fails without declared secret" \
  env -u GITFLIC_API_TOKEN -u AGENTMARSHAL_GITFLIC_API_TOKEN \
      -u AGENTOPS_GITFLIC_API_TOKEN -u CI_JOB_TOKEN \
    "$gitflic_plugin_dir/scripts/doctor.sh"
assert_ok "gitflic doctor passes with declared secret" \
  env -u GITFLIC_API_TOKEN -u AGENTOPS_GITFLIC_API_TOKEN -u CI_JOB_TOKEN \
      AGENTMARSHAL_GITFLIC_API_TOKEN=fixture \
    "$gitflic_plugin_dir/scripts/doctor.sh"

echo "== mock provider =="
assert_json "mock branch SHA" '.provider == "mock" and .branch == "main" and (.sha | length == 40)' \
  "$DISPATCH" --provider mock --capability provider.refs --operation branch-sha --branch main
assert_json "mock blob" '.provider == "mock" and .path == "README.md" and .content == "fixture blob"' \
  "$DISPATCH" --provider mock --capability provider.refs --operation blob --path README.md
assert_json "mock merge request" '.provider == "mock" and .id == 101 and .state == "OPEN"' \
  "$DISPATCH" --provider mock --capability provider.merge_request --operation get --mr 101
assert_json "mock compare" '.provider == "mock" and .base == "aaaa" and .head == "bbbb"' \
  "$DISPATCH" --provider mock --capability provider.compare --operation commits --base aaaa --head bbbb
assert_json "mock pipeline by sha" '.provider == "mock" and .status == "SUCCESS"' \
  env AGENTMARSHAL_PROVIDER_MOCK_SCENARIO=success "$DISPATCH" --provider mock --capability provider.pipeline --operation by-sha --sha deadbeef
assert_json "mock pipeline by sha error" '.provider == "mock" and .status == "ERROR"' \
  env AGENTMARSHAL_PROVIDER_MOCK_SCENARIO=error "$DISPATCH" --provider mock --capability provider.pipeline --operation by-sha --sha deadbeef
assert_json "mock jobs" 'length == 2 and .[0].stageName == "lint"' \
  "$DISPATCH" --provider mock --capability provider.pipeline --operation jobs --pipeline-id 7001
assert_json "mock jobs error scenario" '.[1].status == "ERROR"' \
  env AGENTMARSHAL_PROVIDER_MOCK_SCENARIO=error "$DISPATCH" --provider mock --capability provider.pipeline --operation jobs --pipeline-id 7001
assert_json "mock wait success" '.status == "SUCCESS"' \
  env AGENTMARSHAL_PROVIDER_MOCK_SCENARIO=success "$DISPATCH" --provider mock --capability provider.pipeline --operation wait --pipeline-id 7001
assert_fail '"status":"FAILED"' "mock wait failed terminal status" \
  env AGENTMARSHAL_PROVIDER_MOCK_SCENARIO=failed "$DISPATCH" --provider mock --capability provider.pipeline --operation wait --pipeline-id 7001
assert_fail 'transport error' "mock wait transport error" \
  env AGENTMARSHAL_PROVIDER_MOCK_SCENARIO=error "$DISPATCH" --provider mock --capability provider.pipeline --operation wait --pipeline-id 7001
assert_fail 'timeout waiting for pipeline' "mock wait timeout" \
  env AGENTMARSHAL_PROVIDER_MOCK_SCENARIO=running "$DISPATCH" --provider mock --capability provider.pipeline --operation wait --pipeline-id 7001 --timeout 1 --interval 1

CONFIG_HOST="$(mktemp_dir)"
mkdir -p "$CONFIG_HOST/.agentmarshal" "$CONFIG_HOST/agentmarshal"
cp -R "$FRAMEWORK_ROOT/plugins" "$CONFIG_HOST/agentmarshal/"
cat >"$CONFIG_HOST/.agentmarshal/project.json" <<'EOF'
{
  "schema": 1,
  "preset": "minimal",
  "runtime_config": ".agentmarshal/config/runtime.conf",
  "journal_root": ".agentmarshal/journal",
  "agents_dir": "agentmarshal/agents",
  "prompts_dir": "agentmarshal/agents/prompts",
  "provider": {
    "default": "mock",
    "secret_bindings": {}
  },
  "plugins": {
    "roots": {
      "bundled": "agentmarshal/plugins",
      "host_local": ".agentmarshal/plugins"
    },
    "resolved": []
  },
  "adoption": {
    "mode": "fresh"
  }
}
EOF
mkdir -p "$CONFIG_HOST/.agentmarshal/config" "$CONFIG_HOST/.agentmarshal/journal" "$CONFIG_HOST/agentmarshal/agents/prompts"
cat >"$CONFIG_HOST/.agentmarshal/config/runtime.conf" <<'EOF'
schema=1
review_language=ru
active_roles=lead
operating_mode=normal
active_milestone=fixture
backlog_amplification_limit=0.25
worktree_root=../worktrees
worktree_pattern={repo}-{alias}
stats_enabled=false
stats_store=.agentmarshal/journal/stats/runs
evaluation_store=.agentmarshal/journal/stats/evaluations
stats_raw_store=.agentmarshal/journal/runs
stats_retention_days=30
EOF
assert_json "dispatch reads provider.default from project config" '.provider == "mock" and .branch == "main"' \
  "$DISPATCH" --project-root "$CONFIG_HOST" --capability provider.refs --operation branch-sha --branch main

echo "== gitflic facade =="
WRAP_DIR="$(mktemp_dir)"
CI_ARGS="$WRAP_DIR/ci-args"
SCOPE_ARGS="$WRAP_DIR/scope-args"

cat >"$WRAP_DIR/gitflic-ci.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >"${AGENTMARSHAL_TEST_GITFLIC_CI_ARGS:?}"
case "${1:-}" in
  sha)
    jq -nc --arg command "$1" --arg sha "${2:-}" '{command: $command, sha: $sha}'
    ;;
  jobs)
    jq -nc --arg command "$1" --arg id "${2:-}" '[{command: $command, pipelineId: ($id | tonumber)}]'
    ;;
  wait)
    jq -nc --arg command "$1" --arg id "${2:-}" '{command: $command, localId: ($id | tonumber), status: "SUCCESS"}'
    ;;
  *)
    jq -nc --arg command "${1:-}" '{command: $command}'
    ;;
esac
EOF

cat >"$WRAP_DIR/scope-guard-gitflic.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >"${AGENTMARSHAL_TEST_GITFLIC_SCOPE_ARGS:?}"
jq -nc --arg command "scope-guard" --arg args "$*" '{command: $command, args: $args}'
EOF

chmod +x "$WRAP_DIR/gitflic-ci.sh" "$WRAP_DIR/scope-guard-gitflic.sh"

assert_json "gitflic by-sha delegates to existing ci script" '.command == "sha" and .sha == "deadbeef"' \
  env \
    AGENTMARSHAL_PROVIDER_GITFLIC_CI_SCRIPT="$WRAP_DIR/gitflic-ci.sh" \
    AGENTMARSHAL_PROVIDER_GITFLIC_SCOPE_SCRIPT="$WRAP_DIR/scope-guard-gitflic.sh" \
    AGENTMARSHAL_TEST_GITFLIC_CI_ARGS="$CI_ARGS" \
    AGENTMARSHAL_TEST_GITFLIC_SCOPE_ARGS="$SCOPE_ARGS" \
    "$DISPATCH" --provider gitflic --capability provider.pipeline --operation by-sha -- deadbeef
assert_ok "gitflic by-sha preserves delegated argv" grep -Fxq 'sha deadbeef' "$CI_ARGS"

assert_json "gitflic jobs delegates to existing ci script" '.[0].command == "jobs" and .[0].pipelineId == 17' \
  env \
    AGENTMARSHAL_PROVIDER_GITFLIC_CI_SCRIPT="$WRAP_DIR/gitflic-ci.sh" \
    AGENTMARSHAL_PROVIDER_GITFLIC_SCOPE_SCRIPT="$WRAP_DIR/scope-guard-gitflic.sh" \
    AGENTMARSHAL_TEST_GITFLIC_CI_ARGS="$CI_ARGS" \
    AGENTMARSHAL_TEST_GITFLIC_SCOPE_ARGS="$SCOPE_ARGS" \
    "$DISPATCH" --provider gitflic --capability provider.pipeline --operation jobs -- 17
assert_ok "gitflic jobs preserves delegated argv" grep -Fxq 'jobs 17' "$CI_ARGS"

assert_json "gitflic scope guard delegates to existing script" '.command == "scope-guard" and (.args | contains("--branch feat/mock"))' \
  env \
    AGENTMARSHAL_PROVIDER_GITFLIC_CI_SCRIPT="$WRAP_DIR/gitflic-ci.sh" \
    AGENTMARSHAL_PROVIDER_GITFLIC_SCOPE_SCRIPT="$WRAP_DIR/scope-guard-gitflic.sh" \
    AGENTMARSHAL_TEST_GITFLIC_CI_ARGS="$CI_ARGS" \
    AGENTMARSHAL_TEST_GITFLIC_SCOPE_ARGS="$SCOPE_ARGS" \
    "$DISPATCH" --provider gitflic --capability provider.compare --operation scope-guard -- --branch feat/mock --head 0123456789012345678901234567890123456789
assert_ok "gitflic scope guard preserves delegated argv" \
  grep -Fxq -- '--branch feat/mock --head 0123456789012345678901234567890123456789' "$SCOPE_ARGS"

echo "== stubs and guards =="
assert_fail 'not implemented' "github stub is explicit" \
  "$DISPATCH" --provider github --capability provider.refs --operation branch-sha --branch main
assert_fail 'not implemented' "gitlab stub is explicit" \
  "$DISPATCH" --provider gitlab --capability provider.refs --operation branch-sha --branch main
assert_fail "does not declare capability" "dispatch blocks undeclared gitflic capability" \
  "$DISPATCH" --provider gitflic --capability provider.refs --operation branch-sha --branch main

TRAVERSAL_DIR="$(mktemp_dir)"
mkdir -p "$TRAVERSAL_DIR/plugin/scripts"
cat >"$TRAVERSAL_DIR/outside.sh" <<'EOF'
#!/usr/bin/env bash
echo unsafe
EOF
chmod +x "$TRAVERSAL_DIR/outside.sh"
cat >"$TRAVERSAL_DIR/plugin/plugin.json" <<'EOF'
{"schema":1,"api_version":"1","type":"provider","capabilities":["provider.refs"],"entrypoints":{"execute":"../outside.sh"}}
EOF
assert_fail "invalid provider entrypoint path" "provider SPI rejects traversal entrypoint" \
  bash -c 'source "$1"; aops_provider_entrypoint_v1 "$2" execute' _ \
  "$FRAMEWORK_ROOT/providers/provider-spi.sh" "$TRAVERSAL_DIR/plugin"

ln -s "$TRAVERSAL_DIR/outside.sh" "$TRAVERSAL_DIR/plugin/scripts/execute.sh"
jq '.entrypoints.execute = "scripts/execute.sh"' \
  "$TRAVERSAL_DIR/plugin/plugin.json" >"$TRAVERSAL_DIR/plugin/plugin.tmp"
mv "$TRAVERSAL_DIR/plugin/plugin.tmp" "$TRAVERSAL_DIR/plugin/plugin.json"
assert_fail "escapes plugin root" "provider SPI rejects symlink entrypoint escape" \
  bash -c 'source "$1"; aops_provider_entrypoint_v1 "$2" execute' _ \
  "$FRAMEWORK_ROOT/providers/provider-spi.sh" "$TRAVERSAL_DIR/plugin"

echo "== summary =="
echo "passed=$pass failed=$fail"
[[ $fail -eq 0 ]]
