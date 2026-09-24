Проверил diff против контракта: версия 0.4.1 стоит в `pyproject.toml`, `src/agentmarshal/__init__.py`, `uv.lock` и smoke-тесте, `--version` печатает `__version__` (`src/agentmarshal/cli.py:84-88`); секция CHANGELOG 0.4.1 датирована днём релиза, называет CR-112, CR-113 и CR-114 и описывает только то, что реально смержено — сверил с `src/agentmarshal/journal/records.py:489-524`, `.github/workflows/release.yml:31-48` и disposition'ами proposals 018/024; UPGRADING получил заголовок «0.4.0 → 0.4.1» и фразу о том, что ничего больше делать не нужно; секция 0.4.0 и раздел 0.3.0 → 0.4.0 не тронуты.

Блокирующее:

**contributing-versioning-example-circular** — `CONTRIBUTING.md:123-126`: пример, который CR-112 добавил ровно затем, чтобы правило было конкретным, стал самоповтором: «carries the **next** release's version with a `.dev0` suffix — after 0.4.1 it reads the next release's version with that suffix». Уточнение через тире теперь дословно повторяет главное предложение и не иллюстрирует ничего — читатель по-прежнему не знает, что именно окажется на default branch после 0.4.1 (`0.4.2.dev0` или `0.5.0.dev0`). Правку нужно сделать конкретной, а не вычеркнуть смысл. Вдобавок абзац остался с рваной вёрсткой: строка «suffix — so anything built from it» короче остальных, файл в остальном залит по ~76 символов.

Не блокирующее:

**readme-quickstart-still-describe-040** — `README.md:12`, `README.md:16`, `README.md:46`, `README.md:57-60` и `docs/quickstart.md:198,207,363` продолжают называть текущий релиз 0.4.0 («Trust boundary (0.4.0)», «Version 0.4.0 ships the governed loop end to end», «in 0.4.0 a match does not…»), хотя обе страницы теперь велят ставить 0.4.1, а README — это описание пакета, которое PyPI покажет для 0.4.1. Утверждения не ложны (поведение между релизами не менялось), поэтому не блокирую, но пакет 0.4.1 описывает себя как 0.4.0.

**sidecar-sample-version-stale** — `docs/sidecar.md:125`: пример `project.json` сразу под `pip install agentmarshal==0.4.1` показывает `"version": "0.4.0"`. Соседняя фраза «yours says whichever version you installed» спасает от прямой лжи, но образец не совпадает с тем, что запишет закреплённая установка.

**quickstart-wheel-claim-needs-evidence** — `docs/quickstart.md:6`: строка теперь утверждает, что весь «The governed loop» прогнан против wheel 0.4.1. `tests/test_quickstart.py` берёт исходники из дерева, а не установленный пакет, так что CI это утверждение не подтверждает, и в журнале CR-115 пока только `opened` и `amendment`. Прогон wheel 0.4.1 должен быть в completion рядом с read-only `validate` по журналу адоптера, иначе фразу надо переписать.

**changelog-018-sentence-garbled** — `CHANGELOG.md:44-46`: «that waits for the accounting rework proposal 018 deferred» читается как обрывок; смысл (отложено в ту же переработку accounting, куда 018 отложил поле стоимости) восстанавливается только по самим proposals.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "32cb9b041d4b07e8d58fc9b326c38361f3c01504", "verdict": "changes_required", "findings": ["contributing-versioning-example-circular"], "advisory_findings": ["readme-quickstart-still-describe-040", "sidecar-sample-version-stale", "quickstart-wheel-claim-needs-evidence", "changelog-018-sentence-garbled"]}
AGENTMARSHAL_VERDICT_END
