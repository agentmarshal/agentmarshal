#!/usr/bin/env bash
set -euo pipefail

FRAMEWORK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AOPS="$FRAMEWORK_ROOT/bin/agentmarshal"
pass=0
fail=0

assert() {
  local exp="$1" desc="$2"
  shift 2
  local rc=0
  local out
  out="$(mktemp)"
  "$@" >"$out" 2>&1 || rc=$?
  if { [[ "$exp" == ok && $rc -eq 0 ]] || [[ "$exp" == fail && $rc -ne 0 ]]; }; then
    echo "  ✅ $desc (exit=$rc)"
    ((pass += 1))
  else
    echo "  ❌ $desc (exit=$rc expected $exp)"
    sed 's/^/      /' "$out" | tail -20
    ((fail += 1))
  fi
  rm -f "$out"
}

FIX="$(mktemp -d)"
trap 'rm -rf "$FIX"' EXIT

make_host() {
  local host="$1"
  mkdir -p "$host/agentmarshal"
  cp -R "$FRAMEWORK_ROOT/bin" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/lib" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/presets" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/plugins" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/scripts" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/templates" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/schemas" "$host/agentmarshal/"
  mkdir -p "$host/agentmarshal/agents/prompts"
  git -C "$host" init -q
  git -C "$host" config user.email fixture@example.com
  git -C "$host" config user.name "Fixture"
  chmod +x "$host/agentmarshal/bin/agentmarshal"
  chmod +x "$host/agentmarshal/scripts/"*.sh
}

write_legacy_runtime_config() {
  local target="$1"
  cat >"$target" <<'EOF'
schema=1
review_language=ru
active_roles=lead,frontend,qa
operating_mode=normal
active_milestone=none
backlog_amplification_limit=0.3
worktree_root=../worktrees
worktree_pattern={repo}.{alias}
stats_enabled=true
stats_store=.agents/stats/runs
evaluation_store=.agents/stats/evaluations
stats_raw_store=.agents/runs/stats
stats_retention_days=365
EOF
}

echo "== fresh bootstrap =="
HOST1="$FIX/host-fresh"
make_host "$HOST1"
assert ok "init dry-run plans fresh bootstrap" \
  "$HOST1/agentmarshal/bin/agentmarshal" init --project-root "$HOST1" --non-interactive --dry-run
[[ ! -e "$HOST1/.agentmarshal/project.json" ]] || { echo "  ❌ dry-run wrote files"; exit 1; }
assert ok "init creates fresh bootstrap" \
  "$HOST1/agentmarshal/bin/agentmarshal" init --project-root "$HOST1" --non-interactive --preset minimal
assert ok "fresh bootstrap records requested language" \
  grep -q '^review_language=ru$' "$HOST1/.agentmarshal/config/runtime.conf"
assert ok "validate accepts explicit root+config" \
  "$HOST1/agentmarshal/bin/agentmarshal" validate --project-root "$HOST1" --project-config "$HOST1/.agentmarshal/project.json"
assert ok "doctor passes on fresh bootstrap" \
  "$HOST1/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST1"
assert ok "fresh bootstrap records mock default provider" \
  jq -e '.provider.default == "mock" and .provider.secret_bindings == {}' \
    "$HOST1/.agentmarshal/project.json"

mkdir -p "$HOST1/agentmarshal/plugins/providers/optional-provider/scripts"
cat >"$HOST1/agentmarshal/plugins/providers/optional-provider/plugin.json" <<'EOF'
{
  "schema": 1,
  "id": "optional-provider",
  "version": "0.1.0",
  "api_version": "1",
  "type": "provider",
  "distribution": "bundled",
  "description": "Fixture plugin that is bundled but not resolved.",
  "capabilities": ["provider.refs"],
  "entrypoints": {"doctor": "scripts/doctor.sh"},
  "permissions": {"network": false, "git_write": false, "secrets": []},
  "requires": {
    "agentmarshal": ">=0.1.0 <0.2.0",
    "commands": ["definitely-missing-agentmarshal-fixture-command"]
  }
}
EOF
cat >"$HOST1/agentmarshal/plugins/providers/optional-provider/scripts/doctor.sh" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
assert ok "doctor ignores runtime dependencies of unresolved bundled plugins" \
  "$HOST1/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST1"

jq '.plugins.resolved = [{
  "id": "mock-provider",
  "type": "provider",
  "distribution": "bundled",
  "root": "agentmarshal/plugins/providers/mock-provider"
}]' "$HOST1/.agentmarshal/project.json" >"$HOST1/project.tmp"
mv "$HOST1/project.tmp" "$HOST1/.agentmarshal/project.json"
assert ok "doctor validates resolved bundled plugin runtime" \
  "$HOST1/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST1"
chmod -x "$HOST1/agentmarshal/plugins/providers/mock-provider/scripts/doctor.sh"
assert fail "doctor rejects a broken resolved bundled plugin" \
  "$HOST1/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST1"
chmod +x "$HOST1/agentmarshal/plugins/providers/mock-provider/scripts/doctor.sh"
assert ok "doctor recovers after resolved plugin repair" \
  "$HOST1/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST1"
assert ok "repeated init validates a healthy bootstrap" \
  "$HOST1/agentmarshal/bin/agentmarshal" init --project-root "$HOST1" --non-interactive
rm -rf "$HOST1/.agentmarshal/plugins"
assert fail "repeated init rejects a partially broken bootstrap" \
  "$HOST1/agentmarshal/bin/agentmarshal" init --project-root "$HOST1" --non-interactive
mkdir -p "$HOST1/.agentmarshal/plugins"
(
  cd "$HOST1/agentmarshal"
  assert ok "validate works from submodule dir with explicit host root" \
    ./bin/agentmarshal validate --project-root "$HOST1" --project-config "$HOST1/.agentmarshal/project.json"
  assert ok "doctor works from submodule dir with explicit host root" \
    ./bin/agentmarshal doctor --project-root "$HOST1" --project-config "$HOST1/.agentmarshal/project.json"
)

mkdir -p "$HOST1/.agentmarshal/journal/stats/runs/2026" "$HOST1/.agentmarshal/journal/stats/evaluations/2026"
cat >"$HOST1/.agentmarshal/journal/stats/runs/2026/RUN-001.json" <<'EOF'
{"role":"lead","vendor":"codex","model":"gpt-5","activity":"implementation","outcome":"success","duration_seconds":12,"human_interventions":0,"retries":1,"scope_violations":0,"tests_failed":0,"findings_count":2,"cost_usd":0.42,"trial":false,"recorded_at":"2026-06-23T00:00:00Z"}
EOF
assert ok "stats summary reads new journal layout" \
  "$HOST1/agentmarshal/bin/agentmarshal" stats summary --project-root "$HOST1"
assert ok "agmake init uses fresh journal root" \
  "$HOST1/agentmarshal/bin/agmake" init --project-root "$HOST1" --task CR-123 --branch docs/CR-123-agmake-fresh
assert ok "agmake fresh runbook is generated under .agentmarshal journal" \
  test -f "$HOST1/.agentmarshal/journal/tmp/runner/CR-123-runbook.sh"
assert ok "agmake fresh runbook does not create legacy runtime root" \
  test ! -e "$HOST1/.agents"
assert ok "agmake lint validates fresh runbook without ripgrep dependency" \
  "$HOST1/agentmarshal/bin/agmake" lint "$HOST1/.agentmarshal/journal/tmp/runner/CR-123-runbook.sh"
mkdir -p "$HOST1/.agentmarshal/journal/runs/runner/CR-123"
printf 'IMPLEMENTATION_SHA=%q\n' fixture >"$HOST1/.agentmarshal/journal/runs/runner/CR-123/state.env"
assert ok "agmake state reads fresh journal root" \
  "$HOST1/agentmarshal/bin/agmake" state --project-root "$HOST1" CR-123

printf '# CR-125 Research analysis task fixture\nOwner: lead\nType: feature\nPriority: P2\nStatus: open\nCreated: 2026-06-26\n' \
  >"$HOST1/.agentmarshal/journal/tasks/open/CR-125.md"
mkdir -p "$HOST1/.agentmarshal/plugins/research-workflow/roles"
printf '# Analyst\nHost-local research workflow role.\n' \
  >"$HOST1/.agentmarshal/plugins/research-workflow/roles/analyst.md"
assert ok "record-agent-stat accepts host-local analyst role on fresh host" \
  env AGENTMARSHAL_RECORDED_AT=2026-06-26T10:00:00Z \
  "$HOST1/agentmarshal/scripts/record-agent-stat.sh" \
    --project-root "$HOST1" \
    --task CR-125 --role analyst --vendor mock --model mock-v1 \
    --profile minimal-default --activity analysis --outcome success \
    --source-artifact manual
assert ok "fresh-host stat is created under .agentmarshal journal" \
  bash -c "find \"$HOST1/.agentmarshal/journal/stats/runs\" -name 'RUN-*.json' -print -quit | grep -q ."
assert ok "agentmarshal stats summary reads fresh-host stat" \
  "$HOST1/agentmarshal/bin/agentmarshal" stats summary --project-root "$HOST1"
assert ok "agentmarshal-stats.sh reads fresh-host stat via --project-root" \
  "$HOST1/agentmarshal/scripts/agentmarshal-stats.sh" --project-root "$HOST1" summary

HOST1_EN="$FIX/host-fresh-en"
make_host "$HOST1_EN"
assert ok "init creates English runtime config" \
  "$HOST1_EN/agentmarshal/bin/agentmarshal" init --project-root "$HOST1_EN" --non-interactive --preset minimal --language en
assert ok "English runtime config records review_language" \
  grep -q '^review_language=en$' "$HOST1_EN/.agentmarshal/config/runtime.conf"

echo "== adopt existing =="
HOST2="$FIX/host-adopt"
make_host "$HOST2"
mkdir -p "$HOST2/.agents/config" "$HOST2/.agents/stats/runs/2026"
write_legacy_runtime_config "$HOST2/.agents/config/agentmarshal.conf"
assert fail "init refuses legacy journal without adopt-existing in non-interactive mode" \
  "$HOST2/agentmarshal/bin/agentmarshal" init --project-root "$HOST2" --non-interactive

HOST2_ARCHIVE="$FIX/host-fresh-with-legacy-archive"
make_host "$HOST2_ARCHIVE"
mkdir -p "$HOST2_ARCHIVE/.agents/config" "$HOST2_ARCHIVE/.agents/tasks/done"
printf '# legacy archive marker\n' >"$HOST2_ARCHIVE/.agents/README.md"
assert fail "init refuses legacy archive without explicit mode" \
  "$HOST2_ARCHIVE/agentmarshal/bin/agentmarshal" init --project-root "$HOST2_ARCHIVE" --non-interactive
assert ok "init creates fresh bootstrap next to legacy archive" \
  "$HOST2_ARCHIVE/agentmarshal/bin/agentmarshal" init --project-root "$HOST2_ARCHIVE" --non-interactive --legacy-archive .agents --preset minimal
assert ok "fresh-with-legacy-archive keeps active journal under .agentmarshal" \
  jq -e '.runtime_config == ".agentmarshal/config/runtime.conf"
    and .journal_root == ".agentmarshal/journal"
    and .adoption.mode == "fresh-with-legacy-archive"
    and .adoption.legacy_archive == ".agents"
    and (.adoption.legacy_journal // "") == ""' \
    "$HOST2_ARCHIVE/.agentmarshal/project.json"
assert ok "fresh-with-legacy-archive doctor passes" \
  "$HOST2_ARCHIVE/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST2_ARCHIVE"
assert ok "fresh-with-legacy-archive records archive marker" \
  grep -q 'legacy AgentMarshal archive' "$HOST2_ARCHIVE/.agentmarshal/LEGACY_ARCHIVE.md"
assert ok "fresh-with-legacy-archive does not write active tasks to legacy archive" \
  test -d "$HOST2_ARCHIVE/.agentmarshal/journal/tasks/open"

assert ok "init adopts existing legacy journal" \
  "$HOST2/agentmarshal/bin/agentmarshal" init --project-root "$HOST2" --non-interactive --adopt-existing --preset strict
assert ok "doctor passes on adopted bootstrap" \
  "$HOST2/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST2"
(
  cd "$HOST2/agentmarshal"
  assert ok "doctor works from adopted submodule dir" \
    ./bin/agentmarshal doctor --project-root "$HOST2" --project-config "$HOST2/.agentmarshal/project.json"
)
assert ok "adopted config keeps legacy runtime path" \
  jq -e '.runtime_config == ".agents/config/agentmarshal.conf" and .journal_root == ".agents" and .preset == "strict" and .provider.default == "mock"' \
    "$HOST2/.agentmarshal/project.json"
assert ok "agmake init keeps adopted legacy journal root" \
  "$HOST2/agentmarshal/bin/agmake" init --project-root "$HOST2" --task CR-124 --branch docs/CR-124-agmake-legacy
assert ok "agmake legacy runbook is generated under .agents" \
  test -f "$HOST2/.agents/tmp/runner/CR-124-runbook.sh"
assert ok "agmake lint validates legacy runbook" \
  "$HOST2/agentmarshal/bin/agmake" lint "$HOST2/.agents/tmp/runner/CR-124-runbook.sh"

HOST2_LEGACY="$FIX/host-adopt-agentops-conf"
make_host "$HOST2_LEGACY"
mkdir -p "$HOST2_LEGACY/.agents/config" "$HOST2_LEGACY/.agents/stats/runs/2026"
write_legacy_runtime_config "$HOST2_LEGACY/.agents/config/agentops.conf"
assert ok "init adopts host with legacy agentops.conf" \
  "$HOST2_LEGACY/agentmarshal/bin/agentmarshal" init --project-root "$HOST2_LEGACY" --non-interactive --adopt-existing --preset strict
assert ok "doctor passes on adopted legacy agentops.conf" \
  "$HOST2_LEGACY/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST2_LEGACY"
assert ok "validate passes on adopted legacy agentops.conf" \
  "$HOST2_LEGACY/agentmarshal/bin/agentmarshal" validate --project-root "$HOST2_LEGACY"
assert ok "adopted legacy config keeps agentops runtime path" \
  jq -e '.runtime_config == ".agents/config/agentops.conf" and .journal_root == ".agents" and .preset == "strict" and .provider.default == "mock"' \
    "$HOST2_LEGACY/.agentmarshal/project.json"

echo "== provider credential preflight =="
HOST2_GITFLIC="$FIX/host-gitflic-provider"
make_host "$HOST2_GITFLIC"
assert ok "init creates gitflic provider fixture host" \
  "$HOST2_GITFLIC/agentmarshal/bin/agentmarshal" init --project-root "$HOST2_GITFLIC" --non-interactive
jq '.provider.default = "gitflic" | .provider.secret_bindings = {"GITFLIC_API_TOKEN":"AGENTMARSHAL_FIXTURE_TOKEN"}' \
  "$HOST2_GITFLIC/.agentmarshal/project.json" >"$HOST2_GITFLIC/project.tmp"
mv "$HOST2_GITFLIC/project.tmp" "$HOST2_GITFLIC/.agentmarshal/project.json"
assert fail "doctor rejects default provider with missing declared secret" \
  env -u GITFLIC_API_TOKEN -u AGENTMARSHAL_GITFLIC_API_TOKEN \
      -u AGENTOPS_GITFLIC_API_TOKEN -u CI_JOB_TOKEN \
      -u AGENTMARSHAL_FIXTURE_TOKEN \
    "$HOST2_GITFLIC/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST2_GITFLIC"
assert ok "doctor accepts default provider with bound env secret" \
  env -u GITFLIC_API_TOKEN -u AGENTMARSHAL_GITFLIC_API_TOKEN \
      -u AGENTOPS_GITFLIC_API_TOKEN -u CI_JOB_TOKEN \
      AGENTMARSHAL_FIXTURE_TOKEN=fixture \
    "$HOST2_GITFLIC/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST2_GITFLIC"

echo "== fail-closed =="
HOST3="$FIX/host-invalid"
make_host "$HOST3"
mkdir -p "$HOST3/.agentmarshal"
cat >"$HOST3/.agentmarshal/project.json" <<'EOF'
{"schema":1,"preset":"minimal","runtime_config":"../escape","journal_root":".agentmarshal/journal","agents_dir":"agentmarshal/agents","prompts_dir":"agentmarshal/agents/prompts","plugins":{"roots":{"bundled":"agentmarshal/plugins","host_local":".agentmarshal/plugins"},"resolved":[]},"adoption":{"mode":"fresh"}}
EOF
assert fail "validate rejects escaping paths" \
  "$HOST3/agentmarshal/bin/agentmarshal" validate --project-root "$HOST3"

HOST4="$FIX/host-plugin-invalid"
make_host "$HOST4"
assert ok "init creates plugin validation fixture" \
  "$HOST4/agentmarshal/bin/agentmarshal" init --project-root "$HOST4" --non-interactive
jq '.entrypoints.doctor = "../escape.sh"' \
  "$HOST4/agentmarshal/plugins/providers/mock-provider/plugin.json" >"$HOST4/plugin.tmp"
mv "$HOST4/plugin.tmp" "$HOST4/agentmarshal/plugins/providers/mock-provider/plugin.json"
assert fail "doctor rejects an escaping plugin entrypoint" \
  "$HOST4/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST4"

HOST5="$FIX/host-plugin-symlink"
make_host "$HOST5"
assert ok "init creates plugin symlink fixture" \
  "$HOST5/agentmarshal/bin/agentmarshal" init --project-root "$HOST5" --non-interactive
cat >"$HOST5/outside-entrypoint.sh" <<'EOF'
#!/usr/bin/env bash
exit 0
EOF
chmod +x "$HOST5/outside-entrypoint.sh"
ln -sf "$HOST5/outside-entrypoint.sh" \
  "$HOST5/agentmarshal/plugins/providers/mock-provider/scripts/doctor.sh"
assert fail "doctor rejects a symlink escaping plugin entrypoint" \
  "$HOST5/agentmarshal/bin/agentmarshal" doctor --project-root "$HOST5"

echo
echo "pass=$pass fail=$fail"
[[ $fail -eq 0 ]]
