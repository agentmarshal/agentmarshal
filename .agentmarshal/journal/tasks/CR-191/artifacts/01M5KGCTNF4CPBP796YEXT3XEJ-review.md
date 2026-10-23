Проверил диф статически (запуск Python в этой песочнице не разрешён), сверил его с ADR-0018, ADR-0022, `openspec/specs/contract-governance/spec.md`, с `gate.py` и с существующими пинами `status`.

Что сошлось: секция печатается между scope и `Records:`, фильтр implementer-сессий по `role == "implementer"` соответствует задокументированной конвенции `record-session --role implementer` (`docs/sidecar.md:297`, `docs/quickstart.md:491`); vendor берётся только из `usage.provider`; `fallback_reason` печатается лишь при наличии; каждая строка проходит через `escape_for_display`, и escape-пин совпадает с реальным поведением `display.py`; delta-спека корректно применена в основную спеку, включая MODIFIED-требование; `print_task_detail` вызывается только из `status` (`cli.py:1166`), так что «no other command changes» держится; задокументированный транскрипт в `docs/sidecar.md:306` относится к контракту без этих полей и не меняется; существующий байт-в-байт пин `tests/test_status_view.py:255` покрывает «сегодняшний» вид. Каждый сценарий новых требований назван в docstring соответствующего теста.

Отдельно проверил подозрение, что марк `(not declared for the role)` неправомерно ставится на review записи, привязанные к finding'у: нет — в findings lane именно finding-review является решающим ревью (`gate.py:158-173`), так что декларированный список `reviewers` его тоже покрывает. Снял.

Ниже — то, что осталось.

F1: `openspec/changes/archive/2026-10-23-status-declared-assignment/design.md:61-66` утверждает, что марк «not declared for the role» ставится «after the strip-and-casefold normalisation the gate's comparisons apply, so casing cannot move an actor out of the list», тогда как `src/agentmarshal/journal/status_view.py:373-377` сравнивает строго (`actor in declared`), а собственный тест изменения `tests/test_status_assignment.py:472` (`test_an_actor_differing_only_in_case_is_marked`) закрепляет обратное — `devin` против объявленного `Devin` помечается как не объявленный; задекларированный design-документ изменения описывает поведение, противоположное поставленному коду, причём именно в месте, где от сравнения зависит смысл марка.

F2: `src/agentmarshal/journal/status_view.py:437` печатает `- independence: (not declared)` для контракта без поля, хотя правило `reviewer-not-writer` проверяется гейтом безусловно (`src/agentmarshal/journal/gate.py:1253-1276`, и объявленное `reviewer-not-writer` сознательно не даёт второй строки — `gate.py:1284-1286`), поэтому строка, которую acceptance называет «the independence rules in force», занижает то, что на самом деле в силе.

F3: новое требование в `openspec/specs/contract-governance/spec.md` предписывает печатать «the implementer-session lines in the order the records stand, then the review lines in the order the records stand», но ни один тест в `tests/test_status_assignment.py` не содержит journal'а, где review-запись стоит раньше session-записи, так что группировка (сессии до ревью, а не порядок записей) не продемонстрирована.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "662af7113d1a0edfd783b95eb8b1e7cd7dcb4d9d",
  "verdict": "changes_required",
  "findings": ["F1"],
  "advisory_findings": ["F2", "F3"],
  "classes": {
    "F1": "claim-accuracy",
    "F2": "claim-accuracy",
    "F3": "test-gap"
  }
}
AGENTMARSHAL_VERDICT_END
