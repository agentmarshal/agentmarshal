#!/usr/bin/env bash
# persona-status.sh — health-чек worktree агента перед стартом задачи.
# Codex-замечание: новая задача не должна стартовать с устаревшего мира.
#
# Проверяет: ветка, behind/ahead vs origin/master, чистота дерева, наличие
# .env, git identity (email роли), node_modules. Не меняет ничего.
#
#   persona-status.sh [<worktree-path>]   (default: текущий)
set -uo pipefail

WT="${1:-.}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -f "$HERE/../agentmarshal.config.sh" ]] && source "$HERE/../agentmarshal.config.sh"
BASE_REMOTE="${AGENTMARSHAL_ORIGIN_REMOTE:-origin}/${AGENTMARSHAL_DEFAULT_BRANCH:-master}"

if ! git -C "$WT" rev-parse --git-dir >/dev/null 2>&1; then
  echo "❌ $WT — не git worktree"; exit 2
fi

g() { git -C "$WT" "$@"; }
ok="✅"; warn="⚠️ "; bad="❌"; problems=0

BRANCH="$(g rev-parse --abbrev-ref HEAD)"
PREFIX="${BRANCH%%/*}"
EMAIL="$(g config user.email || echo '?')"
NAME="$(g config user.name || echo '?')"

g fetch "${AGENTMARSHAL_ORIGIN_REMOTE:-origin}" --quiet 2>/dev/null || true
BEHIND="$(g rev-list --count "HEAD..$BASE_REMOTE" 2>/dev/null || echo '?')"
AHEAD="$(g rev-list --count "$BASE_REMOTE..HEAD" 2>/dev/null || echo '?')"
DIRTY="$(g status --porcelain | grep -vE '\.claude/' | wc -l | tr -d ' ')"

echo "── persona-status: $WT ──"
echo "  branch:   $BRANCH (prefix: $PREFIX)"
echo "  identity: $NAME <$EMAIL>"

# behind
if [[ "$BEHIND" == "0" ]]; then echo "  $ok sync: 0 behind $BASE_REMOTE (ahead $AHEAD)"
else echo "  $warn sync: $BEHIND behind $BASE_REMOTE — обнови (git switch $BRANCH; git rebase $BASE_REMOTE)"; ((problems++)); fi

# clean tree (F-007: грязное/конфликтное дерево — НЕ готов)
REBASING=""
[[ -d "$(g rev-parse --git-path rebase-merge 2>/dev/null)" || -d "$(g rev-parse --git-path rebase-apply 2>/dev/null)" ]] && REBASING="yes"
if [[ -n "$REBASING" ]]; then echo "  $bad tree: незавершённый rebase — разреши вручную"; ((problems++))
elif [[ "$DIRTY" == "0" ]]; then echo "  $ok tree: чистое"
else echo "  $bad tree: $DIRTY незакоммиченных (excl .claude) — закоммить/убери"; ((problems++)); fi

# .env
if [[ -f "$WT/.env" ]]; then echo "  $ok .env: есть"
else echo "  $bad .env: НЕТ — dev compose упадёт (см. agentmarshal/config/worktree/env.dev.example)"; ((problems++)); fi

# identity роли по префиксу
if [[ -n "${AGENTMARSHAL_ROLE_EMAIL:-}" || -v AGENTMARSHAL_ROLE_EMAIL ]]; then
  for role in "${!AGENTMARSHAL_ROLE_EMAIL[@]}"; do
    spec="$HERE/../agents/$role.yaml"
    [[ -f "$spec" ]] || continue
    rp="$(awk '$1=="branch_prefix:"{print $2;exit}' "$spec")"
    if [[ "$rp" == "$PREFIX" ]]; then
      exp="${AGENTMARSHAL_ROLE_EMAIL[$role]}"
      if [[ "$EMAIL" == "$exp" ]]; then echo "  $ok identity совпадает с ролью '$role'"
      else echo "  $warn identity '$EMAIL' ≠ ожидаемый для '$role' ($exp)"; ((problems++)); fi
    fi
  done
fi

# node_modules (для frontend worktree)
if [[ -d "$WT/src/frontend" ]]; then
  [[ -d "$WT/src/frontend/node_modules" ]] && echo "  $ok node_modules: есть" \
    || echo "  $warn node_modules: нет (npm ci)"
fi

echo "──"
[[ "$problems" -gt 0 ]] && { echo "$warn problems: $problems"; exit 1; }
echo "$ok worktree готов"; exit 0
