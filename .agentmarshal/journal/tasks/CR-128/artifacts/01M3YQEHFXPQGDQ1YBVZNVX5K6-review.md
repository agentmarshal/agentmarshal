I read the new ADR against ADR-0001, ADR-0007, ADR-0010, ADR-0012, ADR-0009, the proposals it cites, `docs/overview.md`, `docs/self-hosting-workflow.md`, `docs/github-enforcement.md` and the gate code.

Checks that pass: every enumerated point of the approved decision is present (D1–D19, the manifest example, Left open, Consequences, Alternatives), the form matches ADR-0011/ADR-0012, the builds-on and revisits sentences and the proposal-009 answer are there, the local-state decision is referred to without a number, and the doc-map line at `docs/README.md:26` follows the sibling style. The present-behaviour statements hold: the gate as merge authority that decides and never merges (`docs/overview.md:67`, `docs/self-hosting-workflow.md:32`), the gate in CI as a required check (`docs/github-enforcement.md:29`), `complete` running before or after the merge (`docs/self-hosting-workflow.md:43`), base-side manifest reads and the three ADR-0010 manifest effects (`docs/adr/ADR-0010-process-extensions.md:90`, D2/D3/D5), the journal-only lane keyed on `.agentmarshal/journal/` (`src/agentmarshal/journal/gate.py:650`, so D17's "excepted from configuration is reviewed" is a real exception and not a no-op), ADR-0007's acceptance over the blocking findings of the latest non-approving review (`docs/adr/ADR-0007-operator-acceptance.md:54`), the two→three→four manifest readers count, and the states/transitions/events list. ADR-0012 section 6 now names proposal 040's journal write without a shared checkout and routes it to the transaction helper of proposals 019 and 035, which matches those proposals' own dispositions; its process-log clause reads plainly.

I could not execute the CI sequence — the sandbox denied `uv run`. The change is documentation-only and no test reads these files (the `docs/adr/...` strings in `tests/test_brief.py` are synthetic fixtures), so nothing in `validate`/pytest/ruff/mypy is touched.

Four non-blocking points:

`docs/adr/ADR-0013-...:20` states flatly that "ADR-0010 did not refuse an installer", but ADR-0010's Context (`ADR-0010-process-extensions.md:32`) rejects "a plugin platform — installer, sandbox, SDK, registry". The substance the ADR relies on is right (the `extension add/remove` deferral at `ADR-0010:225`), and the sandbox is handled honestly two lines earlier ("the rejected 'a sandbox' alternative is revised"); the installer deserves the same hedge rather than a flat denial of a refusal that is on the page.

`docs/adr/ADR-0012-...:82` now resolves "a pinned version with a package-integrity value — the pin lives in the extension's manifest, a form [ADR-0013] extends beyond ADR-0010's `version` field" to a concrete document, but ADR-0013's manifest form supplies no such field: `version = "1.13.2"` is unchanged from ADR-0010's informational field, and the integrity values live in the lock file the manifest only points at (`ADR-0013:249`).

`docs/adr/ADR-0013-...:239` bumps the manifest to `schema = 2` in the example, while nothing in the decision or the Consequences says the manifest schema moves or what happens to the schema-1 manifests ADR-0010 defines — ADR-0010 itself spelled that transition out for the contract header (`ADR-0010:211`), and `.agentmarshal/extensions/openspec.toml` is a live schema-1 file.

`docs/adr/ADR-0013-...:139` says a personal extension writes "only to the process log and to its own state under `.git/agentmarshal/`", which does not hold for the user scope the table one page up places at `~/.config/agentmarshal/extensions/` and `~/.local/share/agentmarshal/deps/` (`ADR-0013:121`).

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "37a79a380cf33add0b9bda1345f6556c2e6838a3",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "adr0010-installer-refusal-claim-overstated",
    "adr0012-version-pin-points-at-absent-manifest-field",
    "manifest-schema-2-bump-unexplained",
    "personal-state-path-excludes-user-scope"
  ]
}
AGENTMARSHAL_VERDICT_END
