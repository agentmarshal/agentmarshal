Я проверил изменение против контракта и кода.

**Что проверено как верное:**
- Тринадцать классов, сгруппированы в порядке контракта (statements about the tool, consistency, privacy, code, scope, form), у каждого есть «Shows up as» и «Avoid» — `docs/known-defects.md:11-82`.
- «the journal has nine record types» — подтверждается `src/agentmarshal/journal/attestation.py:24-33` (`PREDICATE_TYPES`, девять) и `src/agentmarshal/journal/status.py:21-31` (`WritableRecordType`, девять).
- «the gate records nothing» — в `src/agentmarshal/journal/gate.py` нет ни одной записи в журнал (никаких write/mkdir/open).
- Outcome для provider limit действительно задокументирован раньше — `provider-limit` в `CHANGELOG.md:41` (0.4.1) и `docs/quickstart.md:449-452`, при текущей версии 0.5.0.dev0.
- Маскирование путей leak-скана описано точно: заменяется только проблемный фрагмент пути, остальное сохраняется (`src/agentmarshal/journal/capture.py:312-331`).
- Класс 10 соответствует коду: ревьюер получает `name_all_losses=True` (`src/agentmarshal/journal/review.py:1188`), в отличие от узкого правила скана (`capture.py:530`).
- Примеры общие: ни одного task id, finding id, номера proposal, псевдонима адоптера, коммита или приватного пути; имён публикуемых документов со ссылками в файле нет, так что нечего ломать.
- Строка в карте документации есть и говорит кто и когда читает — `docs/README.md:82`.
- Диффом затронуты только два файла из scope; CI-последовательность (validate/pytest/ruff/mypy) документарным изменением не затрагивается — тестов, проверяющих `docs/README.md` или `docs/known-defects.md`, в `tests/` нет (только `docs/quickstart.md` в `tests/test_quickstart.py:18`).

**Advisory 1 — `docs-known-defects-masking-claim-reads-as-fact`:** в классе 8 (`docs/known-defects.md:53-54`) фраза «every path the tool prints goes through the same masking the leak scan uses» написана в изъявительном наклонении, в отличие от всех остальных «Avoid», которые императивны. Прочитанная как утверждение о текущем поведении, она неверна: имена в промпте ревьюера сознательно остаются немаскированными (`src/agentmarshal/journal/review.py:1197-1199`). Императив («mask every path you print the way the leak scan does») убрал бы конфликт с критерием про правдивость утверждений о поведении.

**Advisory 2 — `docs-known-defects-splitlines-rule-overgeneralised`:** в классе 9 (`docs/known-defects.md:63`) правило сформулировано как «split git output on `"\n"` only», тогда как в коде оно обосновано только для patch-вывода git — «the one separator git uses in patch output» (`src/agentmarshal/journal/capture.py:608-612`). Остальной вывод git намеренно разбирается через `splitlines()` (`gate.py:378`, `gate.py:653`, `prune.py:78`), так что правило в текущей редакции помечает дефектным существующий корректный код; «git patch output» было бы точнее.

Ни одно из двух не искажает класс дефекта и не затрагивает критерии приёмки по существу, поэтому блокировать нечего.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "3a8f9effbc625d06b4013042222d63cc3cea772a", "verdict": "approved", "findings": [], "advisory_findings": ["docs-known-defects-masking-claim-reads-as-fact", "docs-known-defects-splitlines-rule-overgeneralised"]}
AGENTMARSHAL_VERDICT_END
