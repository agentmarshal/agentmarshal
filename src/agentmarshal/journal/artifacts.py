"""Exclusive writes for hash-pinned journal artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path

from agentmarshal.journal.records import (
    JournalRecordError,
    _prepare_record_directory,
    _reject_control_characters,
)
from agentmarshal.project import UnsafeProjectPathError, _create_exclusive


def _prepare_artifact_directory(journal_root: Path, task_id: str) -> Path:
    """Create and return a task's real, non-symlinked artifact directory."""

    records_directory = _prepare_record_directory(journal_root, task_id)
    artifacts_directory = records_directory.parent / "artifacts"
    if artifacts_directory.is_symlink():
        raise JournalRecordError(
            f"refusing to write through a symlink: {artifacts_directory}"
        )
    if artifacts_directory.exists() and not artifacts_directory.is_dir():
        raise JournalRecordError(
            f"artifact path is not a directory: {artifacts_directory}"
        )
    artifacts_directory.mkdir(exist_ok=True)
    resolved_directory = artifacts_directory.resolve()
    if resolved_directory != artifacts_directory:
        raise JournalRecordError(
            "artifact directory resolves outside its expected location: "
            f"{artifacts_directory} -> {resolved_directory}"
        )
    return artifacts_directory


def write_artifact(
    journal_root: Path, task_id: str, name: str, content: bytes
) -> dict[str, str]:
    """Exclusively write exact artifact bytes and return their journal pin."""

    _reject_control_characters(name, "artifact name")
    if not name or Path(name).name != name or name in {".", ".."}:
        raise JournalRecordError("artifact name must be a single path component")
    directory = _prepare_artifact_directory(journal_root, task_id)
    path = directory / name
    try:
        artifact_file = _create_exclusive(path)
    except UnsafeProjectPathError as error:
        raise JournalRecordError(str(error)) from error
    with artifact_file:
        artifact_file.buffer.write(content)
    reference = Path(".agentmarshal/journal/tasks") / task_id / "artifacts" / name
    return {"ref": reference.as_posix(), "hash": hashlib.sha256(content).hexdigest()}
