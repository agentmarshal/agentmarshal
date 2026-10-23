"""Resolving a ``--commit`` reference to the commit it names.

The commands that bind a record to a commit — ``accept``'s pause and
operational forms, ``record-ext``, ``record-check`` and ``acknowledge``
— resolve the reference they are given one way:
``git rev-parse --verify <rev>^{commit}``, never through a shell, in
the repository the caller's root names: the journal's own repository in
either placement for the three record writers — a sidecar resolves
against the commits its own repository carries — and, for
``acknowledge``, the scanned repository whose diff it reads. What
resolves is the full 40-character id the record's hex rule already
requires; what does not — a rev the repository does not hold, or one
naming no commit — is refused here rather than reaching a record with
a name it cannot take, the refusal naming the reference and the
repository that was asked.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from agentmarshal.journal.display import escape_for_display


class CommitResolutionError(ValueError):
    """Raised when a ``--commit`` reference does not resolve to a commit."""


def resolve_commit(root: Path, reference: str, *, repository: str) -> str:
    """Resolve *reference* to its full commit id in the repository at *root*.

    ``rev-parse --verify <rev>^{commit}`` answers both halves of the rule
    at once: what resolves is the full id, and what does not — a rev the
    repository does not hold, or one naming no commit — fails here rather
    than reaching the record's hex rule with a name it cannot take.
    *repository* is the caller's phrase for the repository asked — the
    refusal ends on it, each command naming its own ("the journal's
    repository", "the scanned repository").
    """

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{reference}^{{commit}}"],
            cwd=root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise CommitResolutionError(f"cannot run git: {error}") from error
    resolved = result.stdout.decode("utf-8", errors="replace").strip()
    if result.returncode != 0 or len(resolved) != 40:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        message = (
            f"--commit {escape_for_display(reference)} does not resolve to "
            f"a commit in {repository}"
        )
        if detail:
            # git's error text is a value the tool did not write — escaped
            # like every displayed string it does not control.
            message += f": {escape_for_display(detail)}"
        raise CommitResolutionError(message)
    return resolved
