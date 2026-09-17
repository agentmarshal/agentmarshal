Я прочитал diff, обе прошивки промпта, gate, CLI и тесты. Запустить pytest не удалось — sandbox отклонил запуск python, — поэтому проверка «тесты проходят» сделана чтением, а не прогоном. Ключевое я сверил вручную: реконструкция `_REVIEW_PROMPT` из `_prose_instruction()` и `_verdict_protocol()` даёт байт в байт прежний commit-промпт (включая переносы внутри склеенных строк), `finding_reviewer_identity_refusal` сохраняет ровно те же сообщения и ту же логику PASS/FAIL, что старый inline-блок gate, резолвер остался в одном экземпляре, и все шесть сценариев спеки названы docstring'ами тестов.

Блокирующих дефектов не нашёл. Четыре замечания — не блокирующие.

ADV-IDENTITY-REFUSAL-READS-INVERTED — `review.py:770-774` печатает как причину отказа формулировку gate-чека `gate.py:117-120`: оператор, которому отказали потому, что он и есть recorder, видит на stderr «declared reviewer identity differs from the finding recorder's declared git identities», то есть утверждение условия, которое верно как раз когда всё в порядке; в gate его спасает префикс `FAIL:`, а `cli.py:712` печатает его голым (design.md:73 действительно предписывает переиспользовать формулировку, так что это следование решению, а не отход от него).

ADV-SNAPSHOT-PATH-NOT-REFERENCE-PATH — `_extract_finding_snapshot` (`review.py:726`) кладёт файл по `artifact.path.relative_to(project_root)`, а `artifact_path` (`artifacts.py:29-33`) возвращает *разрешённый* путь, поэтому для ref-симлинка или абсолютного ref промпт называет `evidence/conclusion.md`, а в snapshot лежит `research/conclusion.md` — вразрез с design.md:64 «holding the verified files at their reference paths».

ADV-DRIFT-REFUSAL-STOPS-AT-FIRST-ARTIFACT — `_verified_finding_artifacts` (`review.py:701-704`) бросает на первом несовпавшем артефакте, тогда как findings-lane в `gate.py:228-245` перечисляет все; при дрейфе нескольких pinned-файлов оператор чинит их по одному, получая по одному запуску на артефакт.

ADV-NEW-CLI-PATH-UNDOCUMENTED — `review --reviewed-finding` теперь работает, но `docs/sidecar.md:403-430` («Research findings loop») по-прежнему показывает только `submit-review --reviewed-finding`; `docs/` не входит в `scope` контракта CR-101, так что это задел на следующую задачу, а не упущение этой.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "359515e382e6dc93033b9c911392f11f131fffdf", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-IDENTITY-REFUSAL-READS-INVERTED", "ADV-SNAPSHOT-PATH-NOT-REFERENCE-PATH", "ADV-DRIFT-REFUSAL-STOPS-AT-FIRST-ARTIFACT", "ADV-NEW-CLI-PATH-UNDOCUMENTED"]}
AGENTMARSHAL_VERDICT_END
