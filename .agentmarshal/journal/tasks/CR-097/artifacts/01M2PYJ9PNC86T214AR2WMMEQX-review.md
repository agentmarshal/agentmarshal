Проверил диф против контракта CR-097, дельту спеки, применённую спеку `openspec/specs/reviewer-adapter/spec.md`, ADR-0001 и ADR-0005, а также обе документационные сцены в `docs/quickstart.md`.

Что сходится:

- Все пять сценариев дельты покрыты: четыре — тестами, чьи docstring'и называют сценарий дословно (`test_unsupported_placeholder_is_named_in_the_refusal`, `test_dry_run_reports_a_parseable_verdict_without_changing_the_journal`, `test_dry_run_reports_when_it_cannot_parse_a_verdict`, `test_dry_run_requires_no_task_or_commit`), документационный — самим `docs/quickstart.md:46-66`.
- Dry run ничего не пишет: промпт, снапшот и вывод живут в `tempfile.TemporaryDirectory`, `_parse_verdict(..., preserve_output=False)` не создаёт файл в журнале, а `_tree_contents` в тесте сравнивает журнал побайтово до и после.
- `_dry_run_prompt` идёт через тот же `_review_prompt`/`_REVIEW_PROMPT`, константа не тронута, и закреплённый 0.3.0-тест `test_prompt_without_named_material_is_the_prompt_written_before_schema_2` остался с неизменёнными ожиданиями.
- Отступление от design.md (снапшот `HEAD` вместо пустого каталога) записано в самом design.md, как того требует acceptance.
- `_reviewer_command` теперь называет отвергнутый токен, а тест проверяет только вхождение токена, а не всю фразу.
- Квикстарт заявляет все четыре вещи, чекбоксы в tasks.md проставлены, никаких изменений в gate или в записываемом ревью нет — Non-Goals соблюдены.

Блокирующих находок нет. Три замечания ниже — advisory.

ADV-BRACE-POSITION-MISLEADS — в `src/agentmarshal/journal/review.py:232` ветка «invalid placeholder» вычисляет `template_text.rfind("{")` по всей строке команды, хотя ошибка пришла от конкретного элемента после `shlex.split`. Для `reviewer --model {model:d} --prompt {prompt_file}` скан пропускает оба поля (имена известны), `.format()` падает на `{model:d}`, а сообщение указывает на символ 36 — это валидный `{prompt_file}`, тогда как проблемная скобка на 17. Комментарий рядом утверждает, что «позиция последней открывающей скобки — это то, что оператору нужно, чтобы её найти», а это верно только когда плохая скобка идёт последней. Ровно тот класс «ошибка ничего не называет», из-за которого написана proposal 015.

ADV-DRY-RUN-SNAPSHOT-BEFORE-COMMAND-RESOLUTION — в `src/agentmarshal/journal/review.py:415-441` `dry_run_review` пишет промпт, дёргает `git rev-parse` и разворачивает полный `git archive` HEAD, и только потом зовёт `_reviewer_command`, который и отказывает при неустановленном или сломанном `AGENTMARSHAL_REVIEWER_CMD`. То есть аудитория, ради которой флаг и сделан, платит за распаковку всего дерева, прежде чем услышать «no reviewer command configured». Резолвинг команды дешевле поднять до снапшота.

ADV-NAMED-DOCUMENT-PATH-ABSENT — контракт называет документ `openspec/changes/document-the-reviewer-contract/` (и acceptance ссылается на `.../specs/reviewer-adapter/spec.md` внутри него), но диф создаёт change только по архивному пути `openspec/changes/archive/2026-09-17-document-the-reviewer-contract/`. Gate не падает — проверка «named documents touched» проходит за счёт второго названного документа `openspec/specs/reviewer-adapter/`, — но путь из шапки контракта не существует ни в одном коммите, и независимый проверяющий по нему ничего не найдёт.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e965819ed4875a8a3020abb7a262da779b4a96c3", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-BRACE-POSITION-MISLEADS", "ADV-DRY-RUN-SNAPSHOT-BEFORE-COMMAND-RESOLUTION", "ADV-NAMED-DOCUMENT-PATH-ABSENT"]}
AGENTMARSHAL_VERDICT_END
