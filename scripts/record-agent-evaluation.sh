#!/usr/bin/env bash
# Trusted recorder for adjudicated, versioned agent scores.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$HERE/../lib/runtime-config.sh"
aops_config_init "$ROOT"

INPUT=""; DRY_RUN="no"
RECORDED_AT="${AGENTMARSHAL_RECORDED_AT:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"

usage() {
  echo "usage: record-agent-evaluation.sh --input <assessment.json> [--dry-run]"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input) INPUT="${2:?}"; shift 2 ;;
    --dry-run) DRY_RUN="yes"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "record-agent-evaluation: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

[[ -n "$INPUT" && -f "$INPUT" ]] \
  || { echo "record-agent-evaluation: --input file is required" >&2; exit 2; }
[[ "$(aops_config_get stats_enabled true)" == true ]] \
  || { echo "record-agent-evaluation: statistics disabled by config"; exit 0; }

ASSESSMENT_CHECK='
  (keys == [
    "acceptance_passed","actionable_findings","adjudication_status","batch_id",
    "confirmed_findings","cost_usd","detected_known_defects",
    "diff_discipline_points","difficulty","duration_seconds",
    "efficiency_points","evidence","executor_model","executor_run_id",
    "executor_vendor","false_positive_findings","human_interventions",
    "implementation_findings","known_defects","pipeline_passed","provenance_valid","reviewer_model",
    "reviewer_run_id","reviewer_vendor","rework_cycles","scope_violations",
    "scoring_version","severity_calibration_errors","task","task_class",
    "total_findings"
  ])
  and (.batch_id | type == "string" and test("^TRIAL-[0-9]{8}-[0-9]+$"))
  and (.task | type == "string" and test("^CR-[0-9]+$"))
  and (.task_class | IN("documentation","ci","frontend","backend","review","operations"))
  and (.difficulty | type == "number" and floor == . and . >= 1 and . <= 5)
  and (.executor_run_id | type == "string" and test("^RUN-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8}$"))
  and (.reviewer_run_id | type == "string" and test("^(none|RUN-[0-9]{8}T[0-9]{6}Z-[a-z0-9-]+-[0-9a-f]{8})$"))
  and (.executor_vendor | type == "string" and test("^[a-z][a-z0-9-]*$"))
  and (.executor_model | type == "string" and length > 0)
  and (.reviewer_vendor | type == "string" and test("^(none|[a-z][a-z0-9-]*)$"))
  and (.reviewer_model | type == "string" and length > 0)
  and (.acceptance_passed | type == "boolean")
  and (.pipeline_passed | type == "boolean")
  and (.provenance_valid | type == "boolean")
  and (.confirmed_findings | keys == ["blocking","p2","p3"])
  and (.implementation_findings | keys == ["blocking","p2","p3"])
  and all(.scope_violations,.confirmed_findings.blocking,.confirmed_findings.p2,
          .confirmed_findings.p3,.false_positive_findings,.known_defects,
          .implementation_findings.blocking,.implementation_findings.p2,
          .implementation_findings.p3,
          .detected_known_defects,.severity_calibration_errors,
          .actionable_findings,.total_findings,.rework_cycles,
          .human_interventions,.duration_seconds;
          type == "number" and floor == . and . >= 0)
  and (.cost_usd | type == "number" and . >= 0)
  and (.diff_discipline_points | type == "number" and floor == . and . >= 0 and . <= 15)
  and (.efficiency_points | type == "number" and floor == . and . >= 0 and . <= 10)
  and (.scoring_version == "trial-v1")
  and (.adjudication_status | IN("pending","confirmed","disputed","excluded"))
  and (.evidence | type == "array" and length > 0
       and all(.[]; type == "string" and length > 0 and (contains("\n") | not)))
  and (.detected_known_defects <= .known_defects)
  and (.actionable_findings <= .total_findings)
  and (.false_positive_findings <= .total_findings)
  and ((.confirmed_findings.blocking + .confirmed_findings.p2
        + .confirmed_findings.p3) <= .total_findings)
  and ((.reviewer_run_id == "none" and .reviewer_vendor == "none"
        and .reviewer_model == "none")
       or (.reviewer_run_id != "none" and .reviewer_vendor != "none"
           and .reviewer_model != "none"))
'
jq -e "$ASSESSMENT_CHECK" "$INPUT" >/dev/null \
  || { echo "record-agent-evaluation: invalid assessment" >&2; exit 1; }

task="$(jq -r .task "$INPUT")"
batch="$(jq -r .batch_id "$INPUT")"
executor_run="$(jq -r .executor_run_id "$INPUT")"
reviewer_run="$(jq -r .reviewer_run_id "$INPUT")"

find "$ROOT/.agents/tasks" -name "${task}*.md" -print -quit | grep -q . \
  || { echo "record-agent-evaluation: unknown task '$task'" >&2; exit 1; }
find "$ROOT/.agents/trials" -name "${batch}.json" -print -quit | grep -q . \
  || { echo "record-agent-evaluation: unknown trial batch '$batch'" >&2; exit 1; }

run_store="$(aops_config_path stats_store)"
find "$run_store" -name "${executor_run}.json" -print -quit | grep -q . \
  || { echo "record-agent-evaluation: executor run '$executor_run' not found" >&2; exit 1; }
if [[ "$reviewer_run" != none ]]; then
  find "$run_store" -name "${reviewer_run}.json" -print -quit | grep -q . \
    || { echo "record-agent-evaluation: reviewer run '$reviewer_run' not found" >&2; exit 1; }
fi

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
FINAL="$WORK/evaluation.json"
stamp="$(printf '%s' "$RECORDED_AT" | tr -d ':-')"
hash="$(jq -r '[.batch_id,.task,.executor_run_id,.reviewer_run_id,.scoring_version] | join("\u0000")' "$INPUT" \
  | sha256sum | cut -c1-8)"
id="EVAL-${stamp}-${batch}-${hash}"

jq --arg id "$id" --arg recorded "$RECORDED_AT" '
  def clamp($low; $high): if . < $low then $low elif . > $high then $high else . end;
  . as $a
  | ($a.confirmed_findings.blocking + $a.confirmed_findings.p2
     + $a.confirmed_findings.p3) as $confirmed
  | (25 - $a.implementation_findings.blocking * 15
        - $a.implementation_findings.p2 * 7
        - $a.implementation_findings.p3 * 2 | clamp(0; 25)) as $quality
  | (10 - $a.human_interventions * 3 - $a.rework_cycles * 2
     | clamp(0; 10)) as $autonomy
  | (if ($a.provenance_valid and $a.scope_violations == 0)
     then (if $a.acceptance_passed then 20 else 0 end)
        + (if $a.pipeline_passed then 20 else 0 end)
        + $quality + $a.diff_discipline_points + $autonomy
        + $a.efficiency_points
     else 0 end) as $implementation
  | (if $a.total_findings == 0
     then (if $confirmed == 0 then 25 else 0 end)
     else (25 * $confirmed / $a.total_findings | floor) end) as $precision
  | (20 - $a.severity_calibration_errors * 5 | clamp(0; 20)) as $severity
  | (if $a.total_findings == 0 then 15
     else (15 * $a.actionable_findings / $a.total_findings | floor) end) as $actionability
  | ($precision + $severity + $actionability + $a.efficiency_points) as $review_without_recall
  | (if $a.reviewer_run_id == "none" then null
     elif $a.known_defects > 0
     then (30 * $a.detected_known_defects / $a.known_defects | floor)
          + $review_without_recall
     else ($review_without_recall * 100 / 70 | floor | clamp(0; 100))
     end) as $review
  | {
      schema: 1, id: $id, recorded_at: $recorded,
      batch_id: $a.batch_id, task: $a.task, task_class: $a.task_class,
      difficulty: $a.difficulty,
      executor_run_id: $a.executor_run_id, reviewer_run_id: $a.reviewer_run_id,
      executor_vendor: $a.executor_vendor, executor_model: $a.executor_model,
      reviewer_vendor: $a.reviewer_vendor, reviewer_model: $a.reviewer_model,
      acceptance_passed: $a.acceptance_passed,
      pipeline_passed: $a.pipeline_passed,
      provenance_valid: $a.provenance_valid,
      scope_violations: $a.scope_violations,
      confirmed_findings: $a.confirmed_findings,
      implementation_findings: $a.implementation_findings,
      false_positive_findings: $a.false_positive_findings,
      known_defects: $a.known_defects,
      detected_known_defects: $a.detected_known_defects,
      severity_calibration_errors: $a.severity_calibration_errors,
      actionable_findings: $a.actionable_findings,
      total_findings: $a.total_findings,
      rework_cycles: $a.rework_cycles,
      human_interventions: $a.human_interventions,
      duration_seconds: $a.duration_seconds, cost_usd: $a.cost_usd,
      diff_discipline_points: $a.diff_discipline_points,
      efficiency_points: $a.efficiency_points,
      implementation_score: $implementation,
      review_score: $review,
      review_score_status:
        (if $a.reviewer_run_id == "none" then "unavailable"
         elif $a.known_defects > 0 then "full" else "provisional" end),
      scoring_version: $a.scoring_version,
      adjudication_status: $a.adjudication_status,
      evidence: $a.evidence
    }
' "$INPUT" | jq -S . > "$FINAL"

store="$(aops_config_path evaluation_store)"
year="${RECORDED_AT:0:4}"
target="$store/$year/$id.json"
if [[ -f "$target" ]]; then
  cmp -s "$FINAL" "$target" \
    && { echo "existing: ${target#$ROOT/}"; exit 0; }
  echo "record-agent-evaluation: conflicting existing id: $id" >&2
  exit 1
fi

if [[ "$DRY_RUN" == yes ]]; then
  echo "would create: ${target#$ROOT/}"
  cat "$FINAL"
else
  mkdir -p "$(dirname "$target")"
  tmp="$(dirname "$target")/.$id.tmp"
  cp "$FINAL" "$tmp"
  mv "$tmp" "$target"
  echo "created: ${target#$ROOT/}"
fi
