Прогнал статический разбор: прочитал `capture.py`, `gate.py`, `cli.py`, новые тесты, архивированный change и смёрженный spec. Исполнить тесты в этой песочнице не удалось (Bash блокирует запуск python/uv/pytest), поэтому acceptance «the full CI sequence passes» я проверить **не смог** — говорю об этом прямо, вывод ниже основан на разборе кода, а не на зелёном прогоне.

## Что проверено и сходится

- `decode_diff_per_file` восстанавливает поток байт без потери кадрирования: `_DIFF_BOUNDARY` — zero-width lookahead, секции сохраняют свой `\n`, `"".join` склеивает точно; lossy-путь делит по `b"\n"` и склеивает по `"\n"`, то есть разбивка строк сохраняется. Чистый diff идёт ровно тем же путём, что и до изменения.
- Наблюдаемость бага 026/037 действительно снята: секция `blob.bin` падает в lossy-декод локально, а `secret.py` декодируется строго и сканируется.
- `must_name` соответствует design.md: `not in_hunks or line.startswith(b"+")` — удалённый бинарник (`-` внутри хунка) не попадает в список, добавленный и pre-hunk-заголовок попадают. Проверил на фикстурах всех трёх тестов вручную — результаты совпадают с ассертами.
- Переход `splitlines()` → `split("\n")` разобрал на реальной фикстуре `bytes(range(256)) + token`: git режет только по `0x0a`, хунк `@@ -0,0 +1,2 @@` закрывается ровно двумя `+`-строками, токен попадает в `added_text`, перед `ghp_` стоит U+FFFD (граница слова держится). Со старым `splitlines()` фрагмент после `\x1e` обнулял оба счётчика — тест небессмысленный. Регрессии по CRLF нет: остающийся `\r` — не-словесный символ, `\b` на конце токена сохраняется, а заголовки git не несут `\r`.
- Существующая гарантия отказа жива: `test_gate_refuses_non_utf8_git_output` опирается на `_run_git`, который после рефакторинга всё ещё строго декодирует stdout при `returncode == 0` (`git diff --name-status` выходит с 0), сообщение «non-UTF-8» сохраняется.
- Маскирование: `render_undecodable_files` гоняет каждое имя через `safe_path`; `AKIAIOSFODNN7EXAMPLE.bin` → `<aws-access-key-id>.bin`, marker-каталог → `<private marker #1>`. Сам lossy-декодированный diff никуда не печатается. Exit-код команды завязан только на `hits`, гейт не трогает `violations`.
- Все 10 сценариев delta-спеки покрыты тестами с называющими их docstring'ами; change архивирован, требование вмерджено в `openspec/specs/leak-scan/spec.md` без дублей.

## Замечания (не блокирующие)

`header-name-quoted-prefix-dead`: в `src/agentmarshal/journal/capture.py:434` ветка `_header_name` для C-quoted пути собирает `token = '"b/' + destination`, после чего `token[2:] if token.startswith("b/")` не срабатывает никогда — ведущая кавычка делает проверку ложной. Имя в предупреждении выходит как `"b/x y"`, с префиксом и кавычками, хотя docstring обещает «the destination token». Путь достижим только как fallback для секции без пригодного `+++`, и design.md заранее записывает «worst case is a wrong name in a warning», поэтому это косметика, а не дефект поведения.

`escape-literal-in-docstring`: в `tests/test_capture.py:640` и `tests/test_leak_scan.py:321` docstring'и не raw, а текст содержит `\x0c` — Python разворачивает это в настоящий form feed, так что объяснение вместо литерала `\x0c` несёт управляющий символ. Смысл сценария в первой строке не страдает, но пояснение стоило бы сделать raw-строкой.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "d3c200db9dce8c000f8484c7932171c544076a43", "verdict": "approved", "findings": [], "advisory_findings": ["header-name-quoted-prefix-dead", "escape-literal-in-docstring"]}
AGENTMARSHAL_VERDICT_END
