Ревью CR-111 на коммите `93a2d8c` готово: блокирующих и advisory-замечаний нет, вердикт — approved. Тесты я не запускал, потому что запуск pytest не был разрешён, так что это только статическая проверка.

**Как устроено**
- Уровень берётся из существующего парсера: `capture_policy_from_project(...).level_for(CaptureClass.REVIEWS)`. Проект определяется от пути журнала (`journal_root.parent.parent`), поэтому в sidecar читается файл самого sidecar, а не host. Второй настройки не появилось.
- Путь журнала всегда `<project>/.agentmarshal/journal` (так задано в `placement.py`), так что это вычисление корректно.

**Поведение по уровням**
- **`commit`:** `agentmarshal review` пишет и закрепляет артефакт, строка `reviewer prose pinned: …` на stderr прежняя. Это повторяет поведение до изменения.
- **`hash` (по умолчанию):** запись review идёт с `prose=None`, артефактов нет. Вывод ревьюера сохраняется в `agentmarshal-reviewer-output-*.txt`, путь печатается на stderr.
- **`off`:** ничего не сохраняется, на stderr пишется, что проза не сохранена.
- **Отклонённый вердикт и stderr ревьюера** обрабатываются как раньше на любом уровне.

**Отказы и ранние проверки**
- `agentmarshal review` читает уровень в `launch_review` до запуска ревьюера. Битая секция `capture` не стоит прогона ревьюера, что и описано в сценарии.
- `submit-review --prose` отказывает до любых записей и до чтения файла прозы, если уровень не `commit`. Сообщение называет уровень и `capture.overrides.reviews = "commit"`. `OSError` и ошибки парсера уходят в общий обработчик.

**Тесты**
Каждый сценарий delta spec покрыт тестом, в docstring которого он назван:
- пять новых — в `tests/test_review_capture.py`;
- четыре изменённых — в `tests/test_review_launcher.py` и `tests/test_journal.py`.

Тестовые фикстуры, которые ожидают закреплённую прозу, переведены на `commit`, а не лишились своих assert'ов.

**Репозиторий и документы**
- `.agentmarshal/project.json` задаёт `reviews: commit`.
- README, UPGRADING, раздел 0.4.0 в CHANGELOG, `docs/quickstart.md`, `docs/overview.md` и status note в ADR-0005 называют умолчание и настройку.
- Фразы «No setting turns this off» не осталось нигде, кроме текста контракта и старого артефакта ревью в журнале.
- Отступление `hash` от ADR-0005 Decision 2 (пока нет private store — локальный temp-файл) записано в `design.md`, как требует acceptance.

Отдельно: коннекторы Gmail, Google Calendar и Google Drive на claude.ai требуют авторизации в настройках коннекторов claude.ai. Для этого ревью они не понадобились.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "93a2d8c1a2fa65846b7fe0a5923d16812af95213", "verdict": "approved", "findings": []}
AGENTMARSHAL_VERDICT_END
