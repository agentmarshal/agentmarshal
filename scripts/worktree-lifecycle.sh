#!/usr/bin/env bash
# Enforced lifecycle gates for project worktrees and integration finalization.
set -euo pipefail

COMMAND="${1:-}"
[[ -n "$COMMAND" ]] || {
  echo "usage: worktree-lifecycle.sh {project-preflight|worktree-preflight|finalize|cleanup-ready} [options]" >&2
  exit 2
}
shift

ROOT="${AGENTMARSHAL_PROJECT_ROOT:-${AGENTOPS_PROJECT_ROOT:-}}"
WORKTREE=""
INTEGRATION_SHA=""
INTEGRATION_REF=""
REQUIRE_PUSHED="no"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-root) ROOT="${2:?}"; shift 2 ;;
    --worktree) WORKTREE="${2:?}"; shift 2 ;;
    --integration-sha) INTEGRATION_SHA="${2:?}"; shift 2 ;;
    --integration-ref) INTEGRATION_REF="${2:?}"; shift 2 ;;
    --require-pushed) REQUIRE_PUSHED="yes"; shift ;;
    -h|--help)
      echo "usage: worktree-lifecycle.sh {project-preflight|worktree-preflight|finalize|cleanup-ready} [options]"
      exit 0
      ;;
    *) echo "worktree-lifecycle: unknown argument '$1'" >&2; exit 2 ;;
  esac
done

if [[ -z "$ROOT" ]]; then
  ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" \
    || { echo "worktree-lifecycle: project root not found" >&2; exit 2; }
fi
ROOT="$(cd "$ROOT" && pwd -P)"

die() {
  echo "worktree-lifecycle: $*" >&2
  exit 1
}

git_abs() {
  local repo="$1"
  shift
  git -C "$repo" rev-parse --path-format=absolute "$@" 2>/dev/null
}

project_common_dir() {
  git_abs "$ROOT" --git-common-dir \
    || die "'$ROOT' is not a Git repository"
}

probe_directory_write() {
  local directory="$1" label="$2" probe
  [[ -d "$directory" ]] || die "$label directory not found: $directory"
  probe="$(mktemp "$directory/.agentmarshal-write-probe.XXXXXX" 2>/dev/null)" \
    || die "$label is read-only; dispatcher cannot create refs/commits"
  rm -f "$probe" \
    || die "cannot remove $label write probe: $probe"
}

assert_git_metadata_writable() {
  local repo="$1" refs git_dir
  refs="$(git_abs "$ROOT" --git-path refs)" \
    || die "cannot resolve Git refs directory"
  git_dir="$(git -C "$repo" rev-parse --absolute-git-dir 2>/dev/null)" \
    || die "cannot resolve Git directory for '$repo'"
  probe_directory_write "$refs" "Git refs"
  probe_directory_write "$git_dir" "Git index/metadata"
}

assert_registered_worktree() {
  local wt="$1" wt_abs common expected line branch registered="no"
  [[ -d "$wt" ]] || die "worktree directory not found: $wt"
  wt_abs="$(cd "$wt" && pwd -P)"
  common="$(git_abs "$wt_abs" --git-common-dir)" \
    || die "'$wt_abs' is not a Git repository"
  expected="$(project_common_dir)"
  [[ "$common" == "$expected" ]] \
    || die "'$wt_abs' is a standalone clone, not a worktree of '$ROOT'"

  while IFS= read -r line; do
    if [[ "$line" == "worktree $wt_abs" ]]; then
      registered="yes"
      break
    fi
  done < <(git -C "$ROOT" worktree list --porcelain)
  [[ "$registered" == yes ]] \
    || die "'$wt_abs' is not registered in git worktree list"

  branch="$(git -C "$wt_abs" symbolic-ref --quiet --short HEAD 2>/dev/null)" \
    || die "'$wt_abs' has detached HEAD"
  [[ -z "$(git -C "$wt_abs" status --porcelain --untracked-files=all)" ]] \
    || die "'$wt_abs' is dirty"
  echo "worktree-lifecycle: worktree OK path=$wt_abs branch=$branch"
}

assert_finalized() {
  local full_sha head ref_sha upstream ahead behind
  [[ -n "$INTEGRATION_SHA" ]] \
    || die "finalize requires --integration-sha <full-sha>"
  full_sha="$(git -C "$ROOT" rev-parse --verify "${INTEGRATION_SHA}^{commit}" 2>/dev/null)" \
    || die "integration commit not found: $INTEGRATION_SHA"
  [[ "$INTEGRATION_SHA" == "$full_sha" ]] \
    || die "--integration-sha must be a full 40-character SHA"
  head="$(git -C "$ROOT" rev-parse HEAD)"
  [[ "$head" == "$full_sha" ]] \
    || die "primary HEAD=$head does not equal integration SHA=$full_sha"
  [[ -z "$(git -C "$ROOT" status --porcelain --untracked-files=all)" ]] \
    || die "primary worktree is dirty; copied files are not finalized history"

  if [[ -n "$INTEGRATION_REF" ]]; then
    ref_sha="$(git -C "$ROOT" rev-parse --verify "${INTEGRATION_REF}^{commit}" 2>/dev/null)" \
      || die "integration ref not found: $INTEGRATION_REF"
    [[ "$ref_sha" == "$full_sha" ]] \
      || die "integration ref '$INTEGRATION_REF' points to $ref_sha, expected $full_sha"
  fi

  if [[ "$REQUIRE_PUSHED" == yes ]]; then
    upstream="$(git -C "$ROOT" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2>/dev/null)" \
      || die "current branch has no upstream"
    read -r behind ahead < <(
      git -C "$ROOT" rev-list --left-right --count "$upstream...HEAD"
    )
    [[ "$behind" == 0 && "$ahead" == 0 ]] \
      || die "upstream '$upstream' is not exact HEAD (behind=$behind ahead=$ahead)"
  fi
  echo "worktree-lifecycle: finalized integration_sha=$full_sha pushed=$REQUIRE_PUSHED"
}

case "$COMMAND" in
  project-preflight)
    project_common_dir >/dev/null
    assert_git_metadata_writable "$ROOT"
    echo "worktree-lifecycle: project metadata writable root=$ROOT"
    ;;
  worktree-preflight)
    [[ -n "$WORKTREE" ]] || die "worktree-preflight requires --worktree <path>"
    assert_git_metadata_writable "$ROOT"
    assert_registered_worktree "$WORKTREE"
    assert_git_metadata_writable "$WORKTREE"
    ;;
  finalize)
    assert_git_metadata_writable "$ROOT"
    assert_finalized
    ;;
  cleanup-ready)
    [[ -n "$WORKTREE" ]] || die "cleanup-ready requires --worktree <path>"
    assert_git_metadata_writable "$ROOT"
    assert_registered_worktree "$WORKTREE"
    assert_git_metadata_writable "$WORKTREE"
    assert_finalized
    echo "worktree-lifecycle: cleanup allowed; use git worktree remove '$WORKTREE'"
    ;;
  *) die "unknown command '$COMMAND'" ;;
esac
