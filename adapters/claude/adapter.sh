#!/usr/bin/env bash
# Claude Code адаптер. Рендерит agnostic role-спеку в нативный субагент
# .claude/agents/<role>.md (frontmatter name/description/tools + system prompt).
# Вызывается из adapters/render.sh, использует его spec_* парсеры.

render_claude() {
  local role="$1"
  local name display prompt_file out
  name="$(spec_scalar role)"
  display="$(spec_scalar display_name)"
  prompt_file="$AOPS/agents/$(spec_scalar prompt)"
  out="$ROOT/.claude/agents/$role.md"

  # vendor-нейтральные tools → инструменты Claude Code
  local has_shell="no" claude_tools="Read, Edit, Write, Grep, Glob" t
  while read -r t; do [[ -z "$t" ]] && continue
    case "$t" in git|npm|npx|docker*|pytest|python|ssh|tofu|mr|ci) has_shell="yes" ;; esac
  done < <(spec_list tools)
  [[ "$has_shell" == "yes" ]] && claude_tools="$claude_tools, Bash"

  local allow deny
  allow="$(spec_list scope_allow | sed 's/^/  - /')"
  deny="$(spec_list scope_deny  | sed 's/^/  - /')"
  [[ -z "$allow" ]] && allow="  (без ограничений — Lead)"

  mkdir -p "$(dirname "$out")"
  {
    echo "---"
    echo "name: $name"
    echo "description: $display — роль из agentmarshal/agents/$role.yaml (vendor-agnostic источник истины). НЕ редактировать вручную: \`agentmarshal/adapters/render.sh $role claude\`."
    echo "tools: $claude_tools"
    echo "---"
    echo
    echo "<!-- СГЕНЕРИРОВАНО agentmarshal/adapters/render.sh из agentmarshal/agents/$role.yaml."
    echo "     Правки вносить в спеку, затем перегенерировать. -->"
    echo
    echo "# $display"
    echo
    echo "Ты исполняешь роль **$name** в команде agentmarshal проекта ${AGENTMARSHAL_REPO_NAME}."
    echo "Co-Authored-By: email привязан к роли (\`${AGENTMARSHAL_ROLE_EMAIL[$role]:-?}\`),"
    echo "display name = твоя модель — для traceability в git log."
    echo
    echo "## Твой scope (что ты ИМЕЕШЬ ПРАВО трогать)"
    echo "$allow"
    if [[ -n "$deny" ]]; then echo; echo "## Явно ЗАПРЕЩЕНО"; echo "$deny"; fi
    echo
    echo "Границы держит механически \`agentmarshal/scripts/scope-guard.sh\` (pre-push + CI)."
    echo "Ветки только с префиксом \`$(spec_scalar branch_prefix)/\`. Merge — через Lead."
    echo
    echo "## Роль"
    if [[ -f "$prompt_file" ]]; then cat "$prompt_file"; else
      echo "_(промпт роли: $prompt_file — пока не задан, см. agentmarshal/agents/prompts/)_"
    fi
  } > "$out"
  echo "✅ claude: $out"
}
