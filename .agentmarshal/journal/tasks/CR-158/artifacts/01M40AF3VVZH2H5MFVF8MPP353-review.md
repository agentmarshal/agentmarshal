Прочитал весь `extensions.py`, оба spec-файла, тесты и все три call site (`brief.py:232`, `review.py:1071,1247`, `gate.py:820`). Проверил соответствие каждого сценария delta-спеки тесту с docstring, однократность новых requirement-заголовков в `openspec/specs/extension-manifest/spec.md`, формат архива (`.openspec.yaml` как у соседних change'ей) и то, что `_manifest_from_tree`/`_extension_name` не тронуты (это заявленный non-goal).

Реализация по существу верна. Разбор ключевых мест:

- `_manifest_candidate` (`extensions.py:460`) применяет к обоим кандидатам то же правило, что было у file-формы: lexical `is_symlink()` на самом manifest-пути (ловит dangling link и loop), затем `resolve(strict=True)` с `resolved != path` — именно так отказывается symlinked `<name>/`. `NotADirectoryError` → `None` нужен, чтобы `<name>`-файл (не директория) считался отсутствующим.
- `_require_existing_directory_file` (`extensions.py:504`): `directory` взята как `candidate.parent`, а `candidate` уже доказанно без symlink'ов в компонентах, поэтому сравнение `resolved != target` действительно означает «не вышли за пределы директории». `..` лексически уже отрезан `_require_directory_file` + `validate_scope_entry`, а через link — ловится сравнением. Regular-file проверка через `is_file()` отсекает и директорию, и fifo.
- `_manifest_directory_paths` покрывает ровно те три поля, которые парсер объявляет путями (`stage.command`, `[dependencies].lock`, `[wraps].lock`) — ничего не пропущено.
- Все три caller'а обрабатывают `ExtensionManifestError`, а не только `Missing` (`review.py:1250` — через `except ValueError`), так что новый класс отказа (schema-2 single file, называющий `bin/`) никуда не утечёт traceback'ом.

Два необязательных замечания.

Первое: в `openspec/specs/extension-manifest/spec.md:218-221` новый requirement утверждает без оговорок, что «a symlink for the `<name>` directory itself ... SHALL be refused as a link», но *битый* (dangling) symlink на `<name>` кодом не отказывается — `_manifest_candidate` (`extensions.py:476-483`) делает `is_symlink()` на `<name>/manifest.toml` (lstat падает ENOENT → False), затем `resolve(strict=True)` даёт `FileNotFoundError` → `None`, и вызов заканчивается `ExtensionManifestMissing`. Поведение при этом симметрично тому, что file-форма делает сегодня с битым link'ом выше манифеста, и прочитать через битую ссылку нечего — то есть дефект не в коде, а в слишком сильной формулировке спеки.

Второе: существующий requirement «A manifest declares a known schema version» (`openspec/specs/extension-manifest/spec.md:20`) всё ещё говорит «the declared `name` matching the manifest's file name» — для directory-формы имя файла это `manifest.toml`, и `name` совпадает с именем *директории*, а не файла. Delta оформлена целиком как `## ADDED Requirements`, хотя контракт прямо допускает `MODIFIED` с сохранением точного заголовка; этот абзац стоило уточнить.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "dc4389657774832764695ddc3a5a57a0ba6e9e9a",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "dangling-extension-directory-symlink-reported-missing-not-refused",
    "schema-version-requirement-still-says-name-matches-file-name"
  ]
}
AGENTMARSHAL_VERDICT_END
