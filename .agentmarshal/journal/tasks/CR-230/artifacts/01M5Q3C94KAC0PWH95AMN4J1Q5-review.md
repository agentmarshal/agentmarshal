Проверил оба дайджеста против кода, ADR-0020/ADR-0009, индекса и контракта. Ниже — прозой по находкам и по каждому критерию приёмки.

**BLK-044-write-side-release-unnamed** (blocking, contract-mismatch). Критерий приёмки 1 требует, чтобы диспозиция 044 называла write-side «with the next record schema **in 0.7.0**». В дайджесте релиз не назван нигде: `docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:3` (шапка), `:73` (заголовок Disposition), `:91` (абзац write side), `:107-109` (секция Where) и строка индекса `docs/proposals/README.md:92` везде говорят только «with the next record schema». Вывести `0.7.0` читателю неоткуда: строка `0.7.0` не встречается в репозитории нигде, кроме самого контракта (`grep -rn "0\.7\.0"` даёт только `.agentmarshal/journal/tasks/CR-230/contract.md:11`), ADR-0022 следующий schema-переход к релизу не привязывает, а `pyproject.toml:3` стоит на `0.6.0.dev0`. При этом README сам объявляет, что колонка Where говорит «what an accepted proposal became — a release, a decision record, or the piece of work that carries it» (`README.md:63-65`), и соседние дайджесты релизы называют свободно — 045 называет ещё не вышедший 0.6.0. То есть это не стилистическое воздержание от обещаний, а недоданная часть критерия; как departure в отчёте она тоже не заявлена.

**ADV-readme-wrappers-overstated** (advisory, claim-accuracy). Вводный абзац нового батча — `docs/proposals/README.md:86-88` — говорит «the reporter's wrappers each invented a marker — a documented zero, a file copied by hand». Про wrapper говорит только 044 (`044-...md:31,33`: executor wrapper пишет per-run usage line и документирует нулевой total); в 045 слова «wrapper» нет вообще, доставка шла ручным копированием файла (`045-...md:38-39`, `:63`). Множественное «wrappers, each» приписывает второй находке механизм, которого в её дайджесте нет.

По критериям приёмки:

- **AC1 (044: Source, версии, форма дайджеста)** — выполнен частично. Хеш совпадает с контрактом побайтно (`grep -o "sha256:[0-9a-f]\{64\}"` даёт `816c7ff8…b0d` в файле и в контракте), «Observed on: 0.4.1, rechecked on 0.5.0» на месте, форма ровно как у существующих (reporter line → `## Finding` → `## Proposed` → `## Disposition` → `## Where`, как в 024/042/043), а строка Reporter дословно повторяет конвенцию Adopter A из 010/025/026. Reading-side диспозиция («status и report показывают такую сессию как unmeasured, в 0.6.0») на месте; не хватает только `0.7.0` — см. BLK выше. Фактические утверждения дайджеста проверил по коду и все подтвердились: дефолты `0` у трёх флагов (`cli.py:407-409`), `create_session_record` всегда пишет трёхцелочисленный `tokens` (`journal/records.py:2322-2326`), правило `session-tokens` требует ровно три неотрицательных int и отвергает запись без объекта (`records.py:778-793`), `usage` опционален и несёт `provider`/`method` (`records.py:796-823`, `records.py:2329-2330`), `--usage-method` принимает только `reported`/`measured` в паре с `--usage-provider` (`cli.py:410-411`, `cli.py:1308-1313`), `report` суммирует `tokens` каждой session-записи (`journal/report.py:364-365`), читает отсутствие `usage` как `usage=unrecorded` (`report.py:174-179`, `:691,716`) и считает `sessions_without_cost` отдельно (`report.py:663`), а quickstart действительно велит опускать usage-флаги при недоступном provenance (`docs/quickstart.md:547-550`). Теста, демонстрирующего этот критерий, в наборе нет и быть не может: содержимое дайджестов ничем не покрыто — единственный тест про proposals, `tests/test_project.py:28-45`, проверяет указатели в README аутбокса, а не docs/proposals.
- **AC2 (045: Source, 0.5.0, диспозиция)** — выполнен. Хеш `a819341c…008` совпадает с контрактом; диспозиция ровно та, что требуется («check и send пропускают уже отправленные — по манифесту, который пишет send, или по индексу, который берёт status, в 0.6.0»). Механика проверена по коду: `_check` обходит все записи, считает draft'ом любой regular file кроме `README.md` и требует пять полей точными `## <Field>`-заголовками (`src/agentmarshal/outbox.py:410-456`, `:338-350`, `_FIELDS` на `:57`), не-regular запись печатается как `not a draft, not checked` и валит батч (`:449-452`), `_run_send` исполняет тот же check буквально и стейджит весь каталог через `git add --force -- .agentmarshal/upstream` (`:659-663`, `:708-710`), `outbox status` хеширует файлы sha256 и сверяет с `Source:`-строками индекса из `--index` (`:764`, `:767-820`, `:108-113`), флагов, меняющих набор проверяемых файлов, у `check`/`send` нет (`register`, `:96-101`), README в аутбоксе пишет `init` (`project.py:298-310`, тест `tests/test_project.py:28-45`). Утверждение «0.5.0 shipped the outbox group» подтверждается `CHANGELOG.md:150-158` (секция 0.5.0) и `UPGRADING.md:75`. Противоречия с названными решениями нет: ADR-0020 decision 3 действительно ставит правило «leak scan over what would be sent», и дайджест его сохраняет; ADR-0009 про session/token и аутбокс-форму ничего не решает. Тестом этот критерий тоже не демонстрируется — покрытия docs-контента в наборе нет.
- **AC3 (оба в индексе, существующий формат строки)** — выполнен: заголовок таблицы и разделитель в новой секции (`README.md:90-91`) идентичны таблице батча 2026-10-03 (`README.md:113-114`), секция вставлена в обратно-хронологическом порядке перед 2026-10-03, обе строки несут все пять колонок. Фоновые утверждения вводного абзаца тоже сверил: Adopter A — один из трёх репортёров первого батча (`README.md:221-222`) и репортёр батча 2026-09-24 (`README.md:156-158`). Теста нет (та же причина).
- **AC4 (никаких идентификаторов, English only, ссылки резолвятся)** — выполнен. Поиск `CR-\d+`, ULID-подобных последовательностей, `.sh/.py/.yaml`-имён дал только собственные файлы AgentMarshal (`cli.py`, `journal/records.py`, `src/agentmarshal/outbox.py`); имён людей, продукта, провайдерского аккаунта и путей чужого журнала нет, измерения даны счётчиками («ten finding files», «nine consecutive tasks»), профиль репортёра совпадает с публичной таблицей `README.md:252`. Из не-ASCII только типографика (em dash, middle dot), кириллицы нет. Все три добавленные ссылки резолвятся: `025-validate-refused-records-an-earlier-release-wrote.md`, `026-reviewer-facts-round-convergence-and-two-gaps.md`, `../adr/ADR-0020-the-outbox-command-group.md` — файлы существуют; в 044 ссылок не добавлено. Единственное расхождение прозы — ADV выше, и оно в README, не в дайджестах.
- **AC5 (других изменений нет; suite и CI проходят)** — по диффу выполнен: тронуты ровно три пути из scope и ничего больше. Сам CI я не запускал (read-only ревью, изменение docs-only); беру как факт координатора, что полная последовательность прошла на этом коммите.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b9ff7ff5bcbea8b0ac8da430988333c8a6c76d83",
  "verdict": "changes_required",
  "findings": ["BLK-044-write-side-release-unnamed"],
  "advisory_findings": ["ADV-readme-wrappers-overstated"],
  "classes": {
    "BLK-044-write-side-release-unnamed": "contract-mismatch",
    "ADV-readme-wrappers-overstated": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "grep -rn \"0\\.7\\.0\" over the repository (md/toml/py, journal excluded)", "result": "only .agentmarshal/journal/tasks/CR-230/contract.md:11; no occurrence in docs/proposals/044-*.md, docs/proposals/README.md or any ADR"},
      {"what": "grep -o \"sha256:[0-9a-f]{64}\" over both new digests and the contract", "result": "816c7ff8e0ad09bd1bc55f0030897758eba0a539c0da556744de745a76e57b0d and a819341cbe9022523a08b200c6ee92e687335c6b83fd4b12a88b22b35a411008 match the contract exactly"},
      {"what": "grep -n \"input-tokens|output-tokens|cache-tokens|usage-method|usage-provider\" src/", "result": "cli.py:407-409 default=0 for all three; cli.py:410-411 --usage-provider and --usage-method choices=(reported, measured); cli.py:1308-1313 the pairing refusal"},
      {"what": "read src/agentmarshal/journal/records.py:778-823 and 2272-2346", "result": "session-tokens requires a dict of exactly input/output/cache, each type int and >= 0; create_session_record always writes the tokens object; usage written only when usage_provider is supplied"},
      {"what": "grep -n \"unrecorded|sessions_without_cost|tokens\" src/agentmarshal/journal/report.py", "result": "report.py:174-179 absent usage reads as 'unrecorded', rendered as usage= at :691 and :716; tokens summed over every session record at :364-365; sessions_without_cost printed at :663"},
      {"what": "read src/agentmarshal/outbox.py:30-113, 315-350, 396-520, 655-720, 767-835", "result": "_check treats every regular file but README.md as a draft needing the five '## <Field>' headings, prints 'not a draft, not checked' and refuses for non-regular entries, scans every entry for leaks; _run_send runs _check then 'add --force -- .agentmarshal/upstream'; status hashes files and matches Source: lines from --index; check and send register no arguments"},
      {"what": "grep -n \"outbox\" CHANGELOG.md UPGRADING.md", "result": "CHANGELOG.md:150-158 inside the 0.5.0 section ships the group; UPGRADING.md:75 lists 'the agentmarshal outbox group (new, check, send, status)' as what the new version adds"},
      {"what": "grep -oE '\\]\\([^)]+\\)' over both new digests, then ls docs/proposals and docs/adr", "result": "three link targets only (025-..., 026-..., ../adr/ADR-0020-the-outbox-command-group.md); all three files exist"},
      {"what": "grep -nE 'CR-[0-9]+|[0-9A-HJKMNP-TV-Z]{26}|\\.sh\\b|\\.py\\b|\\.yaml\\b' over both new digests", "result": "only AgentMarshal's own files: cli.py, journal/records.py, src/agentmarshal/outbox.py"},
      {"what": "LC_ALL=C grep -n '[^ -~]' over both new digests", "result": "non-ASCII limited to em dash and middle dot; no Cyrillic, English only"},
      {"what": "grep -n \"wrapper\" over both digests and the index", "result": "044-...md:31,33 (one executor wrapper); no match in 045-...md; README.md:87 says 'wrappers each'"},
      {"what": "grep -rn \"proposals\" tests/", "result": "only tests/test_project.py:31-44 (the outbox README's pointers); no test covers digest content or the proposals index"},
      {"what": "sed -n '90,93p' and '113,114p' docs/proposals/README.md", "result": "new table header and separator identical to the 2026-10-03 batch table; both new rows carry all five columns"}
    ],
    "read": [
      "docs/proposals/044-unmeasured-usage-is-written-as-zeros.md",
      "docs/proposals/045-outbox-check-refuses-an-outbox-that-predates-it.md",
      "docs/proposals/README.md",
      ".agentmarshal/journal/tasks/CR-230/contract.md",
      "docs/adr/ADR-0020-the-outbox-command-group.md",
      "docs/adr/ADR-0009-research-findings-lifecycle.md",
      "docs/adr/ADR-0022-the-0-5-0-record-model-one-transition.md",
      "docs/quickstart.md",
      "src/agentmarshal/cli.py",
      "src/agentmarshal/journal/records.py",
      "src/agentmarshal/journal/report.py",
      "src/agentmarshal/outbox.py",
      "src/agentmarshal/project.py",
      "tests/test_project.py",
      "CHANGELOG.md",
      "UPGRADING.md",
      "pyproject.toml",
      "docs/proposals/025-validate-refused-records-an-earlier-release-wrote.md",
      "docs/proposals/026-reviewer-facts-round-convergence-and-two-gaps.md",
      "docs/proposals/010-executor-artifacts-lifecycle.md",
      "docs/proposals/024-provider-quota-stop-cannot-be-recorded.md",
      "docs/proposals/042-liveness-of-an-unattended-loop-is-watched-by-hand.md",
      "docs/proposals/043-review-before-integration-makes-every-merge-stale.md"
    ],
    "not_run": [
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy", "why": "read-only review of a docs-only diff; the coordinator states the full sequence passed on this commit"},
      {"what": "git diff / git status to confirm no files outside the diff changed", "why": "the snapshot is not a git repository; judged from the supplied diff, which touches only the three scope paths"},
      {"what": "comparison of each digest against the reporter's original files", "why": "the originals are staged privately and are not in the repository"}
    ]
  },
  "evidence": {
    "BLK-044-write-side-release-unnamed": "Contract acceptance 1 requires the write side 'with the next record schema in 0.7.0'; docs/proposals/044-unmeasured-usage-is-written-as-zeros.md:3, :73, :91, :107-109 and docs/proposals/README.md:92 all say only 'with the next record schema'. `grep -rn \"0\\.7\\.0\" .` (journal excluded) returns no hit in the repository, so the release cannot be derived: ADR-0022 names no successor schema release and pyproject.toml:3 is version = \"0.6.0.dev0\", while docs/proposals/README.md:63-65 defines the Where column as naming the release a proposal became and 045-...md:76,111 names the unreleased 0.6.0.",
    "ADV-readme-wrappers-overstated": "docs/proposals/README.md:86-88 'the reporter's wrappers each invented a marker — a documented zero, a file copied by hand'; `grep -n wrapper docs/proposals/044-*.md docs/proposals/045-*.md docs/proposals/README.md` → 044-...md:31 'an executor wrapper writes a per-run usage line', 044-...md:33 'a convention the wrapper documents', README.md:87; no match in 045-...md, where delivery is a hand copy (045-...md:38-39 'The pending finding was delivered by copying the file', :63 'continuing to deliver by copy')."
  }
}
AGENTMARSHAL_VERDICT_END
