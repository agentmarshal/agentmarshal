Проверил снапшот: десять дайджестов, обновлённый индекс и абзац в CONTRIBUTING. Сверил заявленные цифры с журналом (21 amendment-запись в 18 из 91 завершённой задачи — совпадает), проверил дайджесты на утечки путей, идентификаторов задач и кода — чисто.

**Blocking**

`source-hash-truncated-contradicts-stated-lookup` — все десять дайджестов несут `**Source:** sha256:<16 hex>` (напр. `docs/proposals/014-init-leaves-trust-preconditions-unchecked.md:3`), то есть 64-битный префикс, а не sha256. При этом `docs/proposals/README.md:45-49` говорит «Its **source line** is the sha256 of the file you sent» и прямо инструктирует: «Hash your outbox file and search this directory for the result» — репортёр, выполнивший ровно это (`sha256sum finding.md`, поиск полного 64-символьного hex), не найдёт ничего. То же утверждение продублировано в `CONTRIBUTING.md:57-59`. Усечение нигде не документировано, и оно расходится с собственной конвенцией проекта (`docs/adr/ADR-0009-research-findings-lifecycle.md:54`: «sha256 over the artifact's bytes, lowercase hex»). Критерий 2 требует, чтобы по source-строке репортёр мог сопоставить дайджест со своим файлом; описанная процедура сопоставления не работает. Чинится либо публикацией полного дайджеста, либо явной формулировкой «первые 16 hex-символов sha256» в обоих местах.

**Advisory**

`016-disposition-does-not-name-release` — критерий 4 требует, чтобы дайджест уже исправленной на default-ветке находки *в своей disposition* назвал релиз, который понесёт фикс. `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:47-49` говорит «has been on the default branch since shortly after the release» (первая половина выполнена) и «The behaviour ships in the next release» — релиз обозначен ссылкой, но не назван. Версию `0.4.0` называет только строка индекса (`docs/proposals/README.md:82`). Формально читатель дайджеста в отрыве от таблицы версию не получает; правка — в одно слово.

`reporter-profile-names-provider` — профиль репортёра в индексе (`docs/proposals/README.md:122`) и строка в каждом дайджесте называют конкретного провайдера («GitHub»), тогда как установленная в том же файле конвенция обобщает его (Adopter A: «Git hosting provider»). Это сужает круг анонимности сильнее, чем у прошлой партии, хотя содержательно оправдано: proposal 017 — про шаблон, который проект поставляет именно для GitHub. Не блокирует, но стоит решить сознательно, а не по инерции.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "9a459a0d64e875952361a58c1cd06a6427c858f3", "verdict": "changes_required", "findings": ["source-hash-truncated-contradicts-stated-lookup"], "advisory_findings": ["016-disposition-does-not-name-release", "reporter-profile-names-provider"]}
AGENTMARSHAL_VERDICT_END
