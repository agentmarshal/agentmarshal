Разобрал контракт, диff и файлы в снапшоте. Блокирующих находок нет — механизм соответствует всем пяти критериям; четыре замечания advisory.

## Критерии приёмки

**AC1 — change, delta, архив.** `openspec/changes/archive/2026-10-24-readonly-floor-holds/` содержит `proposal.md`, `design.md`, `tasks.md` и delta `specs/extension-stages/spec.md`; `openspec/changes/` кроме `archive/` пуст, то есть change действительно заархивирован. Текст MODIFIED-требования я сравнил построчно: тело delta (строки 3–116) байт в байт совпадает с опубликованным `openspec/specs/extension-stages/spec.md:923-1035`, включая заголовок `### Requirement: a pre-gate stage's candidate is bound read-only over itself` — `diff` выдал только отсутствующий в published заголовок `## MODIFIED Requirements` и завершающую пустую строку. Все 11 сценариев требования названы в docstring'ах тестов: `tests/test_isolation.py:220, 285, 326, 357, 391, 439, 464, 489, 512, 514, 1361`. Purpose капабилити (`spec.md:3`) архивом не затронут.

**AC2 — locked flags на remount.** Отображение — одна функция `_locked_mount_flags` (`src/agentmarshal/isolation.py:283-290`) над таблицей `_LOCKED_FLAG_MAP:273`. Константы я сверил с `linux/mount.h` и `bits/statvfs.h`: `MS_NOSUID 2 / NODEV 4 / NOEXEC 8 / NOATIME 0x400 / NODIRATIME 0x800 / RELATIME 0x200000` и `ST_NOSUID 2 / NODEV 4 / NOEXEC 8 / NOATIME 1024 / NODIRATIME 2048 / RELATIME 4096` — все шесть пар верны, и набор совпадает с тем, что ядро блокирует (`MNT_LOCK_NOSUID/NODEV/NOEXEC/ATIME`; `MNT_LOCK_READONLY` покрыт тем, что remount и так несёт `MS_RDONLY`). `statvfs` читается до bind'а (`isolation.py:308`), то есть берутся флаги собственного mount кандидата. Юнит-тест по каждому флагу — `test_each_locked_flag_statvfs_reports_is_mapped_to_its_mount_flag` (`:325-350`): шесть флагов по отдельности, все вместе, `0` и бит вне набора (`ST_SYNCHRONOUS`). Случай `/tmp` (`nosuid,nodev,relatime`) — `test_the_read_only_remount_keeps_the_flags_the_candidate_s_mount_locks` (`:280-322`), проверяет и то, что `statvfs` вызван ровно на каталоге кандидата.

**AC3 — повторный вход.** `os.chdir(directory)` стоит последней строкой `_bind_read_only` (`isolation.py:312`), то есть после remount и до `_drop_capabilities` (`isolation.py:450`) и exec. Порядок шагов демонстрирует `test_the_child_re_enters_the_candidate_after_the_read_only_remount` (`:352-387`) — список `steps` фиксирует `mount/mount/mount/chdir/drop`. Отказ шага: `os.chdir` поднимает `OSError`, его ловит `except OSError` вокруг `_bind_read_only` (`isolation.py:442-444`) и пишет на гарантию `read-only candidate`; демонстрирует `test_a_re_entry_that_fails_is_named_on_the_read_only_guarantee` (`:389-409`), ожидающий `{"read-only candidate": "Permission denied"}` и то, что drop всё равно прошёл. Отказ `statvfs` покрыт дополнительно (`:412-433`): этаж назван, ни один mount не сделан.

**AC4 — probe тем же путём.** `_probe_read_only` вызывает ту же `_bind_read_only` (`isolation.py:652`), так что remount с mapped-флагами и re-entry у probe и у stage — один код. Демонстрирует `test_the_probe_performs_the_same_remount_and_re_entry_the_stage_gets` (`:1358-1398`), сверяющий точную последовательность `statvfs/mount×3/chdir` с `MS_NOSUID` в remount. E2E: `test_an_isolated_stage_cannot_reach_the_network_or_write_the_candidate` (`:509-592`) пишет относительным путём (`probe-write.txt`) и абсолютным (`:560`) и требует `WRITE:blocked` + `ABSWRITE:blocked`, когда `verdicts.readonly is None`; иначе печатается нота с причиной probe. Проверил, что это действительно закрывает дыру: `cwd` у `Popen` ставится до `preexec_fn`, оба каталога (snapshot и probe-каталог) живут под `TMPDIR`, так что вердикт probe относится к тому же mount, что и кандидат.

**AC5 — ничего больше не меняется.** На платформе, где `f_flag` не даёт ни одного из шести бит, `locked == 0` и remount получает в точности прежние флаги — это зафиксировано в `test_a_pre_gate_stage_s_candidate_directory_is_bound_read_only_over_itself` (`:240-278`), где `statvfs` подменён на `f_flag=0` и ожидаемый remount — старый `MS_BIND|MS_REMOUNT|MS_RDONLY`. Для post-gate `readonly is None`, ни `statvfs`, ни `chdir` не вызываются (`test_a_network_only_stage_setup_drops_capabilities:1231`, `mounted == []`). Диff не выходит за scope контракта: тронуты только `src/agentmarshal/isolation.py`, `tests/test_isolation.py`, `openspec/changes/archive/2026-10-24-readonly-floor-holds/`, `openspec/specs/extension-stages/spec.md`. Противоречий ADR-0013 решению 8 (`docs/adr/ADR-0013-...:121-129`) нет — этаж усиливается, не ослабляется. Полную последовательность CI я прогнать не смог: в снапшоте нет ни `uv`, ни `.venv`, а запуск `python3` в этой песочнице заблокирован — по CI полагаюсь на утверждение координатора.

## Advisory

**ADV-1 (style).** В `src/agentmarshal/isolation.py` реflow прозы оставил рваные короткие строки посреди абзаца: строка 21 («before exec, the child drops») в docstring модуля и строка 329 («is named on the right») в docstring `stage_setup` обрываются задолго до принятой в файле ширины ~72 символа, хотя соседние строки заполнены. Там же мелкая непоследовательность в тестах: сценарные тесты в этом файле идут без пустой строки после docstring (`:220`, `:285`, `:512`), а новые `:326` и `:391` — с ней.

**ADV-2 (test-gap).** В `tests/test_isolation.py:560` «абсолютный» путь E2E-теста строится как `os.path.join(os.getcwd(), "probe-abs.txt")` — то есть из того самого `cwd`, который устанавливает проверяемый шаг re-entry, а не из независимо известного пути (`os.environ["AGENTMARSHAL_SNAPSHOT"]`, который `_stage_env` уже отдаёт стадии). Сейчас значения совпадают и обе проверки работают как задумано, но абсолютная нога теста не независима от относительной.

**ADV-3 (contract-mismatch).** `tests/test_isolation.py:517` пропускает E2E-тест только когда недоступны *обе* гарантии (`verdicts.network is not None and verdicts.readonly is not None`). Там, где недоступен один read-only floor, а network-namespace доступен, тест выполняется, сценарий «a stage cannot write the candidate by a relative or an absolute path» не демонстрируется и при этом не пропускается с причиной probe — AC4 просит «run only where the real probe succeeds … skipped with the probe's reason elsewhere». Форма унаследована от CR-221, и в else-ветке нота с причиной всё же проверяется, поэтому это не блокер.

**ADV-4 (claim-accuracy, unconfirmed).** Комментарий `src/agentmarshal/isolation.py:72` атрибутирует биты `f_flag` заголовку `sys/vfs.h`; константы `ST_NOSUID`…`ST_RELATIME` объявлены в `sys/statvfs.h` (через `bits/statvfs.h`), а `sys/vfs.h` относится к интерфейсу `statfs`. Проверить заголовки на этой машине не удалось — песочница не даёт читать `/usr/include`, поэтому помечаю unconfirmed.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "0c2996a177fc0a0bea81986babe153bce17e3779",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1", "ADV-2", "ADV-3", "ADV-4"],
  "classes": {
    "ADV-1": "style",
    "ADV-2": "test-gap",
    "ADV-3": "contract-mismatch",
    "ADV-4": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "diff of the delta's MODIFIED requirement body (archive/2026-10-24-readonly-floor-holds/specs/extension-stages/spec.md lines 3-116) against openspec/specs/extension-stages/spec.md lines 923-1035", "result": "identical apart from the delta's '## MODIFIED Requirements' header and one trailing blank line — the heading and full text match byte for byte"},
      {"what": "grep -n 'Scenario:' tests/test_isolation.py", "result": "all 11 scenarios of the MODIFIED requirement named in test docstrings at lines 220, 285, 326, 357, 391, 439, 464, 489, 512, 514, 1361"},
      {"what": "grep -n '^### Requirement' openspec/specs/extension-stages/spec.md", "result": "the read-only requirement is at line 923; Purpose at line 3 intact"},
      {"what": "grep -n for _setup_report / _probe_read_only / _bind_read_only / os.chdir / statvfs call sites in tests/test_isolation.py", "result": "every in-process call path either stubs os.chdir or raises before reaching it; the only unstubbed real chdir is in the forked child of test_a_failed_capability_drop_is_named_and_the_stage_still_runs (line 1273), so pytest's own cwd is never changed"},
      {"what": "grep -n -i changelog CONTRIBUTING.md AGENTS.md", "result": "no match — no CHANGELOG entry is required for this change"},
      {"what": "grep -n -i 'read-only|readonly|EPERM|nosuid' docs/known-defects.md docs/threat-model.md", "result": "no match — no stale defect note left behind outside the contract's scope"},
      {"what": "which uv python3; ls .venv/bin", "result": "only /usr/bin/python3; no uv and no virtualenv in the snapshot"}
    ],
    "read": [
      "src/agentmarshal/isolation.py (whole file)",
      "tests/test_isolation.py lines 1-240, 500-595, 1040-1398",
      "src/agentmarshal/stages.py lines 480-650, 920-990",
      "openspec/specs/extension-stages/spec.md lines 1-30, 109-135, 923-1035",
      "openspec/changes/archive/2026-10-24-readonly-floor-holds/{proposal.md,design.md,tasks.md,specs/extension-stages/spec.md}",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md lines 115-135",
      "pyproject.toml ruff settings (line-length = 88)"
    ],
    "not_run": [
      {"what": "uv sync --locked; uv run agentmarshal validate; uv run pytest; uv run ruff check; uv run ruff format --check; uv run mypy", "why": "the snapshot has no uv and no virtualenv, and running python3 is blocked in this sandbox; relying on the coordinator's statement that the sequence passed on this commit"},
      {"what": "a live check of the MS_*/ST_* constants and of the kernel's can_change_locked_flags against the system headers and kernel source", "why": "the sandbox refuses reads outside the project directory, so the constant and lock-set verification is from the C headers' published values, not from this machine"},
      {"what": "an end-to-end run of the real read-only floor (a stage writing into a bound candidate)", "why": "no test runner available and the review is read-only"}
    ]
  },
  "evidence": {
    "ADV-1": "src/agentmarshal/isolation.py:21 ('before exec, the child drops') and :329 ('is named on the right') — short line breaks mid-paragraph where neighbouring lines fill to ~72 columns; tests/test_isolation.py:326 and :391 add a blank line after a scenario docstring where :220, :285 and :512 do not",
    "ADV-2": "tests/test_isolation.py:560 — 'open(os.path.join(os.getcwd(), \"probe-abs.txt\"), \"w\")'; the absolute path is derived from the cwd that the re-entry under test installs, while src/agentmarshal/stages.py:492 already exports AGENTMARSHAL_SNAPSHOT as an independent absolute path",
    "ADV-3": "tests/test_isolation.py:517 — 'if verdicts.network is not None and verdicts.readonly is not None: pytest.skip(...)'; with verdicts.readonly set and verdicts.network None the test runs and the lines 586-587 assertions on WRITE/ABSWRITE are skipped by the 'if verdicts.readonly is None' branch at line 585 without any skip reason",
    "ADV-4": "src/agentmarshal/isolation.py:72 — '#: The ``statvfs`` ``f_flag`` bits (``sys/vfs.h``)'; ST_NOSUID..ST_RELATIME are declared in sys/statvfs.h via bits/statvfs.h, while sys/vfs.h provides the statfs interface — unconfirmed, the sandbox refused 'grep -rn ST_NOSUID /usr/include/'"
  }
}
AGENTMARSHAL_VERDICT_END
