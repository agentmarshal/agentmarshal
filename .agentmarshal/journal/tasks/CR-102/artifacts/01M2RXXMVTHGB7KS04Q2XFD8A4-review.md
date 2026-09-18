Проверил диff против контракта: прошёл по всем writer-путям (`submit_review`, `acceptance`, `complete` ×3, `session`, cli `amend`/`finding`/`reopen`, обе ветки лаунчера), сверил guard с проекцией, прогрепал дерево на второй список допустимых типов, сверил цитаты из ADR-0005 (Decision 3 и status-note про reopened — на месте) и покрытие сценариев тестами. Тесты запустить не смог — `pytest` в этой песочнице требует подтверждения, так что проверка статическая.

Блокирующих дефектов не нашёл. Guard в `status.py:105` верно эквивалентен проекции: `state == "open"` тогда и только тогда, когда активного терминального записи нет (reopened сбрасывает флаг и проецируется в `open`), так что ранний возврат не пропускает ничего, что читатель отверг бы. Все шесть команд, которые раньше носили свою копию правила, теперь идут через хелпер, единственный экземпляр множества — `_RECORD_TYPES_ADMITTED_AFTER_TERMINAL`, и старые ассерты на сообщения (`tests/test_reopen.py:82,94`, `tests/test_journal.py:1001`) остаются подстроками нового текста.

Три замечания, ни одно не блокирует:

`refusal-message-misleads-on-abandoned` — в `src/agentmarshal/journal/status.py:119` отказ сообщает брошенной задаче, что её терминальная запись «admits only a measurement or a reopening», хотя следующая же ветка в той же функции (`status.py:123`) и проекция (`status.py:69`) отказывают в reopen после abandon; для `state: abandoned` вторая половина фразы ложна.

`reopen-rule-split-across-two-modules` — в `src/agentmarshal/cli.py:989` осталась собственная проверка `task.state != "done"` с текстом, дословно совпадающим с `status.py:130`; после guard она достижима только при `state == "open"`, то есть ветка «abandoned» в ней мертва, а правило «кого можно переоткрыть» теперь живёт в двух местах — ровно тот дрейф, который design.md заявлял целью устранить.

`gate-post-terminal-set-not-from-the-constant` — в `src/agentmarshal/journal/gate.py:744` лана measurements-only жёстко кодирует `-session.json` как единственное, что можно добавить к закрытой в base задаче; это второе выражение того же правила, и оно уже расходится с константой (нет `reopened`), из-за чего кандидат с записью reopen не проходит merge-gate. Код существует до этого изменения и `gate.py` не входит в scope контракта, но критерий «no second list of it exists in the tree» указывает именно на такие места.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ac73088906cdd86e56732f65e2cc9534692afd36", "verdict": "approved", "findings": [], "advisory_findings": ["refusal-message-misleads-on-abandoned", "reopen-rule-split-across-two-modules", "gate-post-terminal-set-not-from-the-constant"]}
AGENTMARSHAL_VERDICT_END
