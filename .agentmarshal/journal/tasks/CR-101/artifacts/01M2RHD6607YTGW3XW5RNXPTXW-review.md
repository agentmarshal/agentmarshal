Прочитал контракт, ADR-0009/ADR-0006, обе спеки (дельту и опубликованную), реализацию и тесты. Проверил ключевые вещи статически: байтовую идентичность commit-промпта после выноса хелперов, байтовую стабильность транскрипта findings-lane после рефактора identity-проверки, порядок pre-run отказов, и соответствие закреплённого finding-промпта его pinned-тесту.

Что проверено и сходится:

- `_review_prompt` через `_prose_instruction()`/`_verdict_protocol()` рендерится байт в байт как раньше (сверил по символам, включая переносы внутри склеенных строк) — `src/agentmarshal/journal/review.py:210`.
- Рефактор `finding_reviewer_identity_refusal` сохраняет ровно одну строку `check(...)` с теми же байтами во всех трёх ветках гейта — `src/agentmarshal/journal/gate.py:106`, `src/agentmarshal/journal/gate.py:225`.
- Резолвер один: `artifact_path` в `artifacts.py`, оба вызывающих читают его, `_artifact_path` из `gate.py` исчез — `src/agentmarshal/journal/artifacts.py:17`.
- Все 13 сценариев `findings-review` и 2 сценария `reviewer-adapter` имеют тест, чей docstring их называет.
- Отказы до запуска ревьюера (не-последний finding, зависимая личность, непустой scope, закрытая задача, дрейф артефакта, нечего верифицировать) все срабатывают до `with tempfile...`, так что `prompt_output` действительно не создаётся.
- Защита от инъекции вердикта: `summary` и `ref` уже отвергают control-символы на записи (`records.py:468`, `records.py:479`), содержимое артефакта префиксуется — сентинелы в промпте только там, где их поставил лаунчер.
- `reviewed_finding` + `reviewed_contract` даёт schema 5, и `reviewed_finding` входит в `_RECORD_FIELDS["review"]` безусловно, так что запись валидна.
- Цикла импортов нет: `gate` не импортирует `review`.

Два замечания, не блокирующие.

Сценарий `a task with no amendments is unchanged` из `openspec/specs/contract-history/spec.md:35` требует, чтобы байт-в-байт совпадали и brief, и промпт; диф переименовал docstring `tests/test_review_launcher.py:1880` на новый сценарий findings-review, и половину про промпт теперь не называет ни один тест — `tests/test_brief.py:70` покрывает только brief.

Сообщение `reviewer verdict must name exactly one of reviewed_commit or reviewed_finding` в `src/agentmarshal/journal/review.py:556` при finding-ревью предлагает ревьюеру `reviewed_commit`, который промпт никогда не упоминал и который лаунчер отвергнет строкой ниже.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "717bae28d78129ed85e385b020d65c4544872039", "verdict": "approved", "findings": [], "advisory_findings": ["contract-history-prompt-scenario-unnamed", "finding-verdict-binding-message-names-commit"]}
AGENTMARSHAL_VERDICT_END
