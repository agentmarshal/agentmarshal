Проверил диф статически: запустить pytest не смог — команда требовала подтверждения, которого в неинтерактивной сессии нет. Поэтому «тесты проходят» я не подтверждаю; всё ниже — из чтения кода.

Что сошлось: байты commit-промпта не тронуты (`_REVIEW_PROMPT`, `_review_prompt` без изменений, пинованный тест с неизменённым ожиданием), резолвер действительно существует один раз (`artifacts.py:17`, два вызова — `gate.py:214` и `review.py:711`, `_artifact_path` из `gate.py` удалён), вывод корня проекта через `journal_root.parents[1]` совпадает с тем, что делает gate, поэтому sidecar-ссылки резолвятся одинаково у обоих, проверка хэшей идёт до запуска reviewer'а, отказ называет оба субъекта, и все шесть сценариев спеки названы в докстрингах тестов — переиспользование докстринга в `test_prompt_without_named_material_is_the_prompt_written_before_schema_2` не осиротило сценарий contract-history, его по-прежнему называет `tests/test_brief.py:70`.

Теперь то, что мешает.

`F-001-named-material-duplicated`: в `src/agentmarshal/journal/review.py:214-228` блок «Named contract material» скопирован дословно из `_review_prompt` (`review.py:174-188`) вместо общего хелпера, хотя design.md в разделе Risks утверждает как факт, что «the shared parts (verdict protocol, named material, amendment history) stay in shared helpers» — и дрейф случился уже внутри этого же дифа: строка 187 говорит «absent in the reviewed tree», строка 227 — «absent in the project», два написания одной строки, то есть буквально тот урок CR-100 («two leak-scan callers ... still kept two spellings of the suppression key»), на который design.md ссылается в решении «One resolver, shared with the gate»; отступление в design.md не зафиксировано, поэтому первый acceptance-критерий не выполнен.

`F-002-verdict-parser-duplicated`: `_parse_finding_verdict` (`review.py:529-596`) переписывает целиком `_parse_verdict` (`review.py:476-526`) — скан сентинелов, разбор JSON, проверка объекта, missing/unknown-полей и типов, — так что verdict-протокол получил две независимые реализации, а `_VERDICT_REQUIRED`/`_VERDICT_OPTIONAL` перестали быть единственным определением формы вердикта; design.md же говорит «the parser accepts exactly one of the two» в единственном числе, и по той же логике «two copies would be two answers», которой обоснован общий резолвер.

`A-001-finding-snapshot-hides-named-documents`: `_extract_finding_snapshot` (`review.py:735`) кладёт в снапшот только проверенные артефакты, но промпт при этом перечисляет `Decisions:` и `Documents:` из заголовка контракта (`review.py:214-228`) — reviewer'а просят проверить вывод против ADR-0009, сидя в каталоге, где нет ни `docs/adr/`, ни `openspec/`; на commit-пути эти файлы лежат в снапшоте. Решение «snapshot is the verified artifacts, not the tree» зафиксировано осознанно, так что это следствие, а не промах, но как отгружено — названный материал reviewer'у недоступен.

`A-002-base-refusal-untested`: `cli.py:697` вводит новый отказ `review --base applies only to --commit`, и ни один тест его не покрывает, хотя tasks.md этого же изменения называет тест на каждый отказ.

`A-003-finding-prompt-unpinned-and-hard-wrapped`: `_FINDING_REVIEW_PROMPT` (`review.py:80-105`) рвёт фразы посередине («Review the supplied\ntask contract», «print one\nline of prose») там, где commit-шаблон использовал продолжение строки через `\`, и в отличие от него не защищён побайтовым тестом — ровно та сторона, которую design.md оставил без страховки.

`A-004-obfuscated-resolver-assertion`: `tests/test_gate.py:252-255` собирает имя атрибута как `"".join(("art", "ifacts"))`, хотя литерал «artifacts» встречается в этом же файле ещё 14 раз; обфускация ничего не даёт и только скрывает, что именно утверждает ассерт.

`A-005-no-independence-precheck`: лаунчер сверяет хэши до запуска, но не независимость reviewer'а, поэтому `review --reviewed-finding` с `--email` самого рекордера потратит прогон и допишет в append-only журнал review-запись, которую findings-lane (`gate.py:194-208`) будет отклонять всегда — та же асимметрия «до/после», которой design.md обосновал проверку хэшей в лаунчере.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "23c54095d07ed85fdc01ded5ed74c54d1ebcf7eb", "verdict": "changes_required", "findings": ["F-001-named-material-duplicated", "F-002-verdict-parser-duplicated"], "advisory_findings": ["A-001-finding-snapshot-hides-named-documents", "A-002-base-refusal-untested", "A-003-finding-prompt-unpinned-and-hard-wrapped", "A-004-obfuscated-resolver-assertion", "A-005-no-independence-precheck"]}
AGENTMARSHAL_VERDICT_END
