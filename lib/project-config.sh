#!/usr/bin/env bash
# Safe loader/validator for .agentmarshal/project.json.
# The config is treated as JSON data and parsed through jq only.

if [[ -z "${AOPS_RUNTIME_CONFIG_LIB_LOADED:-}" ]]; then
  # shellcheck source=agentmarshal/lib/runtime-config.sh
  source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/runtime-config.sh"
fi

aops_project_error() {
  echo "agentmarshal: $*" >&2
}

aops_project_require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    aops_project_error "required command not found: $cmd"
    return 1
  }
}

aops_project_abs_path() {
  local path="$1"
  if [[ "$path" == /* ]]; then
    _aops_canonical_path "$path"
  else
    _aops_canonical_path "$PWD/$path"
  fi
}

aops_project_default_config_path() {
  local root="$1"
  if [[ -f "$root/.agentmarshal/project.json" ]]; then
    printf '%s\n' "$root/.agentmarshal/project.json"
  elif [[ -f "$root/.agentops/project.json" ]]; then
    printf '%s\n' "$root/.agentops/project.json"
  else
    printf '%s\n' "$root/.agentmarshal/project.json"
  fi
}

aops_project_infer_root_from_config() {
  local config="$1"
  local config_abs config_dir
  config_abs="$(aops_project_abs_path "$config")" || return 1
  config_dir="$(dirname "$config_abs")"
  if [[ "$(basename "$config_dir")" == ".agentmarshal" || "$(basename "$config_dir")" == ".agentops" ]]; then
    printf '%s\n' "$(dirname "$config_dir")"
    return 0
  fi
  git -C "$config_dir" rev-parse --show-toplevel 2>/dev/null || return 1
}

aops_project_discover_root() {
  local explicit_root="${1:-}" explicit_config="${2:-}"
  if [[ -n "$explicit_root" ]]; then
    aops_project_abs_path "$explicit_root"
    return 0
  fi
  if [[ -n "${AGENTMARSHAL_PROJECT_ROOT:-}" ]]; then
    aops_project_abs_path "$AGENTMARSHAL_PROJECT_ROOT"
    return 0
  fi
  if [[ -n "${AGENTOPS_PROJECT_ROOT:-}" ]]; then
    aops_project_abs_path "$AGENTOPS_PROJECT_ROOT"
    return 0
  fi
  if [[ -n "$explicit_config" ]]; then
    aops_project_infer_root_from_config "$explicit_config"
    return 0
  fi
  if [[ -n "${AGENTMARSHAL_PROJECT_CONFIG:-}" ]]; then
    aops_project_infer_root_from_config "$AGENTMARSHAL_PROJECT_CONFIG"
    return 0
  fi
  if [[ -n "${AGENTOPS_PROJECT_CONFIG:-}" ]]; then
    aops_project_infer_root_from_config "$AGENTOPS_PROJECT_CONFIG"
    return 0
  fi
  git rev-parse --show-toplevel 2>/dev/null || _aops_canonical_path "$PWD"
}

aops_project_discover_config() {
  local root="$1" explicit_config="${2:-}"
  if [[ -n "$explicit_config" ]]; then
    aops_project_abs_path "$explicit_config"
    return 0
  fi
  if [[ -n "${AGENTMARSHAL_PROJECT_CONFIG:-}" ]]; then
    aops_project_abs_path "$AGENTMARSHAL_PROJECT_CONFIG"
    return 0
  fi
  if [[ -n "${AGENTOPS_PROJECT_CONFIG:-}" ]]; then
    aops_project_abs_path "$AGENTOPS_PROJECT_CONFIG"
    return 0
  fi
  aops_project_default_config_path "$root"
}

aops_project_validate_json() {
  local root="$1" config="$2"
  aops_project_require_cmd jq || return 1
  [[ -f "$config" ]] || {
    aops_project_error "project config not found: $config"
    return 1
  }

  jq -e '
    def relpath:
      type == "string"
      and length > 0
      and test("^(?!/)(?!.*(?:^|/)\\.\\.(?:/|$))[A-Za-z0-9._/-]+$");
    (.schema == 1)
    and (.preset | type == "string")
    and (.runtime_config | relpath)
    and (.journal_root | relpath)
    and (.agents_dir | relpath)
    and (.prompts_dir | relpath)
    and (.provider.default | type == "string" and test("^[a-z][a-z0-9-]*$"))
    and (.provider.secret_bindings | type == "object")
    and (.provider.secret_bindings | keys_unsorted | all(test("^[A-Z][A-Z0-9_]*$")))
    and all(.provider.secret_bindings[]; type == "string" and test("^[A-Z][A-Z0-9_]*$"))
    and (.plugins.roots.bundled | relpath)
    and (.plugins.roots.host_local | relpath)
    and (.plugins.resolved | type == "array")
    and (.plugins.resolved | all(
      (.id | type == "string")
      and ((.distribution == "bundled")
        or (.distribution == "official")
        or (.distribution == "community")
        or (.distribution == "host-local"))
      and ((.type == "provider") or (.type == "framework") or (.type == "host"))
      and (.root | relpath)
    ))
    and (
      (.adoption | type == "object")
      and ((.adoption.mode == "fresh")
        or (.adoption.mode == "fresh-with-legacy-archive")
        or (.adoption.mode == "adopt-existing"))
      and (
        (.adoption.legacy_journal // "") == ""
        or (.adoption.legacy_journal | relpath)
      )
      and (
        (.adoption.legacy_archive // "") == ""
        or (.adoption.legacy_archive | relpath)
      )
    )
  ' "$config" >/dev/null || {
    aops_project_error "invalid project config: $config"
    return 1
  }

  local resolved
  while IFS= read -r resolved; do
    [[ "$resolved" == "$root" || "$resolved" == "$root/"* ]] || {
      aops_project_error "config path escapes project root: $resolved"
      return 1
    }
  done < <(
    jq -r '.runtime_config, .journal_root, .agents_dir, .prompts_dir,
      .plugins.roots.bundled, .plugins.roots.host_local,
      (.plugins.resolved[]?.root // empty),
      (.adoption.legacy_journal // empty),
      (.adoption.legacy_archive // empty)' "$config" \
      | while IFS= read -r rel; do
          [[ -n "$rel" ]] || continue
          _aops_canonical_path "$root/$rel"
        done
  )
}

aops_project_load() {
  local root="$1" config="$2"
  aops_project_validate_json "$root" "$config" || return 1

  declare -gA AOPS_PROJECT=()
  AOPS_PROJECT[root]="$root"
  AOPS_PROJECT[config]="$config"
  while IFS=$'\t' read -r key value; do
    AOPS_PROJECT["$key"]="$value"
  done < <(
    jq -r '
      [
        ["schema", (.schema | tostring)],
        ["preset", .preset],
        ["runtime_config", .runtime_config],
        ["journal_root", .journal_root],
        ["agents_dir", .agents_dir],
        ["prompts_dir", .prompts_dir],
        ["default_provider", .provider.default],
        ["bundled_plugins_root", .plugins.roots.bundled],
        ["host_local_plugins_root", .plugins.roots.host_local],
        ["adoption_mode", .adoption.mode],
        ["legacy_journal", (.adoption.legacy_journal // "")],
        ["legacy_archive", (.adoption.legacy_archive // "")]
      ] | .[] | @tsv
    ' "$config"
  )
}

aops_project_get() {
  local key="$1"
  printf '%s\n' "${AOPS_PROJECT[$key]:-}"
}

aops_project_path() {
  local key="$1"
  local value
  value="$(aops_project_get "$key")"
  [[ -n "$value" ]] || return 1
  _aops_canonical_path "${AOPS_PROJECT[root]}/$value"
}

aops_project_read_preset() {
  local preset_dir="$1" preset="$2"
  local file="$preset_dir/$preset.json"
  [[ -f "$file" ]] || {
    aops_project_error "unknown preset: $preset"
    return 1
  }
  jq -e '
    (.schema == 1)
    and (.id | type == "string")
    and (.defaults.runtime_config | type == "string")
    and (.defaults.journal_root | type == "string")
    and (.defaults.agents_dir | type == "string")
    and (.defaults.prompts_dir | type == "string")
    and (.defaults.provider.default | type == "string")
    and (.defaults.provider.secret_bindings | type == "object")
    and (.defaults.plugins.roots.bundled | type == "string")
    and (.defaults.plugins.roots.host_local | type == "string")
    and (.defaults.plugins.resolved | type == "array")
    and (.defaults.plugins.resolved | all(
      (.id | type == "string")
      and ((.type == "provider") or (.type == "framework") or (.type == "host"))
      and ((.distribution == "bundled")
        or (.distribution == "official")
        or (.distribution == "community")
        or (.distribution == "host-local"))
      and (.root | type == "string")
    ))
    and (.adoption.runtime_config | type == "string")
    and (.adoption.journal_root | type == "string")
  ' "$file" >/dev/null || {
    aops_project_error "invalid preset file: $file"
    return 1
  }
  printf '%s\n' "$file"
}
