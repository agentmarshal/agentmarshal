Разобрал контракт, диффы, ADR-0018/ADR-0022, спеку `contract-governance`, `status_view.py`, `records.py`, `gate.py` и новый тест-файл. Проверка по пунктам:

**Что сходится**

- Секция печатается между блоком `Scope:` и `Records:` — `src/agentmarshal/journal/status_view.py:544`; все строки проходят через `escape_for_display`, как остальные rendered-строки (ADR-0015 решение 5), и байтовый pin в `tests/test_status_assignment.py:712` это демонстрирует.
- Vendor читается только из `usage.provider` (`status_view.py:401`), никогда не выводится из `actor` — совпадает с ADR-0022 §2 («the vendor is read from the existing `usage.provider`, no new field») и с правилом гейта `_session_independence_value` (`gate.py:660`).
- Утверждение «`reviewer-not-writer` (always checked by the gate)» подтверждается кодом: проверка идентичности ревьюера выполняется при любом `latest is not None`, независимо от объявления (`gate.py:1257`), а объявленное правило исключается из списка правил (`gate.py:1285`) — ровно то, что требует `openspec/specs/contract-governance/spec.md:741`.
- Mark `(not declared for the role)` ставится только при объявленном списке роли и только при наличии имени (`status_view.py:389`) — «показано, не отказано», как требует ADR-0018 решение 3.
- MODIFIED-требование применено в основную спеку дословно, ADDED-требования совпадают с дельтой байт в байт (diff дельты и `openspec/specs/contract-governance/spec.md:758-916` даёт только заголовок `## MODIFIED Requirements`); change заархивирован по тому же соглашению, что и соседи в `openspec/changes/archive/`, `openspec/changes/` пуст. Правило AGENTS.md «не править `openspec/specs/` руками» соблюдено.
- Все 18 сценариев дельты имеют тест, чей docstring их называет. Байтовый pin «без объявлений» опирается на сравнение schema-1 и schema-3-без-полей плюс существующий полный pin `tests/test_status_view.py:255`, который диффом не тронут.
- Ни фикстуры гейта, ни транскрипт в `docs/sidecar.md:315` (контракт schema 1) не затронуты; других команд диff не касается — `print_task_detail` вызывается только из `status` (`cli.py:1166`).

Проверку CI я не перезапускал (в снапшоте нет ни `uv`, ни `pytest`) и на её результат не ссылаюсь.

**Advisory-находки**

A1-ran-side-silent-when-nothing-ran: в `src/agentmarshal/journal/status_view.py:455` строки «что выполнялось» просто не печатаются, когда подходящих записей нет, — контракт с объявленным `implementers` и без implementer-сессий выводит три строки объявления и сразу `Records:`, то есть сторона «кто сделал» не говорит ничего; это противоречит собственному принципу секции («the absence is stated rather than omitted» в `_declared_list`) и блоку `Scope:`, который в таком случае печатает `- (none)`. Поведение зафиксировано тестом `tests/test_status_assignment.py:264`, спека его не запрещает — отсюда advisory, а не blocking.

A2-unreachable-absent-session-actor: `openspec/specs/contract-governance/spec.md:821` обещает, что «a session carrying no actor shows the absent value and no mark», но read-правило `_check_session_fields` (`src/agentmarshal/journal/records.py:751`) безусловно, для любой schema, отказывает session-записи без непустого `actor`, и `actor` входит в `_REQUIRED_FIELDS["session"]` (`records.py:122`) — такого состояния journal держать не может, поэтому тест `tests/test_status_assignment.py:405` вынужден собирать `TaskStatus` руками в обход `read_records`. Ветка безвредна как defense-in-depth (в отличие от `reviewer.actor`, который действительно опционален), но сценарий спеки читается как покрытие реального случая.

Оба пункта не блокируют: ни одно acceptance-условие контракта и ни одно требование спеки ими не нарушено.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8691817adf50c5e8449bd44e5aa7c967fae74e9d",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "A1-ran-side-silent-when-nothing-ran",
    "A2-unreachable-absent-session-actor"
  ],
  "classes": {
    "A1-ran-side-silent-when-nothing-ran": "style",
    "A2-unreachable-absent-session-actor": "claim-accuracy"
  }
}
AGENTMARSHAL_VERDICT_END
