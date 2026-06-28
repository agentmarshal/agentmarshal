#!/usr/bin/env bash
# AgentMarshal v0.1 standalone qualification.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRAMEWORK_TOP="$(git -C "$FRAMEWORK_ROOT" rev-parse --show-toplevel 2>/dev/null || true)"
HOST_ROOT="$(git -C "$FRAMEWORK_ROOT" rev-parse --show-superproject-working-tree 2>/dev/null || true)"

if [[ -z "$FRAMEWORK_TOP" ]]; then
  echo "qualification: AgentMarshal must be inside a git checkout" >&2
  exit 2
fi

if [[ -z "$HOST_ROOT" ]]; then
  if [[ "$FRAMEWORK_TOP" == "$FRAMEWORK_ROOT" ]]; then
    HOST_ROOT="$FRAMEWORK_ROOT"
  else
    HOST_ROOT="$FRAMEWORK_TOP"
  fi
fi

if [[ "$FRAMEWORK_TOP" == "$FRAMEWORK_ROOT" ]]; then
  FRAMEWORK_ARCHIVE_MODE="standalone"
  FRAMEWORK_SOURCE_SHA="$(git -C "$FRAMEWORK_ROOT" rev-parse HEAD)"
else
  FRAMEWORK_ARCHIVE_MODE="host-subdir"
  FRAMEWORK_SOURCE_SHA="$(git -C "$HOST_ROOT" rev-parse HEAD)"
fi

ROOT="$HOST_ROOT"
REPORT_DIR="$ROOT/.agents/runs/qualification"
REPORT="$REPORT_DIR/agentmarshal-v0.1-qualification.txt"

pass=0
fail=0
tmp=""

cleanup() {
  [[ -n "$tmp" ]] && rm -rf "$tmp"
}
trap cleanup EXIT

tmp="$(mktemp -d)"
mkdir -p "$REPORT_DIR"

log() {
  printf '%s\n' "$*" | tee -a "$REPORT"
}

ok() {
  log "OK  $*"
  pass=$((pass + 1))
}

bad() {
  log "FAIL $*"
  fail=$((fail + 1))
}

run_ok() {
  local desc="$1"
  shift
  local out rc=0
  out="$tmp/run-${pass}-${fail}.log"
  "$@" >"$out" 2>&1 || rc=$?
  if [[ $rc -eq 0 ]]; then
    ok "$desc"
  else
    bad "$desc (exit=$rc)"
    sed 's/^/    /' "$out" | tail -20 | tee -a "$REPORT"
  fi
}

run_fail() {
  local desc="$1" want="$2"
  shift 2
  local out rc=0
  out="$tmp/run-${pass}-${fail}.log"
  "$@" >"$out" 2>&1 || rc=$?
  if [[ $rc -ne 0 ]] && grep -Fq "$want" "$out"; then
    ok "$desc"
  else
    bad "$desc (exit=$rc, expected failure containing '$want')"
    sed 's/^/    /' "$out" | tail -20 | tee -a "$REPORT"
  fi
}

run_no_match() {
  local desc="$1" pattern="$2"
  shift 2
  local out rc=0
  out="$tmp/run-${pass}-${fail}.log"
  "$@" >"$out" 2>&1 || rc=$?
  if [[ $rc -ne 0 ]]; then
    ok "$desc"
  else
    bad "$desc (unexpected match for '$pattern')"
    sed 's/^/    /' "$out" | tail -20 | tee -a "$REPORT"
  fi
}

make_host() {
  local host="$1"
  mkdir -p "$host/agentmarshal"
  cp -R "$FRAMEWORK_ROOT/bin" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/lib" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/presets" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/plugins" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/providers" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/schemas" "$host/agentmarshal/"
  cp -R "$FRAMEWORK_ROOT/templates" "$host/agentmarshal/"
  mkdir -p "$host/agentmarshal/agents/prompts"
  git -C "$host" init -q
  git -C "$host" config user.email qualification@example.invalid
  git -C "$host" config user.name "AgentMarshal Qualification"
}

archive_framework_list() {
  if [[ "$FRAMEWORK_ARCHIVE_MODE" == "standalone" ]]; then
    git -C "$FRAMEWORK_ROOT" archive "$FRAMEWORK_SOURCE_SHA" | tar -t
  else
    git -C "$HOST_ROOT" archive "$FRAMEWORK_SOURCE_SHA" agentmarshal/ \
      | tar -t \
      | sed 's#^agentmarshal/##'
  fi
}

archive_framework_extract() {
  local dest="$1"
  if [[ "$FRAMEWORK_ARCHIVE_MODE" == "standalone" ]]; then
    git -C "$FRAMEWORK_ROOT" archive "$FRAMEWORK_SOURCE_SHA" | tar -x -C "$dest"
  else
    git -C "$HOST_ROOT" archive "$FRAMEWORK_SOURCE_SHA" agentmarshal/ \
      | tar -x -C "$dest" --strip-components=1
  fi
}

write_host_local_plugin() {
  local root="$1" id="$2" exit_code="$3" git_write="$4"
  local dir="$root/.agentmarshal/plugins/providers/$id"
  mkdir -p "$dir/scripts"
  cat >"$dir/plugin.json" <<EOF
{
  "schema": 1,
  "id": "$id",
  "version": "0.1.0",
  "api_version": "1",
  "type": "provider",
  "distribution": "host-local",
  "description": "Qualification host-local provider fixture.",
  "capabilities": ["provider.refs"],
  "entrypoints": {
    "doctor": "scripts/doctor.sh",
    "execute": "scripts/execute.sh"
  },
  "permissions": {
    "network": false,
    "git_write": $git_write,
    "secrets": []
  },
  "requires": {
    "agentmarshal": ">=0.1.0 <0.2.0",
    "commands": []
  }
}
EOF
  cat >"$dir/scripts/doctor.sh" <<EOF
#!/usr/bin/env bash
exit $exit_code
EOF
  cat >"$dir/scripts/execute.sh" <<'EOF'
#!/usr/bin/env bash
jq -nc '{provider:"host-local-fixture", ok:true}'
EOF
  chmod +x "$dir/scripts/doctor.sh" "$dir/scripts/execute.sh"
}

set_resolved_plugin() {
  local host="$1" id="$2"
  jq --arg id "$id" '
    .plugins.resolved = [{
      "id": $id,
      "type": "provider",
      "distribution": "host-local",
      "root": (".agentmarshal/plugins/providers/" + $id)
    }]
  ' "$host/.agentmarshal/project.json" >"$host/project.tmp"
  mv "$host/project.tmp" "$host/.agentmarshal/project.json"
}

: >"$REPORT"
log "AgentMarshal v0.1 qualification"
log "Source-SHA: $FRAMEWORK_SOURCE_SHA"
log "Archive-Mode: $FRAMEWORK_ARCHIVE_MODE"
log "Started-At: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
log ""

run_ok "validate full host journal/framework" bash "$FRAMEWORK_ROOT/scripts/validate.sh"
run_ok "public bilingual docs parity" bash "$FRAMEWORK_ROOT/scripts/check-doc-parity.sh"
run_ok "bootstrap fixtures" bash "$FRAMEWORK_ROOT/tests/bootstrap.sh"
run_ok "provider SPI fixtures" bash "$FRAMEWORK_ROOT/tests/provider-spi.sh"
run_ok "resource routing fixtures" bash "$FRAMEWORK_ROOT/tests/resource-routing.sh"
run_ok "negative gate fixtures" bash "$FRAMEWORK_ROOT/tests/negative.sh"

log ""
log "== preset qualification =="
for preset in minimal standard strict; do
  host="$tmp/host-$preset"
  make_host "$host"
  run_ok "init/doctor preset=$preset" \
    "$host/agentmarshal/bin/agentmarshal" init --project-root "$host" --preset "$preset" --language en --non-interactive
  run_ok "doctor preset=$preset" \
    "$host/agentmarshal/bin/agentmarshal" doctor --project-root "$host"
done

log ""
log "== host-local plugin activation =="
host="$tmp/host-host-local"
make_host "$host"
run_ok "init host-local fixture" \
  "$host/agentmarshal/bin/agentmarshal" init --project-root "$host" --preset strict --non-interactive
write_host_local_plugin "$host" "blocking-gate" 42 false
run_ok "unresolved host-local blocking gate is discovered but not executed" \
  "$host/agentmarshal/bin/agentmarshal" doctor --project-root "$host"
set_resolved_plugin "$host" "blocking-gate"
run_no_match "resolved host-local blocking gate executes and blocks" "success" \
  "$host/agentmarshal/bin/agentmarshal" doctor --project-root "$host"

host="$tmp/host-overprivileged"
make_host "$host"
run_ok "init overprivileged fixture" \
  "$host/agentmarshal/bin/agentmarshal" init --project-root "$host" --preset strict --non-interactive
write_host_local_plugin "$host" "overprivileged-provider" 0 true
set_resolved_plugin "$host" "overprivileged-provider"
run_fail "resolved git_write plugin is blocked by qualification policy" "git_write permission" \
  "$host/agentmarshal/bin/agentmarshal" doctor --project-root "$host"

log ""
log "== snapshot contaminant scan =="
archive_list="$tmp/archive-list.txt"
archive_framework_list >"$archive_list"
run_no_match "snapshot excludes pycache" "__pycache__" grep -F "__pycache__" "$archive_list"
run_no_match "snapshot excludes raw run state" ".agents/runs" grep -F ".agents/runs" "$archive_list"
run_no_match "snapshot excludes environment files" ".env" grep -E '(^|/)\.env([^/]*$|/)' "$archive_list"
run_ok "snapshot contains public README selector" grep -Fx "README.md" "$archive_list"
run_ok "snapshot contains bilingual public docs" grep -Fx "README.en.md" "$archive_list"

log ""
log "== local extraction and submodule simulation =="
source_sha="$FRAMEWORK_SOURCE_SHA"
snapshot_dir="$tmp/agentmarshal-snapshot"
extracted_repo="$tmp/agentmarshal-extracted"
host_repo="$tmp/host-with-submodule"
recursive_clone="$tmp/host-recursive-clone"
existing_clone="$tmp/host-existing-clone"
mkdir -p "$snapshot_dir"
archive_framework_extract "$snapshot_dir"
run_ok "snapshot validate script exists" test -x "$snapshot_dir/scripts/validate.sh"
git -C "$snapshot_dir" init -q
git -C "$snapshot_dir" config user.email qualification@example.invalid
git -C "$snapshot_dir" config user.name "AgentMarshal Qualification"
git -C "$snapshot_dir" add -A
git -C "$snapshot_dir" commit -qm "Initial AgentMarshal extraction snapshot"
git -C "$snapshot_dir" tag -a v0.1.0-qualification -m "AgentMarshal v0.1 qualification snapshot"
git clone -q --bare "$snapshot_dir" "$extracted_repo"
run_ok "extracted repository starts with one snapshot commit" \
  test "$(git -C "$snapshot_dir" rev-list --count HEAD)" = "1"
run_ok "qualification release tag exists" \
  git -C "$snapshot_dir" rev-parse --verify v0.1.0-qualification

mkdir -p "$host_repo"
git -C "$host_repo" init -q
git -C "$host_repo" config user.email qualification@example.invalid
git -C "$host_repo" config user.name "AgentMarshal Qualification"
printf '# host fixture\n' >"$host_repo/README.md"
git -C "$host_repo" add README.md
git -C "$host_repo" commit -qm "host base"
run_ok "host adds AgentMarshal as pinned submodule" \
  git -C "$host_repo" -c protocol.file.allow=always submodule add "$extracted_repo" agentmarshal
git -C "$host_repo" commit -qam "pin AgentMarshal submodule"
run_ok "host gitlink points to extracted snapshot" \
  test "$(git -C "$host_repo/agentmarshal" rev-parse HEAD)" = "$(git -C "$snapshot_dir" rev-parse HEAD)"
run_ok "recursive clone recovers submodule" \
  git -c protocol.file.allow=always clone -q --recurse-submodules "$host_repo" "$recursive_clone"
run_ok "recursive clone doctor works from submodule" \
  "$recursive_clone/agentmarshal/bin/agentmarshal" init --project-root "$recursive_clone" --preset minimal --language en --non-interactive
run_ok "existing clone submodule recovery works" \
  git -c protocol.file.allow=always clone -q "$host_repo" "$existing_clone"
run_ok "submodule update recovers existing clone" \
  git -C "$existing_clone" -c protocol.file.allow=always submodule update --init --recursive
run_ok "existing clone doctor works after recovery" \
  "$existing_clone/agentmarshal/bin/agentmarshal" init --project-root "$existing_clone" --preset minimal --language en --non-interactive

log ""
log "Finished-At: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
log "Result: pass=$pass fail=$fail"

if [[ $fail -ne 0 ]]; then
  log "Qualification: failed"
  exit 1
fi

log "Qualification: passed"
exit 0
