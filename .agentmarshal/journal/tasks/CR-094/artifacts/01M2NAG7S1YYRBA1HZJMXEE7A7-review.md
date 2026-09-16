Проверил все пять критериев приёмки против снапшота и против кода на дефолтной ветке.

Что подтвердилось:

- Десять дайджестов `014`–`023`, у каждого строка с `**Observed on:** 0.3.0`, полный lowercase-sha256 (проверил: ровно 64 hex, все десять уникальны), секции `## Finding` / `Measurements, as reported` / `## Proposed` / `## Disposition` с обоснованием.
- Санитизация чистая: по дайджестам и по строкам индекса нет URL, доменов, путей, идентификаторов задач (`[A-Z]{2,}-\d+`), расширений файлов; единственные backtick-спаны — имена собственных команд проекта (`init`, `doctor`, `leak-scan`, `record-session`, `review`, `validate`, `agentmarshal review`). Профиль Adopter D описывает setup, не продукт/клиента/домен.
- Колонка `Where` заполнена во всех десяти строках; `016` в диспозиции прямо говорит, что поведение уже на дефолтной ветке, и называет 0.4.0.
- CONTRIBUTING (строки 57–64) описывает все три ручки отслеживания и отсылает к `docs/proposals/README.md`.
- Фактические утверждения дайджестов сверил с кодом: `_SESSION_ACTIVITIES = {implementation, review, other}` (`src/agentmarshal/journal/records.py:151`) подтверждает 018; четыре проверки `doctor` (`src/agentmarshal/doctor.py:119-124`) подтверждают 014; `_run_reviewer` возвращает только stdout и использует stderr лишь для ненулевого кода возврата (`src/agentmarshal/journal/review.py:193-210`) подтверждает 021 и 015; `submit_review(..., prose=raw_output)` без kept-at пути (`review.py:418-431`) подтверждает диспозицию 016.
- Самопроверяемое утверждение в 022 сходится точно: в журнале 21 amendment-запись в 18 задачах из 91 завершённой, и CR-075 — ровно описанный случай (второй review `changes_required`, затем amendment о формулировке критерия, затем третий и четвёртый раунды против изменённого текста).
- Затронуты только `docs/proposals/` и `CONTRIBUTING.md`; non-goals не нарушены.

Одно замечание, не блокирующее:

In `docs/proposals/016-reviewer-prose-not-durable-in-the-published-release.md:48`, the line `which this proposal has moved earlier in the plan. And the` is an unfilled mid-paragraph wrap (57 characters where every other prose line in the batch fills to ~79), leaving a ragged break inside the disposition; it is the only such line across the ten new digests and the index.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "121b9cbbc2d9d86a7a86b127a57f1f2f86e4df00", "verdict": "approved", "findings": [], "advisory_findings": ["016-disposition-unfilled-line-wrap"]}
AGENTMARSHAL_VERDICT_END
