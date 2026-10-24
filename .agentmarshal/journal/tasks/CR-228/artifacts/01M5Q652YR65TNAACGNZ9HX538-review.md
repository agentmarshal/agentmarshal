Среда не даёт запускать python/uv (нет `uv`, вызовы интерпретатора не разрешены), поэтому review чисто читающий: я прочёл `src/agentmarshal/outbox.py` целиком, `tests/test_outbox.py`, `openspec/specs/outbox/spec.md`, delta изменения, `docs/adr/ADR-0020-the-outbox-command-group.md`, `journal/display.py`, `journal/records.py` (`forges_rendered_text`), `journal/capture.py` (`safe_path`) и `project.py` (scaffold README). Результат CI беру из записки координатора.

## Где diff выполняет acceptance criteria

**AC1** (change + delta + archive). Все четыре файла изменения лежат под `openspec/changes/archive/2026-10-25-outbox-skips-sent/`; MODIFIED-требование в delta совпадает с `openspec/specs/outbox/spec.md:56-66` текстом и всеми пятью сценариями (`a freshly scaffolded draft…`, `a draft that dropped a field…`, `a field emptied by hand…`, `the README init writes…`, `check refuses when there is no outbox`), заголовок — байт в байт; в живом spec каждое requirement встречается ровно один раз. Каждый новый сценарий демонстрируется тестом, чей docstring его называет: `test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft`, `test_check_index_skips_a_file_a_source_line_claims`, `test_send_index_skips_a_file_a_source_line_claims`, `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`, `test_the_sent_manifest_is_not_a_draft`, `test_an_unreadable_sent_manifest_refuses_the_check`, `test_send_refuses_when_every_file_is_already_sent`, `test_send_commits_a_rename_of_a_file_already_sent`, три теста на `a manifest line that does not parse`, `test_a_file_whose_name_could_add_a_line_to_the_manifest_is_refused`, `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends`, `test_a_refused_send_leaves_the_manifest_as_it_was` (+ вариант `…removes_a_manifest_it_wrote`), `test_the_manifests_next_content_goes_through_the_leak_scan`. Единственный пробел по AC1 — F1 ниже.

**AC2** (skip по manifest и по `--index`, строка `skipped as sent: <n>`). Выполнено: `outbox.py:630-632` снимает `is_draft` по digest из `sent_digests`, который собирается и из `SENT` (`outbox.py:551-556`), и из `_index_claims` (`outbox.py:566-572`); счётчик печатается на `outbox.py:707-708`. Демонстрируют `test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft` (`skipped as sent: 2`, `1 draft(s) checked`), `test_check_index_skips_a_file_a_source_line_claims`, `test_send_index_skips_a_file_a_source_line_claims`.

**AC3** (manifest обновляется в том же batch commit; изменившийся файл проверяется и помечается). Выполнено: `_manifest_next` считает содержимое в check, пин берётся с него один раз (`outbox.py:693-700`), `send` пишет ровно эти байты перед `add` (`outbox.py:950-956`). Демонстрируют `test_send_records_the_batch_in_the_sent_manifest` (далее `check` даёт `skipped as sent: 1`), `test_a_manifest_gained_across_batches_appends`, `test_the_sent_manifest_is_pinned_once_with_the_content_send_writes`, а «changed after sending» — `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`.

**AC4** (non-regular entry одной строкой; README как раньше; outbox без manifest и без `--index` — как сегодня). Выполнено для `check`: `outbox.py:600-606` не изменилось по сути, README исключён на `outbox.py:612`. Демонстрируют `test_an_entry_that_is_not_a_regular_file_is_named_as_not_checked`, `test_the_readme_init_writes_is_not_a_draft`, `test_the_sent_manifest_is_not_a_draft` и весь прежний send-набор (`test_send_refuses_an_empty_batch`, `test_send_refuses_when_the_outbox_holds_no_drafts`, `test_a_failed_commit_leaves_the_index_as_send_found_it`, `test_a_draft_renamed_since_the_last_batch_is_sent_as_a_rename`) — в diff из старых тестов тронут только docstring на строке 200. Оговорка: `send` теперь всегда создаёт и коммитит `SENT`, то есть «ровно как сегодня» держится для `check`, а для `send` AC3 это прямо требует.

**AC5** (escaping, leak scan по всем staged файлам, остальные команды, CI). Escaping — `test_a_secret_beside_a_control_character_in_a_name_is_masked` (masking по сырому имени, затем escape: `lead\u0007<github-token>.md`) и прежний `test_a_file_name_that_is_not_utf8_is_named_escaped_and_still_masked`. Покрытие scan — `test_a_skipped_file_still_goes_through_the_leak_scan` (skipped файл даёт `private-marker #1`) и `test_the_manifests_next_content_goes_through_the_leak_scan` (hit на `SENT`, `send` ничего не стейджит). CI я здесь не прогонял. По «no other command changes» — F5.

## Findings

**F1 — blocking.** В `openspec/specs/outbox/spec.md:178` требование «`outbox send` commits the checked batch» по-прежнему говорит: `it SHALL refuse, saying there are no drafts to send, when the outbox holds no finding draft`. Новое ADDED-требование на строке 366 того же файла для того же входа говорит обратное: `When send finds no new draft it SHALL still commit a change the outbox holds to a file already sent — a rename, a move inside the outbox`. Код следует второму (`src/agentmarshal/outbox.py:966-978`: при пустом `result.drafts` коммит делается, если есть хоть одна staged-запись со `status != "A"` и `names != [sent_spec]`), и это подтверждает `test_send_commits_a_rename_of_a_file_already_sent`. Delta провела как MODIFIED только check-требование, поэтому в опубликованной capability-спеке теперь два противоположных SHALL про одну и ту же ситуацию — ровно тот случай, который openspec-дисциплина этого репозитория и существует ловить. Чинится только новым change с MODIFIED на send-требование (править `openspec/specs/` руками нельзя).

**F2 — advisory.** `src/agentmarshal/outbox.py:486` — docstring `_manifest_next` утверждает `The rebuilt lines are byte-identical to what was read`. Это не так для manifest, у которого последняя строка без завершающего `\n`: `_SENT_LINE` такую строку принимает (`outbox.py:64`, split по `"\n"` на 547-549), а сборка на 495 всегда дописывает `\n`. Следствие: `manifest_new != manifest_old` при полностью неизменном содержимом, `send` переписывает файл и пин берётся не с найденных байт. Вреда нет (без drafts и без изменения в outbox send всё равно откатывает и отказывает), но заявление в docstring ложное.

**F3 — advisory.** Outbox README, который пишет `init` (`src/agentmarshal/project.py:232-277`), всё ещё говорит `one file per finding` и нигде не упоминает `SENT`. Adopter после первого `send` находит в outbox файл, который создала и ведёт сама tool, без единой строки объяснения — delta фиксирует «bookkeeping the outbox keeps beside the findings, not a finding itself» только в спеке. `project.py` вне scope контракта, так что это departure, о котором нужно сообщить, а не править.

**F4 — advisory.** Отказ по неразобранной строке manifest (`src/agentmarshal/outbox.py:560-563`) печатает только `SENT: line <n> does not parse` — без причины. design.md (decision 2) оправдывает строгость тем, что опечатка «restores the very refusal digest 045 reported unless it is diagnosed», а самая вероятная причина, которая валит сразу все строки — checkout с CRLF, что собственный `test_a_manifest_line_ending_in_a_carriage_return_refuses_the_check` и кодирует как намеренный отказ, — оставляет оператора с неотправляемым outbox и без подсказки. Диагноз сводится к номеру строки; спека большего не требует, но обещание design.md не выполнено.

**F5 — advisory.** `src/agentmarshal/outbox.py:1094` — `_run_status` теперь рендерит имена через `_printable`, то есть `outbox status` display-escape'ит control-символы в именах там, где раньше печатал их сырыми (прежний код: `safe_path(_shown_name(entry.name), markers)`). То же для сообщений об ошибке чтения outbox и index. Это изменение поведения команды, про которую последний acceptance criterion говорит `no other command changes`, и delta его не упоминает; requirement `outbox status` в спеке тоже не обновлён. Направление безопасное (escape сверх masking), но изменение есть.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "fc66a5b2e7f55a0b8fb2d51198a1eae53651d52f",
  "verdict": "changes_required",
  "findings": ["F1"],
  "advisory_findings": ["F2", "F3", "F4", "F5"],
  "classes": {
    "F1": "contract-mismatch",
    "F2": "claim-accuracy",
    "F3": "scope",
    "F4": "style",
    "F5": "scope"
  },
  "verification": {
    "read": [
      "src/agentmarshal/outbox.py",
      "tests/test_outbox.py",
      "openspec/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-25-outbox-skips-sent/proposal.md",
      "openspec/changes/archive/2026-10-25-outbox-skips-sent/design.md",
      "openspec/changes/archive/2026-10-25-outbox-skips-sent/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-25-outbox-skips-sent/tasks.md",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "src/agentmarshal/journal/display.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/capture.py",
      "src/agentmarshal/project.py",
      "CHANGELOG.md",
      "AGENTS.md"
    ],
    "executed": [
      {"what": "grep -n '^### Requirement:|^#### Scenario:' openspec/specs/outbox/spec.md", "result": "each requirement appears exactly once; the MODIFIED check requirement keeps its five scenarios at lines 68-89"},
      {"what": "sed -n '174,182p;352,368p' openspec/specs/outbox/spec.md", "result": "line 178 'SHALL refuse, saying there are no drafts to send, when the outbox holds no finding draft' vs line 366 'When send finds no new draft it SHALL still commit a change the outbox holds to a file already sent'"},
      {"what": "grep -rn 'outbox check|outbox send|outbox status' over docs, CONTRIBUTING.md, README.md, templates, CHANGELOG.md", "result": "no adopter-facing document mentions SENT or --index; the outbox README lives in src/agentmarshal/project.py:232"}
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "uv is not installed in this environment and interpreter invocations were not permitted in this non-interactive session; the coordinator's note that the sequence passed on this commit is taken as given"},
      {"what": "openspec archive / openspec validate", "why": "the openspec CLI could not be run for the same reason; the archive's shape was checked by reading the files"}
    ]
  },
  "evidence": {
    "F1": "openspec/specs/outbox/spec.md:178 ('it SHALL refuse, saying there are no drafts to send, when the outbox holds no finding draft') contradicts openspec/specs/outbox/spec.md:366 ('When send finds no new draft it SHALL still commit a change the outbox holds to a file already sent'); the code follows the latter at src/agentmarshal/outbox.py:966-978 and tests/test_outbox.py:1599 (test_send_commits_a_rename_of_a_file_already_sent) asserts the commit; the delta carried only the check requirement as MODIFIED (openspec/changes/archive/2026-10-25-outbox-skips-sent/specs/outbox/spec.md, '## MODIFIED Requirements' holds one requirement)",
    "F2": "src/agentmarshal/outbox.py:486 claims 'The rebuilt lines are byte-identical to what was read'; src/agentmarshal/outbox.py:547-549 drops at most one trailing empty element so a manifest without a final newline parses, and src/agentmarshal/outbox.py:495 always emits a trailing newline, so manifest_new != manifest_old for unchanged content",
    "F3": "src/agentmarshal/project.py:234 'Findings about **AgentMarshal itself** go here — one file per finding'; no occurrence of SENT in project.py's _OUTBOX_README (lines 232-277), and grep over docs/, CONTRIBUTING.md, README.md, templates/ finds no mention of the manifest",
    "F4": "src/agentmarshal/outbox.py:560-563 prints only f'{_printable(_SENT, markers)}: line {line_number} does not parse'; openspec/changes/archive/2026-10-25-outbox-skips-sent/design.md decision 2 claims 'a typo restores the very refusal digest 045 reported unless it is diagnosed'; tests/test_outbox.py:1719 (test_a_manifest_line_ending_in_a_carriage_return_refuses_the_check) encodes the CRLF case as a refusal",
    "F5": "src/agentmarshal/outbox.py:1094 is now `name = _printable(entry.name, markers)` where the diff's '-' line was `name = safe_path(_shown_name(entry.name), markers)`; _printable adds escape_for_display (src/agentmarshal/outbox.py:238), so outbox status escapes control characters it previously printed raw, while the contract's last criterion says 'no other command changes'"
  }
}
AGENTMARSHAL_VERDICT_END
