Проверил diff статически (тесты в этой песочнице запустить не дали — `python -m pytest` требует approval, поэтому выводы ниже основаны на чтении кода, спеки, ADR-0001/0005 и proposal 015).

Что сделано хорошо: quickstart действительно говорит все четыре вещи, которые требует спека; pinned-тест 0.3.0-промпта не тронут, а `_dry_run_prompt` строится через тот же `_REVIEW_PROMPT`; все четыре недокументационных сценария имеют тест с докстрингой, называющей сценарий; журнал в dry run действительно не пишется; `{0}` раньше вылетал непойманным `IndexError`, теперь это внятный отказ.

Ниже — по одной строке прозы на каждый finding.

**F-DRY-RUN-REQUIRES-HEAD-COMMIT** — `dry_run_review` безусловно распаковывает `HEAD` (`src/agentmarshal/journal/review.py:403`), поэтому в инициализированном проекте без ни одного коммита (`git init && agentmarshal init && agentmarshal review --dry-run` — ровно тот greenfield-путь, ради которого флаг и вводится, см. proposal 015) команда падает с кодом 1 и сообщением `dry run failed: git archive failed: fatal: not a valid object name: HEAD`; это противоречит acceptance-критерию «it needs neither a task nor a commit» и сценарию спеки «a dry run needs no task and no commit», а design.md подменяет «no commit» на «не коммит, который назвал оператор» — переформулировка живёт в design.md, но не в контракте; сообщение при этом не называет ни того, что dry run нужен коммит, ни что делать, и теста на этот случай нет.

**A-UNTERMINATED-BRACE-STILL-UNNAMED** — конкретный дефект из proposal 015 §3 («the reporter's value had lost a closing brace to a shell quoting accident, and the message gave nothing to search for») не исправлен: `string.Formatter().parse("{prompt_file")` бросает `ValueError` до того, как токен вообще выделен, и отказ проваливается в generic-ветку `src/agentmarshal/journal/review.py:222-224` — «AGENTMARSHAL_REVIEWER_CMD has an invalid placeholder», без токена и даже без самого аргумента, который не разобрался; комментарий в коде это признаёт сознательно, но назвать хотя бы проблемный элемент шаблона было бы дёшево и закрыло бы именно то, о чём отчитался адоптер.

**A-DRY-RUN-IGNORES-WORK-FLAGS-SILENTLY** — `src/agentmarshal/cli.py:580-593` отвергает при `--dry-run` только `--task` и `--commit`, хотя само сообщение заявляет «judges the configured command, not any work»: `--base`, `--role`, `--vendor`, `--email` и особенно `--reviewed-finding` (который на recorded-пути отвергается явно) проглатываются молча.

**A-DRY-RUN-COMMIT-CHECK-UNDOCUMENTED-UNTESTED** — проверка `verdict[0] != _DRY_RUN_COMMIT` в `src/agentmarshal/journal/review.py:422-426` добавляет строгость, которой нет ни в design.md (где записана только HEAD-departure), ни в quickstart, не покрыта тестом и, в отличие от ветки парсинга, не сохраняет вывод команды; плюс синтетический SHA — это git-овский null-SHA из 40 нулей, который живая модель-ревьюер вполне может отказаться эхом вернуть, превратив рабочую конфигурацию в «reviewer verdict names a commit the dry run did not ask about».

**A-PLACEHOLDER-TEST-PARAM-SELF-MATCHES** — в `tests/test_review_launcher.py:312-323` параметр `"unsupported"` совпадает со словом из самого сообщения («has an unsupported placeholder: …»), так что `assert token in str(...)` для этой половины параметризации держится при любом сообщении с этим словом и не проверяет, что токен назван; реальную работу делает только случай `"0"`.

**A-SNAPSHOT-EXTRACTED-BEFORE-TEMPLATE-VALIDATED** — в `src/agentmarshal/journal/review.py:397-406` полный `git archive HEAD` распаковывается до вызова `_reviewer_command`, поэтому незаданный `AGENTMARSHAL_REVIEWER_CMD` или битый placeholder — то, что флаг и должен диагностировать — оплачиваются распаковкой всего дерева.

**A-REVIEW-USAGE-ERRORS-NOW-EXIT-1** — `src/agentmarshal/cli.py:610-622` заменяет argparse-овские `required=True` ручной проверкой, из-за чего `agentmarshal review` без аргументов теперь печатает строку без usage и выходит с кодом 1 вместо 2, то есть ошибка вызова стала неотличима по коду возврата от «ревью прошло и отказало».

**A-SPEC-HAS-ONE-DOCUMENTATION-SCENARIO-NOT-TWO** — acceptance-критерий исключает «the two documentation scenarios», а в `openspec/specs/reviewer-adapter/spec.md:12-16` (и в архивной копии) документационный сценарий один, хотя нормативных предложений в требовании два и tasks.md делит их на 1.1 и 1.2.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "3767b68b374983f084f045f3e0fe0317a445f972", "verdict": "changes_required", "findings": ["F-DRY-RUN-REQUIRES-HEAD-COMMIT"], "advisory_findings": ["A-UNTERMINATED-BRACE-STILL-UNNAMED", "A-DRY-RUN-IGNORES-WORK-FLAGS-SILENTLY", "A-DRY-RUN-COMMIT-CHECK-UNDOCUMENTED-UNTESTED", "A-PLACEHOLDER-TEST-PARAM-SELF-MATCHES", "A-SNAPSHOT-EXTRACTED-BEFORE-TEMPLATE-VALIDATED", "A-REVIEW-USAGE-ERRORS-NOW-EXIT-1", "A-SPEC-HAS-ONE-DOCUMENTATION-SCENARIO-NOT-TWO"]}
AGENTMARSHAL_VERDICT_END
