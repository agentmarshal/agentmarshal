Проверил contract, diff и каждое утверждение диффа по самому коду. Ниже — прозой по каждому критерию и по каждому finding.

## По критериям приёмки

**1. Формат `release/audit-0.6.0.toml`.** Выполнен. Файл даёт `version = "0.6.0"`, `audited_commit = "dff244b2df8e8003dad6faa4f7aa2ddd2d25422a"` (ровно 40 hex, совпадает с freeze-commit из Context контракта), `model = "gpt-6-astra"` (единственное значение в `ALLOWED_MODELS`, `.github/scripts/check_release_audit.py:36`), `audited_at = 2026-10-26T06:23:00+10:00` — offset date-time, то есть aware, что и требует `_is_timestamp`. 22 `[[finding]]`: все id уникальны, у каждого `fixed` есть `task = "CR-<n>"`, у единственного `deferred` (`AUD-gate-journal-5-residue`) — непустой `reason`, совпадающий по смыслу с residue-оговоркой в `CR-237/contract.md:15`. Привязки сошлись с контрактами fix-задач построчно: `AUD-gate-journal-1→CR-235`, `-2/-3/-6→CR-236`, `-4/-5→CR-237`, `AUD-extensions-1→CR-238`, `-2/-3→CR-239`, `AUD-commands-1/-2→CR-241`, `-3→CR-242`, `docs-claims-1-*→CR-243`, `2-1/2-2→CR-244`, `AUD-whole-project-1→CR-240`. Advisory-находки аудита (`AUD-commands-6`, `AUD-extensions-4/-5`, `docs-claims-2-3..`) в файл справедливо не попали — их контексты прямо называют их advisory. Комментарий говорит всё требуемое: gate-journal на 15af26e до freeze по решению оператора, остальные на freeze, docs-claims в двух частях, и что `AUD-whole-project-1` из сравнительного прохода Claude Fable. Все 11 задач, перечисленных как `fixed`, имеют последней lifecycle-записью `completed` (проверил `records/` каждой) — то, что требует скрипт. Тест, демонстрирующий формат как таковой: `tests/test_release_audit_check.py` (`test_passes_with_fixed_finding_covering_change`, `test_string_audited_at_passes`) — но он работает на синтетических репозиториях, не на поставляемом файле; см. ADV-audit-file-untested.

**2. Прогон `check_release_audit.py v0.6.0`.** Проверить не смог: review-снапшот не git-репозиторий, и отчёт имплементера мне не передан. Что проверяемо — проверил: все пути, изменённые этим кандидатом, покрыты либо `ALWAYS_ALLOWED` (`release/`, `CHANGELOG.md`), либо scope задач из списка `fixed` — `README.md` через scope CR-234, `docs/proposals/012-*` через `docs/proposals/` CR-243, `docs/harness-setup.md` и `docs/templates/claude-code-settings.local.json` через `docs/` CR-244. Остаётся непроверенным один риск: `_covered` в скрипте, в отличие от merge-gate, не добавляет footprint объявленных extensions, а footprint openspec покрывает всё `openspec/` — если какая-то fix-задача задела путь под `openspec/` вне своего объявленного scope, скрипт на теге это отвергнет, а CI на master — нет.

**3. CHANGELOG.** Выполнен. Заголовок `## 0.6.0 — 2026-10-26` вместо `unreleased` (`CHANGELOG.md:11`), формат совпадает с остальными секциями. Audit-fixes абзац называет все задачи и описывает каждую — и каждое описание я сверил с кодом, не с памятью: вложенные record-пути (`gate.py:2160-2167` + `_record_path_task`, тесты `test_gate.py:2079/2108/2140/2170`), `self-accepted` на строке gate и в `report` (`gate.py:1930-1941`, `report.py:47`, `996-1003`, тесты `test_self_acceptance_on_every_surface.py:233/389`), решение `report` по completed-commit (`report.py:648-672`), `self-acknowledged` через общий comparison (`capture.py:426-452`, `gate.py:2390`, `cli.py:1830`, `tests/test_self_acknowledgement_mark.py`), file-form правило для manifest из base tree (`gate.py:662-729`), `nan`-устойчивое сравнение при rewrite switches (`switch_off.py:410-430`, `extension_trust.py:934-951`, тесты `test_personal_extensions.py:1449/1472`), outbox-отказы и escaping (`outbox.py:176-194`, `_pinned_blob:832-851`, `project.py:340-345`, тесты `test_outbox.py:2046/2095/2166`), требование extension-stages (`openspec/specs/extension-stages/spec.md:1803-1812`), тринадцать record types (13 записей `RecordTypeSpec` в `attestation.py`, `docs/known-defects.md:13`). Закрывающая строка documentation-only задач полна: каждая задача CR-205…CR-244 названа в секции; CR-245 по заведённому порядку (CR-205 попал в 0.6.0, а не в 0.5.0) уходит в следующие notes.

**4. README и proposal 012.** Выполнен. README теперь говорит, что `off` не сохраняет ничего от принятого verdict, а сырой вывод сохраняется при отказе на любом уровне — и это так: `_preserve_output` (`review.py:599-616`) вызывается из `_reject` безотносительно capture level, и в dry-run ветке (`review.py:1284`) тоже. В 012 старая строка «Not yet done» помечена superseded ссылкой на секцию Where, сама дата и текст находки не переписаны; «scaffold shipped in 0.2.0» подтверждается `CHANGELOG.md:906-907` внутри секции 0.2.0.

**5. harness-setup и template.** Выполнен и фактически верен. `outbox check` только читает (`_check` в `outbox.py:534+` ничего не пишет), `outbox status` требует `--index` (`outbox.py:141-146`), поэтому запись только с `*` — правильно; `extension list` не принимает аргументов и лишь пересчитывает хеши для доклада о grant (`extension_trust.py:131-133`, `700-743`), поэтому одна голая запись — правильно. Голый `agentmarshal gate` реально запускаем: все аргументы парсера опциональны (`cli.py:301-330`). Гранулярность в комментарии template выдержана: `outbox new`, `outbox send`, `extension trust/untrust/switch off/disable/enable` вместо групп; `stage` остался группой законно — у него единственный subcommand `run` (`stages.py:274-278`).

**6. Прочие файлы.** Diff не выходит за scope. Изменены только `.md`, `.json` и `.toml`, которые не читает ни один тест (проверил `tests/` на ссылки на `docs/templates`, `harness-setup`, `CHANGELOG`), так что pytest/ruff/mypy эти правки задеть не могут; прогон CI я не делал — полагаюсь на твою заметку о b222d7e.

## Findings (все advisory, ни один не блокирует)

**ADV-readme-refused-verdict-wording** — `README.md:52-54`: формулировка «a verdict that is refused keeps the reviewer's raw output at any level» читается двояко, потому что `rejected` — это одно из допустимых значений самого verdict. Сохранение сырого вывода происходит не при отказном verdict, а когда launcher отвергает вывод reviewer как неразборный (`review.py:813-824` `_reject`, вызовы из `_parse_verdict`); у записанного `blocked`/`rejected` verdict на уровне `off` prose не сохраняется нигде. Формулировка взята из самого критерия, поэтому это не расхождение с контрактом, а остаточная неточность той самой фразы, которую CR-243 ADV-readme-capture-off-1 просил починить.

**ADV-upgrading-outbox-eol-refusal** — `UPGRADING.md:50-54`: секция 0.5.0 → 0.6.0 не изменена, хотя audit fix CR-241 (AUD-commands-2) добавил отказ `outbox send`/`check`, который словит любой проект с `core.autocrlf` (а это Windows-адоптер B) или с clean filter на outbox: `_pinned_blob` (`outbox.py:832-851`) сравнивает blob с `--path` и с `--no-filters`, и лекарство — строка `-text` в `.gitattributes` (`outbox.py:912-920`, тест `test_outbox.py:2166`). То есть audit fix меняет то, о чём просит upgrade, а bullet про outbox по-прежнему говорит «No action needed» про свою тему и ничего про новый отказ. Критерий 3 оставляет это решение имплементеру, поэтому advisory, а не блокирующее.

**ADV-audit-file-untested** — `release/audit-0.6.0.toml:1`: поставляемый audit-файл не проверяется ничем в CI. `tests/test_release_audit_check.py` целиком работает на синтетических репозиториях, а `check_release_audit.py` запускается только в release-job на теге, так что опечатка в реальном файле проявится отказом релиза. Дёшево закрывается тестом, который грузит `release/audit-<текущая версия>.toml` и прогоняет по нему `_check_findings` и `_is_timestamp`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b222d7e47ab43dc0effd66149fd56a96bdc32405",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "ADV-readme-refused-verdict-wording",
    "ADV-upgrading-outbox-eol-refusal",
    "ADV-audit-file-untested"
  ],
  "classes": {
    "ADV-readme-refused-verdict-wording": "claim-accuracy",
    "ADV-upgrading-outbox-eol-refusal": "contract-mismatch",
    "ADV-audit-file-untested": "test-gap"
  },
  "verification": {
    "read": [
      "release/audit-0.6.0.toml",
      ".github/scripts/check_release_audit.py",
      "CONTRIBUTING.md (Releases section, lines 140-196)",
      "CHANGELOG.md (lines 1-12, 137-158, 200-330, 900-907)",
      "README.md (lines 38-64)",
      "UPGRADING.md (lines 3-62)",
      "docs/harness-setup.md (lines 60-118)",
      "docs/templates/claude-code-settings.local.json",
      "docs/proposals/012-upstream-feedback-channel.md",
      "docs/proposals/README.md (lines 238-249)",
      "docs/known-defects.md (line 13)",
      "docs/adr/ADR-0001-governance-plane.md",
      "src/agentmarshal/journal/review.py (_reject, _preserve_output, dry-run branch)",
      "src/agentmarshal/journal/gate.py (_manifest_from_tree, _record_path_task, added-records check, acceptance line)",
      "src/agentmarshal/journal/report.py (SELF_ACCEPTED_MARK, decision derivation, task line)",
      "src/agentmarshal/journal/capture.py (_acknowledgement_mark)",
      "src/agentmarshal/journal/attestation.py (RECORD_TYPES)",
      "src/agentmarshal/outbox.py (register, _locate, _check, _pinned_blob, remedy text)",
      "src/agentmarshal/project.py (outbox scaffold symlink refusal)",
      "src/agentmarshal/extension_trust.py (_run_list, parser, rewrite verification)",
      "src/agentmarshal/switch_off.py (rewrite verification)",
      "src/agentmarshal/switches.py (toml_values_equal)",
      "src/agentmarshal/stages.py (register)",
      "src/agentmarshal/cli.py (gate parser)",
      "openspec/specs/extension-stages/spec.md (lines 1803-1827)",
      ".agentmarshal/extensions/openspec.toml",
      ".agentmarshal/journal/tasks/CR-234..CR-245/contract.md (scope, acceptance, context)",
      ".agentmarshal/journal/tasks/CR-234..CR-245/records/ (lifecycle records)"
    ],
    "executed": [
      {
        "what": "listing lifecycle records of every task the audit file lists as fixed (CR-234..CR-244)",
        "result": "each task's last lifecycle record is 'completed'; CR-245 has only 'opened'"
      },
      {
        "what": "grep of AUD- ids across the fix tasks' contracts",
        "result": "every blocking id in the audit file maps to the task its contract names; AUD-commands-6, AUD-extensions-4/-5 and AUD-docs-claims-2-3.. are declared advisory in those contracts and are correctly absent"
      },
      {
        "what": "grep -c '\": RecordTypeSpec' src/agentmarshal/journal/attestation.py",
        "result": "13 — the 'thirteen record types' claim holds"
      }
    ],
    "not_run": [
      {
        "what": "python3 .github/scripts/check_release_audit.py v0.6.0",
        "why": "the review snapshot is not a git repository and nothing is tagged; the implementer's report with the command output was not supplied"
      },
      {
        "what": "a python run of the script's pure validators against release/audit-0.6.0.toml",
        "why": "python execution was denied in this sandbox; the same checks were applied by reading the file against the validators"
      },
      {
        "what": "uv sync --locked; agentmarshal validate; pytest; ruff check; ruff format --check; mypy",
        "why": "read-only review; the coordinator states the sequence passed on b222d7e, and the diff touches only .md/.json/.toml files no test reads"
      },
      {
        "what": "whether audited_at is the moment the last area ran, and whether 15af26e/dff244b are the stated commits",
        "why": "operator facts outside the repository; ULID times of CR-243/CR-244's opened records are consistent with the value but cannot confirm it"
      },
      {
        "what": "the diff between dff244b and the tag for fix-task paths outside their declared scopes (e.g. openspec extension footprint paths)",
        "why": "no git history in the snapshot"
      }
    ]
  },
  "evidence": {
    "ADV-readme-refused-verdict-wording": "README.md:52-54 vs src/agentmarshal/journal/review.py:813-824 (_reject preserves output only on a launcher refusal of malformed reviewer output) and review.py:599-616 (_preserve_output, independent of capture level); 'rejected' is a valid verdict value, making the sentence ambiguous",
    "ADV-upgrading-outbox-eol-refusal": "UPGRADING.md:50-54 unchanged; src/agentmarshal/outbox.py:832-851 (_pinned_blob compares --path against --no-filters) and outbox.py:912-920 (remedy: `.agentmarshal/upstream/** -text` in .gitattributes); tests/test_outbox.py:2166 test_an_autocrlf_refusal_names_the_same_remedy shows core.autocrlf alone triggers it",
    "ADV-audit-file-untested": "tests/test_release_audit_check.py builds synthetic repositories only (no test reads release/audit-0.6.0.toml); .github/scripts/check_release_audit.py runs in the release job on the pushed tag"
  }
}
AGENTMARSHAL_VERDICT_END
