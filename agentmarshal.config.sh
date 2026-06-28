#!/usr/bin/env bash
# Public sanitized default config used by legacy compatibility tests.
# Hosts should configure runtime through .agentmarshal/project.json and runtime.conf.

AGENTMARSHAL_REPO_NAME="${AGENTMARSHAL_REPO_NAME:-agentmarshal-host}"
AGENTMARSHAL_DEFAULT_BRANCH="${AGENTMARSHAL_DEFAULT_BRANCH:-master}"

declare -A AGENTMARSHAL_ROLE_EMAIL=(
  [lead]="lead-agent@agent.example.invalid"
  [frontend]="fe-agent@agent.example.invalid"
  [backend]="be-agent@agent.example.invalid"
  [qa]="qa-agent@agent.example.invalid"
  [release]="ops-agent@agent.example.invalid"
)

AGENTMARSHAL_GITFLIC_OWNER="${GITFLIC_OWNER:-agentmarshal}"
AGENTMARSHAL_GITFLIC_PROJECT="${GITFLIC_PROJECT:-agentmarshal-host}"
