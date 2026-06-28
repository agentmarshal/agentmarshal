#!/usr/bin/env bash
# Vendor-aware implementation launcher with content-free raw statistics.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib/runtime-config.sh"
aops_config_init "$ROOT"
cd "$ROOT"

bash "$HERE/worktree-lifecycle.sh" worktree-preflight \
  --project-root "$ROOT" --worktree "$ROOT"

TASK=""; VENDOR=""; MODEL=""; REASONING_EFFORT="unspecified"; PROFILE=""; EXTRA_PROMPT=""

usage() {
  cat <<'EOF'
usage: run-agent-task.sh --task CR-NNN --vendor <claude|codex> --model <model>
                         [--reasoning-effort <low|medium|high|max>]
                         [--profile <id>] [--prompt <file>]

The launcher edits the current worktree but never commits or pushes.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task) TASK="${2:?}"; shift 2 ;;
    --vendor) VENDOR="${2:?}"; shift 2 ;;
    --model) MODEL="${2:?}"; shift 2 ;;
    --reasoning-effort) REASONING_EFFORT="${2:?}"; shift 2 ;;
    --profile) PROFILE="${2:?}"; shift 2 ;;
    --prompt) EXTRA_PROMPT="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "run-agent-task: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

[[ "$TASK" =~ ^CR-[0-9]+$ ]] \
  || { echo "run-agent-task: --task CR-NNN is required" >&2; exit 2; }
[[ "$VENDOR" == claude || "$VENDOR" == codex ]] \
  || { echo "run-agent-task: vendor must be claude or codex" >&2; exit 2; }
[[ -n "$MODEL" ]] || { echo "run-agent-task: --model is required" >&2; exit 2; }
[[ "$REASONING_EFFORT" =~ ^(unspecified|low|medium|high|max)$ ]] \
  || { echo "run-agent-task: invalid --reasoning-effort '$REASONING_EFFORT'" >&2; exit 2; }
[[ -z "$EXTRA_PROMPT" || -f "$EXTRA_PROMPT" ]] \
  || { echo "run-agent-task: prompt file not found: $EXTRA_PROMPT" >&2; exit 2; }

TASK_FILE="$(find "$ROOT/.agents/tasks" -name "${TASK}*.md" -print -quit)"
[[ -n "$TASK_FILE" ]] || { echo "run-agent-task: task '$TASK' not found" >&2; exit 2; }
ROLE="$(awk -F': *' 'tolower($1)=="owner"{print $2; exit}' "$TASK_FILE")"
[[ -f "$ROOT/agentmarshal/agents/$ROLE.yaml" ]] \
  || { echo "run-agent-task: unknown task owner '$ROLE'" >&2; exit 2; }
aops_config_has_list_item active_roles "$ROLE" \
  || { echo "run-agent-task: role '$ROLE' is not active" >&2; exit 2; }
[[ -n "$PROFILE" ]] || PROFILE="${ROLE}-trial"
[[ "$PROFILE" =~ ^[a-z0-9][a-z0-9-]*$ ]] \
  || { echo "run-agent-task: invalid profile '$PROFILE'" >&2; exit 2; }

if [[ -n "$(git status --porcelain)" ]]; then
  echo "run-agent-task: worktree must be clean before launch" >&2
  exit 1
fi

BASE_SHA="$(git rev-parse HEAD)"
BRANCH="$(git branch --show-current)"
RAW_STORE="$(aops_config_path stats_raw_store)"
mkdir -p "$RAW_STORE" "$ROOT/.agents/runs"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
SHORT="${BASE_SHA:0:7}"
OUT_BASE="$ROOT/.agents/runs/${TASK}-implementation-${VENDOR}-${SHORT}-${STAMP}"
PROMPT_FILE="$(mktemp)"
trap 'rm -f "$PROMPT_FILE"' EXIT

{
  cat <<EOF
Выполни задачу из приложенного task contract в текущем worktree.

Жёсткие правила:
- изменяй только пути из секции Scope;
- не изменяй .agents, сам task contract и AgentMarshal policy;
- не выполняй commit, push, merge, checkout, reset или rebase;
- не читай .env, секреты, SSH/config credential files;
- сохрани существующее поведение вне явно сформулированных acceptance criteria;
- перед завершением проверь diff и перечисли выполненные проверки;
- если задача не может быть выполнена в scope, остановись и объясни blocker.

Task: $TASK
Role: $ROLE
Vendor: $VENDOR
Model: $MODEL
Reasoning-Effort: $REASONING_EFFORT
Base-Commit: $BASE_SHA
Branch: $BRANCH

--- task contract ---
EOF
  cat "$TASK_FILE"
  if [[ -n "$EXTRA_PROMPT" ]]; then
    printf '\n--- additional instructions ---\n'
    cat "$EXTRA_PROMPT"
  fi
} > "$PROMPT_FILE"

START="$(date +%s)"
VENDOR_STATUS=0
RAW_FILE=""; RESULT_FILE="${OUT_BASE}.md"
case "$VENDOR" in
  claude)
    command -v claude >/dev/null \
      || { echo "run-agent-task: claude CLI not found" >&2; exit 1; }
    RAW_FILE="${OUT_BASE}.json"
    set +e
    claude --safe-mode --print --model "$MODEL" \
      --permission-mode acceptEdits --output-format json \
      --no-session-persistence --tools Read,Glob,Grep,Edit,Write \
      < "$PROMPT_FILE" > "$RAW_FILE"
    VENDOR_STATUS=$?
    set -e
    if [[ $VENDOR_STATUS -eq 0 ]] && jq -e '(.is_error // false) == false' "$RAW_FILE" >/dev/null 2>&1; then
      jq -er '.result' "$RAW_FILE" > "$RESULT_FILE" || VENDOR_STATUS=1
    else
      VENDOR_STATUS=1
    fi
    ;;
  codex)
    command -v codex >/dev/null \
      || { echo "run-agent-task: codex CLI not found" >&2; exit 1; }
    RAW_FILE="${OUT_BASE}.jsonl"
    set +e
    codex exec -C "$ROOT" --model "$MODEL" --sandbox workspace-write \
      --ephemeral --ignore-user-config -c 'approval_policy="never"' \
      --json --output-last-message "$RESULT_FILE" - \
      < "$PROMPT_FILE" > "$RAW_FILE"
    VENDOR_STATUS=$?
    set -e
    [[ $VENDOR_STATUS -eq 0 && -s "$RESULT_FILE" ]] || VENDOR_STATUS=1
    ;;
esac
END="$(date +%s)"
DURATION=$((END - START))

mapfile -t CHANGED_PATHS < <(
  git status --porcelain | sed -E 's/^.. //' | sed -E 's/^.* -> //'
)
mapfile -t ALLOWED_PATHS < <(
  awk '
    /^Scope:[[:space:]]*$/ {in_scope=1; next}
    in_scope && /^-[[:space:]]+/ {
      sub(/^-[[:space:]]+/, "")
      print
      next
    }
    in_scope {exit}
  ' "$TASK_FILE"
)
SCOPE_VIOLATIONS=0
for changed in "${CHANGED_PATHS[@]}"; do
  allowed="no"
  for scope in "${ALLOWED_PATHS[@]}"; do
    if [[ "$scope" == */ && "$changed" == "$scope"* ]] || [[ "$changed" == "$scope" ]]; then
      allowed="yes"
      break
    fi
  done
  if [[ "$allowed" != yes ]]; then
    echo "run-agent-task: scope violation: $changed" >&2
    ((SCOPE_VIOLATIONS += 1))
  fi
done

read -r _TRACKED_FILES ADDITIONS DELETIONS < <(
  git diff --numstat "$BASE_SHA" \
    | awk '{files++; if ($1 ~ /^[0-9]+$/) add+=$1; if ($2 ~ /^[0-9]+$/) del+=$2}
           END {print files+0, add+0, del+0}'
)
while IFS= read -r untracked; do
  [[ -f "$untracked" ]] || continue
  lines="$(wc -l < "$untracked" | tr -d ' ')"
  ADDITIONS=$((ADDITIONS + lines))
done < <(git ls-files --others --exclude-standard)
CHANGED_FILES="${#CHANGED_PATHS[@]}"
OUTCOME="success"
[[ $VENDOR_STATUS -eq 0 && $SCOPE_VIOLATIONS -eq 0 ]] || OUTCOME="failed"

TURNS=0; INPUT_TOKENS=0; OUTPUT_TOKENS=0; COST=0
if [[ "$VENDOR" == claude && -s "$RAW_FILE" ]]; then
  TURNS="$(jq -r '.num_turns // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
  INPUT_TOKENS="$(jq -r '(.usage.input_tokens // 0) + (.usage.cache_creation_input_tokens // 0) + (.usage.cache_read_input_tokens // 0)' "$RAW_FILE" 2>/dev/null || printf 0)"
  OUTPUT_TOKENS="$(jq -r '.usage.output_tokens // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
  COST="$(jq -r '.total_cost_usd // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
elif [[ "$VENDOR" == codex && -s "$RAW_FILE" ]]; then
  TURNS="$(jq -s '[.[] | select(.type == "turn.completed")] | length' "$RAW_FILE" 2>/dev/null || printf 0)"
  INPUT_TOKENS="$(jq -s '[.[] | select(.type == "turn.completed") | .usage.input_tokens // 0] | add // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
  OUTPUT_TOKENS="$(jq -s '[.[] | select(.type == "turn.completed") | .usage.output_tokens // 0] | add // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
fi

RECORDED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
stat_stamp="$(printf '%s' "$RECORDED_AT" | tr -d ':-')"
stat_hash="$(printf '%s\0' "$TASK" "$ROLE" "$VENDOR" "$MODEL" "$BASE_SHA" "$RECORDED_AT" \
  | sha256sum | cut -c1-8)"
stat_id="RUN-${stat_stamp}-${ROLE}-${stat_hash}"
STAT_FILE="$RAW_STORE/$stat_id.json"
jq -n \
  --arg id "$stat_id" --arg recorded "$RECORDED_AT" --arg task "$TASK" \
  --arg role "$ROLE" --arg vendor "$VENDOR" --arg model "$MODEL" \
  --arg reasoning_effort "$REASONING_EFFORT" \
  --arg profile "$PROFILE" --arg outcome "$OUTCOME" \
  --arg source "${RESULT_FILE#$ROOT/}" \
  --argjson duration "$DURATION" --argjson turns "$TURNS" \
  --argjson scope "$SCOPE_VIOLATIONS" --argjson changed "$CHANGED_FILES" \
  --argjson additions "$ADDITIONS" --argjson deletions "$DELETIONS" \
  --argjson input_tokens "$INPUT_TOKENS" --argjson output_tokens "$OUTPUT_TOKENS" \
  --argjson cost "$COST" '{
    schema: 1, id: $id, recorded_at: $recorded, task: $task, role: $role,
    vendor: $vendor, model: $model, reasoning_effort: $reasoning_effort,
    profile: $profile,
    activity: "implementation", outcome: $outcome, trial: true, commit: "none",
    duration_seconds: $duration, turns: $turns, human_interventions: 0,
    retries: 0, scope_violations: $scope, tests_passed: 0, tests_failed: 0,
    findings_count: 0, changed_files: $changed, additions: $additions,
    deletions: $deletions, input_tokens: $input_tokens,
    output_tokens: $output_tokens, cost_usd: $cost, source_artifact: $source
  }' | jq -S . > "$STAT_FILE"

sha256sum "$RAW_FILE" "$RESULT_FILE" > "${OUT_BASE}.sha256" 2>/dev/null || true
echo "run-agent-task: result: ${RESULT_FILE#$ROOT/}" >&2
echo "run-agent-task: raw stat: ${STAT_FILE#$ROOT/}" >&2
[[ "$OUTCOME" == success ]] || exit 1
