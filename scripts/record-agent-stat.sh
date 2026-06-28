#!/usr/bin/env bash
# Trusted recorder for normalized, content-free agent performance statistics.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib/runtime-config.sh"
source "$HERE/../lib/project-config.sh"

PROJECT_ROOT_ARG=""
INPUT=""; DRY_RUN="no"
TASK=""; ROLE=""; VENDOR=""; MODEL=""; PROFILE=""; ACTIVITY=""; OUTCOME=""
REASONING_EFFORT="unspecified"
TRIAL="false"; COMMIT="none"; SOURCE_ARTIFACT="manual"
DURATION=0; TURNS=0; HUMAN=0; RETRIES=0; SCOPE=0; TESTS_PASS=0; TESTS_FAIL=0
FINDINGS=0; CHANGED=0; ADDITIONS=0; DELETIONS=0; INPUT_TOKENS=0
OUTPUT_TOKENS=0; COST=0
RECORDED_AT="${AGENTMARSHAL_RECORDED_AT:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"

usage() {
  cat <<'EOF'
usage:
  record-agent-stat.sh [--project-root <root>] --input <json> [--dry-run]
  record-agent-stat.sh [--project-root <root>] --task CR-N --role <role> --vendor <vendor>
    --model <model> --profile <profile> --activity <activity>
    --outcome <outcome> [metric options]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root) PROJECT_ROOT_ARG="${2:?}"; shift 2 ;;
    --input) INPUT="${2:?}"; shift 2 ;; --dry-run) DRY_RUN="yes"; shift ;;
    --task) TASK="${2:?}"; shift 2 ;; --role) ROLE="${2:?}"; shift 2 ;;
    --vendor) VENDOR="${2:?}"; shift 2 ;; --model) MODEL="${2:?}"; shift 2 ;;
    --reasoning-effort) REASONING_EFFORT="${2:?}"; shift 2 ;;
    --profile) PROFILE="${2:?}"; shift 2 ;; --activity) ACTIVITY="${2:?}"; shift 2 ;;
    --outcome) OUTCOME="${2:?}"; shift 2 ;; --trial) TRIAL="${2:?}"; shift 2 ;;
    --commit) COMMIT="${2:?}"; shift 2 ;; --source-artifact) SOURCE_ARTIFACT="${2:?}"; shift 2 ;;
    --duration-seconds) DURATION="${2:?}"; shift 2 ;; --turns) TURNS="${2:?}"; shift 2 ;;
    --human-interventions) HUMAN="${2:?}"; shift 2 ;; --retries) RETRIES="${2:?}"; shift 2 ;;
    --scope-violations) SCOPE="${2:?}"; shift 2 ;; --tests-passed) TESTS_PASS="${2:?}"; shift 2 ;;
    --tests-failed) TESTS_FAIL="${2:?}"; shift 2 ;; --findings) FINDINGS="${2:?}"; shift 2 ;;
    --changed-files) CHANGED="${2:?}"; shift 2 ;; --additions) ADDITIONS="${2:?}"; shift 2 ;;
    --deletions) DELETIONS="${2:?}"; shift 2 ;; --input-tokens) INPUT_TOKENS="${2:?}"; shift 2 ;;
    --output-tokens) OUTPUT_TOKENS="${2:?}"; shift 2 ;; --cost-usd) COST="${2:?}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "record-agent-stat: unknown argument '$1'" >&2; usage >&2; exit 2 ;;
  esac
done

_PROJECT_ROOT="$(aops_project_discover_root "$PROJECT_ROOT_ARG")"
_PROJECT_CONFIG="$(aops_project_discover_config "$_PROJECT_ROOT")"
_HAS_PROJECT_CONFIG=no
if [[ -f "$_PROJECT_CONFIG" ]]; then
  aops_project_load "$_PROJECT_ROOT" "$_PROJECT_CONFIG"
  AGENTMARSHAL_RUNTIME_CONFIG="$(aops_project_path runtime_config)"
  export AGENTMARSHAL_RUNTIME_CONFIG
  _HAS_PROJECT_CONFIG=yes
fi
aops_config_init "$_PROJECT_ROOT"

[[ "$(aops_config_get stats_enabled true)" == true ]] \
  || { echo "record-agent-stat: statistics disabled by config"; exit 0; }

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
STAT="$WORK/stat.json"
if [[ -n "$INPUT" ]]; then
  [[ -f "$INPUT" ]] || { echo "record-agent-stat: input not found: $INPUT" >&2; exit 1; }
  jq -S . "$INPUT" > "$STAT"
else
  for value in TASK ROLE VENDOR MODEL PROFILE ACTIVITY OUTCOME; do
    [[ -n "${!value}" ]] || { echo "record-agent-stat: --${value,,} is required" >&2; exit 2; }
  done
  stamp="$(printf '%s' "$RECORDED_AT" | tr -d ':-')"
  hash="$(printf '%s\0' "$TASK" "$ROLE" "$VENDOR" "$MODEL" "$PROFILE" "$ACTIVITY" \
    "$COMMIT" "$RECORDED_AT" | sha256sum | cut -c1-8)"
  id="RUN-${stamp}-${ROLE}-${hash}"
  jq -n \
    --arg id "$id" --arg recorded "$RECORDED_AT" --arg task "$TASK" \
    --arg role "$ROLE" --arg vendor "$VENDOR" --arg model "$MODEL" \
    --arg reasoning_effort "$REASONING_EFFORT" \
    --arg profile "$PROFILE" --arg activity "$ACTIVITY" --arg outcome "$OUTCOME" \
    --arg commit "$COMMIT" --arg source "$SOURCE_ARTIFACT" \
    --argjson trial "$TRIAL" --argjson duration "$DURATION" --argjson turns "$TURNS" \
    --argjson human "$HUMAN" --argjson retries "$RETRIES" --argjson scope "$SCOPE" \
    --argjson tests_pass "$TESTS_PASS" --argjson tests_fail "$TESTS_FAIL" \
    --argjson findings "$FINDINGS" --argjson changed "$CHANGED" \
    --argjson additions "$ADDITIONS" --argjson deletions "$DELETIONS" \
    --argjson input_tokens "$INPUT_TOKENS" --argjson output_tokens "$OUTPUT_TOKENS" \
    --argjson cost "$COST" '{
      schema: 1, id: $id, recorded_at: $recorded, task: $task, role: $role,
      vendor: $vendor, model: $model, reasoning_effort: $reasoning_effort,
      profile: $profile, activity: $activity,
      outcome: $outcome, trial: $trial, commit: $commit,
      duration_seconds: $duration, turns: $turns,
      human_interventions: $human, retries: $retries,
      scope_violations: $scope, tests_passed: $tests_pass,
      tests_failed: $tests_fail, findings_count: $findings,
      changed_files: $changed, additions: $additions, deletions: $deletions,
      input_tokens: $input_tokens, output_tokens: $output_tokens,
      cost_usd: $cost, source_artifact: $source
    }' | jq -S . > "$STAT"
fi

CHECK='
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
  and (.commit | type == "string" and test("^(none|[0-9a-f]{40})$"))
  and all(.duration_seconds,.turns,.human_interventions,.retries,.scope_violations,
          .tests_passed,.tests_failed,.findings_count,.changed_files,.additions,
          .deletions,.input_tokens,.output_tokens; type == "number" and . >= 0 and floor == .)
  and (.cost_usd | type == "number" and . >= 0)
  and (.source_artifact | type == "string" and length > 0 and (contains("\n") | not))
'
jq -e "$CHECK" "$STAT" >/dev/null \
  || { echo "record-agent-stat: invalid statistic" >&2; exit 1; }

role="$(jq -r .role "$STAT")"; task="$(jq -r .task "$STAT")"

_role_found=no
if [[ "$_HAS_PROJECT_CONFIG" == yes ]]; then
  _agents_dir="$(aops_project_path agents_dir)"
  if [[ -f "$_agents_dir/$role.yaml" ]]; then
    _role_found=yes
  else
    _host_local="$(aops_project_path host_local_plugins_root)"
    if find "$_host_local" -path "*/roles/${role}.md" -print -quit 2>/dev/null | grep -q .; then
      _role_found=yes
    fi
  fi
else
  [[ -f "$AOPS_PROJECT_ROOT/agentmarshal/agents/$role.yaml" ]] && _role_found=yes
fi
[[ "$_role_found" == yes ]] || { echo "record-agent-stat: unknown role '$role'" >&2; exit 1; }

_task_found=no
if [[ "$_HAS_PROJECT_CONFIG" == yes ]]; then
  _journal_root="$(aops_project_path journal_root)"
  find "$_journal_root/tasks" -name "${task}*.md" -print -quit 2>/dev/null | grep -q . \
    && _task_found=yes
else
  find "$AOPS_PROJECT_ROOT/.agents/tasks" -name "${task}*.md" -print -quit 2>/dev/null | grep -q . \
    && _task_found=yes
fi
[[ "$_task_found" == yes ]] || { echo "record-agent-stat: unknown task '$task'" >&2; exit 1; }

store="$(aops_config_path stats_store)"
year="$(jq -r '.recorded_at[0:4]' "$STAT")"
id="$(jq -r .id "$STAT")"
target="$store/$year/$id.json"
if [[ -f "$target" ]]; then
  cmp -s "$STAT" "$target" \
    && { echo "existing: ${target#$AOPS_PROJECT_ROOT/}"; exit 0; }
  echo "record-agent-stat: conflicting existing id: $id" >&2
  exit 1
fi
if [[ "$DRY_RUN" == yes ]]; then
  echo "would create: ${target#$AOPS_PROJECT_ROOT/}"
else
  mkdir -p "$(dirname "$target")"
  tmp="$(dirname "$target")/.$id.tmp"
  cp "$STAT" "$tmp"
  mv "$tmp" "$target"
  echo "created: ${target#$AOPS_PROJECT_ROOT/}"
fi
