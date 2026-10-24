I reviewed the diff against the contract, reading `outbox.py`, the new and existing tests, the archived change, the live spec, ADR-0020, the leak-scan internals (`capture.py`, `display.py`, `records.py`) and the threat model. Python/`uv` execution was refused in this sandbox, so I verified by reading and by file-level shell checks; CI status I take from your note.

## Acceptance criteria

**AC1 (change artifacts, scenario tests, archive) — met.** `openspec/changes/` now holds only `archive/`, and `openspec/changes/archive/2026-10-24-outbox-skips-sent/` carries `proposal.md`, `design.md`, `tasks.md` and `specs/outbox/spec.md`. The live spec has 7 `### Requirement:` headings, each once. The MODIFIED requirement restates `### Requirement: \`outbox check\` names what each draft lacks` with its heading and all five scenarios, and its text matches `openspec/specs/outbox/spec.md:56-89` word for word. Each of the 13 new scenarios has a test whose docstring names it: `test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft`, `test_check_index_skips_a_file_a_source_line_claims`, `test_send_index_skips_a_file_a_source_line_claims`, `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`, `test_the_sent_manifest_is_not_a_draft`, `test_an_unreadable_sent_manifest_refuses_the_check`, `test_send_refuses_when_every_file_is_already_sent`, `test_a_manifest_line_in_another_shape_lists_nothing`, `test_a_file_whose_name_could_add_a_line_to_the_manifest_is_refused`, `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends`, `test_a_refused_send_leaves_the_manifest_as_it_was` (plus the absent-manifest variant) and `test_the_manifests_next_content_goes_through_the_leak_scan`.

**AC2 (skip what is already sent) — met.** `outbox.py:510-534` reads `SENT` strictly (`_SENT_LINE`, `outbox.py:62`) and folds in `_index_claims`; the skip is `outbox.py:587-589`; `skipped as sent: <n>` is `outbox.py:659-660`; `--index` is registered on both commands at `outbox.py:116-128`. Demonstrated by the three skip tests above and `test_check_index_refuses_an_unreadable_index`.

**AC3 (send records the batch; changed-after-sending) — met.** `_manifest_next` (`outbox.py:464-478`), the pinned write (`outbox.py:645-658`, `886-892`) and the `changed after sending` note (`outbox.py:590-591`) are demonstrated by `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends` and `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`.

**AC4 — met except its last clause.** Non-regular entries still refuse on one line (`outbox.py:561-567`, `test_an_entry_that_is_not_a_regular_file_is_named_as_not_checked`), the README stays skipped (`test_the_readme_init_writes_is_not_a_draft`); the "existing outbox tests demonstrate unchanged" clause is CR-228-A1 below.

**AC5 — leak-scan coverage met** (`test_a_skipped_file_still_goes_through_the_leak_scan`, `test_the_manifests_next_content_goes_through_the_leak_scan`); **"every value shown is escaped as today" is where CR-228-F1 lands**, and `status`'s shown names did change (`_shown_name` → `_display_name`, `outbox.py:1017`) against "no other command changes".

## Findings

**CR-228-F1 (blocking, security) — the diff masks an *escaped* name, so an outbox file whose name carries a secret beside a control character now has that secret printed instead of described.** `_name_hits` (`outbox.py:418`), `_draft_hits` (`outbox.py:430`), the check's per-entry prints (`outbox.py:560`, `566`, `631`) and `_display_name` (`outbox.py:232`, used by `status` at `1017`, `_staged_paths` at `739-746` and `_batch_mismatch` at `812`) all now compute `safe_path(escape_for_display(name), markers)` — escape first, mask second. `escape_for_display` (`display.py:14-24`) renders a tab as `\t`, `\x07` as `\u0007`, i.e. it inserts word characters where a control character was, and `safe_path`'s signatures (`capture.py:275-289`) are boundary- and whitespace-anchored. A regular outbox file named `my\x07ghp_<36 chars>.md` was masked to `my\x07<github-token>.md` before this diff (`\bghp_` had a non-word char in front); after it the printed name is `my\u0007ghp_<36 chars>.md`, because `7` is a word character and the `\b` no longer holds — so the token is printed both on the entry's own line and inside the "possible leaks" line. Same for `authorization: bearer\t<token>`: the escape breaks the `\s+` after `bearer`, and the whole span goes out unmasked. That contradicts the unmodified requirement at `openspec/specs/outbox/spec.md:100-109` ("The matched text, a marker's value, and a name that itself carries a secret SHALL appear nowhere in the output") and its scenario at `:124-129`; the same order also defeats a configured marker that itself contains a control character. The existing masking tests (`tests/test_outbox.py:346-363`, `628-648`) use control-free names, so nothing catches it — the `\xNN` escapes in the latter come from `_shown_name`, not from `escape_for_display`. Masking before escaping (`escape_for_display(safe_path(name, markers))`) keeps both properties, since the replacement text holds no control characters.

**CR-228-A1 (advisory, claim-accuracy) — AC4's "the existing outbox tests demonstrate unchanged" does not hold, and the diff does not record it as a departure.** `tests/test_outbox.py:934-947` had its setup rewritten: the first batch is now committed by hand because, after a real `send`, the renamed draft's bytes are unchanged, its digest is in `SENT`, so it is skipped and `send` refuses `no drafts to send` — which the new `test_send_refuses_a_rename_of_an_already_sent_draft` (`tests/test_outbox.py:1593`) asserts as the intended behavior. And "no sent manifest and no `--index` behaves exactly as today" holds only for the draft judgement: `test_the_manifests_next_content_goes_through_the_leak_scan` (`tests/test_outbox.py:1688`) builds an outbox with no manifest at all and shows `send` refusing, where the same outbox passed before (the name `authorization: bearer` alone matches nothing — the signature needs a non-space after `bearer`). `tasks.md` 3.3 records the rename consequence, but neither `design.md` nor the delta notes it against AC4's wording.

**CR-228-A2 (advisory, scope) — `send` now writes and commits a `SENT` file into an outbox whose own README says it holds one file per finding, and nothing user-facing explains it.** `_OUTBOX_README` (`src/agentmarshal/project.py:232-235`): "Findings about **AgentMarshal itself** go here — one file per finding". `CHANGELOG.md:150-157` has a section for the outbox group, and `docs/quickstart.md` documents the commands; none mentions the manifest or the new `--index` on `check`/`send`. Those paths are outside the contract's scope, so the right move was a named departure/follow-up rather than silence — an adopter's next `send` commits a file they have no documentation for.

**CR-228-A3 (advisory, correctness, unconfirmed) — a `SENT` checked out with CRLF line endings lists nothing, silently restoring the problem the change fixes.** `_SENT_LINE` (`outbox.py:62`) anchors with `$` and the name is then rejected by `forges_rendered_text` if it ends in `\r` (`records.py:1830`, `Cc`), so every line of a CRLF manifest "lists nothing" and every previously sent file becomes a draft again. `send` itself writes LF, so this bites only after a checkout that converts line endings; I could not check whether that applies to any adopter's git configuration here, hence unconfirmed. The strict parse is what the delta specifies, so this is a design note, not a deviation.

No defect found in the pin/restore paths: the `SENT` pin after the loop overwrites the in-loop pin of the old bytes (`outbox.py:645-658`), `_batch_mismatch` covers the manifest like every path, and the refusal path restores the index and then the manifest's bytes or removes it (`outbox.py:921-935`), which `test_a_refused_send_leaves_the_manifest_as_it_was` and `test_a_refused_send_removes_a_manifest_it_wrote` demonstrate. The `batch == [SENT]` guard (`outbox.py:903`) keeps `test_send_refuses_an_empty_batch` passing on its original path.

Коротко по-русски: одна блокирующая находка — порядок «сначала escape, потом маскирование» в `outbox.py` ломает маскировку имени файла, в котором секрет стоит рядом с control-символом (лечится обратным порядком); остальное — три advisory (формулировка AC4, недокументированный `SENT`, строгий парсинг при CRLF). Реализация в остальном соответствует контракту.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "e4c8aa6c0d85435b6b4d1e1ae4b14075b1ba6f98",
  "verdict": "changes_required",
  "findings": ["CR-228-F1"],
  "advisory_findings": ["CR-228-A1", "CR-228-A2", "CR-228-A3"],
  "classes": {
    "CR-228-F1": "security",
    "CR-228-A1": "claim-accuracy",
    "CR-228-A2": "scope",
    "CR-228-A3": "correctness"
  },
  "evidence": {
    "CR-228-F1": "src/agentmarshal/outbox.py:418 and :430 compute safe_path(escape_for_display(name), markers); the check prints safe_path(display, markers) at :566 and :631; display.py:14-24 renders \\t as backslash-t and \\x07 as backslash-u0007, inserting word characters, while capture.py:275-289 anchors github-token on \\bghp_[A-Za-z0-9]{36}\\b and authorization-header on authorization:\\s*(?:bearer|basic)\\s+\\S+, so a name 'my\\x07ghp_<36>.md' masked to 'my\\x07<github-token>.md' before the diff now prints the token; the requirement it breaks is openspec/specs/outbox/spec.md:100-109 with the scenario at :124-129; the existing masking tests tests/test_outbox.py:346-363 and :628-648 use control-free names",
    "CR-228-A1": "tests/test_outbox.py:934-947 (setup changed from `main([\"outbox\",\"send\"])` to a hand commit, docstring states why), tests/test_outbox.py:1593-1620 (test_send_refuses_a_rename_of_an_already_sent_draft), tests/test_outbox.py:1688-1709 (no-manifest outbox now refuses); contract AC4 text 'an outbox with no sent manifest and no --index behaves exactly as today, which the existing outbox tests demonstrate unchanged'",
    "CR-228-A2": "src/agentmarshal/project.py:232-235 ('one file per finding'); CHANGELOG.md:150-157 outbox section with no manifest entry; grep -rln outbox docs/ README.md CONTRIBUTING.md CHANGELOG.md shows docs/quickstart.md documents the group and was not touched by the diff",
    "CR-228-A3": "src/agentmarshal/outbox.py:62 (_SENT_LINE anchored with $), :523-527 (lines split on \\n, name rejected by forges_rendered_text), src/agentmarshal/journal/records.py:1830 (Cc includes \\r)"
  },
  "verification": {
    "executed": [
      {"what": "ls openspec/changes/ and ls -R of the archived change", "result": "only archive/ remains; 2026-10-24-outbox-skips-sent holds proposal.md, design.md, tasks.md and specs/outbox/spec.md"},
      {"what": "grep -c '^### Requirement:' openspec/specs/outbox/spec.md with the heading list", "result": "7 headings, each requirement exactly once, including the two ADDED ones"},
      {"what": "grep '^def test_' tests/test_outbox.py and read of the new tests' docstrings", "result": "each of the 13 new scenarios has a test whose docstring names it; file is 1709 lines"},
      {"what": "grep -n outbox docs/threat-model.md CHANGELOG.md CONTRIBUTING.md docs/adr/ADR-0020*", "result": "threat model's 'A non-regular file in the outbox is named as not checked' still holds; no changelog or README line for the manifest"}
    ],
    "read": [
      "src/agentmarshal/outbox.py (whole file)",
      "tests/test_outbox.py (lines 1-200, 340-410, 628-662, 700-1019, and the added block 1257-1709 via the diff)",
      "openspec/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-24-outbox-skips-sent/specs/outbox/spec.md, design.md, proposal.md, tasks.md (via the diff)",
      "src/agentmarshal/journal/display.py",
      "src/agentmarshal/journal/records.py:1830-1880",
      "src/agentmarshal/journal/capture.py:260-335, 440-470, 771-806",
      "src/agentmarshal/journal/gate.py:647-692",
      "src/agentmarshal/project.py:228-290",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/threat-model.md:155-205",
      "CONTRIBUTING.md:13-25",
      "AGENTS.md"
    ],
    "not_run": [
      {"what": "uv sync --locked, agentmarshal validate, pytest, ruff check, ruff format --check, mypy, and any Python at all", "why": "the snapshot is not a git repository and python/uv invocations were refused by the sandbox; CI status taken from the coordinator's note on e4c8aa6c0d85435b6b4d1e1ae4b14075b1ba6f98 and not independently checked"},
      {"what": "whether the archive was produced by `openspec archive` rather than by hand", "why": "no git history in the snapshot; the date-prefixed directory and the byte-identical requirement text in openspec/specs/outbox/spec.md are consistent with the command"},
      {"what": "the CRLF premise of CR-228-A3", "why": "depends on an adopter's git line-ending configuration, which is outside this snapshot"}
    ]
  }
}
AGENTMARSHAL_VERDICT_END
