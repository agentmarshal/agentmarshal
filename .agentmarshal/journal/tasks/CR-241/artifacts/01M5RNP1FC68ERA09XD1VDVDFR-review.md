Проверил контракт, диф и сами файлы в snapshot'е. Выполнять что-либо (pytest, git, python) в этой сессии нельзя — Bash на таких командах отказывает, поэтому прогон тестов я не делал; факт зелёного CI на a16520d0 беру из записки координатора, всё остальное проверено чтением файлов и несколькими read-only командами (grep/ls/diff).

## Как закрыты acceptance criteria

**1. Отказ на symlink до любой записи — выполнен.** `_locate` (`src/agentmarshal/outbox.py:174-196`) проверяет `outbox.parent` и `outbox` через `is_symlink()` (lstat, без следования) до `outbox.is_dir()` и до любого I/O, и возвращает `None` всем четырём подкомандам; `_run_new` вызывает `_locate` раньше `_write_draft` (`outbox.py:361-366`), `_run_send` — внутри `_check` (`outbox.py:981`). Утверждение design.md, что между resolved project root и outbox есть только два компонента, проверяемо верно: `_ancestors_from` делает `start.resolve()` (`project.py:50`), так что `find_project_root` отдаёт физический путь — значит двух проверок достаточно для формулировки «любой компонент между project root и ним». В `init` отказ живёт в `_scaffold_outbox` (`project.py:317-319`) до `mkdir`/`open`, а текст уходит в единственную warning-строку `cli.py:556-561`. Демонстрируют: `test_a_linked_outbox_refuses_a_command_before_it_writes` (четыре подкоманды, `outside` пуст, 0 коммитов), `test_a_linked_agentmarshal_component_refuses_the_command`, `test_init_never_scaffolds_through_a_linked_outbox`, `test_a_sidecars_linked_outbox_never_writes_the_host`. Две заметки без статуса finding: у `outbox send` строка отказа подписана `outbox check:` (send прогоняет check первым) — тест считает строки по подстроке, так что это косметика; и ветка `project_directory` в `_scaffold_outbox` недостижима, потому что `write_project_file` отказывает на symlink'нутом родителе раньше (`project.py:189-193`, вызов на `project.py:449` до `453`) — защита в глубину, не дыра.

**2. Отказ на расхождении staged-байтов с проверенными — выполнен.** `_pinned_blob` (`outbox.py:817-837`) сравнивает `hash-object --stdin --path=<rel>` (атрибуты пути применены) с `hash-object --stdin --no-filters` тех же байт; `None` превращается в problem по файлу (`outbox.py:690-694`) и в отказ по `SENT` (`outbox.py:748-753`), то есть `_check` возвращает 1 и `_run_send` выходит до `git add`. Выбор «спросить git дважды» корректен: без `--path` git не применяет никаких conversion'ов (нет пути — нет атрибутов), а с `--path` применяет и clean filter, и eol, и encoding, так что сравнение покрывает преобразования целиком и не зависит от object format. Демонстрируют: `test_send_refuses_a_draft_a_clean_filter_would_transform` и `test_send_refuses_when_a_filter_would_transform_the_sent_manifest` — оба с настоящим `filter.x.clean = sed s/a/b/` и проверкой `rev-list --count --all == 0`.

**3. Escaping имён в `status` — выполнен.** Все три места, где `_run_status` печатает имя или путь, теперь идут через `_printable` (`outbox.py:1148`, `1158`, `1166`); других имён в функции нет — строка про index-записи печатает только hex-digest (`outbox.py:1190-1192`). Демонстрирует `test_a_control_character_in_a_file_name_is_escaped_in_the_report`. Для печатаемых имён вывод не меняется: `escape_for_display` — тождество на тексте, который `forges_rendered_text` не отвергает (`journal/display.py:38-39`), а подстановка `safe_path` — ASCII `<private marker #N>` (`journal/capture.py:328`), так что двойного escaping не возникает.

**4. Delta и архив — выполнены.** Три ADDED-требования с шестью сценариями, у каждого сценария тест с одноимённым docstring'ом. `diff` тела delta и хвоста `openspec/specs/outbox/spec.md` расходится только на заголовке `## ADDED Requirements` — тексты требований совпадают байт в байт; каждое требование в capability-спеке встречается один раз (`grep -n '^### Requirement:'` — 489, 512, 530); `openspec/changes/` содержит только `archive`, рабочий каталог change'а удалён, `.openspec.yaml` совпадает по форме с соседями (`schema: spec-driven`, `created`). Мелочь без статуса finding: `README.md` внутри каталога change'а — единственный такой на 99 архивов.

**5. Поведение без symlink/transformation/непечатаемых имён — выполнено в той части, которую можно проверить чтением** (см. пункт 3 про тождественность escaping); зелёный полный CI на этом коммите — факт из записки координатора, сам я его не прогонял.

## Advisory

**locate-refusal-unmasked-path** — новая строка отказа в `_locate` (`src/agentmarshal/outbox.py:183-187`) печатает абсолютный путь через `escape_for_display(_shown_name(...))`, без marker masking, тогда как тот же самый путь в `_run_status` печатается через `_printable` с масками (`outbox.py:1158`), и весь модуль демонстративно избегает непромаскированных путей (`_os_error_text`, `_config_error_text` существуют ровно для этого). Markers здесь доступны: `_markers(command, project_root, stderr)` требует только project root, а чтение project.json — это чтение, а не запись через ссылку. Не блокирует: ни контракт, ни спека маскирования в этой строке не требуют, и формулировка в точности повторяет precedent `extension_trust._managed_directory` (`extension_trust.py:224-226`), который тоже печатает путь без масок.

**eol-refusal-no-remedy** (unconfirmed) — отказ «git would transform it on staging — a clean filter or eol conversion applies» (`outbox.py:691-693`) не называет операторe выхода, а срабатывает он не только на враждебном clean filter: при `core.autocrlf=true` или `* text=auto` draft, сохранённый редактором с CRLF, даёт разные blob id, и `outbox send` будет отказывать безысходно. Проект заявляет «Windows is untested» (`README.md:118`), но Windows-адоптеры реальны и сам upstream-канал пришёл именно от такого (`docs/proposals/012-upstream-feedback-channel.md:3`). Поведение санкционировано спекой и criterion 5 («no git transformation»), так что это не блокер — но ни текст отказа, ни README outbox'а не говорят «нормализуй draft в LF». Помечаю unconfirmed: механику eol-нормализации git я здесь не исполнял, вывод сделан из того, как `convert_to_git` применяется при `--path`.

**status-requirement-duplicated** — добавленное требование `outbox status escapes the names it prints` (`openspec/specs/outbox/spec.md:530-540`) повторяет обязательство, уже записанное в существующем требовании про `status`: «Every name the command prints SHALL be masked and a name that is not UTF-8 SHALL be written in escaped printable form, exactly as `outbox check` names files» (`openspec/specs/outbox/spec.md:290-292`, со сценарием на 335-339). То есть аудит AUD-commands-6 — это баг против уже существующего требования, и по смыслу здесь был MODIFIED с полным текстом, а не ADDED; теперь одно свойство печати управляется двумя требованиями и может разъехаться. Контракт ADDED прямо разрешает, поэтому advisory.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "a16520d043f56b1e08536cec9ee972f40a6241b0",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "locate-refusal-unmasked-path",
    "eol-refusal-no-remedy",
    "status-requirement-duplicated"
  ],
  "classes": {
    "locate-refusal-unmasked-path": "security",
    "eol-refusal-no-remedy": "style",
    "status-requirement-duplicated": "style"
  },
  "verification": {
    "executed": [
      {"what": "diff of openspec/changes/archive/2026-10-25-outbox-boundaries/specs/outbox/spec.md (minus its '# Spec Delta' header) against the last 55 lines of openspec/specs/outbox/spec.md", "result": "only the '## ADDED Requirements' heading line differs; the three requirement bodies and six scenarios are byte-identical"},
      {"what": "grep -n '^### Requirement:' openspec/specs/outbox/spec.md", "result": "10 requirements, the three new ones once each at lines 489, 512, 530"},
      {"what": "ls openspec/changes/", "result": "only 'archive' — the working change directory is gone"},
      {"what": "find openspec/changes/archive -maxdepth 2 -name .openspec.yaml / -name README.md and grep of two .openspec.yaml files", "result": "34 of 99 archived changes carry .openspec.yaml with the same 'schema: spec-driven' + 'created:' form; README.md inside a change directory exists only for this change"},
      {"what": "grep -rn 'upstream' over src/agentmarshal/*.py excluding outbox.py", "result": "only project.py writes the outbox path, so _locate plus _scaffold_outbox cover every writer"},
      {"what": "grep of pyproject.toml for pytest/coverage settings", "result": "[tool.pytest.ini_options] testpaths only — no coverage gate, so the unreachable _scaffold_outbox branch cannot fail CI"}
    ],
    "read": [
      "src/agentmarshal/outbox.py (module docstring, _locate, _shown_name, _printable, _markers, _run_new, _write_draft, _check, _git, _pinned_blob, _batch_mismatch, _run_send, _run_status)",
      "src/agentmarshal/project.py (_ancestors_from, find_project_root, write_project_file, _scaffold_outbox, initialize_project tail)",
      "src/agentmarshal/cli.py:538-561 (_run_init warning line)",
      "src/agentmarshal/extension_trust.py:205-244 (_managed_directory precedent)",
      "src/agentmarshal/journal/display.py (escape_for_display)",
      "src/agentmarshal/journal/capture.py:312-331 (safe_path)",
      "tests/test_outbox.py:1-95 (helpers, _CONFORMING) and 1923-2113 (the seven new tests)",
      "openspec/specs/outbox/spec.md (Purpose, send and status requirements, the three appended requirements)",
      "openspec/changes/archive/2026-10-25-outbox-boundaries/{proposal.md,design.md,tasks.md,README.md,specs/outbox/spec.md}",
      "README.md:118, docs/proposals/012-upstream-feedback-channel.md:3, CONTRIBUTING.md:175-199"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "Bash approval was denied for every execution in this non-interactive session; the coordinator states the full sequence passed on the reviewed commit"},
      {"what": "git hash-object --stdin --path=... vs --no-filters on a repository with a clean filter, and the sha256 of the conforming draft used by the manifest test", "why": "no command execution available; reasoned from git's conversion behaviour and from the sed filter adding a trailing newline, which makes the mismatch independent of the digest's characters"}
    ]
  },
  "evidence": {
    "locate-refusal-unmasked-path": "src/agentmarshal/outbox.py:183-187 prints escape_for_display(_shown_name(component)) with no markers, while src/agentmarshal/outbox.py:1158 prints the same outbox path as _printable(outbox, markers); _markers() needs only project_root (src/agentmarshal/outbox.py:262-275); precedent src/agentmarshal/extension_trust.py:224-226",
    "eol-refusal-no-remedy": "src/agentmarshal/outbox.py:690-694 and 748-753 (refusal text names no remedy); src/agentmarshal/outbox.py:817-837 (_pinned_blob compares the attribute-applied id with the raw id, so any eol normalisation refuses); README.md:118 'Windows is untested.'; docs/proposals/012-upstream-feedback-channel.md:3 names a Windows adopter as a reporter of this very channel",
    "status-requirement-duplicated": "openspec/specs/outbox/spec.md:290-292 and :335-339 (pre-existing masking/escaping obligation for status) versus openspec/specs/outbox/spec.md:530-540 (the new ADDED requirement restating it)"
  }
}
AGENTMARSHAL_VERDICT_END
