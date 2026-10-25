## Что я проверил

Прочитал `src/agentmarshal/outbox.py` целиком (`_locate`, `_check`, `_pinned_blob`, `_batch_mismatch`, `_run_send`, `_run_status`), `src/agentmarshal/project.py` (`_scaffold_outbox`, `write_project_file`, `initialize_project`, `find_project_root`/`_ancestors_from`), `src/agentmarshal/cli.py` (вывод `init`), `src/agentmarshal/extension_trust.py` (`_managed_directory` — прецедент, на который ссылается design), `docs/adr/ADR-0020-the-outbox-command-group.md`, `openspec/specs/outbox/spec.md` и новые тесты. Тесты запустить не смог — в этой песочнице `uv`/`pytest` требуют подтверждения, поэтому про CI опираюсь на утверждение координатора.

## Приёмочные критерии

**AC-1 (отказ на symlink до любой записи) — выполнен.** `_locate` (`outbox.py:181-188`) проверяет `outbox.parent` (`.agentmarshal`) и `outbox` через `is_symlink()` (lstat, без следования) до `outbox.is_dir()` и до любого I/O; `project_root` приходит из `find_project_root`, а `_ancestors_from` (`project.py:50`) делает `start.resolve()`, так что эти два компонента — единственные, которые могут быть ссылкой, и проверка лексическая по уже разрешённому корню. Формулировка отказа совпадает с прецедентом `extension_trust._managed_directory:226` байт в байт. `_run_new:361` вызывает `_locate` до `_write_draft`. Для `init`: `_scaffold_outbox` (`project.py:316-318`) отказывает до `mkdir`, а связанный `.agentmarshal` отсекает ещё раньше `write_project_file:190-193` (и `resolved_parent != parent` на `:199` закрывает symlink в предках). Демонстрируют: `test_a_linked_outbox_refuses_a_command_before_it_writes` (все четыре subcommand, `captured.out == ""`, `outside` пуст, `rev-list --count --all == "0"`), `test_a_linked_agentmarshal_component_refuses_the_command`, `test_init_never_scaffolds_through_a_linked_outbox`, `test_a_sidecars_linked_outbox_never_writes_the_host` (форма из threat model), плюс существующий `tests/test_smoke.py:224 test_init_rejects_symlinked_agentmarshal_directory`.

**AC-2 (send фиксирует только проверенные байты) — выполнен.** `_pinned_blob` (`outbox.py:814-836`) сравнивает `hash-object --stdin --path=<rel>` с `hash-object --stdin --no-filters` по одним и тем же байтам; расхождение даёт `None`, и вызывающий добавляет проблему к файлу (`:688-696`) либо к `SENT` (`:752-759`), что ставит `refused = True`, так что `_run_send:974` отказывает до `git add`. Механика корректна: `--path` применяет те же атрибуты, что и `add`, а для `--stdin` без `--path` фильтры не применяются вообще, поэтому `--no-filters` — точный blob прочитанных байт. Побочный эффект — усиление: pin теперь равен нефильтрованному blob, поэтому `_batch_mismatch:945` поймал бы и фильтр, появившийся между check и add. Демонстрируют: `test_send_refuses_a_draft_a_clean_filter_would_transform` (реальный `filter.x.clean = sed s/a/b/` на `.agentmarshal/upstream/0*.md`, проверяет `rev-list --count --all == "0"` и `diff --cached --name-only == ""`) и `test_send_refuses_when_a_filter_would_transform_the_sent_manifest`.

**AC-3 (`outbox status` escape имён) — выполнен.** Все три места, где `status` печатал имя, переведены на `_printable` (`outbox.py:1148`, `:1157`, `:1166`); остальное, что печатает `_run_status` — номера строк и hex-digest из регулярки. `_printable` маскирует раньше, чем escape, что и есть проверенное свойство. `escape_for_display` (`journal/display.py:27-43`) покрывает `\n`, `\r`, `\t` и всё остальное, что `forges_rendered_text` отклоняет. Демонстрирует: `test_a_control_character_in_a_file_name_is_escaped_in_the_report` (`bad\nname.md` → `bad\\nname.md: no index entry`, сырой перевод строки в выводе отсутствует).

**AC-4 (delta + архив) — выполнен.** Delta `openspec/changes/archive/2026-10-25-outbox-boundaries/specs/outbox/spec.md` — три ADDED requirements, шесть сценариев; каждый назван docstring'ом ровно одного теста (проверил все шесть). Требования попали в `openspec/specs/outbox/spec.md:489`, `:512`, `:530` по одному разу (`grep -n "^### Requirement:"` даёт 10 заголовков, новых — три), `openspec/changes/` содержит только `archive`, у директории есть `.openspec.yaml` — та же форма, что у 34 других архивных изменений.

**AC-5 (без symlink/трансформации/непечатных имён — как сегодня) — выполнен по чтению.** `_printable` для печатного имени тождественно прежнему `safe_path(_shown_name(...))`, потому что `escape_for_display` имеет быстрый выход `if not forges_rendered_text(value): return value`. Существующий `test_the_sent_manifest_is_pinned_once_with_the_content_send_writes` продолжает работать: он monkeypatch'ит `outbox_module._git` и считает только вызовы с `--path=.agentmarshal/upstream/SENT`, а `_pinned_blob` берёт `_git` из globals, поэтому дополнительные `--no-filters` вызовы в счёт не идут. Сам прогон CI я не воспроизводил.

## Findings (все advisory, ни один не блокирует)

**AUD-241-a1** — `outbox check` не видит трансформацию: `_run_check` (`outbox.py:524`) зовёт `_check(pin=False)`, поэтому `_pinned_blob` не вызывается, и для черновика, который clean filter перепишет, `check` печатает «all conform; no known leak signatures» и выходит с 0 — отказывает только `send`. Требование check'а в спеке заканчивается словами «so a batch wrapper can refuse to send» (`openspec/specs/outbox/spec.md:112`), и ADR-0020 решение 3 делает exit status именно этой точкой отказа до публикации, так что wrapper, завязанный на `outbox check`, получает чистый вердикт на черновике, который отправить нельзя. Сама дыра закрыта (`send` отказывает, `_batch_mismatch` страхует), а AC-2 говорит именно про `send`, поэтому это advisory, а не блокер.

**AUD-241-a2** — архивная спека несёт одно и то же обязательство дважды: новое ADDED-требование `openspec/specs/outbox/spec.md:530-533` («Every name `outbox status` prints SHALL be ... display-escaped printable form») перекрывает пункт, уже стоящий внутри существующего требования `outbox status` на `:290-292` («Every name the command prints SHALL be masked and a name that is not UTF-8 SHALL be written in escaped printable form»). Старая, более узкая формулировка осталась и теперь читается так, будто escape нужен только не-UTF-8 именам; MODIFIED на том требовании оставил бы одну формулировку. AC-4 ADDED разрешает, поэтому это замечание к качеству спеки, а не несоответствие контракту.

**AUD-241-a3** — три видимых пользователю отказа (`outbox` на symlink, `send` на трансформации, изменение вывода `status`) не описаны в CHANGELOG.md, хотя сопоставимое изменение outbox'а имеет там запись (`CHANGELOG.md:186`, «The outbox skips files it already sent (CR-228)»), а раздел `## 0.6.0 — unreleased` открыт. `CHANGELOG.md` не входит в scope контракта, так что править его было нельзя — по AGENTS.md это следует назвать departure в финальном отчёте; я лишь фиксирую пробел.

**AUD-241-a4** — `openspec/changes/archive/2026-10-25-outbox-boundaries/README.md` — единственный `README.md` среди всех 99 архивных изменений (`find openspec/changes/archive -maxdepth 2 -name README.md | wc -l` → 1, и это он); его три строки дублируют «Why» из `proposal.md`. Лишний файл в директории изменения, которого не просит ни одна конвенция репозитория.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "a16520d043f56b1e08536cec9ee972f40a6241b0",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["AUD-241-a1", "AUD-241-a2", "AUD-241-a3", "AUD-241-a4"],
  "classes": {
    "AUD-241-a1": "contract-mismatch",
    "AUD-241-a2": "style",
    "AUD-241-a3": "scope",
    "AUD-241-a4": "style"
  },
  "verification": {
    "executed": [
      {"what": "grep -n \"^### Requirement:\" openspec/specs/outbox/spec.md", "result": "10 requirements; the three new ones at lines 489, 512, 530, each exactly once"},
      {"what": "ls openspec/changes/", "result": "only 'archive' — the change is archived, nothing left unarchived"},
      {"what": "ls -a openspec/changes/archive/2026-10-25-outbox-boundaries and a prior change (2026-09-18-review-binds-to-a-finding)", "result": "same set plus an extra README.md; .openspec.yaml present in both"},
      {"what": "find openspec/changes/archive -name .openspec.yaml | wc -l; find openspec/changes/archive -maxdepth 2 -name README.md | wc -l", "result": "34 of 99 changes carry .openspec.yaml; exactly 1 README.md exists in the archive — this change's"},
      {"what": "grep -n \"escaped printable form, exactly as\" openspec/specs/outbox/spec.md", "result": "lines 206, 292, 533 — 292 is the pre-existing status clause the new requirement at 533 restates"},
      {"what": "grep -n outbox CHANGELOG.md", "result": "CHANGELOG.md:186 '### The outbox skips files it already sent (CR-228)'; no CR-241 entry under '## 0.6.0 — unreleased'"},
      {"what": "grep -rn symlink_to tests/ (outside test_outbox.py)", "result": "tests/test_smoke.py:231 already covers init refusing a symlinked .agentmarshal; no existing test relies on a symlinked outbox or .agentmarshal working for outbox commands"},
      {"what": "grep -n \"_managed_directory\" -A 25 src/agentmarshal/extension_trust.py", "result": "lines 212-227: same two-component is_symlink loop and the same 'refusing a symbolic link: {component}' wording — the design's cited precedent is exact"}
    ],
    "read": [
      "src/agentmarshal/outbox.py (module docstring, _locate, _shown_name, _printable, _check, _pinned_blob, _git, _batch_mismatch, _run_send, _index_claims, _run_status)",
      "src/agentmarshal/project.py (_ancestors_from, find_project_root, write_project_file, _scaffold_outbox, initialize_project)",
      "src/agentmarshal/cli.py:540-562 (init's outbox warning line)",
      "src/agentmarshal/journal/display.py:27-43 (escape_for_display)",
      "src/agentmarshal/extension_trust.py:212-227",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "openspec/specs/outbox/spec.md (requirements at 91, 174, 276 and the three new ones at 489, 512, 530)",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/{proposal.md,design.md,tasks.md,README.md,specs/outbox/spec.md}",
      "tests/test_outbox.py (helpers _CONFORMING/_project/_outbox/_conforming_draft/_git_out, test_the_sent_manifest_is_pinned_once_with_the_content_send_writes, and all seven new tests)",
      "CHANGELOG.md:1-40, 183-191"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the sandbox denied approval for every uv/pytest invocation; AC-5's CI claim is taken from the coordinator's note on this commit and was verified only by reading"}
    ]
  },
  "evidence": {
    "AUD-241-a1": "src/agentmarshal/outbox.py:524 `_run_check` calls `_check(stderr, pin=False, index=index)`; the transformation refusal lives behind `if pin and entry.name != _SENT:` at outbox.py:678 and `if pin and (manifest_old is not None or manifest_new):` at outbox.py:736, so `outbox check` reaches outbox.py:777 'outbox check: N draft(s) checked; all conform' and returns 0. Spec clause openspec/specs/outbox/spec.md:112 'so a batch wrapper can refuse to send'; ADR-0020 Decision 3 'Its exit status refuses on a failure, so a batch wrapper can refuse to send before publication rather than after it'.",
    "AUD-241-a2": "openspec/specs/outbox/spec.md:290-292 (existing, inside 'Requirement: `outbox status` reports which findings an index file claims'): 'Every name the command prints SHALL be masked and a name that is not UTF-8 SHALL be written in escaped printable form, exactly as `outbox check` names files.' vs openspec/specs/outbox/spec.md:530-533 (new ADDED): 'Every name `outbox status` prints SHALL be masked and written in display-escaped printable form, exactly as `outbox check` names files'.",
    "AUD-241-a3": "`grep -n outbox CHANGELOG.md` → CHANGELOG.md:186 '### The outbox skips files it already sent (CR-228)'; the '## 0.6.0 — unreleased' section (CHANGELOG.md:11) carries no CR-241 entry, and the contract's scope list does not include CHANGELOG.md.",
    "AUD-241-a4": "`find openspec/changes/archive -maxdepth 2 -name README.md | wc -l` → 1 (openspec/changes/archive/2026-10-25-outbox-boundaries/README.md), against `find openspec/changes/archive -maxdepth 1 -type d | wc -l` → 100 (99 changes + archive itself); the comparison change openspec/changes/archive/2026-09-18-review-binds-to-a-finding holds only .openspec.yaml, proposal.md, design.md, tasks.md, specs/."
  }
}
AGENTMARSHAL_VERDICT_END
