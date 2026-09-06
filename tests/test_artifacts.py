"""Tests for durable, hash-pinned journal artifacts."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from agentmarshal.journal.artifacts import write_artifact
from agentmarshal.journal.records import JournalRecordError


def test_write_artifact_is_exclusive_and_returns_sha256(tmp_path: Path) -> None:
    journal = tmp_path / ".agentmarshal" / "journal"
    journal.parent.mkdir()
    content = b"review prose\nwith exact bytes\x00"

    pin = write_artifact(journal, "CR-001", "review.md", content)

    path = journal / "tasks" / "CR-001" / "artifacts" / "review.md"
    assert path.read_bytes() == content
    assert pin == {
        "ref": ".agentmarshal/journal/tasks/CR-001/artifacts/review.md",
        "hash": hashlib.sha256(content).hexdigest(),
    }
    with pytest.raises(FileExistsError):
        write_artifact(journal, "CR-001", "review.md", b"replacement")
    assert path.read_bytes() == content


def test_write_artifact_validates_the_task_id_as_it_validates_the_name(
    tmp_path: Path,
) -> None:
    journal = tmp_path / ".agentmarshal" / "journal"
    journal.parent.mkdir()

    with pytest.raises(JournalRecordError, match="task id"):
        write_artifact(journal, "../escape", "review.md", b"x")
    assert not (tmp_path / "escape").exists()
