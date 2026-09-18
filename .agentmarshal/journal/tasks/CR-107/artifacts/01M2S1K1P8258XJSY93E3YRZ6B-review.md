Всё, что можно было проверить в дереве, сходится с контрактом. Два пункта проверить не удалось, и одно замечание некритичное.

**Проверено и сходится:**
- **Workflow (`.github/workflows/agentmarshal-governance.yml`).** Строки `continue-on-error` больше нет. `--without-review` на месте (строка 65). Комментарий говорит, что job — required check, а не merge authority (строки 37–42). От `templates/github/agentmarshal-governance.yml` gate job отличается только в двух местах: uv вместо setup-python/pip и `uv run` при вызове. Оба отличия прокомментированы.
- **Числа в архиве CR-102.** «Twelve in six modules» совпадает с тем, что сейчас в дереве: 12 вызовов `load_task_for_record` в 6 модулях (session, cli ×4, review ×2, submit_review, complete ×3, acceptance). «Восемь путей с собственным отказом» совпадает с журналом ревью CR-102 (`01M2RZR82MHY3QWRNGRJF0DTBC`: «Diff удаляет восемь проверок `state != "open"`»). Там же подтверждено, что у `reopen` была своя проверка и что finding-review получил отказ до запуска ревьюера ещё в CR-101. Commit-review раньше шёл через `submit_review` и отказа не имел, так что формулировки в design.md верны.
- **Ссылки на невидимые записи.** Grep по `docs/` и `openspec/changes/archive/` на backlog, register, «not published» и похожие формулировки нашёл только повествовательные упоминания реестра адоптера (ADR-0009:23, proposal 005). Читателя они никуда не отсылают.
- **Секции примеров в ADR.** Обе ссылки живые: якорь `docs/sidecar.md#research-findings-loop` существует, `.agentmarshal/extensions/openspec.toml` тоже.
- **Тест.** Новый тест действительно фиксирует guard в `cli.py:881`. Если guard убрать, gate провалится со своим сообщением («already closed at base») в stdout. Тогда проверка `"task CR-001 is not open (state: done)"` в stderr упадёт.

**Не проверено:**
- Тесты я не запускал: запуск pytest требует одобрения, а его не дали. Вывод о тесте основан только на чтении кода.
- Сообщения коммита у меня нет: снапшот не git-репозиторий. Поэтому я не проверил, что команды grep и подсчёта вместе с результатами процитированы в нём, как требует контракт.

ADV-adr0009-example-overstates-usage (некритично): в `docs/adr/ADR-0009-research-findings-lifecycle.md:230-231` написано, что runbook «shows how this repository uses the lane in a sidecar journal». Но `docs/sidecar.md:404-427` — это обобщённая инструкция с `CR-001` и плейсхолдерами `<vendor>`/`<model>`, а не запись о том, как этот репозиторий пользуется lane.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "cc760104504fafc9cbf8746064e13984ef9aaef3", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-adr0009-example-overstates-usage"]}
AGENTMARSHAL_VERDICT_END
