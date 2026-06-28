#!/usr/bin/env bash
# Read-only GitFlic CI API client for AgentMarshal automation.
#
# Pipeline query parameters such as localId/ref/commitId are ignored by the
# tested GitFlic API version. This client paginates and filters exact values
# locally instead.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
[[ -f "$HERE/../agentmarshal.config.sh" ]] && source "$HERE/../agentmarshal.config.sh"

API_BASE="${AGENTMARSHAL_API_BASE:-${GITFLIC_API_BASE:-https://api.gitflic.ru}}"
OWNER="${AGENTMARSHAL_GITFLIC_OWNER:-${GITFLIC_OWNER:-agentmarshal}}"
PROJECT="${AGENTMARSHAL_GITFLIC_PROJECT:-${GITFLIC_PROJECT:-agentmarshal-host}}"
PROJECT_API="${API_BASE%/}/project/$OWNER/$PROJECT"
PAGE_SIZE="${AGENTMARSHAL_GITFLIC_PAGE_SIZE:-100}"
SECRETS_FILE="${PROJECT_SECRETS_FILE:-$HOME/.config/$PROJECT/secrets.env}"

if [[ -z "${GITFLIC_API_TOKEN:-}" && -f "$SECRETS_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$SECRETS_FILE"
fi

die() { echo "gitflic-ci: $*" >&2; exit 1; }
require_cmd() { command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"; }
require_uint() { [[ "$2" =~ ^[0-9]+$ ]] || die "$1 must be an unsigned integer: '$2'"; }

require_cmd curl
require_cmd jq
[[ -n "${GITFLIC_API_TOKEN:-}" ]] \
  || die "GITFLIC_API_TOKEN is not set (checked $SECRETS_FILE)."
[[ "$PAGE_SIZE" =~ ^[1-9][0-9]*$ ]] || die "invalid AGENTMARSHAL_GITFLIC_PAGE_SIZE: '$PAGE_SIZE'."

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

api_get() {
  local path="$1" out="$2" code
  code="$(curl -sS -o "$out" -w '%{http_code}' \
    -H "Authorization: token $GITFLIC_API_TOKEN" "$PROJECT_API$path")" \
    || die "GET $path failed at transport level."
  [[ "$code" == 200 ]] || {
    echo "gitflic-ci: GET $path returned HTTP $code" >&2
    jq -c . "$out" >&2 2>/dev/null || sed -n '1,20p' "$out" >&2
    return 1
  }
}

pipeline_page() {
  local page="$1" out="$2"
  api_get "/cicd/pipeline?size=$PAGE_SIZE&page=$page" "$out"
  jq -e '
    (._embedded.restPipelineModelList | type == "array")
    and ((.page.totalPages // 1) | type == "number")
  ' "$out" >/dev/null || die "unexpected pipeline list response."
}

find_pipeline() {
  local mode="$1" value="$2" page=0 response found pages
  while :; do
    response="$WORK/pipelines-$page.json"
    pipeline_page "$page" "$response"
    if [[ "$mode" == id ]]; then
      found="$(jq -c --argjson value "$value" \
        '._embedded.restPipelineModelList[] | select(.localId == $value)' "$response" | head -1)"
    else
      found="$(jq -c --arg value "$value" \
        '._embedded.restPipelineModelList[] | select(.commitId == $value)' "$response" | head -1)"
    fi
    [[ -n "$found" ]] && { printf '%s\n' "$found"; return 0; }
    pages="$(jq -r '.page.totalPages // 1' "$response")"
    (( page + 1 >= pages )) && return 1
    ((page += 1))
  done
}

collect_pipelines() {
  local out="$1" page=0 response pages
  : > "$out"
  while :; do
    response="$WORK/pipelines-$page.json"
    pipeline_page "$page" "$response"
    jq -c '._embedded.restPipelineModelList[]' "$response" >> "$out"
    pages="$(jq -r '.page.totalPages // 1' "$response")"
    (( page + 1 >= pages )) && break
    ((page += 1))
  done
}

collect_jobs() {
  local pipeline_id="$1" out="$2" page=0 response pages
  : > "$out"
  while :; do
    response="$WORK/jobs-$pipeline_id-$page.json"
    api_get "/cicd/pipeline/$pipeline_id/jobs?size=$PAGE_SIZE&page=$page" "$response"
    jq -e '
      (._embedded.restPipelineJobModelList | type == "array")
      and ((.page.totalPages // 1) | type == "number")
    ' "$response" >/dev/null || die "unexpected job list response for pipeline #$pipeline_id."
    jq -c '._embedded.restPipelineJobModelList[]' "$response" >> "$out"
    pages="$(jq -r '.page.totalPages // 1' "$response")"
    (( page + 1 >= pages )) && break
    ((page += 1))
  done
}

cmd_list() {
  local limit="${1:-20}" rows="$WORK/all-pipelines.jsonl"
  require_uint limit "$limit"
  collect_pipelines "$rows"
  jq -s --argjson limit "$limit" 'sort_by(.localId) | reverse | .[:$limit]' "$rows"
}

cmd_pipeline() {
  local id="${1:-}"
  require_uint pipeline-id "$id"
  find_pipeline id "$id" | jq . || die "pipeline #$id not found."
}

cmd_sha() {
  local sha="${1:-}" rows="$WORK/all-pipelines.jsonl"
  [[ "$sha" =~ ^[0-9a-f]{40}$ ]] || die "sha must be a full 40-character lowercase commit SHA."
  collect_pipelines "$rows"
  jq -s --arg sha "$sha" \
    '[.[] | select(.commitId == $sha)] | sort_by(.localId) | reverse' "$rows"
}

cmd_jobs() {
  local id="${1:-}" rows="$WORK/jobs.jsonl"
  require_uint pipeline-id "$id"
  collect_jobs "$id" "$rows"
  jq -s 'sort_by(.localId)' "$rows"
}

cmd_job() {
  local id="${1:-}" response="$WORK/job.json"
  require_uint job-id "$id"
  api_get "/cicd/job/$id" "$response"
  jq -e '(.localId | type == "number") and (.name | type == "string")' "$response" >/dev/null \
    || die "unexpected job response for #$id."
  jq . "$response"
}

cmd_wait() {
  local id="${1:-}" timeout="${2:-900}" interval="${3:-15}"
  local started now pipeline status previous=""
  require_uint pipeline-id "$id"
  require_uint timeout "$timeout"
  require_uint interval "$interval"
  (( interval > 0 )) || die "interval must be greater than zero."
  started="$(date +%s)"
  while :; do
    pipeline="$(find_pipeline id "$id" || true)"
    [[ -n "$pipeline" ]] || die "pipeline #$id not found."
    status="$(jq -r '.status // "UNKNOWN"' <<<"$pipeline")"
    if [[ "$status" != "$previous" ]]; then
      echo "pipeline #$id status=$status" >&2
      previous="$status"
    fi
    case "$status" in
      SUCCESS) jq . <<<"$pipeline"; return 0 ;;
      FAILED|WARNING|CANCELED|CANCELLED|ERROR|CONFIG_ERROR|SKIPPED)
        jq . <<<"$pipeline"
        return 1
        ;;
      PENDING|RUNNING|CREATED|WAITING|PREPARING) ;;
      *)
        jq . <<<"$pipeline"
        die "unknown terminal policy for pipeline status '$status'."
        ;;
    esac
    now="$(date +%s)"
    (( now - started < timeout )) || {
      jq . <<<"$pipeline"
      echo "gitflic-ci: timeout waiting for pipeline #$id after ${timeout}s." >&2
      return 124
    }
    sleep "$interval"
  done
}

cmd_diagnose() {
  local id="${1:-}" pipeline jobs="$WORK/jobs.jsonl"
  require_uint pipeline-id "$id"
  pipeline="$(find_pipeline id "$id" || true)"
  [[ -n "$pipeline" ]] || die "pipeline #$id not found."
  collect_jobs "$id" "$jobs"
  jq -r '"pipeline #\(.localId) \(.status) ref=\(.ref) sha=\(.commitId) duration=\(.duration // "?")s"' \
    <<<"$pipeline"
  jq -sr '. | sort_by(.localId)[] |
    "job #\(.localId) \(.status)\tstage=\(.stageName)\tname=\(.name)"' "$jobs"
}

cmd_runner_log() {
  local id="${1:-}" response="$WORK/job.json" uuid
  local wsl="${AGENTMARSHAL_WSL_EXE:-/mnt/c/Windows/System32/wsl.exe}"
  local distro="${AGENTMARSHAL_GITFLIC_RUNNER_WSL:-gitflic-runner}"
  local container="${AGENTMARSHAL_GITFLIC_RUNNER_CONTAINER:-gitflic-runner}"
  require_uint job-id "$id"
  [[ "$distro" =~ ^[A-Za-z0-9._-]+$ ]] || die "unsafe runner WSL name: '$distro'."
  [[ "$container" =~ ^[A-Za-z0-9._-]+$ ]] || die "unsafe runner container name: '$container'."
  [[ -x "$wsl" ]] || die "WSL executable not found: $wsl"
  api_get "/cicd/job/$id" "$response"
  uuid="$(jq -r '.id // empty' "$response")"
  [[ "$uuid" =~ ^[0-9a-f-]{36}$ ]] || die "job #$id has no valid UUID."
  "$wsl" -d "$distro" -- docker logs "$container" 2>&1 \
    | grep -F -C 12 "$uuid" \
    || die "runner log has no lines for job UUID $uuid."
}

usage() {
  cat <<'EOF'
Usage: agentmarshal/scripts/gitflic-ci.sh <command> [arguments]

  list [limit]                         latest pipelines as JSON array
  pipeline <local-id>                  exact pipeline as JSON object
  sha <full-commit-sha>                pipelines for exact SHA as JSON array
  jobs <pipeline-local-id>             jobs as JSON array
  job <job-local-id>                   job metadata as JSON object
  wait <pipeline-id> [timeout] [poll]  wait; success only for SUCCESS
  diagnose <pipeline-id>               concise pipeline and job table
  runner-log <job-local-id>            runner service log around job UUID

runner-log is a self-hosted runner fallback. It does not provide job stdout.
Configure AGENTMARSHAL_GITFLIC_RUNNER_WSL/CONTAINER when defaults differ.
EOF
}

case "${1:-}" in
  list) shift; cmd_list "$@" ;;
  pipeline) shift; cmd_pipeline "$@" ;;
  sha) shift; cmd_sha "$@" ;;
  jobs) shift; cmd_jobs "$@" ;;
  job) shift; cmd_job "$@" ;;
  wait) shift; cmd_wait "$@" ;;
  diagnose) shift; cmd_diagnose "$@" ;;
  runner-log) shift; cmd_runner_log "$@" ;;
  -h|--help|help|"") usage ;;
  *) usage >&2; die "unknown command: $1" ;;
esac
