Разобрался. Ниже — то, что нашёл.

## Что проверил

Прочитал `display.py`, `status_view.py`, `report.py`, путь `_run_status`/`_run_report` в `cli.py`, предикат `forges_rendered_text` в `records.py`, парсер контракта, оба новых теста и изменённый pin-тест, дельту и применённую спеку, AGENTS.md и ADR-0015.

Содержательно реализация закрывает задачу. Покрытие полное: в списке задач экранируются `task_id` и `contract.title`, в per-task view — `task_id`, `title`, каждая запись scope, строка acceptance-следа, обобщённая строка записи и целиком строка, которую вернул renderer; в `format_report` — `task_id` и оба `usage`. Табы остаются структурой, потому что их добавляет форматтер, а не экранируемое значение. `state` и `decision` действительно производные от закрытых множеств (`_RECORD_TYPE_STATES`, литералы в `_task_report`), так что их неэкранирование обосновано. Сообщения об ошибках в `status` строятся только из путей и валидированного `task_id` — там record-текст не протекает. Я отдельно проверил, что `title` и `scope` в `parse_contract_text` не проходят `reject_control_characters`, то есть экранирование этих двух полей нужно не только для старых записей — это настоящая дыра, и она закрыта. Pin-тест консистентен: проекция состояний допускает `completed`(13) → `reopened`(14) → `abandoned`(15) → `session`(16), а `completed_finding` требует схемы 4, что `_minimum_schema` ставит сам.

Оговорка: прогнать CI-последовательность я не смог — запуск `uv run ruff check` / `mypy` / `pytest` в этой песочнице отклоняется, одобрения нет. Критерий «полная CI-последовательность проходит» я не верифицировал, только статически: длины строк, неиспользуемых импортов и типовых проблем под mypy strict не вижу (литералы dict выводятся как `dict[str, object]` из контекста параметра `TaskStatus.records`).

## Findings

**applied-spec-purpose-hand-edited** — абзац `## Purpose` в `openspec/specs/record-text-safety/spec.md:3-14` переписан руками, а не командой archive. AGENTS.md:20-21 говорит категорично: «never edit a file under `openspec/specs/` by hand». `design.md:52-58` это признаёт и называет «the one permitted hand edit», но обоснование там неверно: «The delta format carries no Purpose section» — в этом же репозитории 11 архивных дельт несут `## Purpose`, включая дельту, которой эта самая capability была создана (`openspec/changes/archive/2026-09-24-narrow-the-forgeable-text-rule/specs/record-text-safety/spec.md:1`), и именно оттуда взялся прежний текст Purpose. Дельта этого изменения секции Purpose не несёт вовсе — то есть штатный путь даже не пробовали. В результате применённая спека содержит текст, которого нет ни в одной дельте, и её больше нельзя воспроизвести из архива — ровно то свойство, на котором держится spec-driven репозиторий. Починка: либо положить обновлённый `## Purpose` в дельту и перезаархивировать (проверив, применяет ли команда Purpose к существующей capability), либо откатить ручную правку и назвать устаревший Purpose departure'ом в отчёте — решение за оператором, а не за реализатором.

**unreachable-astral-escape-branch** (advisory) — ветка `\UXXXXXXXX` в `src/agentmarshal/journal/display.py:23` недостижима. Отказываемое множество — это `Cc` (U+0000–001F, U+007F–009F), `Cs` (U+D800–DFFF), `Zl` (U+2028), `Zp` (U+2029) и bidi-контролы из `_BIDIRECTIONAL_CONTROLS`; все они лежат в BMP, и по политике стабильности Unicode новых там не появится. Значит `codepoint <= 0xFFFF` всегда истинно, а тест `test_what_the_write_refuses_the_display_escapes`, который по условию «derives its cases from the rule's own definition», эту ветку покрыть не может ни при каком Unicode. Код безвреден и честно defensive, но и proposal, и дельта, и применённая спека описывают форму вывода, которая не возникает — стоит либо сказать в design.md, что ветка страховочная и недостижима, либо убрать её вместе с упоминанием в спеке.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "4dae34257f6faf222a3b218580ab7a29b38b416a",
  "verdict": "changes_required",
  "findings": ["applied-spec-purpose-hand-edited"],
  "advisory_findings": ["unreachable-astral-escape-branch"]
}
AGENTMARSHAL_VERDICT_END
