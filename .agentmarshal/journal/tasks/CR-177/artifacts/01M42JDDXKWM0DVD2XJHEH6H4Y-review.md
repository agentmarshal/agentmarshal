Я прочитал код в снапшоте и сверил его с контрактом, с ADR-0018/ADR-0022 и с опубликованными спеками. Ниже — что проверено и что нашёл.

**Что подтвердилось как сделанное правильно**

- `agreement` объявлен один раз в `RECORD_TYPES` (`src/agentmarshal/journal/attestation.py:100`): predicate type, `projects_to=None`, `admitted_after_terminal` по умолчанию пустой (значит — никогда после terminal, как «no» в таблице ADR-0022 раздела 3), `writable` по умолчанию `True`, `requires_recorded_by=True`. Всё производное (`PREDICATE_TYPES`, таблицы проекции, writable-множество) выводится из реестра; два рукописных места — `_RECORD_FIELDS` и `WritableRecordType` — обновлены, и pinning-тест в `tests/test_attestation.py` получил литералы.
- `contract` зарегистрирован через **ту же** `_SCHEMA_7_CONTRACT_FIELDS` (`records.py:400`), второго 64-hex-правила нет. Порядок правил проверен по месту регистрации: `contract-hash-7` на строке 870 идёт раньше `agreement-fields-7` на 912, поэтому форму владеет общее правило, а новое проверяет только наличие — как и заявлено в design.md.
- Нижние schema закрыты с двух сторон: запись/чтение агримента со `schema: 6` и полем `contract` ловит правило `fields` (строка 525, bound 1) сообщением про unsupported fields, а «пустой» агримент ниже 7 — gate-правило `agreement` (строка 648, bound 1). Тесты пинят оба сообщения в правильном порядке срабатывания.
- `_minimum_schema` поднимает 7 по типу (`records.py:1892`), `create_agreement_record` построен по образцу `create_check_record`/`create_acknowledgement_record` (keyword-only `source`, стамп в конце).
- Опубликованные требования contract-governance «An opened or amendment record may carry the contract's hash» (строка 136) и «The contract field is refused below schema 7» (строка 167) я прочитал целиком: они говорят про `opened`/`amendment` через `MAY` и нигде не резервируют поле только за ними, так что они остаются буквально истинными — MODIFIED действительно не нужен. Drift-требование (`status_view.py:180`) сравнивает только с `opened`/`amendment`, агримент его не трогает. `record-schema`'s требования про реестр и таблицу правил сформулированы механизмом, а не перечнем типов, — тоже не ломаются.
- Gate ничего не хардкодит: `gate.py:811-830` берёт тип из имени файла и спрашивает проекцию, поэтому «допускается так же, как другие schema-7 типы» выполняется структурно, а не списком. Фикстуры в `tests/fixtures/` не тронуты.
- Все 12 сценариев спеки имеют тест с называющим их docstring'ом.

Теперь — три advisory-замечания, ни одно не блокирующее.

Перечисление forgeable-полей в `docs/threat-model.md:101` по-прежнему говорит «an `opened` or `amendment` record's `contract`», тогда как `("agreement", "contract")` теперь тоже зарегистрирован в `_FORGEABLE_TEXT_FIELDS` (`records.py:477`) — опубликованный threat model стал неполным. Это отложено верно: `docs/` нет в scope контракта, AGENTS.md требует именно не расширять диff, и design.md эту дырку называет. Тестом она не ловится (ни один тест не пинит threat-model), так что её легко потерять — её стоит закрыть вместе с задачей про `agree`/`status`.

Константа `_AGREEMENT_RECORD_SCHEMA = 7` вставлена в `src/agentmarshal/journal/records.py:237`, то есть между `_SCHEMA_7_ACKNOWLEDGEMENT_FIELDS` и `_ACKNOWLEDGEMENT_REASON_CHAR_LIMIT`, и разрывает блок acknowledgement: комментарий выше (строки 227-232) объясняет «a bounded reason», а сама константа этого лимита теперь оторвана от него четырёхстрочным комментарием про agreement. Чисто читаемость, поведение не меняется.

Тест сценария «a recorder that is not a declared actor is accepted» (`tests/test_agreement.py:143-160`) пишет в `tmp_path/"journal"`, где нет ни `project.json`, ни таблицы акторов вовсе, и ставит `AGENTMARSHAL_ACTOR`; `resolve_recorded_by` (`actors.py:97-99`) возвращается на override до любого обращения к таблице, так что assert прошёл бы точно так же и для объявленного актора. То есть тест демонстрирует «override записывается как дан», но не отличает «не объявлен — всё равно принят» от «таблицу просто некому было прочитать». Docstring при этом утверждает «The project's actors table declares no actor at all here», что формально верно, но наводит на мысль, что проект существует. Более сильный паттерн в репозитории есть — `tests/test_journal.py:1870` поднимает `project.json` с акторами и проверяет источник `project-actor`; через него сценарий проверялся бы по существу.

Блокирующих дефектов не нашёл: сам record type, его поле, оба schema-гейта, проекция и поведение gate соответствуют контракту и ADR-0022, и ни один другой record type не затронут.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "5bbda5876ffc950c6d468c6461c9535103522508", "verdict": "approved", "findings": [], "advisory_findings": ["threat-model-forgeable-enumeration-omits-agreement-contract", "agreement-schema-constant-splits-acknowledgement-block", "declared-actor-scenario-test-has-no-actors-table"]}
AGENTMARSHAL_VERDICT_END
