"""Implementer briefings built from open task contracts."""

from __future__ import annotations

from pathlib import Path

from agentmarshal.journal.status import TaskStatusError, load_task_status


def _contract_body(text: str) -> str:
    """Return everything after the contract header without altering it."""

    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines[1:], 1):
        if line.strip() == "+++":
            return "".join(lines[index + 1 :])
    # load_task_status parses the same file before this helper is reached, so a
    # missing delimiter has already produced the more useful contract error.
    raise AssertionError("parsed contract has no closing header delimiter")


def build_brief(journal_root: Path, task_id: str) -> str:
    """Build an implementer briefing for an open task."""

    task = load_task_status(journal_root, task_id)
    if task.state != "open":
        raise TaskStatusError(f"task {task_id} is not open (state: {task.state})")

    contract_path = journal_root / "tasks" / task_id / "contract.md"
    with contract_path.open("r", encoding="utf-8-sig", newline="") as contract_file:
        body = _contract_body(contract_file.read())

    scope = "".join(f"- {path}\n" for path in task.contract.scope) or "- (none)\n"
    acceptance = (
        "".join(f"- {criterion}\n" for criterion in task.contract.acceptance)
        or "- (none)\n"
    )
    return (
        "You are implementing one governed AgentMarshal task.\n\n"
        f"Task id: {task.task_id}\n\n"
        "Declared scope (only these paths may change):\n"
        f"{scope}\n"
        "Acceptance criteria (the definition of done):\n"
        f"{acceptance}\n"
        "Rules enforced by AgentMarshal:\n"
        "- Change only paths declared in the scope above.\n"
        "- Do not edit anything under .agentmarshal/; the journal is not the "
        "implementer's to edit.\n"
        "- Satisfy every acceptance criterion; they are the definition of done.\n\n"
        "Contract body (verbatim):\n"
        f"{body}"
    )
