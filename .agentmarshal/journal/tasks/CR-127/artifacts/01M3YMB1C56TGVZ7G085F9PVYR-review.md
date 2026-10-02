Прочитал весь затронутый код (`capture.py`, `gate.py`, `cli.py`), архивированный change, обновлённый `openspec/specs/leak-scan/spec.md` и новые тесты. Запускать Python в этой песочнице нельзя (permission denied), поэтому проверка статическая — но оба блокирующих вывода прослеживаются по коду построчно.

Что сделано правильно: раздельный декод по секциям `diff --git` (`_DIFF_BOUNDARY` — zero-width lookahead, заголовок остаётся в своей секции, многобайтовая последовательность не может пересечь границу, потому что граница — ASCII после `\n`); один helper `leak_scan_diff` на оба вызова и ни одной второй копии списка флагов; `--name-status` по-прежнему строго отказывает на не-UTF-8 путях, и это записано в design.md как намеренное; все шесть сценариев delta spec закрыты тестами, чьи docstring их называют; exit 0 на «только недекодируемое» и advisory-характер gate'а запинены.

Теперь то, что нужно исправить.

**1. Имена недекодируемых файлов печатаются мимо `safe_path`.** Хиты проходят через `safe_path(path, private_markers)` (`src/agentmarshal/journal/capture.py:592`, `:608`) — ровно для того, чтобы путь, который сам несёт секрет или private marker, не попал в вывод; это пинится тестами `tests/test_capture.py:380` и `:398`. Новый канал вывода этой маскировки не делает: `_undecodable_section_name` отдаёт сырое имя (`capture.py:501`), и оба вызывающих печатают его как есть — `WARN: leak-scan could not decode as UTF-8 … {unread}` в транскрипт gate'а (`src/agentmarshal/journal/gate.py:1190`) и `', '.join(undecodable)` в stderr команды (`src/agentmarshal/cli.py:1303`). Коммит, добавляющий `keys/AKIAIOSFODNN7EXAMPLE.bin` с не-UTF-8 байтами, напечатает значение ключа целиком в транскрипт, который люди читают и хранят; то же с путём `configs/internal.corp.invalid/blob.bin` и настроенным marker'ом. Это прямо противоречит четвёртому acceptance criterion («no private marker's value and no path carrying a secret is printed»). Маркеры в обеих точках уже под рукой (`markers` в `run_gate` и в `_run_leak_scan`), так что фикс — прогнать имена через `safe_path`, и добавить тест на этот канал.

**2. У недекодируемого файла реально просматриваются только байты до первого control-символа, хотя вывод утверждает обратное.** `scan_diff_for_leaks` режет текст через `unified_diff.splitlines()` (`capture.py:558`), а `str.splitlines` ломает строку ещё и на `\x0b`, `\x0c`, `\r`, `\x1c`, `\x1d`, `\x1e`, `\u2028`, `\u2029`. После `errors="replace"` эти байты выживают как есть (они валидный ASCII), поэтому одна `+`-строка бинарника распадается на фрагменты; фрагмент без префикса `+`/`-` трактуется в теле хунка как context-строка и декрементирует оба счётчика, тело завершается досрочно, а оставшиеся настоящие `+`-строки внешний цикл просто пропускает. Для фикстуры самой репродукции — `bytes(range(256))` — это видно насквозь: git отдаёт две добавленные строки (`\x0a` внутри), `@@ -0,0 +2 @@`; первая строка (`\x00`–`\x09`) съедает один счётчик, второй забирает фрагмент `"+"`, оборванный на `\x0b`, и всё от `\x0e` до `\xff` не сканируется вообще. Токен, лежащий в блобе после первого `\x0c`, не будет найден — при том что и spec-требование говорит «The file's own added bytes SHALL still be searched», и сообщение пользователю говорит «(added bytes still searched)», и design.md перечисляет только одну потерю (подпись, разрезанную невалидным байтом). Тест `test_an_undecodable_files_bytes_are_still_searched` проходит лишь потому, что токен стоит до любого control-байта. Либо резать по `"\n"` (единственный разделитель, который git вообще использует в patch-выводе), либо нейтрализовать эти символы в `_decode_section_lossy`, либо честно записать ограничение в design.md и ослабить формулировку spec'а и сообщения.

**3. (advisory)** Комментарий в `src/agentmarshal/cli.py:1223` всё ещё говорит «Every git call goes through `_leak_scan_git`, so non-UTF-8 paths/content are a clean refusal» — после этого change diff идёт через `leak_scan_diff`, и не-UTF-8 content уже не отказ, а именованная деградация. В репозитории, где комментарии несут обоснование решений, такой остаток вводит в заблуждение.

**4. (advisory)** Удаление бинарного файла теперь называется как «не декодировалось», хотя скан смотрит только добавленное: `_decode_section_lossy`/`_undecodable_section_name` отрабатывают секцию, у которой все недекодируемые байты — в `-`-строках (это и закрепляет `test_an_undecodable_deletion_is_named_from_the_diff_header`), и оба вызывающих печатают про неё «(added bytes still searched)». Любой коммит, удаляющий картинку, добавит в транскрипт предупреждение о файле, который скану и не требовался.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "46fafafa890c8e996644905a50c3408bc16eb585",
  "verdict": "changes_required",
  "findings": [
    "undecodable-names-bypass-safe-path",
    "control-bytes-truncate-undecodable-scan"
  ],
  "advisory_findings": [
    "stale-leak-scan-git-comment",
    "deletion-named-as-unread-added-bytes"
  ]
}
AGENTMARSHAL_VERDICT_END
