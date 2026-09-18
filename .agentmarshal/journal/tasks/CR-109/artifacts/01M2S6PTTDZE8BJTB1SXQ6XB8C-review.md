Проверка статическая: запуск pytest требует approval, поэтому `tests/test_quickstart.py`, `tests/test_smoke.py` и закреплённые тесты транскрипта 0.3.0 я не запускал. Выводы ниже я сверил с исходниками, журналом и шаблоном.

**Что проверено**
- **Версия.** В `pyproject.toml`, `__init__.py` и `uv.lock` стоит 0.4.0. `test_smoke.py` проверяет `--version` через `__version__`. `tests/test_gate.py` в диффе не тронут, значит ожидания закреплённого транскрипта 0.3.0 остались как были.
- **CHANGELOG.** Все 25 задач CR-084…CR-108 названы по разу, и у каждой в журнале есть запись `completed`. Слов «planned/next/soon/in line» в новом разделе нет. Утверждения совпадают с кодом:
  - лимит `_LEAK_HIT_RENDER_LIMIT = 20`;
  - строки TODO у `doctor` и итоговая строка со счётчиком preconditions;
  - четыре preconditions, которые печатает `init`;
  - OpenSpec 1.12.0 в `.agentmarshal/extensions/openspec.toml`.
  Где возможность частичная, раздел это говорит: GitHub, непроверяемые артефакты, gate не исполняет команды manifest.
- **UPGRADING.** Схемы 4/5/6 описаны верно: `create_review_record` пишет 5, когда передан `reviewed_contract`, а `review.py:883` передаёт его всегда; у 0.3.0 это сообщение `record has an unknown or missing schema version`. Раздел также покрывает CR-102, CR-105, `--without-review` с шаблоном и новый вывод leak-scan.
- **Три advisory из CR-107.**
  - В `docs/overview.md` заголовок больше не говорит «designed», у каждого пункта указано, есть ли опубликованный дизайн.
  - Proposal 005 помечен как superseded и получил датированный раздел: ADR-0009 от 2026-09-05, дата сверена.
  - Комментарий job `governance` дословно совпадает с `templates/github/agentmarshal-governance.yml:24-27`.

**Замечания (не блокируют)**

В `CHANGELOG.md:78-82` из новых схем записей упомянута только схема 6. О том, что `agentmarshal review` теперь пишет каждую запись review в схеме 5, а finding использует схему 4, и что 0.3.0 такой журнал не прочитает, раздел молчит и на UPGRADING.md не ссылается. В разделе 0.3.0 для сравнения прямо сказано «No record-format change».

В `UPGRADING.md:3-35` раздел 0.3.0 → 0.4.0 не содержит блока «Per installation method», который есть в предыдущих разделах: сменить pin на `==0.4.0`, а unpinned-установка сама не обновится. При разрыве, который fail-closed, именно CI без pin и остаётся на 0.3.0 незамеченным читателем.

В `docs/overview.md:169-171` пункт «Contract extensions» переписан в «Further contract metadata», и из roadmap пропало направление «обязательные machine-readable acceptance criteria, которые проверяет gate». При этом `docs/adr/ADR-0004-journal-data-model.md:138-140` и `docs/migration-v1-to-v2.md:77-81` по-прежнему описывают его как ещё не действующее.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "aba99fb83248f763fc12ee3746cec95041cb00c7", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-CHANGELOG-SCHEMA-4-5-UNMENTIONED", "ADV-UPGRADING-NO-INSTALL-METHOD-GUIDANCE", "ADV-OVERVIEW-ACCEPTANCE-ENFORCEMENT-DROPPED"]}
AGENTMARSHAL_VERDICT_END
