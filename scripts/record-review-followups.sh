#!/usr/bin/env bash
# Trusted recorder: materialize non-blocking findings from an approved review.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
JOURNAL="$ROOT/.agents"
TASKS="$JOURNAL/tasks"
EVENTS="$JOURNAL/events"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib/runtime-config.sh"
aops_config_init "$ROOT"

REVIEW=""
MANIFEST=""
SOURCE_TASK=""
DRY_RUN="no"
TODAY="${AGENTMARSHAL_TODAY:-${AGENTOPS_TODAY:-$(date +%Y-%m-%d)}}"
NOW="${AGENTMARSHAL_NOW:-${AGENTOPS_NOW:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}}"
STAMP="${AGENTMARSHAL_STAMP:-${AGENTOPS_STAMP:-$(date -u +%Y%m%dT%H%M%SZ)}}"

usage() {
  cat <<'EOF'
usage: agentmarshal/scripts/record-review-followups.sh --review <file> [options]

options:
  --manifest <json>      external manifest for legacy reviews; otherwise read
                         ```json follow-up-manifest from the review
  --source-task CR-NNN   override/inject source task for legacy reviews
  --dry-run              validate and print planned files without writing
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --review) REVIEW="${2:?}"; shift 2 ;;
    --manifest) MANIFEST="${2:?}"; shift 2 ;;
    --source-task) SOURCE_TASK="${2:?}"; shift 2 ;;
    --dry-run) DRY_RUN="yes"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "record-review-followups: неизвестный аргумент '$1'" >&2; usage >&2; exit 2 ;;
  esac
done

die() { echo "record-review-followups: $*" >&2; exit 1; }
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"; }
require_cmd jq
require_cmd sha256sum

[[ -n "$REVIEW" && -f "$REVIEW" ]] || die "нужен существующий --review <file>."
REVIEW="$(realpath "$REVIEW")"
case "$REVIEW" in "$ROOT"/*) REVIEW_REL="${REVIEW#$ROOT/}";; *) REVIEW_REL="$REVIEW";; esac

# Read plain or Markdown-bold metadata, e.g. `Verdict: approved` and
# `## Verdict: **approved**`.
review_field() {
  local key="$1"
  awk -v wanted="$key" '
    function trim(s) {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", s)
      return s
    }
    {
      line=$0
      gsub(/\*\*/, "", line)
      sub(/^[[:space:]#>*-]+/, "", line)
      pos=index(line, ":")
      if (!pos) next
      name=trim(substr(line, 1, pos-1))
      value=trim(substr(line, pos+1))
      if (tolower(name) == tolower(wanted)) {
        gsub(/^`|`$/, "", value)
        print value
        exit
      }
    }
  ' "$REVIEW"
}

VERDICT="$(review_field Verdict | tr 'A-Z' 'a-z')"
[[ "$VERDICT" == approved ]] \
  || die "review должен иметь Verdict: approved (получено '${VERDICT:-empty}')."

REVIEWED_COMMIT="$(review_field Reviewed-Commit)"
[[ "$REVIEWED_COMMIT" =~ ^[0-9a-f]{40}$ ]] \
  || die "review должен содержать полный Reviewed-Commit."

if [[ -z "$SOURCE_TASK" ]]; then
  SOURCE_TASK="$(review_field Task | grep -oE 'CR-[0-9]+' | head -1 || true)"
fi
[[ "$SOURCE_TASK" =~ ^CR-[0-9]+$ ]] \
  || die "review должен содержать Task: CR-NNN или нужен --source-task."
find "$TASKS" -name "${SOURCE_TASK}*.md" -print -quit 2>/dev/null | grep -q . \
  || die "source task $SOURCE_TASK не найдена в .agents/tasks/."

WORK="$(mktemp -d)"
LOCK="$JOURNAL/tmp/record-review-followups.lock"
locked="no"
cleanup() {
  rm -rf "$WORK"
  [[ "$locked" == yes ]] && rmdir "$LOCK" 2>/dev/null || true
}
trap cleanup EXIT

MANIFEST_JSON="$WORK/manifest.json"
EMBEDDED_MANIFEST="no"
if [[ -n "$MANIFEST" ]]; then
  [[ -f "$MANIFEST" ]] || die "manifest '$MANIFEST' не найден."
  cp "$MANIFEST" "$MANIFEST_JSON"
else
  EMBEDDED_MANIFEST="yes"
  awk '
    /^```json[[:space:]]+follow-up-manifest[[:space:]]*$/ {inside=1; next}
    inside && /^```[[:space:]]*$/ {found=1; exit}
    inside {print}
    END {if (!found) exit 1}
  ' "$REVIEW" > "$MANIFEST_JSON" \
    || die 'в review нет блока ```json follow-up-manifest; передай --manifest для legacy review.'
fi

MANIFEST_CHECK='
  def nonempty: type == "string" and length > 0 and (contains("\n") | not);
  def finding: type == "string" and test("^[A-Za-z][A-Za-z0-9.-]*$");
  def due: type == "string" and test("^(none|[0-9]{4}-[0-9]{2}-[0-9]{2}|CR-[0-9]+|[a-z0-9][a-z0-9._-]*)$");
  def is_unique: length == (unique | length);
  (.schema == 1)
  and (.review_findings | type == "array" and all(.[]; finding) and is_unique)
  and (.tasks | type == "array")
  and (.non_task | type == "array")
  and all(.tasks[];
    (.title | nonempty)
    and (.type | IN("feature","bug","refactor","documentation","technical_debt","security","operations","process"))
    and (.priority | IN("P1","P2","P3"))
    and (.owner | IN("lead","frontend","backend","qa","release"))
    and (.source_findings | type == "array" and length > 0 and all(.[]; finding) and is_unique)
    and (.due_before | due)
    and (.risk | nonempty)
    and (.acceptance_criteria | type == "array" and length > 0 and all(.[]; nonempty))
    and (.scope | type == "array" and length > 0 and all(.[]; nonempty))
  )
  and all(.non_task[];
    (.source_findings | type == "array" and length > 0 and all(.[]; finding) and is_unique)
    and (.disposition | IN(
      "existing_task","debt_bundle","duplicate","post_cutoff",
      "accepted_risk","wont_fix"
    ))
    and (.rationale | nonempty)
    and ((.target // "") | type == "string" and (length == 0 or nonempty))
    and (
      if (.disposition | IN("existing_task","debt_bundle","duplicate"))
      then ((.target // "") | nonempty)
      else true
      end
    )
  )
  and (
    ([.tasks[].source_findings[], .non_task[].source_findings[]] | unique | sort)
    == (.review_findings | unique | sort)
  )
  and (
    [.tasks[].source_findings[], .non_task[].source_findings[]] | unique
    | length
  ) == (
    [.tasks[].source_findings[], .non_task[].source_findings[]] | length
  )
'
jq -e "$MANIFEST_CHECK" "$MANIFEST_JSON" >/dev/null \
  || die "follow-up manifest не соответствует schema v1 или не покрывает findings ровно один раз."
jq -S . "$MANIFEST_JSON" > "$WORK/manifest.normalized.json"

OPERATING_MODE="$(aops_config_get operating_mode normal)"
ACTIVE_MILESTONE="$(aops_config_get active_milestone none)"
if [[ "$OPERATING_MODE" == cutoff_freeze && "${AGENTMARSHAL_CUTOFF_TASK_OVERRIDE:-${AGENTOPS_CUTOFF_TASK_OVERRIDE:-0}}" != 1 ]]; then
  cutoff_rejection="$(jq -r --arg milestone "$ACTIVE_MILESTONE" '
    [
      .tasks[]
      | select(
          .priority == "P3"
          or (.priority == "P2"
              and (.due_before == "none" or .due_before != $milestone))
        )
      | "\(.priority): \(.title) (Due-Before=\(.due_before))"
    ]
    | join("; ")
  ' "$MANIFEST_JSON")"
  [[ -z "$cutoff_rejection" ]] \
    || die "cutoff_freeze запрещает новые active P3 и P2 вне milestone '$ACTIVE_MILESTONE': $cutoff_rejection. Используй existing_task/debt_bundle/post_cutoff либо trusted override."
fi

HEADER_FINDINGS="$(review_field Finding-IDs)"
if [[ -z "$HEADER_FINDINGS" && "$EMBEDDED_MANIFEST" == yes ]]; then
  die "review со встроенным manifest должен содержать Finding-IDs."
fi
if [[ -n "$HEADER_FINDINGS" ]]; then
  if [[ "${HEADER_FINDINGS,,}" == none ]]; then
    HEADER_NORMALIZED=""
  else
    [[ "$HEADER_FINDINGS" =~ ^[A-Za-z][A-Za-z0-9.-]*(,[[:space:]]*[A-Za-z][A-Za-z0-9.-]*)*$ ]] \
      || die "Finding-IDs имеет неверный формат."
    header_count="$(printf '%s\n' "$HEADER_FINDINGS" | tr ',' '\n' | wc -l)"
    HEADER_NORMALIZED="$(printf '%s\n' "$HEADER_FINDINGS" | tr -d ' ' | tr ',' '\n' | sort -u | paste -sd, -)"
    unique_count="$(printf '%s\n' "$HEADER_NORMALIZED" | tr ',' '\n' | sed '/^$/d' | wc -l)"
    [[ "$header_count" == "$unique_count" ]] || die "Finding-IDs содержит дубликаты."
  fi
  MANIFEST_FINDINGS="$(jq -r '.review_findings | sort | join(",")' "$MANIFEST_JSON")"
  [[ "$HEADER_NORMALIZED" == "$MANIFEST_FINDINGS" ]] \
    || die "Finding-IDs не совпадает с review_findings manifest."
fi

REVIEW_SHA256="$(sha256sum "$REVIEW" | awk '{print $1}')"
MANIFEST_SHA256="$(sha256sum "$WORK/manifest.normalized.json" | awk '{print $1}')"
REVIEW_KEY="$(printf '%s\0%s\0%s' "$SOURCE_TASK" "$REVIEWED_COMMIT" "$MANIFEST_SHA256" | sha256sum | awk '{print $1}')"
SOURCE_REVIEW="${SOURCE_TASK}@${REVIEWED_COMMIT}"

if [[ "$DRY_RUN" != yes ]]; then
  mkdir -p "$JOURNAL/tmp" "$TASKS/open" "$EVENTS/${TODAY%%-*}/$SOURCE_TASK"
  lock_error="$(mkdir "$LOCK" 2>&1)" \
    || die "не удалось получить lock '$LOCK': ${lock_error:-unknown error}"
  locked="yes"
fi

next_task_number() {
  local max
  max="$(find "$TASKS" -type f -name 'CR-*.md' -exec basename {} \; 2>/dev/null \
    | sed -nE 's/^CR-([0-9]+).*/\1/p' | sort -n | tail -1)"
  max="${max:-0}"
  printf '%s\n' "$(( 10#$max + 1 ))"
}

next_event_number() {
  local max
  max="$(grep -rhoE "^id:[[:space:]]*${SOURCE_TASK}-EV-[0-9]+" "$EVENTS" 2>/dev/null \
    | sed -nE 's/.*-EV-([0-9]+)$/\1/p' | sort -n | tail -1)"
  printf '%03d\n' "$(( 10#${max:-0} + 1 ))"
}

task_key() {
  local findings="$1"
  printf '%s\0%s\0%s' "$SOURCE_TASK" "$REVIEWED_COMMIT" "$findings" \
    | sha256sum | awk '{print $1}'
}

created_tasks=()
existing_tasks=()
next_id="$(next_task_number)"
task_count="$(jq '.tasks | length' "$MANIFEST_JSON")"
for ((i=0; i<task_count; i++)); do
  title="$(jq -r ".tasks[$i].title" "$MANIFEST_JSON")"
  type="$(jq -r ".tasks[$i].type" "$MANIFEST_JSON")"
  priority="$(jq -r ".tasks[$i].priority" "$MANIFEST_JSON")"
  owner="$(jq -r ".tasks[$i].owner" "$MANIFEST_JSON")"
  due="$(jq -r ".tasks[$i].due_before" "$MANIFEST_JSON")"
  risk="$(jq -r ".tasks[$i].risk" "$MANIFEST_JSON")"
  findings="$(jq -r ".tasks[$i].source_findings | sort | join(\", \")" "$MANIFEST_JSON")"
  key="$(task_key "$findings")"
  existing="$(grep -rl "^Triage-Key: sha256:$key$" "$TASKS" 2>/dev/null | head -1 || true)"
  if [[ -n "$existing" ]]; then
    existing_tasks+=("$(basename "$existing" .md)")
    continue
  fi

  id="$(printf 'CR-%03d' "$next_id")"
  slug="$(printf '%s' "$findings" | tr 'A-Z, ' 'a-z--' | tr -cs 'a-z0-9-' '-' | sed 's/^-//;s/-$//')"
  target="$TASKS/open/${id}-review-follow-up-${slug}.md"
  [[ ! -e "$target" ]] || die "target task уже существует: $target"
  draft="$WORK/$(basename "$target")"
  {
    printf '# %s: %s\n\n' "$id" "$title"
    printf 'Owner: %s\n' "$owner"
    printf 'Type: %s\n' "$type"
    printf 'Priority: %s\n' "$priority"
    printf 'Status: open\n'
    printf 'Created: %s\n' "$TODAY"
    printf 'Source-Task: %s\n' "$SOURCE_TASK"
    printf 'Source-Commit: %s\n' "$REVIEWED_COMMIT"
    printf 'Source-Review: %s\n' "$SOURCE_REVIEW"
    printf 'Source-Findings: %s\n' "$findings"
    printf 'Due-Before: %s\n' "$due"
    printf 'Triage-Key: sha256:%s\n' "$key"
    printf 'Scope:\n'
    jq -r ".tasks[$i].scope[] | \"- \" + ." "$MANIFEST_JSON"
    printf '\n## Risk\n\n%s\n\n' "$risk"
    printf '## Acceptance Criteria\n\n'
    jq -r ".tasks[$i].acceptance_criteria[] | \"- [ ] \" + ." "$MANIFEST_JSON"
    printf '\n## Provenance\n\n'
    printf -- '- Review artifact: `%s`\n' "$REVIEW_REL"
    printf -- '- Review SHA256: `%s`\n' "$REVIEW_SHA256"
    printf -- '- Manifest SHA256: `%s`\n' "$MANIFEST_SHA256"
    printf -- '- Generated by: `agentmarshal/scripts/record-review-followups.sh`\n'
  } > "$draft"
  if [[ "$DRY_RUN" == yes ]]; then
    echo "would create: ${target#$ROOT/}"
  else
    mv "$draft" "$target"
    echo "created: ${target#$ROOT/}"
  fi
  created_tasks+=("$id")
  ((next_id += 1))
done

event_existing="$(grep -rl "^Triage-Review-Key: sha256:$REVIEW_KEY$" "$EVENTS" 2>/dev/null | head -1 || true)"
if [[ -z "$event_existing" ]]; then
  event_id="${SOURCE_TASK}-EV-$(next_event_number)"
  event="$EVENTS/${TODAY%%-*}/$SOURCE_TASK/${STAMP}-lead-review-triage.md"
  event_draft="$WORK/$(basename "$event")"
  {
    printf 'id: %s\n' "$event_id"
    printf 'task: %s\n' "$SOURCE_TASK"
    printf 'type: review_triage\n'
    printf 'created_at: %s\n' "$NOW"
    printf 'status: open\n'
    printf 'Triage-Review-Key: sha256:%s\n\n' "$REVIEW_KEY"
    printf '# Review triage\n\n'
    printf 'Source-Review: %s\n' "$SOURCE_REVIEW"
    printf 'Source-Artifact: %s\n' "$REVIEW_REL"
    printf 'Source-Review-SHA256: %s\n' "$REVIEW_SHA256"
    printf 'Manifest-SHA256: %s\n\n' "$MANIFEST_SHA256"
    printf '## Generated tasks\n\n'
    if [[ ${#created_tasks[@]} -eq 0 && ${#existing_tasks[@]} -eq 0 ]]; then
      printf -- '- none\n'
    else
      for task in "${created_tasks[@]}"; do printf -- '- %s (created)\n' "$task"; done
      for task in "${existing_tasks[@]}"; do printf -- '- %s (existing)\n' "$task"; done
    fi
    printf '\n## Non-task dispositions\n\n'
    non_task_count="$(jq '.non_task | length' "$MANIFEST_JSON")"
    if (( non_task_count == 0 )); then
      printf -- '- none\n'
    else
      for ((i=0; i<non_task_count; i++)); do
        nt_findings="$(jq -r ".non_task[$i].source_findings | sort | join(\", \")" "$MANIFEST_JSON")"
        disposition="$(jq -r ".non_task[$i].disposition" "$MANIFEST_JSON")"
        rationale="$(jq -r ".non_task[$i].rationale" "$MANIFEST_JSON")"
        target_ref="$(jq -r ".non_task[$i].target // empty" "$MANIFEST_JSON")"
        if [[ -n "$target_ref" ]]; then
          printf -- '- %s: `%s` → `%s` — %s\n' \
            "$nt_findings" "$disposition" "$target_ref" "$rationale"
        else
          printf -- '- %s: `%s` — %s\n' "$nt_findings" "$disposition" "$rationale"
        fi
      done
    fi
  } > "$event_draft"
  if [[ "$DRY_RUN" == yes ]]; then
    echo "would create: ${event#$ROOT/}"
  else
    mv "$event_draft" "$event"
    echo "created: ${event#$ROOT/}"
  fi
else
  echo "existing triage event: ${event_existing#$ROOT/}"
fi

echo "record-review-followups: source=$SOURCE_REVIEW tasks=${#created_tasks[@]} existing=${#existing_tasks[@]}"
