Разобрал ADR против contract'а: прошёл по каждому acceptance criterion, сверил ссылки и все утверждения о текущем поведении с файлами, на которые они опираются (`gate_context.py`, `gate.py`, `steps.py`, `cli.py`, `docs/self-hosting-workflow.md`), и сверил декларативную часть с ADR-0007/0008/0012/0013/0014/0015/0016/0018/0019/0022 и proposals 034/036/038/041/042/043.

Что проверено и сходится:
- девять actions (§3), одиннадцать правил first-match с тремя определениями (§4), «что считается attempt» (§5), вывод в text/JSON с escaping только в text (§6, согласуется с ADR-0015 D5 и с `display.py`, которым пользуются только текстовые view), reference driver в adopter kit (§8), Left open — всё на месте;
- оба operator-решения названы именно решениями: A — refinement disposition'а proposal 036 (и прямо назван refinement'ом), B — порог считается от последнего `amendment`, а `status` продолжает считать по всей задаче (сходится с ADR-0016 D4);
- ревизии названы в header: ADR-0019 decision 5 (там действительно «vocabulary stays documentation... neither checks nor counts»), disposition proposal 036 («review и gate refuse a candidate whose producing session did not end `implemented`»), ADR-0014 (D9 называет читателями `status` и `doctor`; gate по-прежнему не читает log — `process_log` импортирует только `steps.py`);
- факты о текущем поведении верны: branch policy `(feat|fix|docs|ci|completion)/(CR-\d+)-\S+` с отказом на двух id, default base `origin/HEAD` → `master` → отказ; refusals «candidate range contains no changes» (gate.py:648) и «the opening transaction must merge before implementation» (gate.py:806); pipeline attestation берёт SHA у invoker'а (gate.py:1041); `complete --base` должен быть ancestor'ом; `git merge-tree --write-tree` действительно пишет tree-объекты;
- форма ADR-0012..0022 соблюдена (Context, Decision, Left open, Consequences, Alternatives considered), все 16 ссылок резолвятся в существующие файлы, proposals названы как «proposal NNN»;
- приватных документов, adopter'ов, клиентов в тексте нет; `0.5.0` упомянут один раз и имеет прецедент в уже опубликованных ADR-0012, ADR-0022 и `docs/README.md`.

Ниже — пять non-blocking замечаний по точности.

Правило 10 (строка 229) отбирает «the latest implementer session», но его bullet про `environment-failure` (строки 242–244) распоряжается и «a reviewer's» session — случай, который собственный селектор правила не выбирает (действие во всех разобранных сценариях совпадает, расходится только пометка «origin not recorded»).

Строка 265 ссылается на «ADR-0013's decision 5», но решения ADR-0013 пронумерованы буквами A–F: цитируемый текст — пункт 5 внутри раздела A.

Правило 11 (строки 255–269) перечисляет gate-проверки, решаемые по records без pipeline, но пропускает append-only / validity / collision-free проверки записей (ADR-0007 decision 3), которые тоже решаются по одному журналу, — поэтому `next` может ответить `complete` там, где gate откажет.

Bullet в Consequences (строки 362–366) называет machine-local только step- и plan-правила, тогда как условие «no extension pause standing» правила 11 тоже читается из локального process log (§2, строки 145–147).

Bullet «How it works today» про вывод входов gate (строки 77–83) не упоминает, что в sidecar вывод task из branch запрещён и `--task` обязателен (`cli.py:679-690`).

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "e9c8932933d63ec8318f86da6c3eeb46c1c2a861", "verdict": "approved", "findings": [], "advisory_findings": ["rule-10-selector-names-a-reviewer-session", "adr-0013-decision-5-mislabelled", "rule-11-omits-record-integrity-checks", "machine-local-rules-understated-in-consequences", "gate-task-derivation-sidecar-exception-unstated"]}
AGENTMARSHAL_VERDICT_END
