"""Implementer briefings built from open task contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agentmarshal.journal.contracts import ContractHeader
from agentmarshal.journal.extensions import (
    ExtensionManifestError,
    ExtensionManifestMissing,
    read_extension_manifest,
)
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
        resolved.relative_to(project_root.resolve())
        relative = path.absolute().relative_to(project_root.absolute())
    except (OSError, RuntimeError, ValueError):
        return None
    return relative.as_posix() if resolved.is_file() else None


@dataclass(frozen=True)
class _Listed:
    """One entry found under a documents entry, with what the brief can do with it."""

    kind: str  # "file", "linked_directory", "directory" or "unresolvable"
    lexical: str
    path: Path


_LISTED_REASONS = {
    "linked_directory": "LINKED DIRECTORY (not followed; name its target)",
    "directory": "DIRECTORY (name it with a trailing slash)",
    "unresolvable": "UNRESOLVABLE (outside the tree, a broken link, or a cycle)",
}


def _ancestor_unresolvable(path: Path) -> bool:
    """Whether the parent of ``path`` fails to resolve for a reason other than
    absence — a symlink loop, or a link the tree cannot follow."""

    try:
        path.parent.resolve(strict=True)
    except FileNotFoundError:
        return False
    except (OSError, RuntimeError):
        return True
    return False


def _link_kind(project_root: Path, link: Path) -> str:
    """Classify a symlink: a linked directory inside the tree, or unresolvable."""

    try:
        resolved = link.resolve(strict=True)
        resolved.relative_to(project_root.resolve())
    except (OSError, RuntimeError, ValueError):
        return "unresolvable"
    return "linked_directory" if resolved.is_dir() else "file"


def _document_files(project_root: Path, entry: str) -> list[_Listed]:
    """What lies under a documents entry, by lexical path.

    A trailing slash names a directory, as in scope; an entry with one that
    resolves to a file is missing, not a file. A linked directory — as the
    entry or below it — is not followed, so brief and gate agree on what is
    under the entry. Whatever cannot be read is returned with its kind so the
    caller reports it rather than skipping it.
    """

    lexical_target = entry.rstrip("/")
    target = project_root / lexical_target
    if _ancestor_unresolvable(target):
        # ``exists()`` swallows a symlink loop in an ancestor and would report
        # the entry missing; it is unresolvable, and the brief says so.
        return [_Listed("unresolvable", lexical_target, target)]
    if entry.endswith("/"):
        if target.is_symlink():
            kind = _link_kind(project_root, target)
            if kind == "file":
                # A trailing slash names a directory; a file there — linked or
                # not — is missing, not a file.
                return []
            return [_Listed(kind, lexical_target, target)]
        if not target.is_dir():
            return []
        return _files_below(project_root, target)
    if not target.exists() and not target.is_symlink():
        return []
    if target.is_symlink():
        kind = _link_kind(project_root, target)
        if kind != "file":
            return [_Listed(kind, lexical_target, target)]
    if target.is_dir():
        return [_Listed("directory", lexical_target, target)]
    relative = _relative_file(project_root, target)
    kind = "file" if relative is not None else "unresolvable"
    return [_Listed(kind, lexical_target, target)]


def _files_below(project_root: Path, directory: Path) -> list[_Listed]:
    """Walk lexical paths below a directory without following linked directories."""

    files: list[_Listed] = []
    for candidate in sorted(directory.rglob("*")):
        lexical = candidate.relative_to(project_root).as_posix()
        if candidate.is_symlink():
            kind = _link_kind(project_root, candidate)
            if kind != "file":
                files.append(_Listed(kind, lexical, candidate))
                continue
        if candidate.is_dir():
            continue
        relative = _relative_file(project_root, candidate)
        kind = "file" if relative is not None else "unresolvable"
        files.append(_Listed(kind, lexical, candidate))
    return files


def _append_named_material(
    brief: str, material_root: Path, manifest_root: Path, contract: ContractHeader
) -> str:
    """Append all decision and document text requested by the contract.

    ``material_root`` is the governed tree — the host, in a sidecar — where
    decisions and documents live; ``manifest_root`` is the project holding
    the journal, where extension manifests live (ADR-0010).
    """

    sections: list[str] = []
    adr_root = material_root / "docs" / "adr"
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
            lexical = path.relative_to(material_root).as_posix()
            relative = _relative_file(material_root, path)
            if relative is None:
                # A decision file is inlined as the implementer's authority;
                # one that resolves outside the governed tree is not read.
                content.append(
                    f"\n### {lexical}\n\n"
                    f"UNRESOLVABLE (outside the tree or a broken link): {lexical}\n"
                )
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content.append(
                    f"\n### {relative}\n\nUNREADABLE (not UTF-8): {relative}\n"
                )
                continue
            content.append(f"\n### {relative}\n\n{text}")
            if not text.endswith("\n"):
                content.append("\n")
        sections.append("".join(content))

    entries: list[str] = list(contract.documents)
    for name in contract.extensions:
        try:
            entries.extend(read_extension_manifest(manifest_root, name).documents)
        except ExtensionManifestMissing:
            sections.append(
                f"## Named extension: {name}\n\n"
                f"MISSING: .agentmarshal/extensions/{name}.toml\n"
            )
        except ExtensionManifestError as error:
            # Context, not authority: a manifest the brief cannot read is
            # reported here; the gate, which decides, refuses it loudly.
            sections.append(f"## Named extension: {name}\n\nMALFORMED: {error}\n")
    seen_files: set[str] = set()
    for entry in entries:
        files = _document_files(material_root, entry)
        if not files:
            target = material_root / entry.rstrip("/")
            state = "EMPTY" if entry.endswith("/") and target.is_dir() else "MISSING"
            sections.append(f"## Named document: {entry}\n\n{state}: {entry}\n")
            continue
        for listed in files:
            if listed.kind != "file":
                reason = _LISTED_REASONS[listed.kind]
                lexical = listed.lexical
                sections.append(
                    f"## Named document: {lexical}\n\n{reason}: {lexical}\n"
                )
                continue
            relative, path = listed.lexical, listed.path
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


def build_brief(journal_root: Path, task_id: str, host_root: Path | None = None) -> str:
    """Build an uncapped implementer briefing for an open task.

    ``host_root`` is the governed tree whose decisions and documents the brief
    inlines; it defaults to the project holding the journal, which is right
    for the embedded placement and wrong for a sidecar, whose caller passes
    the host.
    """

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
    project_root = journal_root.parents[1]
    return _append_named_material(
        brief, host_root or project_root, project_root, task.contract
    )
