Изучил снапшот на коммите `dc499ae9e65df6eacfacfd1cba18cff3017d285c`. Диффа к ревью не приложено, и состояние дерева подтверждает: по контракту CR-096 не приземлилось ничего. В журнале задачи (`.agentmarshal/journal/tasks/CR-096/`) лежит одна запись — `opened`, ни одной session-записи, ни одного артефакта. Проверил каждый критерий приёмки отдельно.

**cr096-change-delta-absent** — директории `openspec/changes/render-amendment-history/` не существует: под `openspec/changes/` есть только `archive/` с тремя закрытыми изменениями (`2026-09-06-keep-review-prose`, `2026-09-07-close-rename-scope-hole`, `2026-09-07-retire-review-temp-copy`). Нет ни `proposal.md`, ни `design.md`, ни `tasks.md`, ни `specs/`. Строка `render-amendment-history` встречается во всём репозитории ровно в одном месте — в самом контракте `.agentmarshal/journal/tasks/CR-096/contract.md:14`. Критерий 1 требует, чтобы каждый сценарий из `specs/` был продемонстрирован тестом с называющим его докстрингом, а критерий 5 — чтобы в `tasks.md` были отмечены галочки; ни того документа, ни этого файла нет. Заодно это ломает критерий 1 на уровне «implementation follows design.md's decisions or records in design.md why it departed»: departure-заметке негде находиться.

**cr096-contract-history-spec-absent** — `openspec/specs/contract-history/` тоже отсутствует: в `openspec/specs/` лежат только `review-evidence/spec.md` и `scope-enforcement/spec.md`. Изменение, объявленное дельтой, никуда не сведено, и capability, которую CR-096 вводит, не имеет спеки в основном дереве.

**cr096-amendment-rendering-absent** — ни промпт ревьюера, ни бриф имплементера не несут блока amendment-истории. `src/agentmarshal/journal/review.py:39` — шаблон `_REVIEW_PROMPT` — подставляет `{contract}` (`review.py:60-61`) и «Named contract material» (`review.py:114`), и слово `amendment` в файле не встречается ни разу. То же в `src/agentmarshal/journal/brief.py`: `build_brief` (`brief.py:243-299`) собирает scope, acceptance и именованный материал, записей журнала при этом не читает вовсе. Критерий 3 — «the rendering reads amendment records from the journal the command works in, so an amendment recorded after the reviewed commit reaches the prompt for that commit» — не реализован ни в одной из двух точек. Это ровно тот механизм, который ADR-0011 (`docs/adr/ADR-0011-contract-amendment-visibility.md:9-12`) откладывал «in their own task»: «The rendering and the record field it describes are **not implemented by this document**; they follow in their own task». Эта задача и есть та самая, и рендеринга в ней нет.

**cr096-reviewed-contract-schema-absent** — поля `reviewed_contract` нет в `src/` ни разу; грепом оно находится только в тексте ADR-0011 (`:104`, `:135`), в контракте CR-096 и в ревью-артефактах предыдущей задачи CR-095. Валидатор записей остался нетронутым: `src/agentmarshal/journal/records.py:144` — `_SUPPORTED_SCHEMAS = frozenset({1, 2, 3, 4})`, версионированные группы полей заканчиваются на `_SCHEMA_4_FIELDS` (`records.py:145`), а логика штампа схемы — `records.py:282` — знает только `needs_schema_4`. `src/agentmarshal/journal/submit_review.py:35-60` контракт не читает и ничего не хеширует. Критерий 4 требует четырёх вещей — новая схема, разрешающая поле; писатель, штампующий её только на записи, которая поле несёт; отказ с сообщением, называющим поле, для записи под ранней схемой; и неизменная валидация существующих записей — из них не выполнено ни одно из первых трёх. Это же прямое расхождение с ADR-0004: его Consequences делают bump схемы механизмом, который делает рассогласование reader/writer читаемым как unsupported schema вместо «misreporting those fields as invalid»; без bump'а запись с `reviewed_contract` попала бы в закрытую проверку `records.py:224-227` («record has unsupported fields»), то есть в ровно ту ошибку, которую ADR-0004 велит избегать.

**cr096-no-tests-for-scenarios** — ни один тест из перечисленных в scope файлов не демонстрирует новое поведение: в `tests/test_review_launcher.py` и `tests/test_brief.py` слово `amendment` не встречается вовсе, а в `tests/test_journal.py` все упоминания (`:859-929`, `:1971`) относятся к существующей команде `amend` и её отказам, то есть к поведению до этого изменения. Критерий 1 требует теста на каждый сценарий дельты с докстрингом, называющим сценарий; таких тестов нет. Критерий 2 (пиннованный 0.3.0-промпт и gate-транскрипты проходят с неизменёнными ожиданиями) формально выполняется, но только потому, что не изменилось ничего — как доказательство обратной совместимости он пуст.

Критерий 5 в части «no line is added to the gate in any placement or lane» соблюдён: `src/agentmarshal/journal/gate.py` не тронут, и границы из Non-Goals (`amend` не пишет в `contract.md`, findings-лейн и sidecar-сверка не тронуты) нарушены не были. Это единственная часть контракта, которую пустой дифф удовлетворяет.

Отдельно отмечу как advisory: контракт называет `openspec/changes/render-amendment-history/` в `documents`, а `brief.py:105-106` на несуществующий путь возвращает пустой список молча — ни бриф имплементера, ни «Named contract material» в промпте ревьюера не скажут, что затребованный документ отсутствует. В моём собственном промпте этот документ значится в списке, но его текста нет, и причина не названа. Это симптом, а не отдельный дефект кода, но он означает, что имплементер CR-096 не получил бы сигнала о недостающей дельте.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "dc499ae9e65df6eacfacfd1cba18cff3017d285c",
  "verdict": "blocked",
  "findings": [
    "cr096-change-delta-absent",
    "cr096-contract-history-spec-absent",
    "cr096-amendment-rendering-absent",
    "cr096-reviewed-contract-schema-absent",
    "cr096-no-tests-for-scenarios"
  ],
  "advisory_findings": [
    "cr096-missing-document-silently-omitted-from-brief"
  ]
}
AGENTMARSHAL_VERDICT_END
