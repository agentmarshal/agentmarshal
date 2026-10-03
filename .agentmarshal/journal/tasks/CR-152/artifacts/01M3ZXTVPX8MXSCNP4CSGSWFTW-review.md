Разобрал диф и состояние файлов на коммите `8b41fe4`. Код исполнять в этой песочнице нельзя (запуск `python3`/`pytest`/`mypy` требует подтверждения), поэтому CI-прогон я не воспроизводил — проверка статическая: парсер, тесты, delta-spec против ADR-0013/0015/0022 и против acceptance.

Что сходится:

- Все пять schema-2 секций разбираются ровно теми именами и доменами значений, что в примере ADR-0013 (`docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:311-342`): `phase` из трёх режимов, `command` под `bin/`, `[dependencies].lock` и `[wraps].lock` под `lock/`, `runtime` как `<name> >= <version>`, `kinds` вида `<name>/<kind>@<version>` со своим именем, `isolation` с `network`/`env`/`writes`/`timeout_seconds`.
- Лестница схем держится: `schema not in {1, 2}` (`extensions.py:335`), отказ schema-2 полей под schema 1 ровно в фразировке контрактного хедера (`extensions.py:339-344`, ср. `contracts.py:200-205`), `install`/`remove` слабеют только во второй схеме.
- `_require_directory_file` (`extensions.py:143-164`) действительно закрывает все четыре случая из AC: абсолютный путь и `..` — через `validate_scope_entry`, голое имя программы — через `len(parts) < 2`, чужой каталог — через `parts[0] != directory`; `bin/` и `bin//x` ловятся проверкой на пустой компонент.
- Все 21 сценарий delta-spec покрыты тестом с одноимённым docstring; формат архива и собранного `openspec/specs/extension-manifest/spec.md` совпадает с тем, что даёт archive-команда на соседних изменениях (сравнил с `2026-10-03-local-state-location`).
- Новые поля никто не читает: в `src/` обращения к манифесту только `.footprint`/`.documents` (`gate.py:847,886,927`, `review.py:1071,1247`, `brief.py:232`), `install`/`remove` не рендерятся нигде, дефолты на dataclass не ломают позиционную сборку. Фикстуры гейта не тронуты.

Блокирующего не нашёл. Три замечания в советующем режиме:

**adv-wraps-free-text-control-characters** — в `_parse_wraps` (`src/agentmarshal/journal/extensions.py:219-241`) `reject_control_characters` стоит только на `runtime` (строка 231), а `product`, `version`, `ecosystem` и `license` проходят через голый `_require_string`, то есть `license = "MIT\nAPPROVED: yes"` разберётся. Та же дырка в `_RECORD_KIND` (`extensions.py:43`): класс `[^/@\s]+` исключает пробельные, но пропускает `\x00`, `\x1b`, `\x7f` и bidi-override `\u202e`, которые `forges_rendered_text` считает способными подделать строку. Сейчас это не эксплуатируется (эти поля ещё никто не печатает), но `doctor` по D19 ADR-0013 будет их рендерить, и асимметрия с соседним `runtime` выглядит случайной, а не решённой.

**adv-schema-1-install-required-untested** — `tasks.md` 1.9 отмечен как «`install` и `remove` опциональны в schema 2, обязательны в schema 1 — verify: tests», но тестом закрыта только первая половина (`tests/test_extensions.py:263`). Ни один тест не подаёт schema-1 манифест без `install`/`remove`: `_write_manifest` всегда пишет оба поля, а `_parse` ходит только по второй схеме. Требование спеки «schema 1 requires them as non-empty strings» не прибито, и ветка `extensions.py:370-372` может тихо ослабнуть при следующем рефакторинге.

**adv-artifacts-required-vs-adr-example** — в schema 2 `artifacts` остаётся обязательным (`extensions.py:354`), поэтому пример манифеста из самого ADR-0013 (`docs/adr/ADR-0013-extensions-stages-scopes-isolation-trust.md:311-342`, где есть `footprint` и `documents`, но нет `artifacts`, `install` и `remove`) парсером отвергается. Решение задокументировано в `design.md` («The schema-1 field set stays required»), и личная область объявлена non-goal, но `install`/`remove` ослабили именно ради этого примера — а он всё равно не проходит. Стоит либо поправить пример в ADR, либо снять требование в задаче про directory/personal form, иначе первый, кто скопирует пример из ADR, получит отказ.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "8b41fe4b93c1148730990063d89351f55ea19898", "verdict": "approved", "findings": [], "advisory_findings": ["adv-wraps-free-text-control-characters", "adv-schema-1-install-required-untested", "adv-artifacts-required-vs-adr-example"]}
AGENTMARSHAL_VERDICT_END
