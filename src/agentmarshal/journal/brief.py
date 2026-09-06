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

    # An empty scope is not the absence of a restriction, it is the strictest
    # one: the gate matches every changed path against the entries, so with no
    # entries every path is outside scope. A dash under "only these paths may
    # change" would read as "no limits", which is the opposite of what happens.
    if task.contract.scope:
        scope_section = "Declared scope (only these paths may change):\n" + "".join(
            f"- {path}\n" for path in task.contract.scope
        )
    else:
        scope_section = (
            "Declared scope: empty. This task lands through findings, not a diff.\n"
            "Because its scope is empty, no file may land through the diff lane.\n"
            "A finding must carry a non-empty summary and at least one artifact\n"
            "pinned by reference and sha256 hash.\n"
        )
    acceptance = (
        "".join(f"- {criterion}\n" for criterion in task.contract.acceptance)
        or "- (none)\n"
    )
    opening = (
        "You are implementing one governed AgentMarshal task.\n\n"
        if task.contract.scope
        else "You are working on one governed AgentMarshal research task.\n\n"
    )
    return opening + (
        f"Task id: {task.task_id}\n\n"
        f"{scope_section}\n"
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
