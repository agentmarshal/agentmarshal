Прошёлся по диффу, сверил утверждения о поведении инструмента с кодом и статусы с индексом.

**Что проверено и сходится.** Правка 032 теперь точна и подтверждается кодом: `journal_only = all(path.startswith(_JOURNAL_PREFIX) ...)` (`src/agentmarshal/journal/gate.py:650`), транскрипт дословно `PASS: journal-only transaction (deterministic lane; review not required)` (`gate.py:738-741`), и ветка действительно обходит и scope-проверку, и review-проверки целиком (`gate.py:741-985`) — принятая часть сформулирована как вынос существующей полосы в обязательную проверку, как требует критерий 4. 037 верна по коду с обеих сторон: `review`-хелпер декодирует вывод git строго (`src/agentmarshal/journal/review.py:198-214`, `encoding="utf-8"` без `errors=`), а хелпер ворот декодирует так же, но ловит ошибку и деградирует до `WARN: leak-scan skipped (...)` (`gate.py:241-261`, `gate.py:1147-1148`) — ровно то, что цитирует 026 finding 4; смещение 15936543 ≈ «около 16 MB» сходится. 035 — строка индекса теперь перечисляет все три принятые части (`035-...md:90-102`). 034 — Where и тело согласованы и называют решение, а не неопубликованный документ. 024 и 026 несут новые статусы согласованно в шапке, Disposition, Where и строке индекса; `review --since` остаётся deferred с причиной. Арифметика измерений сходится: 040 — шесть застоев по шести пунктам; 039 — 46 задач, 15/46, 9/46 из них 6; 038 — 16 скриптов / 2 700 строк / 3 800 строк тестов / шесть мест повторены в Disposition без расхождений. Все хеши — 64 знака нижним регистром, дублей по каталогу нет. Введение батча перечисляет ровно четырнадцать тем плюс отзыв; строки индекса 037-040 и карта документации на месте; все ссылки разрешаются; ни одного релиза, предложения или документа вне опубликованных не названо.

**Чего проверить не смог.** Оригиналы репортёра 022-025 и документ координатора с dispositions в снапшот не входят, поэтому дословность измерений, совпадение sha256 и «top section overriding the rows» (критерии 1-2) непроверяемы. Полную последовательность CI запустить не удалось: `uv run pytest` в этой песочнице требует approval. Дифф — только markdown, тестов, читающих содержимое `docs/proposals/`, нет, так что причин для падения не вижу — но утверждать, что критерий 5 выполнен целиком, не могу.

Блокирующее: в `docs/proposals/033-contract-review-before-implementation-does-not-pay-off.md:3` и в строке индекса `docs/proposals/README.md:100` диспозиция теперь — `recorded`, но раздел «Disposition» того же индекса (`docs/proposals/README.md:26-38`) объявляет закрытый набор из трёх значений — **accepted**, **deferred**, **declined** — словами «Every proposal carries one», и в этом диффе не расширен. Критерий 2 требует диспозиции «in the index's vocabulary», а раздел «Tracking what happened to yours» обещает репортёру, что диспозиция читается по этому словарю; репортёр 033 получает слово, которого в словаре нет. До этой правки строка несла `accepted`, то есть расхождение внесено здесь.

Ниже — непреграждающие замечания.

В `docs/proposals/039-review-findings-do-not-feed-back-into-the-next-round.md:103-104` обоснование занижает то, что инструмент уже печатает: «`status` today projects only the lifecycle state — a task is open, done or abandoned — and prints no verdict counts at all». Проекция действительно даёт только состояние (`src/agentmarshal/journal/status.py:40-43`), но `agentmarshal status <task>` печатает каждую review-запись со своим `verdict=`, `findings=N` и `advisory=N` (`src/agentmarshal/cli.py:536-552`), так что `changes_required` сегодня видны построчно — не хватает именно счётчика. Это тот же класс неточности, который критерий 4 велел исправить в 032.

В `docs/proposals/039-...md:102-107` пункт 4 предложения репортёра просит тормоз в «`status` (and the gate output)» (`039-...md:61`), а диспозиция и Where отвечают только про `status`; половина про вывод ворот не получает ни принятия, ни отказа, хотя критерий 2 требует диспозиции для каждой части файла.

В `docs/proposals/README.md:107` строка 040 теряет «in part», которое несёт шапка файла (`040-...md:3`: «accepted *(in part; the stuck-step visibility is met by a supplied watcher template, not a record type)*»), а строка 105 для 038 не упоминает, что потребность закрывается поставляемым kit'ом — это сказано только в столбце Where. Шапки и строки индекса здесь сжаты неодинаково.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "08c548805b8178f5c10257b0d55b46beba429ae1",
  "verdict": "changes_required",
  "findings": [
    "033-disposition-recorded-not-in-index-vocabulary"
  ],
  "advisory_findings": [
    "039-status-already-prints-each-verdict",
    "039-gate-output-half-of-the-brake-undisposed",
    "index-rows-compress-headers-unevenly-038-040"
  ]
}
AGENTMARSHAL_VERDICT_END
