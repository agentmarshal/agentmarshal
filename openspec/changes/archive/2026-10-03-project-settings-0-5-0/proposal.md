## Why

ADR-0022 section 6 adds three `project.json` keys to the 0.5.0 model:
`review.finding_classes`, the finding-class vocabulary of ADR-0016 decision
3; `review.changes_required_threshold`, the count flag of ADR-0016 decision
4; and `contract.require_agreement`, ADR-0018's switch that makes a contract
need a recorded agreement. The tasks that read them — the review launcher,
`status`, the gate — follow this one. Without a single reader each consumer
would re-derive the defaults on its own, and a mistyped value in a
hand-edited `project.json` would silently revert to a default nobody chose.

## What Changes

One module reads the three settings and returns a typed result. An absent
key — or an absent section — yields the documented default: the seven
finding classes, a threshold of 3, an agreement requirement of false. A
present but malformed value raises an error naming the key and what it
expects, never the default.

`agentmarshal doctor` gains one check per key, so each malformed value is
reported by name with what it expected. A project that declares none of the
keys passes exactly as before.

## Capabilities

- new: `project-settings`

## Impact

The launcher, `status` and the gate get one function to call when their
tasks land. `init` writes none of the keys, and a 0.4.x installation
ignores them, both unchanged.
