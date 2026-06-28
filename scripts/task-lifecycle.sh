#!/usr/bin/env bash
# Enforce the post-merge task lifecycle:
# in_review -> merged exact reviewed commit -> canonical review -> done.
set -euo pipefail

COMMAND="${1:-}"
[[ -n "$COMMAND" ]] || {
  echo "usage: task-lifecycle.sh {complete|audit} [options]" >&2
  exit 2
}
shift

ROOT="${AGENTMARSHAL_PROJECT_ROOT:-${AGENTOPS_PROJECT_ROOT:-}}"
REVIEW_TASK=""
REVIEW_FILE=""
REVIEWED_COMMIT=""
TARGET_REF=""
MERGED_COMMIT=""
COMPLETED_AT=""
DRY_RUN="no"
COMPLETION_PREFIX="${AGENTMARSHAL_COMPLETION_PREFIX:-${AGENTOPS_COMPLETION_PREFIX:-completion}}"
TASKS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root) ROOT="${2:?}"; shift 2 ;;
    --task) TASKS+=("${2:?}"); shift 2 ;;
    --review-task) REVIEW_TASK="${2:?}"; shift 2 ;;
    --review-file) REVIEW_FILE="${2:?}"; shift 2 ;;
    --reviewed-commit) REVIEWED_COMMIT="${2:?}"; shift 2 ;;
    --target-ref) TARGET_REF="${2:?}"; shift 2 ;;
    --merged-commit) MERGED_COMMIT="${2:?}"; shift 2 ;;
    --completed-at) COMPLETED_AT="${2:?}"; shift 2 ;;
    --dry-run) DRY_RUN="yes"; shift ;;
    -h|--help)
      echo "usage: task-lifecycle.sh complete --task CR-N [--task CR-M ...] --review-task CR-N --review-file <path> --reviewed-commit <sha> --target-ref <branch> [--merged-commit <sha>] [--dry-run]"
      echo "       complete must run on ${COMPLETION_PREFIX}/<slug> created from the updated target ref"
      echo "       task-lifecycle.sh audit [--project-root <path>]"
      exit 0
      ;;
    *) echo "task-lifecycle: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

if [[ -z "$ROOT" ]]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" \
    || { echo "task-lifecycle: project root not found" >&2; exit 2; }
fi
ROOT="$(cd "$ROOT" && pwd -P)"
JOURNAL="$ROOT/.agents"

die() {
  echo "task-lifecycle: $*" >&2
  exit 1
}

field() {
  local key="$1" file="$2"
  awk -v k="$key" '
    {
      line=$0
      gsub(/\*\*/, "", line)
      sub(/^[[:space:]#>*-]+/, "", line)
      pos=index(line, ":")
      if (!pos) next
      name=substr(line, 1, pos-1)
      if (tolower(name) == tolower(k)) {
        value=substr(line, pos+1)
        sub(/^[[:space:]]*/, "", value)
        sub(/[[:space:]]*$/, "", value)
        print value
        exit
      }
    }
  ' "$file"
}

normalize_scalar() {
  printf '%s' "$1" | tr 'A-Z' 'a-z' | tr -d ' `*'
}

full_commit() {
  local value="$1" label="$2" full
  full="$(git -C "$ROOT" rev-parse --verify "${value}^{commit}" 2>/dev/null)" \
    || die "$label commit not found: $value"
  [[ "$value" == "$full" ]] || die "$label must be a full 40-character SHA"
  printf '%s\n' "$full"
}

ci_completion_head() {
  local merged="$1" target="$2"
  local requested="${AGENTMARSHAL_AUDIT_COMPLETION_HEAD:-${AGENTOPS_AUDIT_COMPLETION_HEAD:-}}"
  local attested_target="${AGENTMARSHAL_AUDIT_TARGET_BRANCH:-${AGENTOPS_AUDIT_TARGET_BRANCH:-}}"
  local branch="${CI_COMMIT_REF_NAME:-}" ci_sha="${CI_COMMIT_SHA:-}" head
  [[ "$requested" =~ ^[0-9a-f]{40}$ ]] || return 1
  [[ "$ci_sha" =~ ^[0-9a-f]{40}$ ]] || return 1
  [[ "$attested_target" =~ ^[A-Za-z0-9._/-]+$ ]] || return 1
  [[ "$target" == "$attested_target" ]] || return 1
  [[ "$branch" == "$COMPLETION_PREFIX/"* ]] || return 1
  head="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)" || return 1
  [[ "$requested" == "$ci_sha" && "$ci_sha" == "$head" ]] || return 1
  git -C "$ROOT" merge-base --is-ancestor "$merged" "$head" 2>/dev/null \
    || return 1
  printf '%s\n' "$head"
}

ci_branch_head() {
  local merged="$1" target="$2"
  local requested="${AGENTMARSHAL_AUDIT_COMPLETION_HEAD:-${AGENTOPS_AUDIT_COMPLETION_HEAD:-}}"
  local attested_target="${AGENTMARSHAL_AUDIT_TARGET_BRANCH:-${AGENTOPS_AUDIT_TARGET_BRANCH:-}}"
  local ci_sha="${CI_COMMIT_SHA:-}" head
  [[ "$requested" =~ ^[0-9a-f]{40}$ ]] || return 1
  [[ -z "$ci_sha" || "$ci_sha" =~ ^[0-9a-f]{40}$ ]] || return 1
  [[ "$attested_target" =~ ^[A-Za-z0-9._/-]+$ ]] || return 1
  [[ "$target" == "$attested_target" ]] || return 1
  head="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null)" || return 1
  [[ "$requested" == "$head" ]] || return 1
  [[ -z "$ci_sha" || "$ci_sha" == "$head" ]] || return 1
  git -C "$ROOT" merge-base --is-ancestor "$merged" "$head" 2>/dev/null \
    || return 1
  printf '%s\n' "$head"
}

find_task() {
  local wanted="$1" file found=""
  while IFS= read -r file; do
    [[ -f "$file" ]] || continue
    if grep -qm1 -E "^# ${wanted}: " "$file"; then
      [[ -z "$found" ]] || die "duplicate task $wanted: $found and $file"
      found="$file"
    fi
  done < <(find "$JOURNAL/tasks" -type f -name "${wanted}*.md" 2>/dev/null)
  [[ -n "$found" ]] || die "task not found: $wanted"
  printf '%s\n' "$found"
}

validate_review() {
  local file="$1" expected_task="$2" expected_commit="$3"
  local task verdict reviewed
  [[ -f "$file" ]] || die "review file not found: $file"
  task="$(field Task "$file" | grep -oE 'CR-[0-9]+' | head -1)"
  verdict="$(normalize_scalar "$(field Verdict "$file")")"
  reviewed="$(field Reviewed-Commit "$file" | tr -d ' ')"
  [[ "$task" == "$expected_task" ]] \
    || die "review Task='$task', expected '$expected_task'"
  [[ "$verdict" == "approved" ]] \
    || die "review Verdict='${verdict:-empty}', expected approved"
  [[ "$reviewed" == "$expected_commit" ]] \
    || die "reviewed commit '$reviewed' != '$expected_commit'"
}

canonical_review_path() {
  local year="$1" task="$2" commit="$3"
  printf '%s/.agents/reviews/%s/%s-completion-%s.md\n' \
    "$ROOT" "$year" "$task" "${commit:0:12}"
}

audit_done_tasks() {
  local file count=0 failed=0
  while IFS= read -r file; do
    [[ -f "$file" ]] || continue
    ((count+=1))
    local task status review_task reviewed target target_sha merged completed artifact digest actual
    task="$(grep -m1 -E '^# CR-[0-9]+: ' "$file" | grep -oE 'CR-[0-9]+' | head -1)"
    status="$(field Status "$file")"
    review_task="$(field Completion-Review "$file" | tr -d ' ')"
    reviewed="$(field Reviewed-Commit "$file" | tr -d ' ')"
    target="$(field Target-Branch "$file" | tr -d ' ')"
    merged="$(field Merged-Commit "$file" | tr -d ' ')"
    completed="$(field Completed-At "$file" | tr -d ' ')"
    artifact="$(field Completion-Review-Artifact "$file")"
    digest="$(field Completion-Review-SHA256 "$file" | tr -d ' ')"

    if [[ "$status" != "done" ||
          ! "$review_task" =~ ^CR-[0-9]+$ ||
          ! "$reviewed" =~ ^[0-9a-f]{40}$ ||
          -z "$target" ||
          ! "$merged" =~ ^[0-9a-f]{40}$ ||
          ! "$completed" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ||
          ! "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]; then
      echo "task-lifecycle: invalid completion metadata: ${task:-$(basename "$file")}" >&2
      failed=1
      continue
    fi
    case "$artifact" in
      .agents/reviews/*) ;;
      *) echo "task-lifecycle: invalid review artifact path for $task: $artifact" >&2; failed=1; continue ;;
    esac
    [[ "$artifact" != *".."* ]] \
      || { echo "task-lifecycle: unsafe review artifact path for $task" >&2; failed=1; continue; }
    artifact="$ROOT/$artifact"
    target_sha="$(git -C "$ROOT" rev-parse --verify "origin/${target}^{commit}" 2>/dev/null || true)"
    [[ -n "$target_sha" ]] \
      || target_sha="$(git -C "$ROOT" rev-parse --verify "${target}^{commit}" 2>/dev/null || true)"
    [[ -n "$target_sha" ]] \
      || target_sha="$(ci_completion_head "$merged" "$target" || true)"
    [[ -n "$target_sha" ]] \
      || target_sha="$(ci_branch_head "$merged" "$target" || true)"
    if ! git -C "$ROOT" cat-file -e "${reviewed}^{commit}" 2>/dev/null ||
       ! git -C "$ROOT" cat-file -e "${merged}^{commit}" 2>/dev/null ||
       ! git -C "$ROOT" merge-base --is-ancestor "$reviewed" "$merged" 2>/dev/null ||
       [[ -z "$target_sha" ]] ||
       ! git -C "$ROOT" merge-base --is-ancestor "$merged" "$target_sha" 2>/dev/null; then
      echo "task-lifecycle: merge evidence is invalid for $task" >&2
      failed=1
      continue
    fi
    if ! validate_review "$artifact" "$review_task" "$reviewed"; then
      failed=1
      continue
    fi
    actual="sha256:$(sha256sum "$artifact" | awk '{print $1}')"
    if [[ "$actual" != "$digest" ]]; then
      echo "task-lifecycle: review digest mismatch for $task" >&2
      failed=1
    fi
  done < <(find "$JOURNAL/tasks/done" -type f -name 'CR-*.md' 2>/dev/null)

  [[ $failed -eq 0 ]] || return 1
  echo "task-lifecycle: audit passed done_tasks=$count"
}

complete_tasks() {
  [[ ${#TASKS[@]} -gt 0 ]] || die "complete requires at least one --task CR-N"
  [[ "$REVIEW_TASK" =~ ^CR-[0-9]+$ ]] \
    || die "complete requires --review-task CR-N"
  [[ -n "$REVIEW_FILE" ]] || die "complete requires --review-file <path>"
  [[ -n "$REVIEWED_COMMIT" ]] || die "complete requires --reviewed-commit <full-sha>"
  [[ -n "$TARGET_REF" ]] || die "complete requires --target-ref <branch>"

  local reviewed target_sha merged current_branch normalized_target year
  local review_source review_dest review_rel review_digest task task_file status
  local completed_dir dest tmp
  reviewed="$(full_commit "$REVIEWED_COMMIT" "reviewed")"
  target_sha="$(git -C "$ROOT" rev-parse --verify "${TARGET_REF}^{commit}" 2>/dev/null)" \
    || die "target ref not found: $TARGET_REF"
  [[ -n "$MERGED_COMMIT" ]] || MERGED_COMMIT="$target_sha"
  merged="$(full_commit "$MERGED_COMMIT" "merged")"
  git -C "$ROOT" merge-base --is-ancestor "$reviewed" "$merged" 2>/dev/null \
    || die "reviewed commit $reviewed is not contained in merged commit $merged"
  git -C "$ROOT" merge-base --is-ancestor "$merged" "$target_sha" 2>/dev/null \
    || die "merged commit $merged is not contained in target ref $TARGET_REF"
  [[ "$(git -C "$ROOT" rev-parse HEAD)" == "$target_sha" ]] \
    || die "current HEAD must equal target ref '$TARGET_REF' before completion"
  [[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=all)" ]] \
    || die "working tree must be clean before task completion"

  current_branch="$(git -C "$ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null)" \
    || die "task completion requires a checked-out completion branch"
  normalized_target="${TARGET_REF#refs/heads/}"
  normalized_target="${normalized_target#refs/remotes/}"
  normalized_target="${normalized_target#origin/}"
  [[ "$current_branch" == "$COMPLETION_PREFIX/"* ]] \
    || die "current branch '$current_branch' is not ${COMPLETION_PREFIX}/<slug>"
  [[ "$current_branch" != "$normalized_target" ]] \
    || die "direct completion on protected target '$normalized_target' is forbidden"

  if [[ "$REVIEW_FILE" = /* ]]; then
    review_source="$REVIEW_FILE"
  else
    review_source="$ROOT/$REVIEW_FILE"
  fi
  validate_review "$review_source" "$REVIEW_TASK" "$reviewed"

  [[ -n "$COMPLETED_AT" ]] || COMPLETED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  [[ "$COMPLETED_AT" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] \
    || die "--completed-at must be UTC YYYY-MM-DDTHH:MM:SSZ"
  year="${COMPLETED_AT:0:4}"
  review_dest="$(canonical_review_path "$year" "$REVIEW_TASK" "$reviewed")"
  review_rel="${review_dest#$ROOT/}"
  review_digest="sha256:$(sha256sum "$review_source" | awk '{print $1}')"

  if [[ -e "$review_dest" ]]; then
    [[ "sha256:$(sha256sum "$review_dest" | awk '{print $1}')" == "$review_digest" ]] \
      || die "canonical review already exists with different content: $review_rel"
  fi

  local task_files=()
  for task in "${TASKS[@]}"; do
    [[ "$task" =~ ^CR-[0-9]+$ ]] || die "invalid task id: $task"
    task_file="$(find_task "$task")"
    case "$task_file" in
      "$JOURNAL/tasks/open/"*) ;;
      *) die "$task must be in tasks/open before completion" ;;
    esac
    status="$(field Status "$task_file")"
    [[ "$status" == "in_review" ]] \
      || die "$task status must be in_review before completion, got '$status'"
    for key in Completion-Review Reviewed-Commit Target-Branch Merged-Commit \
               Completed-At Completion-Review-Artifact Completion-Review-SHA256; do
      [[ -z "$(field "$key" "$task_file")" ]] \
        || die "$task already contains completion field '$key'"
    done
    task_files+=("$task_file")
  done

  echo "task-lifecycle: completion plan"
  echo "  tasks: ${TASKS[*]}"
  echo "  review: $REVIEW_TASK @ $reviewed"
  echo "  target: $normalized_target @ $merged"
  echo "  completion branch: $current_branch"
  echo "  artifact: $review_rel"
  [[ "$DRY_RUN" == "no" ]] || return 0

  mkdir -p "$(dirname "$review_dest")" "$JOURNAL/tasks/done/$year"
  [[ -e "$review_dest" ]] || cp "$review_source" "$review_dest"

  for task_file in "${task_files[@]}"; do
    dest="$JOURNAL/tasks/done/$year/$(basename "$task_file")"
    [[ ! -e "$dest" ]] || die "destination already exists: $dest"
    tmp="$(mktemp "$JOURNAL/tasks/open/.task-complete.XXXXXX")"
    awk \
      -v review_task="$REVIEW_TASK" \
      -v reviewed="$reviewed" \
      -v target="$normalized_target" \
      -v merged="$merged" \
      -v completed="$COMPLETED_AT" \
      -v artifact="$review_rel" \
      -v digest="$review_digest" '
        /^Status:/ {
          print "Status: done"
          print "Completion-Review: " review_task
          print "Reviewed-Commit: " reviewed
          print "Target-Branch: " target
          print "Merged-Commit: " merged
          print "Completed-At: " completed
          print "Completion-Review-Artifact: " artifact
          print "Completion-Review-SHA256: " digest
          next
        }
        { print }
      ' "$task_file" > "$tmp"
    mv "$tmp" "$dest"
    rm "$task_file"
  done
  echo "task-lifecycle: tasks completed; commit canonical review and task moves"
}

case "$COMMAND" in
  complete) complete_tasks ;;
  audit) audit_done_tasks ;;
  *) die "unknown command '$COMMAND'" ;;
esac
