Вердикт — **approved**, три замечания advisory. Проверял статически: sandbox не дал запустить `uv run pytest` без подтверждения, поэтому ни новый `tests/test_quickstart.py`, ни остальной suite я не прогонял.

**Что проверено по acceptance:**
- **Changelog.** В секции 0.4.0 есть все задачи с CR-084 по CR-108, и у каждой подсекции названы задачи. Утверждения я сверил с кодом, все подтвердились:
  - схемы 4/5/6 (`records.py:144-153`); `agentmarshal review` всегда пишет `reviewed_contract` (`review.py:883`), значит каждое ревью получает схему 5;
  - порог в 20 хитов leak-scan (`gate.py:68`);
  - `TODO` в `doctor` и exit 0 (`cli.py:407-432`);
  - `NOT EXAMINED` для двух проверок, завязанных на ревью (`gate.py:949-954`);
  - отказ при дрейфе и при отсутствии проверяемых артефактов (`review.py:739-773`);
  - блокирующая проверка `named documents` (`gate.py:852`);
  - self-match для маркеров (`capture.py:471-488`).
  
  Где возможность частичная, это сказано: GitHub не проверяет требование независимого одобряющего ревью, а часть артефактов может остаться непроверенной. Слов вроде «planned/next/soon» в секции нет.
- **Upgrade guide.** В `UPGRADING.md` покрыты все пункты, которые требует contract: схемы 4/5/6 с текстом отказа 0.3.0, отказ writer'а (CR-102), reopening через gate (CR-105), `--without-review` вместе с шаблоном и изменение вывода leak-scan. Сверх этого описаны rename, коммит `artifacts/` и schema-2 contract header.
- **Версия.** Везде 0.4.0: `pyproject.toml`, `__init__.py`, `uv.lock`. `test_smoke` проверяет, что `--version` печатает `__version__`.
- **Упоминания версий.** Фразы про текущий релиз переведены на 0.4.0, исторические («new in 0.3.0», ADR-0009, proposals) остались как были. `tests/test_gate.py` и pinned-тест промпта в `test_review_launcher.py` не тронуты.
- **Три advisory от CR-107:**
  - В `docs/overview.md` направления больше не стоят под формулировкой «designed», у каждого пункта сказано, есть ли опубликованный дизайн. Пункт переименован в «Further contract metadata» и явно отделён от `extensions` из ADR-0010.
  - В proposal 005 «next in line» прямо помечено как несостоявшееся.
  - Комментарий job'а `governance` в workflow совпадает с шаблоном дословно.

**Замечания (не блокируют):**

`UPGRADING.md` (раздел 0.3.0 → 0.4.0) не упоминает, что `agentmarshal doctor` теперь выводит `TODO` для трёх новых предусловий и меняет строку `Summary:`, а `agentmarshal init` печатает список предусловий. Это такое же изменение вывода, как у leak-scan, которое там названо, и скрипт, ищущий `Summary: all N checks passed`, его заметит.

`UPGRADING.md` («Commit the review's prose with its record») говорит, как застейджить `artifacts/`, но не предупреждает, что полный вывод ревьюера теперь попадает в коммит. Во встроенном журнале публичного репозитория этот текст становится публичным, а в 0.3.0 он жил только во временном файле.

`README.md:56-60` (Status): абзац открывается «Version 0.4.0 ships…», а из нового выделено только «New in 0.3.0» (sidecar). О 0.4.0 ничего не сказано, и выглядит так, будто sidecar — самое свежее.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit": "eb6f57fd6cea2677a738807122f045b331a04d9e", "verdict": "approved", "findings": [], "advisory_findings": ["ADV-UPGRADING-DOCTOR-INIT-OUTPUT", "ADV-UPGRADING-PROSE-PUBLICATION", "ADV-README-STATUS-NAMES-ONLY-030"]}
AGENTMARSHAL_VERDICT_END
