Прочитал контракт, дельту, архив, обе спеки и весь новый код в `tests/test_gate.py`, плюс строки транскрипта в `src/agentmarshal/journal/gate.py` и `src/agentmarshal/cli.py`, из которых собраны фикстуры.

## Что сошлось

- Архив `openspec/changes/archive/2026-10-03-pin-gate-transcript-by-fixture/` содержит proposal, design, tasks и дельту; текст дельты совпадает с `openspec/specs/gate-lanes/spec.md:46-77` байт в байт, структура совпадает с соседними архивами — похоже на результат `openspec archive`, а не на ручную правку.
- Три сценария дельты закрыты тестами, чьи docstring их называют: `test_default_run_transcript_matches_the_committed_fixture`, `test_a_transcript_difference_is_shown_as_a_readable_diff`, `test_a_fixture_changes_only_when_the_output_changes_on_purpose`.
- Все строки в четырёх фикстурах я нашёл в источнике: `gate.py:787` (детерминированная полоса), `gate.py:872` (контракт из рабочего дерева сидекара), `gate.py:1083-1087` и `1101-1106` (варианты «none examined»), `cli.py:855/867` и `placement.advisory_notice`. Аббревиатура — ровно `[:12]` (`gate.py:1007,1044`), что совпадает с `_run_values`.
- Оба сравнения с релизным 0.3.0 удалены; `released_030`/`SKIP_030` остались и реально используются в `test_findings.py:22` и `test_journal.py:265`, так что `subprocess`/`shutil`/`os` не повисли неиспользованными.
- Ослабления соседних тестов не нашёл: `test_empty_scope_candidate_takes_the_diff_lane_and_is_refused` (`tests/test_gate.py:851`) сохранил утверждение `paths outside contract scope: host-change.py`, которое раньше жило только в удалённом 0.3.0-тесте. Прямой вызов параметризованной функции из двух делегатов работает — `parametrize` возвращает ту же функцию.
- Полную последовательность CI я не прогонял: в этой песочнице `python3 -m pytest` требует подтверждения, а `uv`/`pytest`/`ruff`/`mypy` не установлены. Критерий 5 проверен только чтением, не исполнением.

## Находки

**scope-enforcement-spec-still-pins-030** — `openspec/specs/scope-enforcement/spec.md:37-39`: сценарий «a candidate without renames prints the transcript it printed before» по-прежнему утверждает «the gate's transcript is byte-for-byte what 0.3.0 printed for it», а единственный тест, который его называет (`tests/test_gate.py:717`), теперь делегирует в фикстурное сравнение, и сравнения с 0.3.0 в наборе больше нет ни одного. То есть спека утверждает проверку, которой в репозитории не существует. Proposal в разделе Impact заявляет обратное — «keeps its test, which now demonstrates the scenario through the committed fixture rather than the released binary», — хотя THEN-клаузу про 0.3.0 фикстура не демонстрирует. Путь `openspec/specs/scope-enforcement/` не в scope контракта, так что починить его здесь нельзя; но тогда это обязано было уйти в дельту плюс расширение scope или в отчёт как departure, а не в Impact как уже решённое.

**sha-placeholder-collapses-full-and-abbreviated** (advisory) — `tests/test_gate.py:361-369`: `_run_values` отображает и полный `head` (40 символов), и `head[:12]` в один и тот же плейсхолдер `<head-sha>` (то же для `base`). Значит, изменение, которое переключит любую строку транскрипта с `resolved_commit[:12]` на `resolved_commit` (или назад), после нормализации даст тот же текст, и пин этого не заметит — ровно тот класс изменения вывода, который по требованию должен быть «made, and named, by the task that changes the output». Разные плейсхолдеры (`<head-sha>` / `<head-sha-12>`) закрыли бы дыру без потери читаемости.

**missing-fixture-compares-as-empty** (advisory) — `tests/test_gate.py:332-341`: отсутствующий файл фикстуры подставляется как `""`, а не считается ошибкой. Для трёх кейсов, у которых `.stderr` пустой (`embedded-implementation`, `embedded-journal-only`, `sidecar-implementation`), это значит, что удаление файла фикстуры не отличимо от совпадения — поток перестаёт быть запинованным молча, хотя требование говорит «stderr ... SHALL each equal the fixture for its lane and placement». Задача 1.1 верифицировалась глазами («the files exist»), тестом существование триплетов не проверяется.

**sidecar-journal-only-lane-overstated-in-spec** (advisory) — `openspec/specs/gate-lanes/spec.md:59-64`: сценарий перечисляет «the journal-only lane, in the embedded and the sidecar placement», как будто такая полоса в сидекаре есть. Её нет — `run_gate` принудительно выключает `journal_only` в сидекаре (ADR-0008 Decision 2), и фикстура `sidecar-journal-only` пинует отказ, а не полосу. Design и docstring кейса (`tests/test_gate.py:412-417`) это честно объясняют, но текст спеки, который переживёт их обоих, читается как противоречие ADR-0008.

**empty-scope-candidate-duplicates-gate-arguments** (advisory) — `tests/test_gate.py:825-835`: `_empty_scope_candidate` собирает тот же список аргументов вручную, который теперь даёт `_gate_arguments` (`tests/test_gate.py:347`); при изменении формы вызова gate эти два места разъедутся.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "2244618d4bc69e5548a77774e82a39e0cb8fb37e",
  "verdict": "changes_required",
  "findings": ["scope-enforcement-spec-still-pins-030"],
  "advisory_findings": [
    "sha-placeholder-collapses-full-and-abbreviated",
    "missing-fixture-compares-as-empty",
    "sidecar-journal-only-lane-overstated-in-spec",
    "empty-scope-candidate-duplicates-gate-arguments"
  ]
}
AGENTMARSHAL_VERDICT_END
