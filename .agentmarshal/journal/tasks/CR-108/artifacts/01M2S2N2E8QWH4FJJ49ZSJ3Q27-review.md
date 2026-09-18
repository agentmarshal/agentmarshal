Проверил всё, что можно проверить локально, и одобряю коммит `8d66a6b` с тремя замечаниями, ни одно из которых не блокирует. Покрытие `docs/` сверил вручную, скриптом сравнить не удалось.

**Что соответствует контракту:**
- **Карта документации.** `docs/README.md` покрывает все 45 файлов в `docs/`, битых ссылок нет, группировка по цели читателя. `README.md` на неё ссылается.
- **Issue-формы.** В `finding.yml` пять обязательных полей в точности по формату из CONTRIBUTING. Форма `gate-refusal.yml` на месте. `config.yml` отключает пустые issue и ведёт на SECURITY.md по абсолютному URL на ветку `master`, это совпадает с workflow.
- **Шаблон PR.** Пункты шаблона (CR-NNN, scope, `AGENTMARSHAL_ACTOR`, английский, шесть команд проверки) совпадают с CONTRIBUTING.md. Пункт «не меняет контракт» согласуется с `docs/self-hosting-workflow.md:13-17`: контракт попадает в base отдельным journal-only merge.
- **SECURITY.md.** Канал ровно один, срока ответа не обещает. Описание границы доверия согласуется с `README.md:12-19`.
- **CONTRIBUTING.md.** Прямо сказано, что проект ведёт один человек и срока ответа нет.
- **Несуществующие каналы.** Ссылок на Discussions или другие отсутствующие каналы нет.

**Замечания (не блокируют):**

1. `.github/pull_request_template.md:29`: относительная ссылка `../CONTRIBUTING.md#this-repository-governs-itself` в описании PR раскрывается относительно URL страницы `/pull/N` или `/compare/...`, а не пути к файлу. Там она даст 404. Лучше взять абсолютный URL, как в `config.yml`.
2. `.github/ISSUE_TEMPLATE/finding.yml:2`: политика языка есть только в поле `description`. По документации GitHub оно показывается в списке выбора шаблона, а верхний markdown-блок формы о языке молчит. В `gate-refusal.yml` политика стоит в самой форме. Проверить, выводит ли GitHub `description` на странице заполнения, локально я не смог.
3. `SECURITY.md:12-24`: пункт из acceptance про подделку (forging) переформулирован как «засчитать review/acceptance/completion для коммита, который в записи не назван». Сразу за этим сказано, что новая запись под выдуманной identity — не уязвимость. Поэтому не очевидно, входит ли в scope поддельный `completed`- или review-запись, которую gate принимает без прохождения gate. Остаётся лишь общий пункт «bypassing the gate».

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "8d66a6b46d7f287819b0f7babfafbdd3170108b3", "verdict": "approved", "findings": [], "advisory_findings": ["PR-TEMPLATE-RELATIVE-LINK-BROKEN", "FINDING-FORM-LANGUAGE-POLICY-NOT-IN-FORM-HEADER", "SECURITY-FORGED-RECORD-SCOPE-AMBIGUOUS"]}
AGENTMARSHAL_VERDICT_END
