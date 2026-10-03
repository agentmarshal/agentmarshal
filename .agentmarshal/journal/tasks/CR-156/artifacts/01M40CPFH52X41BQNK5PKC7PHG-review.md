## Review of CR-156 — `outbox send` / `outbox status`

I read the whole of `src/agentmarshal/outbox.py`, the archived change (proposal, design, delta, tasks), the archived `openspec/specs/outbox/spec.md`, `tests/test_outbox.py`, and the surrounding `project.py` / `cli.py` invariants the design leans on. I could not execute anything in this sandbox (no venv, and shell/script execution was declined), so everything below is static reasoning plus the coordinator's CI statement.

**Acceptance criteria**

1. **Change artifacts and archival** — met. `openspec/changes/` holds only `archive/`; the change sits at `openspec/changes/archive/2026-10-03-outbox-send-and-status/` with `proposal.md`, `design.md`, `tasks.md` and `specs/outbox/spec.md`. The MODIFIED header `### Requirement: \`outbox check\` scans what would be sent and refuses by exit status` is byte-identical to the one already in `openspec/specs/outbox/spec.md`, the two new requirements are ADDED, and the archived spec's requirement bodies and scenario *order* match the delta exactly — consistent with `openspec archive` output rather than a hand edit (AGENTS.md's rule). Every one of the 34 delta scenarios has a test whose docstring names it; I cross-checked the scenario list against the docstrings at `tests/test_outbox.py:110`–`1250`.
2. **`send`** — met. `_run_send` (`outbox.py:655`) runs `_check(pin=True)` literally and refuses on any non-zero; refuses a draftless outbox; refuses on anything staged outside `.agentmarshal/upstream/` (both halves of a rename, via `--name-status -z`); stages with `git add --force -- .agentmarshal/upstream`; refuses an empty batch; verifies staged blobs against the pins; makes one `git commit -m` naming the files and prints `rev-parse HEAD`. No network, no push. The blob pinning via `git hash-object --stdin --path=` is the right call — it applies the same clean/EOL filters `add` does, so the id genuinely is the one staging writes, and there is no second read for an edit to slip through. The index restore (`_restore_outbox_index`, `outbox.py:590`) is correct in the cases I traced: additions force-removed, prior records replayed via `--index-info`; deletions staged by `add` are restored by the replay; empty records correctly skip the replay; nothing outside the outbox is ever in either list. Avoiding any hard-coded null object id is the reason the sha256 test passes, and that reasoning holds.
3. **`status --index`** — met. sha256 lowercase hex over the file's bytes, symlinks never followed, `Source:` parsed in both the bare and `**Source:** \`…\`` forms (I checked the real published headers in `docs/proposals/*.md` — the regex at `outbox.py:764` matches them), entries keyed by digest with line numbers retained, unclaimed entries listed once, missing/unreadable index refused, non-regular and unreadable entries named and exit non-zero.
4. **Non-UTF-8 names** — met. `_shown_name` (`outbox.py:182`) is applied before masking everywhere a name reaches output in `check`, `send` and `status`, and the raw surrogate-carrying name is kept only where it must be (the `is_draft` README comparison, `os.fsencode` for the pin key and for subprocess args). Note the escaped form cannot collide into the outbox prefix, so the "staged outside" guard cannot be fooled by an escaped name.
5. **Registration and CI** — met. `cli.py` is untouched; it still only calls `outbox.register` (`cli.py:348`) and `outbox.run` (`cli.py:1236`). CI per the coordinator's note.

Two non-blocking observations follow.

The staged-outside-the-outbox guard at `src/agentmarshal/outbox.py:570` reads the staged set with the *porcelain* `git diff --cached`, which honours `diff.ignoreSubmodules` and `submodule.<name>.ignore`; with either set to `all`, a staged submodule pointer change is invisible to the guard, and the subsequent `git commit` (which commits the whole index) would carry it into the findings batch — exactly the "another commit's work never rides along in the batch" property the requirement states. Plumbing (`git diff-index --cached`) or an explicit `--ignore-submodules=none` would close it. I could not run git here to demonstrate it, so I mark this unverified; it is also config-dependent, which is why it is advisory rather than blocking.

`design.md:139` says a missing or unreadable index "is refused with a message before the outbox is touched", but `_run_status` (`src/agentmarshal/outbox.py:767`) calls `_locate` — which stats `.agentmarshal/upstream/` and refuses when it is absent — before it ever reads `--index`; in a project with no outbox the operator gets the "no outbox" message even when their index path is also wrong. Both refusals are spec-conformant, so this is a design-document inaccuracy, not a behaviour defect.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b9649ebee1fe07791cb0c85d9cda2dc097088700",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "advisory-staged-guard-uses-porcelain-diff-submodules-unverified",
    "advisory-design-claims-index-refusal-precedes-outbox-lookup"
  ]
}
AGENTMARSHAL_VERDICT_END
