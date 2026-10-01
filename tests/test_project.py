"""Tests for project initialization helpers."""

from __future__ import annotations

from pathlib import Path

from agentmarshal.project import _scaffold_outbox


def test_outbox_readme_excludes_non_evidence_from_journal_staging(
    tmp_path: Path,
) -> None:
    """Task 4.1: the outbox is not evidence and names its staging pathspec."""

    outbox, error = _scaffold_outbox(tmp_path)

    assert error is None
    readme = (outbox / "README.md").read_text(encoding="utf-8")
    assert "not journal evidence" in readme
    assert "git add .agentmarshal/journal" in readme
    assert "git add .agentmarshal ':(exclude).agentmarshal/upstream/**'" in readme, (
        "the pathspec is given as a runnable command: its parentheses need quoting"
    )


def test_outbox_readme_says_how_a_sent_finding_is_matched(tmp_path: Path) -> None:
    """CR-119: the README says how to match a sent finding to its digest."""

    outbox, error = _scaffold_outbox(tmp_path)

    assert error is None
    readme = (outbox / "README.md").read_text(encoding="utf-8")
    assert "sha256" in readme
    assert "Source:" in readme
    assert "Tracking what happened to yours" in readme
