Проверил диффы против contract, против `src/agentmarshal/journal/gate.py`, `cli.py`, ADR-0008/0009/0010/0015 и против round‑5 записей CR-128. Блокирующих расхождений не нашёл: все утверждения о том, что читает gate и откуда, совпадают с кодом — contract из merge-base tree (`gate.py:793-813`), manifests оттуда же (`gate.py:819-823`), leak-scan markers из merge-base (`gate.py:1156-1158`), lifecycle из base tree (`gate.py:718-737`), records из working tree вызывающего checkout (`gate.py:937`), а в sidecar всё перечисленное — из рабочего дерева журнала (`gate.py:797, 820, 1156`), с advisory-выводом в CLI (`cli.py:794, 855-867`) и исключением findings lane (ADR-0009 D4). Четыре round‑5 advisory CR-128 закрыты все: installer-формулировка (ADR-0013:24-28), pin в lock + `[wraps].version`, объяснение `schema = 2` через ADR-0015, user-scope в D10.

Два замечания по учёту: в записях CR-128 round 5 зафиксированы четыре advisory-пункта, а не пять, как говорит acceptance — пятый я в журнале не нашёл, поэтому не считаю его пропущенным. Полную CI-последовательность выполнить не смог: sandbox не даёт запустить `uv run`. Диффы только документационные, ни один тест эти файлы не читает (`tests/test_project.py` смотрит корневой README), `.py` не менялись — значит `validate`/pytest/ruff/mypy не затронуты.

Ниже — пять non-blocking пунктов.

В `docs/adr/ADR-0013-...:183-188` поправка к решению 10 приписывает scope-таблице путь `%LOCALAPPDATA%\agentmarshal\`, которого в ней нет: таблица (строка 161) называет только `%APPDATA%\agentmarshal\extensions\`, а `%LOCALAPPDATA%` встречается лишь в карте мест ADR-0014:153 — и решение 11 того же ADR-0013, на которое поправка ссылается («как их размещает Decision 11»), в своём перечне sandbox-мест этот путь не упоминает, так что поправка вводит место локального состояния, которое правило sandbox не покрывает.

В примере манифеста `docs/adr/ADR-0013-...:318` python-зависимости адаптера названы `lock/adapter-lock.json`, хотя решение 12 того же ADR для Python называет `uv sync --locked`, чей lock — `uv.lock` (TOML); `.json` читается как npm-артефакт и смазывает весь смысл «двух локов» в примере.

В `docs/adr/ADR-0013-...:109-111` сказано, что в sidecar «the transcript says so on its scope line» про всё перечисленное, но `gate.py:870-874` печатает на scope-строке только contract («contract read from the sidecar working tree, not pinned to a commit»), и только в ветке без выходов за scope; provenance manifests, markers и lifecycle в транскрипте не упоминается.

В `docs/overview.md` поправка легла в повествовательный абзац (строки 75-81) перед `## Terminology`, тогда как acceptance называет именно глоссарий: сам список терминов не менялся, и пункт строкой выше — «The **gate** … reads git and the journal and decides» (строка 67) — остался тем самым расплывчатым утверждением, которое задача правит в двух других местах.

В `docs/adr/ADR-0012-...:203-206` исключение для репозитория расширений утверждает, что признаки и так выполнены — «the Decision-5 boundary has held a release»; граница объявлена самим ADR-0012 днём раньше (2026-10-02), её тест ещё не существует, а 0.5.0 не выпущен, так что в перфекте это утверждение сейчас неверно (станет верным к моменту переноса). Решение от него не зависит — текст сам говорит «what moves them is the rhythm, not the signs».

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "c6871d508d0b9695952dbe278ca0f69932b092a1",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "adr0013-localappdata-attributed-to-scope-table",
    "adapter-lock-named-json-for-python-deps",
    "sidecar-transcript-claim-overstates-scope-line",
    "overview-glossary-left-unamended",
    "extensions-repository-signs-claim-not-yet-true"
  ]
}
AGENTMARSHAL_VERDICT_END
