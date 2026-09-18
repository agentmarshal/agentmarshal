Ревью CR-109 на коммите b83fab98 — **approved**, блокирующих замечаний нет, есть два некритичных.

Как проверял. Тесты запустить не удалось: этот запуск не одобрили, поэтому новый `tests/test_quickstart.py` я прошёл только чтением. Всё остальное сверял с кодом, контрактами задач и журналом.

- **Версия 0.4.0** стоит во всех трёх местах: `pyproject.toml`, `__init__.py`, `uv.lock`. `test_smoke` сравнивает её с `__version__`. Тесты, которые байт в байт закрепляют transcript и prompt 0.3.0 (`test_gate.py`, `test_review_launcher.py`), в диффе не тронуты.
- **Упоминания версий.** Все упоминания 0.3.0, которые остались в `docs/`, README, шаблонах и `gitflic-ci.yaml`, исторические («new in 0.3.0», «Since 0.3.0»). Там, где речь о текущем релизе, теперь 0.4.0.
- **CHANGELOG** покрывает все 25 задач CR-084…CR-108. Утверждения совпадают с кодом:
  - схема 5 ставится на каждое `agentmarshal review`: `review.py:883` всегда передаёт `reviewed_contract`;
  - схема 6 только у coordination (`records.py:879`);
  - лимит в двадцать совпадений leak-scan в gate (`_LEAK_HIT_RENDER_LIMIT = 20`);
  - `doctor` для невыполненного предусловия печатает TODO и не меняет exit status;
  - при проверке finding'а обрабатываются drift и отсутствие проверяемых артефактов.

  Ссылки ведут только на существующие файлы. Слов «planned/next/soon» в разделе 0.4.0 нет.
- **UPGRADING** называет всё, что требует критерий: схемы 4/5/6 с сообщением отказа 0.3.0, отказ writer'а (CR-102), reopen через gate (CR-105), `--without-review` вместе со сменой шаблона, новый вывод leak-scan. Утверждения о rename (CR-093) и reopen (CR-105) сходятся со спекой и контрактом.
- **Три замечания CR-107 закрыты:**
  - в roadmap `docs/overview.md` больше нет заголовка «designed», у каждого пункта сказано, есть ли опубликованный дизайн;
  - в proposal 005 отмечено, что порядок работ «next in line» не выдержан, и добавлен датированный раздел;
  - job `governance` в workflow дословно совпадает с комментарием шаблона.

Два некритичных замечания:

`CHANGELOG.md:18-22`: абзац про несовместимость схем 4, 5 и 6 не называет задачи (CR-086, CR-096, CR-106). А критерий приёмки требует, чтобы каждая запись называла свои задачи; сейчас они названы только в тематических разделах ниже.

`docs/quickstart.md:6-11`: там написано «Every command below was run against `agentmarshal` 0.4.0 before it was published». Но ниже есть `pip install agentmarshal==0.4.0`, а его до публикации выполнить нельзя. Кроме того, `tests/test_quickstart.py` запускает только раздел «The governed loop» и берёт исходники из дерева, а не установленный пакет. Так что фраза обещает больше, чем проверено.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "b83fab98bbee33427fbfdd6ec91e9334eb767bcf", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-CHANGELOG-SCHEMA-PARAGRAPH-NAMES-NO-TASK", "ADV-QUICKSTART-EVERY-COMMAND-RUN-OVERSTATES"]}
AGENTMARSHAL_VERDICT_END
