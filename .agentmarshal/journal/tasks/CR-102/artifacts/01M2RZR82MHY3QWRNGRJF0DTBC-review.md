Ревью готово: блокирующих замечаний нет, есть три рекомендательных (advisory). Тесты я не запускал: запуск `pytest` в этом окружении не одобрили, так что всё ниже основано только на чтении кода. Все места, где в `src/` вызывается `write_record`, я сверил с guard'ом:

- **Guard стоит везде, где нужно.** Его получили `submit_review` (единственная дыра, найденная пробой), `accept`, `amend`, `finding`, `complete` (commit, findings и sidecar), `abandon`, `reopen`, `record-session` и оба пути запуска `review`.
- **Вне охвата — только то, что туда не относится.** `migrate.py` пишет задачи с нуля в новый журнал, а `backfill.py` возвращает записи и ничего не пишет сам.
- **Решение принимается по одному набору.** Guard читает `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`, и `project_status` читает тот же набор.
- **Проверка до оплаты.** Оба launcher'а отказывают раньше, чем создаётся временная директория, пишется prompt и запускается reviewer.
- **Сценарии покрыты тестами.** У каждого сценария из delta spec есть тест, чей docstring его называет. Проверены оба терминальных состояния для каждой команды. Отказ `reopen` для abandoned уже покрыт в `tests/test_reopen.py:73`.
- **ADR.** Противоречий с ADR-0004 (state как projection) и ADR-0005 Decision 3 с его status note нет.

Рекомендательные замечания:

- **`reopen-predicate-still-duplicated`.** В `src/agentmarshal/journal/status.py:132-139` guard заново реализует правило «reopen только из `done`». `project_status` (`status.py:81-85`) продолжает держать своё. Из CLI копия действительно ушла, но у правила по-прежнему два места, а не одно, как утверждает `design.md`. Если guard будет спрашивать саму projection, например `project_status(task.records + ({"record_type": record_type},))`, копия исчезнет совсем.
- **`refusal-message-enumerates-admitted-set`.** Текст отказа в `status.py:142-149` («a measurement or a reopening» / «a measurement») перечисляет допустимые типы вручную и выбирает вариант по `task.state`, а не выводит его из константы. Если набор поменяется, сообщение начнёт врать. По сути это второй список, только в прозе.
- **`change-record-misstates-prior-state`.** Описание change в архиве неверно передаёт, как было до изменения:
  - В `proposal.md` (Impact) сказано, что `reopen` «keeps its own refusal… which the guard now mirrors». На деле diff удаляет эту проверку из CLI и переносит её в guard.
  - `proposal.md` называет пять копий правила, `design.md` — шесть. Diff удаляет восемь проверок `state != "open"`.
  - Оба документа называют отказ до запуска новым для обеих привязок. Для привязки к finding он уже был со времён CR-101: diff удаляет старую проверку из `_launch_finding_review`, и спека `findings-review` сама об этом пишет.
  - «Twelve in eight modules» не сходится с перечислением в самом `design.md`: там 13 мест в 7 модулях.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "16820dec0e35da9de0ba57128ebc48c03dd24653", "verdict": "approved", "findings": [], "advisory_findings": ["reopen-predicate-still-duplicated", "refusal-message-enumerates-admitted-set", "change-record-misstates-prior-state"]}
AGENTMARSHAL_VERDICT_END
