Сверил каждое добавленное утверждение с кодом этого дерева. Тег v0.3.0 здесь недоступен: в snapshot нет `.git`. Поэтому поведение 0.3.0 я проверял по архивным openspec-изменениям в репозитории.

**Что подтвердилось:**
- **Прозу коммитят вместе с журналом.** `_launch_review_tail` передаёт `prose=raw_output` в `submit_review` для каждого вердикта, который он записывает. Настройки, которая это отключает, нет: в коде есть только переменные `AGENTMARSHAL_ACTOR`, `AGENTMARSHAL_PIPELINE_OK_SHA` и `AGENTMARSHAL_REVIEWER_CMD`. `submit-review` сохраняет прозу, только когда передан `--prose`.
- **В 0.3.0 была временная копия, и только при названных findings.** Так пишет `openspec/changes/archive/2026-09-07-retire-review-temp-copy/proposal.md`: «copies the same bytes into the system temp directory on every accepted verdict with findings».
- **Вывод `doctor`** (`src/agentmarshal/cli.py:410-433`). Невыполненное предусловие печатается как `TODO`. Сводка выглядит как `N precondition(s) left to the operator`. Код выхода 1 бывает только при настоящем сбое проверки, а строка `all N checks passed` печатается, только когда всё выполнено.
- **Три новые проверки** (`doctor.py:224-240`): recorded actor, reviewer command placeholders и CI validate definition. Раньше проверок было четыре, об этом говорит `proposal.md` в CR-098.
- **`init`** печатает список предусловий в stdout (`cli.py:371-388`).
- **Status в README.** Все четыре пункта «New in 0.4.0» соответствуют разделам CHANGELOG. Номера задач не упоминаются, фраза про sidecar из 0.3.0 оставлена как история.
- Ни один тест не ссылается на текст `README.md` или `UPGRADING.md`. Полную CI-последовательность я не запускал: `uv` создал бы `.venv`, а ревьюер read-only.

Одно замечание, не блокирующее:

UPGRADING.md:60: фраза «writes what the reviewer command prints into the journal» неточна. В артефакт журнала попадает только stdout ревьюера (`_run_reviewer` возвращает `result.stdout`). Stderr при успешном запуске сохраняется вне журнала через `_keep_diagnostics`. Точнее было бы «prints on standard output». От этого зависит совет «shape what the reviewer command prints in its adapter».

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "cf746accc1fb1e5dd274ea4b07711a71933275ea", "verdict": "approved", "findings": [], "advisory_findings": ["upgrading-prose-stdout-only-imprecise"]}
AGENTMARSHAL_VERDICT_END
