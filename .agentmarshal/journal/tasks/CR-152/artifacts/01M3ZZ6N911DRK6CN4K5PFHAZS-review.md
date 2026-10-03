Прошёл по контракту, delta-спеке и реализации. Все 26 сценариев спеки покрыты тестами с docstring'ами, которые их называют; схема-ладдер (1/2/3), `[[stage]]`, `[dependencies]`, `[wraps]`, `[records].kinds`, `[isolation]`, опциональность `install`/`remove`/`artifacts` и неизменность schema-1 — на месте; новые поля никто не читает (`gate`/`brief`/`review` берут только `documents`), диффа в фикстурах нет; скоуп диффа не выходит за контракт. Прогнать CI локально не смог — Bash в этой сессии отказывает в запуске `pytest`/`ruff`/`mypy`, так что последний acceptance-пункт проверен только статически.

Одно блокирующее расхождение.

Верхнеуровневое `version` — свободный текст, который манифест объявляет, — в schema 2 не проходит правило контрольных символов: `src/agentmarshal/journal/extensions.py:395` зовёт `_require_string`, а не `_require_text`, в отличие от `install`/`remove` (строки 405–406) и всех строк `[wraps]`. Это прямо противоречит нормативному требованию собственной спеки (`openspec/specs/extension-manifest/spec.md:25` — «Every free-text string a schema-2 manifest declares ... SHALL pass the control-character rule», причём в том же абзаце `version` назван «a non-empty string») и acceptance-пункту 4 вместе с поправкой к контракту от 2026-10-03 («free-text fields pass the control-character rule»). Ссылка на ADR-0015 («правило применяется с той схемы, что его ввела») тут не спасает: `install` и `remove` — такие же поля schema 1, и для них правило в schema 2 как раз включено, так что `version` выпадает не по границе схемы, а по пропуску. Практически: `schema = 2` с `version = "1.0\u2028fake"` сейчас парсится успешно, и теста на этот случай тоже нет.

changes_required: вместо `_require_string` для `version` в schema 2 нужен `_require_text` (с сохранением schema-1 поведения, если это намеренная граница), плюс тест на контрольный символ в `version`.

AGENTMARSHAL_VERDICT_BEGIN
{
  "reviewed_commit": "bf1670bfbeaa54efaa07e7a20db41fb0ff6fe877",
  "verdict": "changes_required",
  "findings": ["manifest-version-skips-control-character-rule"]
}
AGENTMARSHAL_VERDICT_END
