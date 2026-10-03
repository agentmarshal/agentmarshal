Я прочитал `steps.py`, `process_log.py`, хук в `cli.py`, оба тестовых файла, delta-спеку, архив изменения и итоговый `openspec/specs/process-log/spec.md`, а также сверил поля событий с ADR-0022 §7 и §4.

**Что сошлось**

- Все 13 сценариев из ADDED-требований и 2 новых сценария MODIFIED-требования имеют тест, чей docstring называет сценарий дословно; MODIFIED-заголовок совпадает с существующим посимвольно, порядок сценариев в итоговой спеке точно повторяет delta — ни один не потерян.
- `step start` пишет ровно `step`/`activity`/`pid`/`pid_started_at`/`deadline` (+`actor`/`run_dir` по запросу) — это и есть набор ADR-0022 §7; `outcome` как «непустое слово» не расходится с §4, где сказано, что `outcome` принимает любую непустую строку.
- Путь отказов закрыт плотно: `local_state` оборачивает `GitNotAvailableError` в `LocalStateError`, `resolve_placement` ловит `OSError`/`ValueError` при чтении `project.json`, и `_writer_for` ловит весь этот набор плюс `OSError`, так что ни одна ветка не уходит в traceback. Сайдкар пишет `sidecar/.git/agentmarshal/log/`, хост не создаётся — тест это проверяет напрямую.
- `write_event`: `allow_nan=False` до открытия файла (строка не ложится), `OSError` на append → `ProcessLogError` с путём и ремедией. `cli.py` — только две строки хука.

**Замечания (все не блокирующие)**

Разбор `ps -o etime=` не является тотальным, хотя модуль обещает `unknown` вместо traceback: в `src/agentmarshal/steps.py:369` `_elapsed_seconds` пропускает всё, что проходит `str.isdigit()` (включая надстрочные цифры, которые `int()` отвергает), а `src/agentmarshal/steps.py:366` вычитает полученный интервал без защиты от `OverflowError` — в отличие от `_parse_deadline`, который именно это и ловит; с реальным `ps` недостижимо, так что это hardening, а не дефект поведения.

Проверка `--outcome` существует во второй форме: `_is_word` в `src/agentmarshal/steps.py:238` дублирует обе проверки `_refuse_unclean_text`, а `src/agentmarshal/steps.py:202` печатает собственное сообщение вместо общего пути `StepError`, так что один предикат живёт в двух видах.

Единственный отказ, который приходит оператору из `write_event`, печатается без префикса команды: `src/agentmarshal/steps.py:187` и `src/agentmarshal/steps.py:217` выводят текст `ProcessLogError` как есть, тогда как все остальные сообщения модуля начинаются с `step start: ` / `step end: `.

В каталоге изменения `openspec/changes/archive/2026-10-03-step-commands/` нет `.openspec.yaml`, который `.agents/skills/openspec-explore/SKILL.md` называет обязательными метаданными, создаваемыми `openspec new change` («never create a new change directory by hand»); у 21 из 26 архивных изменений он есть, у этого — нет.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ffca6170d04e71a8a6e9fafe3e6ef992f45f9f1c", "verdict": "approved", "findings": [], "advisory_findings": ["ps-etime-parse-is-not-total", "outcome-refusal-bypasses-the-step-error-path", "append-failure-message-lacks-the-command-prefix", "archived-change-lacks-openspec-metadata"]}
AGENTMARSHAL_VERDICT_END
