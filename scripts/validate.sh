#!/usr/bin/env bash
# validate.sh — машинная валидация role/profile-спек и журнала.
# Без неё advisory-метаданные и форматы артефактов расходятся со временем.
#
#   validate.sh [--config] [--specs] [--profiles] [--docs] [--journal]
# Exit ≠0 при любой проблеме. Запускается локально и в CI.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
AGENTS="$ROOT/agentmarshal/agents"
PROFILES="$ROOT/agentmarshal/profiles"
JOURNAL="$ROOT/.agents"
FRAMEWORK_DOCS="$ROOT/agentmarshal/docs"
FRAMEWORK_ADR="$FRAMEWORK_DOCS/adr"
TASK_LIFECYCLE="$ROOT/agentmarshal/scripts/task-lifecycle.sh"
DOC_PARITY="$ROOT/agentmarshal/scripts/check-doc-parity.sh"
source "$ROOT/agentmarshal/lib/runtime-config.sh"
RUNTIME_CONFIG="$(aops_runtime_config_default "$ROOT")"

ALLOWED_STATUS="open in_progress in_review blocked done abandoned"
ALLOWED_OWNER="lead frontend backend qa release"
ALLOWED_VERDICT="approved changes_required blocked rejected"
ALLOWED_HO_STATUS="open ack acked closed done"
ALLOWED_ADR_STATUS="Proposed Accepted Superseded Deprecated"
ALLOWED_PROFILE_MODE="review implementation analysis operations"
ALLOWED_WRITE_POLICY="none role_scope workspace"
ALLOWED_NETWORK_POLICY="none read_only allowed"
ALLOWED_RECORDER="launcher dispatcher agent"
ALLOWED_TOOL="read grep glob shell edit write browser computer git-read git-write network"
ALLOWED_VENDOR="claude codex gemini"
ALLOWED_MODEL_POLICY="preferred required"
ALLOWED_TASK_TYPE="feature bug refactor documentation technical_debt security operations process"
ALLOWED_PRIORITY="P0 P1 P2 P3"
SHA_RE='^[0-9a-f]{7,40}$'
FULL_SHA_RE='^[0-9a-f]{40}$'
TRIAGE_KEY_RE='^sha256:[0-9a-f]{64}$'

DO_CONFIG="no"; DO_SPECS="no"; DO_PROFILES="no"; DO_DOCS="no"; DO_JOURNAL="no"
[[ $# -eq 0 ]] && { DO_CONFIG="yes"; DO_SPECS="yes"; DO_PROFILES="yes"; DO_DOCS="yes"; DO_JOURNAL="yes"; }
while [[ $# -gt 0 ]]; do case "$1" in
  --config) DO_CONFIG="yes";; --specs) DO_SPECS="yes";; --profiles) DO_PROFILES="yes";;
  --docs) DO_DOCS="yes";; --journal) DO_JOURNAL="yes";;
  *) echo "validate: неизвестный аргумент $1" >&2; exit 2;; esac; shift; done

problems=0
err() { echo "  ❌ $*" >&2; ((problems++)); }
ok()  { echo "  ✅ $*" >&2; }
scalar() { awk -v k="$1:" '$1==k{print $2; exit}' "$2"; }
has_key() { grep -qE "^$1:" "$2"; }
field() {
  awk -v k="$1" '
    {
      pos=index($0, ":")
      if (!pos) next
      name=substr($0, 1, pos-1)
      if (tolower(name) == tolower(k)) {
        value=substr($0, pos+1)
        sub(/^[[:space:]]*/, "", value)
        sub(/[[:space:]]*$/, "", value)
        print value
        exit
      }
    }
  ' "$2"
}
in_set() { local x="$1"; shift; local i; for i in "$@"; do [[ "$x" == "$i" ]] && return 0; done; return 1; }
nested() {
  awk -v p="$1:" -v c="  $2:" '
    $0 ~ "^"p"$" {f=1; next}
    /^[a-z_]+:/ {f=0}
    f && index($0,c)==1 {sub(c,""); sub(/^[[:space:]]*/,""); sub(/[[:space:]]*#.*$/,""); print; exit}
  ' "$3"
}
list_values() {
  awk -v key="$1:" '
    $0 ~ "^"key"$" {f=1; next}
    /^[a-z_]+:/ {f=0}
    f && /^[[:space:]]*-[[:space:]]/ {
      sub(/^[[:space:]]*-[[:space:]]*/,"")
      sub(/[[:space:]]*#.*$/,"")
      print
    }
  ' "$2"
}

# ── host runtime config ─────────────────────────────────────────────────────
if [[ "$DO_CONFIG" == "yes" ]]; then
  echo "── host config ($RUNTIME_CONFIG) ──" >&2
  if aops_config_init "$ROOT"; then
    required_keys="schema review_language active_roles operating_mode active_milestone backlog_amplification_limit worktree_root worktree_pattern stats_enabled stats_store evaluation_store stats_raw_store stats_retention_days"
    allowed_keys="$required_keys"
    for key in $required_keys; do
      [[ -n "${AOPS_CONFIG[$key]+x}" ]] || err "config: нет ключа '$key'"
    done
    for key in "${!AOPS_CONFIG[@]}"; do
      in_set "$key" $allowed_keys || err "config: неизвестный ключ '$key'"
    done
    [[ "$(aops_config_get schema)" == 1 ]] || err "config: schema должна быть 1"
    lang="$(aops_config_get review_language)"
    [[ "$lang" =~ ^[a-z]{2}(-[A-Z]{2})?$ ]] || err "config: review_language='$lang' не похож на language tag"
    operating_mode="$(aops_config_get operating_mode)"
    in_set "$operating_mode" normal cutoff_freeze \
      || err "config: operating_mode должен быть normal|cutoff_freeze"
    active_milestone="$(aops_config_get active_milestone)"
    [[ "$active_milestone" =~ ^[a-z0-9][a-z0-9._-]*$ ]] \
      || err "config: active_milestone имеет неверный формат"
    amplification_limit="$(aops_config_get backlog_amplification_limit)"
    [[ "$amplification_limit" =~ ^(0(\.[0-9]+)?|1(\.0+)?)$ ]] \
      || err "config: backlog_amplification_limit должен быть числом 0..1"
    stats_enabled="$(aops_config_get stats_enabled)"
    [[ "$stats_enabled" == true || "$stats_enabled" == false ]] || err "config: stats_enabled должен быть true|false"
    retention="$(aops_config_get stats_retention_days)"
    [[ "$retention" =~ ^[1-9][0-9]*$ ]] || err "config: stats_retention_days должен быть положительным числом"

    declare -A seen_active_role
    active_count=0
    IFS=',' read -ra active_roles <<< "$(aops_config_get active_roles)"
    for role in "${active_roles[@]}"; do
      role="${role#"${role%%[![:space:]]*}"}"; role="${role%"${role##*[![:space:]]}"}"
      [[ "$role" =~ ^[a-z][a-z0-9-]*$ ]] || { err "config: невалидная active role '$role'"; continue; }
      [[ -z "${seen_active_role[$role]:-}" ]] || err "config: active role '$role' дублируется"
      seen_active_role[$role]=1; ((active_count++))
      spec="$AGENTS/$role.yaml"
      [[ -f "$spec" ]] || { err "config: role spec '$role' не найдена"; continue; }
      [[ "$(scalar active "$spec")" == true ]] || err "config: role '$role' указана active, но spec active=false"
    done
    [[ $active_count -gt 0 ]] || err "config: active_roles пуст"

    wt_pattern="$(aops_config_get worktree_pattern)"
    [[ "$wt_pattern" == *"{alias}"* ]] || err "config: worktree_pattern должен содержать {alias}"
    sample="${wt_pattern//\{repo\}/repo}"; sample="${sample//\{alias\}/role}"
    [[ "$sample" =~ ^[A-Za-z0-9._-]+$ ]] || err "config: worktree_pattern создаёт небезопасное имя '$sample'"
    wt_root="$(aops_config_path worktree_root 2>/dev/null || true)"
    [[ -n "$wt_root" ]] || err "config: worktree_root не разрешается"
    case "$wt_root/" in "$ROOT/"*) err "config: worktree_root должен быть вне project root";; esac

    stats_store="$(aops_config_get stats_store)"
    evaluation_store="$(aops_config_get evaluation_store)"
    stats_raw="$(aops_config_get stats_raw_store)"
    [[ "$stats_store" == .agents/stats/* ]] || err "config: stats_store должен быть внутри .agents/stats/"
    [[ "$evaluation_store" == .agents/stats/* ]] || err "config: evaluation_store должен быть внутри .agents/stats/"
    [[ "$stats_raw" == .agents/runs/* ]] || err "config: stats_raw_store должен быть внутри ignored .agents/runs/"
    stats_store_path="$(aops_config_path stats_store 2>/dev/null || true)"
    evaluation_store_path="$(aops_config_path evaluation_store 2>/dev/null || true)"
    stats_raw_path="$(aops_config_path stats_raw_store 2>/dev/null || true)"
    stats_root="$(_aops_canonical_path "$ROOT/.agents/stats")"
    runs_root="$(_aops_canonical_path "$ROOT/.agents/runs")"
    case "$stats_store_path/" in "$stats_root/"*) ;; *) err "config: stats_store выходит из .agents/stats/";; esac
    case "$evaluation_store_path/" in "$stats_root/"*) ;; *) err "config: evaluation_store выходит из .agents/stats/";; esac
    case "$stats_raw_path/" in "$runs_root/"*) ;; *) err "config: stats_raw_store выходит из .agents/runs/";; esac
    [[ $problems -eq 0 ]] && ok "host runtime config валиден (${active_count} active roles)"
  else
    err "host runtime config не читается"
  fi
fi

# ── role-спеки ──────────────────────────────────────────────────────────────
if [[ "$DO_SPECS" == "yes" ]]; then
  echo "── role-спеки ($AGENTS) ──" >&2
  declare -A seen_prefix seen_role
  for f in "$AGENTS"/*.yaml; do
    [[ "$(basename "$f")" == _* ]] && continue
    base="$(basename "$f" .yaml)"
    for key in role display_name branch_prefix active prompt; do has_key "$key" "$f" || err "$base: нет поля '$key'"; done
    r="$(scalar role "$f")"; [[ "$r" == "$base" ]] || err "$base: role='$r' ≠ имени файла"
    a="$(scalar active "$f")"; [[ "$a" == "true" || "$a" == "false" ]] || err "$base: active='$a' (нужно true/false)"
    has_key scope_allow "$f" || err "$base: нет ключа scope_allow"
    grep -qE "^[[:space:]]+preferred:" "$f" || err "$base: нет vendor.preferred"
    p="$(scalar branch_prefix "$f")"
    [[ -n "${seen_prefix[$p]:-}" ]] && err "$base: branch_prefix '$p' дублирует ${seen_prefix[$p]}"; seen_prefix[$p]="$base"
    [[ -n "${seen_role[$r]:-}" ]] && err "$base: role '$r' дублирует ${seen_role[$r]}"; seen_role[$r]="$base"
    pf="$AGENTS/$(scalar prompt "$f")"; [[ -f "$pf" ]] || err "$base: prompt-файл не найден: $(scalar prompt "$f")"
  done
  [[ $problems -eq 0 ]] && ok "спеки валидны"
fi

# ── execution profiles ─────────────────────────────────────────────────────
if [[ "$DO_PROFILES" == "yes" ]]; then
  echo "── execution profiles ($PROFILES) ──" >&2
  for f in "$PROFILES"/*.yaml; do
    [[ -f "$f" ]] || continue
    [[ "$(basename "$f")" == _* ]] && continue
    base="$(basename "$f" .yaml)"
    for key in profile display_name role active mode write_policy network_policy \
               session_persistence prompt output_recorder output_directory
    do
      has_key "$key" "$f" || err "$base: нет поля '$key'"
    done
    pid="$(scalar profile "$f")"
    [[ "$pid" == "$base" ]] || err "$base: profile='$pid' ≠ имени файла"
    prole="$(scalar role "$f")"
    in_set "$prole" $ALLOWED_OWNER || err "$base: role='$prole' не из [$ALLOWED_OWNER]"
    [[ -f "$AGENTS/$prole.yaml" ]] || err "$base: role-спека '$prole' не найдена"
    active="$(scalar active "$f")"
    [[ "$active" == "true" || "$active" == "false" ]] || err "$base: active='$active' (нужно true/false)"
    persistence="$(scalar session_persistence "$f")"
    [[ "$persistence" == "true" || "$persistence" == "false" ]] \
      || err "$base: session_persistence='$persistence' (нужно true/false)"
    mode="$(scalar mode "$f")"
    in_set "$mode" $ALLOWED_PROFILE_MODE || err "$base: mode='$mode' не из [$ALLOWED_PROFILE_MODE]"
    wp="$(scalar write_policy "$f")"
    in_set "$wp" $ALLOWED_WRITE_POLICY || err "$base: write_policy='$wp' не из [$ALLOWED_WRITE_POLICY]"
    np="$(scalar network_policy "$f")"
    in_set "$np" $ALLOWED_NETWORK_POLICY || err "$base: network_policy='$np' не из [$ALLOWED_NETWORK_POLICY]"
    recorder="$(scalar output_recorder "$f")"
    in_set "$recorder" $ALLOWED_RECORDER || err "$base: output_recorder='$recorder' не из [$ALLOWED_RECORDER]"
    [[ "$wp" != "none" || "$recorder" != "agent" ]] \
      || err "$base: write_policy=none несовместим с output_recorder=agent"
    outdir="$(scalar output_directory "$f")"
    [[ "$outdir" == ".agents/runs/" || "$outdir" == ".agents/runs" ]] \
      || err "$base: output_directory должен быть .agents/runs/"
    pp="$PROFILES/$(scalar prompt "$f")"
    [[ -f "$pp" ]] || err "$base: prompt-файл не найден: $(scalar prompt "$f")"
    preferred="$(nested vendor preferred "$f")"
    model="$(nested vendor model "$f")"
    in_set "$preferred" $ALLOWED_VENDOR || err "$base: vendor.preferred='$preferred' не из [$ALLOWED_VENDOR]"
    [[ -n "$model" ]] || err "$base: нет vendor.model"
    tool_n=0
    while IFS= read -r tool; do
      [[ -z "$tool" ]] && continue
      ((tool_n++))
      in_set "$tool" $ALLOWED_TOOL || err "$base: tool='$tool' не из [$ALLOWED_TOOL]"
      if [[ "$wp" == "none" ]]; then
        case "$tool" in edit|write|shell|git-write) err "$base: write_policy=none запрещает tool='$tool'";; esac
      fi
      if [[ "$np" == "none" && "$tool" == "network" ]]; then
        err "$base: network_policy=none запрещает tool=network"
      fi
    done < <(list_values tools "$f")
    [[ $tool_n -gt 0 ]] || err "$base: tools пуст"
  done
  [[ $problems -eq 0 ]] && ok "execution profiles валидны"
fi

# ── framework docs / ADR ────────────────────────────────────────────────────
if [[ "$DO_DOCS" == "yes" ]]; then
  echo "── framework docs ($FRAMEWORK_DOCS) ──" >&2
  [[ -f "$FRAMEWORK_DOCS/README.md" ]] || err "docs: нет README.md"
  [[ -f "$FRAMEWORK_ADR/README.md" ]] || err "docs/adr: нет README.md"
  declare -A seen_framework_adr
  adr_n=0
  for adr in "$FRAMEWORK_ADR"/ADR-*.md; do
    [[ -f "$adr" ]] || continue
    b="$(basename "$adr")"
    file_id="$(printf '%s' "$b" | grep -oE '^ADR-[0-9]+' || true)"
    heading_id="$(grep -m1 -E '^# ADR-[0-9]+:' "$adr" | grep -oE 'ADR-[0-9]+' || true)"
    [[ -n "$heading_id" ]] || err "$b: нет заголовка '# ADR-NNNN: title'"
    [[ "$file_id" == "$heading_id" ]] || err "$b: id заголовка '$heading_id' ≠ имени '$file_id'"
    [[ -n "${seen_framework_adr[$file_id]:-}" ]] && err "$b: дубликат id '$file_id'"
    seen_framework_adr[$file_id]="$b"
    ast="$(field Status "$adr")"
    [[ -n "$ast" ]] && { in_set "$ast" $ALLOWED_ADR_STATUS || err "$b: Status='$ast' не из [$ALLOWED_ADR_STATUS]"; } || err "$b: нет Status"
    grep -qE '^Date: [0-9]{4}-[0-9]{2}-[0-9]{2}$' "$adr" || err "$b: нет валидного Date"
    grep -qE '^Decision owner: .+' "$adr" || err "$b: нет Decision owner"
    ((adr_n++))
  done
  [[ $adr_n -gt 0 ]] || err "docs/adr: framework ADR не найдены"
  while IFS= read -r link; do
    [[ -f "$FRAMEWORK_ADR/$link" ]] || err "docs/adr/README.md: битая ссылка '$link'"
  done < <(grep -oE '\(ADR-[0-9]+-[^)]+\.md\)' "$FRAMEWORK_ADR/README.md" 2>/dev/null | tr -d '()')
  grep -RqsE '\.agents/decisions/ADR-[0-9]+' "$FRAMEWORK_DOCS" \
    && err "framework docs ссылаются на legacy host path .agents/decisions/ADR-*"
  if [[ -x "$DOC_PARITY" ]]; then
    parity_output="$(bash "$DOC_PARITY" 2>&1)"
    parity_rc=$?
    if [[ $parity_rc -ne 0 ]]; then
      while IFS= read -r line; do
        [[ -n "$line" ]] && err "doc parity: $line"
      done <<< "$parity_output"
    else
      ok "$parity_output"
    fi
  else
    err "docs: executable check-doc-parity.sh не найден"
  fi
  [[ $problems -eq 0 ]] && ok "framework docs/ADR валидны ($adr_n ADR)"
fi

# ── журнал ──────────────────────────────────────────────────────────────────
if [[ "$DO_JOURNAL" == "yes" ]]; then
  echo "── журнал ($JOURNAL) ──" >&2
  declare -A seen_task seen_msgid seen_triage_key
  task_n=0; msg_n=0   # bash+set -u: ${#assoc[@]} падает на пустом массиве → считаем явно
  task_exists() { find "$JOURNAL/tasks" -name "${1}*.md" 2>/dev/null | grep -q . ; }

  # задачи: строгий заголовок, Owner/Status из допустимых, уникальный id
  while IFS= read -r t; do
    [[ -z "$t" ]] && continue
    head1="$(grep -m1 -E '\S' "$t")"
    if ! [[ "$head1" =~ ^#\ CR-[0-9]+:\  ]]; then err "task $(basename "$t"): первый заголовок не '# CR-<id>: <title>'"; continue; fi
    id="$(printf '%s' "$head1" | grep -oE 'CR-[0-9]+' | head -1)"
    own="$(field Owner "$t")"; st="$(field Status "$t")"
    type="$(field Type "$t" | tr -d ' ')"; priority="$(field Priority "$t" | tr -d ' ')"
    [[ -n "$own" ]] && { in_set "$own" $ALLOWED_OWNER || err "task $id: Owner='$own' не из [$ALLOWED_OWNER]"; } || err "task $id: нет Owner"
    [[ -n "$st" ]] && { in_set "$st" $ALLOWED_STATUS || err "task $id: Status='$st' не из [$ALLOWED_STATUS]"; } || err "task $id: нет Status"
    [[ -n "$type" ]] && { in_set "$type" $ALLOWED_TASK_TYPE || err "task $id: Type='$type' не из [$ALLOWED_TASK_TYPE]"; } || err "task $id: нет Type"
    [[ -n "$priority" ]] && { in_set "$priority" $ALLOWED_PRIORITY || err "task $id: Priority='$priority' не из [$ALLOWED_PRIORITY]"; } || err "task $id: нет Priority"
    case "$t" in
      "$JOURNAL/tasks/open/"*)
        [[ "$st" != "done" && "$st" != "abandoned" ]] \
          || err "task $id: Status='$st' не соответствует каталогу tasks/open"
        ;;
      "$JOURNAL/tasks/done/"*)
        [[ "$st" == "done" ]] \
          || err "task $id: каталог tasks/done требует Status: done"
        ;;
      "$JOURNAL/tasks/abandoned/"*)
        [[ "$st" == "abandoned" ]] \
          || err "task $id: каталог tasks/abandoned требует Status: abandoned"
        ;;
    esac
    ep="$(field Execution-Profile "$t" | tr -d ' ')"
    [[ -z "$ep" || -f "$PROFILES/$ep.yaml" ]] || err "task $id: Execution-Profile='$ep' не найден"
    if [[ -n "$ep" && -f "$PROFILES/$ep.yaml" ]]; then
      eprole="$(scalar role "$PROFILES/$ep.yaml")"
      [[ "$eprole" == "$own" ]] \
        || err "task $id: Execution-Profile '$ep' принадлежит role='$eprole', Owner='$own'"
      epactive="$(scalar active "$PROFILES/$ep.yaml")"
      [[ "$epactive" == "true" ]] || err "task $id: Execution-Profile '$ep' не активен"
    fi
    pv="$(field Preferred-Vendor "$t" | tr -d ' ')"
    [[ -z "$pv" ]] || in_set "$pv" $ALLOWED_VENDOR || err "task $id: Preferred-Vendor='$pv' не из [$ALLOWED_VENDOR]"
    if grep -qiE '^Preferred-Model:' "$t"; then
      pmodel="$(field Preferred-Model "$t" | tr -d ' ')"
      [[ -n "$pmodel" ]] || err "task $id: Preferred-Model задан пустым"
    fi
    mp="$(field Model-Policy "$t" | tr -d ' ')"
    [[ -z "$mp" ]] || in_set "$mp" $ALLOWED_MODEL_POLICY || err "task $id: Model-Policy='$mp' не из [$ALLOWED_MODEL_POLICY]"
    source_findings="$(field Source-Findings "$t")"
    source_task="$(field Source-Task "$t" | tr -d ' ')"
    source_commit="$(field Source-Commit "$t" | tr -d ' ')"
    source_review="$(field Source-Review "$t" | tr -d ' ')"
    due_before="$(field Due-Before "$t" | tr -d ' ')"
    triage_key="$(field Triage-Key "$t" | tr -d ' ')"
    if [[ -n "$source_findings$source_task$source_commit$source_review$triage_key" ]]; then
      [[ "$source_task" =~ ^CR-[0-9]+$ ]] || err "task $id: Source-Task должен быть CR-NNN"
      [[ "$source_task" =~ ^CR-[0-9]+$ ]] && task_exists "$source_task" \
        || err "task $id: Source-Task '$source_task' не найдена"
      [[ "$source_commit" =~ $FULL_SHA_RE ]] || err "task $id: Source-Commit должен быть полным SHA"
      [[ "$source_review" =~ ^CR-[0-9]+@[0-9a-f]{40}$ ]] || err "task $id: Source-Review должен быть CR-NNN@<full-sha>"
      [[ "$source_review" == "$source_task@$source_commit" ]] \
        || err "task $id: Source-Review не совпадает с Source-Task@Source-Commit"
      [[ "$source_findings" =~ ^[A-Za-z][A-Za-z0-9.-]*(,[[:space:]]*[A-Za-z][A-Za-z0-9.-]*)*$ ]] \
        || err "task $id: Source-Findings имеет неверный формат"
      [[ "$due_before" =~ ^(none|[0-9]{4}-[0-9]{2}-[0-9]{2}|CR-[0-9]+|[a-z0-9][a-z0-9._-]*)$ ]] \
        || err "task $id: Due-Before имеет неверный формат"
      if [[ "$triage_key" =~ $TRIAGE_KEY_RE ]]; then
        [[ -n "${seen_triage_key[$triage_key]:-}" ]] \
          && err "task $id: Triage-Key дублирует ${seen_triage_key[$triage_key]}"
        seen_triage_key[$triage_key]="$id"
      else
        err "task $id: Triage-Key имеет неверный формат"
      fi
    elif [[ -n "$due_before" ]]; then
      [[ "$due_before" =~ ^(none|[0-9]{4}-[0-9]{2}-[0-9]{2}|CR-[0-9]+|[a-z0-9][a-z0-9._-]*)$ ]] \
        || err "task $id: Due-Before имеет неверный формат"
    fi
    [[ -n "${seen_task[$id]:-}" ]] && err "task $id: дубликат id (${seen_task[$id]} и $(basename "$t"))"; seen_task[$id]="$(basename "$t")"; ((task_n++))
  done < <(find "$JOURNAL/tasks" -name '*.md' 2>/dev/null)

  if [[ -x "$TASK_LIFECYCLE" ]]; then
    audit_output="$(bash "$TASK_LIFECYCLE" audit --project-root "$ROOT" 2>&1)"
    audit_rc=$?
    if [[ $audit_rc -ne 0 ]]; then
      while IFS= read -r line; do
        [[ -n "$line" ]] && err "task completion: $line"
      done <<< "$audit_output"
    else
      ok "$audit_output"
    fi
  else
    err "task completion: executable task-lifecycle.sh не найден"
  fi

  # ревью: Task(существует) + Verdict(допустим) + reviewed-commit(SHA) + reviewer identity
  for rv in "$JOURNAL"/reviews/2026/*.md; do
    [[ -f "$rv" ]] || continue; b="$(basename "$rv")"
    tk="$(field Task "$rv" | grep -oE 'CR-[0-9]+' | head -1)"
    [[ -n "$tk" ]] || err "review $b: нет 'Task:'"
    [[ -n "$tk" ]] && { task_exists "$tk" || err "review $b: ссылается на несуществующую задачу $tk"; }
    vd="$(field Verdict "$rv" | tr -d ' ')"
    [[ -n "$vd" ]] && { in_set "$vd" $ALLOWED_VERDICT || err "review $b: Verdict='$vd' не из [$ALLOWED_VERDICT]"; } || err "review $b: нет Verdict"
    rc="$(awk -F': *' 'tolower($1) ~ /^reviewed[ -]commit$/{print $2; exit}' "$rv" | tr -d ' ')"
    [[ -n "$rc" ]] || err "review $b: нет Reviewed-Commit"
    [[ -n "$rc" && ! "$rc" =~ $SHA_RE ]] && err "review $b: Reviewed-Commit '$rc' не похож на SHA"
    { [[ -n "$(field Reviewer-Role "$rv")" ]] || [[ -n "$(field Reviewer "$rv")" ]]; } || err "review $b: нет reviewer identity (Reviewer-Role или Reviewer)"
  done

  # handoff: обязательные поля envelope, SHA, status, task ref, unique id
  for ho in "$JOURNAL"/handoffs/2026/*.md; do
    [[ -f "$ho" ]] || continue; b="$(basename "$ho")"
    for k in id task type from to created_at branch commit requires_ack status; do
      grep -qiE "^$k:" "$ho" || err "handoff $b: нет поля '$k'"
    done
    hid="$(field id "$ho")"; [[ -n "$hid" ]] && { [[ -n "${seen_msgid[$hid]:-}" ]] && err "handoff $b: дубликат id '$hid'"; seen_msgid[$hid]="$b"; ((msg_n++)); }
    htk="$(field task "$ho" | grep -oE 'CR-[0-9]+' | head -1)"; [[ -n "$htk" ]] && { task_exists "$htk" || err "handoff $b: задача $htk не найдена"; }
    hc="$(field commit "$ho" | tr -d ' ')"; [[ -n "$hc" && ! "$hc" =~ $SHA_RE ]] && err "handoff $b: commit '$hc' не похож на SHA"
    hs="$(field status "$ho" | tr -d ' ')"; [[ -n "$hs" ]] && { in_set "$hs" $ALLOWED_HO_STATUS || err "handoff $b: status='$hs' не из [$ALLOWED_HO_STATUS]"; }
  done

  # event-конверты (если есть): id/task/type/created_at/status + uniq id + task ref
  while IFS= read -r ev; do
    [[ -z "$ev" ]] && continue; b="$(basename "$ev")"
    for k in id task type created_at status; do grep -qiE "^$k:" "$ev" || err "event $b: нет поля '$k'"; done
    eid="$(field id "$ev")"; [[ -n "$eid" ]] && { [[ -n "${seen_msgid[$eid]:-}" ]] && err "event $b: дубликат id '$eid'"; seen_msgid[$eid]="$b"; ((msg_n++)); }
    etk="$(field task "$ev" | grep -oE 'CR-[0-9]+' | head -1)"; [[ -n "$etk" ]] && { task_exists "$etk" || err "event $b: задача $etk не найдена"; }
  done < <(find "$JOURNAL/events" -name '*.md' 2>/dev/null)

  # ADR: Status(допустим) + Date; битые [[ADR-NNNN]]
  for adr in "$JOURNAL"/decisions/ADR-*.md; do
    [[ -f "$adr" ]] || continue; b="$(basename "$adr")"
    ast="$(field Status "$adr")"; [[ -n "$ast" ]] && { in_set "$ast" $ALLOWED_ADR_STATUS || err "$b: Status='$ast' не из [$ALLOWED_ADR_STATUS]"; } || err "$b: нет Status"
    grep -qE '^Date:' "$adr" || err "$b: нет 'Date:'"
  done
  while IFS= read -r link; do
    num="${link#ADR-}"; ls "$JOURNAL"/decisions/ADR-"${num}"-*.md >/dev/null 2>&1 || err "битая ссылка [[$link]] (нет decisions/ADR-${num}-*.md)"
  done < <(grep -rhoE '\[\[ADR-[0-9]+\]\]' "$JOURNAL" 2>/dev/null | tr -d '[]' | sort -u)

  # tracked agent run statistics
  while IFS= read -r stat; do
    [[ -z "$stat" ]] && continue
    b="$(basename "$stat")"
    jq -e '
      ((keys - ["reasoning_effort"]) == [
        "activity","additions","changed_files","commit","cost_usd","deletions",
        "duration_seconds","findings_count","human_interventions","id",
        "input_tokens","model","outcome","output_tokens","profile","recorded_at",
        "retries","role","schema","scope_violations","source_artifact","task",
        "tests_failed","tests_passed","trial","turns","vendor"
      ])
      and (.schema == 1)
      and (.id | type == "string" and test("^RUN-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8}$"))
      and (.recorded_at | type == "string" and test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"))
      and (.task | type == "string" and test("^CR-[0-9]+$"))
      and (.role | type == "string" and test("^[a-z][a-z0-9-]*$"))
      and (.vendor | type == "string" and test("^[a-z][a-z0-9-]*$"))
      and (.model | type == "string" and length > 0)
      and ((.reasoning_effort // "unspecified") | IN("unspecified","low","medium","high","max"))
      and (.profile | type == "string" and test("^[a-z0-9][a-z0-9-]*$"))
      and (.activity | type == "string" and test("^[a-z][a-z0-9-]*$"))
      and (.outcome | IN("success","approved","changes_required","blocked","rejected","failed","canceled","partial","negative"))
      and (.trial | type == "boolean")
      and (.commit | test("^(none|[0-9a-f]{40})$"))
      and all(.duration_seconds,.turns,.human_interventions,.retries,.scope_violations,
              .tests_passed,.tests_failed,.findings_count,.changed_files,.additions,
              .deletions,.input_tokens,.output_tokens; type == "number" and . >= 0 and floor == .)
      and (.cost_usd | type == "number" and . >= 0)
      and (.source_artifact | type == "string" and length > 0 and (contains("\n") | not))
    ' "$stat" >/dev/null 2>&1 || { err "stat $b: невалидная запись"; continue; }
    sid="$(jq -r .id "$stat")"
    [[ "$b" == "$sid.json" ]] || err "stat $b: filename не совпадает с id '$sid'"
    stk="$(jq -r .task "$stat")"; task_exists "$stk" || err "stat $b: task '$stk' не найдена"
    srole="$(jq -r .role "$stat")"
    _role_valid=no
    [[ -f "$AGENTS/$srole.yaml" ]] && _role_valid=yes
    if [[ "$_role_valid" == no ]]; then
      find "$ROOT/.agentmarshal/plugins" -path "*/roles/${srole}.md" -print -quit 2>/dev/null | grep -q . && _role_valid=yes
    fi
    [[ "$_role_valid" == yes ]] || err "stat $b: role '$srole' не найдена"
  done < <(find "$JOURNAL/stats/runs" -type f -name 'RUN-*.json' 2>/dev/null)

  # trial batches: immutable experiment contract with reciprocal reviewers.
  while IFS= read -r batch; do
    [[ -z "$batch" ]] && continue
    b="$(basename "$batch")"
    jq -e '
      (keys == [
        "assignments","base_commit","created_at","id","minimum_stable_sample",
        "schema","scoring_version"
      ])
      and (.schema == 1)
      and (.id | type == "string" and test("^TRIAL-[0-9]{8}-[0-9]+$"))
      and (.created_at | type == "string" and test("^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"))
      and (.base_commit | type == "string" and test("^[0-9a-f]{40}$"))
      and (.scoring_version == "trial-v1")
      and (.minimum_stable_sample | type == "number" and floor == . and . >= 3)
      and (.assignments | type == "array" and length >= 2)
      and all(.assignments[];
        (keys == [
          "difficulty","executor_model","executor_vendor","reviewer_model",
          "reviewer_vendor","scope","task","task_class"
        ])
        and (.task | type == "string" and test("^CR-[0-9]+$"))
        and (.task_class | IN("documentation","ci","frontend","backend","review","operations"))
        and (.difficulty | type == "number" and floor == . and . >= 1 and . <= 5)
        and (.executor_vendor | IN("claude","codex"))
        and (.reviewer_vendor | IN("claude","codex"))
        and (.executor_vendor != .reviewer_vendor)
        and (.executor_model | type == "string" and length > 0)
        and (.reviewer_model | type == "string" and length > 0)
        and (.scope | type == "array" and length > 0
             and all(.[]; type == "string" and length > 0))
      )
    ' "$batch" >/dev/null 2>&1 || { err "trial batch $b: невалидная запись"; continue; }
    bid="$(jq -r .id "$batch")"
    [[ "$b" == "$bid.json" ]] || err "trial batch $b: filename не совпадает с id '$bid'"
    while IFS= read -r btask; do
      task_exists "$btask" || err "trial batch $b: task '$btask' не найдена"
    done < <(jq -r '.assignments[].task' "$batch")
  done < <(find "$JOURNAL/trials" -type f -name 'TRIAL-*.json' 2>/dev/null)

  # adjudicated evaluations are derived from immutable run records.
  while IFS= read -r evaluation; do
    [[ -z "$evaluation" ]] && continue
    b="$(basename "$evaluation")"
    jq -e '
      (keys == [
        "acceptance_passed","actionable_findings","adjudication_status",
        "batch_id","confirmed_findings","cost_usd","detected_known_defects",
        "diff_discipline_points","difficulty","duration_seconds",
        "efficiency_points","evidence","executor_model","executor_run_id",
        "executor_vendor","false_positive_findings","human_interventions","id",
        "implementation_findings",
        "implementation_score","known_defects","pipeline_passed",
        "provenance_valid","recorded_at","review_score","review_score_status",
        "reviewer_model","reviewer_run_id","reviewer_vendor","rework_cycles",
        "schema","scope_violations","scoring_version",
        "severity_calibration_errors","task","task_class","total_findings"
      ])
      and (.schema == 1)
      and (.id | type == "string" and test("^EVAL-[0-9]{8}T[0-9]{6}Z-[A-Za-z0-9._-]+-[0-9a-f]{8}$"))
      and (.batch_id | type == "string" and test("^TRIAL-[0-9]{8}-[0-9]+$"))
      and (.task | type == "string" and test("^CR-[0-9]+$"))
      and (.executor_run_id | type == "string" and test("^RUN-"))
      and (.reviewer_run_id | type == "string" and test("^(none|RUN-)"))
      and (.implementation_score | type == "number" and floor == . and . >= 0 and . <= 100)
      and ((.review_score == null)
           or (.review_score | type == "number" and floor == . and . >= 0 and . <= 100))
      and (.review_score_status | IN("full","provisional","unavailable"))
      and (.scoring_version == "trial-v1")
      and (.adjudication_status | IN("pending","confirmed","disputed","excluded"))
      and (.evidence | type == "array" and length > 0)
    ' "$evaluation" >/dev/null 2>&1 || { err "evaluation $b: невалидная запись"; continue; }
    eid="$(jq -r .id "$evaluation")"
    [[ "$b" == "$eid.json" ]] || err "evaluation $b: filename не совпадает с id '$eid'"
    etk="$(jq -r .task "$evaluation")"; task_exists "$etk" || err "evaluation $b: task '$etk' не найдена"
    ebatch="$(jq -r .batch_id "$evaluation")"
    find "$JOURNAL/trials" -name "$ebatch.json" -print -quit | grep -q . \
      || err "evaluation $b: trial batch '$ebatch' не найден"
    erun="$(jq -r .executor_run_id "$evaluation")"
    find "$JOURNAL/stats/runs" -name "$erun.json" -print -quit | grep -q . \
      || err "evaluation $b: executor run '$erun' не найден"
    rrun="$(jq -r .reviewer_run_id "$evaluation")"
    if [[ "$rrun" != none ]]; then
      find "$JOURNAL/stats/runs" -name "$rrun.json" -print -quit | grep -q . \
        || err "evaluation $b: reviewer run '$rrun' не найден"
    fi
  done < <(find "$JOURNAL/stats/evaluations" -type f -name 'EVAL-*.json' 2>/dev/null)

  [[ $problems -eq 0 ]] && ok "журнал согласован (задач: $task_n, msg-id: $msg_n)"
fi

echo "──" >&2
[[ $problems -gt 0 ]] && { echo "❌ validate: проблем — $problems" >&2; exit 1; }
echo "✅ validate: OK" >&2; exit 0
