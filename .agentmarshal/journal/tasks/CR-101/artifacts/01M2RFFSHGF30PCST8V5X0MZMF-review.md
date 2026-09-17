Прошёл по диффу целиком: launcher, gate-рефактор, общий resolver, CLI, оба prompt-шаблона, спеки и docs.

**Что проверено и сходится:**

- **Byte-стабильность commit-prompt.** `_REVIEW_PROMPT` разбит на `{prose_instruction}` + `{verdict_protocol}`, но рендер совпадает символ в символ с прежним текстом — `test_prompt_without_named_material_is_the_prompt_written_before_schema_2` пройдёт с неизменённым ожиданием.
- **Byte-стабильность findings-транскрипта gate.** `finding_reviewer_identity_refusal(..., launching=False)` возвращает ровно те же три строки, что печатала прежняя ветка `if not recorder_identities / else`, в том же порядке PASS/FAIL.
- **Resolver ровно один.** `artifact_path` живёт в `artifacts.py`, `gate.py:244` и `review.py:712` держат один и тот же объект функции; `_artifact_path` из `gate.py` исчез.
- **Парсер verdict.** Для finding-пути `required` теряет `reviewed_commit`, `bindings` требует ровно одного из двух полей, `unknown` считается от `required | subject_fields | _VERDICT_OPTIONAL` — verdict с обоими полями и verdict без них одинаково отвергаются; commit-путь поведенчески не тронут, включая текст сообщения о пропущенном `reviewed_commit`.
- **Pre-run отказы** (не-latest finding, закрытая задача, непустой scope, зависимый reviewer) все стоят до `_verified_finding_artifacts` и до `_run_reviewer`; дрейф и «нечего верифицировать» — до запуска.
- **Инъекция verdict через артефакт** закрыта: `_parse_verdict` сравнивает строку целиком (`line == _VERDICT_BEGIN`), а каждая встроенная строка несёт `| `. Newline в `ref`/`summary` невозможен — `_reject_control_characters` в `records.py:487`.
- **Sidecar.** `require_host=args.reviewed_finding is None` плюс `journal_root.parents[1]` как project_root — finding-review действительно решает по sidecar-евиденции без досягаемого host, и docs/sidecar.md это теперь говорит.
- Все сценарии обеих спек (`findings-review`, `reviewer-adapter`) имеют тест, чей docstring их называет; «a task with no amendments is unchanged» не осиротел — он остался за `tests/test_brief.py:70`.

Блокирующих дефектов не нашёл. Два advisory ниже.

design.md:51 объявляет решение «Binary and **oversized** artifacts are named, not embedded», но `_finding_review_prompt` (review.py:263-281) опускает содержимое только по `UnicodeDecodeError` — порога размера нет нигде, и Non-Goals/Risks того же документа прямо говорят, что лимит не изобретается; расхождение с собственным решением не записано как departure, хотя acceptance-критерий 1 этого требует.

review.py:49 задаёт `_ARTIFACT_CONTENT_PREFIX = "|"`, а review.py:85 вшивает тот же символ литералом в объяснение внутри `_FINDING_REVIEW_PROMPT` — два написания одного ключа, ровно тот урок CR-100, который design.md цитирует в решении про общий resolver: смена константы молча делает объяснение в prompt неверным.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "06652af8e316cba4680e8fd639c5337fe8bfd201", "verdict": "approved", "findings": [], "advisory_findings": ["design-oversized-decision-unimplemented", "artifact-prefix-spelled-twice"]}
AGENTMARSHAL_VERDICT_END
