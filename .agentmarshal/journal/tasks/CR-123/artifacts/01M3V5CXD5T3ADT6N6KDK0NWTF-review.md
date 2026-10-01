Прошёлся по диффу и сверил каждое утверждение о поведении инструмента с кодом: девять типов записей и их поля (`src/agentmarshal/journal/records.py:34`), ворота, читающие только `verdict` и покрытие blocking-списка acceptance-записью (`src/agentmarshal/journal/gate.py:898-937`), `--attestation commit` / `ci-required` (`src/agentmarshal/journal/gate.py:528`), снапшот через `git archive` (`src/agentmarshal/journal/review.py:652`), `agentmarshal finding --task` (`src/agentmarshal/cli.py:298-307`), пять полей аутбокса и `agentmarshal --version` в `CONTRIBUTING.md:38-42`, README аутбокса, который `init` пишет с 0.2.0 (`CHANGELOG.md:377`), и `init`, печатающий trust preconditions с 0.4.0 (`CHANGELOG.md:119`). Всё сходится. Шапки 027-031 используют тот же профиль Adopter D, что 014/018/024, релизы (0.3.0, 0.4.0) опубликованы, упомянутые номера proposal'ов (023, 026, 028, 030) тоже, посторонних идентификаторов репозитория репортёра нет, индекс и карта документации заполнены. Оригиналы репортёра и документ координатора с dispositions в снапшот не входят, поэтому дословность измерений и совпадение sha256 я проверить не мог — проверял внутреннюю согласованность (у 029 1+5+7=13, у 028 5+4=9 и т.д., расхождений нет). Последовательность CI запустить не удалось: `uv` в этой песочнице требует approval; дифф состоит только из документации, а единственный тест, который трогает `docs/`, проверяет лишь наличие ссылок на `docs/proposals/` в README (`tests/test_project.py:38-42`), так что причин для падения не видно — но утверждать, что критерий 5 выполнен, я не могу, что ровно и есть предмет proposal 030.

Ниже — непреграждающие замечания.

В `docs/proposals/031-the-contract-is-written-by-an-agent-and-nothing-governs-it.md:15-17` утверждение «a review record pins the contract it judged with a sha256» слишком широкое: `reviewed_contract` — опциональное поле схемы 5, и его выставляет только лаунчер (`src/agentmarshal/journal/review.py:906`); `submit-review` не передаёт его вообще (`src/agentmarshal/cli.py:629-641`), так что review-запись, созданная вручную, никакого хеша контракта не несёт. На этом же утверждении держится disposition («the review record already proves the primitive works», строка 82), и пропуск заодно занижает сам finding.

В `docs/proposals/030-review-verdicts-do-not-say-what-was-executed.md:67` «Both are legitimate work» не имеет внятного антецедента: ближайшее множественное в абзаце — «Two false blocking findings», и при таком чтении фраза говорит обратное задуманному. Имелись в виду два вида подтверждения — исполнение и чтение.

В `docs/proposals/027-advisory-findings-have-no-lifecycle.md:85-91` отклонённая часть (переименование verdict) не называет, кем она отклонена, хотя критерий 2 требует этого от declined- или withdrawn-части. Отозванную часть в 031 автор называет явно («withdrawn by the reporter»), а 024 и 031 говорят от первого лица («We will not…», «We record the withdrawal»); в 027 первого лица нет нигде.

В `docs/proposals/028-check-outcomes-are-not-evidence.md:3` и `docs/proposals/030-review-verdicts-do-not-say-what-was-executed.md:3` формулировка «accepted *(as a piece of work; deferred)*» применяет сразу две из трёх диспозиций, которые определяет раздел Disposition в `docs/proposals/README.md:30-40`, к целому предложению, а не к его части; документированная форма в скобках предназначена для «the part we are not taking». Сам раздел, хотя README в скоупе, под эту форму не расширен, так что репортёр, отслеживающий свою заявку по словарю диспозиций, видит неопределённое значение.

Файлы 027-030 не содержат раздела `## Where`, который есть у 024, 025, 026 и у 031 из этого же батча. Критерии его не требуют, но внутри одного батча расхождение заметно, а именно эту секцию индекс объявляет местом, где «a disposition without that column is a promise; with it, it is a place to look».

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "b06e6d2e2f85b0864dbd1df8cc57bd9dc023773e",
  "verdict": "approved",
  "findings": [],
  "advisory_findings": [
    "031-contract-hash-claim-overgeneralized",
    "030-both-has-no-antecedent",
    "027-declined-part-omits-decider",
    "028-030-disposition-form-not-in-vocabulary",
    "027-030-missing-where-section"
  ]
}
AGENTMARSHAL_VERDICT_END
