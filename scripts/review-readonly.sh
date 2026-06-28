#!/usr/bin/env bash
# Vendor-aware launcher для execution profile qa-readonly.
# Политика инструментов читается из agentmarshal/profiles/qa-readonly.yaml.
# Сырые результаты пишет launcher в ignored .agents/runs/; сам reviewer не
# получает filesystem-write или shell.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
AOPS="$ROOT/agentmarshal"
PROFILES="$AOPS/profiles"
source "$AOPS/lib/runtime-config.sh"
[[ -f "$AOPS/agentmarshal.config.sh" ]] && source "$AOPS/agentmarshal.config.sh"
aops_config_init "$ROOT"
cd "$ROOT"

PROFILE="qa-readonly"
TASK=""
SHA=""
BASE="origin/master"
VENDOR=""
MODEL=""
REASONING_EFFORT="unspecified"
EXTRA_PROMPT=""

usage() {
  cat <<'EOF'
usage: agentmarshal/scripts/review-readonly.sh --task CR-NNN --sha <commit> [options]

options:
  --profile <id>        execution profile (default: qa-readonly)
  --base <ref>          base для diff (default: origin/master)
  --vendor <vendor>     override vendor из профиля
  --model <model>       override модели из профиля
  --reasoning-effort <low|medium|high|max>
                       override reasoning effort для статистики маршрута
  --prompt <file>       дополнительное задание reviewer
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="${2:?}"; shift 2 ;;
    --task) TASK="${2:?}"; shift 2 ;;
    --sha) SHA="${2:?}"; shift 2 ;;
    --base) BASE="${2:?}"; shift 2 ;;
    --vendor) VENDOR="${2:?}"; shift 2 ;;
    --model) MODEL="${2:?}"; shift 2 ;;
    --reasoning-effort) REASONING_EFFORT="${2:?}"; shift 2 ;;
    --prompt) EXTRA_PROMPT="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "review-readonly: неизвестный аргумент '$1'" >&2; usage >&2; exit 2 ;;
  esac
done

[[ "$PROFILE" =~ ^[a-z0-9][a-z0-9-]*$ ]] \
  || { echo "review-readonly: невалидный profile id '$PROFILE'" >&2; exit 2; }
SPEC="$PROFILES/$PROFILE.yaml"
[[ -f "$SPEC" ]] || { echo "review-readonly: профиль '$PROFILE' не найден" >&2; exit 2; }

scalar() {
  awk -v k="$1:" '$1==k{$1=""; sub(/^ /,""); sub(/[[:space:]]*#.*$/,""); print; exit}' "$SPEC"
}
list() {
  awk -v key="$1:" '
    $0 ~ "^"key"$" {f=1; next}
    /^[a-z_]+:/ {f=0}
    f && /^[[:space:]]*-[[:space:]]/ {
      sub(/^[[:space:]]*-[[:space:]]*/,"")
      sub(/[[:space:]]*#.*$/,"")
      print
    }
  ' "$SPEC"
}
nested() {
  awk -v p="$1:" -v c="  $2:" '
    $0 ~ "^"p"$" {f=1; next}
    /^[a-z_]+:/ {f=0}
    f && index($0,c)==1 {
      sub(c,"")
      sub(/^[[:space:]]*/,"")
      sub(/[[:space:]]*#.*$/,"")
      print
      exit
    }
  ' "$SPEC"
}

[[ "$(scalar active)" == "true" ]] \
  || { echo "review-readonly: профиль '$PROFILE' не активен" >&2; exit 2; }
[[ "$(scalar mode)" == "review" ]] \
  || { echo "review-readonly: профиль '$PROFILE' не review-mode" >&2; exit 2; }
[[ "$(scalar write_policy)" == "none" ]] \
  || { echo "review-readonly: профиль '$PROFILE' не read-only" >&2; exit 2; }
[[ "$(scalar network_policy)" == "none" ]] \
  || { echo "review-readonly: профиль '$PROFILE' разрешает network" >&2; exit 2; }
[[ "$(scalar session_persistence)" == "false" ]] \
  || { echo "review-readonly: профиль '$PROFILE' сохраняет vendor session" >&2; exit 2; }
[[ "$(scalar output_recorder)" == "launcher" ]] \
  || { echo "review-readonly: профиль '$PROFILE' требует recorder=launcher" >&2; exit 2; }
REVIEWER_ROLE="$(scalar role)"
REVIEWER_EMAIL="${AGENTMARSHAL_ROLE_EMAIL[$REVIEWER_ROLE]:-}"
[[ -n "$REVIEWER_EMAIL" ]] \
  || { echo "review-readonly: email роли '$REVIEWER_ROLE' не настроен" >&2; exit 2; }
aops_config_has_list_item active_roles "$REVIEWER_ROLE" \
  || { echo "review-readonly: роль '$REVIEWER_ROLE' не активна в runtime config" >&2; exit 2; }

[[ "$TASK" =~ ^CR-[0-9]+$ ]] \
  || { echo "review-readonly: нужен --task CR-NNN" >&2; exit 2; }
TASK_FILE="$(find "$ROOT/.agents/tasks" -name "${TASK}*.md" -print -quit)"
TRIAL_RUN=false
if [[ -n "$TASK_FILE" ]] && grep -qE '^Trial-Batch:[[:space:]]*TRIAL-' "$TASK_FILE"; then
  TRIAL_RUN=true
fi
FULL_SHA="$(git rev-parse --verify "${SHA}^{commit}" 2>/dev/null)" \
  || { echo "review-readonly: commit '$SHA' не найден" >&2; exit 2; }
BASE_SHA="$(git rev-parse --verify "${BASE}^{commit}" 2>/dev/null)" \
  || { echo "review-readonly: base '$BASE' не найден" >&2; exit 2; }
MERGE_BASE="$(git merge-base "$BASE_SHA" "$FULL_SHA")" \
  || { echo "review-readonly: нет merge-base($BASE, $FULL_SHA)" >&2; exit 2; }

[[ -z "$EXTRA_PROMPT" || -f "$EXTRA_PROMPT" ]] \
  || { echo "review-readonly: prompt-файл '$EXTRA_PROMPT' не найден" >&2; exit 2; }

PROFILE_PROMPT="$PROFILES/$(scalar prompt)"
[[ -f "$PROFILE_PROMPT" ]] \
  || { echo "review-readonly: prompt профиля не найден: $PROFILE_PROMPT" >&2; exit 2; }

[[ -n "$VENDOR" ]] || VENDOR="$(nested vendor preferred)"
[[ -n "$MODEL" ]] || MODEL="$(nested vendor model)"
[[ -n "$VENDOR" && -n "$MODEL" ]] \
  || { echo "review-readonly: профиль не задаёт vendor/model" >&2; exit 2; }
[[ "$REASONING_EFFORT" =~ ^(unspecified|low|medium|high|max)$ ]] \
  || { echo "review-readonly: invalid --reasoning-effort '$REASONING_EFFORT'" >&2; exit 2; }

REVIEW_LANGUAGE="$(aops_config_get review_language ru)"
case "$REVIEW_LANGUAGE" in
  ru) REVIEW_LANGUAGE_NAME="русском" ;;
  en) REVIEW_LANGUAGE_NAME="английском" ;;
  *) REVIEW_LANGUAGE_NAME="$REVIEW_LANGUAGE" ;;
esac

OUTPUT_DIRECTORY="$(scalar output_directory)"
case "$OUTPUT_DIRECTORY" in
  .agents/runs|.agents/runs/) ;;
  *) echo "review-readonly: output_directory обязан быть .agents/runs/" >&2; exit 2 ;;
esac
OUTPUT_DIRECTORY="${OUTPUT_DIRECTORY%/}"

CLAUDE_TOOLS=()
while IFS= read -r capability; do
  [[ -z "$capability" ]] && continue
  case "$capability" in
    read) CLAUDE_TOOLS+=("Read") ;;
    grep) CLAUDE_TOOLS+=("Grep") ;;
    glob) CLAUDE_TOOLS+=("Glob") ;;
    *) echo "review-readonly: capability '$capability' не разрешена read-only launcher" >&2; exit 2 ;;
  esac
done < <(list tools)
[[ ${#CLAUDE_TOOLS[@]} -gt 0 ]] \
  || { echo "review-readonly: профиль не задаёт tools" >&2; exit 2; }
CLAUDE_TOOL_LIST="$(IFS=,; printf '%s' "${CLAUDE_TOOLS[*]}")"

mkdir -p "$ROOT/$OUTPUT_DIRECTORY"
SHORT="${FULL_SHA:0:7}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_BASE="$ROOT/$OUTPUT_DIRECTORY/${TASK}-qa-review-${SHORT}-${STAMP}"
PROMPT_FILE="$(mktemp)"
DIFF_FILE="$(mktemp)"
SNAPSHOT="$(mktemp -d)"
MD_FILE="${OUT_BASE}.md"
HASH_FILE="${OUT_BASE}.sha256"
case "$VENDOR" in
  claude) RAW_FILE="${OUT_BASE}.json" ;;
  codex) RAW_FILE="${OUT_BASE}.jsonl" ;;
  *) RAW_FILE="${OUT_BASE}.raw" ;;
esac
trap 'rm -f "$PROMPT_FILE" "$DIFF_FILE"; rm -rf "$SNAPSHOT"' EXIT

git archive "$FULL_SHA" | tar -x -C "$SNAPSHOT"
git diff --no-ext-diff --unified=20 "$MERGE_BASE" "$FULL_SHA" > "$DIFF_FILE"

{
  cat "$PROFILE_PROMPT"
  cat <<EOF

Task: $TASK
Execution-Profile: $PROFILE
Reviewer-Role: $REVIEWER_ROLE
Reviewer-Vendor: $VENDOR
Reviewer-Model: $MODEL
Reviewer-Email: $REVIEWER_EMAIL
Reviewed-Commit: $FULL_SHA
Base: $BASE_SHA
Merge-Base: $MERGE_BASE

Проверь указанный commit. Верни findings по приоритету с file:line, risk и
suggested fix. Начни ответ с plain-text machine header без Markdown-выделения:
Task, Reviewer-Role, Reviewer-Vendor, Reviewer-Model, Reviewer-Email,
Reviewed-Commit, Verdict, Finding-IDs. Содержательный текст отчёта пиши на
$REVIEW_LANGUAGE_NAME языке
(config: review_language=$REVIEW_LANGUAGE). Для approved review укажи
Finding-IDs и добавь JSON follow-up-manifest по инструкции профиля.

Изменённые файлы:
EOF
  git diff --name-status "$MERGE_BASE" "$FULL_SHA"
  printf '\nКоммиты в review range:\n'
  git log --format='%H %an <%ae> %s' "$MERGE_BASE..$FULL_SHA"
  printf '\nDiff stat:\n'
  git diff --stat "$MERGE_BASE" "$FULL_SHA"
  printf '\nExact unified diff (%s..%s):\n' "$MERGE_BASE" "$FULL_SHA"
  cat "$DIFF_FILE"
  if [[ -n "$EXTRA_PROMPT" ]]; then
    printf '\nДополнительное задание:\n'
    cat "$EXTRA_PROMPT"
  fi
} > "$PROMPT_FILE"

echo "review-readonly: profile=$PROFILE vendor=$VENDOR model=$MODEL task=$TASK sha=$SHORT" >&2
echo "review-readonly: capabilities=$(IFS=,; printf '%s' "${CLAUDE_TOOLS[*]}"); write_policy=none" >&2

write_review_stat() {
  local outcome="$1" findings="$2" source="$3"
  [[ "$(aops_config_get stats_enabled true)" == true ]] || return 0

  local raw_stats recorded_at duration turns input_tokens output_tokens cost
  local changed additions deletions stat_hash stat_stamp stat_id stat_file
  raw_stats="$(aops_config_path stats_raw_store)"
  mkdir -p "$raw_stats"
  recorded_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  read -r changed additions deletions < <(
    git diff --numstat "$MERGE_BASE" "$FULL_SHA" \
      | awk '{files++; if ($1 ~ /^[0-9]+$/) add+=$1; if ($2 ~ /^[0-9]+$/) del+=$2}
             END {print files+0, add+0, del+0}'
  )
  if [[ "$VENDOR" == claude ]]; then
    duration="$(jq -r '((.duration_ms // 0) / 1000 | floor)' "$RAW_FILE" 2>/dev/null || printf 0)"
    turns="$(jq -r '.num_turns // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
    input_tokens="$(jq -r '(.usage.input_tokens // 0) + (.usage.cache_creation_input_tokens // 0) + (.usage.cache_read_input_tokens // 0)' "$RAW_FILE" 2>/dev/null || printf 0)"
    output_tokens="$(jq -r '.usage.output_tokens // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
    cost="$(jq -r '.total_cost_usd // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
  else
    duration="${REVIEW_DURATION:-0}"
    turns="$(jq -s '[.[] | select(.type == "turn.completed")] | length' "$RAW_FILE" 2>/dev/null || printf 0)"
    input_tokens="$(jq -s '[.[] | select(.type == "turn.completed") | .usage.input_tokens // 0] | add // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
    output_tokens="$(jq -s '[.[] | select(.type == "turn.completed") | .usage.output_tokens // 0] | add // 0' "$RAW_FILE" 2>/dev/null || printf 0)"
    cost=0
  fi
  stat_hash="$(printf '%s\0' "$TASK" "$VENDOR" "$MODEL" "$PROFILE" "$FULL_SHA" "$recorded_at" | sha256sum | cut -c1-8)"
  stat_stamp="$(printf '%s' "$recorded_at" | tr -d ':-')"
  stat_id="RUN-${stat_stamp}-qa-${stat_hash}"
  stat_file="$raw_stats/$stat_id.json"
  jq -n \
    --arg id "$stat_id" --arg recorded "$recorded_at" --arg task "$TASK" \
    --arg vendor "$VENDOR" --arg model "$MODEL" --arg profile "$PROFILE" \
    --arg reasoning_effort "$REASONING_EFFORT" \
    --arg outcome "$outcome" --arg commit "$FULL_SHA" \
    --arg source "${source#$ROOT/}" \
    --argjson duration "$duration" --argjson turns "$turns" \
    --argjson findings "$findings" --argjson changed "$changed" \
    --argjson additions "$additions" --argjson deletions "$deletions" \
    --argjson input_tokens "$input_tokens" --argjson output_tokens "$output_tokens" \
    --argjson cost "$cost" --argjson trial "$TRIAL_RUN" '{
      schema: 1, id: $id, recorded_at: $recorded, task: $task, role: "qa",
      vendor: $vendor, model: $model, reasoning_effort: $reasoning_effort,
      profile: $profile, activity: "review",
      outcome: $outcome, trial: $trial, commit: $commit,
      duration_seconds: $duration, turns: $turns, human_interventions: 0,
      retries: 0, scope_violations: 0, tests_passed: 0, tests_failed: 0,
      findings_count: $findings, changed_files: $changed,
      additions: $additions, deletions: $deletions,
      input_tokens: $input_tokens, output_tokens: $output_tokens,
      cost_usd: $cost, source_artifact: $source
    }' | jq -S . > "$stat_file"
  echo "review-readonly: raw stat: ${stat_file#$ROOT/}" >&2
}

REVIEW_START="$(date +%s)"
case "$VENDOR" in
  claude)
    command -v claude >/dev/null || { echo "review-readonly: claude CLI не найден" >&2; exit 1; }
    set +e
    (
      cd "$SNAPSHOT"
      claude \
        --safe-mode \
        --print \
        --model "$MODEL" \
        --permission-mode dontAsk \
        --output-format json \
        --no-session-persistence \
        --tools "$CLAUDE_TOOL_LIST" \
        < "$PROMPT_FILE" > "$RAW_FILE"
    )
    VENDOR_STATUS=$?
    set -e
    if [[ $VENDOR_STATUS -ne 0 ]] || ! jq -e '(.is_error // false) == false' "$RAW_FILE" >/dev/null 2>&1; then
      REVIEW_DURATION=$(($(date +%s) - REVIEW_START))
      sha256sum "$RAW_FILE" > "$HASH_FILE"
      write_review_stat failed 0 "$RAW_FILE"
      ERROR_TEXT="$(jq -r '.result // .error // "vendor invocation failed"' "$RAW_FILE" 2>/dev/null || printf 'vendor invocation failed')"
      echo "review-readonly: Claude failed: $ERROR_TEXT" >&2
      echo "review-readonly: raw JSON: ${RAW_FILE#$ROOT/}" >&2
      echo "review-readonly: hashes:   ${HASH_FILE#$ROOT/}" >&2
      exit 1
    fi
    jq -er '.result' "$RAW_FILE" > "$MD_FILE" \
      || { echo "review-readonly: Claude не вернул текстовый result" >&2; exit 1; }
    ;;
  codex)
    command -v codex >/dev/null || { echo "review-readonly: codex CLI не найден" >&2; exit 1; }
    set +e
    codex exec -C "$SNAPSHOT" --model "$MODEL" --sandbox read-only \
      --ephemeral --ignore-user-config --skip-git-repo-check \
      -c 'approval_policy="never"' \
      --json --output-last-message "$MD_FILE" - \
      < "$PROMPT_FILE" > "$RAW_FILE"
    VENDOR_STATUS=$?
    set -e
    REVIEW_DURATION=$(($(date +%s) - REVIEW_START))
    if [[ $VENDOR_STATUS -ne 0 || ! -s "$MD_FILE" ]]; then
      sha256sum "$RAW_FILE" > "$HASH_FILE"
      write_review_stat failed 0 "$RAW_FILE"
      echo "review-readonly: Codex failed (exit=$VENDOR_STATUS)" >&2
      echo "review-readonly: raw JSONL: ${RAW_FILE#$ROOT/}" >&2
      echo "review-readonly: hashes:     ${HASH_FILE#$ROOT/}" >&2
      exit 1
    fi
    ;;
  *)
    echo "review-readonly: vendor '$VENDOR' пока не поддержан этим launcher" >&2
    exit 2
    ;;
esac
REVIEW_DURATION="${REVIEW_DURATION:-$(($(date +%s) - REVIEW_START))}"

VERDICT="$(awk '
  {
    line=$0; gsub(/\*\*/, "", line); sub(/^[[:space:]#>*-]+/, "", line)
    if (tolower(line) ~ /^verdict:[[:space:]]*/) {
      sub(/^[^:]+:[[:space:]]*/, "", line); gsub(/`/, "", line); value=tolower(line)
    }
  }
  END {print value}
' "$MD_FILE")"
case "$VERDICT" in approved|changes_required|blocked|rejected) OUTCOME="$VERDICT";; *) OUTCOME="success";; esac
FINDING_IDS="$(awk '
  {
    line=$0; gsub(/\*\*/, "", line); sub(/^[[:space:]#>*-]+/, "", line)
    if (tolower(line) ~ /^finding-ids:[[:space:]]*/) {
      sub(/^[^:]+:[[:space:]]*/, "", line); gsub(/`/, "", line); value=line
    }
  }
  END {print value}
' "$MD_FILE")"
if [[ -z "$FINDING_IDS" || "${FINDING_IDS,,}" == none ]]; then FINDINGS=0
else FINDINGS="$(printf '%s' "$FINDING_IDS" | awk -F',' '{print NF}')"; fi

BODY_FILE="$(mktemp)"
mv "$MD_FILE" "$BODY_FILE"
{
  printf 'Task: %s\n' "$TASK"
  printf 'Reviewer-Role: %s\n' "$REVIEWER_ROLE"
  printf 'Reviewer-Vendor: %s\n' "$VENDOR"
  printf 'Reviewer-Model: %s\n' "$MODEL"
  printf 'Reviewer-Email: %s\n' "$REVIEWER_EMAIL"
  printf 'Reviewed-Commit: %s\n' "$FULL_SHA"
  printf 'Verdict: %s\n' "${VERDICT:-unknown}"
  printf 'Finding-IDs: %s\n\n' "${FINDING_IDS:-none}"
  cat "$BODY_FILE"
} > "$MD_FILE"
rm -f "$BODY_FILE"

sha256sum "$RAW_FILE" "$MD_FILE" > "$HASH_FILE"
write_review_stat "$OUTCOME" "$FINDINGS" "$MD_FILE"

echo "review-readonly: raw output: ${RAW_FILE#$ROOT/}" >&2
echo "review-readonly: review:   ${MD_FILE#$ROOT/}" >&2
echo "review-readonly: hashes:   ${HASH_FILE#$ROOT/}" >&2
printf '%s\n' "$MD_FILE"
