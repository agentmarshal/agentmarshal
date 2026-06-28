# Startup Guide AgentMarshal

Document-ID: agentmarshal-startup-guide
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

Этот документ описывает первый день новой host-интеграции AgentMarshal.
AgentMarshal является Git governance layer: он даёт контракты, evidence,
policy checks и runbook rails. Он не является model runtime.

<!-- Section-ID: when-to-use -->
## Когда использовать

Используйте AgentMarshal там, где работа агентов должна быть аудируемой:
важны task contracts, независимое review, exact SHA, CI evidence и durable
follow-up tracking, а не максимальная автономность любой ценой.

<!-- Section-ID: install -->
## Установка

Добавьте AgentMarshal как pinned submodule:

```bash
git submodule add <agentmarshal-url> agentmarshal
git submodule update --init --recursive
```

Submodule не должен следить за moving branch. Host обновляет gitlink отдельной
задачей и review.

<!-- Section-ID: init -->
## Инициализация

Новый host:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language ru
./agentmarshal/bin/agentmarshal doctor --project-root .
./agentmarshal/bin/agentmarshal validate --project-root .
```

Host с историческим archive `.agents`:

```bash
./agentmarshal/bin/agentmarshal init --preset minimal --language ru \
  --legacy-archive .agents
```

Используйте `--adopt-existing` только если старый journal остаётся активным
runtime.

<!-- Section-ID: first-task -->
## Первая задача

1. Создайте небольшую documentation/configuration task.
2. Сгенерируйте task-local AgMake runbook.
3. Проверьте runbook до запуска.
4. Запустите runbook в терминале, а не внутри долгого polling model loop.
5. Отправьте exact implementation commit независимому reviewer.

```bash
./agentmarshal/bin/agmake init --task CR-001 --branch docs/CR-001-first-task
./agentmarshal/bin/agmake lint .agentmarshal/journal/tmp/runner/CR-001-runbook.sh
bash .agentmarshal/journal/tmp/runner/CR-001-runbook.sh
```

<!-- Section-ID: update -->
## Обновление

Обновление framework является изменением host:

```text
read changelog -> update submodule -> host CI -> review exact gitlink -> merge
```

Не пушьте framework commits из host submodule checkout, если operator явно не
открыл framework-development task.
