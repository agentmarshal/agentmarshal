Проверил реализацию, delta-спеку, архив и тесты статически. Выполнить CI-последовательность в этом окружении не удалось — здесь разрешены только read-only операции с файлами (запуск `python3`/`uv` требует approval), поэтому критерий «the full CI sequence passes» я подтвердить не могу; всё остальное проверено по файлам.

Что проверено и сошлось:

- Все 8 сценариев `outbox status`, 6 сценариев `outbox send` и новый сценарий `check` из delta имеют тест, чей docstring дословно повторяет заголовок сценария (`tests/test_outbox.py:603-936`).
- MODIFIED-заголовок `### Requirement: outbox check scans what would be sent and refuses by exit status` совпадает с существующим в `openspec/specs/outbox/spec.md:89`; каждое требование встречается в итоговой спеке ровно один раз; `openspec/changes/` содержит только `archive/`.
- `cli.py` не тронут и держит только hook (`cli.py:348`, `cli.py:1235`); регистрация обеих команд — в `src/agentmarshal/outbox.py:100-111`.
- Инвариант «что проверено, то и уходит» держится: `check` отказывает на любой нерегулярной записи и на нечитаемом файле, поэтому вложенный каталог в outbox не может попасть в commit непроверенным.
- `project_root` действительно git-worktree root (`project.py:397` — `init` привязывается к `find_git_root`), поэтому сравнение staged-путей с префиксом `.agentmarshal/upstream/` корректно; `-z` снимает quoting, обе половины rename учтены (`outbox.py:544-556`).
- Сети нет: только `subprocess` c `git` и `hashlib`.

Теперь то, что стоит знать человеку.

Идентичность index-записи в `outbox status` — это номер строки, а не само вхождение: `matched` в `src/agentmarshal/outbox.py:672` наполняется номерами строк, и финальный цикл `src/agentmarshal/outbox.py:695-697` пропускает запись, чья строка уже «засчитана» другим вхождением. Если в одной строке индекса стоят два `Source:`-дайджеста и первый совпал с файлом, второй — ничей — не будет напечатан, хотя и design.md, и требование говорят «each occurrence is one index entry» и «SHALL print each index entry that claims no outbox file». На реальном формате (`docs/proposals/*.md` — один `Source:` на строку) не воспроизводится, потому advisory.

`outbox send` делает commit с сообщением `outbox: findings batch` даже когда отправлять нечего по существу: пустой batch определён как «ничего не staged под outbox», а не «нет драфтов», поэтому сразу после `init` команда пишет «0 draft(s) checked; all conform» и коммитит один только scaffold-README (`src/agentmarshal/outbox.py:607-616`). Спеке это не противоречит — README действительно «leaves with the batch» — но оператор получает «батч находок» без находок.

Единственное имя в группе, которое не прошло через `_shown_name`, — путь самого outbox в сообщениях об ошибке чтения каталога: `safe_path(str(outbox), markers)` в `src/agentmarshal/outbox.py:418` и `src/agentmarshal/outbox.py:666`. Если корень проекта содержит не-UTF-8 байты, `str(outbox)` несёт surrogate-символы и `print` падает с `UnicodeEncodeError` — ровно тот класс падения, который CR-156 убирал. Требует одновременно OSError на `iterdir()` и не-UTF-8 путь проекта, поэтому advisory, а не блокер; буквально критерий про «имя файла в outbox» это не нарушает.

Переписанный `## Purpose` из delta не доехал до итоговой спеки: `openspec/changes/archive/2026-10-03-outbox-send-and-status/specs/outbox/spec.md:5-13` описывает capability уже с `send` и `status`, а `openspec/specs/outbox/spec.md:4-8` по-прежнему говорит только про «a command that scaffolds a conforming draft, and a check». По AGENTS.md:21 `openspec archive` берёт Purpose только для новой capability, так что текст в delta оказался мёртвым, а поправить руками спеку тот же AGENTS.md запрещает — это вопрос к инструменту, не к реализации.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "680d3cb9e5218132311be2c72c34bb92c00c74d4", "verdict": "approved", "findings": [], "advisory_findings": ["status-index-entry-identity-is-the-line-number", "send-commits-a-readme-only-batch", "outbox-dir-path-printed-without-escaping", "delta-purpose-absent-from-shipped-spec"]}
AGENTMARSHAL_VERDICT_END
