Проверил ADR-0013, правку ADR-0012 §6 и строку в карте документации против файлов, на которые они опираются (ADR-0007, ADR-0009, ADR-0010, ADR-0012, proposal 009, proposal 040, `docs/overview.md`, `src/agentmarshal/journal/gate.py`).

Что сошлось: структура ADR-0013 повторяет ADR-0011/ADR-0012 (заголовок, Status/Date, «Builds on», оговорка о нереализованности, Context, Decision, Left open, Consequences, Alternatives); «builds on» называет и линкует ADR-0007, ADR-0010, ADR-0012, заявляет частичный пересмотр ADR-0010 и ответ на proposal 009, а решение о местоположении локального состояния упоминает без номера; все перечисленные в контракте пункты решения на месте (D1–D19, пример манифеста, три секции в конце); чтение манифеста с базовой стороны совпадает с ADR-0010 D2; места запуска гейта (CI — `.github/workflows/agentmarshal-governance.yml:40`, merge-authority-обёртка — `docs/self-hosting-workflow.md:32`, `complete` — там же, п. 5) подтверждаются; формулировка в ADR-0012 §6 про «journal write without the shared checkout, accepted into the journal-transactions work of proposals 019 and 035» дословно совпадает с диспозицией proposal 040 (`docs/proposals/040-...md:93-97`), а клауза про process log теперь читается ровно; строка в `docs/README.md:26` сделана по форме соседних.

Полную последовательность CI я не выполнял: запуск команд в этой песочнице не разрешён, а снапшот не является git-репозиторием, так что `validate`/`gate` всё равно не отработали бы честно. Диф чисто документационный, ни один тест на эти файлы не ссылается — ожидаемого влияния на CI нет, но как проверенный факт я это не заявляю.

Блокирующее:

**`adr0013-lane-count-contradicts-findings-lane`** — в Consequences (`docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:244`) сказано «The gate gains a third lane — operational — alongside the regular and the journal lanes». Это утверждение о текущем поведении, и оно не сходится с файлами: `docs/overview.md:134` прямо пишет «the gate recognizes three kinds of work» — journal-only, diff и findings-дорожка, — а findings-дорожка реализована отдельной точкой входа `run_findings_gate` в `src/agentmarshal/journal/gate.py:90` по решению ADR-0009 D3. Операционная дорожка, таким образом, четвёртая, а не третья, и перечисление «regular и journal» пропускает существующую. Правка локальная — только эта строка; D17 («a gate lane of its own, next to the journal one») счёта не называет и корректна.

Рекомендательное:

**`adr0013-operational-lane-revisits-adr0010-unnamed`** — D17 (строки 172–180) вводит дорожку, на которой изменение `.agentmarshal/extensions/switches.toml` проходит без ревью. ADR-0010 D2 решает обратное именно для этого каталога: «`.agentmarshal/extensions/` lies outside `.agentmarshal/journal/`, so a manifest-only change already takes the diff lane and needs a review» (`ADR-0010-process-extensions.md:112-115`, повтор в Consequences, строка 227) с обоснованием «it is configuration, and configuration is reviewed». Шапка ADR-0013 перечисляет пересмотр ADR-0010 ровно двумя пунктами (хуки сняты, отказ от инсталлятора стоит) и этот третий не называет.

**`adr0013-manifest-example-contradicts-decisions`** — комментарии в примере манифеста (строки 219–220) задают ограничения, которых нет в самих решениях и которые им противоречат: `env = [] # always empty for pre-gate` жёстче пола из D8, где для `pre-gate` запрещены только «provider secrets», а переменные по именам объявляются «for any stage»; `writes = "none" # none | process-log (post-gate only)` запрещает запись в process log на `pre-gate`, тогда как таблица возможностей (строка 107) даёт «writes to the process log — yes» обоим scope без оговорки о стадии, а D10 называет process log единственным, куда личное расширение вообще пишет.

**`adr0013-records-model-reference-dangling`** — D18 (строка 191) отсылает к «the decision on the records model»; в репозитории такой документ не называется нигде, кроме этой строки (грепом по `docs/` и CHANGELOG — единственное вхождение). Если имелся в виду ADR-0004 или ADR-0005, их по критерию 3 надо назвать и залинковать; если это будущее решение — контракт санкционировал ровно одну безномерную отсылку, про местоположение локального состояния.

**`adr0012-extensions-decision-still-unnumbered`** — ADR-0012 входит в scope задачи, и после публикации ADR-0013 три его отсылки к безымянному «separate decision on how extensions run» (строки 60, 79–80, 152–153) указывают на документ, у которого теперь есть номер и файл; читатель ADR-0012 перейти по ним не может.

**`adr0013-switches-path-collides-with-manifest-naming`** — D17 кладёт файл переключателей в `.agentmarshal/extensions/switches.toml`, то есть ровно по тому пути, который ADR-0010 D1 резервирует под манифест расширения с именем `switches` (`.agentmarshal/extensions/<name>.toml`). Коллизия имён в одном каталоге, где после D9 уже соседствуют `<name>.toml` и `<name>/`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "9b2e5a224ef26b95b50392d2938cd8ff7ac28dbe",
  "verdict": "changes_required",
  "findings": ["adr0013-lane-count-contradicts-findings-lane"],
  "advisory_findings": [
    "adr0013-operational-lane-revisits-adr0010-unnamed",
    "adr0013-manifest-example-contradicts-decisions",
    "adr0013-records-model-reference-dangling",
    "adr0012-extensions-decision-still-unnumbered",
    "adr0013-switches-path-collides-with-manifest-naming"
  ]
}
AGENTMARSHAL_VERDICT_END
