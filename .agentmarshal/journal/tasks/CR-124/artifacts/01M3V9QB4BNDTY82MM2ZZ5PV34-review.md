Проверил диф против контракта, снапшота кода и предыдущего ревью CR-123.

**Что проверено фактически**

- Форма шапок 032–036 совпадает с 027–031 (псевдоним, профиль, релиз наблюдения, `sha256:` в 64 hex, уникальные), структура разделов Finding → Proposed → Disposition → Where у всех десяти дайджестов батча, Where стоит последним.
- Утверждения о поведении инструмента сверены с исходниками: `report` печатает только `reviews=`/`tokens=` (`src/agentmarshal/journal/report.py:134`); session-запись имеет `created_at`, но ни старта, ни длительности, ни коммита (`src/agentmarshal/journal/records.py:940`); `submit-review` действительно не передаёт `reviewed_contract` (`src/agentmarshal/cli.py:629`), так что сужение формулировки в 031 корректно; `gate` проверяет «последнее ревью approved» и несовпадение e-mail ревьюера с авторами коммитов (`src/agentmarshal/journal/gate.py:959`), валидирует добавленные записи и соответствие `task` каталогу по всем задачам диффа, коллизии путей и второй `opened` (`gate.py:1019`, `gate.py:1070`), и нигде не требует, чтобы запись принадлежала названной задаче — как и сказано в 035; рецепт стейджинга из outbox README воспроизведён дословно (`src/agentmarshal/project.py:238`); цитата «stages only the journal» из 019 верна (`docs/proposals/019-...md:33`); `provider-limit` действительно документирован с 0.4.1 (`CHANGELOG.md:41`, `docs/quickstart.md:449`).
- Все перенесённые адвизори CR-123 закрыты: декларант отказа в 027, антецедент «both» в 030, сужение про хеш контракта в 031, Where у 027–030, и введение батча теперь перечисляет четырнадцать тем на четырнадцать файлов без неопубликованных номеров.
- Все markdown-ссылки в изменённых файлах разрешаются; строки карты документации и строки индекса для 032–036 на месте; ни один номер предложения, релиз или документ в новых файлах не является неопубликованным.
- Полную CI-последовательность здесь запустить не удалось (`uv run …` требует подтверждения, которого в неинтерактивной сессии нет), поэтому часть AC5 про CI я подтвердить не могу; изменение чисто документационное, а единственный тест, трогающий `docs/proposals`, — проверки README в `tests/test_project.py:38` — остаётся истинным.

Блокирующего не нашёл. Четыре необязательных замечания:

В `docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md:3` и в строке индекса `docs/proposals/README.md:101` диспозиция записана как `accepted *(it is the reporter's own measured withdrawal…)*`, но круглые скобки индекс определяет (`docs/proposals/README.md:36`) для «the part we are not taking» — здесь же в них стоит пояснение ко всему файлу, то есть ровно та форма, которую прошлый раунд отметил на 028/030 и которую этот дифф там убрал.

В том же файле шапка объявляет `accepted`, а раздел `## Disposition — the withdrawal is recorded` (`033-...md:82`) говорит, что судьба предложения «not a disposition of ours but the reporter's» — читатель получает «мы приняли отзыв» там, где тело утверждает, что диспозиции с нашей стороны нет.

В `docs/proposals/034-the-contract-does-not-name-its-implementer-and-reviewer.md:95` работа привязана к «the same contract-governance question the agreement record of proposal 031 waits on», а раздел Where (`034-...md:106`) и строка индекса (`docs/proposals/README.md:102`) называют только «the decision on the tool's boundary» и «where the assignment lives is undecided» — по Where и по строке таблицы нельзя понять, что это то же решение, с которым едет agreement record из 031.

В `docs/proposals/035-journal-transactions-sweep-records-of-other-tasks.md:97` Where называет три принятые части (постейджинг по задаче, предупреждение gate, листинг `status` неопубликованных записей), а строка индекса `docs/proposals/README.md:103` перечисляет только две — в отличие от строк 032 и 036, где перечислены все части.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "ae6a33e462173e18c25216bc4ef63dab43bf6c3d",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "033-disposition-parenthetical-outside-vocabulary",
    "033-header-disposition-contradicts-body",
    "034-where-does-not-name-the-contract-governance-decision",
    "035-index-row-omits-the-status-listing"
  ]
}
AGENTMARSHAL_VERDICT_END
