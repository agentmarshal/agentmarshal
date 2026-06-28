#!/usr/bin/env bash
set -euo pipefail

for cmd in bash curl jq; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "gitflic-provider doctor: required command not found: $cmd" >&2; exit 1; }
done

present="no"
for var in GITFLIC_API_TOKEN AGENTMARSHAL_GITFLIC_API_TOKEN AGENTOPS_GITFLIC_API_TOKEN CI_JOB_TOKEN; do
  if [[ -n "${!var:-}" ]]; then
    present="yes"
    break
  fi
done
[[ "$present" == yes ]] || {
  echo "gitflic-provider doctor: none of declared secret env vars found" >&2
  exit 1
}

echo "gitflic-provider doctor: ok"
