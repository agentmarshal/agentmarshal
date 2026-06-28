# ADR-0001: AI Team Workflow

Status: Accepted
Decision owner: AgentMarshal maintainers
Date: 2026-06-28

## Context

AgentMarshal coordinates AI-agent work through Git-backed task contracts,
review gates and evidence artifacts.

## Decision

AgentMarshal keeps framework-level roles, profiles, review policy and evidence
contracts in the framework repository. Host projects keep host-specific tasks,
journals, secrets, integrations and operational history in host-owned paths.

## Consequences

Public documentation can describe the framework contract without publishing
private host history.
