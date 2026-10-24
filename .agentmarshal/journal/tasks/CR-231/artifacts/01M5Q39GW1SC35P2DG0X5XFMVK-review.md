Проверил снапшот целиком: манифест, все шесть сгенерированных `SKILL.md`, спеку `extension-stages`, ADR-0010/ADR-0013, контракт с его amendment и запись amendment в журнале. Сети и `npx` в этой песочнице нет (`curl` к registry.npmjs.org и `python3 -I` требуют approval, которого в non-interactive сессии не будет), поэтому всё, что требует прогона `@fission-ai/openspec@1.15.0`, я свериться не могу — это отмечено ниже как unconfirmed.

**По критериям приёмки.**

Критерий 1 выполнен в проверяемой части: `.agentmarshal/extensions/openspec.toml:20` несёт `version = "1.15.0"`, `:33` — `install = "OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.15.0 init --tools claude,codex --no-animation ."`. Та часть комментария, которую репозиторий может подтвердить сам, верна: `.gitignore:19` действительно игнорирует `.claude/` целиком, а front matter всех шести скиллов несёт `license: MIT` и `allowed-tools: Bash(openspec:*)` (`grep -c "license: MIT"` → 1 в каждом из шести). Манифест проходит ридер schema 1 (`src/agentmarshal/journal/extensions.py:386-456`): `documents = ["openspec/specs/"]` и `artifacts = ["openspec/changes/archive/"]` лежат под `footprint`, полей schema 2 нет, `version` — свободная строка, с `install` код её не сверяет. Теста, который читал бы настоящий манифест, в сюите нет: все восемь мест в `tests/test_gate.py`, `tests/test_placement.py:319`, `tests/test_brief.py:531` строят синтетические манифесты по тому же пути во временных репозиториях, так что критерий демонстрируется кодом ридера, а не тестом.

Критерий 2 выполнен в проверяемой части: `generatedBy: "1.15.0"` стоит во всех шести `.agents/skills/openspec-*/SKILL.md:10`; состав `.agents/skills/` — ровно шесть директорий плюс `.openspec-target` (содержимое `codex`), то есть footprint и диск совпадают один в один, расширять его не потребовалось. Признаков ручной правки не нашёл: общий boilerplate («In both branches, never create the root as a side effect: …») побайтово одинаков во всех шести файлах, а новые перекрёстные ссылки согласованы — «(step 4)» в `openspec-update-change/SKILL.md:62,106` указывает на реально существующий шаг 4 на строке 68, который именно этот glob-случай и описывает, и `changeRoot` в новом шаге 3 `openspec-explore/SKILL.md:160` берётся из status JSON, как и объявлено на `:171`. Вне footprint изменился только сам манифест, который входит в scope. Все изменённые пути лежат в scope; `openspec/` не тронут, Python и тесты — тоже, так что Non-Goals соблюдены и критерий 5 дифф не нарушает.

Критерий 3: половина про `--changes` тривиальна — в `openspec/changes/` нет ничего, кроме `archive/`, неархивных changes ноль. Вторая половина — прогон `validate --specs` по 23 capability; число совпадает с amendment'ом («1.15.0 non-strict passes 23/23»): `ls openspec/specs | wc -l` → 23. Сам прогон и количество новых warning'ов про длину requirement'ов остаются на отчёте.

Критерий 4 в дереве не выполнен, и это главное, на что стоит смотреть человеку. Зато fallback-ветка критерия подтверждается файлами, которые приносит этот же дифф, — ниже.

Governance чистая: amendment записан (`.agentmarshal/journal/tasks/CR-231/records/01M5Q265G32JBE335MBS8M9T3Z-amendment.json`), и его `contract` — `3fb186…d360` — совпадает с `sha256sum` текущего `contract.md` байт в байт, то есть я ревьюю именно ту версию контракта, на которую пин.

**Findings.**

`purpose-still-contradicts-its-own-requirements` (advisory) — `openspec/specs/extension-stages/spec.md:25` по-прежнему заканчивается словами «network isolation, write isolation and pause records are later work, not this capability», тогда как тот же файл содержит требования на все три: `:879` «a stage with no declared network runs in a new user and network namespace», `:925` «a pre-gate stage's candidate is bound read-only over itself» и `:1113` «an accepted pause stands down a pre-gate-stop stage's pause…». Это самопротиворечивый Purpose в пути, который манифест объявляет `documents` и который `brief` подаёт имплементеру. Change `extension-stages-purpose` в дереве нет ни под `openspec/changes/`, ни среди 91 записи архива, и ни один spec-файл руками не правлен — то есть выбрана именно fallback-ветка критерия 4. Ветка легитимна, и дифф сам это доказывает: сгенерированный 1.15.0 `openspec-sync-specs/SKILL.md:158-160` говорит «The main spec already has one and it is authoritative - leave it alone (this is what `openspec archive` does; it warns and moves on)», а `openspec-archive-change/SKILL.md:156-157` — «Preserve existing `## Purpose` sections completely untouched for established main specs… Do not regenerate or rewrite existing authored purpose». Через delta 1.15.0 существующий Purpose по-прежнему не обновляет, так что имплементер был заблокирован по-настоящему, а не поленился. Блокировать нельзя — критерий этот исход прямо разрешает; но выполненность критерия 4 целиком висит на том, что отчёт приводит вывод команды, а отчёта в выданном мне материале нет.

`install-comment-1150-commands-unconfirmed` (advisory, unconfirmed) — комментарий `.agentmarshal/extensions/openspec.toml:4-11` теперь утверждает новый внешний факт: 1.15.0 снова пишет шесть команд под `.claude/`, и `remove` чистит их именно по пути `.claude/commands/opsx`. Критерий 1 требует, чтобы этот комментарий был «checked against what 1.15.0 actually writes», но по собственной логике комментария эти ассеты в дифф не попадают, а сети и `npx` здесь нет — проверить ни утверждение, ни то, что команды 1.15.0 ложатся под `opsx/`, а не прямо в `.claude/commands/`, я не могу. Если путь другой, строка `remove` их не снимет.

`skills-and-validate-run-unconfirmed` (advisory, unconfirmed) — побайтовое равенство шести `SKILL.md` выводу `npx -y @fission-ai/openspec@1.15.0 init --tools claude,codex` (критерий 2) и прогон `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.15.0 validate --specs` с числом новых warning'ов про длину requirement'ов (критерий 3) из репозитория не выводятся. Косвенно против ручной правки говорят одинаковый boilerplate и согласованные перекрёстные ссылки, названные выше, и то, что седьмого скилла 1.15.0 не принесла, — но это чтение прозы, а не прогон, которого требуют критерии.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "a289b9d7eea53fcfb21e694df606dc0a7e32b372",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "purpose-still-contradicts-its-own-requirements",
    "install-comment-1150-commands-unconfirmed",
    "skills-and-validate-run-unconfirmed"
  ],
  "classes": {
    "purpose-still-contradicts-its-own-requirements": "claim-accuracy",
    "install-comment-1150-commands-unconfirmed": "claim-accuracy",
    "skills-and-validate-run-unconfirmed": "claim-accuracy"
  },
  "verification": {
    "executed": [
      {"what": "find .agents/skills -type f -o -type l | sort", "result": "six openspec-*/SKILL.md plus .agents/skills/.openspec-target — matches the manifest footprint exactly"},
      {"what": "grep -n generatedBy over the six SKILL.md", "result": "all six carry generatedBy: \"1.15.0\" at line 10"},
      {"what": "grep -c 'license: MIT' over the six SKILL.md", "result": "1 in each of six; allowed-tools: Bash(openspec:*) present"},
      {"what": "ls openspec/specs | wc -l", "result": "23 — matches the amendment's 23/23"},
      {"what": "ls openspec/changes/ and ls openspec/changes/archive | wc -l", "result": "only archive/ (91 entries); no non-archived change, no extension-stages-purpose anywhere"},
      {"what": "grep -n -i 'network|write isolation|pause' openspec/specs/extension-stages/spec.md", "result": "Purpose at :25 calls all three later work while requirements exist at :879, :925, :1113"},
      {"what": "grep -n 'never create the root as a side effect' over the six SKILL.md", "result": "byte-identical boilerplate in all six (lines 26-40) — no sign of hand editing"},
      {"what": "sha256sum .agentmarshal/journal/tasks/CR-231/contract.md", "result": "3fb186fdf55b7895f7e48147f0d5e47bde8f66d2ef2d83486db6462cc1d2d360 — equals the amendment record's pinned contract hash"},
      {"what": "grep -rn 'extensions/openspec.toml' tests/", "result": "eight hits, all synthetic manifests in temp repos; no test reads the repository's own manifest"},
      {"what": "grep -rn '1.13.2|1.15.0|1.12.0' across py/md/toml/yaml", "result": "no stale live reference to 1.13.2 outside the ADR-0013 [wraps] example and append-only journal/archive text"}
    ],
    "read": [
      ".agentmarshal/extensions/openspec.toml",
      ".agents/skills/openspec-apply-change/SKILL.md",
      ".agents/skills/openspec-archive-change/SKILL.md",
      ".agents/skills/openspec-explore/SKILL.md",
      ".agents/skills/openspec-propose/SKILL.md",
      ".agents/skills/openspec-sync-specs/SKILL.md",
      ".agents/skills/openspec-update-change/SKILL.md",
      ".agents/skills/.openspec-target",
      "openspec/specs/extension-stages/spec.md",
      "openspec/config.yaml",
      ".gitignore",
      "docs/adr/ADR-0010-process-extensions.md",
      "docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md",
      "src/agentmarshal/journal/extensions.py",
      "src/agentmarshal/journal/contracts.py",
      ".agentmarshal/journal/tasks/CR-231/contract.md",
      ".agentmarshal/journal/tasks/CR-231/records/01M5Q265G32JBE335MBS8M9T3Z-amendment.json",
      "AGENTS.md",
      "CHANGELOG.md"
    ],
    "not_run": [
      {"what": "OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.15.0 init --tools claude,codex --no-animation . (to diff the generated skills)", "why": "no network in this sandbox; curl to registry.npmjs.org requires approval that a non-interactive session cannot grant"},
      {"what": "OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@1.15.0 validate --specs / --changes", "why": "same — the openspec CLI cannot be fetched or run here"},
      {"what": "the 1.15.0 archive command on a Purpose-only delta", "why": "same; corroborated instead from the generated sync/archive skills shipped in this diff"},
      {"what": "uv sync --locked; agentmarshal validate; pytest; ruff; mypy", "why": "read-only review; the coordinator states the sequence passed on this commit, and the diff touches no Python or test file"}
    ]
  },
  "evidence": {
    "purpose-still-contradicts-its-own-requirements": "openspec/specs/extension-stages/spec.md:25 ('network isolation, write isolation and pause records are later work, not this capability') against :879, :925, :1113 in the same file; no openspec/changes/extension-stages-purpose/ and no such entry among the 91 archive directories; fallback corroborated by .agents/skills/openspec-sync-specs/SKILL.md:158-160 and .agents/skills/openspec-archive-change/SKILL.md:156-157",
    "install-comment-1150-commands-unconfirmed": ".agentmarshal/extensions/openspec.toml:4-11 (comment) and :34 (remove names .claude/commands/opsx); `curl -sS -m 15 https://registry.npmjs.org/@fission-ai/openspec/1.15.0` → refused, 'This command requires approval' — the claim cannot be checked here",
    "skills-and-validate-run-unconfirmed": "criterion 2 and 3 in .agentmarshal/journal/tasks/CR-231/contract.md:14-15; no npx/network (see not_run). Negative evidence for hand editing only: identical boilerplate across the six SKILL.md and consistent cross-references (openspec-update-change/SKILL.md:62,106 → step 4 at :68; openspec-explore/SKILL.md:160 → changeRoot at :171)"
  }
}
AGENTMARSHAL_VERDICT_END
