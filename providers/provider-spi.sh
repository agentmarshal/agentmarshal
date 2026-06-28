#!/usr/bin/env bash
set -euo pipefail

AOPS_PROVIDER_SPI_VERSION=1
PROVIDER_SPI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=agentmarshal/lib/runtime-config.sh
source "$PROVIDER_SPI_DIR/../lib/runtime-config.sh"
# shellcheck source=agentmarshal/lib/project-config.sh
source "$PROVIDER_SPI_DIR/../lib/project-config.sh"

aops_provider_die() {
  echo "provider-spi: $*" >&2
  exit 1
}

aops_provider_framework_root() {
  cd "$PROVIDER_SPI_DIR/.." && pwd
}

aops_provider_plugins_dir() {
  printf '%s\n' "$(aops_provider_framework_root)/plugins/providers"
}

aops_provider_plugin_search_roots() {
  local root config configured="no"
  root="$(aops_project_discover_root "" "" 2>/dev/null || true)"
  if [[ -n "$root" ]]; then
    config="$(aops_project_discover_config "$root" "" 2>/dev/null || true)"
    if [[ -n "$config" && -f "$config" ]] && aops_project_load "$root" "$config" >/dev/null 2>&1; then
      printf '%s\n' "$(aops_project_path bundled_plugins_root)"
      printf '%s\n' "$(aops_project_path host_local_plugins_root)"
      configured="yes"
    fi
  fi
  [[ "$configured" == yes ]] || printf '%s\n' "$(aops_provider_framework_root)/plugins"
}

aops_provider_default_from_project() {
  local project_root_arg="${1:-}" project_config_arg="${2:-}"
  local root config
  root="$(aops_project_discover_root "$project_root_arg" "$project_config_arg")" \
    || aops_provider_die "cannot discover project root"
  config="$(aops_project_discover_config "$root" "$project_config_arg")" \
    || aops_provider_die "cannot discover project config"
  aops_project_load "$root" "$config" \
    || aops_provider_die "cannot load project config for provider selection"
  local provider
  provider="$(aops_project_get default_provider)"
  [[ -n "$provider" ]] || aops_provider_die "project config does not define provider.default"
  printf '%s\n' "$provider"
}

aops_provider_validate_name() {
  local provider="${1:-}"
  [[ "$provider" =~ ^[a-z][a-z0-9-]*$ ]] \
    || aops_provider_die "invalid provider name: '$provider'"
}

aops_provider_spi_version() {
  printf '%s\n' "$AOPS_PROVIDER_SPI_VERSION"
}

aops_provider_plugin_dir() {
  local provider="${1:?provider is required}" root
  aops_provider_validate_name "$provider"
  while IFS= read -r root; do
    [[ -n "$root" ]] || continue
    if [[ -d "$root/providers/$provider-provider" ]]; then
      printf '%s\n' "$root/providers/$provider-provider"
      return 0
    fi
    if [[ -d "$root/providers/$provider" ]]; then
      printf '%s\n' "$root/providers/$provider"
      return 0
    fi
    if [[ -d "$root/$provider-provider" ]]; then
      printf '%s\n' "$root/$provider-provider"
      return 0
    fi
    if [[ -d "$root/$provider" ]]; then
      printf '%s\n' "$root/$provider"
      return 0
    fi
  done < <(aops_provider_plugin_search_roots)
  aops_provider_die "provider plugin not found: '$provider'"
}

aops_provider_manifest() {
  local dir="${1:?plugin dir is required}"
  printf '%s\n' "$dir/plugin.json"
}

aops_provider_manifest_value() {
  local manifest="${1:?manifest is required}" query="${2:?query is required}"
  jq -er "$query" "$manifest"
}

aops_provider_resolve_entrypoint_v1() {
  local dir="${1:?plugin dir is required}" rel="${2:?entrypoint path is required}"
  local root candidate resolved
  [[ "$rel" =~ ^[A-Za-z0-9._/-]+$ && "$rel" != /* && ! "$rel" =~ (^|/)\.\.(/|$) ]] \
    || aops_provider_die "invalid provider entrypoint path: $rel"
  root="$(_aops_realpath_existing "$dir")" \
    || aops_provider_die "cannot resolve provider plugin root: $dir"
  candidate="$root/$rel"
  resolved="$(_aops_realpath_existing "$candidate")" \
    || aops_provider_die "cannot resolve provider entrypoint: $candidate"
  [[ "$resolved" == "$root/"* ]] \
    || aops_provider_die "provider entrypoint escapes plugin root: $candidate"
  [[ -x "$resolved" ]] \
    || aops_provider_die "provider entrypoint is not executable: $resolved"
  printf '%s\n' "$resolved"
}

aops_provider_assert_plugin_v1() {
  local dir="${1:?plugin dir is required}" manifest execute
  manifest="$(aops_provider_manifest "$dir")"
  [[ -f "$manifest" ]] || aops_provider_die "plugin manifest is missing: $manifest"
  [[ "$(aops_provider_manifest_value "$manifest" '.schema')" == "1" ]] \
    || aops_provider_die "unsupported manifest schema: $manifest"
  [[ "$(aops_provider_manifest_value "$manifest" '.api_version')" == "$AOPS_PROVIDER_SPI_VERSION" ]] \
    || aops_provider_die "provider API version mismatch in $manifest"
  [[ "$(aops_provider_manifest_value "$manifest" '.type')" == "provider" ]] \
    || aops_provider_die "plugin is not a provider: $manifest"
  execute="$(aops_provider_manifest_value "$manifest" '.entrypoints.execute')"
  aops_provider_resolve_entrypoint_v1 "$dir" "$execute" >/dev/null
}

aops_provider_require_capability_v1() {
  local dir="${1:?plugin dir is required}" capability="${2:?capability is required}" manifest
  manifest="$(aops_provider_manifest "$dir")"
  jq -e --arg capability "$capability" '.capabilities | index($capability) != null' "$manifest" >/dev/null \
    || aops_provider_die "provider does not declare capability '$capability': $manifest"
}

aops_provider_entrypoint_v1() {
  local dir="${1:?plugin dir is required}" name="${2:?entrypoint name is required}" manifest rel
  manifest="$(aops_provider_manifest "$dir")"
  rel="$(jq -er --arg name "$name" '.entrypoints[$name]' "$manifest")"
  [[ -n "$rel" ]] || aops_provider_die "entrypoint '$name' is missing in $manifest"
  aops_provider_resolve_entrypoint_v1 "$dir" "$rel"
}

aops_provider_dispatch_v1() {
  local provider="${1:?provider is required}"
  local capability="${2:?capability is required}"
  local operation="${3:?operation is required}"
  local dir execute
  shift 3
  dir="$(aops_provider_plugin_dir "$provider")"
  aops_provider_assert_plugin_v1 "$dir"
  aops_provider_require_capability_v1 "$dir" "$capability"
  execute="$(aops_provider_entrypoint_v1 "$dir" execute)"
  AGENTMARSHAL_PROVIDER_SPI_VERSION="$AOPS_PROVIDER_SPI_VERSION" \
  AGENTMARSHAL_PROVIDER_NAME="$provider" \
  AGENTMARSHAL_PROVIDER_PLUGIN_ROOT="$dir" \
    "$execute" "$capability" "$operation" "$@"
}

aops_provider_assert_plugin() {
  case "$(aops_provider_spi_version)" in
    1) aops_provider_assert_plugin_v1 "$@" ;;
    *) aops_provider_die "unsupported provider SPI version: $(aops_provider_spi_version)" ;;
  esac
}

aops_provider_require_capability() {
  case "$(aops_provider_spi_version)" in
    1) aops_provider_require_capability_v1 "$@" ;;
    *) aops_provider_die "unsupported provider SPI version: $(aops_provider_spi_version)" ;;
  esac
}

aops_provider_entrypoint() {
  case "$(aops_provider_spi_version)" in
    1) aops_provider_entrypoint_v1 "$@" ;;
    *) aops_provider_die "unsupported provider SPI version: $(aops_provider_spi_version)" ;;
  esac
}

aops_provider_dispatch() {
  case "$(aops_provider_spi_version)" in
    1) aops_provider_dispatch_v1 "$@" ;;
    *) aops_provider_die "unsupported provider SPI version: $(aops_provider_spi_version)" ;;
  esac
}
