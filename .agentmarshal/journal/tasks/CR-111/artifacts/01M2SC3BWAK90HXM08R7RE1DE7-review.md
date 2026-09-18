Одобряю с двумя некритичными замечаниями. Проверка статическая: запустить pytest в этой среде не разрешили, так что ни один тест я не прогнал.

Что сверил с контрактом CR-111:

- **Одна настройка.** Уровень читает только `review_capture_level_from_journal` в `capture.py:250`. Он вызывает существующий `capture_policy_from_project(...).level_for(CaptureClass.REVIEWS)`, больше этот парсер никто не вызывает, второго ключа нет.
- **Какой project file читается.** Путь `journal_root.parent.parent`. Журнал всегда лежит в `<project>/.agentmarshal/journal` (так задаёт `resolve_placement`), поэтому для sidecar читается project file самого sidecar, а не host. На это есть отдельный тест.
- **`agentmarshal review`.** Уровень определяется до запуска reviewer. Неправильная секция `capture` даёт `ReviewLaunchError`, и reviewer не запускается.
  - При `commit` в `submit_review` передаётся `prose=raw_output`, и строка `reviewer prose pinned: <ref>` на stderr та же, что раньше.
  - При `hash` запись делается с `prose=None`, stdout reviewer'а сохраняется во временный файл, путь к нему печатается на stderr.
  - При `off` ничего не сохраняется, на stderr об этом сообщается.
- **`submit-review --prose`.** Отказ происходит до `read_bytes` и до `submit_review`. В сообщении есть уровень и `capture.overrides.reviews = "commit"`.
- **Этот репозиторий.** В `.agentmarshal/project.json` добавлен `capture.overrides.reviews = "commit"`.
- **Документы.** README, UPGRADING, раздел 0.4.0 в CHANGELOG, quickstart, overview и status note в ADR-0005 называют умолчание и настройку. Фразы «No setting turns this off» больше нигде нет.
- **Отход от ADR-0005.** Там `hash` определён как private store. То, что здесь `hash` пока означает временный файл, записано и обосновано в `design.md`.
- **Сценарии.** У каждого сценария delta spec есть тест с его названием в docstring. Старые тесты, ожидающие закреплённую prose, теперь явно ставят `commit` в своей fixture.

Замечания:

- **A-001.** Сценарий «a rejected verdict still keeps the prose» требует сохранения «at every capture level». Но `tests/test_review_launcher.py:1831` проверяет только уровень `off` (preset `minimal`), а `hash` и `commit` для отклонённого verdict в этом тесте не проверяются. Код здесь от уровня не зависит, так что это пробел в тестах, а не ошибка.
- **A-002.** В `README.md:66` новая фраза склеена со следующим абзацем в одну строку длиннее 200 символов. Похожая строка есть в `CHANGELOG.md:53`, она длиннее 80. На смысл это не влияет, только на перенос строк.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "93a2d8c1a2fa65846b7fe0a5923d16812af95213", "verdict": "approved", "findings": [], "advisory_findings": ["A-001", "A-002"]}
AGENTMARSHAL_VERDICT_END

Claude.ai Gmail, Google Calendar и Google Drive требуют авторизации в настройках коннекторов на claude.ai, до этого они недоступны. Для этого ревью они не нужны.
