Проверил контракт, дифф и фактическое состояние файлов в снапшоте. Блокирующих дефектов не нашёл — все восемь сценариев из обоих spec-дельт покрыты тестами с именующими их docstring'ами, рендер хитов действительно общий для gate и standalone-команды, self-match задавлен ровно по местоположению, а диагностика reviewer'а кладётся вне журнала и называется путём. Четыре замечания — не блокирующие.

**ADV-001-diagnostics-prefix-collides-with-snapshot-leak-glob** — `_preserve_reviewer_diagnostics` в `src/agentmarshal/journal/review.py:317` даёт префикс `agentmarshal-reviewer-stderr-`, который попадает под glob `agentmarshal-review-*` в `_assert_no_snapshot` (`tests/test_review_launcher.py:180`): сохранённый stderr будет засчитан как утёкший snapshot-каталог. Сегодня ни один тест на это не наступает только потому, что `_reviewer_stub` по умолчанию пишет в stderr пустую строку.

**ADV-002-config-path-literal-duplicated-three-ways** — путь конфига, по которому решается подавление self-match, существует тремя независимыми литералами: `_PROJECT_CONFIG_PATH` в `src/agentmarshal/journal/capture.py:277`, `_PROJECT_FILE` в `src/agentmarshal/journal/gate.py:52` и голая строка `".agentmarshal/project.json"` в `src/agentmarshal/cli.py:1294`. Рендерер объединили именно ради «две стороны не могут разойтись», а ключ подавления — нет; в non-sidecar ветке CLI аргумент вообще можно было не передавать и взять значение по умолчанию.

**ADV-003-diagnostics-keep-failure-discards-recorded-review** — `_keep_diagnostics` в `src/agentmarshal/journal/review.py:326` при `OSError` поднимает `ReviewLaunchError` до вызова `submit_review`, то есть неудача записи вспомогательного temp-файла уничтожает уже полученный отзыв целиком; соседний `_reject` в той же ситуации деградирует строкой «raw output could not be kept», и комментарий `# pragma: no cover - preservation is best effort` на этой же строке обещает именно best-effort.

**ADV-004-outbox-pathspec-needs-shell-quoting** — в `src/agentmarshal/project.py:233` README отдаёт pathspec `:(exclude).agentmarshal/upstream/**` без кавычек и без команды целиком, тогда как соседний совет дан полной командой `git add .agentmarshal/journal`; скобки — метасимволы bash, и вставка этой строки в шелл как есть падает синтаксической ошибкой ровно у того адоптера, которому она адресована.

Отдельно отмечу, что остаточный случай из proposal 020 — маркер, попавший в захваченные artifact-файлы, которые цитируют диф конфига, — этой реализацией не снимается, но это осознанно зафиксировано в contract'е («the narrowing is bounded by location») и в сценарии «a marker elsewhere in the same content is still reported», поэтому дефектом против контракта не считаю.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "30176f407593324f0d2e8ef7e52f61a467bab005", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-001-diagnostics-prefix-collides-with-snapshot-leak-glob", "ADV-002-config-path-literal-duplicated-three-ways", "ADV-003-diagnostics-keep-failure-discards-recorded-review", "ADV-004-outbox-pathspec-needs-shell-quoting"]}
AGENTMARSHAL_VERDICT_END

Замечание о проверке: тесты я не запускал — команда `pytest` в этой сессии требует подтверждения и была отклонена, так что прохождение тестов я вывел чтением кода и тестов, а не исполнением.
