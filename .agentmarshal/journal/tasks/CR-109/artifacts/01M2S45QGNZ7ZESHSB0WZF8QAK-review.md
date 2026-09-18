Ревью закончил. Нашёл одну блокирующую проблему и две некритичные.

Что в порядке:
- **Версия.** `0.4.0` стоит в `pyproject.toml`, `__init__.py`, `uv.lock` и smoke-тесте. Тесты, которые пинят транскрипт 0.3.0 (`tests/test_gate.py`), не тронуты.
- **CHANGELOG.** Все 25 задач с CR-084 по CR-108 упомянуты. Утверждения, которые я проверил по коду, верны: схемы 4/5/6 в `records.py`, лимит в двадцать leak-hit'ов в gate (`gate.py:68`), `reviewed_contract` в `review.py:883`, манифест OpenSpec 1.12.0.
- **UPGRADING.** Есть все обязательные пункты: схемы 4/5/6, отказ writer'ов, reopening, `--without-review` вместе с изменением шаблона, новый вывод leak-scan.
- **Workflow.** Комментарий job'а `governance` теперь совпадает с шаблоном `templates/github/agentmarshal-governance.yml`.

Проблемы:

**Блокирующая.** `docs/quickstart.md:6` и `docs/quickstart.md:22` так и говорят, что гайд проверен на опубликованной версии 0.3.0, и ставят `pip install agentmarshal==0.3.0`. При этом тот же файл описывает `review --dry-run`, review по finding'у и `reviewed_contract` — всё это только в 0.4.0. Этот diff сам вписал в него «in 0.4.0» (строки 196–197 и 350), а README и `docs/sidecar.md` теперь пинят `==0.4.0`. Кто пойдёт по quickstart, поставит версию, в которой описанных команд нет. Это нарушает критерий «every statement about the current release names 0.4.0».

**Некритичная.** В `docs/overview.md:147-149` обещано «Entries say whether a published design exists», но это сказано только в пункте «Further contract metadata». Пункты «Verifiable attestation», «Capture policy», «Mandatory leak-scan enforcement» и «Broader providers» этого не говорят.

**Некритичная.** В `docs/proposals/005-research-findings-have-no-record-type.md` раздел «Disposition — accepted (re-read 2026-09-01)» переписан: теперь там ссылки на ADR-0009 и CR-086, которые появились только 2026-09-06. Выходит, что датированная запись задним числом говорит о том, чего на ту дату ещё не было. Эту информацию лучше вынести в отдельную датированную заметку.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "244081cfa1c8dad80fb09fbc5c5fe761ff2d44c7", "verdict": "changes_required", "findings": ["quickstart-still-pins-and-claims-0.3.0"], "advisory_findings": ["overview-roadmap-promises-design-status-per-entry", "proposal-005-dated-disposition-rewritten-with-later-facts"]}
AGENTMARSHAL_VERDICT_END
