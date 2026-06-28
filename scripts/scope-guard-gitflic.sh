#!/usr/bin/env bash
# scope-guard-gitflic.sh — trusted GitFlic API transport for scope-guard.
#
# Avoids `git fetch` in GitFlic runner jobs. The loader resolves master through
# REST API, downloads this script from that exact master SHA, and re-executes
# the trusted copy. Candidate branch data is reduced to manifests consumed by
# the trusted scope-guard.sh.
set -euo pipefail

die() { echo "scope-guard-gitflic (fail-closed): $*" >&2; exit 1; }

BRANCH="${CI_COMMIT_REF_NAME:-}"
HEAD_SHA="${CI_COMMIT_SHA:-}"
BASE_BRANCH="${AGENTMARSHAL_DEFAULT_BRANCH:-${AGENTOPS_DEFAULT_BRANCH:-master}}"
MASTER_SHA="${AGENTMARSHAL_SCOPE_GUARD_MASTER_SHA:-${AGENTOPS_SCOPE_GUARD_MASTER_SHA:-}}"
TRUSTED="${AGENTMARSHAL_SCOPE_GUARD_TRUSTED:-${AGENTOPS_SCOPE_GUARD_TRUSTED:-no}}"
MAX_COMMITS="${AGENTMARSHAL_SCOPE_GUARD_MAX_COMMITS:-${AGENTOPS_SCOPE_GUARD_MAX_COMMITS:-100}}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="${2:?}"; shift 2 ;;
    --head) HEAD_SHA="${2:?}"; shift 2 ;;
    --base-branch) BASE_BRANCH="${2:?}"; shift 2 ;;
    --master-sha) MASTER_SHA="${2:?}"; shift 2 ;;
    *) die "неизвестный аргумент: $1" ;;
  esac
done

[[ -n "$BRANCH" ]] || die "не задана ветка (--branch/CI_COMMIT_REF_NAME)."
[[ "$HEAD_SHA" =~ ^[0-9a-f]{40}$ ]] || die "невалидный head SHA: '$HEAD_SHA'."
[[ "$MAX_COMMITS" =~ ^[1-9][0-9]*$ ]] || die "невалидный MAX_COMMITS: '$MAX_COMMITS'."

API_BASE="${AGENTMARSHAL_API_BASE:-${AGENTOPS_API_BASE:-${GITFLIC_API_BASE:-https://api.gitflic.ru}}}"
OWNER="${AGENTMARSHAL_GITFLIC_OWNER:-${AGENTOPS_GITFLIC_OWNER:-${GITFLIC_OWNER:-${CI_PROJECT_NAMESPACE:-agentmarshal}}}}"
PROJECT="${AGENTMARSHAL_GITFLIC_PROJECT:-${AGENTOPS_GITFLIC_PROJECT:-${GITFLIC_PROJECT:-${CI_PROJECT_NAME:-agentmarshal-host}}}}"
PROJECT_API="${API_BASE%/}/project/$OWNER/$PROJECT"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [[ -n "${CI_JOB_TOKEN:-}" ]]; then
  API_TOKEN="$CI_JOB_TOKEN"
  TOKEN_KIND="job"
elif [[ -n "${AGENTMARSHAL_GITFLIC_API_TOKEN:-${AGENTOPS_GITFLIC_API_TOKEN:-}}" ]]; then
  API_TOKEN="${AGENTMARSHAL_GITFLIC_API_TOKEN:-$AGENTOPS_GITFLIC_API_TOKEN}"
  TOKEN_KIND="access"
elif [[ -n "${GITFLIC_API_TOKEN:-}" ]]; then
  API_TOKEN="$GITFLIC_API_TOKEN"
  TOKEN_KIND="access"
else
  die "нет API token: нужен CI_JOB_TOKEN или read-only AGENTMARSHAL_GITFLIC_API_TOKEN."
fi

urlencode() { jq -rn --arg value "$1" '$value | @uri'; }

# Writes response body to $2 and HTTP status to stdout. GitFlic documents access
# tokens via Authorization; job tokens vary by runner/server version, so try
# the known headers without ever printing the secret.
api_get() {
  local url="$1" out="$2" code header
  local -a headers=()
  if [[ "$TOKEN_KIND" == "access" ]]; then
    headers=("Authorization: token $API_TOKEN")
  else
    headers=(
      "Authorization: token $API_TOKEN"
      "Job-Token: $API_TOKEN"
      "Authorization: Bearer $API_TOKEN"
    )
  fi
  for header in "${headers[@]}"; do
    code="$(curl -sS -o "$out" -w '%{http_code}' -H "$header" "$url")" \
      || die "curl не выполнил GET $url."
    case "$code" in
      200|404) printf '%s\n' "$code"; return 0 ;;
      401|403) ;;
      *) die "GitFlic API GET $url вернул HTTP $code." ;;
    esac
  done
  die "GitFlic API отклонил token (HTTP $code) для $url."
}

load_branches() {
  local out="$1" code
  code="$(api_get "$PROJECT_API/branch?size=100&page=0" "$out")"
  [[ "$code" == 200 ]] || die "список веток недоступен (HTTP $code)."
  jq -e '._embedded.branchList | type == "array"' "$out" >/dev/null \
    || die "неожиданный ответ branch API."
  [[ "$(jq -r '.page.totalPages // 1' "$out")" -le 1 ]] \
    || die "в проекте больше 100 веток: добавь pagination в trusted loader."
}

branch_sha() {
  local branches="$1" name="$2" sha
  sha="$(jq -r --arg name "$name" \
    '._embedded.branchList[] | select(.name == $name) | .lastCommit.hash' "$branches" | head -1)"
  [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || die "ветка '$name' не найдена через API."
  printf '%s\n' "$sha"
}

blob_get() {
  local sha="$1" path="$2" out="$3"
  api_get "$PROJECT_API/blob/download?commitHash=$(urlencode "$sha")&file=$(urlencode "$path")" "$out"
}

BRANCHES="$WORK/branches.json"
load_branches "$BRANCHES"
CURRENT_MASTER="$(branch_sha "$BRANCHES" "$BASE_BRANCH")"
CURRENT_HEAD="$(branch_sha "$BRANCHES" "$BRANCH")"
[[ "$CURRENT_HEAD" == "$HEAD_SHA" ]] \
  || die "ветка '$BRANCH' уже указывает на ${CURRENT_HEAD:0:8}, job проверяет ${HEAD_SHA:0:8}; перезапусти pipeline."

if [[ "$TRUSTED" != "yes" ]]; then
  TRUSTED_LOADER="$WORK/scope-guard-gitflic.sh"
  code="$(blob_get "$CURRENT_MASTER" "agentmarshal/scripts/scope-guard-gitflic.sh" "$TRUSTED_LOADER")"
  if [[ "$code" == 404 ]]; then
    echo "scope-guard: agentmarshal/ ещё нет на '$BASE_BRANCH' — guard пропущен (bootstrap)." >&2
    exit 0
  fi
  chmod +x "$TRUSTED_LOADER"
  AGENTMARSHAL_SCOPE_GUARD_TRUSTED=yes \
  AGENTMARSHAL_SCOPE_GUARD_MASTER_SHA="$CURRENT_MASTER" \
    bash "$TRUSTED_LOADER" \
      --branch "$BRANCH" --head "$HEAD_SHA" --base-branch "$BASE_BRANCH" \
      --master-sha "$CURRENT_MASTER"
  exit $?
fi

[[ "$MASTER_SHA" == "$CURRENT_MASTER" ]] \
  || die "master сдвинулся во время trusted re-exec (${MASTER_SHA:0:8} -> ${CURRENT_MASTER:0:8}); перезапусти pipeline."

TRUST_ROOT="$WORK/trusted"
mkdir -p "$TRUST_ROOT/agentmarshal/scripts" "$TRUST_ROOT/agentmarshal/agents"

for path in \
  agentmarshal/scripts/scope-guard.sh \
  agentmarshal/agentmarshal.config.sh
do
  code="$(blob_get "$MASTER_SHA" "$path" "$TRUST_ROOT/$path")"
  [[ "$code" == 200 ]] || die "trusted файл '$path' отсутствует в ${MASTER_SHA:0:8}."
done

TREE="$WORK/agents.json"
code="$(api_get "$PROJECT_API/blob/recursive?commitHash=$(urlencode "$MASTER_SHA")&directory=$(urlencode "agentmarshal/agents")&depth=1" "$TREE")"
[[ "$code" == 200 ]] || die "trusted role specs недоступны в ${MASTER_SHA:0:8}."
jq -e 'type == "array"' "$TREE" >/dev/null || die "неожиданный ответ blob/recursive."
mapfile -t SPECS < <(jq -r '.[] | .filePath | select(test("^agentmarshal/agents/[^/]+\\.yaml$"))' "$TREE")
[[ ${#SPECS[@]} -gt 0 ]] || die "trusted role specs не найдены."
for path in "${SPECS[@]}"; do
  code="$(blob_get "$MASTER_SHA" "$path" "$TRUST_ROOT/$path")"
  [[ "$code" == 200 ]] || die "не удалось скачать trusted spec '$path'."
done

CHANGED="$WORK/changed-files"
COMMITS="$WORK/commit-files"
: > "$CHANGED"
: > "$COMMITS"

PREFIX="${BRANCH%%/*}"
ROLE_PREFIX="$(awk -v prefix="$PREFIX" '
  $1 == "branch_prefix:" && $2 == prefix { found=1 }
  END { exit(found ? 0 : 1) }
' "$TRUST_ROOT"/agentmarshal/agents/*.yaml >/dev/null 2>&1 && printf yes || printf no)"

if [[ "$ROLE_PREFIX" == "yes" ]]; then
  compare_branch="$(urlencode "$BRANCH")"
  base_branch="$(urlencode "$BASE_BRANCH")"
  page=0
  while :; do
    DIFF="$WORK/diff-$page.json"
    code="$(api_get "$PROJECT_API/branch/compare?compare=$compare_branch&base=$base_branch&size=100&page=$page" "$DIFF")"
    [[ "$code" == 200 ]] || die "branch compare недоступен."
    jq -e '.commitBlobs | type == "array"' "$DIFF" >/dev/null \
      || die "неожиданный ответ branch compare."
    jq -r '.commitBlobs[].filePath' "$DIFF" >> "$CHANGED"
    pages="$(jq -r '.page.totalPages // 1' "$DIFF")"
    (( page + 1 >= pages )) && break
    ((page += 1))
  done
  sort -u -o "$CHANGED" "$CHANGED"
else
  current="$HEAD_SHA"
  count=0
  while [[ "$current" != "$MASTER_SHA" ]]; do
    ((count += 1))
    (( count <= MAX_COMMITS )) \
      || die "integration-ветка не дошла до актуального master за $MAX_COMMITS коммитов; rebase/split required."

    META="$WORK/commit-$count.json"
    code="$(api_get "$PROJECT_API/commit/$(urlencode "$current")" "$META")"
    [[ "$code" == 200 ]] || die "commit ${current:0:8} недоступен через API."
    [[ "$(jq -r '.hash // empty' "$META")" == "$current" ]] \
      || die "commit API вернул неожиданный SHA для ${current:0:8}."
    [[ "$(jq -r '.parentCommitIds | length' "$META")" == 1 ]] \
      || die "integration-ветка должна быть линейной: commit ${current:0:8} имеет не одного parent."
    email="$(jq -r '.authorIdent.emailAddress // empty' "$META")"
    [[ -n "$email" ]] || die "у commit ${current:0:8} нет author email."

    FILES="$WORK/files-$count.json"
    code="$(api_get "$PROJECT_API/commit/$(urlencode "$current")/file" "$FILES")"
    [[ "$code" == 200 ]] || die "список файлов commit ${current:0:8} недоступен."
    jq -e 'type == "array" and all(.[]; (.filePath | type == "string"))' "$FILES" >/dev/null \
      || die "неожиданный ответ commit files для ${current:0:8}."
    while IFS= read -r file; do
      [[ "$file" != *$'\t'* && "$file" != *$'\n'* ]] \
        || die "path с TAB/newline не поддерживается scope manifest."
      printf '%s\t%s\t%s\n' "$current" "$email" "$file" >> "$COMMITS"
    done < <(jq -r '.[].filePath' "$FILES")
    current="$(jq -r '.parentCommitIds[0]' "$META")"
  done
fi

# Detect branch/master movement after collecting API evidence.
load_branches "$BRANCHES.final"
[[ "$(branch_sha "$BRANCHES.final" "$BASE_BRANCH")" == "$MASTER_SHA" ]] \
  || die "master сдвинулся во время проверки; перезапусти pipeline."
[[ "$(branch_sha "$BRANCHES.final" "$BRANCH")" == "$HEAD_SHA" ]] \
  || die "ветка сдвинулась во время проверки; перезапусти pipeline."

chmod +x "$TRUST_ROOT/agentmarshal/scripts/scope-guard.sh"
bash "$TRUST_ROOT/agentmarshal/scripts/scope-guard.sh" \
  --branch "$BRANCH" \
  --agents-dir "$TRUST_ROOT/agentmarshal/agents" \
  --changed-files "$CHANGED" \
  --commit-files "$COMMITS" \
  --strict
