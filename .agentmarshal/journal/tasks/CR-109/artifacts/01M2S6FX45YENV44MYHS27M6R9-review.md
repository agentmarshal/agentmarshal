Выполнить тесты не получилось: запуск `pytest` требует разрешения, а в этой сессии его нет. Поэтому `tests/test_quickstart.py`, `tests/test_smoke.py` и закреплённые тесты 0.3.0 я проверял только чтением кода. Если найдёшь пропущенное — скажи.

**Что сходится**
- **Версия.** Везде стоит 0.4.0: `pyproject.toml`, `src/agentmarshal/__init__.py`, `uv.lock`, `test_smoke`.
- **Схемы 4, 5 и 6 в UPGRADING** описаны точно:
  - `create_review_record` ставит schema 5 только при `reviewed_contract`. Этот hash передаёт только `review.py:883`, а `submit-review` его не передаёт.
  - schema 6 бывает только у coordination-сессии.
  - `records.py:210` выдаёт ровно ту формулировку отказа, которую цитирует UPGRADING.
- **CHANGELOG.** Все 25 задач с CR-084 по CR-108 завершены, и каждая названа в каком-то разделе. Флаги `--findings`, `--reviewed-finding`, `--without-review`, `--dry-run` существуют. Лимит в 20 строк (`gate.py:68`) и три проверки preconditions в `doctor` совпадают с текстом.
- **Три advisory-замечания CR-107 закрыты:**
  - заголовок roadmap в overview больше не говорит «designed»;
  - в proposal 005 есть пометка о superseded-очерёдности и датированная секция;
  - комментарий job `governance` дословно совпадает с `templates/github/agentmarshal-governance.yml:24-27`.
- **Упоминания 0.3.0,** которые остались, относятся к истории: sidecar new in 0.3.0, record-session since 0.3.0 и тесты с закреплённым релизом.

**Блокирующее**

`docs/proposals/README.md:98`: в колонке Where для proposal 019 записано «0.4.0, templates». Сама disposition 019 говорит «Accepted for the next release». Но в 0.4.0 нет ни документированного protected-base паттерна, ни скрипта: в `templates/` лежит только GitHub workflow, и ни одна задача CR-084–CR-108 этим не занималась. После тега индекс отправит читателя в релиз, где этого нет. А запись CHANGELOG о CR-094 обещает «a way to follow each accepted item».

**Advisory**

- `UPGRADING.md`: не сказано, что `agentmarshal review` теперь кладёт файл с прозой ревьюера рядом с record, в `tasks/<id>/artifacts/`. Этот файл нужно коммитить вместе с record: `validate.py:56-94` падает, если pinned artifact отсутствует. Кроме того, при успешном ревью temp-копия больше не создаётся. Wrapper, который добавляет в git только `records/`, после первого ревью на 0.4.0 получит красный `validate`.
- `CHANGELOG.md:38-45`: раздел про CR-091 не упоминает новую опцию `submit-review --prose`, хотя это новая пользовательская возможность этого релиза.
- `docs/overview.md:167-170`: из roadmap тихо убрано направление «required machine-readable acceptance criteria … gates enforce it». При этом `docs/adr/ADR-0004-journal-data-model.md:139` и `docs/migration-v1-to-v2.md` по-прежнему говорят об этом изменении.
- `docs/proposals/README.md:102`: «the command in 0.5.0» называет номер будущего релиза, которого нет ни в одном опубликованном плане.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "aba99fb83248f763fc12ee3746cec95041cb00c7", "verdict": "changes_required", "findings": ["proposals-index-claims-019-ships-in-0.4.0"], "advisory_findings": ["upgrading-omits-review-artifact-must-be-committed", "changelog-omits-submit-review-prose", "overview-drops-acceptance-enforcement-direction", "proposals-index-promises-0.5.0"]}
AGENTMARSHAL_VERDICT_END
