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
from agentmarshal.journal.records import (
    JournalRecordError,
    read_records,
    validate_record_content,
)
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


def _changed_with_status(
    project_root: Path, merge_base: str, commit: str
) -> list[tuple[str, str]]:
    """Return (status, path) pairs for the range.

    A rename decomposes into a deletion of its source and an addition of
    its destination, so moving a file out of a protected location is
    seen as removing it there; a copy contributes only the addition.
    """

    output = _run_git(
        project_root, ["diff", "--name-status", "-z", f"{merge_base}..{commit}"]
    )
    tokens = [token for token in output.split("\0") if token]
    pairs: list[tuple[str, str]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        if status[0] in "RC":
            if index + 2 >= len(tokens):
                raise GateError("unparseable rename entry in candidate diff")
            if status[0] == "R":
                pairs.append(("D", tokens[index + 1]))
            pairs.append(("A", tokens[index + 2]))
            index += 3
        else:
            if index + 1 >= len(tokens):
                raise GateError("unparseable entry in candidate diff")
            pairs.append((status[0], tokens[index + 1]))
            index += 2
    return pairs


def _is_record_path(path: str) -> bool:
    return path.startswith(_JOURNAL_PREFIX) and "/records/" in path


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
            # Identity comparison is case-insensitive: the reviewer
            # controls its own identity string and must not evade the
            # check through casing.
            normalized_reviewer = (
                reviewer_email.strip().casefold()
                if isinstance(reviewer_email, str)
                else ""
            )
            writer_emails = {
                email.strip().casefold()
                for email in _range_emails(project_root, merge_base, resolved_commit)
            }
            check(
                bool(normalized_reviewer)
                and normalized_reviewer not in writer_emails,
                "reviewer is independent of the candidate's writers",
            )

    attested = pipeline_sha is not None and pipeline_sha == resolved_commit
    check(
        attested,
        f"pipeline attested for {resolved_commit[:12]}"
        if attested
        else "pipeline attestation missing or for a different commit",
    )

    # Evidence records are append-only for every candidate: any
    # modification, deletion or rename of an existing record rewrites
    # history at the merge boundary and is refused (ADR-0004).
    record_changes = [
        (status, path)
        for status, path in _changed_with_status(
            project_root, merge_base, resolved_commit
        )
        if _is_record_path(path)
    ]
    tampered = sorted(path for status, path in record_changes if status != "A")
    check(
        not tampered,
        "evidence records are append-only"
        if not tampered
        else "append-only violation, records modified, deleted or renamed: "
        + ", ".join(tampered),
    )

    added_records = [path for status, path in record_changes if status == "A"]
    invalid: list[str] = []
    for path in added_records:
        try:
            content = _run_git(project_root, ["show", f"{resolved_commit}:{path}"])
            record = validate_record_content(Path(path).name, content)
        except (GateError, JournalRecordError) as error:
            invalid.append(f"{path}: {error}")
            continue
        expected_task = path.removeprefix(f"{_JOURNAL_PREFIX}tasks/").split("/", 1)[0]
        if record.get("task") != expected_task:
            invalid.append(f"{path}: record task does not match its directory")
    check(
        not invalid,
        "added records are valid"
        if not invalid
        else f"invalid added records: {'; '.join(sorted(invalid))}",
    )

    # Collisions are checked against the merge target's tip: a record
    # path independently created on both sides would collide at merge.
    base_tree = set(
        _run_git(
            project_root, ["ls-tree", "-r", "--name-only", base_commit]
        ).splitlines()
    )
    colliding = [path for path in added_records if path in base_tree]
    check(
        not colliding,
        "no record-path collisions with the base tree"
        if not colliding
        else f"record paths already exist on the base: {', '.join(sorted(colliding))}",
    )

    return GateReport(passed=violations == 0, lines=lines)
