"""The merge gate: verifies a candidate against contract, review and attestation.

The gate reads trusted inputs from the base side of the candidate range
(the contract comes from the merge-base tree, so a candidate cannot
widen its own scope) and evidence from the journal records of the
invoking checkout, per ADR-0001/0003/0004. Review records are written by
the launcher into the journal working tree and stay uncommitted until
the completion transaction — a review therefore never has to be part of
the very diff it attests. Record provenance and CI wiring are later
slices; running the gate on a trusted checkout is the operator's
responsibility in this slice.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.contracts import parse_contract_text
from agentmarshal.journal.records import read_records
from agentmarshal.journal.status import TaskStatusError, load_task_status

_JOURNAL_PREFIX = ".agentmarshal/journal/"


class GateError(Exception):
    """Raised when the gate cannot evaluate a candidate at all."""


@dataclass(frozen=True)
class GateReport:
    """The outcome of a gate evaluation."""

    passed: bool
    lines: list[str]


def _run_git(project_root: Path, arguments: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
    except OSError as error:
        raise GateError(f"cannot run git: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise GateError(f"git {' '.join(arguments)} failed: {detail}")
    return result.stdout


def _resolve_commit(project_root: Path, reference: str) -> str:
    resolved = _run_git(
        project_root, ["rev-parse", "--verify", f"{reference}^{{commit}}"]
    ).strip()
    if len(resolved) != 40:
        raise GateError(f"reference did not resolve to a full SHA: {reference}")
    return resolved


def _changed_paths(project_root: Path, merge_base: str, commit: str) -> list[str]:
    output = _run_git(
        project_root, ["diff", "--name-only", "-z", f"{merge_base}..{commit}"]
    )
    return [path for path in output.split("\0") if path]


def _added_paths(project_root: Path, merge_base: str, commit: str) -> list[str]:
    output = _run_git(
        project_root,
        ["diff", "--name-only", "--diff-filter=A", "-z", f"{merge_base}..{commit}"],
    )
    return [path for path in output.split("\0") if path]


def _range_emails(project_root: Path, merge_base: str, commit: str) -> set[str]:
    output = _run_git(
        project_root, ["log", "--format=%ae%n%ce", f"{merge_base}..{commit}"]
    )
    return {line.strip() for line in output.splitlines() if line.strip()}


def _scope_covers(scope: tuple[str, ...], task_id: str, path: str) -> bool:
    if path.startswith(f"{_JOURNAL_PREFIX}tasks/{task_id}/"):
        return True  # a task's own journal area is implicitly in scope
    for entry in scope:
        if entry.endswith("/"):
            if path == entry.rstrip("/") or path.startswith(entry):
                return True
        elif path == entry:
            return True
    return False


def run_gate(
    project_root: Path,
    task_id: str,
    commit: str,
    base: str,
    pipeline_sha: str | None,
) -> GateReport:
    """Evaluate a merge candidate; fail closed on every violation."""

    lines: list[str] = []
    violations = 0

    def check(passed: bool, message: str) -> None:
        nonlocal violations
        if passed:
            lines.append(f"PASS: {message}")
        else:
            violations += 1
            lines.append(f"FAIL: {message}")

    journal_root = project_root / ".agentmarshal" / "journal"
    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise GateError(str(error)) from error
    check(
        task.state == "open",
        f"task {task_id} is open (state: {task.state})",
    )

    resolved_commit = _resolve_commit(project_root, commit)
    base_commit = _resolve_commit(project_root, base)
    merge_base = _run_git(
        project_root, ["merge-base", base_commit, resolved_commit]
    ).strip()
    changed = _changed_paths(project_root, merge_base, resolved_commit)
    if not changed:
        raise GateError("candidate range contains no changes")

    journal_only = all(path.startswith(_JOURNAL_PREFIX) for path in changed)
    if journal_only:
        lines.append(
            "PASS: journal-only transaction (deterministic lane; review not required)"
        )
    else:
        # The contract is read from the merge-base tree: the trusted
        # side, so the candidate cannot widen its own scope.
        contract_path = f"{_JOURNAL_PREFIX}tasks/{task_id}/contract.md"
        try:
            contract_text = _run_git(
                project_root, ["show", f"{merge_base}:{contract_path}"]
            )
        except GateError:
            raise GateError(
                f"contract for {task_id} is not present in the base tree; "
                "the opening transaction must merge before implementation"
            ) from None
        contract = parse_contract_text(contract_text, contract_path)
        outside = [
            path for path in changed if not _scope_covers(contract.scope, task_id, path)
        ]
        check(
            not outside,
            "diff within contract scope"
            if not outside
            else f"paths outside contract scope: {', '.join(sorted(outside))}",
        )

        reviews = [
            record
            for record in read_records(journal_root, task_id)
            if record.get("record_type") == "review"
            and record.get("reviewed_commit") == resolved_commit
        ]
        latest = reviews[-1] if reviews else None
        check(
            latest is not None and latest.get("verdict") == "approved",
            f"latest review of {resolved_commit[:12]} is approved"
            if latest is not None
            else f"no review record for {resolved_commit[:12]}",
        )

        if latest is not None:
            reviewer = latest.get("reviewer")
            reviewer_email = (
                reviewer.get("email") if isinstance(reviewer, dict) else None
            )
            writer_emails = _range_emails(project_root, merge_base, resolved_commit)
            check(
                isinstance(reviewer_email, str)
                and bool(reviewer_email)
                and reviewer_email not in writer_emails,
                "reviewer is independent of the candidate's writers",
            )

    attested = pipeline_sha is not None and pipeline_sha == resolved_commit
    check(
        attested,
        f"pipeline attested for {resolved_commit[:12]}"
        if attested
        else "pipeline attestation missing or for a different commit",
    )

    # Collisions are checked against the merge target's tip: a record
    # path independently created on both sides would collide at merge.
    base_tree = set(
        _run_git(
            project_root, ["ls-tree", "-r", "--name-only", base_commit]
        ).splitlines()
    )
    colliding = [
        path
        for path in _added_paths(project_root, merge_base, resolved_commit)
        if path.startswith(_JOURNAL_PREFIX)
        and "/records/" in path
        and path in base_tree
    ]
    check(
        not colliding,
        "no record-path collisions with the base tree"
        if not colliding
        else f"record paths already exist on the base: {', '.join(sorted(colliding))}",
    )

    return GateReport(passed=violations == 0, lines=lines)
