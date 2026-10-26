Проверил снапшот целиком: оба version-носителя, lock, smoke-тест, CLI-обвязку `--version`, все упоминания `0.6.0` в документации, release-гейт и контракт-предшественник CR-205.

**Критерий 1** — «версия 0.7.0.dev0 в pyproject.toml, src/agentmarshal/\_\_init\_\_.py и uv.lock, smoke-тест её утверждает, и `agentmarshal --version` её печатает» — выполнен: `pyproject.toml:3`, `src/agentmarshal/__init__.py:3` и `uv.lock:11` (запись `[[package]] name = "agentmarshal"`, единственное вхождение версии пакета — остальные `0.6.0` в локе принадлежат `ast_serialize`) несут `0.7.0.dev0`; демонстрируют это `tests/test_smoke.py::test_version_is_declared` (прямое утверждение строки) и `tests/test_smoke.py::test_console_version_prints_package_version`, который запускает `python -m agentmarshal --version` и сравнивает stdout с `f"{agentmarshal.__version__}\n"`; `src/agentmarshal/cli.py:131-134` подключает `--version` через `action="version", version=__version__`, так что печатается именно эта строка.

**Критерий 2** — «никаких других изменений файлов; ни одно утверждение о 0.6.0 как об истории не меняется; полная CI-последовательность проходит» — выполнен: diff трогает ровно четыре файла из scope, и это тот же scope, что у аналогичной задачи CR-205 после 0.5.0 (`.agentmarshal/journal/tasks/CR-205/contract.md`). Все живые упоминания `0.6.0` остаются истинными после бампа: `README.md:12,68,109`, `docs/quickstart.md:6,30`, `docs/sidecar.md:77,131`, `docs/harness-setup.md:45,48`, `docs/overview.md:162,165`, `CHANGELOG.md`, `UPGRADING.md` — все они говорят о выпущенном релизе или о примере вывода, а не о версии ветки; `docs/sidecar.md:134` прямо оговаривает «`framework.version` records the build that wrote the file, so yours says whichever version you installed». `tests/test_quickstart.py` прогоняет только блоки из раздела «The governed loop», а `agentmarshal --version` стоит в разделе «Install», так что транскрипт не задевается. Release-гейт тоже не ломается: `pyproject.toml`, `uv.lock` и `src/agentmarshal/__init__.py` входят в `ALWAYS_ALLOWED` в `.github/scripts/check_release_audit.py`, а `.github/workflows/release.yml:44-50` как раз отказывается публиковать dev-версию. Противоречия с ADR-0001 (governance plane, not execution plane) нет — решение о версиях живёт в CONTRIBUTING.md (раздел «Versions»), и диффом оно соблюдено. Прохождение CI беру из записи координатора, своими руками не запускал.

**ADV-1 (advisory, test-gap)** — ни один тест не связывает `project.version` из `pyproject.toml` с `agentmarshal.__version__`: `tests/test_smoke.py:48` утверждает только значение в `__init__.py`, и расхождение этих двух носителей поймал бы лишь шаг «Verify tag matches project version» в `.github/workflows/release.yml:32-42`, то есть уже при пуше тега. Дефект предсуществующий, диффом не внесён, и `tests/test_smoke.py` входит в scope, так что закрыть его было бы можно одной строкой — но на выполнение критериев это не влияет.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "f8032168fbeaa21f2a55811c4718caf6039593e1",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": ["ADV-1"],
  "classes": {"ADV-1": "test-gap"},
  "verification": {
    "executed": [
      {"what": "grep -rn '0\\.6\\.0|0\\.7\\.0' across the tree (docs, README, CHANGELOG, UPGRADING, CONTRIBUTING, uv.lock, templates, .github, gitflic-ci.yaml)", "result": "only agentmarshal's own version line in uv.lock:11 is 0.7.0.dev0; every other 0.6.0 is the ast_serialize dependency or a statement about the released 0.6.0"},
      {"what": "grep -rn '__version__|0\\.6\\.0|0\\.7\\.0|pyproject' tests/*.py", "result": "only tests/test_smoke.py pins a literal version; other tests compare against agentmarshal.__version__"},
      {"what": "grep -rn 'dev0|development version' src .github docs CONTRIBUTING.md", "result": "release.yml:44-50 refuses a development version; CONTRIBUTING.md:130-137 states the .dev0 branch rule"}
    ],
    "read": [
      "pyproject.toml",
      "src/agentmarshal/__init__.py",
      "uv.lock (lines 1-20, plus every version hit)",
      "tests/test_smoke.py",
      "src/agentmarshal/cli.py:125-145",
      "CONTRIBUTING.md:100-215 (Development, Versions, Releases)",
      "CHANGELOG.md:1-30",
      "docs/quickstart.md:1-40",
      "tests/test_quickstart.py:1-60",
      "docs/sidecar.md:110-145",
      "docs/overview.md:155-175",
      "release/audit-0.6.0.toml",
      ".github/scripts/check_release_audit.py",
      ".github/workflows/release.yml (version checks)",
      ".agentmarshal/project.json",
      ".agentmarshal/journal/tasks/CR-205/contract.md",
      "docs/adr/ADR-0001-governance-plane.md"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "the coordinator records the full sequence as passing at this commit; the snapshot is not a git repository, so journal- and git-dependent tests could not be reproduced here anyway"},
      {"what": "PYTHONPATH=src python3 -I -m agentmarshal --version", "why": "command execution was declined in this sandbox; the printed value was verified by reading cli.py:131-134 and the smoke test that asserts stdout equals __version__"}
    ]
  },
  "evidence": {
    "ADV-1": "tests/test_smoke.py:48 asserts agentmarshal.__version__ == \"0.7.0.dev0\" and no test reads pyproject.toml's [project] version; grep -rn 'pyproject' tests/*.py returns only tests/test_release_audit_check.py:64, which writes a synthetic pyproject for the release-gate fixture — the only real consistency check is .github/workflows/release.yml:32-42, which runs on tag push"
  }
}
AGENTMARSHAL_VERDICT_END
