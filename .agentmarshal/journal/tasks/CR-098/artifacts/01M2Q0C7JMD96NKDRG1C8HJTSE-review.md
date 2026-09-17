Разобрал изменение целиком: `doctor.py`, `cli.py`, шаблон workflow, спеку, design.md и то, как гейт выбирает свои полосы (`gate.py:655-732`, `gate.py:882-890`).

Ниже — по одной строке прозы на каждый идентификатор.

**Блокирующие**

`template-gate-never-runs` — в `templates/github/agentmarshal-governance.yml:74` условие нейтральности ищет `git grep` по дереву самого коммита `$HEAD_SHA` запись с `"reviewed_commit": "$HEAD_SHA"`, то есть требует, чтобы содержимое коммита называло собственный SHA; это недостижимо по построению (запись о ревью коммита C всегда лежит в коммите-потомке D), поэтому ветка `found -eq 1` срабатывает на каждом pull request, `agentmarshal gate` не вызывается никогда, а после снятия `continue-on-error` проверка стала зелёной по построению вместо красной по построению — ровно та же болезнь, которую эта задача лечит, с обратным знаком; сценарий спеки «a head that carries its review is gated» недостижим, а будущий путь Phase C тоже не спасёт, потому что материализованная запись ляжет в рабочее дерево, а `git grep <tree>` его не видит.

`template-drops-deterministic-lanes` — там же, `templates/github/agentmarshal-governance.yml:74-86`: страж пропускает весь вызов гейта, а требование, которое он реализует (`openspec/specs/trust-preconditions/spec.md`, «It SHALL succeed **without evaluating the review-bound lane**»), говорит пропускать только review-bound полосу; журнальные кандидаты (openings и completions) проходят детерминированную полосу без всякой записи о ревью (`gate.py:730-733`), поэтому теперь на PR перестали проверяться scope, append-only, base-state и lifecycle — то, что `docs/github-enforcement.md:60-65` до сих пор перечисляет как то, что эта проверка «fully enforces», и что снятый комментарий шаблона заявлял как ценность advisory-режима; галочка `tasks.md` 3.1 («and runs the gate when it does») отмечена за поведение, которого нет.

`doctor-ci-check-github-only` — `src/agentmarshal/doctor.py:147-176`: проверка «CI validate definition» смотрит только в `.github/workflows/*.yml|yaml`, тогда как сам этот репозиторий держит CI в `gitflic-ci.yaml` в корне (строка 23 — `uv run agentmarshal validate`), так что `agentmarshal doctor` в собственном проекте напечатает `FAIL: CI validate definition — no CI definition invokes agentmarshal validate`; для любого не-GitHub адоптера чек красный по построению, что прямо противоречит Purpose добавленной спеки («never to ship a check that is red by construction») и vendor-neutral позиции ADR-0001 (`docs/overview.md:18` — «works on GitHub, GitFlic, or a self-hosted setup»), причём отступление в design.md не зафиксировано.

**Советующие**

`doctor-precondition-names-duplicated` — `src/agentmarshal/cli.py:73-75` дублирует имена чеков строковыми литералами, оторванными от `doctor_checks()` в `doctor.py:193-201`; переименование чека там молча переведёт advisory-precondition в жёсткий отказ (`cli.py:395` вернёт 1), нарушив «SHALL NOT make doctor exit non-zero», и ни один тест это соответствие не стережёт — признак лучше держать на самом `DoctorCheck`.

`doctor-summary-conflates-failure-and-advice` — `src/agentmarshal/cli.py:394` печатает «check(s) reported unmet» и для настоящих поломок тоже, так что при отсутствующем git строка итога звучит как совет, хотя код возврата 1; критерий «не утверждать, что все проверки прошли» выполнен, но различить сломанный проект и невыполненную предпосылку по итоговой строке больше нельзя.

`contract-document-path-absent` — контракт CR-098 называет документ `openspec/changes/report-what-the-tool-cannot-verify/`, и критерий приёмки 1 ссылается на `.../specs/trust-preconditions/spec.md` внутри него, но на ревьюируемом коммите этот путь не существует: изменение создано сразу в `openspec/changes/archive/2026-09-17-report-what-the-tool-cannot-verify/`, поэтому проверяющий по букве критерия упирается в несуществующий путь.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "35e75be07ca73b71b55d55ba37ae8556a81388ac", "verdict": "changes_required", "findings": ["template-gate-never-runs", "template-drops-deterministic-lanes", "doctor-ci-check-github-only"], "advisory_findings": ["doctor-precondition-names-duplicated", "doctor-summary-conflates-failure-and-advice", "contract-document-path-absent"]}
AGENTMARSHAL_VERDICT_END
