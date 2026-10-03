"""Capture-policy behaviour for recorded reviewer prose."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import NoReturn

import pytest

import agentmarshal.localstate
from agentmarshal.cli import main
from agentmarshal.journal.capture import CaptureLevel, review_capture_level_from_journal
from agentmarshal.journal.placement import resolve_placement
from agentmarshal.journal.records import read_records
from agentmarshal.localstate import LocalStateError, local_state
from agentmarshal.process_log import read_events
from test_placement import _host_and_sidecar


@pytest.fixture(autouse=True)
def _isolated_temp_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    monkeypatch.setattr(tempfile, "tempdir", None)


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--allow-empty",
        "--quiet",
        "-m",
        "initial",
    )
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Review task"]) == 0
    _git(repo, "add", ".agentmarshal")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "open task",
    )
    return repo, _git(repo, "rev-parse", "HEAD")


def _set_capture(repo: Path, capture: object) -> None:
    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["capture"] = capture
    project_path.write_text(json.dumps(project), encoding="utf-8")


def _reviewer_stub(
    tmp_path: Path,
    output: str,
    marker: Path | None = None,
    error_output: str = "",
) -> Path:
    stub = tmp_path / "reviewer.py"
    marker_write = "" if marker is None else f"Path({str(marker)!r}).touch()\n"
    stub.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "from pathlib import Path\n"
        f"{marker_write}"
        f"sys.stdout.write({output!r})\n"
        f"sys.stderr.write({error_output!r})\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return stub


def _verdict(commit: str) -> str:
    return (
        "AGENTMARSHAL_VERDICT_BEGIN\n"
        f'{{"reviewed_commit": "{commit}", "verdict": "approved", "findings": []}}\n'
        "AGENTMARSHAL_VERDICT_END\n"
    )


def _review_args(commit: str) -> list[str]:
    return [
        "review",
        "--task",
        "CR-001",
        "--commit",
        commit,
        "--base",
        "HEAD~1",
        "--role",
        "reviewer",
        "--vendor",
        "test",
        "--model",
        "test-model",
        "--email",
        "reviewer@test.invalid",
    ]


def _submit_args(prose: Path) -> list[str]:
    return [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        "a" * 40,
        "--verdict",
        "approved",
        "--role",
        "reviewer",
        "--vendor",
        "human",
        "--model",
        "none",
        "--email",
        "reviewer@test.invalid",
        "--prose",
        str(prose),
    ]


def test_review_capture_level_comes_from_the_sidecar_project(tmp_path: Path) -> None:
    """A sidecar's evidence policy is independent of its host's configuration."""

    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    for root, level in ((host, "off"), (sidecar, "commit")):
        project_file = root / ".agentmarshal" / "project.json"
        project_file.parent.mkdir(parents=True)
        project_file.write_text(
            json.dumps({"schema": 1, "capture": {"overrides": {"reviews": level}}}),
            encoding="utf-8",
        )

    assert (
        review_capture_level_from_journal(sidecar / ".agentmarshal" / "journal")
        is CaptureLevel.COMMIT
    )


def _refusing(error: Exception) -> Callable[..., NoReturn]:
    def _raise(*_args: object, **_kwargs: object) -> NoReturn:
        raise error

    return _raise


def _prose_events(repo: Path) -> tuple[list[Path], list[dict[str, object]]]:
    """The kept prose files and their ``review-prose`` events under the log."""

    state = local_state(resolve_placement(repo))
    files_dir = state.log / "files"
    kept = (
        sorted(files_dir.glob("agentmarshal-reviewer-output-*.txt"))
        if files_dir.is_dir()
        else []
    )
    events = [
        event for event in read_events(state) if event.get("event") == "review-prose"
    ]
    return kept, events


def test_by_default_the_prose_stays_out_of_the_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: by default the prose stays out of the journal."""

    repo, commit = _repo(tmp_path, monkeypatch)
    output = "reviewer reasoning\n" + _verdict(commit)
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", str(_reviewer_stub(tmp_path, output))
    )

    assert main(_review_args(commit)) == 0

    record = read_records(repo / ".agentmarshal" / "journal", "CR-001")[-1]
    artifacts = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts"
    message = capsys.readouterr().err
    kept, events = _prose_events(repo)
    assert not artifacts.exists()
    assert "artifacts" not in record
    assert len(kept) == 1
    assert kept[0].read_bytes() == output.encode("utf-8")
    assert str(kept[0]) in message
    assert len(events) == 1
    assert events[0]["task"] == "CR-001"
    assert events[0]["path"] == str(kept[0])
    assert events[0]["sha256"] == hashlib.sha256(output.encode("utf-8")).hexdigest()
    # No temporary copy joined the file under the local state.
    assert list(tmp_path.glob("agentmarshal-reviewer-output-*.txt")) == []


def test_commit_keeps_todays_behaviour(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: commit keeps today's behaviour."""

    repo, commit = _repo(tmp_path, monkeypatch)
    _set_capture(repo, {"overrides": {"reviews": "commit"}})
    output = "reviewer reasoning\n" + _verdict(commit)
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", str(_reviewer_stub(tmp_path, output))
    )

    assert main(_review_args(commit)) == 0

    record = read_records(repo / ".agentmarshal" / "journal", "CR-001")[-1]
    artifacts = record["artifacts"]
    assert isinstance(artifacts, list)
    assert len(artifacts) == 1
    assert "reviewer prose pinned: .agentmarshal/journal/tasks/CR-001/artifacts/" in (
        capsys.readouterr().err
    )


def test_off_keeps_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: off keeps nothing."""

    repo, commit = _repo(tmp_path, monkeypatch)
    _set_capture(repo, {"preset": "minimal"})
    output = "reviewer reasoning\n" + _verdict(commit)
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", str(_reviewer_stub(tmp_path, output))
    )

    assert main(_review_args(commit)) == 0

    record = read_records(repo / ".agentmarshal" / "journal", "CR-001")[-1]
    artifacts = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts"
    assert "artifacts" not in record
    assert not artifacts.exists()
    assert list(tmp_path.glob("agentmarshal-*.txt")) == []
    assert "reviewer prose was not kept (capture level: off)" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("capture", "level"),
    [
        (None, "hash"),
        ({"preset": "minimal"}, "off"),
    ],
)
def test_the_human_path_refuses_prose_it_may_not_keep(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    capture: object | None,
    level: str,
) -> None:
    """Scenario: the human path refuses prose it may not keep."""

    repo, _commit = _repo(tmp_path, monkeypatch)
    if capture is not None:
        _set_capture(repo, capture)
    prose = tmp_path / "review.md"
    prose.write_text("human prose\n", encoding="utf-8")
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    before = sorted(records.iterdir())

    assert main(_submit_args(prose)) == 1

    artifacts = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts"
    message = capsys.readouterr().err
    assert sorted(records.iterdir()) == before
    assert not artifacts.exists()
    assert f"capture level '{level}'" in message
    assert 'capture.overrides.reviews = "commit"' in message


@pytest.mark.parametrize("point", ["name", "create"])
def test_local_state_that_cannot_be_used_falls_back_to_a_temporary_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    point: str,
) -> None:
    """Scenario: local state that cannot be used falls back to a temporary file."""

    repo, commit = _repo(tmp_path, monkeypatch)
    output = "reviewer reasoning\n" + _verdict(commit)
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", str(_reviewer_stub(tmp_path, output))
    )
    if point == "name":
        # git cannot name the common directory.
        monkeypatch.setattr(
            agentmarshal.localstate,
            "local_state",
            _refusing(LocalStateError(f"{repo}: git cannot name a common directory")),
        )
    else:
        # the files directory cannot be created — a file sits in its place.
        files_dir = repo / ".git" / "agentmarshal" / "log" / "files"
        files_dir.parent.mkdir(parents=True)
        files_dir.write_text("in the way\n", encoding="utf-8")
    capsys.readouterr()

    assert main(_review_args(commit)) == 0

    record = read_records(repo / ".agentmarshal" / "journal", "CR-001")[-1]
    message = capsys.readouterr().err
    kept = list(tmp_path.glob("agentmarshal-reviewer-output-*.txt"))
    _kept, events = _prose_events(repo)
    try:
        assert "artifacts" not in record
        assert len(kept) == 1
        assert kept[0].read_bytes() == output.encode("utf-8")
        assert str(kept[0]) in message
        assert "the clone's local state could not be used" in message
        assert events == []
    finally:
        for path in kept:
            path.unlink(missing_ok=True)


def test_a_sidecar_keeps_the_prose_in_the_journal_repositorys_local_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a sidecar keeps the prose in the journal repository's local state."""

    host, sidecar, _base, head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Review task"]) == 0
    output = "reviewer reasoning\n" + _verdict(head)
    diagnostic = "wrapper used a fallback\n"
    stub = _reviewer_stub(tmp_path, output, error_output=diagnostic)
    monkeypatch.setenv("AGENTMARSHAL_REVIEWER_CMD", str(stub))
    capsys.readouterr()

    assert main(_review_args(head)) == 0

    message = capsys.readouterr().err
    state = local_state(resolve_placement(sidecar))
    files = list((state.log / "files").iterdir())
    kept, events = _prose_events(sidecar)
    assert len(kept) == 1
    assert kept[0].read_bytes() == output.encode("utf-8")
    assert str(kept[0]) in message
    assert len(events) == 1
    assert events[0]["task"] == "CR-001"
    diagnostics = [path for path in files if "stderr" in path.name]
    assert len(diagnostics) == 1
    assert diagnostics[0].read_bytes() == diagnostic.encode("utf-8")
    assert [
        event
        for event in read_events(state)
        if event.get("event") == "review-diagnostics"
    ]
    assert not (host / ".git" / "agentmarshal").exists()


def test_a_malformed_capture_section_costs_no_reviewer_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed capture section costs no reviewer run."""

    repo, commit = _repo(tmp_path, monkeypatch)
    _set_capture(repo, [])
    marker = tmp_path / "reviewer-ran"
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD",
        str(_reviewer_stub(tmp_path, _verdict(commit), marker)),
    )

    assert main(_review_args(commit)) == 1

    artifacts = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts"
    assert not marker.exists()
    assert not artifacts.exists()
    assert "project 'capture' section must be an object" in capsys.readouterr().err
