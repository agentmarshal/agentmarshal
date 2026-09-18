Готово. Я сверил каждое добавленное утверждение с кодом в дереве. Diff меняет только документацию и ничего не нарушает.

**Публикация review output (UPGRADING.md)**
- В `src/agentmarshal/journal/review.py:881` вывод ревьюера (`prose=raw_output`) передаётся в `submit_review` всегда, без условий. Этот вывод пишется в журнал как артефакт для любого review, записанного через `agentmarshal review`, в том числе для review по finding. Настройки, которая это отключает, нет, так что «No setting turns this off» — верно.
- Про 0.3.0: исходников тега v0.3.0 в snapshot нет. Утверждение совпадает с записью в CHANGELOG о 0.3.0 (стр. 281–282): вывод сохранялся во временный файл, если verdict отклонён или записанный verdict называет finding. Для записанного review условие одно — verdict называет finding, как и написано в diff.
- Все три варианта для оператора рабочие:
  - adapter управляет только stdout, а stderr и так уходит во временный файл;
  - в sidecar `review` поддерживается (`docs/sidecar.md:401`);
  - `submit-review` сохраняет prose только при `--prose` (`submit_review.py:70`).

**doctor и init**
- Три проверки помечены `precondition=True` (`doctor.py:224-240`). Невыполненная печатается как `TODO`. Summary считает «N precondition(s) left to the operator» вместо «all N checks passed», и exit 1 бывает только при настоящем `FAIL` (`cli.py:407-432`).
- `init` печатает список preconditions в stdout (`cli.py:371-387`).

**README Status**
- Каждый из четырёх пунктов «New in 0.4.0» совпадает с разделом CHANGELOG о 0.4.0: CR-085/086, CR-087–090, CR-091/096, CR-097/098.
- Номеров задач в тексте нет, так что лишних ссылок тоже нет.
- Предложение про sidecar из 0.3.0 оставлено как история.

**CI**
- Полный CI-прогон я не запускал: на запуск `pytest` нужно разрешение, а сессия неинтерактивная.
- Тестов, которые читают корневые README.md или UPGRADING.md, нет, а код diff не трогает. Поэтому pytest, ruff и mypy он затронуть не может.

Blocking и advisory findings нет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "cf746accc1fb1e5dd274ea4b07711a71933275ea", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
