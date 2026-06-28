# Архитектура AgentMarshal

## Назначение

AgentMarshal — framework для управляемой работы нескольких AI-агентов над одним
Git-проектом. Он превращает неформальные сессии моделей в воспроизводимый
процесс:

```text
task → role/profile → isolated branch/worktree → evidence → review → triage
     → CI policy → merge
```

AgentMarshal не является системой запуска моделей общего назначения и не заменяет
Git provider, CI или issue tracker. Он задаёт contract, policy и проверяемые
шлюзы поверх существующего репозитория.

## Слои

### 1. Framework layer

Находится внутри `agentmarshal/`:

```text
docs/          architecture, host contract, ADR
methodology/   team workflow and operating rules
agents/        role specs and prompts
profiles/      execution capabilities and launcher policy
schemas/       machine-readable artifact contracts
adapters/      vendor-specific rendering/invocation
scripts/       enforcement, recorder and provider transport
tests/         regression and negative tests
config/        templates and worktree helpers
```

После extraction этот слой должен иметь собственный Git history, CI и release
version.

### 2. Host binding layer

Определяет, как framework подключён к конкретному проекту:

```text
.agentmarshal/
  project.json
  config/
  agents/
  prompts/
  providers/
  journal/
```

Целевая структура ещё не полностью реализована. Сейчас binding временно
находится в `agentmarshal/agentmarshal.config.sh`, `agentmarshal/agents/` и части scripts.
Это главный архитектурный долг перед extraction.

### 3. Record plane

Host-owned record plane. Recommended standalone layout:

```text
.agentmarshal/journal/
  tasks/       contracts and lifecycle
  stats/       normalized content-free performance records
  events/      append-only operational history
  handoffs/    responsibility transfer
  reviews/     canonical review attestations
  decisions/   host/project-specific ADR only
  runs/        raw model output, ignored
  tmp/         ephemeral recorder data, ignored
```

Record plane не входит в AgentMarshal repository. Один AgentMarshal release может
обслуживать несколько host repositories с независимыми журналами.
Текущая Phase 1 использует legacy `.agents/`; ADR-0007 требует configurable
paths до standalone cutoff.

### 4. Evidence plane

Состояние, которое нельзя заменить текстовым утверждением агента:

- branch и exact commit SHA;
- Git authorship и role identity;
- diff/provenance;
- test/build output;
- CI pipeline и job status;
- hashes raw review/manifest;
- screenshots/traces для UI;
- merge result.

### 5. Control plane

Сигналы, которые пробуждают и направляют агентов:

- task assignment;
- issue/MR event;
- review request;
- CI completion;
- handoff/ack;
- debt scheduling.

Сейчас реализованы CLI primitives для GitFlic и external runner contract. До
появления автоматического runner эту роль выполняет координатор вручную.
Event-driven runner/UI остаются отдельными проектами или host extensions.

## Главные сущности

### Role

Role отвечает на вопрос: **кто владеет изменением и какие пути ему доступны**.

Role spec содержит:

- stable role ID;
- branch prefix;
- allow/deny scope;
- role prompt;
- default vendor/model;
- human gates;
- trial restrictions.

Role identity стабильнее модели. Model может меняться, не меняя ownership.

### Execution profile

Execution profile отвечает: **с какими реальными capabilities запускается
сессия**.

Например, `qa-readonly`:

- `Read/Grep/Glob`;
- no write/shell/network;
- no native session persistence;
- output записывает launcher, не reviewer.

Role и profile нельзя объединять: QA может иметь read-only review, test-author
и visual/browser profiles с разными правами.

### Task

Task — unit of scheduling и auditable contract:

- `Owner`, `Type`, `Priority`, `Status`;
- scope и acceptance criteria;
- branch/profile/model hints;
- source provenance для review follow-up;
- verification evidence.

### Review

Review — attestation против exact SHA. Approval становится stale при любом
изменении candidate commit.

Read-only reviewer не пишет canonical review. Он возвращает raw attestation,
а trusted recorder сохраняет/материализует результат.

### Follow-up manifest

Структурированный JSON связывает findings с:

- новыми debt/security/process задачами;
- explicit `accepted_risk`;
- explicit `wont_fix`.

Полное покрытие finding IDs и идемпотентный `Triage-Key` предотвращают потерю
неблокирующих замечаний.

### Runtime config

Runtime config выбирает review language, active roles, worktree location и
statistics storage без изменения framework. Его path разрешается через
`.agentmarshal/project.json`; текущий legacy path — `.agents/config/agentmarshal.conf`.
Оба файла парсятся как данные и проходят validation.

### Agent run statistic

Нормализованная запись связывает task/role/vendor/model/profile с outcome,
duration, interventions, retries, scope violations, tests, findings,
diff size, token usage и cost. Raw content в запись не входит.

## Trust boundaries

### Trusted

- default branch policy и protected settings;
- Lead/dispatcher/recorder identity;
- trusted scope specs и gate logic из immutable default-branch SHA;
- canonical journal artifacts после validation;
- CI status exact candidate SHA;
- release artifacts AgentMarshal после extraction.

### Candidate-controlled

- branch content;
- candidate copy CI config/wrapper;
- agent text output;
- raw review files;
- task implementation commits.

Candidate-controlled данные никогда не должны самостоятельно определять
policy, которой они проверяются. `scope-guard-gitflic.sh` поэтому загружает
trusted logic/specs из immutable default-branch SHA.

### Advisory

- prompt instructions;
- recommended vendor/model;
- prose status reports;
- model self-assertion об отсутствии изменений.

Advisory данные полезны для поведения, но не являются security/enforcement
boundary.

## Enforced invariants

1. Role branch не изменяет файлы вне allow scope.
2. Integration branch сохраняет provenance persona commits.
3. Invalid refs/API responses/manifest shapes fail closed.
4. Agent branch имеет task ID.
5. Review относится к exact head SHA.
6. Reviewer не является implementation writer.
7. Required pipeline относится к exact head SHA.
8. Read-only reviewer не получает write capabilities.
9. Follow-up manifest покрывает каждый finding ровно один раз.
10. Повторный recorder run не создаёт дубликаты задач.
11. Active role существует и разрешена role spec.
12. Worktree root находится вне project repository.
13. Tracked statistics соответствуют schema и существующим task/role.
14. Worker workspace зарегистрирован как linked worktree того же Git
    common-dir; standalone clone не заменяет worktree.
15. Worktree finalization требует clean primary tree и
    `primary HEAD == integration SHA`.
16. Task остаётся `in_review` до merge; `done` требует exact reviewed SHA в
    target history, approved canonical review и completion evidence.
17. Completion выполняется через journal-only `completion/*` MR; direct push
    в protected target не требуется.
18. Cleanup worker worktree разрешён только после finalization и, в строгом
    режиме, exact pushed upstream.

## Потоки

### Implementation

```text
Lead creates task
  → Lead/external runner selects role/profile/model
  → worker uses role worktree/branch
  → pre-push scope guard
  → push/MR
  → trusted CI gates
  → handoff exact SHA
  → integration commit in primary history
  → worktree finalization gate
  → merge policy + merge
  → completion/* journal transaction
  → completion pipeline/review/MR
  → cleanup-ready gate
```

### Review

```text
pipeline SUCCESS exact SHA
  → read-only reviewer
  → raw review in ignored runs/
  → trusted recorder
  → canonical review / triage tasks / event
  → merge policy
```

### Technical debt

```text
approved review + findings
  → complete follow-up manifest
  → recorder validates coverage
  → tasks with Source-* + Due-Before + Triage-Key
  → Lead/external runner schedules debt session
```

## Не-цели

- защита секретов, уже находящихся в Git tree;
- hostile multi-tenant sandbox;
- доказательство корректности модели;
- замена code review автоматическими тестами;
- автоматический production deploy без host human gates;
- универсальный provider API без adapter layer.

Engineering isolation и scope enforcement уменьшают ошибки, но не дают
security isolation от агента с доступом к `.git`.
