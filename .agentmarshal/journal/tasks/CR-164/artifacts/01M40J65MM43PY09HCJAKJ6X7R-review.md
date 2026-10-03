Проверил реализацию, тесты, дельты спеков и архив относительно контракта CR-164.

**Что подтверждено:**

- `GateError.__init__` (`src/agentmarshal/journal/gate.py:88-89`) эскейпит сообщение в точке рождения, поэтому все 18 мест `raise GateError(...)` в `gate.py`, `gate_context.py` и обёртки в `complete.py` / `review.py` несут уже эскейпленный текст; CLI печатает его как есть (`src/agentmarshal/cli.py:668`, `cli.py:703`) — изменение `cli.py` действительно не требуется.
- Каждый путь, который gate печатает, идёт через `say` → `escape_for_display`: в `gate.py` нет ни одного `print`, а `lines.append` встречается только на строках 123 и 638, обе — внутри `say`. Scope-строка (`gate.py:883`), record-collision (`gate.py:1117-1123`), append-only (`gate.py:1081-1086`), removal/named-extension (`gate.py:850-860`, `gate.py:951-956`) — все через `check`/`say`.
- Фикстуры (`tests/fixtures/gate/*`) не меняются и не содержат текста `GateError`, так что byte-identical требование выполнено; делегирующий тест вызывает `test_default_run_transcript_matches_the_committed_fixture` с существующим ключом `embedded-implementation`.
- Тесты не бутафорские: в `test_a_candidate_path_that_would_forge_a_line_is_named_in_escaped_form` проверка `"gate: passed" not in printed_lines` действительно упала бы без эскейпа, так как сырое имя разорвало бы scope-строку ровно на строку `gate: passed`. Rename-тест устойчив к режиму rename detection: источник попадает в outside и как `R`, и как `D`.
- MODIFIED-требование `scope-enforcement` воспроизводит существующий заголовок дословно и сохраняет все 4 прежних сценария; ADDED-требование `record-text-safety` совпадает с дельтой в архиве байт в байт; `openspec/changes/` пуст, кроме `archive/`.

**Advisory-замечание (не блокирует, за пределами изменённого кода):** в добавленном `openspec/changes/archive/2026-10-03-escape-gate-paths-and-errors/design.md` утверждается, что gate читает свои списки путей сырыми — «`git diff --name-status -z`, `git status -z`, `git ls-tree -z`) precisely so a quoted name cannot hide from a matcher». Для двух листингов это не так: `gate.py:677` читает базовое дерево как `git ls-tree -r --name-only base_commit` без `-z`, а `_tampered_records` (`gate.py:374-399`) — как `git log … --name-only` без `-z`. При `core.quotePath` по умолчанию git отдаёт там C-quoted имя, то есть ровно та слепота matcher'а, о которой предупреждает собственный комментарий кода на `gate.py:929-932`. Для отображения это безопасно (C-quoted форма — печатный ASCII, и `say` её не трогает), поэтому цель CR-164 не нарушена; но документ утверждает свойство кода, которого у этих двух листингов нет.

ADV-1-design-overclaims-nul-separated-listings — `openspec/changes/archive/2026-10-03-escape-gate-paths-and-errors/design.md:11-14`: заявленное «gate reads its path listings raw (`-z`)» не выполняется для `src/agentmarshal/journal/gate.py:677` и `src/agentmarshal/journal/gate.py:387`.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "98c724144d92daf613d69899ba838433159ad7cc", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-1-design-overclaims-nul-separated-listings"]}
AGENTMARSHAL_VERDICT_END
