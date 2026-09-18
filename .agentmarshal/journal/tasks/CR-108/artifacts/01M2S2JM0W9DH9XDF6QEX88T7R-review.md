The diff meets all six acceptance criteria and every changed path is inside the contract's scope, so the verdict is **approved**. There are two non-blocking findings.

**What was checked against the snapshot**
- **`docs/README.md`:** it covers every file under `docs/`: 11 ADRs, 23 proposals plus `proposals/README.md`, the incident, the template JSON, and all top-level guides. `README.md` links to it.
- **PR template:** each item matches `CONTRIBUTING.md`: the `CR-NNN` task, the declared scope, append-only evidence with the contract read from the base side, `AGENTMARSHAL_ACTOR`, English public artefacts, the same six-command check sequence CI runs, and Apache-2.0.
- **`config.yml`:** the link uses the correct repository URL from `pyproject.toml` and the right default branch (`master`, as in the governance workflow).
- **No links to features that aren't enabled:** there is no Discussions link and no invented support channel.
- **`SECURITY.md`:** it treats a review written under a made-up reviewer identity as out of scope. This reads "forging … undetected" more narrowly than the criterion's wording, but it matches the trust boundary the README documents: the gate compares identity strings and does not authenticate them. Calling it a vulnerability would contradict the README, so I don't count it as a defect.

**Advisory findings**
- **`CR-108-A1`:** In `.github/ISSUE_TEMPLATE/finding.yml`, the language policy is only in the top-level `description`, which GitHub shows in the template chooser, not on the form itself. The form's opening markdown block doesn't mention language, while `gate-refusal.yml` does. Repeating the policy in that block would keep it in front of someone filling in the form.
- **`CR-108-A2`:** In `.github/pull_request_template.md`, the link `../CONTRIBUTING.md#this-repository-governs-itself` is relative. In a pull-request body it resolves against the PR page's URL (`/owner/repo/pull/N` becomes `/owner/repo/CONTRIBUTING.md`), which should return a 404. `config.yml` already uses an absolute `blob/master` URL, and this link should too.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "8d66a6b46d7f287819b0f7babfafbdd3170108b3", "verdict": "approved", "findings": [], "advisory_findings": ["CR-108-A1", "CR-108-A2"]}
AGENTMARSHAL_VERDICT_END
