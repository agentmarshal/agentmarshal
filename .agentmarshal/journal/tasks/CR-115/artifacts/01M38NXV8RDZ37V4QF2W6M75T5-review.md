I reviewed the release diff against CR-115's contract, checked every CHANGELOG claim against the merged code and docs, and looked at what the 0.4.1 artifact will actually carry.

**What checks out**

- CHANGELOG has a `## 0.4.1 — 2026-09-24` section (today), with one entry per task landed since v0.4.0 — CR-114, CR-112, CR-113 — each naming its task. The CR-114 entry tells an affected installation what to do ("this release reads it again") and links UPGRADING.md. The 0.4.0 section is untouched: the diff only inserts above it.
- The technical claims are true of merged code, not of intent: `_FORGEABLE_CATEGORIES = {"Cc","Cs","Zl","Zp"}` plus the twelve bidi controls at `src/agentmarshal/journal/records.py:498,508`, and the "one predicate" claim holds — `forges_rendered_text` is called from `records.py:543`, `contracts.py:64` and `validate.py:72` (the artifact reference). CR-112's claim matches `.github/workflows/release.yml:41-47`; CR-113's matches proposal 024's published disposition (`docs/proposals/README.md:81`) and `docs/quickstart.md:446-451`, and 018's deferral is recorded at `docs/proposals/README.md:108`.
- UPGRADING.md is now headed `## 0.4.0 → 0.4.1` with the refusal as a subsection, states nothing else requires action, and the dangling "upgrade to the release that carries CR-114" is now a named version.
- Version is 0.4.1 in `pyproject.toml:3`, `src/agentmarshal/__init__.py:3`, `uv.lock:11`, with `tests/test_smoke.py:48` updated; `--version` prints `__version__` (`src/agentmarshal/cli.py:88`). No unpublished release, task or document is named.

I could not run the CI sequence here: `uv` is absent from this environment and the snapshot is not a git repo, so the fifth criterion — full CI plus the read-only `validate` over the reporting adopter's journal — is unverified by me and must be evidenced in the completion record.

**Findings**

`readme-shipped-to-pypi-still-pins-0-4-0` — `pyproject.toml:5` makes README.md the PyPI long description, and `README.md:73-77` says "Install the published release: `pip install agentmarshal==0.4.0`", with `README.md:57` still opening "Version 0.4.0 ships…". The 0.4.1 project page will therefore instruct every new installer to pin the exact release whose `validate` refuses their journal — which is what this release exists to route people away from. README.md is not in CR-115's scope, unlike CR-109 (release 0.4.0), whose scope carried `README.md` and `docs/` and whose fourth criterion required every "current release" statement to name the version. Fixing this needs a scope amendment; it should be settled before the tag is pushed rather than left to the post-tag task.

`docs-install-pins-0-4-0` (advisory) — the same pin sits in `docs/quickstart.md:26` and `docs/sidecar.md:75`. The quickstart's is defensible, since `docs/quickstart.md:6` says the transcript was recorded against a 0.4.0 wheel and `tests/test_quickstart.py` checks it; `docs/sidecar.md:75` has no such reason and is plain staleness.

`contributing-example-names-0-5-0-as-next` (advisory) — `CONTRIBUTING.md:124` illustrates the versioning rule with "after 0.4.0 it reads `0.5.0.dev0`", which the release now contradicts: the release after 0.4.0 is 0.4.1, so the example names a next release that is not the one being made. Out of scope here, but it will mislead whoever performs the post-tag `.dev0` restoration.

`upgrading-paragraph-not-reflowed` (advisory) — `UPGRADING.md:11-13` leaves a 51-character line ("upgrade to 0.4.1; it reads that record again.** The") mid-paragraph where the file otherwise wraps near 79; the shortened version string was substituted without reflowing.

`changelog-refused-write-sentence-unclear` (advisory) — `CHANGELOG.md:28-29` ends with "The verdict a refused write produced is unaffected: a refused write wrote nothing." UPGRADING.md:39 states the same point clearly ("Records written on 0.4.0 are unaffected"); the changelog's phrasing attributes a verdict to a write that, by its own clause, produced nothing.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "a0496d896f730b8430dd0edbc2e06de87f2884fc", "verdict": "changes_required", "findings": ["readme-shipped-to-pypi-still-pins-0-4-0"], "advisory_findings": ["docs-install-pins-0-4-0", "contributing-example-names-0-5-0-as-next", "upgrading-paragraph-not-reflowed", "changelog-refused-write-sentence-unclear"]}
AGENTMARSHAL_VERDICT_END
