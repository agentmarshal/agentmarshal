#!/usr/bin/env bash
set -euo pipefail

die() {
  echo "mock-provider: $*" >&2
  exit 1
}

not_impl() {
  echo "mock-provider: operation not implemented: $1/$2" >&2
  exit 3
}

CAPABILITY="${1:-}"
OPERATION="${2:-}"
shift $(( $# >= 2 ? 2 : $# ))
SCENARIO="${AGENTMARSHAL_PROVIDER_MOCK_SCENARIO:-success}"

BRANCH="main"
SHA=""
MR_ID="101"
BASE_SHA="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
HEAD_SHA="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
PIPELINE_ID="7001"
TIMEOUT="900"
INTERVAL="15"
PATH_ARG="README.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --branch) BRANCH="${2:?}"; shift 2 ;;
    --sha) SHA="${2:?}"; shift 2 ;;
    --mr|--mr-id) MR_ID="${2:?}"; shift 2 ;;
    --base) BASE_SHA="${2:?}"; shift 2 ;;
    --head) HEAD_SHA="${2:?}"; shift 2 ;;
    --pipeline-id) PIPELINE_ID="${2:?}"; shift 2 ;;
    --timeout) TIMEOUT="${2:?}"; shift 2 ;;
    --interval) INTERVAL="${2:?}"; shift 2 ;;
    --path) PATH_ARG="${2:?}"; shift 2 ;;
    *) die "unknown argument: $1" ;;
  esac
done

pipeline_json() {
  local status="$1"
  jq -nc \
    --arg provider "mock" \
    --arg scenario "$SCENARIO" \
    --arg ref "$BRANCH" \
    --arg sha "${SHA:-$HEAD_SHA}" \
    --argjson localId "$PIPELINE_ID" \
    --arg status "$status" \
    '{
      provider: $provider,
      scenario: $scenario,
      localId: $localId,
      ref: $ref,
      commitId: $sha,
      status: $status
    }'
}

jobs_json() {
  jq -nc --arg scenario "$SCENARIO" '
    [
      {
        localId: 8101,
        stageName: "lint",
        name: "shellcheck",
        status: (if $scenario == "failed" then "FAILED" else "SUCCESS" end)
      },
      {
        localId: 8102,
        stageName: "test",
        name: "provider-spi",
        status: (
          if $scenario == "error" then "ERROR"
          elif $scenario == "failed" then "FAILED"
          else "SUCCESS"
          end
        )
      }
    ]'
}

case "$CAPABILITY/$OPERATION" in
  provider.refs/branch-sha)
    case "$BRANCH" in
      main|master) SHA="1111111111111111111111111111111111111111" ;;
      feature/mock|feat/mock) SHA="2222222222222222222222222222222222222222" ;;
      *) SHA="3333333333333333333333333333333333333333" ;;
    esac
    jq -nc --arg provider "mock" --arg branch "$BRANCH" --arg sha "$SHA" \
      '{provider: $provider, branch: $branch, sha: $sha}'
    ;;
  provider.refs/blob)
    jq -nc --arg provider "mock" --arg path "$PATH_ARG" \
      '{provider: $provider, path: $path, commitId: "1111111111111111111111111111111111111111", content: "fixture blob"}'
    ;;
  provider.merge_request/get)
    jq -nc \
      --arg provider "mock" \
      --argjson id "$MR_ID" \
      --arg source "feature/mock" \
      --arg target "main" \
      '{provider: $provider, id: $id, iid: $id, title: "Mock merge request", state: "OPEN", sourceBranch: $source, targetBranch: $target}'
    ;;
  provider.compare/commits)
    jq -nc \
      --arg provider "mock" \
      --arg base "$BASE_SHA" \
      --arg head "$HEAD_SHA" \
      '{provider: $provider, base: $base, head: $head, commits: [{sha: $head}], files: [{path: "agentmarshal/providers/dispatch.sh", status: "modified"}]}'
    ;;
  provider.pipeline/by-sha)
    case "$SCENARIO" in
      success) pipeline_json "SUCCESS" ;;
      failed) pipeline_json "FAILED" ;;
      error) pipeline_json "ERROR" ;;
      running) pipeline_json "RUNNING" ;;
      *) die "unknown mock scenario: $SCENARIO" ;;
    esac
    ;;
  provider.pipeline/jobs)
    jobs_json
    ;;
  provider.pipeline/wait)
    case "$SCENARIO" in
      success)
        pipeline_json "SUCCESS"
        ;;
      failed)
        pipeline_json "FAILED"
        exit 1
        ;;
      error)
        echo "mock-provider: pipeline ${PIPELINE_ID} transport error" >&2
        exit 1
        ;;
      running)
        pipeline_json "RUNNING"
        echo "mock-provider: timeout waiting for pipeline ${PIPELINE_ID} after ${TIMEOUT}s (poll=${INTERVAL}s)" >&2
        exit 124
        ;;
      *)
        die "unknown mock scenario: $SCENARIO"
        ;;
    esac
    ;;
  *)
    not_impl "$CAPABILITY" "$OPERATION"
    ;;
esac
