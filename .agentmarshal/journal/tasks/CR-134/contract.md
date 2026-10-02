+++
schema = 1
id = "CR-134"
title = "Amendments to ADR-0012, ADR-0013 and ADR-0014: extension forms and language, where the pin lives, the extensions repository, what the gate reads"
scope = [
  "docs/adr/ADR-0012-what-the-tool-does-and-what-it-supplies.md",
  "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
  "docs/adr/ADR-0014-where-things-live.md",
  "docs/overview.md",
  "docs/proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md",
  "docs/proposals/README.md",
  "docs/README.md",
]
acceptance = [
  "ADR-0013 carries, as dated amendments that keep the earlier decision text visible: the three extension forms (manifest only, wrapper, native) distinguished by form and not by the supplied/declared obligations of ADR-0012; the language rule — Python adapters and native shared extensions run as a separate process by AgentMarshal's interpreter, a wrapped product's runtime the one named exception to the PATH rule, declared with a minimum version and reported by doctor; the wrapper directory with two locks and an updated manifest example; the verified version of a wrapped product living in the extension; and the five round-5 points carried from CR-128",
  "ADR-0012 carries, as dated amendments: the separate extensions repository right after 0.5.0 as a named exception to its own criteria with its reason, supplied extensions in the list of optional components, where the compatibility test runs before and after the move, the in-repository `extensions/` directory distinguished from an adopter's `.agentmarshal/extensions/`, adopter code arriving through their outbox with an explicit Apache-2.0 line as a named new use of that channel, the pin's hashes living in the lock, and 'no heartbeats' read as 'in the core'",
  "ADR-0013 decision 6, ADR-0014 and the glossary in docs/overview.md say exactly what the gate reads and from where — in the embedded placement contract, manifests, leak-scan markers and lifecycle state from the base and the journal's records from the caller's working tree; in a sidecar all of them from the journal repository's working tree, unpinned, with the gate advisory except in the findings lane — each statement matching gate.py",
  "ADR-0014's rotation decision points to the local formats of a later decision without a number and its decisions 3, 7 and 8 read as full sentences; proposal 042 and the proposals index no longer say the route for the reporter's code is undecided; the documentation map has a line for ADR-0015",
  "nothing names an unpublished decision by number, no private document or adopter identifier appears, and the full CI sequence passes",
]
+++

# CR-134: amendments to ADR-0012, ADR-0013, ADR-0014

## Context

After ADR-0012..0014 were published the operator decided four more things:
extensions come in forms (a wrapper around another product is its own
class), shared extension code is Python, the verified version of a wrapped
product lives with the extension, and a separate extensions repository
follows 0.5.0. A cross-check of these amendments against the published text
found where each touches an earlier decision and how the gate's reading is
described inaccurately in three places. The `step` stage is not part of this
task: it is its own decision.

## Objective

The published decisions say what the operator decided, accurately.

## Acceptance Criteria

As in the header.

## Non-Goals

- The `step` stage (a separate decision).
- Implementing anything.
