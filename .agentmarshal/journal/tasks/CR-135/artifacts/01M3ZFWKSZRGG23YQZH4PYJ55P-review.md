Проверил контракт и диф по снапшоту.

**Что проверял по фактам (criterion 3):**
- «журнал имеет девять типов записей» — подтверждено кодом: `src/agentmarshal/journal/records.py:34-127` даёт ровно 9 типов (`opened`, `review`, `acceptance`, `completed`, `abandoned`, `reopened`, `amendment`, `session`, `finding`), и это совпадает с опубликованным `docs/proposals/028-check-outcomes-are-not-evidence.md:8-10`.
- «gate ничего не записывает» — в `src/agentmarshal/journal/gate.py` нет ни `write_record`, ни записи файлов; его докстринг (`gate.py:6-8`) прямо говорит, что review-записи пишет лаунчер.
- «outcome для лимита провайдера документирован с более раннего релиза» — `provider-limit` с 0.4.1 (`CHANGELOG.md:41`, `docs/proposals/README.md:125`, `docs/quickstart.md:449`).
- маскировка путей в leak-scan — `capture.py:312-331` (`safe_path`), применяется ко всем путям хитов (`capture.py:647,662-663`) и к именам недекодируемых файлов (`capture.py:370`); совпадает со спекой `openspec/specs/leak-scan/spec.md`.
- класс 9 (`splitlines`) — дословно соответствует решению `openspec/changes/archive/2026-10-03-per-file-leak-scan/design.md:54-64`, включая «later added bytes unscanned while the output claims they were searched».
- класс 10 (правило «важны только добавленные строки», переиспользованное для ревьюера) — соответствует `openspec/changes/archive/2026-10-03-review-diff-per-file/design.md:43-52` и живому коду (`review.py:1188` передаёт `name_all_losses=True`).
- класс 12 («gate отказывает кандидату») — `openspec/specs/scope-enforcement/spec.md:20-24`.
- классы 4, 5, 13 — секции `Disposition`/`Where` и индексная таблица реально существуют (`docs/proposals/README.md:90`, `docs/proposals/043-...:85,121`), конвенция «ADR называет ревизию в шапке» есть (`ADR-0013:17-22`, `ADR-0015:11`), запятая как разделитель тысяч — текущая практика (`docs/proposals/038-...:35-37`).

Тринадцать классов на месте, сгруппированы ровно шестью заголовками в порядке контракта, нумерация сквозная; примеров-идентификаторов (task id, record id, finding id, номер proposal, псевдоним, коммит, приватный путь) в файле нет, ссылок нет вовсе — значит нечему вести в несуществующий файл. Строка карты документации есть и называет и читателя, и два момента (`docs/README.md:82`).

CI последовательность (`validate`, `pytest`, `ruff check`, `ruff format --check`, `mypy`) я выполнить не смог: в снапшоте нет `.venv`, а запуск `uv` требует подтверждения. Изменение затрагивает только два markdown-файла, в CI нет ни линтера markdown, ни теста, читающего `docs/`, поэтому влияния на последовательность не вижу — но это вывод по составу диффа, а не исполненный прогон.

Advisory: строка в карте документации (`docs/README.md:82`) выбивается из формы соседей — все остальные пункты карты начинаются с императива, адресованного читателю («follow the task lifecycle…», «review the finding…», «understand…»), а новая написана описательно («the defect classes reviews keep finding; an implementer reads it…»). Критерий про «кто читает и когда» она выполняет, так что это не блокер, но формулировку вида «read it before starting a task and check your change against it before finishing — …» карта держала бы однороднее.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "d5894f9a655cd1f22e6fb19c753ceff3ce418892", "verdict": "approved", "findings": [], "advisory_findings": ["doc-map-line-breaks-imperative-form-of-neighbours"]}
AGENTMARSHAL_VERDICT_END
