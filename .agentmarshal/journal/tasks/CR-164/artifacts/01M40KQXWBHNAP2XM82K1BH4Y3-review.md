Разобрал diff, прочитал `gate.py`, `cli.py`, `display.py`, `records.forges_rendered_text`, `placement.py`, новые тесты и обе спеки.

Что сделано верно (проверил по файлам):

- `GateError.__init__` escape'ит сообщение при создании (`gate.py:88`), и все raise-сайты передают ровно один `str` — в `src/` нет ни одного `GateError()` без аргумента, ни подкласса, ни многострочного сообщения, поэтому сужение сигнатуры ничего не ломает; повторный escape в обёртках (`gate.py:244`, `_manifest_from_tree`, `say`) идемпотентен, т.к. `\` не входит в refused-набор.
- Весь transcript идёт через `say`/`check` — других записей в `lines` нет (`gate.py:123`, `643`), так что scope-линия, rename source/target, record-пути, extension/manifest-пути и WARN-линии leak-scan escape'ятся в одной точке.
- `placement.evidence_line`/`advisory_notice` — фиксированный текст, так что escape в `_placement` (`cli.py:415`) закрывает единственный placement-канал с недоверенным значением (host из `project.json`).
- `Cs` входит в `_FORGEABLE_CATEGORIES`, поэтому surrogate-путь из `str(OSError)` теперь печатается как `\udcXX`, а не падает на encode.
- Утверждение design.md «каждый listing, против которого матчится имя, читается NUL-separated» после патча верно: `diff --name-status -z`, `status -z`, `ls-tree -z` (база и кандидат), `log --name-only -z`.

Три замечания.

**1 (blocking).** `openspec/changes/archive/2026-10-03-escape-gate-paths-and-errors/proposal.md:43` утверждает «No fixture changes and no `cli.py` change», хотя `src/agentmarshal/cli.py:408-415` изменён в этом же diff (escape placement-refusal) и на него написан тест `test_a_placement_refusal_names_a_forgeable_host_in_escaped_form`. Там же proposal не упоминает две правки listing'ов в `gate.py:393` и `gate.py:684-690`, а «Why» (строка 11) подаёт «the gate reads its path listings raw (`-z`)» как уже существующий факт, хотя для `ls-tree` базового дерева и `log --name-only` это стало правдой только благодаря этому change'у. В `tasks.md` нет ни одного пункта ни про cli.py, ни про `-z`, то есть две из трёх production-правок не записаны и не отмечены. design.md при этом описывает обе честно — не обновлён именно proposal, и он уже заархивирован как постоянная запись.

**2 (advisory).** Переход на `-z` в `gate.py:386-403` и `gate.py:680-690` меняет не отображение, а обнаружение: имя, которое git C-quote'ит (любое не-ASCII, не только refused-символы), раньше не совпадало с сырым именем из diff'а, поэтому record-collision и append-only его не видели, а теперь видят. Ни в record-text-safety, ни в scope-enforcement нет требования, которое бы это фиксировало — добавленные требования говорят только про escape на выводе. При этом два теста, которые реально пинят именно эту правку (`test_a_record_collision_names_a_path_carrying_a_refused_character_in_escaped_form`, `test_a_tampered_evidence_path_carrying_a_refused_character_is_named_in_escaped_form`), в docstring'ах подписаны display-сценариями, так что в будущем причину правки видно только в design.md.

**3 (advisory).** `gate.py:684-690` расширяет жёсткий отказ на не-UTF-8 имена с diff'а кандидата на всё базовое дерево: `_run_git` декодирует strict (`gate.py:282`), а `ls-tree -z` отдаёт сырые байты, поэтому один файл с не-UTF-8 именем где угодно в базовом дереве превращает любой запуск gate в `GateError: git produced non-UTF-8 output` вместо вердикта — раньше C-quoted форма декодировалась как ASCII и gate доходил до transcript'а. Направление fail-closed и согласовано с `test_gate_refuses_non_utf8_git_output`, но ни в design.md Decisions, ни в тестах этот расширенный радиус не зафиксирован.

Про CI ничего не оспариваю: fixtures не тронуты, и «byte-identical» в операциональном смысле (фикстуры + существующие тесты) выполнено.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "c75dac60a04921d9fee694c95fec816d6da8e839", "verdict": "changes_required", "findings": ["proposal-denies-the-cli-change-and-omits-the-z-listing-changes"], "advisory_findings": ["z-listing-change-alters-detection-without-a-requirement", "base-tree-z-widens-the-non-utf8-refusal"]}
AGENTMARSHAL_VERDICT_END
