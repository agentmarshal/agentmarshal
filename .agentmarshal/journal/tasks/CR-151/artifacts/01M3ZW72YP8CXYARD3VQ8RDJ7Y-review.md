Проверил диff статически: модуль, доктор, тесты, дельта-спек и архив. Выполнить `uv run pytest / ruff / mypy` в этой песочнице не дали (команды требуют одобрения), поэтому критерий «the full CI sequence passes» я подтвердить исполнением не могу — ниже статический разбор.

**Что сходится с контрактом**

- `src/agentmarshal/settings.py:31-44` — ключи и дефолты совпадают с ADR-0022 §6 и ADR-0016 решение 3 (семь классов), 4 (порог 3) и ADR-0018 решение 2 (`false`), проверил по `docs/adr/`.
- Отсутствие и невалидность различаются членством ключа (`settings.py:68`, `:80`, `:111`, `:124`), `null` падает как present — ровно как требует критерий 3. `bool` отбрасывается до `int` (`settings.py:116`).
- Контрольные символы берутся из единого предиката: `reject_control_characters` → `forges_rendered_text` (`journal/records.py:512`), так что `\t` (Cc) и bidi-марки отбиваются, а `repr` в сообщениях их экранирует (Cc/Cf/Zl/Zp/Co не `isprintable`) — заявление design.md держится.
- `doctor.py:131-148` даёт три независимые проверки; порядок `except ProjectSettingsError` перед `except (OSError, ValueError)` корректен, так как `ProjectSettingsError` — подкласс `ValueError`.
- Все 12 сценариев дельта-спека покрыты тестами с называющими их докстрингами; `openspec/specs/project-settings/spec.md` отличается от дельты только заголовком и `ADDED Requirements` → `Requirements`, то есть архив сделан командой, а не руками, и `.openspec.yaml` соответствует другим архивным change'ам.
- Потребителей нет: `agentmarshal.settings` импортируется только из `doctor.py` и тестов.

**Advisory-замечания**

`doctor-ok-detail-repeats-key` — в `src/agentmarshal/doctor.py:147` деталь успешной проверки собирается как `f"{key}: {value!r}"`, а рендерер в `src/agentmarshal/cli.py:424` печатает `f"{status}: {result.name} — {result.detail}"`, где `result.name` уже равен `project setting review.finding_classes`. Строка выходит как `OK: project setting review.finding_classes — review.finding_classes: ('correctness', 'contract-mismatch', ...)`: ключ назван дважды, а значение показано сырым Python-репром кортежа, тогда как все соседние проверки печатают прозу («project schema 1 is supported»).

`control-char-entry-not-named` — в `src/agentmarshal/settings.py:101` вызов `reject_control_characters(entry, f"{what} entry")` не подставляет сам `entry`, хотя две соседние ветки (`settings.py:91`, `:96`) его эхом выводят, и `validate_scope_entry` в том же модуле правила (`journal/contracts.py:132`) передаёт `f"{what} entry {entry!r}"`. При словаре из нескольких классов оператор получает «... entry must not contain control characters» без указания, какая именно запись виновата; design.md сам отмечает, что `repr` делает эхо безопасным, так что ограничение здесь непреднамеренное.

Блокирующих дефектов не нашёл.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "59b8847b2e881b35afac91dafc5966707bd4c62b", "verdict": "approved", "findings": [], "advisory_findings": ["doctor-ok-detail-repeats-key", "control-char-entry-not-named"]}
AGENTMARSHAL_VERDICT_END
