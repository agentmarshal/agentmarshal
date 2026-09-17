Прочитал diff и окружающий код (`capture.py`, `gate.py`, `review.py`, `cli.py`, `project.py`, тесты, ADR-0005/0008, `openspec/specs/leak-scan/`). Запустить pytest в этой песочнице не дали (команда требует approval), поэтому проверка статическая — про это скажу честно: утверждения ниже основаны на чтении кода, а не на прогоне.

Семь сценариев из `openspec/changes/archive/2026-09-17-adopter-small-defects/specs/` действительно закрыты тестами, чьи docstring их называют, и общий рендерер `render_leak_hits` у standalone-команды и у gate один — расхождения между ними больше не будет. Ниже то, что не сходится.

**leak-scan-path-discloses-marker-value** — `src/agentmarshal/journal/capture.py:300`: `render_leak_hits` печатает `hit.path` как есть, а путь — это неотфильтрованное содержимое репозитория. Требование, которое эта же задача добавила в `openspec/specs/leak-scan/spec.md`, говорит «It SHALL NOT print the matched text, nor the marker's value». Если private marker (внутренний hostname, кодовое имя клиента) встречается в имени файла или каталога — `deploy/coordinator.internal.example.yaml` — и в этом файле срабатывает любая built-in сигнатура, значение маркера уходит прямо в вывод и в CI-лог. Ни `_line_hits`, ни `render_leak_hits` путь против `private_markers` не проверяют. Тест `test_a_private_marker_is_named_by_position_not_by_value` кладёт маркер только в содержимое строки, поэтому этот канал не покрыт.

**self-match-suppression-keys-on-wrong-repository** — `src/agentmarshal/journal/capture.py:277` и `:424`: подавление self-match сравнивает путь с жёсткой константой `.agentmarshal/project.json` и никак не проверяет, что этот файл и есть конфигурация, из которой маркеры были загружены. В sidecar-размещении (ADR-0008) маркеры читаются из репозитория оператора (`markers_from_config(sidecar_config)` в `cli.py:1263`, `markers_from_config(journal_root.parents[1])` в `gate.py:1114`), а diff берётся из host'а. Значит `.agentmarshal/project.json` внутри host-диффа — это всегда чужой, недоверенный кандидатский файл, который данный маркер не объявляет, и тем не менее единственное вхождение маркера в нём молча отбрасывается. Это false negative в секрет-сканере ровно в том месте, где комментарии в `gate.py:1110-1113` и `cli.py:1256-1259` специально настаивают, что маркеры берутся с доверенной стороны, «so a candidate cannot weaken its own scan». Требование в спеке формулирует условие как «the project configuration that declares that marker» — код проверяет только имя файла.

**project-config-path-not-placement-aware** (advisory) — та же константа `capture.py:277`: пути в `git diff` относительны корню git-репозитория, а `.agentmarshal/` может лежать в подкаталоге (`find_project_root(Path.cwd(), stop_at=git_root)` в `cli.py:1226` это допускает, и `test_leak_scan_binds_to_nested_repo_not_ancestor` показывает, что вложенные layout'ы в проекте рассматриваются). Для проекта в подкаталоге путь будет `sub/.agentmarshal/project.json`, подавление не сработает, и false positive, ради которого задача существует, вернётся.

**per-line-scan-drops-multi-line-matches** (advisory) — `src/agentmarshal/journal/capture.py:346-353` и `:407`: раньше `scan_diff_for_leaks` склеивал добавленные строки через `"\n"` и отдавал их в `scan_for_leaks` одним текстом, теперь каждая строка сканируется отдельно. Паттерн `authorization-header` (`capture.py:270-273`) использует `\s*`/`\s+`, которые матчили перевод строки, так что `Authorization:` с токеном на следующей добавленной строке больше не находится; то же для маркера, содержащего перевод строки. Это второе сужение скана, помимо того, которое design.md объявляет «bounded by location», и в design.md оно не зафиксировано.

**unknown-file-placeholder-not-recorded** (advisory) — `src/agentmarshal/journal/capture.py:384` и тест `tests/test_capture.py:313`: хит может отрендериться как `(unknown file): aws-access-key-id`, то есть не назвать файл, хотя добавленное требование говорит «SHALL name the file it matched in». Решение разумное (лучше сообщить, чем промолчать), но design.md его не записывает, а acceptance задачи требует либо следовать design.md, либо записать в нём отступление.

**standalone-headline-still-says-categories** (advisory) — `src/agentmarshal/cli.py:1289`: строка по-прежнему начинается с «possible leak categories in added content: », хотя дальше идёт уже не категория, а `path: identification`; получается двойное двоеточие и заголовок, противоречащий новой семантике. Gate-строка («possible leak in candidate additions») формулировку не унаследовала, так что тексты двух путей всё же разные — общий у них только хвост.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "8e29891f03b78270c5480d47854201487612ccee",
  "verdict": "changes_required",
  "findings": [
    "leak-scan-path-discloses-marker-value",
    "self-match-suppression-keys-on-wrong-repository"
  ],
  "advisory_findings": [
    "project-config-path-not-placement-aware",
    "per-line-scan-drops-multi-line-matches",
    "unknown-file-placeholder-not-recorded",
    "standalone-headline-still-says-categories"
  ]
}
AGENTMARSHAL_VERDICT_END
