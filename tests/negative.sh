#!/usr/bin/env bash
# negative.sh — негативные тесты на каждый найденный обход (ревью F-002/F-003/
# R-001/R-002/R-003/R-004). Каждый кейс строит изолированный fixture-репозиторий
# и проверяет, что гейт ПАДАЕТ там, где должен (и проходит там, где должен).
#
#   agentmarshal/tests/negative.sh        # exit 0 если все ассерты прошли
set -uo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$TEST_DIR/../scripts" && -d "$TEST_DIR/../agents" ]]; then
  FRAMEWORK_ROOT="$(cd "$TEST_DIR/.." && pwd)"
  HOST_ROOT="$FRAMEWORK_ROOT"
else
  HOST_ROOT="$(cd "$TEST_DIR/../.." && pwd)"
  FRAMEWORK_ROOT="$HOST_ROOT/agentmarshal"
fi
pass=0; fail=0
# assert <ok|fail> "<desc>" <cmd...>
assert() {
  local exp="$1" desc="$2"; shift 2
  local rc=0; "$@" >/tmp/ng.$$ 2>&1 || rc=$?
  if { [[ "$exp" == fail && $rc -ne 0 ]] || [[ "$exp" == ok && $rc -eq 0 ]]; }; then
    echo "  ✅ $desc (exit=$rc)"; ((pass++))
  else
    echo "  ❌ $desc — ожидали '$exp', exit=$rc"; sed 's/^/        /' /tmp/ng.$$ | tail -6; ((fail++))
  fi
}

# ── fixture-репозиторий ─────────────────────────────────────────────────────
FIX="$(mktemp -d)"
FIX_WT="${FIX}.worktree"
FIX_CLONE="${FIX}.clone"
FIX_CI_CLONE="${FIX}.ci-clone"
FIX_READONLY_BIN="${FIX}.readonly-bin"
trap 'rm -rf "$FIX" "$FIX_WT" "$FIX_CLONE" "$FIX_CI_CLONE" "$FIX_READONLY_BIN" /tmp/ng.$$' EXIT
mkdir -p "$FIX/agentmarshal/scripts" "$FIX/agentmarshal/lib" "$FIX/.agents/config" \
    "$FIX/.agents/stats/runs/2026" "$FIX/.agents/tasks/open" "$FIX/.agents/tasks/abandoned/2026" \
    "$FIX/.agents/stats/evaluations/2026" "$FIX/.agents/trials/2026" \
    "$FIX/.agents/reviews/2026" "$FIX/.agents/handoffs/2026" "$FIX/.agents/decisions" "$FIX/.agents/events/2026"
cp "$FRAMEWORK_ROOT"/scripts/{scope-guard,merge-policy,review-readonly,run-agent-task,worktree-lifecycle,task-lifecycle,validate,check-doc-parity,gitflic-ci,record-review-followups,record-agent-stat,record-agent-evaluation,agentmarshal-stats,agentmarshal-config}.sh "$FIX/agentmarshal/scripts/"
cp "$FRAMEWORK_ROOT/lib/runtime-config.sh" "$FIX/agentmarshal/lib/"
cp "$FRAMEWORK_ROOT/lib/project-config.sh" "$FIX/agentmarshal/lib/"
cp -r "$FRAMEWORK_ROOT/agents" "$FIX/agentmarshal/agents"
cp -r "$FRAMEWORK_ROOT/profiles" "$FIX/agentmarshal/profiles"
cp -r "$FRAMEWORK_ROOT/docs" "$FIX/agentmarshal/docs"
cp -r "$FRAMEWORK_ROOT/methodology" "$FIX/agentmarshal/methodology"
cp "$FRAMEWORK_ROOT"/{README,README.ru,README.en,ADOPT,ADOPT.ru,ADOPT.en}.md "$FIX/agentmarshal/"
if [[ -f "$HOST_ROOT/.agents/config/agentmarshal.conf" ]]; then
  cp "$HOST_ROOT/.agents/config/agentmarshal.conf" "$FIX/.agents/config/"
else
  cat > "$FIX/.agents/config/agentmarshal.conf" <<'EOF'
schema=1
review_language=ru
active_roles=lead,frontend,qa
operating_mode=normal
active_milestone=none
backlog_amplification_limit=0.3
worktree_root=../agentmarshal.worktrees
worktree_pattern={alias}
stats_enabled=true
stats_store=.agents/stats/runs
evaluation_store=.agents/stats/evaluations
stats_raw_store=.agents/runs/stats
stats_retention_days=365
EOF
fi
if [[ -f "$HOST_ROOT/.agents/.gitignore" ]]; then
  cp "$HOST_ROOT/.agents/.gitignore" "$FIX/.agents/"
else
  printf 'runs/\ntmp/\n*.log\n' > "$FIX/.agents/.gitignore"
fi
cp "$FRAMEWORK_ROOT/agentmarshal.config.sh" "$FIX/agentmarshal/"
chmod +x "$FIX"/agentmarshal/scripts/*.sh
SG="$FIX/agentmarshal/scripts/scope-guard.sh"; MP="$FIX/agentmarshal/scripts/merge-policy.sh"; VAL="$FIX/agentmarshal/scripts/validate.sh"
GC="$FIX/agentmarshal/scripts/gitflic-ci.sh"
RR="$FIX/agentmarshal/scripts/record-review-followups.sh"
RS="$FIX/agentmarshal/scripts/record-agent-stat.sh"
RE="$FIX/agentmarshal/scripts/record-agent-evaluation.sh"
ST="$FIX/agentmarshal/scripts/agentmarshal-stats.sh"
WL="$FIX/agentmarshal/scripts/worktree-lifecycle.sh"
TL="$FIX/agentmarshal/scripts/task-lifecycle.sh"
AG="$FIX/agentmarshal/agents"
gx() { git -C "$FIX" "$@"; }

gx init -q
gx config user.email lead-agent@agent.example.invalid; gx config user.name "Lead Agent"
gx add -A; gx commit -qm "base"; gx branch -M master
gx update-ref refs/remotes/origin/master master
sgrun() { bash "$SG" --repo "$FIX" --agents-dir "$AG" "$@"; }

echo "== worktree lifecycle =="
wlrun() { bash "$WL" "$@" --project-root "$FIX"; }
assert ok "lifecycle: writable primary metadata" wlrun project-preflight
assert ok "lifecycle: legacy AGENTOPS_PROJECT_ROOT accepted" \
  env AGENTOPS_PROJECT_ROOT="$FIX" bash "$WL" project-preflight
mkdir -p "$FIX_READONLY_BIN"
cat > "$FIX_READONLY_BIN/mktemp" <<'EOF'
#!/usr/bin/env sh
exit 1
EOF
chmod +x "$FIX_READONLY_BIN/mktemp"
assert fail "lifecycle: read-only Git metadata fails before agent launch" \
  env PATH="$FIX_READONLY_BIN:$PATH" bash "$WL" project-preflight --project-root "$FIX"
gx worktree add -q -b lead/lifecycle "$FIX_WT" master
assert ok "lifecycle: registered linked worktree accepted" \
  wlrun worktree-preflight --worktree "$FIX_WT"
git clone -q "$FIX" "$FIX_CLONE"
assert fail "lifecycle: standalone clone rejected" \
  wlrun worktree-preflight --worktree "$FIX_CLONE"

echo integrated > "$FIX_WT/lifecycle.txt"
git -C "$FIX_WT" add lifecycle.txt
git -C "$FIX_WT" commit -qm "lifecycle fixture"
LIFECYCLE_SHA="$(git -C "$FIX_WT" rev-parse HEAD)"
cp "$FIX_WT/lifecycle.txt" "$FIX/lifecycle.txt"
assert fail "lifecycle: copied files without primary ref are not finalized" \
  wlrun finalize --integration-sha "$LIFECYCLE_SHA"
rm -f "$FIX/lifecycle.txt"
gx merge -q --ff-only lead/lifecycle
assert ok "lifecycle: exact clean primary SHA finalized" \
  wlrun finalize --integration-sha "$LIFECYCLE_SHA" --integration-ref master
assert fail "lifecycle: cleanup blocked before exact upstream push" \
  wlrun cleanup-ready --worktree "$FIX_WT" --integration-sha "$LIFECYCLE_SHA" \
    --integration-ref master --require-pushed
gx update-ref refs/remotes/origin/master master
gx remote add origin "$FIX"
gx config branch.master.remote origin
gx config branch.master.merge refs/heads/master
assert ok "lifecycle: cleanup allowed after integration and push" \
  wlrun cleanup-ready --worktree "$FIX_WT" --integration-sha "$LIFECYCLE_SHA" \
    --integration-ref master --require-pushed

echo "== task completion lifecycle =="
cat > "$FIX/.agents/tasks/open/CR-930-completion.md" <<'EOF'
# CR-930: completion fixture
Owner: lead
Type: process
Priority: P1
Status: in_review
Created: 2026-06-23
EOF
gx add .agents/tasks/open/CR-930-completion.md
gx commit -qm "open completion fixture"
gx switch -qc feat/CR-930-completion master
echo completed > "$FIX/completion.txt"
gx add completion.txt
gx commit -qm "CR-930 implementation"
COMPLETION_REVIEWED="$(gx rev-parse HEAD)"
gx switch -q master
cat > "$FIX/.agents/reviews/2026/CR-930-review.md" <<EOF
Task: CR-930
Reviewer-Role: qa
Reviewer-Vendor: claude
Reviewer-Model: fixture
Reviewer-Email: qa-agent@agent.example.invalid
Reviewed-Commit: $COMPLETION_REVIEWED
Verdict: approved
Finding-IDs: none
EOF
gx add .agents/reviews/2026/CR-930-review.md
gx commit -qm "record CR-930 review"
assert fail "task completion: reviewed SHA absent from target history" \
  bash "$TL" complete --project-root "$FIX" --task CR-930 \
    --review-task CR-930 --review-file .agents/reviews/2026/CR-930-review.md \
    --reviewed-commit "$COMPLETION_REVIEWED" --target-ref master --dry-run
gx merge -q --no-ff feat/CR-930-completion -m "merge CR-930"
COMPLETION_MERGED="$(gx rev-parse HEAD)"
gx update-ref refs/remotes/origin/master master
assert fail "task completion: direct target branch mutation forbidden" \
  bash "$TL" complete --project-root "$FIX" --task CR-930 \
    --review-task CR-930 --review-file .agents/reviews/2026/CR-930-review.md \
    --reviewed-commit "$COMPLETION_REVIEWED" --target-ref origin/master --dry-run
gx switch -qc completion/CR-930 origin/master
BOLD_COMPLETION_REVIEW="$FIX_READONLY_BIN/CR-930-bold-review.md"
cp "$FIX/.agents/reviews/2026/CR-930-review.md" "$BOLD_COMPLETION_REVIEW"
sed -i \
  -e 's/^Task: /**Task:** /' \
  -e 's/^Reviewed-Commit: /**Reviewed-Commit:** /' \
  -e 's/^Verdict: /**Verdict:** /' \
  "$BOLD_COMPLETION_REVIEW"
assert ok "task completion: Markdown-bold review metadata accepted" \
  bash "$TL" complete --project-root "$FIX" --task CR-930 \
    --review-task CR-930 --review-file "$BOLD_COMPLETION_REVIEW" \
    --reviewed-commit "$COMPLETION_REVIEWED" --target-ref origin/master --dry-run
assert ok "task completion: post-merge dry-run succeeds" \
  bash "$TL" complete --project-root "$FIX" --task CR-930 \
    --review-task CR-930 --review-file .agents/reviews/2026/CR-930-review.md \
    --reviewed-commit "$COMPLETION_REVIEWED" --target-ref origin/master --dry-run
assert ok "task completion: post-merge task moves to done" \
  bash "$TL" complete --project-root "$FIX" --task CR-930 \
    --review-task CR-930 --review-file .agents/reviews/2026/CR-930-review.md \
    --reviewed-commit "$COMPLETION_REVIEWED" --target-ref origin/master \
    --merged-commit "$COMPLETION_MERGED" --completed-at 2026-06-23T05:00:00Z
gx add -A
gx commit -qm "complete CR-930"
COMPLETION_HEAD="$(gx rev-parse HEAD)"
COMPLETION_GATE_REVIEW="$FIX_READONLY_BIN/CR-930-completion-review.md"
cat > "$COMPLETION_GATE_REVIEW" <<EOF
Task: CR-930
Reviewer-Role: qa
Reviewer-Vendor: claude
Reviewer-Model: fixture
Reviewer-Email: qa-agent@agent.example.invalid
Reviewed-Commit: $COMPLETION_HEAD
Verdict: approved
Finding-IDs: none
EOF
assert ok "merge-policy: protected-branch completion MR accepted" \
  env AGENTMARSHAL_PIPELINE_OK_SHA="$COMPLETION_HEAD" bash "$MP" \
    --branch completion/CR-930 --head "$COMPLETION_HEAD" \
    --base origin/master --task CR-930 \
    --review-file "$COMPLETION_GATE_REVIEW"
gx switch -qc completion/CR-930-bad completion/CR-930
echo forbidden > "$FIX/forbidden.txt"
gx add forbidden.txt
gx commit -qm "completion touches implementation path"
BAD_COMPLETION_HEAD="$(gx rev-parse HEAD)"
BAD_COMPLETION_REVIEW="$FIX_READONLY_BIN/CR-930-bad-review.md"
sed "s/$COMPLETION_HEAD/$BAD_COMPLETION_HEAD/" \
  "$COMPLETION_GATE_REVIEW" > "$BAD_COMPLETION_REVIEW"
assert fail "merge-policy: completion MR rejects non-journal path" \
  env AGENTMARSHAL_PIPELINE_OK_SHA="$BAD_COMPLETION_HEAD" bash "$MP" \
    --branch completion/CR-930-bad --head "$BAD_COMPLETION_HEAD" \
    --base origin/master --task CR-930 \
    --review-file "$BAD_COMPLETION_REVIEW"
gx switch -q completion/CR-930
assert ok "task completion: done audit verifies graph and review digest" \
  bash "$TL" audit --project-root "$FIX"
git clone -q --single-branch --branch completion/CR-930 "$FIX" "$FIX_CI_CLONE"
CI_CLONE_HEAD="$(git -C "$FIX_CI_CLONE" rev-parse HEAD)"
assert fail "task completion: missing target ref fails without explicit CI fallback" \
  bash "$FIX_CI_CLONE/agentmarshal/scripts/task-lifecycle.sh" audit \
    --project-root "$FIX_CI_CLONE"
assert fail "task completion: CI fallback rejects mismatched attested SHA" \
  env CI_COMMIT_REF_NAME=completion/CR-930 CI_COMMIT_SHA="$CI_CLONE_HEAD" \
    AGENTMARSHAL_AUDIT_COMPLETION_HEAD=0000000000000000000000000000000000000000 \
    AGENTMARSHAL_AUDIT_TARGET_BRANCH=master \
    bash "$FIX_CI_CLONE/agentmarshal/scripts/task-lifecycle.sh" audit \
      --project-root "$FIX_CI_CLONE"
assert fail "task completion: CI fallback rejects mismatched target branch" \
  env CI_COMMIT_REF_NAME=completion/CR-930 CI_COMMIT_SHA="$CI_CLONE_HEAD" \
    AGENTMARSHAL_AUDIT_COMPLETION_HEAD="$CI_CLONE_HEAD" \
    AGENTMARSHAL_AUDIT_TARGET_BRANCH=not-master \
    bash "$FIX_CI_CLONE/agentmarshal/scripts/task-lifecycle.sh" audit \
      --project-root "$FIX_CI_CLONE"
assert ok "task completion: exact CI completion head supports single-branch clone" \
  env CI_COMMIT_REF_NAME=completion/CR-930 CI_COMMIT_SHA="$CI_CLONE_HEAD" \
    AGENTMARSHAL_AUDIT_COMPLETION_HEAD="$CI_CLONE_HEAD" \
    AGENTMARSHAL_AUDIT_TARGET_BRANCH=master \
    bash "$FIX_CI_CLONE/agentmarshal/scripts/task-lifecycle.sh" audit \
      --project-root "$FIX_CI_CLONE"
git -C "$FIX_CI_CLONE" switch -q -c refactor/CR-930-validate
CI_REFACTOR_HEAD="$(git -C "$FIX_CI_CLONE" rev-parse HEAD)"
assert ok "task completion: exact CI branch head supports single-branch validate audit" \
  env CI_COMMIT_REF_NAME=refactor/CR-930-validate CI_COMMIT_SHA="$CI_REFACTOR_HEAD" \
    AGENTMARSHAL_AUDIT_COMPLETION_HEAD="$CI_REFACTOR_HEAD" \
    AGENTMARSHAL_AUDIT_TARGET_BRANCH=master \
    bash "$FIX_CI_CLONE/agentmarshal/scripts/task-lifecycle.sh" audit \
      --project-root "$FIX_CI_CLONE"
COMPLETION_CANONICAL="$FIX/.agents/reviews/2026/CR-930-completion-${COMPLETION_REVIEWED:0:12}.md"
cp "$COMPLETION_CANONICAL" "$FIX/completion-review.backup"
printf '\ntampered\n' >> "$COMPLETION_CANONICAL"
assert fail "task completion: review tampering invalidates done task" \
  bash "$TL" audit --project-root "$FIX"
mv "$FIX/completion-review.backup" "$COMPLETION_CANONICAL"
sed -i 's/^Target-Branch: master$/Target-Branch: missing-target/' \
  "$FIX/.agents/tasks/done/2026/CR-930-completion.md"
assert fail "task completion: missing target branch invalidates done task" \
  bash "$TL" audit --project-root "$FIX"
sed -i 's/^Target-Branch: missing-target$/Target-Branch: master/' \
  "$FIX/.agents/tasks/done/2026/CR-930-completion.md"
gx switch -q master
rm -f "$FIX/completion.txt" \
  "$FIX/.agents/tasks/open/CR-930-completion.md" \
  "$FIX/.agents/reviews/2026/CR-930-review.md"
gx add -A
gx commit -qm "remove completion fixture from target"

echo "== scope-guard =="
assert ok "provenance: completion branch classified as integration" \
  sgrun --branch completion/CR-930 --base origin/master --head completion/CR-930
assert fail "fail-closed: невалидный base" sgrun --branch fe/x --base no-such-ref --head master
assert fail "unknown prefix --strict" sgrun --branch zzz/x --base master --head master --strict
assert ok   "unknown prefix без --strict (skip)" sgrun --branch zzz/x --base master --head master

gx switch -qc fe/bad master; mkdir -p "$FIX/src/backend"; echo x > "$FIX/src/backend/f.py"; gx add -A; gx commit -qm "fe touches backend"
assert fail "role fe трогает backend (вне scope)" sgrun --branch fe/bad --base master --head fe/bad
gx switch -q master

gx switch -qc fe/good master; mkdir -p "$FIX/src/frontend"; echo x > "$FIX/src/frontend/f.tsx"; gx add -A; gx commit -qm "fe touches frontend"
assert ok   "role fe в своём scope" sgrun --branch fe/good --base master --head fe/good
gx switch -q master

# provenance: persona-коммит вне своего scope на integration-ветке
gx switch -qc feat/integ master
gx -c user.email=qa-agent@agent.example.invalid -c user.name="QA Agent" commit -q --allow-empty -m placeholder
mkdir -p "$FIX/src/backend"; echo y > "$FIX/src/backend/sneak.py"; gx add -A
gx -c user.email=qa-agent@agent.example.invalid -c user.name="QA Agent" commit -qm "qa sneaks backend via generic"
assert fail "provenance: qa вне scope на integration" sgrun --branch feat/integ --base master --head feat/integ
gx switch -q master

# provenance: lead на integration — без ограничений
gx switch -qc feat/leadok master; mkdir -p "$FIX/src/backend"; echo z > "$FIX/src/backend/leadfile.py"; gx add -A; gx commit -qm "lead on integration"
assert ok   "provenance: lead на integration ок" sgrun --branch feat/leadok --base master --head feat/leadok
gx switch -q master

# provenance: qa пишет только в reviews/ (в своём scope) на integration — ок
gx switch -qc feat/qareview master
echo "x" > "$FIX/.agents/reviews/2026/scratch.md"; gx add -A
gx -c user.email=qa-agent@agent.example.invalid -c user.name="QA Agent" commit -qm "qa review-only on integration"
assert ok   "provenance: qa review-only на integration ок" sgrun --branch feat/qareview --base master --head feat/qareview
gx switch -q master; rm -f "$FIX/.agents/reviews/2026/scratch.md"

# API-manifest mode: те же policy-проверки без доступных git refs/history.
API_CHANGED="$FIX/api-changed"; API_COMMITS="$FIX/api-commits"
: > "$API_COMMITS"
printf 'src/backend/sneak.py\n' > "$API_CHANGED"
assert fail "API mode: role fe вне scope без git refs" \
  sgrun --branch fe/api --base no-such-ref --changed-files "$API_CHANGED" --commit-files "$API_COMMITS"
printf 'src/frontend/good.tsx\n' > "$API_CHANGED"
assert ok "API mode: role fe в scope без git refs" \
  sgrun --branch fe/api --base no-such-ref --changed-files "$API_CHANGED" --commit-files "$API_COMMITS"

: > "$API_CHANGED"
printf 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\tqa-agent@agent.example.invalid\tsrc/backend/sneak.py\n' > "$API_COMMITS"
assert fail "API mode: provenance qa вне scope без git refs" \
  sgrun --branch feat/api --base no-such-ref --changed-files "$API_CHANGED" --commit-files "$API_COMMITS"
printf 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb\tqa-agent@agent.example.invalid\t.agents/reviews/2026/api.md\n' > "$API_COMMITS"
assert ok "API mode: provenance qa в scope без git refs" \
  sgrun --branch feat/api --base no-such-ref --changed-files "$API_CHANGED" --commit-files "$API_COMMITS"
printf 'bad\tqa-agent@agent.example.invalid\tsrc/backend/x.py\textra\n' > "$API_COMMITS"
assert fail "API mode: malformed commit manifest fail-closed" \
  sgrun --branch feat/api --base no-such-ref --changed-files "$API_CHANGED" --commit-files "$API_COMMITS"

echo "== merge-policy =="
# рабочая be-ветка с коммитом be-agent в своём scope + task CR-900
mkdir -p "$FIX/.agents/tasks/open"
cat > "$FIX/.agents/tasks/open/CR-900-test.md" <<'EOF'
# CR-900: fixture task
Owner: backend
Type: feature
Priority: P2
Status: in_progress
Created: 2026-06-21
EOF
gx switch -qc be/CR-900 master
mkdir -p "$FIX/.agents/events/2026/CR-900"
cat > "$FIX/.agents/events/2026/CR-900/qa-evidence.md" <<'EOF'
id: CR-900-EV-001
task: CR-900
type: note
created_at: 2026-06-23T00:00:00Z
status: done

# QA evidence only
EOF
gx add .agents/events/2026/CR-900/qa-evidence.md
gx -c user.email=qa-agent@agent.example.invalid -c user.name="QA Agent" \
  commit -qm "qa: CR-900 evidence only"
mkdir -p "$FIX/src/backend/app/cars"; echo c > "$FIX/src/backend/app/cars/x.py"
gx add -A
gx -c user.email=be-agent@agent.example.invalid -c user.name="Backend Agent" commit -qm "be: CR-900 cars feature"
HSHA="$(gx rev-parse be/CR-900)"
mprun() { bash "$MP" --branch be/CR-900 --head "$HSHA" --base master "$@"; }
write_review() { # $1=reviewed-commit $2=verdict $3=reviewer-email
  mkdir -p "$FIX/.agents/reviews/2026"
  cat > "$FIX/.agents/reviews/2026/CR-900-review.md" <<EOF
Task: CR-900
Reviewer-Role: qa
Reviewer-Vendor: codex
Reviewer-Model: gpt-5.5
Reviewer-Email: ${3:-qa-agent@agent.example.invalid}
Reviewed-Commit: $1
Verdict: $2
EOF
}

# no task → fail (ветка be/, task обязателен; убираем CR из сообщения нельзя, даём --task пустым через отдельную ветку)
gx switch -qc be/notask master; mkdir -p "$FIX/src/backend/app/cars"; echo n > "$FIX/src/backend/app/cars/n.py"; gx add -A
gx -c user.email=be-agent@agent.example.invalid commit -qm "be no task ref here"
assert fail "merge-policy: agent-ветка без task ID" bash "$MP" --branch be/notask --head "$(gx rev-parse be/notask)" --base master
gx switch -q be/CR-900   # рабочее дерево с CR-900-test.md (merge-policy читает журнал с ФС)

sed -i 's/Status: in_progress/Status: in_review/' "$FIX/.agents/tasks/open/CR-900-test.md"
write_review "$HSHA" approved qa-agent@agent.example.invalid
assert fail "merge-policy: pipeline не подтверждён" mprun --task CR-900
assert ok   "merge-policy: всё ок (approved+независим+pipeline)" env AGENTMARSHAL_PIPELINE_OK_SHA="$HSHA" bash "$MP" --branch be/CR-900 --head "$HSHA" --base master --task CR-900
cp "$FIX/.agents/reviews/2026/CR-900-review.md" "$FIX/CR-900-raw-review.md"
rm "$FIX/.agents/reviews/2026/CR-900-review.md"
assert ok "merge-policy: explicit raw review file accepted" \
  env AGENTMARSHAL_PIPELINE_OK_SHA="$HSHA" bash "$MP" --branch be/CR-900 \
    --head "$HSHA" --base master --task CR-900 \
    --review-file "$FIX/CR-900-raw-review.md"
sed -i \
  -e 's/^Task: /**Task:** /' \
  -e 's/^Reviewer-Role: /**Reviewer-Role:** /' \
  -e 's/^Reviewer-Email: /**Reviewer-Email:** /' \
  -e 's/^Reviewed-Commit: /**Reviewed-Commit:** /' \
  -e 's/^Verdict: /**Verdict:** /' \
  "$FIX/CR-900-raw-review.md"
assert ok "merge-policy: Markdown-bold review metadata accepted" \
  env AGENTMARSHAL_PIPELINE_OK_SHA="$HSHA" bash "$MP" --branch be/CR-900 \
    --head "$HSHA" --base master --task CR-900 \
    --review-file "$FIX/CR-900-raw-review.md"
mv "$FIX/CR-900-raw-review.md" "$FIX/.agents/reviews/2026/CR-900-review.md"
sed -i 's/Status: in_review/Status: in_progress/' "$FIX/.agents/tasks/open/CR-900-test.md"
assert fail "merge-policy: task must be in_review" \
  env AGENTMARSHAL_PIPELINE_OK_SHA="$HSHA" bash "$MP" --branch be/CR-900 \
    --head "$HSHA" --base master --task CR-900
sed -i 's/Status: in_progress/Status: in_review/' "$FIX/.agents/tasks/open/CR-900-test.md"

write_review "deadbeef1234567" approved qa-agent@agent.example.invalid
assert fail "merge-policy: stale review (reviewed≠head)" env AGENTMARSHAL_PIPELINE_OK_SHA="$HSHA" bash "$MP" --branch be/CR-900 --head "$HSHA" --base master --task CR-900

write_review "$HSHA" changes_required qa-agent@agent.example.invalid
assert fail "merge-policy: verdict changes_required" env AGENTMARSHAL_PIPELINE_OK_SHA="$HSHA" bash "$MP" --branch be/CR-900 --head "$HSHA" --base master --task CR-900

write_review "$HSHA" approved be-agent@agent.example.invalid
assert fail "merge-policy: reviewer == writer (be)" env AGENTMARSHAL_PIPELINE_OK_SHA="$HSHA" bash "$MP" --branch be/CR-900 --head "$HSHA" --base master --task CR-900

assert ok   "merge-policy: emergency override" env AGENTMARSHAL_SKIP_MERGE_POLICY=1 bash "$MP" --branch be/CR-900 --head "$HSHA" --base master
rm -f "$FIX/.agents/reviews/2026/CR-900-review.md" "$FIX/.agents/tasks/open/CR-900-test.md"
rm -rf "$FIX/.agents/events/2026/CR-900"

echo "== gitflic-ci =="
mkdir -p "$FIX/gitflic-fixtures" "$FIX/gitflic-bin"
cat > "$FIX/gitflic-fixtures/pipelines-0.json" <<'EOF'
{
  "_embedded": {
    "restPipelineModelList": [
      {"localId": 190, "status": "RUNNING", "commitId": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", "ref": "feat/new"},
      {"localId": 188, "status": "SUCCESS", "commitId": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "ref": "master"}
    ]
  },
  "page": {"size": 2, "totalElements": 3, "totalPages": 2, "number": 0}
}
EOF
cat > "$FIX/gitflic-fixtures/pipelines-1.json" <<'EOF'
{
  "_embedded": {
    "restPipelineModelList": [
      {"localId": 189, "status": "FAILED", "duration": 145, "commitId": "d85e9c05170e6af4680683dba5bcb2c36d753f84", "ref": "feat/agentmarshal-phase1"}
    ]
  },
  "page": {"size": 2, "totalElements": 3, "totalPages": 2, "number": 1}
}
EOF
cat > "$FIX/gitflic-fixtures/jobs-189.json" <<'EOF'
{
  "_embedded": {
    "restPipelineJobModelList": [
      {"id": "0b82c7b3-1210-4c8a-b61c-b7fec8e4869d", "localId": 389, "name": "agentmarshal_tests", "stageName": "gate", "status": "FAILED", "pipelineLocalId": 189},
      {"id": "a4151fbe-19a1-467e-b93c-c4f48fe2a24e", "localId": 387, "name": "scope_guard", "stageName": "gate", "status": "SUCCESS", "pipelineLocalId": 189}
    ]
  },
  "page": {"size": 100, "totalElements": 2, "totalPages": 1, "number": 0}
}
EOF
cat > "$FIX/gitflic-fixtures/job-389.json" <<'EOF'
{"id": "0b82c7b3-1210-4c8a-b61c-b7fec8e4869d", "localId": 389, "name": "agentmarshal_tests", "stageName": "gate", "status": "FAILED", "pipelineLocalId": 189}
EOF
cat > "$FIX/gitflic-bin/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
out=""; url=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|-w|-H) [[ "$1" == -o ]] && out="$2"; shift 2 ;;
    -s|-S|-sS) shift ;;
    *) url="$1"; shift ;;
  esac
done
case "$url" in
  */cicd/pipeline/189/jobs*) src="$MOCK_GITFLIC_FIXTURES/jobs-189.json"; code=200 ;;
  */cicd/job/389) src="$MOCK_GITFLIC_FIXTURES/job-389.json"; code=200 ;;
  */cicd/pipeline*page=1*) src="$MOCK_GITFLIC_FIXTURES/pipelines-1.json"; code=200 ;;
  */cicd/pipeline*) src="$MOCK_GITFLIC_FIXTURES/pipelines-0.json"; code=200 ;;
  *) src=""; code=404 ;;
esac
if [[ -n "$src" ]]; then cp "$src" "$out"; else printf '{"error":"not found"}\n' > "$out"; fi
printf '%s' "$code"
EOF
chmod +x "$FIX/gitflic-bin/curl"
gcrun() {
  env PATH="$FIX/gitflic-bin:$PATH" HOME="$FIX/home" \
    GITFLIC_API_TOKEN=fixture GITFLIC_API_BASE=https://mock.invalid \
    GITFLIC_OWNER=fixture GITFLIC_PROJECT=fixture \
    AGENTMARSHAL_GITFLIC_PAGE_SIZE=2 MOCK_GITFLIC_FIXTURES="$FIX/gitflic-fixtures" \
    bash "$GC" "$@"
}
pipeline_189_exact() { [[ "$(gcrun pipeline 189 | jq -r '.localId')" == 189 ]]; }
sha_189_exact() {
  [[ "$(gcrun sha d85e9c05170e6af4680683dba5bcb2c36d753f84 | jq -r '.[0].localId')" == 189 ]]
}
jobs_189_exact() { [[ "$(gcrun jobs 189 | jq -r '.[1].name')" == agentmarshal_tests ]]; }
job_389_exact() { [[ "$(gcrun job 389 | jq -r '.pipelineLocalId')" == 189 ]]; }
diagnose_189() { gcrun diagnose 189 | grep -F "job #389 FAILED" >/dev/null; }
assert ok "gitflic-ci: exact pipeline найден на второй странице" pipeline_189_exact
assert ok "gitflic-ci: exact SHA фильтруется на клиенте" sha_189_exact
assert ok "gitflic-ci: jobs pipeline доступны" jobs_189_exact
assert ok "gitflic-ci: job metadata доступна" job_389_exact
assert ok "gitflic-ci: diagnose показывает упавшую job" diagnose_189
assert fail "gitflic-ci: отсутствующий pipeline fail-closed" gcrun pipeline 999
assert fail "gitflic-ci: FAILED pipeline не проходит wait" gcrun wait 189 1 1
assert ok "gitflic-ci: SUCCESS pipeline проходит wait" gcrun wait 188 1 1

echo "== review triage recorder =="
cat > "$FIX/.agents/tasks/open/CR-010-source.md" <<'EOF'
# CR-010: source review task
Owner: lead
Type: feature
Priority: P1
Status: in_review
Created: 2026-06-21
EOF
cat > "$FIX/approved-review.md" <<'EOF'
Task: CR-010
Reviewer-Role: qa
Reviewed-Commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Verdict: approved
Finding-IDs: F1, F2, F3

```json follow-up-manifest
{
  "schema": 1,
  "review_findings": ["F1", "F2", "F3"],
  "tasks": [
    {
      "title": "Harden transport tests",
      "type": "technical_debt",
      "priority": "P2",
      "owner": "lead",
      "source_findings": ["F1", "F2"],
      "due_before": "dispatcher",
      "risk": "Transport errors are not covered.",
      "acceptance_criteria": ["HTTP errors are tested.", "Timeout is tested."],
      "scope": ["agentmarshal/scripts/", "agentmarshal/tests/"]
    }
  ],
  "non_task": [
    {
      "source_findings": ["F3"],
      "disposition": "accepted_risk",
      "rationale": "Single-user fixture has no shared process table."
    }
  ]
}
```
EOF
rrrun() {
  (
    cd "$FIX"
    AGENTMARSHAL_TODAY=2026-06-22 \
    AGENTMARSHAL_NOW=2026-06-21T17:00:00Z \
    AGENTMARSHAL_STAMP=20260621T170000Z \
      bash "$RR" "$@"
  )
}
recorder_creates() {
  rrrun --review "$FIX/approved-review.md" >/dev/null &&
    grep -q '^Type: technical_debt$' "$FIX/.agents/tasks/open/CR-011-review-follow-up-f1-f2.md" &&
    grep -q '^Priority: P2$' "$FIX/.agents/tasks/open/CR-011-review-follow-up-f1-f2.md" &&
    grep -q '^Source-Findings: F1, F2$' "$FIX/.agents/tasks/open/CR-011-review-follow-up-f1-f2.md" &&
    grep -q '^Due-Before: dispatcher$' "$FIX/.agents/tasks/open/CR-011-review-follow-up-f1-f2.md" &&
    grep -q 'F3: `accepted_risk`' "$FIX/.agents/events/2026/CR-010/20260621T170000Z-lead-review-triage.md"
}
recorder_idempotent() {
  rrrun --review "$FIX/approved-review.md" >/dev/null &&
    [[ "$(find "$FIX/.agents/tasks" -name 'CR-011-review-follow-up-f1-f2.md' | wc -l)" == 1 ]] &&
    [[ "$(find "$FIX/.agents/events/2026/CR-010" -name '*review-triage.md' | wc -l)" == 1 ]]
}
cp "$FIX/approved-review.md" "$FIX/rejected-review.md"
sed -i 's/Verdict: approved/Verdict: rejected/' "$FIX/rejected-review.md"
jq '.review_findings += ["F4"]' \
  < <(awk '/^```json follow-up-manifest$/{f=1;next} f&&/^```$/{exit} f{print}' "$FIX/approved-review.md") \
  > "$FIX/incomplete-manifest.json"
sed -i 's/^operating_mode=.*/operating_mode=normal/' "$FIX/.agents/config/agentmarshal.conf"
assert ok "recorder: decimal CR-010 → CR-011 создаёт task и triage event" recorder_creates
assert ok "recorder: повторный запуск идемпотентен" recorder_idempotent
assert fail "recorder: rejected review не материализуется" rrrun --review "$FIX/rejected-review.md"
assert fail "recorder: неполное покрытие findings блокируется" \
  rrrun --review "$FIX/approved-review.md" --manifest "$FIX/incomplete-manifest.json"
assert ok "validate: recorder-артефакты валидны" bash "$VAL" --journal
sed -i 's/^operating_mode=.*/operating_mode=cutoff_freeze/' "$FIX/.agents/config/agentmarshal.conf"
rm -rf "$FIX/.agents/events/2026/CR-010"
rm -f "$FIX/.agents/tasks/open/CR-011-review-follow-up-f1-f2.md"
cat > "$FIX/.agents/tasks/open/CR-010-source.md" <<'EOF'
# CR-010: source review task
Owner: lead
Type: feature
Priority: P1
Status: in_review
Created: 2026-06-21
EOF

echo "== cutoff admission =="
cutoff_cfg="$FIX/.agents/config/agentmarshal.conf"
cp "$cutoff_cfg" "$FIX/agentmarshal.conf.cutoff.bak"
cutoff_run() {
  (
    cd "$FIX"
    AGENTMARSHAL_TODAY=2026-06-23 \
    AGENTMARSHAL_NOW=2026-06-23T04:00:00Z \
    AGENTMARSHAL_STAMP=20260623T040000Z \
      bash "$RR" "$@"
  )
}
cat > "$FIX/cutoff-review.md" <<'EOF'
Task: CR-010
Reviewer-Role: qa
Reviewed-Commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Verdict: approved
Finding-IDs: F1

```json follow-up-manifest
{
  "schema": 1,
  "review_findings": ["F1"],
  "tasks": [
    {
      "title": "Cutoff fixture task",
      "type": "technical_debt",
      "priority": "P3",
      "owner": "lead",
      "source_findings": ["F1"],
      "due_before": "agentmarshal-v0.1-cutoff",
      "risk": "P3 task should be rejected in cutoff freeze.",
      "acceptance_criteria": ["It should never be admitted in cutoff freeze."],
      "scope": ["agentmarshal/tests/"]
    }
  ],
  "non_task": []
}
```
EOF
sed -i 's/^operating_mode=.*/operating_mode=normal/' "$cutoff_cfg"
assert ok "cutoff: normal mode keeps legacy task creation" \
  cutoff_run --review "$FIX/cutoff-review.md" >/dev/null
rm -f "$FIX/.agents/tasks/open/CR-011-cutoff-fixture-task.md" \
  "$FIX/.agents/events/2026/CR-010/20260623T040000Z-lead-review-triage.md"
sed -i 's/^operating_mode=.*/operating_mode=cutoff_freeze/' "$cutoff_cfg"
cat > "$FIX/cutoff-p3-review.md" <<'EOF'
Task: CR-010
Reviewer-Role: qa
Reviewed-Commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Verdict: approved
Finding-IDs: F1

```json follow-up-manifest
{
  "schema": 1,
  "review_findings": ["F1"],
  "tasks": [
    {
      "title": "Cutoff P3 task",
      "type": "technical_debt",
      "priority": "P3",
      "owner": "lead",
      "source_findings": ["F1"],
      "due_before": "agentmarshal-v0.1-cutoff",
      "risk": "Forbidden in cutoff freeze.",
      "acceptance_criteria": ["Blocked in cutoff freeze."],
      "scope": ["agentmarshal/tests/"]
    }
  ],
  "non_task": []
}
```
EOF
assert fail "cutoff: cutoff_freeze rejects new P3 task" \
  cutoff_run --review "$FIX/cutoff-p3-review.md"
cat > "$FIX/cutoff-p2-review.md" <<'EOF'
Task: CR-010
Reviewer-Role: qa
Reviewed-Commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Verdict: approved
Finding-IDs: F1

```json follow-up-manifest
{
  "schema": 1,
  "review_findings": ["F1"],
  "tasks": [
    {
      "title": "Cutoff P2 wrong milestone",
      "type": "technical_debt",
      "priority": "P2",
      "owner": "lead",
      "source_findings": ["F1"],
      "due_before": "other-milestone",
      "risk": "P2 tasks must stay on the active milestone.",
      "acceptance_criteria": ["Blocked when Due-Before differs."],
      "scope": ["agentmarshal/tests/"]
    }
  ],
  "non_task": []
}
```
EOF
assert fail "cutoff: P2 with Due-Before != active_milestone rejects" \
  cutoff_run --review "$FIX/cutoff-p2-review.md"
cat > "$FIX/cutoff-post-cutoff-review.md" <<'EOF'
Task: CR-010
Reviewer-Role: qa
Reviewed-Commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Verdict: approved
Finding-IDs: F1

```json follow-up-manifest
{
  "schema": 1,
  "review_findings": ["F1"],
  "tasks": [],
  "non_task": [
    {
      "source_findings": ["F1"],
      "disposition": "post_cutoff",
      "rationale": "This is acceptable to defer past the cutoff."
    }
  ]
}
```
EOF
assert ok "cutoff: post_cutoff non_task is accepted" \
  cutoff_run --review "$FIX/cutoff-post-cutoff-review.md" >/dev/null
cat > "$FIX/cutoff-existing-task-review.md" <<'EOF'
Task: CR-010
Reviewer-Role: qa
Reviewed-Commit: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
Verdict: approved
Finding-IDs: F1

```json follow-up-manifest
{
  "schema": 1,
  "review_findings": ["F1"],
  "tasks": [],
  "non_task": [
    {
      "source_findings": ["F1"],
      "disposition": "existing_task",
      "rationale": "This finding already maps to a task."
    }
  ]
}
```
EOF
assert fail "cutoff: existing_task requires target" \
  cutoff_run --review "$FIX/cutoff-existing-task-review.md"
sed -i 's/^operating_mode=.*/operating_mode=cutoff_freeze/' "$cutoff_cfg"
mv "$FIX/agentmarshal.conf.cutoff.bak" "$cutoff_cfg"

echo "== validate =="
valrun() { bash "$VAL" --journal; }
profvalrun() { bash "$VAL" --profiles; }
docsvalrun() { bash "$VAL" --docs; }
configvalrun() { bash "$VAL" --config; }
put() { mkdir -p "$(dirname "$1")"; cat > "$1"; }
assert ok "validate: host config валиден" configvalrun
cp "$FIX/.agents/config/agentmarshal.conf" "$FIX/agentmarshal.conf.bak"
sed -i 's/^review_language=ru$/review_language=RUSSIAN/' "$FIX/.agents/config/agentmarshal.conf"
assert fail "validate: невалидный review_language" configvalrun
cp "$FIX/agentmarshal.conf.bak" "$FIX/.agents/config/agentmarshal.conf"
sed -i 's/^active_roles=.*/active_roles=lead,unknown/' "$FIX/.agents/config/agentmarshal.conf"
assert fail "validate: неизвестная active role" configvalrun
cp "$FIX/agentmarshal.conf.bak" "$FIX/.agents/config/agentmarshal.conf"
sed -i 's#^worktree_root=.*#worktree_root=.agents/worktrees#' "$FIX/.agents/config/agentmarshal.conf"
assert fail "validate: worktree_root внутри repo запрещён" configvalrun
cp "$FIX/agentmarshal.conf.bak" "$FIX/.agents/config/agentmarshal.conf"
sed -i 's#^stats_store=.*#stats_store=.agents/stats/../../escaped#' "$FIX/.agents/config/agentmarshal.conf"
assert fail "validate: stats_store traversal запрещён" configvalrun
cp "$FIX/agentmarshal.conf.bak" "$FIX/.agents/config/agentmarshal.conf"
assert ok "validate: qa-readonly profile валиден" profvalrun
assert ok "validate: framework docs/ADR валидны" docsvalrun
cp "$FIX/agentmarshal/docs/adr/ADR-0001-ai-team-workflow.md" "$FIX/adr-0001.bak"
sed -i 's/^Status: Accepted$/Status: Mystery/' "$FIX/agentmarshal/docs/adr/ADR-0001-ai-team-workflow.md"
assert fail "validate: неизвестный framework ADR status" docsvalrun
cp "$FIX/adr-0001.bak" "$FIX/agentmarshal/docs/adr/ADR-0001-ai-team-workflow.md"
cp "$FIX/agentmarshal/profiles/qa-readonly.yaml" "$FIX/qa-readonly.yaml.bak"
sed -i 's/^write_policy: none$/write_policy: chaos/' "$FIX/agentmarshal/profiles/qa-readonly.yaml"
assert fail "validate: неизвестный write_policy профиля" profvalrun
cp "$FIX/qa-readonly.yaml.bak" "$FIX/agentmarshal/profiles/qa-readonly.yaml"
sed -i '/^  - glob$/a\\  - shell' "$FIX/agentmarshal/profiles/qa-readonly.yaml"
assert fail "validate: read-only profile не получает shell" profvalrun
cp "$FIX/qa-readonly.yaml.bak" "$FIX/agentmarshal/profiles/qa-readonly.yaml"
# launcher читает profile и выдаёт Claude только safe-mode + Read/Grep/Glob.
mkdir -p "$FIX/bin"
cat > "$FIX/bin/claude" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "${MOCK_CLAUDE_ARGS:?}"
cat > "${MOCK_CLAUDE_PROMPT:?}"
if [[ "${MOCK_CLAUDE_FAIL:-no}" == yes ]]; then
  printf '{"is_error":true,"duration_ms":1200,"num_turns":1,"total_cost_usd":0.01,"result":"API Error: overloaded"}\n'
  exit 1
fi
printf '{"result":"Reviewed-Commit: fixture\\nVerdict: approved\\n"}\n'
EOF
chmod +x "$FIX/bin/claude"
cat > "$FIX/bin/codex" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "${MOCK_CODEX_ARGS:?}"
out=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output-last-message) out="$2"; shift 2 ;;
    *) shift ;;
  esac
done
cat > "${MOCK_CODEX_PROMPT:?}"
if [[ "${MOCK_CODEX_FAIL:-no}" == yes ]]; then
  printf '{"type":"turn.failed","error":"fixture"}\n'
  exit 1
fi
printf 'Reviewed-Commit: fixture\nFinding-IDs: none\nVerdict: approved\n' > "$out"
printf '{"type":"turn.completed","usage":{"input_tokens":120,"output_tokens":30}}\n'
EOF
chmod +x "$FIX/bin/codex"
profile_run() {
  local args="$FIX/claude.args"
  local prompt="$FIX/claude.prompt"
  local review
  (
    cd "$FIX"
    PATH="$FIX/bin:$PATH" MOCK_CLAUDE_ARGS="$args" MOCK_CLAUDE_PROMPT="$prompt" \
      bash "$FIX/agentmarshal/scripts/review-readonly.sh" \
        --task CR-900 --sha master --base master --model fixture \
        --reasoning-effort low >/dev/null
  ) &&
    grep -Fx -- '--safe-mode' "$args" >/dev/null &&
    grep -Fx -- '--no-session-persistence' "$args" >/dev/null &&
    grep -Fx -- 'Read,Grep,Glob' "$args" >/dev/null &&
    grep -F 'config: review_language=ru' "$prompt" >/dev/null &&
    grep -F 'Reviewer-Email: qa-agent@agent.example.invalid' "$prompt" >/dev/null &&
    review="$(find "$FIX/.agents/runs" -maxdepth 1 -name 'CR-900-qa-review-*.md' -print -quit)" &&
    grep -Fx 'Task: CR-900' "$review" >/dev/null &&
    grep -Fx 'Reviewer-Email: qa-agent@agent.example.invalid' "$review" >/dev/null &&
    jq -e -s 'any(.[]; .reasoning_effort == "low")' \
      "$FIX"/.agents/runs/stats/RUN-*.json >/dev/null
}
assert ok "qa-readonly launcher: tools, config language и raw stats" profile_run
profile_failure_run() {
  local args="$FIX/claude-fail.args"
  local prompt="$FIX/claude-fail.prompt"
  if (
    cd "$FIX"
    PATH="$FIX/bin:$PATH" MOCK_CLAUDE_ARGS="$args" MOCK_CLAUDE_PROMPT="$prompt" \
      MOCK_CLAUDE_FAIL=yes bash "$FIX/agentmarshal/scripts/review-readonly.sh" \
        --task CR-900 --sha master --base master --model fixture >/dev/null
  ); then
    return 1
  fi
  jq -e -s 'any(.[]; .outcome == "failed")' "$FIX"/.agents/runs/stats/RUN-*.json >/dev/null
}
assert ok "qa-readonly launcher: vendor failure записывается в stats" profile_failure_run
cat > "$FIX/.agents/tasks/open/CR-909-trial-review.md" <<'EOF'
# CR-909: trial review fixture
Owner: qa
Type: process
Priority: P3
Status: in_review
Trial-Batch: TRIAL-20260623-99
EOF
codex_profile_run() {
  local args="$FIX/codex.args"
  local prompt="$FIX/codex.prompt"
  (
    cd "$FIX"
    PATH="$FIX/bin:$PATH" MOCK_CODEX_ARGS="$args" MOCK_CODEX_PROMPT="$prompt" \
      bash "$FIX/agentmarshal/scripts/review-readonly.sh" \
        --task CR-909 --sha master --base master \
        --vendor codex --model fixture --reasoning-effort medium >/dev/null
  ) &&
    grep -Fx -- '--sandbox' "$args" >/dev/null &&
    grep -Fx -- 'read-only' "$args" >/dev/null &&
    grep -Fx -- '--ephemeral' "$args" >/dev/null &&
    grep -Fx -- '--ignore-user-config' "$args" >/dev/null &&
    grep -Fx -- 'approval_policy="never"' "$args" >/dev/null &&
    jq -e -s 'any(.[]; .vendor == "codex" and .outcome == "approved" and .trial == true and .reasoning_effort == "medium")' \
      "$FIX"/.agents/runs/stats/RUN-*.json >/dev/null
}
assert ok "qa-readonly launcher: Codex получает read-only ephemeral sandbox" codex_profile_run
rm -f "$FIX/.agents/tasks/open/CR-909-trial-review.md"

implementation_launcher_run() {
  local vendor="$1" impl bin
  impl="$FIX/impl-$vendor"
  bin="$FIX/impl-bin-$vendor"
  git clone -q "$FIX" "$impl"
  mkdir -p "$bin"
  cat > "$impl/.agents/tasks/open/CR-910-implementation.md" <<'EOF'
# CR-910: implementation launcher fixture
Owner: lead
Type: documentation
Priority: P3
Status: open
Scope:
- pilot.txt
EOF
  git -C "$impl" add .agents/tasks/open/CR-910-implementation.md
  git -C "$impl" -c user.name=Fixture -c user.email=fixture@example.invalid \
    commit -qm "add implementation task"
  if [[ "$vendor" == claude ]]; then
    cat > "$bin/claude" <<'EOF'
#!/usr/bin/env bash
cat >/dev/null
printf 'implemented\n' > pilot.txt
printf '{"result":"done","num_turns":1,"duration_ms":1000,"usage":{"input_tokens":10,"output_tokens":5},"total_cost_usd":0.01}\n'
EOF
    chmod +x "$bin/claude"
  else
    cat > "$bin/codex" <<'EOF'
#!/usr/bin/env bash
out=""
while [[ $# -gt 0 ]]; do
  case "$1" in -o|--output-last-message) out="$2"; shift 2 ;; *) shift ;; esac
done
cat >/dev/null
printf 'implemented\n' > pilot.txt
printf 'done\n' > "$out"
printf '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":5}}\n'
EOF
    chmod +x "$bin/codex"
  fi
  (
    cd "$impl"
    PATH="$bin:$PATH" bash agentmarshal/scripts/run-agent-task.sh \
      --task CR-910 --vendor "$vendor" --model fixture \
      --reasoning-effort high >/dev/null
  ) &&
    jq -e -s --arg vendor "$vendor" '
      any(.[]; .vendor == $vendor and .activity == "implementation"
               and .outcome == "success" and .scope_violations == 0
               and .reasoning_effort == "high")
    ' "$impl"/.agents/runs/stats/RUN-*.json >/dev/null
}
assert ok "implementation launcher: Claude raw stats" implementation_launcher_run claude
assert ok "implementation launcher: Codex raw stats" implementation_launcher_run codex
# чистый журнал → ок
assert ok "validate: пустой журнал ок" valrun
# плохой заголовок task
printf 'Owner: lead\nStatus: open\nbody\n' | put "$FIX/.agents/tasks/open/bad.md"
assert fail "validate: task без '# CR-<id>:' заголовка" valrun
rm -f "$FIX/.agents/tasks/open/bad.md"
# неизвестный execution profile
printf '# CR-902: t\nOwner: qa\nType: feature\nPriority: P2\nStatus: open\nExecution-Profile: no-such-profile\n' | put "$FIX/.agents/tasks/open/CR-902.md"
assert fail "validate: task с неизвестным execution profile" valrun
rm -f "$FIX/.agents/tasks/open/CR-902.md"
printf '# CR-903: t\nOwner: backend\nType: feature\nPriority: P2\nStatus: open\nExecution-Profile: qa-readonly\n' | put "$FIX/.agents/tasks/open/CR-903.md"
assert fail "validate: execution profile должен совпадать с Owner" valrun
rm -f "$FIX/.agents/tasks/open/CR-903.md"
# плохой Owner/Status
printf '# CR-901: t\nOwner: wizard\nType: feature\nPriority: P2\nStatus: flying\n' | put "$FIX/.agents/tasks/open/CR-901.md"
assert fail "validate: недопустимый Owner/Status" valrun
printf '# CR-906: t\nOwner: lead\nType: process\nPriority: P2\nStatus: done\n' | put "$FIX/.agents/tasks/open/CR-906.md"
assert fail "validate: done task запрещена в tasks/open" valrun
rm -f "$FIX/.agents/tasks/open/CR-906.md"
# плохой Type/Priority
printf '# CR-904: t\nOwner: lead\nType: chaos\nPriority: NOW\nStatus: open\n' | put "$FIX/.agents/tasks/open/CR-904.md"
assert fail "validate: недопустимый Type/Priority" valrun
rm -f "$FIX/.agents/tasks/open/CR-904.md"
# неполная review provenance не должна аварийно ломать validator
printf '# CR-905: t\nOwner: lead\nType: technical_debt\nPriority: P2\nStatus: open\nSource-Findings: F1\n' | put "$FIX/.agents/tasks/open/CR-905.md"
assert fail "validate: неполные Source-* поля блокируются без crash" valrun
rm -f "$FIX/.agents/tasks/open/CR-905.md"
# дубликат task id
printf '# CR-901: dup\nOwner: lead\nType: feature\nPriority: P2\nStatus: open\n' | put "$FIX/.agents/tasks/open/CR-901-dup.md"
printf '# CR-901: t\nOwner: lead\nType: feature\nPriority: P2\nStatus: open\n' | put "$FIX/.agents/tasks/open/CR-901.md"
assert fail "validate: дубликат task id" valrun
rm -f "$FIX/.agents/tasks/open/CR-901.md" "$FIX/.agents/tasks/open/CR-901-dup.md"
# handoff без обязательных полей
printf 'id: H1\ntask: CR-900\ntype: handoff\n' | put "$FIX/.agents/handoffs/2026/bad.md"
assert fail "validate: handoff без обязательных полей" valrun
rm -f "$FIX/.agents/handoffs/2026/bad.md"
# review без Reviewed-Commit
printf 'Task: CR-900\nReviewer: codex\nVerdict: approved\n' | put "$FIX/.agents/reviews/2026/bad.md"
printf '# CR-900: t\nOwner: lead\nType: feature\nPriority: P2\nStatus: open\n' | put "$FIX/.agents/tasks/open/CR-900.md"
assert fail "validate: review без Reviewed-Commit" valrun
# review с плохим SHA
printf 'Task: CR-900\nReviewer: codex\nVerdict: approved\nReviewed-Commit: NOTASHA!!\n' | put "$FIX/.agents/reviews/2026/bad.md"
assert fail "validate: review с плохим SHA" valrun
rm -f "$FIX/.agents/reviews/2026/bad.md" "$FIX/.agents/tasks/open/CR-900.md"

echo "== agent statistics =="
cat > "$FIX/.agents/tasks/open/CR-920-stat.md" <<'EOF'
# CR-920: statistic fixture
Owner: qa
Type: process
Priority: P3
Status: in_review
Created: 2026-06-22
EOF
cat > "$FIX/.agents/tasks/open/CR-921-stat-peer.md" <<'EOF'
# CR-921: statistic peer fixture
Owner: lead
Type: process
Priority: P3
Status: open
Created: 2026-06-23
EOF
record_stat() {
  (
    cd "$FIX"
    AGENTMARSHAL_RECORDED_AT=2026-06-21T18:00:00Z \
      bash "$RS" --task CR-920 --role qa --vendor claude --model fixture \
        --profile qa-readonly --activity review --outcome approved \
        --commit aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
        --duration-seconds 42 --turns 3 --findings 2 \
        --input-tokens 100 --output-tokens 20 --cost-usd 0.25 \
        --source-artifact .agents/runs/fixture.md >/dev/null
  )
}
stats_summary() {
  (cd "$FIX" && bash "$ST" summary --json) \
    | jq -e '.[0] | .role == "qa" and .runs == 1 and .findings == 2 and .cost_usd == 0.25' >/dev/null
}
assert ok "stats: normalized run записывается" record_stat
assert ok "stats: повторная запись идемпотентна" record_stat
assert ok "stats: summary агрегирует модель/роль" stats_summary
record_executor_stat() {
  (
    cd "$FIX"
    AGENTMARSHAL_RECORDED_AT=2026-06-21T18:01:00Z \
      bash "$RS" --task CR-920 --role lead --vendor codex --model fixture \
        --profile lead-trial --activity implementation --outcome success \
        --trial true --commit bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb \
        --duration-seconds 30 --turns 2 --tests-passed 2 \
        --changed-files 1 --additions 3 --source-artifact .agents/runs/impl.md >/dev/null
  )
}
assert ok "stats: implementation run записывается" record_executor_stat

cat > "$FIX/.agents/trials/2026/TRIAL-20260623-1.json" <<'EOF'
{
  "schema": 1,
  "id": "TRIAL-20260623-1",
  "created_at": "2026-06-23T00:00:00Z",
  "base_commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "scoring_version": "trial-v1",
  "minimum_stable_sample": 3,
  "assignments": [
    {
      "task": "CR-920",
      "task_class": "review",
      "difficulty": 2,
      "executor_vendor": "codex",
      "executor_model": "fixture",
      "reviewer_vendor": "claude",
      "reviewer_model": "fixture",
      "scope": ["agentmarshal/"]
    },
    {
      "task": "CR-921",
      "task_class": "review",
      "difficulty": 2,
      "executor_vendor": "claude",
      "executor_model": "fixture",
      "reviewer_vendor": "codex",
      "reviewer_model": "fixture",
      "scope": ["docs/"]
    }
  ]
}
EOF
executor_run="$(jq -r 'select(.role == "lead") | .id' "$FIX"/.agents/stats/runs/2026/RUN-*.json)"
reviewer_run="$(jq -r 'select(.role == "qa") | .id' "$FIX"/.agents/stats/runs/2026/RUN-*.json)"
cat > "$FIX/assessment.json" <<EOF
{
  "batch_id": "TRIAL-20260623-1",
  "task": "CR-920",
  "task_class": "review",
  "difficulty": 2,
  "executor_run_id": "$executor_run",
  "reviewer_run_id": "$reviewer_run",
  "executor_vendor": "codex",
  "executor_model": "fixture",
  "reviewer_vendor": "claude",
  "reviewer_model": "fixture",
  "acceptance_passed": true,
  "pipeline_passed": true,
  "provenance_valid": true,
  "scope_violations": 0,
  "confirmed_findings": {"blocking": 0, "p2": 2, "p3": 0},
  "implementation_findings": {"blocking": 0, "p2": 2, "p3": 0},
  "false_positive_findings": 0,
  "known_defects": 2,
  "detected_known_defects": 2,
  "severity_calibration_errors": 0,
  "actionable_findings": 2,
  "total_findings": 2,
  "rework_cycles": 0,
  "human_interventions": 0,
  "duration_seconds": 72,
  "cost_usd": 0.25,
  "diff_discipline_points": 15,
  "efficiency_points": 8,
  "scoring_version": "trial-v1",
  "adjudication_status": "confirmed",
  "evidence": [".agents/runs/impl.md", ".agents/runs/review.md"]
}
EOF
record_evaluation() {
  (
    cd "$FIX"
    AGENTMARSHAL_RECORDED_AT=2026-06-21T18:02:00Z \
      bash "$RE" --input "$FIX/assessment.json" >/dev/null
  )
}
ranking_summary() {
  (cd "$FIX" && bash "$ST" ranking --json) \
    | jq -e '
      length == 2
      and any(.[]; .activity == "implementation" and .samples == 1
                   and .stable == false)
      and any(.[]; .activity == "review" and .score_status == "full"
                   and .stable == false)
    ' >/dev/null
}
assert ok "evaluation: score записывается отдельно от run facts" record_evaluation
assert ok "evaluation: повторная запись идемпотентна" record_evaluation
assert ok "ranking: implementation и review не смешиваются" ranking_summary
jq '.detected_known_defects = 3' "$FIX/assessment.json" > "$FIX/assessment-invalid.json"
assert fail "evaluation: detected defects не могут превышать known defects" \
  bash "$RE" --input "$FIX/assessment-invalid.json"
assert ok "validate: tracked statistics валидны" valrun
stat_file="$(find "$FIX/.agents/stats/runs/2026" -name 'RUN-*.json' -print -quit)"
jq '.unexpected = true' "$stat_file" > "$FIX/stat-invalid.json"
mv "$FIX/stat-invalid.json" "$stat_file"
assert fail "validate: лишнее поле статистики запрещено" valrun
rm -f "$FIX/.agents/tasks/open/CR-920-stat.md" "$FIX/.agents/tasks/open/CR-921-stat-peer.md" \
  "$FIX/.agents/stats/runs/2026"/RUN-*.json \
  "$FIX/.agents/stats/evaluations/2026"/EVAL-*.json \
  "$FIX/.agents/trials/2026/TRIAL-20260623-1.json"

echo ""
echo "── итог: $pass прошло, $fail упало ──"
[[ $fail -gt 0 ]] && exit 1 || exit 0
