Проверил contract и diff: прочитал все четыре новых дайджеста, правки 024/026/032-035, индекс и карту документации, а также сверил утверждения о коде с исходниками.

**Что подтвердилось фактами в репозитории:**

- 032: gate действительно уже вычисляет journal-only lane — `journal_only = all(path.startswith(_JOURNAL_PREFIX) ...)` (`src/agentmarshal/journal/gate.py:650`), строка транскрипта совпадает дословно (`gate.py:740`), и lane реально пропускает scope- и review-проверки. Формулировка «accepted part is exposing it to the required check» корректна.
- 037: strict decode подтверждён — `review.py:198` `_run_git` c `encoding="utf-8"` без `errors`, а gate-хелпер (`gate.py:251-257`) ловит `UnicodeDecodeError` и деградирует до `WARN: leak-scan skipped (...)`. Все функции из traceback существуют (`cli.py:1349 → _run_review`, `review.py:1040 launch_review`, `_run_git`).
- 039: `status` действительно печатает `verdict= findings=N advisory=N` (`cli.py:548-552`); `finding` — «hash-pinned research finding» (`cli.py:299`); `brief` строится из contract + amendment history + decisions/documents, review findings во входах нет (`brief.py`). Цитата про ADR-0010 точна: «code running at a gate boundary becomes something the gate trusts» — Alternatives considered.
- Ни один дайджест не называет непубликованный документ, релиз, proposal- или ADR-номер; все ссылки (018, 019, 026, 027, 029, 031, 035, 036, 038, ADR-0010, 0.4.1) опубликованы.
- 035 в индексе перечисляет все три accepted-части, 033 header согласован с телом, 034 Where называет «the decision on the contract's roles» без имени документа.

**Блокирующая находка:**

Вводный абзац раздела «Batch of 2026-09-18» в `docs/proposals/README.md:134` всё ещё заканчивается фразой «Accepted in part.», хотя 024 — единственный proposal этого батча — после override полностью accepted: его header, заголовок `## Disposition — accepted`, Where и строка таблицы прямо под этим абзацем (`README.md:138`) больше не содержат ни deferred, ни declined части. До этого изменения фраза была верна, после — противоречит строке таблицы в двух строках ниже; это и есть та самая дисциплина «одно и то же в header, Disposition, Where и строке индекса», которую требует acceptance-критерий 3.

Отдельно: полную последовательность CI (`uv run agentmarshal validate`, `pytest`, `ruff`, `mypy`) выполнить не удалось — sandbox отклонил запуск. Изменение чисто markdown-овое и не касается ни одного assert'а в `tests/` (единственный тест, упоминающий `docs/proposals/`, — `tests/test_project.py:26`, он проверяет текст outbox README), так что регрессии в CI я не ожидаю, но это не проверено исполнением.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "9e42d80d3739dee4df570912d88627b5907aa964", "verdict": "changes_required", "findings": ["stale-batch-intro-2026-09-18-accepted-in-part"]}
AGENTMARSHAL_VERDICT_END
