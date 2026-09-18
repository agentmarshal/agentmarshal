Проверил всё, что можно проверить по snapshot'у. Серьёзных проблем нет, одно мелкое замечание.

**Что сходится:**
- **Workflow.** Gate job теперь запускается с `--without-review` и без `continue-on-error`. Шапка комментария дословно совпадает с шаблоном: required check, not the merge authority. Отличия от шаблона (uv вместо pip, `master`, запуск из checkout'а PR вместо pinned release) помечены как `Repository-specific`. Ссылка на maintainer-run merge authority подтверждается описанием `am-merge` в `docs/self-hosting-workflow.md:61-71`.
- **Цифры CR-102.** «Twelve in six modules» совпадает с тем, что есть в дереве: 12 вызовов `load_task_for_record` в 6 модулях (`complete` ×3, `cli` ×4, `review` ×2, `acceptance`, `submit_review`, `session`). Восемь частных `state != "open"` проверок, pre-run refusal для finding review со времён CR-101 и перенос `reopen`'а в guard согласуются с последним ревью CR-102 (`change-record-misstates-prior-state`, ADV-3). Сам merge diff CR-102 недоступен: snapshot не git-репозиторий. Поэтому сверял с деревом и журналом, а не с diff'ом.
- **Ссылки на невидимые записи.** Грепом по `docs/` и `openspec/changes/archive/` (backlog/register/release plan/RFC/tracked) указателей на неопубликованные записи не нашёл. Оставшиеся упоминания «register» в `docs/proposals/005` и `ADR-0009` — это описание истории, а не ссылка на запись.
- **Примеры в ADR.** Оба помечены как non-normative. Якорь `#research-findings-loop` в `docs/sidecar.md` существует. Путь `../../.agentmarshal/extensions/openspec.toml` ведёт на рабочий манифест с `footprint`.
- **Тест.** Он действительно закрепляет guard в `cli.py:881`. Без guard'а gate тоже отказал бы, но с текстом «already closed at base» в stdout. Тест же проверяет «is not open (state: done)» в stderr, неизменность журнала и `validate`. Запустить тест не удалось: команда требует approval. Проверял чтением кода.
- **Commit message** в материалах нет. Поэтому процитированные греп и команды из acceptance 2 и 3 проверить не могу.

**Замечание (advisory):**

wf-gate-uncommented-drift — в `.github/workflows/agentmarshal-governance.yml:74-75` комментарий «Phase C» в gate job перефразирован относительно шаблона: выпало «(reviewer identity + verdict)», строки переразбиты. Это отличие без причины в настройке репозитория и без комментария. Acceptance требует, чтобы gate jobs отличались только там, где настройка действительно другая.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c4c07d4f087265e00a849b1d3b8a6e913af9aaac", "verdict": "approved", "findings": [], "advisory_findings": ["wf-gate-uncommented-drift"]}
AGENTMARSHAL_VERDICT_END
