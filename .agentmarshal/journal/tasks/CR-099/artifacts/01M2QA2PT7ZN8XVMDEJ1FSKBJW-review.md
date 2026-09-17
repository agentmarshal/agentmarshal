Проверку делал статически: запуск `uv run pytest` / `python3 -m pytest` в этой песочнице не разрешён, поэтому тесты я читал, а не прогонял. Об этом говорю прямо — «зелёный прогон» я не подтверждаю.

Ядро правки корректно. `review_required` — keyword-only параметр со значением `True`, новая ветка `gate.py:938` срабатывает только при `latest is None`, так что при любом наличии review-записи (одобряющей или нет) поведение побайтово прежнее; `complete.py:59` и `cli.py:864` (sidecar-completion) флаг не передают, то есть merge authority этого проекта режимом не пользуется. Обе строки `NOT EXAMINED:` повторяют форму findings-полосы (`gate.py:141,146,241`). Все пять сценариев спеки закрыты тестами, чьи docstring называют их дословно. Дефолтный транскрипт не тронут.

Дальше — то, что я считаю проблемами.

**doc-claims-a-second-gate-run-github-does-not-have** — `docs/github-enforcement.md:76` утверждает «and why the merge authority runs the gate again without the flag». В документе про GitHub (Variant 2), где та же таблица внизу называет merge authority именно required-check'ом, это читается как обещание второго, review-enforcing прогона у адоптера. Двумя абзацами выше (`:37-42`) документ сам говорит обратное: «Nothing shipped here enforces it on GitHub» и что «this repository's own merge tooling» — это про GitFlic-путь, не про читателя. Два взаимоисключающих утверждения в одном документе, причём переоценка ровно того типа, из-за которого задача и существует («the documentation calls it advisory while the provider has no such state»). Acceptance-критерий 5 требует, чтобы этот файл описывал то, что теперь есть. Лечится переформулировкой одного предложения: назвать, что второй прогон без флага делает только собственный merge-путь этого репозитория (GitFlic/`complete`), а у адоптера на GitHub его нет.

**required-gate-blocks-non-cr-branches-undocumented** (advisory) — вместе с `continue-on-error` из шаблона ушла терпимость к структурным сбоям job'а, а `templates/github/agentmarshal-governance.yml:74` по-прежнему выводит задачу из имени ветки (`grep -oE 'CR-[0-9]+'`). Если ветка не содержит `CR-<n>`, получается `--task ""`, `validate_task_id("")` кидает, `gate` падает с кодом 1 — и теперь это блокирует merge, а не просто светится красным. `docs/github-enforcement.md:30-35` говорит «Mark it REQUIRED» и про это предусловие молчит. Dependabot- и release-PR упрутся в него первыми. Достаточно одной фразы в разделе Branch protection.

**repo-own-workflow-left-on-the-retired-arrangement** (advisory) — `.github/workflows/agentmarshal-governance.yml` всё ещё несёт `continue-on-error: true`, не просит `--without-review`, а в шапке пишет «`gate` is advisory until review materialisation (Phase C)». Это прямо противоречит и новому шаблону, и переписанному документу. Файл вне scope контракта, так что правильно, что его не трогали, — но собственный CI проекта остаётся на схеме, которую этот change объявляет снятой. Просится follow-up-задача со scope на `.github/`.

**archived-proposal-link-depth** (advisory) — `openspec/changes/archive/2026-09-17-gate-without-a-review/proposal.md:8` ссылается на `../../../docs/proposals/017-...`, что из архивного каталога разрешается в `openspec/docs/proposals/...` — такого пути нет. Соседний архив `2026-09-17-document-the-reviewer-contract/proposal.md:5` показывает верную глубину: `../../../../`. Ссылка была корректна, пока change лежал в `openspec/changes/<name>/`, и сломалась при архивации.

**passed-line-does-not-distinguish-a-partial-run** (advisory) — при чистом прогоне с режимом последняя строка — `gate: passed`, побайтово та же, что у полностью отсуженного кандидата. Threat model контракта просит, чтобы merge authority различала эти два случая «at a glance», а различие лежит двумя строками в середине транскрипта. design.md это фиксирует («The gate has no summary line to count them in»), так что формально критерий 1 выполнен, но обоснование слабое: итоговую строку можно было бы дополнить только под режимом, и дефолтный транскрипт при этом не сдвинулся бы.

**pinned-transcript-wrapper-duplicates-an-expensive-test** (advisory) — `tests/test_gate.py:232` добавляет тест, который целиком состоит из вызова уже существующего `test_embedded_diff_lane_transcript_matches_published_030_byte_for_byte`, чтобы повесить на сценарий docstring. Новое покрытие нулевое, зато самый дорогой тест набора (запуск released-бинаря подпроцессом + вторая сборка репозитория) исполняется дважды, и связка ломается от любого нового fixture-параметра у цели. Критерий 3 запрещает менять *expectations* пинованного теста — добавление docstring их не меняет.

**review-helper-duplicated-in-new-test** (advisory) — `tests/test_gate.py:345` вручную разворачивает 25-строчный вызов `submit-review`, который уже даёт хелпер `_require_changes(repo, head, "F-001")` в том же файле. Аналогично `_run_without_review` (`:295`) дублирует `_run` (`:226`) ради одного параметра.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "ed2556aa01e7ebfeea2f211407fbdf45a720e292",
  "verdict": "changes_required",
  "findings": ["doc-claims-a-second-gate-run-github-does-not-have"],
  "advisory_findings": [
    "required-gate-blocks-non-cr-branches-undocumented",
    "repo-own-workflow-left-on-the-retired-arrangement",
    "archived-proposal-link-depth",
    "passed-line-does-not-distinguish-a-partial-run",
    "pinned-transcript-wrapper-duplicates-an-expensive-test",
    "review-helper-duplicated-in-new-test"
  ]
}
AGENTMARSHAL_VERDICT_END
