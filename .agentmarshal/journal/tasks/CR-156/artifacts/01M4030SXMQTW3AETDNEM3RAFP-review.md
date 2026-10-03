Проверил контракт CR-156, delta-спеку, `src/agentmarshal/outbox.py`, `tests/test_outbox.py`, архив change-а и соседний код (`gate.py`, `project.py`, `cli.py`).

**Что сходится**

- Архив на месте (`openspec/changes/archive/2026-10-03-outbox-send-and-status/` с proposal, design, tasks, delta), `openspec/changes/` пуст, в `openspec/specs/outbox/spec.md` каждое requirement ровно один раз, MODIFIED-заголовок `outbox check` scans what would be sent and refuses by exit status` совпадает дословно, два новых requirement добавлены.
- Все 41 сценарий спеки покрыты тестами, чьи docstring называют сценарий дословно (41 docstring «Scenario: …»).
- `send`: `_run_check` выполняется буквально первым и любой non-zero отказывает (`outbox.py:593`); отказ при staged-чём-либо вне `.agentmarshal/upstream/` учитывает обе половины rename/copy (`outbox.py:622`); stage только `git add --force -- .agentmarshal/upstream`, пустой batch отказывается, один `git commit --message` с перечислением файлов, печать `rev-parse HEAD`. Сети нет.
- Откат индекса через `ls-files --stage -z` → `update-index -z --index-info` корректен, в том числе на unborn HEAD; порядок `-z` перед `--index-info` обязателен и соблюдён.
- `status`: sha256 lowercase hex, парсинг и bare, и `**Source:** \`sha256:…\``, entry идентифицируется digest-ом (две записи в строке — две entry, один digest в двух строках — одна), отказ на нечитаемый index и на отсутствующий outbox, non-regular/нечитаемый файл → non-zero.
- `_shown_name` (`os.fsencode` + `backslashreplace`) применён везде, где имя печатается или сканируется, в `check`, `send` и `status`; маскировка `safe_path` идёт по уже escape-нутому имени, так что marker в не-UTF-8 имени остаётся замаскированным.
- Регистрация обоих subcommand-ов живёт в `outbox.py:97-111`, в `cli.py` только hook (`cli.py:348`, `cli.py:1235`).

CI-последовательность запустить в этой песочнице не могу (git/python требуют approval) — оценивал статически.

**Замечания (не блокирующие)**

`send-git-error-echoes-commit-message` — в `src/agentmarshal/outbox.py:524` текст ошибки собирается как `git {' '.join(arguments)} failed`, а для коммита в `arguments` лежит весь многострочный message, поэтому отказ hook-а печатает в stderr (`outbox.py:678`) обратно весь `outbox: findings batch` со списком файлов; имена при этом замаскированы и escape-нуты, так что это только читаемость, а не утечка.

`restore-hardcodes-sha1-null-oid` — в `src/agentmarshal/outbox.py:580` строки удаления формируются с 40 нулями; в репозитории с `--object-format=sha256` `update-index --index-info` отвергнет такую строку (`hexsz` 64), и после неудачного коммита то, что застейджил `send`, останется в индексе — команда честно сообщит «could not restore the index», но требование «refused send leaves the index as it found it» не выполнится. Остальной код (`gate._resolve_commit` с проверкой длины 40) уже предполагает sha1, так что это согласованное ограничение, не регрессия.

`restore-runs-after-successful-commit` — в `src/agentmarshal/outbox.py:666` `git rev-parse HEAD` стоит внутри того же `try`, что и `commit`, поэтому его отказ уже после успешного коммита приведёт к откату индекса к pre-add состоянию и сообщению об отказе, хотя коммит создан: оператор узнает об отказе, но не о коммите. Вероятность крайне низкая (сбой `rev-parse` сразу после удачного `commit`).

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "7fc703877c75255a43e1cb4e707d7189c1fe567d", "verdict": "approved", "findings": [], "advisory_findings": ["send-git-error-echoes-commit-message", "restore-hardcodes-sha1-null-oid", "restore-runs-after-successful-commit"]}
AGENTMARSHAL_VERDICT_END
