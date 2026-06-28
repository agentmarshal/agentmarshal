#!/usr/bin/env bash
# scope-guard.sh — авторизация изменений по роли/типу ветки.
#
# Классификация ветки по префиксу:
#   role  (lead|fe|be|infra|qa из <agents-dir>/*.yaml branch_prefix)
#         → diff ветки ⊆ scope_allow роли (lead = без ограничений).
#   integration (feature|feat|fix|refactor|completion) — Lead-owned
#         cross-role/integration and post-merge journal branches.
#         ветки. Не имеют единой роли, поэтому проверяем PROVENANCE: каждый
#         коммит, автор которого — НЕ-lead persona, обязан остаться в scope этой
#         persona. Так persona не может через generic-префикс обойти свой scope
#         (R-001). Lead/неизвестные авторы на integration — без ограничений.
#   unknown — в --strict блок (agent-MR обязан иметь роль), иначе пропуск.
#
# FAIL-CLOSED: любая ошибка git/API-данных (нерешаемый ref/нет merge-base/
# сбой diff/невалидный manifest)=exit 1.
# TRUSTED: в CI скрипт и спеки берутся из master (--repo/--agents-dir),
# кандидатский commit и API-manifest — только данные.
#
#   scope-guard.sh [--branch <name>] [--base <ref>] [--head <ref>] [--role <role>]
#                  [--agents-dir <dir>] [--repo <dir>]
#                  [--changed-files <file>] [--commit-files <file>] [--strict]
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
AGENTS_DIR="$ROOT/agentmarshal/agents"
REPO="$ROOT"
# карта role→email (для provenance). Конфиг рядом со скриптом (в т.ч. в /trusted).
[[ -f "$HERE/../agentmarshal.config.sh" ]] && source "$HERE/../agentmarshal.config.sh"

GENERIC_PREFIXES="feature feat fix refactor completion"

die() { echo "❌ scope-guard (fail-closed): $*" >&2; exit 1; }

BRANCH=""; BASE=""; ROLE=""; HEAD_REF=""; STRICT="no"
CHANGED_FILES_FILE=""; COMMIT_FILES_FILE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="${2:?}"; shift 2 ;;
    --base) BASE="${2:?}"; shift 2 ;;
    --head) HEAD_REF="${2:?}"; shift 2 ;;
    --role) ROLE="${2:?}"; shift 2 ;;
    --agents-dir) AGENTS_DIR="${2:?}"; shift 2 ;;
    --repo) REPO="${2:?}"; shift 2 ;;
    --changed-files) CHANGED_FILES_FILE="${2:?}"; shift 2 ;;
    --commit-files) COMMIT_FILES_FILE="${2:?}"; shift 2 ;;
    --strict) STRICT="yes"; shift ;;
    *) echo "scope-guard: неизвестный аргумент $1" >&2; exit 2 ;;
  esac
done

[[ -z "$BRANCH" ]] && BRANCH="$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null)"
[[ -z "$HEAD_REF" ]] && HEAD_REF="HEAD"
PREFIX="${BRANCH%%/*}"
[[ -z "$BASE" ]] && BASE="origin/${AGENTMARSHAL_DEFAULT_BRANCH:-master}"
[[ -d "$AGENTS_DIR" ]] || die "agents-dir не найден: $AGENTS_DIR"
[[ -z "$CHANGED_FILES_FILE" || -f "$CHANGED_FILES_FILE" ]] \
  || die "changed-files manifest не найден: $CHANGED_FILES_FILE"
[[ -z "$COMMIT_FILES_FILE" || -f "$COMMIT_FILES_FILE" ]] \
  || die "commit-files manifest не найден: $COMMIT_FILES_FILE"

extract_list() {  # $1=file $2=key
  awk -v key="$2:" '
    $0 ~ "^"key"$" {f=1; next}
    /^[a-z_]+:/ {f=0}
    f && /^[[:space:]]*-[[:space:]]/ { sub(/^[[:space:]]*-[[:space:]]*/,""); sub(/[[:space:]]*#.*$/,""); print }
  ' "$1"
}
extract_scalar() { awk -v k="$1:" '$1==k{print $2; exit}' "$2"; }

spec_for_role() { echo "$AGENTS_DIR/$1.yaml"; }
email_role() {  # email → role (по AGENTMARSHAL_ROLE_EMAIL), пусто если не persona
  local e="$1" r
  declare -p AGENTMARSHAL_ROLE_EMAIL >/dev/null 2>&1 || return 0
  for r in "${!AGENTMARSHAL_ROLE_EMAIL[@]}"; do
    [[ "${AGENTMARSHAL_ROLE_EMAIL[$r]}" == "$e" ]] && { echo "$r"; return 0; }
  done
}
is_generic() { local g; for g in $GENERIC_PREFIXES; do [[ "$1" == "$g" ]] && return 0; done; return 1; }

starts_with_any() { local p="$1"; shift; local x; for x in "$@"; do [[ "$p" == "$x"* ]] && return 0; done; return 1; }

# выбрать спеку: по --role / branch_prefix
SPEC=""
if [[ -n "$ROLE" ]]; then
  SPEC="$AGENTS_DIR/$ROLE.yaml"
else
  for f in "$AGENTS_DIR"/*.yaml; do
    [[ "$(basename "$f")" == _* ]] && continue
    [[ "$(extract_scalar branch_prefix "$f")" == "$PREFIX" ]] && { SPEC="$f"; ROLE="$(extract_scalar role "$f")"; break; }
  done
fi

# API-mode получает trusted manifests от scope-guard-gitflic.sh и не зависит от
# shallow checkout. Локальный/pre-push режим по-прежнему использует git refs.
EXTERNAL_DATA="no"
if [[ -n "$CHANGED_FILES_FILE" || -n "$COMMIT_FILES_FILE" ]]; then
  EXTERNAL_DATA="yes"
else
  BASE_SHA="$(git -C "$REPO" rev-parse --verify --quiet "${BASE}^{commit}")" \
    || die "base ref '$BASE' не разрешается в коммит (нет ветки/неполный клон?)."
  HEAD_SHA="$(git -C "$REPO" rev-parse --verify --quiet "${HEAD_REF}^{commit}")" \
    || die "head ref '$HEAD_REF' не разрешается в коммит."
  MB="$(git -C "$REPO" merge-base "$BASE_SHA" "$HEAD_SHA" 2>/dev/null)" \
    || die "нет merge-base($BASE, $HEAD_REF) — shallow-клон? сделай fetch с глубиной."
fi

# ── ROLE-ветка ──────────────────────────────────────────────────────────────
if [[ -n "$SPEC" && -f "$SPEC" ]]; then
  mapfile -t ALLOW < <(extract_list "$SPEC" scope_allow)
  mapfile -t DENY  < <(extract_list "$SPEC" scope_deny)
  if [[ ${#ALLOW[@]} -eq 0 ]]; then
    echo "scope-guard: роль '$ROLE' без scope-ограничений (allow пуст) — OK." >&2; exit 0
  fi
  if [[ "$EXTERNAL_DATA" == "yes" ]]; then
    [[ -n "$CHANGED_FILES_FILE" ]] \
      || die "для role-ветки нужен --changed-files manifest."
    CHANGED_RAW="$(cat "$CHANGED_FILES_FILE")" \
      || die "не удалось прочитать changed-files manifest."
  else
    CHANGED_RAW="$(git -C "$REPO" diff --name-only "$MB" "$HEAD_SHA" 2>/dev/null)" \
      || die "git diff упал."
  fi
  mapfile -t CHANGED < <(printf '%s\n' "$CHANGED_RAW" | sed '/^$/d')
  [[ ${#CHANGED[@]} -eq 0 ]] && { echo "scope-guard: нет изменений — OK." >&2; exit 0; }
  V=()
  for file in "${CHANGED[@]}"; do
    [[ -z "$file" ]] && continue
    if [[ ${#DENY[@]} -gt 0 ]] && starts_with_any "$file" "${DENY[@]}"; then V+=("$file (явный deny)"); continue; fi
    starts_with_any "$file" "${ALLOW[@]}" || V+=("$file (вне allow)")
  done
  if [[ ${#V[@]} -gt 0 ]]; then
    echo "❌ scope-guard: ветка '$BRANCH' (роль $ROLE) трогает файлы ВНЕ scope:" >&2
    printf '   - %s\n' "${V[@]}" >&2
    echo "   Допустимо роли '$ROLE': ${ALLOW[*]}" >&2; exit 1
  fi
  echo "✅ scope-guard: ветка '$BRANCH' (роль $ROLE) в пределах scope (${#CHANGED[@]} файлов)." >&2
  exit 0
fi

# ── INTEGRATION (generic) ветка — provenance ────────────────────────────────
if is_generic "$PREFIX"; then
  echo "scope-guard: '$BRANCH' — integration (Lead-owned). Provenance по коммитам persona." >&2
  V=()
  check_commit_file() {
    local commit="$1" ae="$2" file="$3" crole rspec
    local -a RALLOW=() RDENY=()
    [[ -z "$commit" || -z "$ae" || -z "$file" ]] \
      && die "невалидная строка commit-files manifest (нужны commit<TAB>email<TAB>path)."
    crole="$(email_role "$ae")"
    [[ -z "$crole" || "$crole" == "lead" ]] && return 0
    rspec="$(spec_for_role "$crole")"
    [[ -f "$rspec" ]] || { V+=("$commit: автор '$ae' роль '$crole' без спеки"); return 0; }
    mapfile -t RALLOW < <(extract_list "$rspec" scope_allow)
    mapfile -t RDENY  < <(extract_list "$rspec" scope_deny)
    [[ ${#RALLOW[@]} -eq 0 ]] && return 0
    if [[ ${#RDENY[@]} -gt 0 ]] && starts_with_any "$file" "${RDENY[@]}"; then
      V+=("${commit:0:8} ($crole): $file — deny роли $crole на integration-ветке")
      return 0
    fi
    starts_with_any "$file" "${RALLOW[@]}" \
      || V+=("${commit:0:8} ($crole): $file — вне scope роли $crole")
  }

  if [[ "$EXTERNAL_DATA" == "yes" ]]; then
    [[ -n "$COMMIT_FILES_FILE" ]] \
      || die "для integration-ветки нужен --commit-files manifest."
    while IFS=$'\t' read -r commit ae file extra; do
      [[ -z "$commit$ae$file$extra" ]] && continue
      [[ -z "$extra" ]] || die "невалидная строка commit-files manifest: лишнее поле."
      check_commit_file "$commit" "$ae" "$file"
    done < "$COMMIT_FILES_FILE"
  else
    while read -r commit; do
      [[ -z "$commit" ]] && continue
      ae="$(git -C "$REPO" show -s --format='%ae' "$commit")"
      mapfile -t CF < <(git -C "$REPO" show --name-only --format='' "$commit" | sed '/^$/d')
      for file in "${CF[@]}"; do
        [[ -z "$file" ]] && continue
        check_commit_file "$commit" "$ae" "$file"
      done
    done < <(git -C "$REPO" rev-list "$MB..$HEAD_SHA")
  fi
  if [[ ${#V[@]} -gt 0 ]]; then
    echo "❌ scope-guard: на integration-ветке '$BRANCH' persona вышла за свой scope (обход через generic-префикс):" >&2
    printf '   - %s\n' "${V[@]}" >&2
    echo "   Persona должна работать в своей role-ветке (fe/be/qa/infra), не в generic." >&2
    exit 1
  fi
  echo "✅ scope-guard: integration-ветка '$BRANCH' — provenance OK (persona-коммиты в своём scope)." >&2
  exit 0
fi

# ── unknown префикс ─────────────────────────────────────────────────────────
if [[ "$STRICT" == "yes" ]]; then
  die "ветка '$BRANCH' — неизвестный префикс '$PREFIX' (не role и не integration). В strict это блок."
fi
echo "scope-guard: префикс '$PREFIX' не классифицирован — пропуск (не agent-ветка)." >&2
exit 0
