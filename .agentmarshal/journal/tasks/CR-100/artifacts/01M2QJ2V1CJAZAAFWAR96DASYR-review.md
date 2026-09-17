Разобрал диф против контракта, прочитал реализацию, тесты, спеки и design.md. Тесты запустить не удалось — песочница отклонила выполнение `pytest`, поэтому выводы ниже статические (проверял вручную все затронутые assertion'ы, включая `tests/test_leak_scan.py`, `tests/test_gate.py`, `tests/test_placement.py` — они с новым рендерингом сходятся).

Что сделано хорошо: один рендерер `render_leak_hits` на оба вызова, `safe_path` закрывает путь-как-секрет в обе стороны (маркер и сигнатура), константа `PROJECT_CONFIG_RELPATH` действительно одна на три места, `config_path=""` в sidecar — безопасное направление, `diagnostics_note` протянут по всем путям отказа и не теряет вердикт при неудачной записи. Циклического импорта `capture → project` нет, порядок импортов совместим с `order-by-type`.

Ниже — то, что блокирует.

**declaration-suppressed-beside-real-occurrence** — в `src/agentmarshal/journal/capture.py:463` вхождение маркера в `.agentmarshal/project.json` выбрасывается безусловно (`elsewhere` исключает `config_path`, а затем отчёт строится только по `elsewhere`), а не только когда оно единственное; контракт в «Threat model and boundaries» ограничивает сужение словами «and only when it is the sole occurrence», и design.md тоже пишет «An occurrence anywhere else is reported, including in the same content» — отступление зафиксировано лишь комментарием в коде, а не в design.md, чего требует первый критерий приёмки.

**leak-scan-purpose-placeholder** — `openspec/specs/leak-scan/spec.md:4` уезжает в релиз с заглушкой архиватора «TBD - created by archiving change adopter-small-defects. Update Purpose after archive.»; причина в том, что дельта `openspec/changes/archive/2026-09-17-adopter-small-defects/specs/leak-scan/spec.md` не содержит секции `## Purpose`, хотя все шесть остальных capability-спеков в `openspec/specs/` имеют написанный Purpose, а `.agents/skills/openspec-sync-specs/SKILL.md:162` прямо требует не оставлять такой placeholder висеть.

**scenario-docstring-does-not-name-it** — `tests/test_capture.py:376` даёт docstring «Scenario: a path that matches a built-in signature is described, not printed», тогда как сценарий в спеке называется «a path that is itself a key is described, not printed»; остальные девять сценариев процитированы дословно, так что здесь механическая связь «сценарий → тест», которую требует первый критерий приёмки, рвётся.

Небилокирующее.

**launched-review-type-not-exported** — `src/agentmarshal/journal/__init__.py:49` по-прежнему экспортирует `SubmittedReview`, но экспортируемый `launch_review` теперь возвращает `LaunchedReview`, которого в `__all__` нет, и потребитель пакетной поверхности не может назвать тип, который получает.

**sidecar-doc-stale-on-warn-line** — `docs/sidecar.md:247` описывает строку гейта как идущую «with the markers it matched», хотя теперь она несёт `file: what matched`; файл вне scope этой задачи, поэтому только к сведению.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "06a9a5674ca875594daa3cc9892e45f3cb36f202", "verdict": "changes_required", "findings": ["declaration-suppressed-beside-real-occurrence", "leak-scan-purpose-placeholder", "scenario-docstring-does-not-name-it"], "advisory_findings": ["launched-review-type-not-exported", "sidecar-doc-stale-on-warn-line"]}
AGENTMARSHAL_VERDICT_END
