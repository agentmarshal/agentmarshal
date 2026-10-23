#!/bin/sh
# journal-transaction.sh <task-id> <slug> <message-file>
#
# A journal transaction for one task, for adopters whose default branch
# refuses direct commits. Run from a clean checkout of the default branch,
# it:
#
#   - creates a branch named for the task — the gate's job reads the task
#     id from the head reference, so the branch carries the CR-<n> form,
#   - stages .agentmarshal/journal/tasks/<task-id>/ and nothing else — a
#     literal pathspec, so uncommitted records of other tasks in flight
#     never ride this task's transaction,
#   - lists every other changed or untracked path under
#     .agentmarshal/journal/ before committing, and leaves it as it is,
#   - commits with the given message file and pushes the branch to the
#     remote named by AM_REMOTE (default: origin),
#   - prints that a pull request is the next step.
#
# It does NOT open the pull request — that is the provider's verb, marked
# ADAPT below — and it does not wait for checks, merge, or touch anything
# outside the task's own journal directory.
#
# It refuses — staging nothing — when the task id is not of the CR-<n>
# form, the checkout is not on the default branch, or the task's journal
# directory has no change; each refusal names the reason. The script is a
# template: copy it and adapt the copy.

set -eu

die() {
    echo "journal-transaction: $*" >&2
    exit 1
}

task=${1:?usage: journal-transaction.sh <task-id> <slug> <message-file>}
slug=${2:?usage: journal-transaction.sh <task-id> <slug> <message-file>}
msg=${3:?usage: journal-transaction.sh <task-id> <slug> <message-file>}

# The CR-<n> check refuses every exotic id at once: an id that is not the
# letters CR, a dash and digits is never a task the gate can find.
suffix=${task#CR-}
[ "$suffix" != "$task" ] || die "task id is not of the CR-<n> form: $task"
case $suffix in
    '' | *[!0-9]*) die "task id is not of the CR-<n> form: $task" ;;
esac

[ -f "$msg" ] || die "message file does not exist: $msg"
case $msg in
    /*) ;;
    *) msg=$(pwd)/$msg ;;
esac

remote=${AM_REMOTE:-origin}

cd "$(git rev-parse --show-toplevel)"

# The default branch is read from the remote's HEAD — the same place a
# clone leaves it. If it is not set there is no safe guess, so refuse.
remote_head=$(git symbolic-ref --quiet --short "refs/remotes/$remote/HEAD" 2>/dev/null || true)
default_branch=${remote_head#"$remote"/}
[ -n "$default_branch" ] || die "cannot determine the default branch of remote '$remote'; set it with: git remote set-head $remote --auto"

current=$(git branch --show-current)
[ "$current" = "$default_branch" ] || die "not on the default branch: on '${current:-<detached HEAD>}', want '$default_branch'"

task_dir=".agentmarshal/journal/tasks/$task"
[ -d "$task_dir" ] || die "task $task has no journal directory: $task_dir"
git status --porcelain=v1 -uall -- "$task_dir" | grep -q . || die "nothing to commit: no change under $task_dir"

# Report — do not take — everything else under the journal. Another
# task's uncommitted records stay for that task's own transaction.
others=$(git status --porcelain=v1 -uall -- .agentmarshal/journal/ | grep -v "tasks/$task/" || true)
if [ -n "$others" ]; then
    echo "journal-transaction: not taken, left as it is under .agentmarshal/journal/:"
    echo "$others"
fi

branch="journal/$task-$slug"
git switch -c "$branch"
git add -- "$task_dir"
# A pathspec commit records only the task's directory even if the index
# already held a foreign record staged by hand; `git commit <paths>`
# needs the paths in the index, which the `git add` above did.
git commit -F "$msg" -- "$task_dir"
git push --set-upstream "$remote" "$branch"

echo "journal-transaction: $task committed on $branch and pushed to $remote."
echo "Next step: open a pull request from $branch into $default_branch — the"
echo "gate check on that branch is what decides the merge. Open it with your"
echo "provider's tooling:"
# ADAPT — the provider-specific pull-request command goes here, e.g.:
#   gh pr create --base "$default_branch" --head "$branch" --fill
