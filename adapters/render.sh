#!/usr/bin/env bash
# render.sh — agnostic role-спека → нативный конфиг конкретного vendor'а.
#
# Источник истины: agentmarshal/agents/<role>.yaml. Этот dispatcher грузит
# vendor-адаптер (adapters/<vendor>/adapter.sh, функция render_<vendor>) и
# отдаёт ему распарсенные поля. Один спек → любой производитель.
#
#   render.sh <role> <vendor>        # vendor: claude | codex | gemini
#   render.sh frontend claude        → .claude/agents/frontend.md
set -euo pipefail

ROLE="${1:?usage: render.sh <role> <vendor>}"
VENDOR="${2:?usage: render.sh <role> <vendor>}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AOPS="$(cd "$HERE/.." && pwd)"
ROOT="$(cd "$AOPS/.." && pwd)"
source "$AOPS/agentmarshal.config.sh"

SPEC="$AOPS/agents/$ROLE.yaml"
[[ -f "$SPEC" ]] || { echo "render: нет спеки $SPEC" >&2; exit 1; }
ADAPTER="$HERE/$VENDOR/adapter.sh"
[[ -f "$ADAPTER" ]] || { echo "render: нет адаптера для '$VENDOR' ($ADAPTER) — стаб? см. $HERE/$VENDOR/README.md" >&2; exit 1; }

# ── парсеры спеки (без yq) — экспортируются адаптеру ────────────────────────
spec_scalar() { awk -v k="$1:" '$1==k{ $1=""; sub(/^ /,""); sub(/[[:space:]]*#.*$/,""); print; exit }' "$SPEC"; }
spec_list()   { awk -v key="$1:" '$0 ~ "^"key"$"{f=1;next} /^[a-z_]+:/{f=0} f && /^[[:space:]]*-[[:space:]]/{sub(/^[[:space:]]*-[[:space:]]*/,"");sub(/[[:space:]]*#.*$/,"");print}' "$SPEC"; }
spec_nested() { # $1=parent $2=child  → значение child под parent
  awk -v p="$1:" -v c="  $2:" '$0 ~ "^"p"$"{f=1;next} /^[a-z_]+:/{f=0} f && index($0,c)==1{ sub(c,""); sub(/^[[:space:]]*/,""); sub(/[[:space:]]*#.*$/,""); print; exit }' "$SPEC"; }

export SPEC ROLE VENDOR AOPS ROOT
export -f spec_scalar spec_list spec_nested

source "$ADAPTER"
"render_$VENDOR" "$ROLE"
