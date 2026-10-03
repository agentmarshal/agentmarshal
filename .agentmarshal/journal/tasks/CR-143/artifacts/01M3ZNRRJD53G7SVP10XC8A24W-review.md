Проверил ADR-0022 против контракта CR-143 — файл, схемы, поля, типы записей, локальные форматы и все утверждения о текущем поведении.

**Что сверено с кодом и опубликованными текстами (всё сходится):**
- максимумы схем: 6 — только `coordination`-сессия (`records.py:154,915`), 5 — review с `reviewed_contract` (`records.py:993`), 4 — `finding` и привязки (`records.py:289`), остальное 3 ✓
- имя файла записи `<id>-<type>.json`, тип `[a-z]+`, id — 26 символов (`records.py:30-32,201`) ✓
- заголовок контракта знает схемы 1 и 2, схема 2 ввела ровно `decisions`, `documents`, `extensions` (`contracts.py:147-156`) ✓
- манифест расширения — только схема 1, один файл `.agentmarshal/extensions/<name>.toml` (`extensions.py:88,105`) ✓
- читатель падает закрыто: `read_records` бросает «record has an unknown or missing schema version»; `status`-листинг и `report` валятся целиком (`status.py:179-202`, `report.py:115-124`), `validate` даёт FAIL на задачу (`validate.py:185-186`), гейт отказывает (`gate.py:937`) ✓
- отказ по манифесту только для расширения, названного контрактом — `gate.py:815-838` «named extension manifest unreadable»; для неназванного — тишина ✓
- `project.json` читается по именованным ключам, строгая проверка полей есть только внутри секций `capture` и `leak_scan` — новые секции `review` и `contract` 0.4.x просто игнорирует ✓
- `usage` опционален и несёт одновременно `provider` и `method` (`records.py:584-608`) ✓; объект `reviewer` сегодня закрыт на `{role, vendor, model, email}` (`records.py:351`) ✓; `recorded_by`+`recorded_by_source` уже обязательны на `finding` (`records.py:482`) ✓
- названные правки: требование record-lifecycle о том, что допускает терминальная задача (`openspec/specs/record-lifecycle/spec.md:11-23,59-62`), byte-for-byte требование gate-lanes и строка гейта «(session records accrue post-terminal)» (`gate.py:777`), решение 9 ADR-0014 и форма стадии `step` из диспозиции proposal 042 — все четыре названы в шапке ✓
- содержание решения сверено с ADR-0013 (пауза расширения, операционный CR без ревью, commit в конверте), ADR-0016 (dispositions, цепочка ревью, классы, порог 3), ADR-0017 (поля `check`, verification, evidence), ADR-0018 (хеш контракта, implementers/reviewers, independence, commit сессии), ADR-0019 (времена, resets_at, cost, экспорты в лог), ADR-0021 (файл как его печатает скан, само-подтверждение), proposals 041–043 — ни один пункт не потерян и ничего лишнего не добавлено ✓
- форма (Context / Decision / Left open / Consequences / Alternatives considered), дата, статус и все относительные ссылки — как у ADR-0012..0021 ✓; приватных документов, адоптеров и клиентов нет (только обобщённые «adopters»)
- диффом затронут ровно один файл из scope, код и журнал не тронуты

Полную последовательность CI я в этой read-only песочнице выполнить не смог (`uv`/`python3` недоступны без разрешения) — изменение состоит из одного markdown-файла, `pytest`/`ruff`/`mypy`/`validate` на него не опираются.

Единственное замечание, не блокирующее: ADR-0017 и ADR-0019 цитируются многократно (колонка Source в таблицах §2 и строки `check-output`/`provider-export` в §7, строки 124-125, 159, 224-225, 130, 135-136), но ни разу не оформлены ссылкой, тогда как все остальные упоминаемые ADR (0004, 0006, 0007, 0013, 0014, 0015, 0016, 0018, 0021) ссылку получают — два из шести решений, которые этот документ закрывает, остаются ненавигируемыми.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "d77e04e36d6f45be89dce242479dead2bdaa115e", "verdict": "approved", "findings": [], "advisory_findings": ["adr-0017-and-adr-0019-cited-without-links"]}
AGENTMARSHAL_VERDICT_END
