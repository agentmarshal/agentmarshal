Прошёл по контракту, дифу и коду в снапшоте. Ниже — что сошлось, и два необязательных замечания.

**Что проверено и держится.**

- Все восемь сценариев из `openspec/changes/archive/2026-09-18-bounded-leak-scan-output/specs/leak-scan/spec.md` имеют тест, чей docstring называет их дословно: шесть прежних (`tests/test_capture.py:242,337,355,376,489`, `tests/test_gate.py:1779`) и два новых — `tests/test_gate.py:1809` и `tests/test_leak_scan.py:66`. Архивная дельта совпадает с `openspec/specs/leak-scan/spec.md` слово в слово, включая новый абзац про границу.
- Реализация следует всем трём решениям design.md: `limit` — параметр (`src/agentmarshal/journal/capture.py:324`), гейт передаёт свою константу (`src/agentmarshal/journal/gate.py:62,1187`), standalone передаёт `None` (`src/agentmarshal/cli.py:1309`); счётчик остаётся внутри той же строки; двадцать не менялось.
- Рендерер по-прежнему один: `grep` по всему репозиторию даёт ровно два вызывающих места плюс тесты, и ни одно из них не собирает форму хита само.
- Гейтовый тест корректен на деле, а не только на вид: 21 файл даёт 21 хит в алфавитном порядке, `src/secret20.py` выпадает за границу, суффикс `, and 1 more not shown` пинит и число показанных. `next(...)` по `WARN:` однозначен — в `gate.py` всего две `WARN`-строки, и они взаимоисключающие, так что пропуск скана тест уронит, а не проглотит.
- `docs/sidecar.md:247-248` описывает строку ровно так, как её пинит `tests/test_gate.py:1793`. Больше нигде в репозитории эта формулировка не дублируется — `grep` по `docs/`, `README.md`, `templates/` чист.
- `LaunchedReview` в `__all__` и в импорте (`src/agentmarshal/journal/__init__.py:25,45`), запинено `tests/test_journal.py:94`. Строка импорта — ровно 88 символов, под лимитом ruff.
- Все десять затронутых путей внутри scope; байт-в-байт транскриптный тест не задет, потому что его кандидат чист — ровно как предсказывает раздел Risks в design.md.

**ADV-SIDECAR-BELOW-IT-AMBIGUOUS** — `docs/sidecar.md:251`: в фразе «past that it ends `, and N more not shown`, and below it there is no such suffix» местоимение «it» во второй половине должно означать «двадцать», но предыдущая клауза говорит буквально о том, чем строка *заканчивается*, поэтому «below it» естественно читается пространственно — «ниже этой строки». Критерий приёмки №4 — про точность именно этого абзаца, так что стоит перефразировать, например «at twenty hits or fewer there is no such suffix».

**ADV-RENDER-LIMIT-NOT-IN-DOCSTRING** — `src/agentmarshal/journal/capture.py:321-330`: у `render_leak_hits` появился обязательный параметр `limit`, но объяснение, кто и почему его выбирает, лежит в комментарии *над* `def`, а docstring не упоминает его вовсе и по-прежнему описывает функцию так, будто у неё нет режимов. Комментарий не попадает ни в `help()`, ни в подсказку IDE — это единственное место, где вызывающий увидит сигнатуру.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "b72564daf990c9c8877e2ddcbb9901382839ac6c", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-SIDECAR-BELOW-IT-AMBIGUOUS", "ADV-RENDER-LIMIT-NOT-IN-DOCSTRING"]}
AGENTMARSHAL_VERDICT_END
