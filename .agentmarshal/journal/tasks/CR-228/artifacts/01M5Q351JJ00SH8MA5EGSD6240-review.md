Прочитал весь `src/agentmarshal/outbox.py`, оба спека (живой и архивную дельту), `tests/test_outbox.py`, `ADR-0020`, `display.py`/`records.py`/`capture.py` (`escape_for_display`, `forges_rendered_text`, `safe_path`, `LeakHit`) и `cli.py`. Ниже — по критериям приёмки, потом находки.

**Где диф попадает в критерии приёмки**

- **Критерий 1** выполнен. В дельте есть `proposal.md`, `design.md` и спек-дельта на capability `outbox`: блок MODIFIED воспроизводит требование `outbox check` names what each draft lacks вместе с заголовком и всеми пятью сценариями — сверил с `openspec/specs/outbox/spec.md:56-89`, текст совпадает побайтово; плюс два ADDED-требования с 13 сценариями, у каждого есть тест, чей docstring называет сценарий (`test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft`, `test_the_sent_manifest_is_not_a_draft`, `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends`, `test_the_manifests_next_content_goes_through_the_leak_scan` и остальные). Change лежит в `openspec/changes/archive/2026-10-24-outbox-skips-sent/`, а в `openspec/changes/` остался только `archive` — архивация командой подтверждается.
- **Критерий 2** выполнен: чтение манифеста и слияние с претензиями индекса — `src/agentmarshal/outbox.py:510-534`, сам скип — `:586-594`, строка `skipped as sent: <n>` — `:659-660`; демонстрируют `test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft`, `test_check_index_skips_a_file_a_source_line_claims`, `test_send_index_skips_a_file_a_source_line_claims`.
- **Критерий 3** выполнен: `_manifest_next` (`:464-478`), пин манифеста по вычисленным байтам (`:645-658`) и запись ровно этих байт до `add` (`:886-892`); демонстрируют `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends`, а аннотацию «changed after sending» — `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`.
- **Критерий 4** выполнен частично. Нерегулярная запись по-прежнему одной строкой и не считается провалившимся драфтом (`:561-567`, `test_an_entry_that_is_not_a_regular_file_is_named_as_not_checked`), README по-прежнему не драфт (`:573`, `test_the_readme_init_writes_is_not_a_draft`). Но оговорка «which the existing outbox tests demonstrate unchanged» не держится — см. OB-1 и OB-2.
- **Критерий 5** выполнен: экранирование не ослаблено, а усилено (`_display_name`, `:222-232`), и изменение `status` здесь не самовольное — спек сам требует «exactly as `outbox check` names files» (`openspec/specs/outbox/spec.md:276-278`); leak scan покрывает и пропущенные файлы, и будущее содержимое `SENT` (`test_a_skipped_file_still_goes_through_the_leak_scan`, `test_the_manifests_next_content_goes_through_the_leak_scan`); `cli.py` не тронут — заявление proposal'а верно. Последовательность CI сам не запускал (снапшот не git-репозиторий, режим read-only) — беру из записки координатора.

**Находки**

**OB-1** (blocking). После этого изменения `outbox send` навсегда отказывается коммитить staged-переименование уже отправленного драфта: переименованный файл имеет те же байты, значит его sha256 лежит в `SENT`, значит он не драфт, и `src/agentmarshal/outbox.py:854` (`if not result.drafts`) выдаёт «no drafts to send». Собственный тест автора это и закрепляет — `tests/test_outbox.py:1593-1626`: один коммит, переименование остаётся в индексе, выхода нет (ни флага, ни подсказки). Единственный путь для оператора — ручной `git commit`, то есть ровно тот режим, который ADR-0020 (решение 4 и раздел Consequences: «one commit of the outbox only, so findings stop riding along in journal commits») существует чтобы убрать; proposal 023 его и измерил как дефект. Ни в `openspec/specs/outbox/spec.md`, ни в ADDED-требованиях дельты этот отказ для переименованного отправленного файла не описан — он живёт только в `tasks.md` 3.1-3.3 и в docstring теста.

**OB-2** (advisory). Критерий 4 обещает, что «the existing outbox tests demonstrate [today's behaviour] unchanged», но существующий тест пришлось переписать: в `tests/test_outbox.py:941-947` первый батч теперь делается вручную (`git add` + `git commit`) вместо `main(["outbox", "send"])` — именно потому, что `send` теперь пишет манифест и сценарий иначе недостижим. Это departure, который стоило назвать в отчёте, а не замаскировать правкой теста.

**OB-3** (advisory). Испорченная строка манифеста игнорируется абсолютно молча: `_SENT_LINE` (`src/agentmarshal/outbox.py:62`) и фильтр на `:523-527` отбрасывают её без счётчика и без сообщения, что `tests/test_outbox.py:1660-1686` прямо фиксирует (ни «skipped as sent», ни «changed after sending», ни единого слова о трёх отброшенных строках). При этом `design.md` сам приглашает писать `SENT` руками («the `sha256sum` output form, so an adopter's own record of a batch can become it by hand»), так что опечатка в один пробел или заглавный hex — оба случая из теста — возвращают адоптеру ровно тот отказ, о котором сообщил digest 045, без диагностики. Тот же эффект даёт `SENT`, вычекаутенный с CRLF: `forges_rendered_text` отвергает хвостовой `\r`, и строка не перечисляет ничего. Это расходится с собственным правилом группы — `openspec/specs/outbox/spec.md:100`, «nothing in the outbox passes in silence».

**OB-4** (advisory). Пин `SENT` внутри цикла — мёртвая работа, которая всё же может завалить прогон. При `pin=True` и существующем регулярном `SENT` цикл пинит ключ `.agentmarshal/upstream/SENT` на blob *текущих* байт манифеста (`src/agentmarshal/outbox.py:595-609`), а блок `:645-658` перезаписывает тот же самый ключ blob'ом `manifest_new`; первое значение не используется никогда. Но если именно этот ненужный `git hash-object` упадёт, в `problems` попадёт «cannot be pinned» и check откажет, хотя пин, который реально нужен, прошёл бы.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "e4c8aa6c0d85435b6b4d1e1ae4b14075b1ba6f98",
  "verdict": "changes_required",
  "findings": ["OB-1"],
  "advisory_findings": ["OB-2", "OB-3", "OB-4"],
  "classes": {
    "OB-1": "contract-mismatch",
    "OB-2": "claim-accuracy",
    "OB-3": "correctness",
    "OB-4": "simplification"
  },
  "verification": {
    "read": [
      "src/agentmarshal/outbox.py (full)",
      "src/agentmarshal/journal/display.py (full)",
      "src/agentmarshal/journal/records.py (forges_rendered_text, _FORGEABLE_CATEGORIES, _BIDIRECTIONAL_CONTROLS)",
      "src/agentmarshal/journal/capture.py (LeakHit, safe_path, _LEAK_PATTERNS)",
      "src/agentmarshal/cli.py (outbox registration and dispatch)",
      "src/agentmarshal/project.py (_OUTBOX_README scaffold)",
      "openspec/specs/outbox/spec.md (full)",
      "openspec/changes/archive/2026-10-24-outbox-skips-sent/{proposal.md,design.md,tasks.md,specs/outbox/spec.md}",
      "tests/test_outbox.py (new tests plus the send/check tests they interact with)",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "AGENTS.md, CONTRIBUTING.md, README.md, .gitattributes"
    ],
    "executed": [
      {
        "what": "grep -n '### Requirement|#### Scenario|README|regular file' openspec/specs/outbox/spec.md",
        "result": "the MODIFIED requirement's heading and its five scenarios in the archived delta match openspec/specs/outbox/spec.md:56-89 exactly; the two ADDED requirements appear once each at :331 and :409"
      },
      {
        "what": "grep -n 'def test_|no drafts to send|nothing to send' tests/test_outbox.py",
        "result": "all 13 added scenarios have a test whose docstring names them; test_send_refuses_a_rename_of_an_already_sent_draft at :1593 and the rewritten rename test at :934"
      },
      {
        "what": "ls openspec/changes/ openspec/changes/archive/",
        "result": "openspec/changes/ holds only archive/; the change sits at archive/2026-10-24-outbox-skips-sent/"
      },
      {
        "what": "grep -rln 'upstream' openspec/specs/ ; grep -rn 'outbox' CONTRIBUTING.md README.md ; grep -rn 'CHANGELOG' CONTRIBUTING.md AGENTS.md",
        "result": "only openspec/specs/outbox/spec.md describes the outbox; no changelog obligation in CONTRIBUTING.md or AGENTS.md, so no out-of-scope doc duty was skipped"
      }
    ],
    "not_run": [
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "read-only review, and the snapshot is not a git repository (several outbox tests drive real git), so I rely on the coordinator's note that the sequence passed on this commit"
      }
    ]
  },
  "evidence": {
    "OB-1": "src/agentmarshal/outbox.py:854 ('if not result.drafts: print(\"outbox send: no drafts to send\")') combined with the skip at :586-589 ('if is_draft and digest in sent_digests: skipped += 1; is_draft = False'); tests/test_outbox.py:1593-1626 asserts main(['outbox','send']) == 1, 'no drafts to send' in stderr, rev-list --count HEAD == '1' and the operator's R100 rename still staged; openspec/specs/outbox/spec.md has no scenario for a renamed already-sent file; contradicts docs/adr/ADR-0020-the-outbox-command-group.md decision 4 and its Consequences ('one commit of the outbox only, so findings stop riding along in journal commits')",
    "OB-2": "tests/test_outbox.py:941-947 — the first batch changed from 'assert main([\"outbox\", \"send\"]) == 0' to '_git(repo, \"add\", \".agentmarshal/upstream\"); _git(repo, \"commit\", \"-m\", \"an earlier batch\")', against the contract's criterion 4 clause 'which the existing outbox tests demonstrate unchanged'",
    "OB-3": "src/agentmarshal/outbox.py:62 (_SENT_LINE = r'^([0-9a-f]{64})  (.+)$') and :523-527 ('if match and not forges_rendered_text(match.group(2))') drop a line with no output; tests/test_outbox.py:1660-1686 asserts 'skipped as sent' not in out and 'changed after sending' not in out for three malformed lines; openspec/changes/archive/2026-10-24-outbox-skips-sent/design.md invites a hand-written manifest ('the `sha256sum` output form, so an adopter's own record of a batch can become it by hand'); openspec/specs/outbox/spec.md:100 states 'nothing in the outbox passes in silence'",
    "OB-4": "src/agentmarshal/outbox.py:599-609 pins os.fsencode(f'{_OUTBOX_PREFIX}{entry.name}') for entry.name == 'SENT', and :646-652 overwrites the identical key os.fsencode(f'{_OUTBOX_PREFIX}{_SENT}') with the blob of manifest_new; the loop's failure branch at :606-609 appends 'cannot be pinned' to problems, which sets refused = True at :627-628"
  }
}
AGENTMARSHAL_VERDICT_END
