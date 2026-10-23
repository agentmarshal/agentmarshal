Прошёл по диффу, ADR-0021/0022, `openspec/specs/leak-scan/spec.md` и по исходникам `cli.py`, `capture.py`, `acknowledge.py`, `status.py`, `records.py`.

Главное: реализация соответствует контракту. Чтение записей идёт через `load_task_status`/`list_task_statuses` над `placement.journal_root`, сопоставление — строгое равенство `file`/`identification` без нормализации, любая ошибка чтения ловится одним guard'ом (`TaskStatusError` и `JournalRecordError` оба наследуют `ValueError`, так что tuple в `except` их покрывает; `JournalContractError` из `parse_contract` — тоже `ValueError`), `acknowledgements` остаётся пустым и exit возвращается к сегодняшней единице. `recorded_by` и `reason` обязательны для `acknowledgement` в реестре (`attestation.py:105`, `requires_recorded_by=True`) и проверяются в `read_records`, поэтому прямая индексация `record["recorded_by"]`/`record["reason"]` в `_acknowledgement_mark` не даст KeyError. `render_leak_hits` без `marks` рендерит байт в байт как раньше — вызов gate не тронут. Все сценарии дельта-спеки покрыты тестами с совпадающими docstring'ами.

Блокирующего не нашёл. Четыре advisory:

`mark-masking-unspecified` — `src/agentmarshal/cli.py:1347` прогоняет весь mark через `mask_leaks` перед `escape_for_display`, но живая спека (`openspec/specs/leak-scan/spec.md:637`) обещает только «each escaped on display», а design.md архивной change (`.../design.md:106`) прямо утверждает обратное — «The matched text is in neither the record nor the hit, so it can be in neither mark nor output» — хотя собственный тест `test_the_mark_masks_a_recorder_named_the_secret` показывает, что `recorded_by` вполне может быть значением маркера. Поведение выбрано в безопасную сторону, но ни одно требование и ни один сценарий его не описывают.

`stale-acknowledge-docstring` — `src/agentmarshal/acknowledge.py:29` всё ещё заявляет «An acknowledgement is not yet honoured anywhere: `leak-scan`'s output and exit are unchanged», что после этой задачи ложно; файл вне объявленного scope, поэтому правка — отдельный шаг, но утверждение осталось в поставляемом коде.

`sidecar-read-untested` — новое требование явно называет sidecar («the journal repository's working tree under a sidecar (ADR-0014)»), и именно там расходятся два корня: `scan_root = placement.host_root` для rev-parse и `placement.journal_root` для записей. В `tests/test_leak_scan_acknowledgements.py` нет ни одного sidecar-теста, хотя CR-187 такой тест для записи добавил (`tests/test_acknowledge.py:761`). Статически путь выглядит корректным, но он ничем не закреплён.

`help-verification-unperformed` — `.../tasks.md:4` отмечен выполненным с формулировкой «verify: `leak-scan --help` lists it (pytest)», однако ни один тест не проверяет вывод `leak-scan --help`; `--task` покрыт только функционально.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b3ba0215780fa8a014046150df453357cfa93a80",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "mark-masking-unspecified",
    "stale-acknowledge-docstring",
    "sidecar-read-untested",
    "help-verification-unperformed"
  ],
  "classes": {
    "mark-masking-unspecified": "contract-mismatch",
    "stale-acknowledge-docstring": "claim-accuracy",
    "sidecar-read-untested": "test-gap",
    "help-verification-unperformed": "claim-accuracy"
  }
}
AGENTMARSHAL_VERDICT_END
