Проверил контракт, delta-спеку, реализацию и тесты. Основное всё на месте:

- `launch_review` берёт diff байтами (`_run_git_bytes`) и декодирует через `decode_diff_per_file` — тот же helper, что уже использует leak-scan; `review.py:1161`.
- Все пять сценариев delta-спеки закрыты тестами, docstring каждого называет сценарий (`tests/test_review_launcher.py:2334-2454`).
- Все вызовы `_run_git` (merge-base, ls-tree, rev-parse) и error-detail теперь декодируются `backslashreplace`; `_extract_snapshot` тоже.
- Фикс `_header_name`: для quoted-ветки `rpartition(' "b/')` даёт `destination` уже без `b/`, возвращается `f'"{destination}'` — префикс действительно уходит, кавычка остаётся. Тест `tests/test_capture.py:693` это проверяет на `GIT binary patch`-секции, где имя берётся именно из `diff --git`. Unquoted-ветка даёт тот же результат, что и раньше.
- Шаблон промпта: `diff_note` пустая строка при отсутствии undecodable, так что обычный промпт побайтово тот же — `tests/test_review_launcher.py:2119` с захардкоженным `expected` не ломается.
- `docs/sidecar.md` перечисляет все три строки, которые добавляет скан в gate (`gate.py:1177`, `1181`, `1187`); оба docstring с `\x0c` переведены в `r"""`.
- Change заархивирован как `openspec/changes/archive/2026-10-03-review-diff-per-file/`, `openspec/specs/reviewer-adapter/spec.md` дополнен ровно содержимым delta — соответствует конвенции остальных архивов.

Два advisory-замечания.

**`review-diff-omits-prefix-pinning-flags`** — `src/agentmarshal/journal/review.py:1161` вызывает `git diff` без `--src-prefix=a/ --dst-prefix=b/`, хотя `leak_scan_diff` (`gate.py:554-566`) пинит их именно затем, чтобы парсер корректно срезал `b/`: «with diff.mnemonicPrefix the header reads "+++ c/…" and with diff.dstPrefix anything at all». `review` теперь парсит те же header-строки через `_diff_path`/`_header_name`, так что в репозитории с `diff.mnemonicPrefix=true` имя undecodable-файла приедет в промпт и на stderr как `c/blob.bin`, а `_header_name` при отсутствии `b/`-маркера вернёт весь tail (`c/x c/x`). design.md взвешивает только отказ от `--text` (binary rendering) и не рассматривает prefix-флаги. Второй бок той же проблемы: комментарий `src/agentmarshal/journal/capture.py:418` «Both callers pass --dst-prefix=b/ for exactly this reason» стал неверным — появился второй caller `decode_diff_per_file`, который их не передаёт. Ничего не падает и не теряется молча, имя остаётся узнаваемым, поэтому не блокирует.

**`sidecar-twenty-entry-claim-overreaches`** — `docs/sidecar.md:252`: переписанная фраза «None of them blocks. Each is one line of a transcript, so it shows at most twenty entries» теперь охватывает и `WARN: leak-scan skipped (<reason>)`, у которой никакого лимита в двадцать записей нет (она вообще не перечисляет файлы). Прежний текст был точнее («The hit line is one line of a transcript, so it shows at most twenty hits»). Требование контракта — перечислить все строки — выполнено, но формулировка про лимит стала менее точной.

Отдельно, не как finding: выполнить CI-последовательность здесь не смог — в окружении нет `uv`, `pytest`, `ruff`, `mypy`, а запуск был отклонён permission-проверкой. Проверил статически то, что обычно её ломает: длина строк нового кода в пределах 88, все `.format()`-аргументы шаблона заполнены, дублей имён тестов нет, `subprocess.run` без `encoding` даёт `CompletedProcess[bytes]` под strict mypy, partial-None для `diff_note` разрешается последующим присваиванием. Признаков падения не нашёл, но подтвердить прохождение CI сам не могу.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ba49053e4819f67b50405f3ff0555e976ee602b2", "verdict": "approved", "findings": [], "advisory_findings": ["review-diff-omits-prefix-pinning-flags", "sidecar-twenty-entry-claim-overreaches"]}
AGENTMARSHAL_VERDICT_END
