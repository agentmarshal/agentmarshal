Ревью CR-107 на `c42617e` закончено. Всё, что можно проверить по snapshot, сходится с контрактом, блокирующих находок нет. Тесты запустить не удалось: `uv run pytest` требует approval. Поэтому новый тест я проверил только чтением кода.

**Что проверил:**
- **Workflow.** В `.github/workflows/agentmarshal-governance.yml` gate теперь запускается с `--without-review` и без `continue-on-error`. Комментарий к job совпадает с шаблоном: required check, но не merge authority. От `templates/github/agentmarshal-governance.yml` workflow отличается в трёх местах: `uv` вместо `pip install`, ветка `master` и запуск из собственного checkout PR. Каждое отличие прокомментировано. Слова о maintainer-run merge authority подтверждаются `docs/github-enforcement.md:43-47`.
- **Числа в writer-refuses-a-closed-task.** В `src/` ровно 12 вызовов `load_task_for_record` в 6 модулях: `submit_review`, `complete`, `acceptance`, `session`, `review` и `cli`. Путей со своей копией проверки восемь: 3 в CLI, 1 в `acceptance`, 3 в `complete.py` и 1 у finding-review. Что finding-review уже отказывал до запуска reviewer'а, подтверждает архивная спека CR-101 (`review-binds-to-a-finding/specs/findings-review/spec.md:65-70`). Proposal и design теперь говорят одно и то же.
- **ADR-0009 и ADR-0010.** Секции с примером помечены как non-normative. Обе ссылки ведут на существующие цели: `docs/sidecar.md#research-findings-loop` и `.agentmarshal/extensions/openspec.toml`.
- **Тест sidecar `complete`.** Он действительно закрепляет guard: текст `is not open (state: …)` выдаёт только guard в `status.py:150` (и ещё `brief.py:293`, который `complete` не вызывает). Если убрать guard, stderr будет другим, и тест упадёт. Функции-хелперы и сигнатуры, которые он использует, существуют.
- **Ссылки на невидимые записи.** В `docs/` и `openspec/changes/archive/` таких ссылок я больше не нашёл. Упоминания «register» в proposal 005 и ADR-0009 рассказывают про реестр adopter'а, а не отсылают читателя к нему.

**Что не проверил:** snapshot не является git-репозиторием. Поэтому я не видел ни commit message с цитатами grep'а и подсчётов, ни merge diff'а CR-102. Числа сверены только с текущим кодом.

`docs/proposals/005-research-findings-have-no-record-type.md:42`: «the in-toto Statement projection this waited on is next in line» по-прежнему ссылается на порядок работ из неопубликованного плана. Прежнее «scheduled in the current release plan» просто стало менее явным.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c42617e200f27cb96a7954e0bd4793da7bed8225", "verdict": "approved", "findings": [], "advisory_findings": ["proposal-005-next-in-line-implies-unpublished-plan"]}
AGENTMARSHAL_VERDICT_END
