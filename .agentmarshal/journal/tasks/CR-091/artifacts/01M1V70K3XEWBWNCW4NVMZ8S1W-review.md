Не смог выполнить `uv run pytest` — команда потребовала подтверждения и была отклонена, так что проверка построена на чтении кода, а не на прогоне suite. Все семь сценариев спеки нашли себе тест с называющим их docstring, архив и baseline на месте, `openspec/changes/keep-review-prose/` действительно переехал в `archive/2026-09-06-keep-review-prose/`. Блокирующих дефектов не нашёл; ниже — advisory.

A-003 — `design.md` (решение «Verbatim, unredacted») обосновывает отказ от редактирования тем, что «the leak scan already runs over candidate additions in the completion transaction», но это неправда для самих байтов prose: `gate.py:1094-1104` сканирует диапазон `merge_base..resolved_commit`, то есть кандидата, а review-запись и её артефакт лежат в рабочем дереве журнала незакоммиченными до тех пор, пока gate не прошёл (docstring `gate.py:1-12`, quickstart.md:281-286 и 365) — их не видит ни один сканер, и в design.md отступление не зафиксировано, хотя acceptance-критерий 1 этого требует.

A-005 — `submit_review.py:75-100` вручную дублирует две проверки из `write_record` (включая скопированную строку сообщения об ошибке, ср. `records.py:682-692`), но покрывает не все её отказы: штамповка и валидация `recorded_by`, проверка ULID, несовпадение `task` и любая ошибка ФС срабатывают уже *после* `write_artifact`, оставляя нецитируемый `.md` в каталоге, который gate теперь держит append-only; а при изменении сообщения в `write_record` предвалидация молча разойдётся с ней.

A-004 — `gate.py:1024` проверяет коллизию путей с базовым деревом только по `added_records`, куда артефакты не входят: два кандидата, независимо добавившие один и тот же путь под `tasks/<id>/artifacts/`, столкнутся при merge без строки отказа, хотя ровно для этого случая у записей проверка есть, а правило append-only на артефакты уже распространили.

A-002 — `review.py:438-443` по-прежнему кладёт полный вывод ревьюера в неудаляемый файл системного temp при принятом вердикте с findings, хотя обоснование этого в docstring `_preserve_output` («the record keeps the finding's id and not one word of what it claims») — ровно та проблема, которую данное изменение и закрывает; копия стала избыточной и растаскивает verbatim prose за пределы решения о размещении журнала (ADR-0008), а design.md причину сохранения не фиксирует.

A-001 — docstring `SubmittedReview` в `submit_review.py:28-33` теперь описывает поле неверно: там сказано, что `reviewer_output_path` живёт «for compatibility with the rejected-verdict path», но отклонённый вердикт вообще не возвращает `SubmittedReview` (`review.py:433` бросает исключение) — поле заполняется только на успешном пути, когда принятый вердикт называет blocking или advisory findings.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "a42964b709042855e4e264a1ed38b574322944ce", "verdict": "approved", "findings": [], "advisory_findings": ["A-003", "A-005", "A-004", "A-002", "A-001"]}
AGENTMARSHAL_VERDICT_END
