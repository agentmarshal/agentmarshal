Я разобрал diff статически: запустить `pytest`/`ruff`/`mypy` в этой песочнице не дали (любой вызов `python3` требует approval), так что утверждение «full CI sequence passes» я проверить не смог — ниже только разбор кода, спеки и тестов.

**Что сошлось.** Дельта в `openspec/changes/archive/2026-10-03-outbox-send-and-status/specs/outbox/spec.md` совпадает с `openspec/specs/outbox/spec.md` дословно: MODIFIED-заголовок `outbox check` scans what would be sent and refuses by exit status сохранён буквально, два ADDED-требования добавлены, каждое требование в итоговой спеке встречается ровно один раз, change лежит под `archive/`, а `openspec/changes/` больше ничего не содержит. Все 19 сценариев дельты (1 новый у `check`, 8 у `send`, 10 у `status`) имеют тест, docstring которого называет сценарий. `cli.py` не тронут — обе команды регистрируются из `outbox.py`. Escaped-форма имён (`_shown_name`, outbox.py:181) закрывает все три команды: ни один surrogate-несущий `str` больше не доходит до `print`, и маскирование `safe_path` применяется уже к escaped-строке, так что marker в не-UTF-8 имени по-прежнему маскируется. Разбор `git diff --cached --name-status -z` корректно учитывает обе половины rename/copy, а replay через `git update-index --index-info` для SHA-1 репозитория по формату git (`mode SP sha1 SP stage TAB path` и `0 SP <40 нулей> TAB path`) разбирается верно.

Теперь три advisory-замечания.

`_restore_outbox_index` в `src/agentmarshal/outbox.py:580` жёстко зашивает null-OID длиной 40 hex (`b"0" + b"0" * 40`). В репозитории с `--object-format=sha256` git ждёт 64 hex и валит весь вызов `update-index --index-info` ошибкой «malformed index info» — падает не только удаление лишних путей, но и replay записанных entries в том же вызове. Отказ при этом остаётся громким (печатается «could not restore the index»), но гарантия спеки «a refused send leaves the index as it found it» в таком репозитории не выполняется; длину стоит брать из самих записей `ls-files --stage` или из `git rev-parse --show-object-format`.

`_staged_paths` в `src/agentmarshal/outbox.py:529` возвращает тройки `(status, path, source)`, но `status` не читает ни один из двух вызывающих — оба деструктурируют его в `_` (строки 624 и 652). Внутри парсера статус нужен, в возвращаемом значении — мёртвые данные; функция могла бы отдавать просто множество затронутых путей.

`send` пишет отчёт `check` и SHA коммита в один и тот же поток: `_run_check` печатает «outbox check: N draft(s) checked; all conform…» в stdout (outbox.py:593 → :486), а затем туда же уходит `print(commit)` (outbox.py:680). `COMMIT=$(agentmarshal outbox send)` поэтому даёт не коммит, а несколько строк — сам тест обходит это через `out.strip().splitlines()[-1]`. Спека этого не запрещает, но для «the commit, for whatever delivery the operator chooses» отчёт лучше было бы увести в stderr.

Блокирующих дефектов не нашёл.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "7fc703877c75255a43e1cb4e707d7189c1fe567d", "verdict": "approved", "findings": [], "advisory_findings": ["restore-null-oid-assumes-sha1-object-format", "staged-paths-returns-unused-status-element", "send-stdout-mixes-check-report-with-commit-sha"]}
AGENTMARSHAL_VERDICT_END
