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

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.capture import (
    CaptureError,
    private_markers_from_project,
    scan_diff_for_leaks,
)
from agentmarshal.journal.contracts import JournalContractError, parse_contract_text
from agentmarshal.journal.records import (
    JournalRecordError,
    read_records,
    validate_record_content,
)
from agentmarshal.journal.status import TaskStatusError, load_task_status

_JOURNAL_PREFIX = ".agentmarshal/journal/"
_PROJECT_FILE = ".agentmarshal/project.json"


class GateError(Exception):
    """Raised when the gate cannot evaluate a candidate at all."""


@dataclass(frozen=True)
class GateReport:
    """The outcome of a gate evaluation."""

    passed: bool
    lines: list[str]
    resolved_commit: str


def _run_git(project_root: Path, arguments: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *arguments],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise GateError(f"cannot run git: {error}") from error
    try:
        stdout = result.stdout.decode("utf-8")
        stderr = result.stderr.decode("utf-8")
    except UnicodeDecodeError as error:
        # git permits arbitrary non-NUL bytes in path names; a non-UTF-8
        # path is a controlled refusal, never a traceback.
        raise GateError(f"git produced non-UTF-8 output: {error}") from error
    if result.returncode != 0:
        detail = stderr.strip() or stdout.strip()
        raise GateError(f"git {' '.join(arguments)} failed: {detail}")
    return stdout


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


def _scope_covers(scope: tuple[str, ...], path: str) -> bool:
    for entry in scope:
        if entry.endswith("/"):
            if path == entry.rstrip("/") or path.startswith(entry):
                return True
        elif path == entry:
            return True
    return False


def markers_from_tree(project_root: Path, tree_ref: str) -> tuple[str, ...]:
    """Read ``leak_scan.private_markers`` from ``project.json`` at a git tree.

    The config is read from a **trusted** tree (the merge base), never the
    candidate working tree, so a candidate cannot weaken its own leak-scan by
    editing ``project.json`` in the very change being scanned — the same
    reason the contract is read from the base side.

    A tree that genuinely has no ``project.json`` yields no markers (the scan
    still runs its built-in secret signatures). That is distinguished from a
    real failure — an unknown ref, or a ``git show`` error on a file that
    does exist — which propagates as :class:`GateError` so the caller can
    surface a visible skip warning instead of silently dropping configured
    markers. A malformed config likewise raises (``ValueError`` /
    :class:`CaptureError`).
    """

    # `ls-tree` distinguishes an absent path (empty output, exit 0) from a
    # bad ref (non-zero -> GateError); only genuine absence returns no markers.
    listing = _run_git(
        project_root, ["ls-tree", "--name-only", tree_ref, "--", _PROJECT_FILE]
    )
    if not listing.strip():
        return ()
    project_json = _run_git(project_root, ["show", f"{tree_ref}:{_PROJECT_FILE}"])
    data = json.loads(project_json.lstrip("\ufeff"))
    if not isinstance(data, dict):
        raise ValueError("project.json is not a JSON object")
    return private_markers_from_project(data)


ATTESTATION_MODES = ("commit", "ci-required")


def run_gate(
    project_root: Path,
    task_id: str,
    commit: str,
    base: str,
    pipeline_sha: str | None,
    attestation: str = "commit",
) -> GateReport:
    """Evaluate a merge candidate; fail closed on every violation.

    ``attestation`` selects how the pipeline-attestation check is
    satisfied. ``commit`` (the default, Variant 1) requires
    ``pipeline_sha`` to equal the candidate commit — the invoker attests a
    green pipeline. ``ci-required`` (Variant 2) delegates attestation to
    the provider's required checks: the gate runs as one required check
    and the provider blocks the merge until the test check is also green,
    so the gate does not self-attest. It is only sound when the provider
    independently requires the test check for merge.
    """

    if attestation not in ATTESTATION_MODES:
        raise GateError(
            f"unknown attestation mode: {attestation!r} "
            f"(expected one of {', '.join(ATTESTATION_MODES)})"
        )

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
    # load_task_status validates that the post-candidate journal is
    # well-formed (single opened record, no record after a terminal one,
    # contract id matches); it raises on an inconsistent projection.
    try:
        task = load_task_status(journal_root, task_id)
    except (OSError, TaskStatusError, ValueError) as error:
        raise GateError(str(error)) from error

    resolved_commit = _resolve_commit(project_root, commit)
    base_commit = _resolve_commit(project_root, base)
    merge_base = _run_git(
        project_root, ["merge-base", base_commit, resolved_commit]
    ).strip()
    changed = _changed_paths(project_root, merge_base, resolved_commit)
    if not changed:
        raise GateError("candidate range contains no changes")

    base_tree = set(
        _run_git(
            project_root, ["ls-tree", "-r", "--name-only", base_commit]
        ).splitlines()
    )

    # The candidate's per-path change statuses drive both the measurements
    # lane below and the append-only / validity checks later; compute them
    # once here. A rename decomposes into a deletion plus an addition, so a
    # move is never seen as a pure addition.
    changes_with_status = _changed_with_status(
        project_root, merge_base, resolved_commit
    )
    record_changes = [
        (status, path) for status, path in changes_with_status if _is_record_path(path)
    ]
    added_records = [path for status, path in record_changes if status == "A"]
    journal_only = all(path.startswith(_JOURNAL_PREFIX) for path in changed)

    # "Open" is decided from the base tree, never the candidate: opening,
    # implementation and completion candidates all merge onto a task that
    # is not yet closed there, so a legitimate open->terminal completion
    # passes while work merged onto an already-closed task is refused.
    task_records_prefix = f"{_JOURNAL_PREFIX}tasks/{task_id}/records/"
    task_dir_prefix = f"{_JOURNAL_PREFIX}tasks/{task_id}/"
    closed_at_base = any(
        path.startswith(task_records_prefix)
        and (path.endswith("-completed.json") or path.endswith("-abandoned.json"))
        for path in base_tree
    )
    # A task closed at base still admits measurements, but only a strictly
    # additive candidate confined to this task's own journal subtree that
    # adds at least one session record and no non-session record: economics
    # (and new supplementary artifacts) accrue after the terminal record
    # (ADR-0005 Decision 3) without mutating the lifecycle or any existing
    # file, and without touching any other task. Every change must be an
    # addition — a modification or deletion (of contract.md, an existing
    # artifact, anything) fails the lane, so appended evidence can never
    # authorize a mutation of a closed task. Anything else remains refused
    # by the base-state check.
    measurements_only = (
        bool(added_records)
        and all(
            status == "A" and path.startswith(task_dir_prefix)
            for status, path in changes_with_status
        )
        and all(
            path.startswith(task_records_prefix) and path.endswith("-session.json")
            for path in added_records
        )
    )
    if not closed_at_base:
        lines.append(f"PASS: task {task_id} is not closed at base")
    elif measurements_only:
        lines.append(
            "PASS: measurements-only append to a task closed at base "
            "(session records accrue post-terminal)"
        )
    else:
        check(
            False,
            f"task {task_id} is already closed at base (candidate state: {task.state})",
        )

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
        try:
            contract = parse_contract_text(contract_text, contract_path)
        except JournalContractError as error:
            raise GateError(f"contract in the base tree is invalid: {error}") from error
        outside = [path for path in changed if not _scope_covers(contract.scope, path)]
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
                bool(normalized_reviewer) and normalized_reviewer not in writer_emails,
                "reviewer is independent of the candidate's writers",
            )

    if attestation == "ci-required":
        lines.append(
            "PASS: pipeline attestation delegated to the provider's required "
            "checks (the test check must also be required for merge)"
        )
    else:
        attested = pipeline_sha is not None and pipeline_sha == resolved_commit
        check(
            attested,
            f"pipeline attested for {resolved_commit[:12]}"
            if attested
            else "pipeline attestation missing or for a different commit",
        )

    # Evidence records are append-only for every candidate: any
    # modification, deletion or rename of an existing record rewrites
    # history at the merge boundary and is refused (ADR-0004). The record
    # changes were computed once above for the measurements lane.
    tampered = sorted(path for status, path in record_changes if status != "A")
    check(
        not tampered,
        "evidence records are append-only"
        if not tampered
        else "append-only violation, records modified, deleted or renamed: "
        + ", ".join(tampered),
    )

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
    colliding = [path for path in added_records if path in base_tree]
    check(
        not colliding,
        "no record-path collisions with the base tree"
        if not colliding
        else f"record paths already exist on the base: {', '.join(sorted(colliding))}",
    )

    # A single record is valid in isolation yet corrupts the lifecycle
    # projection in aggregate — a second 'opened' record makes the task
    # unreadable after merge. Reject a task ending up with more than one
    # opened record across the target tip and the candidate's additions.
    def _task_of(path: str) -> str:
        return path.removeprefix(f"{_JOURNAL_PREFIX}tasks/").split("/", 1)[0]

    duplicate_opened: set[str] = set()
    affected_tasks = {_task_of(path) for path in added_records}
    for affected in affected_tasks:
        prefix = f"{_JOURNAL_PREFIX}tasks/{affected}/records/"
        opened_paths = {
            path
            for path in base_tree
            if path.startswith(prefix) and path.endswith("-opened.json")
        }
        opened_paths.update(
            path
            for path in added_records
            if path.startswith(prefix) and path.endswith("-opened.json")
        )
        if len(opened_paths) > 1:
            duplicate_opened.add(affected)
    check(
        not duplicate_opened,
        "task lifecycle records are consistent"
        if not duplicate_opened
        else "multiple opened records after merge for: "
        + ", ".join(sorted(duplicate_opened)),
    )

    # Advisory leak-scan (ADR-0005, CR-041): best-effort and never
    # fail-closed. The scanner is heuristic — a clean result is not proof of
    # safety and a hit is not proof of a leak — so it warns but does not
    # block, and it never touches `violations`. Marker config is read from
    # the merge-base tree (the trusted side), so a candidate cannot weaken
    # its own scan; a malformed config or a git failure degrades to a warning
    # rather than refusing every merge. Only the candidate's added lines are
    # scanned, so accepted historical residuals already in the tree are not
    # re-flagged.
    try:
        markers = markers_from_tree(project_root, merge_base)
        diff_text = _run_git(project_root, ["diff", f"{merge_base}..{resolved_commit}"])
        leak_hits = scan_diff_for_leaks(diff_text, markers)
    except (ValueError, CaptureError, GateError) as error:
        lines.append(f"WARN: leak-scan skipped ({error})")
    else:
        if leak_hits:
            lines.append(
                "WARN: possible leak in candidate additions "
                f"(advisory, not blocking): {', '.join(leak_hits)}"
            )

    return GateReport(
        passed=violations == 0, lines=lines, resolved_commit=resolved_commit
    )
