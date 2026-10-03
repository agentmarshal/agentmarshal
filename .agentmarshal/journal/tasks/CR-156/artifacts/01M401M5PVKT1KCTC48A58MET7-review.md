## Review of CR-156 (commit `680d3cb9e5218132311be2c72c34bb92c00c74d4`)

Что проверил (чтение, без запуска — в этой песочнице нет ни `uv`, ни исполняемого Python, так что CI-последовательность из критерия 5 я подтвердить прогоном не смог; проверил статически: длины строк под `line-length = 88`, отсутствие устаревших assert'ов на изменённый help-текст, импорты в тестах, типы под `mypy --strict`):

- **Контракт ↔ спека.** Заголовок MODIFIED-требования (`### Requirement: outbox check scans what would be sent and refuses by exit status`) совпадает с существующим в `openspec/specs/outbox/spec.md:89`, новые требования пришли как ADDED, каждое встречается в итоговой спеке ровно один раз, change лежит под `openspec/changes/archive/2026-10-03-outbox-send-and-status/` с proposal/design/tasks/delta.
- **Покрытие сценариев.** 36 сценариев в `openspec/specs/outbox/spec.md` — 36 тестовых docstring'ов в `tests/test_outbox.py`, имена совпадают один к одному.
- **`send`.** `_run_check` вызывается буквально первым (`src/agentmarshal/outbox.py:562`), staged-множество читается через `git diff --cached --name-status -z` с обеими половинами rename/copy (`:527-556`, парсинг формата `status\0path\0` и `R100\0old\0new\0` корректен, unborn-HEAD git сам сравнивает с пустым деревом), стейджится только `.agentmarshal/upstream` с `--force`, ровно один `git commit`, печать `rev-parse HEAD`; сети нет. `project_root` действительно всегда git-root — `initialize_project` пишет `project.json` в `find_git_root` (`src/agentmarshal/project.py:397,438`), поэтому префикс `.agentmarshal/upstream/` сопоставим с выводом git напрямую.
- **`status`.** sha256 в lowercase hex, регекс `_SOURCE_LINE` принимает и голую, и markdown-форму — сверил с реальными дайджестами (`docs/proposals/023-...md:3`), non-regular и нечитаемые записи дают non-zero, отсутствующий/нечитаемый индекс и отсутствующий outbox — сообщения.
- **Carried advisory.** `_shown_name` (`os.fsencode` → `backslashreplace`) применяется ко всем именам в `check`, `send` и `status`, и именно эта escaped-форма идёт в скан имени и в `safe_path`, так что маркер в не-UTF-8 имени остаётся замаскированным.

Блокирующих дефектов не нашёл. Ниже — advisory.

`status` различает index-записи только по номеру строки (`src/agentmarshal/outbox.py:653-697`): если на одной строке два `Source:`-дайджеста и один из них совпал с файлом, второй уже никогда не попадёт в список «claims no outbox file» (строка в `matched`), а если оба не совпали и одинаковы — строка напечатается дважды. Дизайн при этом говорит «each occurrence is one index entry».

`send` на свежем outbox'е (только scaffolded `README.md`, ни одной находки) делает коммит «outbox: findings batch» с одним README: `check` рапортует «0 draft(s) checked; all conform», а защита от пустой партии смотрит только на то, застейджено ли хоть что-то под outbox'ом (`src/agentmarshal/outbox.py:599-612`).

Если `git commit` упадёт (хук, незаданная identity), `git add --force` уже отработал и партия остаётся в индексе оператора (`src/agentmarshal/outbox.py:598-620`) — команда отказала, но индекс изменила; обещание «commits nothing» формально выполнено, откат — нет.

`tests/test_outbox.py:927-936` (`test_outbox_help_lists_both_subcommands`) не обновлён: он по-прежнему проверяет только `new` и `check`, так что появление `send` и `status` в help группы не покрыто ничем — регистрация из критерия 5 проверяется лишь косвенно, через вызовы `main`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "680d3cb9e5218132311be2c72c34bb92c00c74d4",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "advisory-status-line-identity-collapses-two-source-entries",
    "advisory-send-commits-a-readme-only-batch",
    "advisory-send-leaves-the-batch-staged-after-a-failed-commit",
    "advisory-help-test-still-names-only-two-subcommands"
  ]
}
AGENTMARSHAL_VERDICT_END
