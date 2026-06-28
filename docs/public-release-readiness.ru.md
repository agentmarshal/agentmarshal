# Готовность к публичному релизу

Document-ID: agentmarshal-public-release-readiness
Document-Version: 1
Language: ru

<!-- Section-ID: overview -->
## Обзор

Публичный релиз означает, что repository можно читать, клонировать и
подключать к новому host без private project context. Private operational
history может оставаться во внутренних repositories.

<!-- Section-ID: private-to-public -->
## От private к public

Перед публикацией подтвердите работу AgentMarshal минимум в двух host
repositories. Один host может быть software-development проектом; второй может
быть research или operations проектом, чтобы доказать независимость framework
от одного workflow.

<!-- Section-ID: sanitization -->
## Sanitization

Удалите или изолируйте:

- private host names, domains, IPs и credentials;
- raw model transcripts;
- customer или production information;
- host-specific ADRs, которые не описывают сам AgentMarshal;
- случайные assumptions о единственном Git provider.

<!-- Section-ID: prompts -->
## Prompts

Bundled prompts должны быть generic и English-first. Host-specific prompts
принадлежат host-local plugins или host configuration.

<!-- Section-ID: github -->
## GitHub

GitHub может быть публичным release home, даже если private development
начинается на другом provider. Public repository должен иметь собственный CI,
release tags и contribution guide.

<!-- Section-ID: release-branch -->
## Release Branch

Используйте protected public branch для stable releases и development branch
для framework changes, которые могут временно ломать host integrations.
