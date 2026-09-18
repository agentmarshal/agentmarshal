Ревью CR-107 на коммите 651c921 закончено. Блокирующих замечаний нет, есть одно некритичное.

**Критерии контракта:**
- **Workflow:** gate теперь запускается с `--without-review`, `continue-on-error` убран, в комментарии сказано, что это required check, а не merge authority. От шаблона `templates/github/agentmarshal-governance.yml` job отличается только uv-окружением и вызовом через `uv run`. Оба отличия прокомментированы как repository-specific. Флаг `--without-review` есть в `src/agentmarshal/cli.py:232`.
- **Ссылки на невидимые записи:** в archived `adopter-small-defects/design.md` отсылки к backlog больше нет. Я прогнал grep по `docs/` и `openspec/changes/archive/` на backlog, register, «release plan», «the plan», «backlog item». Отсылок к неопубликованным записям не осталось. Совпадения «register» в proposal 005 и ADR-0009 про реестр adopter'а, это не отсылка. Правки в proposals 005, 016, 018 и README убирают ссылки на неопубликованный release plan.
- **Архив writer-refuses-a-closed-task:** цифры сходятся с текущим кодом. `load_task_for_record` вызывается 12 раз в 6 модулях: `session`, `submit_review`, `complete` ×3, `cli` ×4, `acceptance`, `review` ×2. Путей со своей проверкой `state != "open"` восемь. У `reopen` был свой predicate `state != "done"`, теперь он в guard (`status.py:138`). Pre-run refusal для finding review появился ещё в CR-101: в его spec есть сценарий «a closed task is refused». Новым он стал только для commit review.
- **Примеры в ADR-0009 и ADR-0010:** обе ссылки рабочие (`docs/sidecar.md#research-findings-loop` и `.agentmarshal/extensions/openspec.toml`), обе секции помечены «non-normative».
- **Тест:** новый тест проверяет строку `task CR-001 is not open (state: done)`. Её выдаёт только guard (`status.py:150`), поэтому если убрать guard перед `run_gate` (`cli.py:881`), тест упадёт.

**Что я не проверил:**
- Commit message мне не передан. Поэтому я не видел, процитированы ли в нём команда grep и команды подсчёта по merge diff CR-102, как требует контракт.
- Git-истории в snapshot нет, так что цифры по CR-102 я сверял с текущим исходником, а не с самим merge diff.
- Новый тест я не запускал: запуск pytest требовал подтверждения, которого в этой сессии нет.

**Некритичное замечание:**
Комментарии в gate job отличаются от шаблона там, где разницы в setup нет, и эти отличия никак не помечены. Это нарушает условие «differ only where this repository's setup genuinely differs» в `.github/workflows/agentmarshal-governance.yml`. Выпали пояснение «a review names a commit only after that commit exists, and it lands at completion» и «(reviewer identity + verdict)» в комментарии про Phase C, а «everything» заменено на «every check».

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "651c921754b7274c1517e8f6d11ca2ba067866c1", "verdict": "approved", "findings": [], "advisory_findings": ["CR107-A1-gate-comment-drift-from-template"]}
AGENTMARSHAL_VERDICT_END

Отдельно: MCP-серверы claude.ai Gmail, Google Calendar и Google Drive требуют авторизации в настройках connector'ов на claude.ai. Пока её нет, они недоступны. Для этого ревью они не понадобились.
