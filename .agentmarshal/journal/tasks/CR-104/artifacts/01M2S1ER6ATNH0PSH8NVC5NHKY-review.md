Ревью готово, вердикт **approved**. Тесты, ruff и mypy запустить не получилось: окружение потребовало подтверждения на запуск. Поэтому всё ниже проверено только чтением кода.

**Общая часть launcher'а (критерий 1).** `_launch_review_tail` (`src/agentmarshal/journal/review.py:810`) теперь делает всю общую последовательность: temp dir, prompt file, запуск reviewer'а, diagnostics, decode, parse, проверку subject, `submit_review`, ветку с artifact-ref и `LaunchedReview`. Оба пути вызывают её, своих копий больше нет. Поведение совпадает с прежним:
- **Finding path.** Prompt и contract, как и раньше, строятся до temp dir, а в tail передаются через `lambda _snapshot: (prompt, contract)`. `reviewed_commit` уходит `None`, как было. Текст ошибки при несовпадении subject тот же.
- **Commit path.** Contract читается из snapshot внутри temp dir, как и раньше. Раньше `_parse_verdict` звался с `expected_field=None`, теперь с `"reviewed_commit"`. Меняется только сообщение ветки `len(bindings) != 1`, но на commit path она недостижима: `reviewed_commit` входит в `_VERDICT_REQUIRED`, и при его отсутствии раньше срабатывает проверка missing fields. Добавленная проверка `subject_field != "reviewed_commit"` на этом пути всегда ложна. Текст «reviewed_commit does not match commit» не изменился.

**Правило identity (критерий 2).** `_actor_git_identities` и `finding_reviewer_identity_refusal` переехали в `actors.py` почти без изменений. Литералы заменены на `SOURCE_GIT_IDENTITY`, `SOURCE_ACTORS_TABLE` и `SOURCE_OVERRIDE`. Значения первых двух видны в том же файле. Значение `SOURCE_OVERRIDE` я не проверял, но старый код его не использовал, так что его совпадение с `"override"` — единственное непроверенное место в этом переносе. В `gate.py` копии не осталось, а launcher больше не импортирует gate.
- Новый импорт `agentmarshal.project` из `actors.py` цикла не создаёт: `project` импортирует только `__version__`.
- Импорты `read_project_file` и `project_file_path` в `gate.py` не стали лишними, они ещё используются в строке 474.

**Строка про независимость (критерии 3 и 4).** Строка gate'а о независимости reviewer'а совпадает байт в байт: и refusal, и fallback-текст в `check()` не изменились. Существующие тесты не тронуты. В `tests/test_findings.py` добавлен один новый тест. Его fixture сопоставляет `researcher` → `recorder@test.invalid`, так что тест проверяет то, что заявляет.

Противоречий с ADR-0006 и ADR-0009 (Decision 3) не нашёл.

Замечание (advisory), не блокирует:
- **CR104-A1.** У `_launch_review_tail` (`src/agentmarshal/journal/review.py:810`) subject передаётся дважды: `expected_subject_field` и `expected_subject`, плюс `reviewed_commit` или `reviewed_finding`. Вызывающий может передать несогласованные значения, например проверить verdict против одного subject, а записать review с другим. Если выводить одно из другого, такое станет невозможным.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ae7a497aa57b67f2570a4f2e087552ffb1ff2250", "verdict": "approved", "findings": [], "advisory_findings": ["CR104-A1"]}
AGENTMARSHAL_VERDICT_END
