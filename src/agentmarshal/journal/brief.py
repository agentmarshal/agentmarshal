"""Implementer briefings built from open task contracts."""

from __future__ import annotations

from pathlib import Path

from agentmarshal.journal.contracts import ContractHeader
from agentmarshal.journal.extensions import extension_document_entries
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


def _relative_file(project_root: Path, path: Path) -> str | None:
    """Return a safe project-relative file name, or ``None`` outside the tree."""

    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(project_root.resolve())
    except (OSError, ValueError):
        return None
    return relative.as_posix() if resolved.is_file() else None


def _document_files(project_root: Path, entry: str) -> list[tuple[str, Path]]:
    target = project_root / entry.rstrip("/")
    if entry.endswith("/") and target.is_dir():
        files: list[tuple[str, Path]] = []
        for candidate in sorted(target.rglob("*")):
            relative = _relative_file(project_root, candidate)
            if relative is not None:
                files.append((relative, candidate.resolve()))
        return files
    relative = _relative_file(project_root, target)
    return [(relative, target.resolve())] if relative is not None else []


def _append_named_material(
    brief: str, project_root: Path, contract: ContractHeader
) -> str:
    """Append all decision and document text requested by the contract."""

    sections: list[str] = []
    adr_root = project_root / "docs" / "adr"
    for decision in contract.decisions:
        matches = (
            sorted(
                path
                for path in adr_root.iterdir()
                if path.is_file()
                and path.name.startswith(f"{decision}-")
                and path.suffix == ".md"
            )
            if adr_root.is_dir()
            else []
        )
        if not matches:
            sections.append(
                f"## Named decision: {decision}\n\nMISSING: docs/adr/{decision}-*.md\n"
            )
            continue
        content = [f"## Named decision: {decision}\n"]
        for path in matches:
            relative = path.relative_to(project_root).as_posix()
            text = path.read_text(encoding="utf-8")
            content.append(f"\n### {relative}\n\n{text}")
            if not text.endswith("\n"):
                content.append("\n")
        sections.append("".join(content))

    entries = contract.documents + extension_document_entries(
        project_root, contract.extensions
    )
    seen_files: set[str] = set()
    for entry in entries:
        files = _document_files(project_root, entry)
        if not files:
            sections.append(f"## Named document: {entry}\n\nMISSING: {entry}\n")
            continue
        for relative, path in files:
            if relative in seen_files:
                continue
            seen_files.add(relative)
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # A documents directory can hold anything; a file the brief
                # cannot render is reported, like a missing one, not skipped.
                sections.append(
                    f"## Named document: {relative}\n\n"
                    f"UNREADABLE (not UTF-8): {relative}\n"
                )
                continue
            section = f"## Named document: {relative}\n\n{text}"
            sections.append(section if section.endswith("\n") else section + "\n")
    if not sections:
        return brief
    separator = (
        "" if brief.endswith("\n\n") else "\n" if brief.endswith("\n") else "\n\n"
    )
    return brief + separator + "\n".join(sections)


def build_brief(journal_root: Path, task_id: str) -> str:
    """Build an uncapped implementer briefing for an open task."""

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
    brief = opening + (
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
    return _append_named_material(brief, journal_root.parents[1], task.contract)
