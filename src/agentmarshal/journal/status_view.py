"""The per-task ``status`` view rendered from journal evidence.

Each record type with a dedicated line registers a renderer in
``_RECORD_RENDERERS``; a record type without an entry falls back to the
generic id, type and time line.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import cast

from agentmarshal.journal.status import TaskStatus

#: A renderer takes what the line needs — the project root for the
#: self-acceptance check, the record itself — and returns the line.
RecordRenderer = Callable[[Path, dict[str, object]], str]


def _declared_commit_writers(project_root: Path, commit: str) -> set[str] | None:
    """Return the commit's declared author and committer names and emails.

    ``None`` when git cannot answer — an absent commit, a shallow clone, a
    directory that is not a repository. That is distinct from an answer of "no
    match", and the caller must keep the two apart.
    """

    try:
        result = subprocess.run(
            ["git", "show", "-s", "--format=%an%n%ae%n%cn%n%ce", commit],
            cwd=project_root,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            return None
        output = result.stdout.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    return {line.strip().casefold() for line in output.splitlines() if line.strip()}


def _is_self_accepted(project_root: Path, record: dict[str, object]) -> bool | None:
    """Whether the accepting party wrote the commit, or ``None`` if unknown.

    ADR-0007 calls self-acceptance the case an operator most needs to see. If an
    unanswerable git query were reported as "not self-accepted", the display
    would quietly lose exactly that — so unknown is carried through and said.
    """

    if "accepted_commit" not in record:
        return None
    writers = _declared_commit_writers(project_root, str(record["accepted_commit"]))
    if writers is None:
        return None
    return str(record["accepted_by"]).strip().casefold() in writers


def _render_review_line(_project_root: Path, record: dict[str, object]) -> str:
    findings = cast(list[object], record["findings"])
    advisory = cast(list[object], record.get("advisory_findings", []))
    binding = (
        f"reviewed_finding={record['reviewed_finding']}"
        if "reviewed_finding" in record
        else f"reviewed_commit={str(record['reviewed_commit'])[:7]}"
    )
    artifacts = cast(list[object], record.get("artifacts", []))
    artifact_detail = f" artifacts={len(artifacts)}" if artifacts else ""
    return (
        f"- {record['id']} review {record['created_at']} "
        f"{binding} "
        f"verdict={record['verdict']} findings={len(findings)} "
        f"advisory={len(advisory)}{artifact_detail}"
    )


def _render_acceptance_line(project_root: Path, record: dict[str, object]) -> str:
    findings = cast(list[object], record["findings"])
    checked = _is_self_accepted(project_root, record)
    marker = (
        ""
        if "accepted_finding" in record
        else {
            None: " self-acceptance-unchecked",
            True: " self-accepted",
        }.get(checked, "")
    )
    binding = (
        f"accepted_finding={record['accepted_finding']}"
        if "accepted_finding" in record
        else f"accepted_commit={str(record['accepted_commit'])[:7]}"
    )
    return (
        f"- {record['id']} acceptance {record['created_at']} "
        f"{binding} "
        f"accepted_by={record['accepted_by']} "
        f"findings={','.join(str(finding) for finding in findings)} "
        f"reason={record['reason']}{marker}"
    )


def _render_completed_line(_project_root: Path, record: dict[str, object]) -> str:
    binding = (
        f"completed_finding={record['completed_finding']}"
        if "completed_finding" in record
        else f"completed_commit={str(record['completed_commit'])[:7]}"
    )
    return f"- {record['id']} completed {record['created_at']} {binding}"


def _render_finding_line(_project_root: Path, record: dict[str, object]) -> str:
    artifacts = cast(list[object], record["artifacts"])
    return (
        f"- {record['id']} finding {record['created_at']} "
        f"summary={record['summary']} artifacts={len(artifacts)}"
    )


def _render_abandoned_line(_project_root: Path, record: dict[str, object]) -> str:
    return (
        f"- {record['id']} abandoned {record['created_at']} reason={record['reason']}"
    )


def _render_reopened_line(_project_root: Path, record: dict[str, object]) -> str:
    return f"- {record['id']} reopened {record['created_at']} reason={record['reason']}"


def _render_amendment_line(_project_root: Path, record: dict[str, object]) -> str:
    return (
        f"- {record['id']} amendment {record['created_at']} reason={record['reason']}"
    )


_RECORD_RENDERERS: dict[str, RecordRenderer] = {
    "review": _render_review_line,
    "acceptance": _render_acceptance_line,
    "completed": _render_completed_line,
    "finding": _render_finding_line,
    "abandoned": _render_abandoned_line,
    "reopened": _render_reopened_line,
    "amendment": _render_amendment_line,
}


def print_task_detail(project_root: Path, task: TaskStatus) -> None:
    """Print one task's detail view: header, acceptance trail, scope, records."""

    print(f"ID: {task.task_id}")
    print(f"Status: {task.state}")
    print(f"Title: {task.contract.title}")
    for acceptance in (
        record for record in task.records if record["record_type"] == "acceptance"
    ):
        summary = f"Acceptance: accepted over findings by {acceptance['accepted_by']}"
        self_accepted = _is_self_accepted(project_root, acceptance)
        if "accepted_finding" in acceptance:
            summary += f" (finding {acceptance['accepted_finding']})"
        elif self_accepted is None:
            summary += (
                " (self-acceptance not checked: git cannot read "
                f"{str(acceptance['accepted_commit'])[:7]} here)"
            )
        elif self_accepted:
            summary += (
                " (self-accepted: accepting party is a declared author or committer)"
            )
        print(summary)
    print("Scope:")
    if task.contract.scope:
        for path in task.contract.scope:
            print(f"- {path}")
    else:
        print("- (none)")
    print("Records:")
    for record in task.records:
        renderer = _RECORD_RENDERERS.get(cast(str, record["record_type"]))
        if renderer is None:
            print(f"- {record['id']} {record['record_type']} {record['created_at']}")
        else:
            print(renderer(project_root, record))
