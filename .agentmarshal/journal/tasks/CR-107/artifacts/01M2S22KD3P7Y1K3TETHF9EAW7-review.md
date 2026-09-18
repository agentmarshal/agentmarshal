Нашёл одно блокирующее замечание и два рекомендательных, поэтому вердикт — changes_required.

Что проверено и в порядке:
- **Workflow.** Флаг `--without-review` на месте, `continue-on-error` убран, в комментарии сказано, что это required check, а не merge authority. Каждое отличие в настройке от `templates/github/agentmarshal-governance.yml` подписано «Repository-specific».
- **Числа CR-102.** Утверждение «twelve in six modules» совпадает с кодом: 12 вызовов `load_task_for_record` в 6 модулях. Восемь собственных проверок `state != "open"`, отказ `reopen`, который переехал в guard, и то, что у finding-review отказ до запуска был ещё с CR-101, — всё это совпадает с advisory-замечаниями ревью CR-102. Сам merge diff я не видел: git-истории в snapshot нет.
- **Примеры в ADR-0009 и ADR-0010.** Обе ссылки ведут на существующие цели: `docs/sidecar.md#research-findings-loop` и `.agentmarshal/extensions/openspec.toml`. Оба раздела помечены как non-normative.
- **Новый тест.** Он проверяет именно guard в sidecar-ветке: текст «is not open (state: done)» выдаёт только guard, `run_gate` его не выдаёт. Ещё тест проверяет, что журнал не изменился. Сам тест я не запускал: на `pytest` не дали разрешения.

Ещё я не смог проверить требование, чтобы grep-команда и числа были процитированы в commit message: самого commit message в материалах нет.

**Блокирующее:**

`unpublished-rfc-pointer-remains` — `docs/migration-v1-to-v2.md:81` отправляет читателя к «contract-schema change tracked by a separate RFC», но такого RFC нет ни в `docs/`, ни где-либо ещё в репозитории. То же с `docs/proposals/006-contract-repair-path.md:40` («the planned contract-schema RFC is the right vehicle»). Значит, не выполнено требование «no document under docs/ … does»: grep из задачи был слишком узким.

**Рекомендательные:**

`gate-runs-candidate-source-overstated` — в `.github/workflows/agentmarshal-governance.yml` job `gate` через `uv sync` запускает AgentMarshal из PR head. Тем самым scope, append-only, base-state и lifecycle проверяет код, который кандидат сам может менять. Комментарий «Repository-specific» об этом не говорит, а унаследованные фразы «Scope, append-only, base-state and lifecycle are enforced here» и «Safe to mark REQUIRED for what it does check» для этого репозитория звучат сильнее, чем есть на самом деле.

`gate-comments-paraphrase-template` — в том же workflow комментарии job `gate` пересказывают шаблон своими словами. Выпали фраза «a review names a commit only after that commit exists, and it lands at completion» и уточнение «(reviewer identity + verdict)». Эти отличия не связаны с настройкой репозитория и нигде не подписаны, а требование было, чтобы два job'а отличались только там, где отличается настройка.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "651c921754b7274c1517e8f6d11ca2ba067866c1", "verdict": "changes_required", "findings": ["unpublished-rfc-pointer-remains"], "advisory_findings": ["gate-runs-candidate-source-overstated", "gate-comments-paraphrase-template"]}
AGENTMARSHAL_VERDICT_END
