Я проверил diff по пяти пунктам acceptance, сверяясь со снапшотом. Замечаний, которые блокировали бы merge, нет. Прогнать CI не удалось: запуск `uv run pytest` потребовал подтверждения, а снапшот не git-репозиторий, так что `agentmarshal validate` здесь не отработает.

**Что сходится:**
- **Reporter и профиль.** Строка Reporter в 024 слово в слово совпадает с 014–023: Adopter D, тот же профиль, Observed on 0.3.0. Source указан как полный sha256 в lowercase hex, как того требует индекс.
- **Три предложения.** У каждого своя disposition с обоснованием: vocabulary и statement приняты, reset-time field отложен до той же переделки accounting, что и cost field из 018. Это совпадает с тем, что написано в 018.
- **Индекс.** В нём появилась таблица batch 2026-09-18 с колонками Disposition и Where. Раздел «Tracking what happened to yours», который объясняет, как по хешу файла из outbox найти свой digest, уже был в индексе до этого diff.
- **Quickstart.** Описание поведения верное:
  - `--outcome` обязателен (`cli.py:292`), пустое значение отвергается проверкой non-empty в `records.py:512`.
  - `report` значение `outcome` нигде не агрегирует.
  - `provider-limit` подан как соглашение, а не как проверяемое значение.
- **README.md.** Формулировок, называющих токены стоимостью задачи, в нём не осталось. Ссылок на старый заголовок шага 7 я не нашёл.
- **Неопубликованные релизы.** Таких упоминаний нет. Релиз 0.4.0 с тремя новыми схемами (CR-086, CR-096, CR-106) есть в CHANGELOG с датой 2026-09-18. Для отложенного поля написано, что оно «not scheduled in any published release yet».

**Что не проверено:** сам исходный файл в репозитории не лежит, поэтому я не могу подтвердить, что измерения процитированы дословно. Сверил только с текстом контракта: 13 сессий и 2 отказа совпадают.

**Advisory (не блокирует):** в `docs/quickstart.md`, в абзацах про незакоммиченную запись в шаге 7, отредактированные строки «measurement would live in a working tree instead of in git, which is the thing this project» и «Nothing calls this for you. Recording the measurement is a step of your loop — put it» после правки не переформатированы и выходят за ширину ~80 символов, как и строка «for a coordinated upgrade over three new schemas. That rework is not scheduled in» в 024. Остальной текст держит эту ширину.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "ebbac7f8bd21f540eab4c761ed48370dc1d85c06", "verdict": "approved", "findings": [], "advisory_findings": ["quickstart-step7-line-wrap"]}
AGENTMARSHAL_VERDICT_END
