Разобрал контракт, diff и файлы в снапшоте. Ниже — проза по каждому finding и по каждому acceptance criterion, потом verdict-блок.

**Где диф соответствует критериям приёмки**

- **Критерий 1 (change + delta + архив).** Изменение лежит в `openspec/changes/archive/2026-10-25-outbox-skips-sent/` с `proposal.md`, `design.md`, `tasks.md` и delta-спекой на capability `outbox`; `openspec/changes/` больше ничего не содержит, то есть архивирование состоялось. Я побайтово сравнил блоки: MODIFIED-требование `outbox check names what each draft lacks` (delta 5–38) идентично живому `openspec/specs/outbox/spec.md:56-89`, а оба ADDED-требования (delta 42–181) идентичны `spec.md:331-470`; `grep "^### Requirement"` показывает каждое требование ровно один раз. Сценарии закрыты тестами с одноимёнными docstring: `test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft`, `test_check_index_skips_a_file_a_source_line_claims`, `test_send_index_skips_a_file_a_source_line_claims`, `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`, `test_the_sent_manifest_is_not_a_draft`, `test_an_unreadable_sent_manifest_refuses_the_check`, `test_send_refuses_when_every_file_is_already_sent`, `test_send_commits_a_rename_of_a_file_already_sent`, три теста на «line does not parse», `test_a_file_whose_name_could_add_a_line_to_the_manifest_is_refused`, `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends`, `test_a_refused_send_leaves_the_manifest_as_it_was` (+ вариант «absent»), `test_the_manifests_next_content_goes_through_the_leak_scan`. Критерий выполнен — с оговоркой CR-228-F2 про цитату внутри самого текста требования.
- **Критерий 2 (skip + строка `skipped as sent`).** `_check` читает `SENT` строго (`outbox.py:534-565`), подмешивает digest'ы индекса через общий `_index_claims` (`outbox.py:566-572`, `1040-1067`) и снимает `is_draft` при совпадении sha256 (`outbox.py:630-632`), печатая `skipped as sent: <n>` на `outbox.py:707-708`. Демонстрируют `test_a_file_the_sent_manifest_lists_is_not_checked_as_a_draft`, `test_check_index_skips_a_file_a_source_line_claims`, `test_send_index_skips_a_file_a_source_line_claims`.
- **Критерий 3 (запись в manifest тем же batch-коммитом + «changed after sending»).** Контент манифеста считается в check и пиннится один раз (`outbox.py:682-706`), `send` пишет ровно эти байты до `add` (`outbox.py:950-956`). Демонстрируют `test_send_records_the_batch_in_the_sent_manifest`, `test_a_manifest_gained_across_batches_appends`, `test_the_sent_manifest_is_pinned_once_with_the_content_send_writes` и `test_a_manifest_listed_file_whose_bytes_changed_is_checked_and_named`.
- **Критерий 4 (не-regular entry, README, прежнее поведение).** Ветка «not a draft, not checked» не изменилась (`outbox.py:600-606`, тест `test_an_entry_that_is_not_a_regular_file_is_named_as_not_checked`), README остался не-draft (`test_the_readme_init_writes_is_not_a_draft`). А вот «outbox без манифеста и без `--index` ведёт себя точно как раньше» — не выполнено: см. CR-228-F1.
- **Критерий 5 (escaping, leak scan, остальные команды).** Маскирование идёт до escaping (`_printable`, `outbox.py:224-238`), что демонстрирует `test_a_secret_beside_a_control_character_in_a_name_is_masked`; скан покрывает и skipped-файлы (`test_a_skipped_file_still_goes_through_the_leak_scan`), и будущие байты манифеста (`test_the_manifests_next_content_goes_through_the_leak_scan`). `outbox status` поменял только форму печати имени (`_printable` вместо `safe_path(_shown_name(...))`), что его собственное требование уже разрешает («exactly as `outbox check` names files», `spec.md:276-278`), так что «no other command changes» я считаю соблюдённым. Полную CI-последовательность я не запускал (см. verification) — опираюсь на заявление координатора.

**Findings**

- **CR-228-F1** — в `src/agentmarshal/outbox.py:966-978` охранник «no drafts to send» проверяет не то, что требует спека: он смотрит на букву статуса git и на путь манифеста (`status != "A" and names != [sent_spec]`), а не на то, что застейджено изменение файла, который уже отправлен. Поэтому любой изменённый или удалённый не-draft в outbox даёт коммит с нулём findings. Воспроизведение: обычный `outbox send` (README + draft + `SENT` закоммичены) → оператор правит `.agentmarshal/upstream/README.md` → `outbox send`: draft пропущен как sent, `result.drafts` пуст, `git diff --cached --name-status -z -M` даёт `M .agentmarshal/upstream/README.md`, условие `any(...)` истинно, `_batch_mismatch` чист (README запиннен на новые байты) → создаётся коммит `outbox: findings batch` со одним только README, и команда печатает его sha. Это противоречит и неизменённому требованию `outbox send` commits the checked batch (`openspec/specs/outbox/spec.md:176-180` плюс сценарий «send refuses when the outbox holds no drafts», `spec.md:207-212`), и новому тексту самого изменения (`spec.md:363-366`: «with no draft and no change to a file already sent, `send` SHALL refuse saying there are no drafts to send»). Тот же путь срабатывает на удалении draft'а (статус `D`). Существующий тест `tests/test_outbox.py:744-758` закрывает только untracked-README (статус `A`), поэтому дыра не покрыта.
- **CR-228-F2** — в `openspec/specs/outbox/spec.md:359-360` (и дословно в `src/agentmarshal/outbox.py:969-971`, и в `design.md` архива) новое поведение обосновано цитатой «ADR-0020 decision 4: findings stop riding along in journal commits». В `docs/adr/ADR-0020-the-outbox-command-group.md:90-97` decision 4 говорит только, что после прохождения check `outbox send` стейджит один outbox и делает **один коммит batch'а**, а доставка остаётся за оператором; тезис про «не ездить вместе с journal-коммитами» принадлежит decision 6 (`ADR-0020:107-116`, «the exclude pathspec stays the mechanism that keeps them out of journal commits»), и самой фразы «riding along» в ADR нет вообще (она есть только в `spec.md:183`). То есть в архивированную спеку попала ссылка на решение, которого это решение не содержит — и именно она оправдывает коммит без draft'а.
- **CR-228-F3** (advisory) — комментарий `_manifest_next` в `src/agentmarshal/outbox.py:486-487` утверждает «The rebuilt lines are byte-identical to what was read: the strict parse accepted only `<sha256>  <name>`». Для манифеста, написанного рукой с не-UTF-8 байтом в имени, это не так: `outbox.py:547` декодирует с `errors="replace"`, U+FFFD не отвергается `forges_rendered_text` (категория `So`), строка парсится, а `_manifest_next` кодирует её обратно уже как `\xef\xbf\xbd` — байты записи молча меняются, и `send` перезапишет файл.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "fc66a5b2e7f55a0b8fb2d51198a1eae53651d52f",
  "verdict": "changes_required",
  "findings": ["CR-228-F1", "CR-228-F2"],
  "advisory_findings": ["CR-228-F3"],
  "classes": {
    "CR-228-F1": "contract-mismatch",
    "CR-228-F2": "claim-accuracy",
    "CR-228-F3": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -n '^### Requirement' openspec/specs/outbox/spec.md", "result": "7 requirements, each heading exactly once; the two new ones at lines 331 and 430"},
      {"what": "diff of the archived delta's MODIFIED block (lines 5-38) against openspec/specs/outbox/spec.md lines 56-89", "result": "identical, no output"},
      {"what": "diff of the archived delta's ADDED block (lines 42-181) against openspec/specs/outbox/spec.md lines 331-470", "result": "identical, no output"},
      {"what": "grep -rn 'ride along|riding along|rides along' docs/adr/ADR-0020-the-outbox-command-group.md openspec/specs/outbox/spec.md", "result": "no hit in ADR-0020; only spec.md:183 and spec.md:360"},
      {"what": "ls openspec/changes/", "result": "only 'archive' — the change is archived, no live change directory remains"},
      {"what": "grep -n 'no drafts to send|nothing to send|README' tests/test_outbox.py", "result": "the only no-drafts send test is tests/test_outbox.py:744-758, on a fresh (untracked) README"}
    ],
    "read": [
      "src/agentmarshal/outbox.py (whole file)",
      "tests/test_outbox.py (helpers, existing send tests, all new tests)",
      "openspec/specs/outbox/spec.md",
      "openspec/changes/archive/2026-10-25-outbox-skips-sent/{proposal.md,design.md,tasks.md,specs/outbox/spec.md}",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "src/agentmarshal/journal/display.py (escape_for_display)",
      "src/agentmarshal/journal/records.py (forges_rendered_text, _FORGEABLE_CATEGORIES)",
      "src/agentmarshal/journal/capture.py (safe_path, render_leak_hits)"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "no uv and no .venv in the snapshot, and the sandbox denied running python at all; I rely on the coordinator's statement that the sequence passed on this commit"},
      {"what": "a scripted repro of CR-228-F1 (commit the outbox, edit only README.md, run outbox send)", "why": "the sandbox refused every python invocation with a script argument, so the finding rests on reading outbox.py:966-978 plus git's documented status letter for a modified tracked file"}
    ]
  },
  "evidence": {
    "CR-228-F1": "src/agentmarshal/outbox.py:966-978 (`if not result.drafts: if not any(status != \"A\" and names != [sent_spec] ...)` — a modified non-draft gives status 'M', so no refusal) against openspec/specs/outbox/spec.md:176-180, spec.md:207-212 and spec.md:363-366; the only existing no-drafts test is tests/test_outbox.py:744-758 and it covers only the untracked ('A') README",
    "CR-228-F2": "openspec/specs/outbox/spec.md:359-360 and src/agentmarshal/outbox.py:969-971 cite 'ADR-0020 decision 4: findings stop riding along in journal commits'; docs/adr/ADR-0020-the-outbox-command-group.md:90-97 (decision 4) says only that send stages the outbox and makes one commit of the batch, while docs/adr/ADR-0020-the-outbox-command-group.md:107-116 (decision 6) holds the journal-commit statement; grep for 'riding along' in that ADR returns nothing",
    "CR-228-F3": "src/agentmarshal/outbox.py:486-487 claims byte-identical rebuilt lines; src/agentmarshal/outbox.py:547 decodes the manifest with errors=\"replace\" and U+FFFD (category So) is not refused by forges_rendered_text (src/agentmarshal/journal/records.py:1830,1844-1855), so _manifest_next re-encodes the name and the bytes change"
  }
}
AGENTMARSHAL_VERDICT_END
