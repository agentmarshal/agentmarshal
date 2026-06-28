#!/usr/bin/env bash
# merge-policy.sh — gate перед merge (ревью F-004 / R-002 / R-003).
#
# Резолвит MR через GitFlic API → source branch + ТОЧНЫЙ head SHA, и проверяет
# именно этот SHA (а не локальный HEAD — иначе Lead мог бы провалидировать одну
# ветку, а смержить другой MR):
#   1. для role/integration ветки обязателен task ID (CR-<id>), задача не abandoned;
#   2. есть review-отчёт по задаче с Reviewed-Commit == head SHA (не stale) и
#      НЕ-changes_required вердиктом;
#   3. reviewer независим: его Role/Email НЕ среди авторов И Co-Authored-By
#      имплементационных коммитов (коммиты, трогающие что-то кроме .agents/reviews/);
#   4. pipeline для head SHA подтверждён. Пока merge-policy не вызывает
#      gitflic-ci.sh автоматически, используется явная аттестация
#      AGENTMARSHAL_PIPELINE_OK_SHA=<sha> / --pipeline-sha.
#
#   merge-policy.sh --mr <id> [--task CR-x] [--review-file <path>] [--pipeline-sha <sha>]
#   merge-policy.sh --branch <b> [--head <sha>] [--base <ref>] [--task CR-x] [--review-file <path>] [--pipeline-sha <sha>]
# Exit ≠0 при нарушении. Emergency override: AGENTMARSHAL_SKIP_MERGE_POLICY=1.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
JOURNAL="$ROOT/.agents"
AGENTS_DIR="$ROOT/agentmarshal/agents"
[[ -f "$HERE/../agentmarshal.config.sh" ]] && source "$HERE/../agentmarshal.config.sh"
_SECRETS="${PROJECT_SECRETS_FILE:-$HOME/.config/${AGENTMARSHAL_GITFLIC_PROJECT:-${AGENTOPS_GITFLIC_PROJECT:-agentmarshal-host}}/secrets.env}"
[[ -z "${GITFLIC_API_TOKEN:-}" && -f "$_SECRETS" ]] && source "$_SECRETS"

GENERIC_PREFIXES="feature feat fix refactor completion"
ROLE_PREFIXES="lead fe be infra qa"

if [[ "${AGENTMARSHAL_SKIP_MERGE_POLICY:-${AGENTOPS_SKIP_MERGE_POLICY:-0}}" == "1" ]]; then
  echo "⚠️  merge-policy пропущена (AGENTMARSHAL_SKIP_MERGE_POLICY=1, emergency override)." >&2; exit 0
fi

MR=""; BRANCH=""; HEAD_REF=""; BASE="origin/${AGENTMARSHAL_DEFAULT_BRANCH:-${AGENTOPS_DEFAULT_BRANCH:-master}}"; TASK=""
PIPE_SHA="${AGENTMARSHAL_PIPELINE_OK_SHA:-${AGENTOPS_PIPELINE_OK_SHA:-}}"
REVIEW_FILE="${AGENTMARSHAL_REVIEW_FILE:-${AGENTOPS_REVIEW_FILE:-}}"
while [[ $# -gt 0 ]]; do case "$1" in
  --mr) MR="${2:?}"; shift 2;; --branch) BRANCH="${2:?}"; shift 2;;
  --head) HEAD_REF="${2:?}"; shift 2;; --base) BASE="${2:?}"; shift 2;;
  --task) TASK="${2:?}"; shift 2;; --pipeline-sha) PIPE_SHA="${2:?}"; shift 2;;
  --review-file) REVIEW_FILE="${2:?}"; shift 2;;
  *) echo "merge-policy: неизвестный аргумент $1" >&2; exit 2;; esac; done

problems=0; err() { echo "  ❌ $*" >&2; ((problems++)); }; ok() { echo "  ✅ $*" >&2; }

review_field() {
  local file="$1" key="$2"
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
  ' "$file"
}

# ── резолв MR через API → branch + head SHA ─────────────────────────────────
if [[ -n "$MR" ]]; then
  [[ -n "${GITFLIC_API_TOKEN:-}" ]] || { echo "❌ merge-policy: --mr задан, но нет GITFLIC_API_TOKEN ($_SECRETS)." >&2; exit 1; }
  PP="${AGENTMARSHAL_GITFLIC_OWNER:-${AGENTOPS_GITFLIC_OWNER:-agentmarshal}}/${AGENTMARSHAL_GITFLIC_PROJECT:-${AGENTOPS_GITFLIC_PROJECT:-agentmarshal-host}}"
  detail="$(curl -sS -H "Authorization: token $GITFLIC_API_TOKEN" "${AGENTMARSHAL_API_BASE:-${AGENTOPS_API_BASE:-https://api.gitflic.ru}}/project/$PP/merge-request/$MR" 2>/dev/null)"
  BRANCH="$(printf '%s' "$detail" | python3 -c "import sys,json;print(json.load(sys.stdin).get('sourceBranch',{}).get('id',''))" 2>/dev/null)"
  HEAD_SHA="$(printf '%s' "$detail" | python3 -c "import sys,json;print(json.load(sys.stdin).get('sourceBranch',{}).get('hash',''))" 2>/dev/null)"
  TGT="$(printf '%s' "$detail" | python3 -c "import sys,json;print(json.load(sys.stdin).get('targetBranch',{}).get('id',''))" 2>/dev/null)"
  [[ -n "$BRANCH" && -n "$HEAD_SHA" ]] || { echo "❌ merge-policy: не разрешил MR #$MR через API (branch/hash пусты)." >&2; exit 1; }
  [[ -n "$TGT" ]] && BASE="origin/$TGT"
  echo "── merge-policy: MR #$MR → $BRANCH @ ${HEAD_SHA:0:8} (target $BASE) ──" >&2
else
  [[ -n "$BRANCH" ]] || { echo "❌ merge-policy: нужен --mr <id> или --branch <name>." >&2; exit 1; }
  [[ -z "$HEAD_REF" ]] && HEAD_REF="$BRANCH"
  HEAD_SHA="$(git -C "$ROOT" rev-parse --verify --quiet "${HEAD_REF}^{commit}" || git -C "$ROOT" rev-parse --verify --quiet "origin/${BRANCH}^{commit}")"
  [[ -n "$HEAD_SHA" ]] || { echo "❌ merge-policy: не разрешил head '$HEAD_REF'." >&2; exit 1; }
  echo "── merge-policy: $BRANCH @ ${HEAD_SHA:0:8} (base $BASE) ──" >&2
fi

PREFIX="${BRANCH%%/*}"
is_in() { local x="$1"; shift; local i; for i in "$@"; do [[ "$x" == "$i" ]] && return 0; done; return 1; }
is_generic() { is_in "$1" $GENERIC_PREFIXES; }
is_role()    { is_in "$1" $ROLE_PREFIXES; }
AGENT_BRANCH="no"; { is_role "$PREFIX" || is_generic "$PREFIX"; } && AGENT_BRANCH="yes"
COMPLETION_BRANCH="no"; [[ "$PREFIX" == completion ]] && COMPLETION_BRANCH="yes"

email_role() { local e="$1" r; declare -p AGENTMARSHAL_ROLE_EMAIL >/dev/null 2>&1 || return 0
  for r in "${!AGENTMARSHAL_ROLE_EMAIL[@]}"; do [[ "${AGENTMARSHAL_ROLE_EMAIL[$r]}" == "$e" ]] && { echo "$r"; return; }; done; }

BASE_SHA="$(git -C "$ROOT" rev-parse --verify --quiet "${BASE}^{commit}")" || { echo "❌ merge-policy: base '$BASE' не разрешается (fetch?)." >&2; exit 1; }
MB="$(git -C "$ROOT" merge-base "$BASE_SHA" "$HEAD_SHA" 2>/dev/null)" || { echo "❌ merge-policy: нет merge-base($BASE,$HEAD_SHA)." >&2; exit 1; }

# ── 1. task id ──────────────────────────────────────────────────────────────
if [[ -z "$TASK" ]]; then
  TASK="$(git -C "$ROOT" log --format='%s%n%b' "$MB..$HEAD_SHA" 2>/dev/null | grep -oE 'CR-[0-9]+' | head -1)"
fi
if [[ "$AGENT_BRANCH" == "yes" && -z "$TASK" ]]; then
  err "role/integration-ветка '$BRANCH' без task ID (CR-<id>) — нет task ID, нет merge."
fi
TASKFILE=""
if [[ -n "$TASK" ]]; then
  TASKFILE="$(find "$JOURNAL/tasks" -name "${TASK}*.md" 2>/dev/null | head -1)"
  [[ -n "$TASKFILE" ]] || err "$TASK: task-файл не найден в .agents/tasks/"
  case "$TASKFILE" in *"/abandoned/"*) err "$TASK: задача abandoned — merge запрещён";; esac
  if [[ -n "$TASKFILE" ]]; then
    TSTATUS="$(awk -F': *' 'tolower($1)=="status"{print tolower($2); exit}' "$TASKFILE" | tr -d ' ')"
    if [[ "$COMPLETION_BRANCH" == yes ]]; then
      [[ "$TSTATUS" == "done" ]] \
        || err "$TASK: completion MR требует Status: done, получено '$TSTATUS'"
    else
      [[ "$TSTATUS" == "in_review" ]] \
        || err "$TASK: Status='$TSTATUS', перед merge требуется Status: in_review"
    fi
  fi
  [[ -n "$TASKFILE" ]] && ok "task: $TASK (${TASKFILE#$ROOT/})"
fi

# completion/* is a protected-branch journal transaction, not implementation.
if [[ "$COMPLETION_BRANCH" == yes ]]; then
  CURRENT_BRANCH="$(git -C "$ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null || true)"
  CURRENT_HEAD="$(git -C "$ROOT" rev-parse HEAD 2>/dev/null || true)"
  [[ "$CURRENT_BRANCH" == "$BRANCH" && "$CURRENT_HEAD" == "$HEAD_SHA" ]] \
    || err "completion MR must be checked out at exact head for filesystem audit"
  while IFS= read -r path; do
    [[ -z "$path" ]] && continue
    case "$path" in
      .agents/tasks/*|.agents/reviews/*|.agents/events/*|.agents/handoffs/*) ;;
      *) err "completion MR changes non-journal path: $path" ;;
    esac
  done < <(git -C "$ROOT" diff --name-only "$MB..$HEAD_SHA")
  if bash "$ROOT/agentmarshal/scripts/task-lifecycle.sh" audit --project-root "$ROOT" >/dev/null 2>&1; then
    ok "completion journal audit passed"
  else
    err "completion journal audit failed"
  fi
fi

# ── 2. review по задаче, не stale (Reviewed-Commit == head SHA) ─────────────
REVIEW=""; RVERDICT=""
if [[ -n "$TASK" ]]; then
  if [[ -n "$REVIEW_FILE" ]]; then
    [[ "$REVIEW_FILE" = /* ]] || REVIEW_FILE="$ROOT/$REVIEW_FILE"
    if [[ ! -f "$REVIEW_FILE" ]]; then
      err "$TASK: explicit review file not found: $REVIEW_FILE"
    else
      REVIEW="$REVIEW_FILE"
      rtask="$(review_field "$REVIEW" Task | grep -oE 'CR-[0-9]+' | head -1)"
      [[ "$rtask" == "$TASK" ]] \
        || err "$TASK: explicit review belongs to '${rtask:-unknown}'"
      rc="$(review_field "$REVIEW" Reviewed-Commit | tr -d ' ')"
      [[ "$rc" == "$HEAD_SHA" ]] \
        || err "$TASK: explicit review Reviewed-Commit='${rc:-empty}' != $HEAD_SHA"
    fi
  else
    while IFS= read -r rv; do
      [[ -f "$rv" ]] || continue
      rtask="$(review_field "$rv" Task | grep -oE 'CR-[0-9]+' | head -1)"
      [[ "$rtask" == "$TASK" ]] || continue
      rc="$(review_field "$rv" Reviewed-Commit | tr -d ' ')"
      [[ -z "$rc" ]] && continue
      if [[ "$HEAD_SHA" == "$rc"* || "$rc" == "$HEAD_SHA"* ]]; then REVIEW="$rv"; break; fi
    done < <(find "$JOURNAL/reviews" -name '*.md' 2>/dev/null)
  fi
  if [[ -z "$REVIEW" ]]; then
    err "$TASK: нет review с Reviewed-Commit == ${HEAD_SHA:0:8} (передай --review-file для raw read-only review)."
  else
    RVERDICT="$(review_field "$REVIEW" Verdict | tr 'A-Z' 'a-z' | tr -d ' ')"
    ok "review: ${REVIEW#$ROOT/} (verdict=${RVERDICT:-?}, reviewed=${HEAD_SHA:0:8})"
    case "$RVERDICT" in
      approved|ok|approve|lgtm) : ;;
      changes_required|blocked|rejected) err "$TASK: verdict='$RVERDICT' — исправь и переревьюй";;
      *) err "$TASK: review без понятного Verdict (approved/changes_required)";;
    esac
  fi
fi

# ── 3. reviewer независимость (R-003): все импл-авторы+co-authors ───────────
if [[ -n "$REVIEW" ]]; then
  R_ROLE="$(review_field "$REVIEW" Reviewer-Role | tr 'A-Z' 'a-z' | tr -d ' ')"
  R_EMAIL="$(review_field "$REVIEW" Reviewer-Email | tr 'A-Z' 'a-z' | tr -d ' ')"
  R_LEGACY="$(review_field "$REVIEW" Reviewer | tr 'A-Z' 'a-z' | tr -d ' ')"
  # Evidence-plane commits do not make their author an implementation writer.
  declare -A WE=() WR=()
  while read -r c; do
    [[ -z "$c" ]] && continue
    implementation="no"
    while read -r f; do
      [[ -z "$f" ]] && continue
      case "$f" in
        .agents/reviews/*|.agents/events/*|.agents/handoffs/*) ;;
        *) implementation="yes" ;;
      esac
    done \
      < <(git -C "$ROOT" show --name-only --format='' "$c" | sed '/^$/d')
    [[ "$implementation" == "no" ]] && continue
    # author + Co-Authored-By emails
    while read -r em; do
      [[ -z "$em" ]] && continue; em="$(printf '%s' "$em" | tr 'A-Z' 'a-z')"
      WE[$em]=1; rr="$(email_role "$em")"; [[ -n "$rr" ]] && WR[$rr]=1
    done < <(
      git -C "$ROOT" show -s --format='%ae' "$c"
      git -C "$ROOT" show -s --format='%b' "$c" \
        | grep -ioE 'co-authored-by:[^<]*<[^>]+>' | grep -oE '<[^>]+>' | tr -d '<>'
    )
  done < <(git -C "$ROOT" rev-list "$MB..$HEAD_SHA")
  if [[ -n "$R_EMAIL" && -n "${WE[$R_EMAIL]:-}" ]]; then
    err "reviewer-email '$R_EMAIL' среди импл-авторов — ревьюер не может быть писателем."
  elif [[ -n "$R_ROLE" && -n "${WR[$R_ROLE]:-}" ]]; then
    err "reviewer-role '$R_ROLE' среди импл-ролей-писателей — нужен независимый ревьюер."
  elif [[ -z "$R_EMAIL" && -z "$R_ROLE" ]]; then
    err "review без структурной identity (Reviewer-Role/Reviewer-Email) — независимость не проверить (R-003)."
  else
    set +u; wr_list="${!WR[*]}"; set -u; [[ -z "$wr_list" ]] && wr_list="∅"
    ok "reviewer независим (role='${R_ROLE:-?}' email='${R_EMAIL:-?}' ∉ импл-писатели: $wr_list)"
  fi
fi

# ── 4. pipeline для head SHA (API-интеграция policy пока не подключена) ─────
if [[ -z "$PIPE_SHA" ]]; then
  err "pipeline для ${HEAD_SHA:0:8} не подтверждён автоматически —"
  echo "       после ЗЕЛЁНОГО пайплайна этого SHA: AGENTMARSHAL_PIPELINE_OK_SHA=$HEAD_SHA или --pipeline-sha $HEAD_SHA" >&2
elif [[ "$HEAD_SHA" == "$PIPE_SHA"* || "$PIPE_SHA" == "$HEAD_SHA"* ]]; then
  ok "pipeline подтверждён для ${HEAD_SHA:0:8}"
else
  err "подтверждённый pipeline SHA ($PIPE_SHA) ≠ head MR (${HEAD_SHA:0:8}) — подтверди именно этот SHA."
fi

echo "──" >&2
[[ $problems -gt 0 ]] && { echo "❌ merge-policy: нарушений — $problems (override: AGENTMARSHAL_SKIP_MERGE_POLICY=1)" >&2; exit 1; }
echo "✅ merge-policy: можно мержить (${TASK:-no-task} @ ${HEAD_SHA:0:8})" >&2; exit 0
