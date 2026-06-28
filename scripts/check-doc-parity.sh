#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$HERE/../docs/public-docs.manifest" ]]; then
  ROOT="$(cd "$HERE/.." && pwd)"
  DOC_ROOT="$ROOT/docs"
else
  ROOT="$(cd "$HERE/../.." && pwd)"
  DOC_ROOT="$ROOT/agentmarshal/docs"
fi
MANIFEST="$DOC_ROOT/public-docs.manifest"

problems=0

err() {
  printf '  ❌ %s\n' "$*" >&2
  ((problems++))
}

ok() {
  printf '  ✅ %s\n' "$*" >&2
}

field() {
  local key="$1" file="$2"
  awk -v wanted="$key" '
    {
      pos=index($0, ":")
      if (!pos) next
      name=substr($0, 1, pos-1)
      value=substr($0, pos+1)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", name)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      if (tolower(name) == tolower(wanted)) {
        print value
        exit
      }
    }
  ' "$file"
}

check_metadata() {
  local file="$1" id="$2" version="$3" language="$4"
  [[ -f "$file" ]] || { err "missing public doc: ${file#$ROOT/}"; return; }
  [[ "$(field Document-ID "$file")" == "$id" ]] \
    || err "${file#$ROOT/}: Document-ID must be '$id'"
  [[ "$(field Document-Version "$file")" == "$version" ]] \
    || err "${file#$ROOT/}: Document-Version must be '$version'"
  [[ "$(field Language "$file")" == "$language" ]] \
    || err "${file#$ROOT/}: Language must be '$language'"
}

check_sections() {
  local file="$1" sections_csv="$2" section
  IFS=',' read -ra sections <<< "$sections_csv"
  for section in "${sections[@]}"; do
    [[ -z "$section" ]] && continue
    grep -Fq "<!-- Section-ID: ${section} -->" "$file" \
      || err "${file#$ROOT/}: missing Section-ID '$section'"
  done
}

check_links() {
  local file="$1" dir link target clean
  dir="$(dirname "$file")"
  while IFS= read -r link; do
    [[ -z "$link" ]] && continue
    case "$link" in
      http://*|https://*|mailto:*|\#*) continue ;;
    esac
    clean="${link%%#*}"
    [[ -z "$clean" ]] && continue
    target="$dir/$clean"
    if [[ -d "$target" ]]; then
      [[ -f "$target/README.md" || -f "$target/README.ru.md" || -f "$target/README.en.md" ]] \
        || err "${file#$ROOT/}: local link '$link' points to directory without README"
    else
      [[ -e "$target" ]] || err "${file#$ROOT/}: broken local link '$link'"
    fi
  done < <(grep -Eo '\[[^]]+\]\([^)]+\)' "$file" 2>/dev/null | sed -E 's/^.*\(([^)]+)\)$/\1/')
}

[[ -f "$MANIFEST" ]] || { err "missing manifest: ${MANIFEST#$ROOT/}"; exit 1; }

while IFS='|' read -r id version ru_path en_path sections; do
  [[ -z "${id:-}" || "$id" == \#* ]] && continue
  if [[ "$ru_path" == agentmarshal/* ]]; then
    ru="$ROOT/${ru_path#agentmarshal/}"
  else
    ru="$ROOT/$ru_path"
  fi
  if [[ "$en_path" == agentmarshal/* ]]; then
    en="$ROOT/${en_path#agentmarshal/}"
  else
    en="$ROOT/$en_path"
  fi
  check_metadata "$ru" "$id" "$version" "ru"
  check_metadata "$en" "$id" "$version" "en"
  if [[ -f "$ru" && -f "$en" ]]; then
    check_sections "$ru" "$sections"
    check_sections "$en" "$sections"
    check_links "$ru"
    check_links "$en"
  fi
done < "$MANIFEST"

[[ $problems -eq 0 ]] && { ok "public bilingual docs parity valid"; exit 0; }
printf '❌ check-doc-parity: problems — %s\n' "$problems" >&2
exit 1
