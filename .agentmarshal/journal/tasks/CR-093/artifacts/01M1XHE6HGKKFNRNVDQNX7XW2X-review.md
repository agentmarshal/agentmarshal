Разобрал diff, реализацию `run_gate`, старые тесты на rename и архив/спеку. Прогнать `pytest` не смог — sandbox блокирует запуск `python3`/`uv`, поэтому проверка статическая; об этом скажу прямо, а не выдам за прогон.

## Что проверил

**Реализация (`gate.py`)** — сделано ровно то, что записано в design.md:
- `_changed_paths` удалён (`grep` по репозиторию: живых ссылок нет, только в архивных design.md/tasks.md как история);
- `changed` собирается из `changes_with_status` через `dict.fromkeys` — дедуп в порядке листинга, как решено;
- три читателя (`journal_only` на строке 655, `outside` на 796, пустой диапазон на 605) читают один и тот же список;
- `--name-only` в файле остались только у `ls-tree` (529, 610, 859) и `git log` (376) — verify-строка задачи 1.1 держится;
- порядок вывода не поехал: `outside` по-прежнему `sorted()`, lane — `all(...)`, так что PASS-формулировки не меняются.

**Регрессии на существующих тестах** — прошёл по всем местам, где кандидат удаляет и добавляет файлы в одном диапазоне. `test_renaming_a_named_document_counts_as_touched` (обе стороны в `docs/`) и `test_gate_refuses_record_rename_out_of_records` (обе стороны под journal-префиксом) остаются в прежнем классе. Тесты удаления extension'ов удаляют без парных добавлений, поэтому rename-детекция их не трогает.

**Mutation-клаузула критерия 1** — при возврате `changed` к `git diff --name-only` все три rename-теста падают: №1 теряет `outside/original.py` из FAIL, №2 получает `checked_paths == ["src/renamed.py"]`, №3 печатает `journal-only transaction` и вообще проходит гейт. Трюк с monkeypatch `scope_covers` в №2 — единственный способ увидеть разницу там, где итог и так PASS; сделано корректно, `scope_covers` в этом тесте больше нигде не вызывается (documents и extensions пусты).

**Архив и спека** — структура `openspec/changes/archive/2026-09-07-close-rename-scope-hole/` совпадает с двумя соседними архивами, `openspec/specs/scope-enforcement/spec.md` написан в том же формате, что `review-evidence` (заголовок, `## Purpose` прозой, `## Requirements`). Требование и четыре сценария скопированы в baseline дословно. `openspec validate --all` запустить не смог.

## Findings (оба advisory, не блокирующие)

Тест `test_embedded_diff_lane_transcript_matches_published_030_byte_for_byte` в `tests/test_gate.py:275` изменён — ему добавлен docstring, — тогда как критерий 3 требует, чтобы этот тест проходил «unmodified». Это прямое противоречие между критерием 1 (каждый сценарий назван в docstring теста) и критерием 3, и реализатор выбрал чтение, при котором выполнимы оба: docstring инертен, ни одно утверждение теста не ослаблено. Фиксирую как расхождение с буквой контракта, а не как дефект.

Три новых rename-теста (`tests/test_gate.py:311`, `:338`, `:373`) создают репозиторий через `_gate_repo`, который делает `git init` без `-c diff.renames=true`, поэтому детекция переименований наследуется из глобального git-конфига запускающего. При `diff.renames=false` все три теста по-прежнему пройдут — git сам покажет D+A, — но перестанут различать исправленный и старый код, и mutation-свойство, которого требует критерий 1, молча исчезнет. Продакшен-поведение от этого не страдает (фикс инвариантен к настройке), страдает только доказательная сила тестов.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c3a0a7a7ec0364c007b5f5bf123cc91a68654987", "verdict": "approved", "findings": [], "advisory_findings": ["transcript-test-modified-by-docstring", "rename-tests-inherit-global-diff-renames"]}
AGENTMARSHAL_VERDICT_END
