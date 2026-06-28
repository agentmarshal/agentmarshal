#!/usr/bin/env bash
# Safe parser for host-owned .agents/config/agentmarshal.conf.
# The format is key=value; values are data, never sourced as shell code.

aops_env_get() {
  local new_name="$1" old_name="$2" default="${3:-}"
  if [[ -n "${!new_name:-}" ]]; then
    printf '%s\n' "${!new_name}"
  elif [[ -n "${!old_name:-}" ]]; then
    printf '%s\n' "${!old_name}"
  else
    printf '%s\n' "$default"
  fi
}

aops_runtime_config_default() {
  local root="$1"
  if [[ -f "$root/.agents/config/agentmarshal.conf" ]]; then
    printf '%s\n' "$root/.agents/config/agentmarshal.conf"
  elif [[ -f "$root/.agents/config/agentops.conf" ]]; then
    printf '%s\n' "$root/.agents/config/agentops.conf"
  else
    printf '%s\n' "$root/.agents/config/agentmarshal.conf"
  fi
}

aops_config_init() {
  local root
  root="${1:-$(aops_env_get AGENTMARSHAL_PROJECT_ROOT AGENTOPS_PROJECT_ROOT)}"
  if [[ -z "$root" ]]; then
    root="$(git rev-parse --show-toplevel 2>/dev/null)" \
      || { echo "agentmarshal-config: project root not found" >&2; return 1; }
  fi
  AOPS_PROJECT_ROOT="$(cd "$root" && pwd)"
  AOPS_RUNTIME_CONFIG="$(aops_env_get \
    AGENTMARSHAL_RUNTIME_CONFIG \
    AGENTOPS_RUNTIME_CONFIG \
    "$(aops_runtime_config_default "$AOPS_PROJECT_ROOT")")"
  AGENTMARSHAL_RUNTIME_CONFIG="$AOPS_RUNTIME_CONFIG"
  export AGENTMARSHAL_RUNTIME_CONFIG
  [[ -f "$AOPS_RUNTIME_CONFIG" ]] \
    || { echo "agentmarshal-config: config not found: $AOPS_RUNTIME_CONFIG" >&2; return 1; }

  declare -gA AOPS_CONFIG=()
  local line key value lineno=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    ((lineno += 1))
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" == *=* ]] \
      || { echo "agentmarshal-config: $AOPS_RUNTIME_CONFIG:$lineno: expected key=value" >&2; return 1; }
    key="${line%%=*}"
    value="${line#*=}"
    key="${key#"${key%%[![:space:]]*}"}"; key="${key%"${key##*[![:space:]]}"}"
    value="${value#"${value%%[![:space:]]*}"}"; value="${value%"${value##*[![:space:]]}"}"
    [[ "$key" =~ ^[a-z][a-z0-9_]*$ ]] \
      || { echo "agentmarshal-config: $AOPS_RUNTIME_CONFIG:$lineno: invalid key '$key'" >&2; return 1; }
    [[ -z "${AOPS_CONFIG[$key]+x}" ]] \
      || { echo "agentmarshal-config: $AOPS_RUNTIME_CONFIG:$lineno: duplicate key '$key'" >&2; return 1; }
    AOPS_CONFIG[$key]="$value"
  done < "$AOPS_RUNTIME_CONFIG"
}

aops_config_get() {
  local key="$1" default="${2:-}"
  if [[ -n "${AOPS_CONFIG[$key]+x}" ]]; then
    printf '%s\n' "${AOPS_CONFIG[$key]}"
  else
    printf '%s\n' "$default"
  fi
}

aops_config_has_list_item() {
  local key="$1" wanted="$2" item
  IFS=',' read -ra _aops_items <<< "$(aops_config_get "$key")"
  for item in "${_aops_items[@]}"; do
    item="${item#"${item%%[![:space:]]*}"}"; item="${item%"${item##*[![:space:]]}"}"
    [[ "$item" == "$wanted" ]] && return 0
  done
  return 1
}

_aops_lexical_path() {
  local path="$1" part
  local -a parts normalized=()
  [[ "$path" == /* ]] || path="$PWD/$path"
  IFS='/' read -ra parts <<< "$path"
  for part in "${parts[@]}"; do
    case "$part" in
      ""|.) ;;
      ..)
        if ((${#normalized[@]} > 0)); then
          unset "normalized[$((${#normalized[@]} - 1))]"
        fi
        ;;
      *) normalized+=("$part") ;;
    esac
  done
  if ((${#normalized[@]} == 0)); then
    printf '/\n'
  else
    local joined
    joined="$(IFS=/; printf '%s' "${normalized[*]}")"
    printf '/%s\n' "$joined"
  fi
}

_aops_canonical_path() {
  local path probe tail="" parent base
  path="$(_aops_lexical_path "$1")"
  probe="$path"
  while [[ ! -d "$probe" ]]; do
    [[ "$probe" != / ]] || return 1
    tail="/${probe##*/}$tail"
    parent="${probe%/*}"
    probe="${parent:-/}"
  done
  base="$(cd -P "$probe" && pwd)" || return 1
  _aops_lexical_path "$base$tail"
}

_aops_realpath_existing() {
  local path="$1" resolved
  command -v readlink >/dev/null 2>&1 \
    || { echo "agentmarshal-config: required command not found: readlink" >&2; return 1; }
  resolved="$(readlink -f "$path")" || return 1
  [[ -n "$resolved" ]] || return 1
  printf '%s\n' "$resolved"
}

aops_config_path() {
  local key="$1" value
  value="$(aops_config_get "$key")"
  [[ -n "$value" ]] || return 1
  if [[ "$value" == /* ]]; then
    _aops_canonical_path "$value"
  else
    _aops_canonical_path "$AOPS_PROJECT_ROOT/$value"
  fi
}
