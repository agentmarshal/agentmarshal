#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib/runtime-config.sh"
source "$HERE/../lib/project-config.sh"

PROJECT_ROOT_ARG=""
if [[ "${1:-}" == "--project-root" ]]; then
  PROJECT_ROOT_ARG="${2:?}"
  shift 2
fi

COMMAND="${1:-summary}"; [[ $# -gt 0 ]] && shift
JSON="no"; ROLE=""; VENDOR=""; MODEL=""; TRIAL="all"; TASK_CLASS=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root) PROJECT_ROOT_ARG="${2:?}"; shift 2 ;;
    --json) JSON="yes"; shift ;; --role) ROLE="${2:?}"; shift 2 ;;
    --vendor) VENDOR="${2:?}"; shift 2 ;; --model) MODEL="${2:?}"; shift 2 ;;
    --trial) TRIAL="${2:?}"; shift 2 ;;
    --task-class) TASK_CLASS="${2:?}"; shift 2 ;;
    *) echo "agentmarshal-stats: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

_PROJECT_ROOT="$(aops_project_discover_root "$PROJECT_ROOT_ARG")"
_PROJECT_CONFIG="$(aops_project_discover_config "$_PROJECT_ROOT")"
if [[ -f "$_PROJECT_CONFIG" ]]; then
  aops_project_load "$_PROJECT_ROOT" "$_PROJECT_CONFIG"
  AGENTMARSHAL_RUNTIME_CONFIG="$(aops_project_path runtime_config)"
  export AGENTMARSHAL_RUNTIME_CONFIG
fi
aops_config_init "$_PROJECT_ROOT"

store="$(aops_config_path stats_store)"
WORK="$(mktemp)"; trap 'rm -f "$WORK"' EXIT
find "$store" -type f -name 'RUN-*.json' -print0 2>/dev/null \
  | xargs -0 -r jq -c . > "$WORK"

FILTER='
  map(select(($role == "" or .role == $role)
    and ($vendor == "" or .vendor == $vendor)
    and ($model == "" or .model == $model)
    and ($trial == "all" or (.trial == ($trial == "true")))))
'
case "$COMMAND" in
  list)
    jq -s --arg role "$ROLE" --arg vendor "$VENDOR" --arg model "$MODEL" \
      --arg trial "$TRIAL" "$FILTER | sort_by(.recorded_at)" "$WORK"
    ;;
  ranking)
    eval_store="$(aops_config_path evaluation_store)"
    EVALS="$(mktemp)"
    trap 'rm -f "$WORK" "$EVALS"' EXIT
    find "$eval_store" -type f -name 'EVAL-*.json' -print0 2>/dev/null \
      | xargs -0 -r jq -c . > "$EVALS"
    ranking="$(jq -s --arg class "$TASK_CLASS" '
      def median:
        sort as $s | length as $n
        | if $n == 0 then 0
          elif ($n % 2) == 1 then $s[($n / 2 | floor)]
          else (($s[$n / 2 - 1] + $s[$n / 2]) / 2) end;
      map(select(.adjudication_status == "confirmed"
                 and ($class == "" or .task_class == $class))) as $rows
      | (
          $rows
          | group_by([.task_class,.executor_vendor,.executor_model])
          | map({
              activity: "implementation", task_class: .[0].task_class,
              vendor: .[0].executor_vendor, model: .[0].executor_model,
              score_status: "full", samples: length,
              median_score: (map(.implementation_score) | median),
              stable: (length >= 3)
            })
        ) + (
          $rows
          | map(select(.review_score != null))
          | group_by([.task_class,.reviewer_vendor,.reviewer_model,.review_score_status])
          | map({
              activity: "review", task_class: .[0].task_class,
              vendor: .[0].reviewer_vendor, model: .[0].reviewer_model,
              score_status: .[0].review_score_status, samples: length,
              median_score: (map(.review_score) | median),
              stable: (length >= 3 and .[0].review_score_status == "full")
            })
        )
      | sort_by(.activity,.task_class,-.median_score)
    ' "$EVALS")"
    if [[ "$JSON" == yes ]]; then
      printf '%s\n' "$ranking" | jq .
    else
      printf 'ACTIVITY\tTASK_CLASS\tVENDOR\tMODEL\tSTATUS\tSAMPLES\tMEDIAN\tSTABLE\n'
      printf '%s\n' "$ranking" | jq -r '.[] | [
        .activity,.task_class,.vendor,.model,.score_status,.samples,
        .median_score,.stable
      ] | @tsv'
    fi
    ;;
  summary)
    summary="$(jq -s --arg role "$ROLE" --arg vendor "$VENDOR" --arg model "$MODEL" \
      --arg trial "$TRIAL" "$FILTER | group_by([.role,.vendor,.model,.activity]) |
      map({
        role: .[0].role, vendor: .[0].vendor, model: .[0].model,
        activity: .[0].activity, runs: length,
        successful: map(select(.outcome == \"success\" or .outcome == \"approved\")) | length,
        avg_duration_seconds: ((map(.duration_seconds) | add // 0) / length | floor),
        human_interventions: (map(.human_interventions) | add // 0),
        retries: (map(.retries) | add // 0),
        scope_violations: (map(.scope_violations) | add // 0),
        tests_failed: (map(.tests_failed) | add // 0),
        findings: (map(.findings_count) | add // 0),
        cost_usd: (map(.cost_usd) | add // 0)
      })" "$WORK")"
    if [[ "$JSON" == yes ]]; then
      printf '%s\n' "$summary" | jq .
    else
      printf 'ROLE\tVENDOR\tMODEL\tACTIVITY\tRUNS\tOK\tAVG_SEC\tHUMAN\tRETRIES\tSCOPE\tTEST_FAIL\tFINDINGS\tCOST_USD\n'
      printf '%s\n' "$summary" | jq -r '.[] | [
        .role,.vendor,.model,.activity,.runs,.successful,.avg_duration_seconds,
        .human_interventions,.retries,.scope_violations,.tests_failed,
        .findings,(.cost_usd * 10000 | round / 10000)
      ] | @tsv'
    fi
    ;;
  *) echo "usage: agentmarshal-stats.sh {summary|list|ranking} [filters]" >&2; exit 2 ;;
esac
