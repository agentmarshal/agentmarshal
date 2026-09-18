Ревью CR-107 на коммите `c4c07d4` — **approved**, с одним advisory-замечанием. Тесты я не запускал: запуск pytest требовал разрешения, в этой сессии его не было. Всё ниже проверено чтением кода.

**Что сходится:**
- **Workflow.** Gate-job в `.github/workflows/agentmarshal-governance.yml` теперь совпадает с `templates/github/agentmarshal-governance.yml`. Там есть `--without-review`, нет `continue-on-error`, есть комментарий «Required check (Variant 2), not the merge authority». Остальные отличия от шаблона: `setup-uv`/`uv sync --locked`, запуск через `uv run` и запуск gate из PR-checkout вместо pinned release. Каждое помечено комментарием «Repository-specific», у последнего честно написано, что это ослабляет «enforced here». Утверждение про maintainer-run merge authority совпадает с `am-merge` из `docs/self-hosting-workflow.md`.
- **Невидимые записи.** Мой grep по `docs/` и `openspec/changes/archive/` на `backlog|register|not published|separate RFC|release plan` больше не находит ссылок на неопубликованные записи. Два оставшихся упоминания «register» (proposal 005 и ADR-0009) описывают реестр adopter'а, читателя туда не отсылают.
- **Числа CR-102.** В текущем дереве 12 вызовов `load_task_for_record` в 6 модулях: submit_review, cli ×4, complete ×3, acceptance, review ×2, session. Восемь собственных проверок `state != "open"`, перенос проверки `reopen` в guard и pre-run refusal у finding review со времён CR-101 подтверждает и финальное ревью CR-102 (`01M2RZR82…-review.md`): «Diff удаляет восемь проверок», «уже был со времён CR-101». Перечисление в design.md теперь сходится с «twelve in six modules».
- **ADR-0009 и ADR-0010.** У обоих появился раздел «Example (non-normative)». Ссылки ведут на реально существующие `docs/sidecar.md#research-findings-loop` и `.agentmarshal/extensions/openspec.toml`.
- **Тест.** `test_sidecar_complete_refuses_a_closed_task_without_writing` действительно ловит guard в `cli.py:881`. Без него `run_gate` отказал бы с другим текстом, а строку `is not open (state: done)` в stderr gate не печатает. Кроме того, тест проверяет, что журнал не изменился и что `validate` проходит.

**Что проверить не удалось:** acceptance 2 и 3 требуют процитировать команды и их результаты в commit message. Commit message мне не передали, а snapshot — не git-репозиторий, так что эти условия остаются непроверенными.

**Advisory-замечание.** В `docs/migration-v1-to-v2.md:81` изменение contract schema, из-за которого gate будет отклонять задачи с пустым acceptance, теперь названо «not been designed or scheduled yet». Это расходится с двумя местами:
- заголовок того же пункта: «Gate enforcement is planned»;
- `docs/overview.md:166`: там «Contract-extension RFC» стоит в списке «designed but **not active**».

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c4c07d4f087265e00a849b1d3b8a6e913af9aaac", "verdict": "approved", "findings": [], "advisory_findings": ["migration-schema-change-status-contradicts-overview"]}
AGENTMARSHAL_VERDICT_END
