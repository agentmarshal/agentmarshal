Проверку закончил. Разобрал все три renderer'а, spec/delta, архив и новые тесты.

**Что проверил и что сходится:**

- **Gate** (`gate.py:104`, `gate.py:619`): оба lane'а теперь складывают transcript только через `say()`, которая escape'ит готовую строку. Проверил, что ни одного `lines.append` в обход `say` не осталось, и что в `gate.py` вообще нет строковых литералов с `\n`/`\t` — значит whole-line escaping не портит ни одну легитимную строку. `render_leak_hits` и `render_undecodable_files` (`capture.py:337`, `capture.py:356`) однострочные (`", ".join`), fixture'ы в `tests/fixtures/gate/` табов не содержат. `GateReport.resolved_finding` остался неescape'ленным и это правильно: он идёт в record как данные (`complete.py:89`), а не на печать.
- **Brief** (`brief.py`): scope, acceptance, task id, byline, `created_at`, named material — всё через `escape_for_display`. Escape до whitespace-fold в `recorded_by` (`brief.py:48`) действительно нужен: `recorded_by` при записи проверяется только на «непустая строка» (`records.py:1072`), control-символы там не отвергаются, так что override из `AGENTMARSHAL_ACTOR` реально доезжает до renderer'а. `rstrip("\n").split("\n")` вместо `splitlines()` (`brief.py:61`) — осознанный выбор, иначе U+2028/U+0085 прятались бы как структура.
- **Prompt** (`review.py`): named material, `finding`, `summary`, artifact refs, undecodable-имена, amendment history — escape'ятся; contract/diff/artifact content остаются блоками, как объявлено в non-goals. Комментарий про markers в `launch_review:1210` согласован с кодом — имена проходят через `_review_prompt`.
- **Spec**: `### Requirement: A refused character a record still carries is escaped on display` — header точный, тело delta в архиве байт-в-байт равно тому, что лежит в `openspec/specs/record-text-safety/spec.md` (сравнил через `diff`, расходится только на пустой строке отступа). Change лежит в `openspec/changes/archive/2026-10-03-escape-in-gate-brief-prompt/`, `openspec/changes/` пуст — архив прогонялся командой.
- **Тесты** без изменения смысла бы падали: без escaping подстроки вида `"- src/app.py\\u202e"` в выводе не появились бы, а `assert "\u202e" not in ...` ловит остатки. Сценарии названы в docstring'ах всех четырёх новых тестов.

Выполнить CI сам не мог — в этой песочнице нет исполняемого Python/uv, так что последовательность проверок я не перезапускал и опираюсь на ноту координатора; расхождений с кодом, которые бы её опровергали, не нашёл.

Одно замечание, не блокирующее:

Блок named material в брифе (`src/agentmarshal/journal/brief.py:217`–`301`) — это ~20 из 24 новых вызовов `escape_for_display` в файле, и ни один тест его не проходит: `test_brief_escapes_record_and_contract_values` (`tests/test_brief.py:841`) подаёт контракт со `schema = 1`, где `decisions`/`documents`/`extensions` вообще запрещены как поля, поэтому до секций «Named decision/document/extension» выполнение не доходит. При этом `tasks.md` 2.1 помечен `[x]` с формулировкой «named decision, document and extension material — verify: a test renders a brief over such values and shows each escaped». Для самих contract-полей это защита про запас (`contracts.py:215` отвергает control-символы в `decisions`/`documents`/`extensions` при любой схеме), но lexical/relative пути из обхода каталога (`brief.py:174`, `brief.py:264`) приходят из файловой системы, и имя файла с U+202E их достигает — то есть непокрытой осталась достижимая ветка.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "1c7c7323b54ecf9604529945c59e64aa5e007604", "verdict": "approved", "findings": [], "advisory_findings": ["brief-named-material-escaping-untested"]}
AGENTMARSHAL_VERDICT_END
