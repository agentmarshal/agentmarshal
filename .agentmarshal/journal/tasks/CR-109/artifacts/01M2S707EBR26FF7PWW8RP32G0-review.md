Проверил diff по всем пяти пунктам acceptance и сверил утверждения с кодом, журналом, template и тестами. Блокирующих проблем нет: **approved**, с одним advisory.

**Что проверено**
- **CHANGELOG.** Секция 0.4.0 датирована 2026-09-18 и покрывает все задачи CR-084…CR-108. Каждая указанная задача есть в журнале и имеет запись `completed`. Утверждения совпадают с кодом:
  - schema 5 ставится на каждую review от `agentmarshal review` (через `reviewed_contract`), а `submit-review` его не несёт;
  - schema 6 используется только для `coordination`;
  - gate показывает не больше 20 leak-scan hits, standalone-команда показывает все;
  - `init` печатает четыре precondition, `doctor` выводит три из них как TODO, не меняет из-за них exit status и считает их в summary.

  Где возможность частичная, это сказано: GitHub не проверяет требование независимого review. Ссылки ведут на существующие ADR-0009, ADR-0010 и `docs/github-enforcement.md`. Слов «planned», «next», «soon» в тексте нет.
- **UPGRADING.** Все требуемые изменения есть: schemas 4/5/6, writers больше не пишут то, что projection не прочитает, reopen теперь проходит gate, режим `--without-review` вместе с изменением template, новый формат вывода leak-scan. Дополнительно описаны rename и то, что нужно стейджить `artifacts/`.
- **Версия.** Везде 0.4.0: `pyproject.toml`, `__init__.py`, `uv.lock`, `test_smoke`. `tests/test_gate.py`, где закреплён transcript 0.3.0, не менялся. Упоминания 0.3.0 как истории («new in 0.3.0») сохранены.
- **Три advisory от CR-107.**
  - В roadmap-секции `docs/overview.md` больше нет заголовка «designed»; у каждого пункта сказано, есть ли опубликованный design. Ссылки на ADR-0005 и ADR-0004 я проверил.
  - В proposal 005 пометка о supersession и датированная секция: проекция описана в опубликованном ADR-0005.
  - У job `governance` в workflow теперь тот же комментарий, что в template.

Тесты я не запускал: запуск `pytest` в этой сессии не одобрен, так что новый `tests/test_quickstart.py` проверен только чтением.

**Advisory.** В `docs/quickstart.md:6` сказано, что каждая команда ниже выполнялась на 0.4.0 до публикации. Но ниже есть `pip install agentmarshal==0.4.0` в `docs/quickstart.md:24`, а она до публикации не может сработать. Новый тест тоже прогоняет только раздел «The governed loop» из исходников.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "b83fab98bbee33427fbfdd6ec91e9334eb767bcf", "verdict": "approved", "findings": [], "advisory_findings": ["quickstart-every-command-claim-includes-unpublished-install"]}
AGENTMARSHAL_VERDICT_END
