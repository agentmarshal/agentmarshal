"""`agentmarshal record-check` — a pipeline's verdict on a commit.

ADR-0017 decision 1 / ADR-0022 sections 3 and 7: what a pipeline check
found on a commit is evidence — the `check` record CR-167 landed —
while the full output goes to the process log as a `check-output`
event. The command resolves `--commit` to its full id in the journal's
repository, keeps the output file in local state, and masks the
record's excerpt rather than refusing it.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.localstate import LocalState
from agentmarshal.process_log import read_events


@pytest.fixture(autouse=True)
def _isolated_actor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _local_state(repo: Path) -> LocalState:
    return LocalState(repo / ".git" / "agentmarshal")


def _repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    markers: tuple[str, ...] = (),
    actors: dict[str, Any] | None = None,
) -> Path:
    """A git root with project.json and one commit — the embedded floor."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    agentmarshal = repo / ".agentmarshal"
    agentmarshal.mkdir()
    project: dict[str, Any] = {"task": {"name": "agentmarshal"}}
    if markers:
        project["leak_scan"] = {"private_markers": list(markers)}
    if actors:
        project["actors"] = actors
    (agentmarshal / "project.json").write_text(
        json.dumps(project) + "\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "initial",
    )
    monkeypatch.chdir(repo)
    return repo


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD")


def _open() -> None:
    from agentmarshal.cli import main

    assert main(["open", "--title", "Task"]) == 0


def _record_check(*extra: str, task: str = "CR-001") -> int:
    from agentmarshal.cli import main

    return main(["record-check", "--task", task, *extra])


def _records(repo: Path, task: str = "CR-001") -> list[dict[str, Any]]:
    records = sorted((_journal(repo) / "tasks" / task / "records").glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in records]


def _checks(repo: Path, task: str = "CR-001") -> list[dict[str, Any]]:
    return [r for r in _records(repo, task) if r["record_type"] == "check"]


def _events(repo: Path) -> list[dict[str, Any]]:
    return [
        event
        for event in read_events(_local_state(repo))
        if event.get("event") == "check-output"
    ]


def _kept_files(repo: Path) -> list[Path]:
    files = _local_state(repo).log / "files"
    return list(files.glob("*.txt")) if files.is_dir() else []


def _snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _tree(repo: Path) -> dict[str, bytes]:
    """The journal plus the local state — everything the command may touch."""

    snapshot = {
        f"journal/{name}": content
        for name, content in _snapshot(_journal(repo)).items()
    }
    state = _local_state(repo).root
    snapshot.update(
        {f"local-state/{name}": content for name, content in _snapshot(state).items()}
    )
    return snapshot


# -- a verdict is recorded at the resolved commit -------------------------------


def test_a_verdict_is_recorded_at_the_resolved_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a verdict is recorded at the resolved commit.

    One `check` record at schema 7 carrying the full 40-hex commit id,
    the name and the result; stdout prints the record's path, the
    commit, the name, the result and the recorder.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    head = _head(repo)
    capsys.readouterr()

    assert (
        _record_check("--commit", "HEAD", "--name", "unit-tests", "--result", "failed")
        == 0
    )

    checks = _checks(repo)
    assert len(checks) == 1
    record = checks[0]
    assert record["schema"] == 7
    assert record["commit"] == head
    assert record["name"] == "unit-tests"
    assert record["result"] == "failed"
    assert record["recorded_by"] == "ci-runner"
    assert record["recorded_by_source"] == "override"
    out = capsys.readouterr().out
    assert head in out
    assert "unit-tests" in out
    assert "failed" in out
    assert "ci-runner" in out
    # The record path the command prints is the record that landed.
    printed_path = Path(out.splitlines()[0])
    assert printed_path.exists()
    assert json.loads(printed_path.read_text(encoding="utf-8")) == record


def test_a_short_or_symbolic_commit_resolves_to_the_full_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a short or symbolic commit resolves to the full id.

    `--commit` takes what rev-parse takes — a short id, a branch name —
    and the record carries the full 40-hex id it resolves to.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    head = _head(repo)

    assert (
        _record_check("--commit", head[:8], "--name", "build", "--result", "passed")
        == 0
    )
    assert _checks(repo)[0]["commit"] == head

    assert (
        _record_check("--commit", "HEAD", "--name", "build", "--result", "passed") == 0
    )
    assert _checks(repo)[1]["commit"] == head


def test_the_optional_fields_land_on_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the optional fields land on the record.

    `--failed-step` and `--run-url` land as `failed_step` and `run_url`;
    without them neither field appears.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "e2e",
            "--result",
            "error",
            "--failed-step",
            "deploy",
            "--run-url",
            "https://ci.example/run/9",
        )
        == 0
    )
    record = _checks(repo)[0]
    assert record["failed_step"] == "deploy"
    assert record["run_url"] == "https://ci.example/run/9"

    assert _record_check("--commit", "HEAD", "--name", "e2e", "--result", "passed") == 0
    bare = _checks(repo)[1]
    for field in ("failed_step", "excerpt", "run_url"):
        assert field not in bare


def test_a_result_outside_the_vocabulary_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a result outside the vocabulary is refused writing nothing.

    The vocabulary is the record family's own; argparse refuses before
    the command runs.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    before = _tree(repo)
    with pytest.raises(SystemExit) as exited:
        _record_check("--commit", "HEAD", "--name", "build", "--result", "success")
    assert exited.value.code != 0
    assert _tree(repo) == before


def test_a_commit_that_does_not_resolve_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a commit that does not resolve is refused writing nothing."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    before = _tree(repo)
    capsys.readouterr()

    assert (
        _record_check(
            "--commit", "deadbeef" * 5, "--name", "build", "--result", "passed"
        )
        == 1
    )
    err = capsys.readouterr().err
    assert "--commit" in err
    assert "deadbeef" in err
    assert _tree(repo) == before


def test_an_unknown_task_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unknown task is refused writing nothing."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    before = _tree(repo)
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "build",
            "--result",
            "passed",
            task="CR-099",
        )
        == 1
    )
    assert "unknown task" in capsys.readouterr().err
    assert _tree(repo) == before
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


@pytest.mark.parametrize("terminal", ["completed", "abandoned"])
def test_a_terminal_task_accepts_the_record(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    terminal: str,
) -> None:
    """Scenarios: a completed task accepts the record; an abandoned task
    accepts the record.

    `check` is the measurement admitted after a terminal record — it
    lands and the projection is unchanged.
    """

    from agentmarshal.journal.records import (
        create_abandoned_record,
        create_completed_record,
        write_record,
    )
    from agentmarshal.journal.status import load_task_status

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    if terminal == "completed":
        record = create_completed_record("CR-001", "test", _head(repo))
    else:
        record = create_abandoned_record("CR-001", "test", "Superseded")
    write_record(_journal(repo), "CR-001", record)
    capsys.readouterr()

    assert (
        _record_check("--commit", "HEAD", "--name", "late-ci", "--result", "failed")
        == 0
    )
    checks = _checks(repo)
    assert len(checks) == 1
    assert checks[0]["name"] == "late-ci"
    assert load_task_status(_journal(repo), "CR-001").state == (
        "done" if terminal == "completed" else "abandoned"
    )
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


# -- the kept output and the check-output event ---------------------------------


def test_an_output_file_is_kept_and_a_check_output_event_announces_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an output file is kept and a check-output event announces it.

    The file's full bytes land under the journal repository's local
    state `log/files/`, and one event carries the task, the name, the
    resolved commit, the kept path and the bytes' sha256 — the same
    mechanism the review launcher's kept prose uses.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    head = _head(repo)
    content = b"step: unit tests\nFAILED test_x\n12 failed, 3 passed\n"
    output = tmp_path / "check-output.log"
    output.write_bytes(content)
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "unit-tests",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    events = _events(repo)
    assert len(events) == 1
    event = events[0]
    kept = _kept_files(repo)
    assert len(kept) == 1
    assert event["task"] == "CR-001"
    assert event["name"] == "unit-tests"
    assert event["commit"] == head
    assert event["path"] == str(kept[0])
    assert event["sha256"] == hashlib.sha256(content).hexdigest()
    assert kept[0].read_bytes() == content
    # The record's excerpt is the tail, escaped for the journal.
    record = _checks(repo)[0]
    assert record["excerpt"] == (
        "step: unit tests\\nFAILED test_x\\n12 failed, 3 passed\\n"
    )
    # The kept path is named for the operator on stderr.
    assert str(kept[0]) in capsys.readouterr().err


def test_the_kept_bytes_are_the_file_exactly_as_given(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the kept bytes are the file exactly as given.

    The masking is the excerpt's: the kept payload holds the bytes
    unmasked — the full output stays on the machine that ran the check.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    secret = "AKIA" + "0" * 16
    content = f"export key={secret}\nFAILED test_x\n".encode()
    output = tmp_path / "out.log"
    output.write_bytes(content)

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "deploy",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    kept = _kept_files(repo)
    assert len(kept) == 1
    assert kept[0].read_bytes() == content
    # The record never carries the secret; the kept file does.
    assert secret not in _checks(repo)[0]["excerpt"]


def test_without_output_file_no_excerpt_and_no_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: without --output-file no excerpt and no event."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()

    assert (
        _record_check("--commit", "HEAD", "--name", "build", "--result", "passed") == 0
    )

    assert "excerpt" not in _checks(repo)[0]
    assert _events(repo) == []
    assert _kept_files(repo) == []


def test_an_unreadable_output_file_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unreadable output file is refused writing nothing."""

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    missing = tmp_path / "no-such.log"
    before = _tree(repo)
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "build",
            "--result",
            "failed",
            "--output-file",
            str(missing),
        )
        == 1
    )
    err = capsys.readouterr().err
    assert "--output-file" in err
    assert "no-such.log" in err
    assert _tree(repo) == before


def test_local_state_that_cannot_be_used_falls_back_to_a_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: local state that cannot be used falls back to a temporary
    file.

    A file sits where `log/files/` should be created, so the payload
    area cannot exist: the output is kept in a temporary file, stderr
    names the path and the reason, no event lands, and the record is
    still written.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    monkeypatch.setenv("TMPDIR", str(tmp_path))
    import tempfile

    monkeypatch.setattr(tempfile, "tempdir", None)
    _open()
    files_dir = _local_state(repo).log / "files"
    files_dir.parent.mkdir(parents=True)
    files_dir.write_text("in the way\n", encoding="utf-8")
    content = b"FAILED test_x\n"
    output = tmp_path / "out.log"
    output.write_bytes(content)
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "build",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    checks = _checks(repo)
    assert len(checks) == 1
    assert checks[0]["excerpt"] == "FAILED test_x\\n"
    assert _events(repo) == []
    err = capsys.readouterr().err
    kept = list(tmp_path.glob("agentmarshal-check-output-*.txt"))
    try:
        assert len(kept) == 1
        assert kept[0].read_bytes() == content
        assert str(kept[0]) in err
        assert "the clone's local state could not be used" in err
    finally:
        for path in kept:
            path.unlink(missing_ok=True)


def test_a_large_outputs_kept_file_exists_after_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A fresh payload is written after the sweep, before its event.

    ``open_writer`` bounds the log directory as it claims the writer
    file; running it before the payload is written means the sweep can
    never take a fresh payload whose event does not exist yet — even an
    output larger than the directory's whole bound is still there when
    the command finishes.
    """

    import agentmarshal.process_log as process_log

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    monkeypatch.setattr(process_log, "DIRECTORY_CAP_BYTES", 1024)
    content = b"x" * 4096 + b"FAILED at the very end\n"
    output = tmp_path / "out.log"
    output.write_bytes(content)
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "unit-tests",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    kept = _kept_files(repo)
    assert len(kept) == 1
    assert kept[0].read_bytes() == content
    events = _events(repo)
    assert len(events) == 1
    assert Path(events[0]["path"]).exists()


# -- the excerpt is the tail ------------------------------------------------------


def test_the_excerpt_is_the_contents_last_4_kib_at_most(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the excerpt is the content's last 4 KiB at most.

    The failing end survives: a larger output is cut to a tail encoding
    to at most 4 KiB of UTF-8, and the excerpt's end is the content's
    end.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    content = ("ok step one\n" * 600 + "FAILED test_x at the very end").encode()
    assert len(content) > 4096
    output = tmp_path / "out.log"
    output.write_bytes(content)

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "unit-tests",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    excerpt = _checks(repo)[0]["excerpt"]
    assert len(excerpt.encode("utf-8")) <= 4096
    assert excerpt.endswith("FAILED test_x at the very end")
    assert not excerpt.startswith("ok step one")


def test_the_tail_is_cut_on_a_character_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the tail is cut on a character boundary.

    The multi-byte character at the boundary is absent — never
    half-carried into a false replacement char — and the content's end
    still survives.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    # 'é' encodes to two bytes: after the 4095 trailing 'b' characters it
    # no longer fits the 4 KiB bound, so the suffix opens at the next
    # character and the two-byte one is dropped whole.
    content = b"a" * 903 + "é".encode() + b"b" * 4095
    assert len(content) == 5000
    output = tmp_path / "out.log"
    output.write_bytes(content)

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "unit-tests",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    excerpt = _checks(repo)[0]["excerpt"]
    assert excerpt == "b" * 4095
    assert "é" not in excerpt
    assert "\ufffd" not in excerpt


def test_undecodable_bytes_are_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: undecodable bytes are replaced.

    Bytes the tail cannot decode land as U+FFFD — visible, never an
    error — and the record is still written.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    content = b"tail start \xff\xfe tail end\n"
    output = tmp_path / "out.log"
    output.write_bytes(content)

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "unit-tests",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    record = _checks(repo)[0]
    assert "\ufffd\ufffd" in record["excerpt"]
    assert record["excerpt"].endswith("tail end\\n")

    # No cut occurred, so a leading continuation byte is an undecodable
    # byte like any other — replaced, never silently dropped.
    leading = tmp_path / "leading.log"
    leading.write_bytes(b"\x80failed\n")
    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "unit-tests",
            "--result",
            "failed",
            "--output-file",
            str(leading),
        )
        == 0
    )
    assert _checks(repo)[1]["excerpt"] == "\ufffdfailed\\n"

    # The decode is Python's own: 0xE2 0x82 0x80 is a whole character
    # (U+2080), the continuation byte after it is an orphan and lands as
    # the replacement character — and U+2080 no longer fits the 4 KiB
    # bound after it, so the excerpt opens with the replacement.
    spanning = tmp_path / "spanning.log"
    spanning.write_bytes(b"a" * 900 + b"\xe2" + b"\x82\x80\x80" + b"b" * 4093)
    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "unit-tests",
            "--result",
            "failed",
            "--output-file",
            str(spanning),
        )
        == 0
    )
    assert _checks(repo)[2]["excerpt"] == "\ufffd" + "b" * 4093
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


def test_the_bound_holds_after_masking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the bound holds after masking.

    A mask token can be longer than the span it replaces — here a 27-
    character token stands for a 20-character key — so the excerpt is
    bounded again after masking, still on a character boundary, and the
    content's end still survives.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    # 21 bytes per "key + space": the 4096-byte tail masks to more than
    # 4 KiB of UTF-8.
    content = (b"AKIA" + b"0" * 16 + b" ") * 200
    output = tmp_path / "out.log"
    output.write_bytes(content)

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "deploy",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    excerpt = _checks(repo)[0]["excerpt"]
    assert len(excerpt.encode("utf-8")) <= 4096
    assert excerpt.endswith("[masked: aws-access-key-id] ")
    assert "AKIA" not in excerpt
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


def test_characters_that_could_forge_a_line_are_escaped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: characters that could forge a line are escaped.

    Check output is lines; the record's forgeable-text rule refuses
    them raw, so the excerpt carries them as visible escapes.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    content = b"line one\nFAILED\ttest_x\n"
    output = tmp_path / "out.log"
    output.write_bytes(content)

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "unit-tests",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    excerpt = _checks(repo)[0]["excerpt"]
    assert "\n" not in excerpt
    assert "\t" not in excerpt
    assert excerpt == "line one\\nFAILED\\ttest_x\\n"
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


# -- a leak-scan hit is masked, never refused --------------------------------------


def test_a_signature_hit_is_masked_and_its_category_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a signature hit is masked and its category named.

    The excerpt carries `[masked: <category>]` in place of the span,
    stderr names the category, and the matched text appears nowhere —
    not in the record, not in the output.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    secret = "AKIA" + "0" * 16
    output = tmp_path / "out.log"
    output.write_bytes(f"credentials {secret} leaked\n".encode())
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "deploy",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    excerpt = _checks(repo)[0]["excerpt"]
    assert excerpt == "credentials [masked: aws-access-key-id] leaked\\n"
    captured = capsys.readouterr()
    assert "aws-access-key-id" in captured.err
    assert secret not in captured.out + captured.err
    assert secret not in json.dumps(_records(repo))


def test_a_private_marker_is_masked_by_category_value_nowhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a private marker is masked by category, value nowhere.

    The project's configured markers mask as `private-marker` — the
    category `scan_for_leaks` reports — and the marker's value appears
    nowhere in the output or the record.
    """

    marker = "builds.internal.corp"
    repo = _repo(tmp_path, monkeypatch, markers=(marker,))
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    output = tmp_path / "out.log"
    output.write_bytes(f"fetch from {marker} failed\n".encode())
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "deploy",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    excerpt = _checks(repo)[0]["excerpt"]
    assert excerpt == "fetch from [masked: private-marker] failed\\n"
    captured = capsys.readouterr()
    assert "private-marker" in captured.err
    assert marker not in captured.out + captured.err
    assert marker not in json.dumps(_records(repo))


def test_a_hit_does_not_refuse_the_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a hit does not refuse the record.

    The check's result is the fact being recorded — the record is
    written with the masked excerpt and the command exits zero.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    output = tmp_path / "out.log"
    output.write_bytes(b"token glpat-01234567890123456789\nFAILED\n")

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "deploy",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )
    checks = _checks(repo)
    assert len(checks) == 1
    assert "[masked: gitlab-token]" in checks[0]["excerpt"]


def test_an_excerpt_the_scan_still_trips_is_withheld(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an excerpt masking cannot make clean is withheld.

    `masked` is configured as a private marker, so the masked excerpt —
    which literally says `[masked: private-marker]` — still trips the
    scan after masking. The record is written with no excerpt rather
    than carrying the marker's value, stderr says the excerpt was
    withheld because masking could not make it clean and still names
    the categories found, and the command still exits zero: the record
    and the result land.
    """

    marker = "masked"
    repo = _repo(tmp_path, monkeypatch, markers=(marker,))
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    output = tmp_path / "out.log"
    output.write_bytes(b"the token was masked here\n")
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "build",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    record = _checks(repo)[0]
    assert "excerpt" not in record
    captured = capsys.readouterr()
    assert "withheld" in captured.err
    assert "masking could not make it clean" in captured.err
    # The categories are named even when the excerpt is withheld; the
    # marker's value never is.
    assert "private-marker" in captured.err
    assert marker not in captured.out + captured.err
    assert marker not in json.dumps(_records(repo))
    # The full output is still kept and announced — only the record's
    # excerpt is withheld.
    assert len(_kept_files(repo)) == 1
    assert len(_events(repo)) == 1


def test_the_withheld_message_names_every_category_either_scan_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an excerpt masking cannot make clean is withheld.

    Regression for RC-MASK-05: the marker `aws` does not occur in the
    content — only the AWS signature's span does — so the first scan
    names `aws-access-key-id` alone, and the mask label it writes,
    `[masked: aws-access-key-id]`, is what the rescan finds `aws` in.
    The withheld message names the union of both scans' categories,
    sorted — and no excerpt is recorded.
    """

    repo = _repo(tmp_path, monkeypatch, markers=("aws",))
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    secret = "AKIA" + "0" * 16
    output = tmp_path / "out.log"
    output.write_bytes(f"credentials {secret} leaked\n".encode())
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "deploy",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 0
    )

    record = _checks(repo)[0]
    assert "excerpt" not in record
    captured = capsys.readouterr()
    assert "withheld" in captured.err
    assert "aws-access-key-id" in captured.err
    assert "private-marker" in captured.err
    # The matched text is never echoed — to stderr or into the journal.
    assert secret not in captured.out + captured.err
    assert secret not in json.dumps(_records(repo))


def test_the_standalone_scan_is_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the standalone scan is untouched.

    `leak-scan` keeps its established output: the hit line names the
    file and the identification, the best-effort note follows on
    stderr, and the exit status still answers whether a hit was found.
    """

    repo = _repo(tmp_path, monkeypatch)
    from agentmarshal.cli import main

    base = _head(repo)
    (repo / "deploy.sh").write_text("KEY=AKIA" + "0" * 16 + "\n", encoding="utf-8")
    _git(repo, "add", "deploy.sh")
    _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "add deploy.sh",
    )
    head = _head(repo)
    capsys.readouterr()

    code = main(["leak-scan", "--base", base, "--commit", head])

    captured = capsys.readouterr()
    assert code == 1
    assert "deploy.sh: aws-access-key-id" in captured.out
    assert "possible leaks in added content" in captured.out
    assert "best-effort" in captured.err


# -- the recorder is named, or nothing is written ----------------------------------


def test_no_resolvable_recorder_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no resolvable recorder is refused writing nothing.

    The record requires `recorded_by`/`recorded_by_source`, so the
    command decides the resolution before anything is created — no
    record, no event, no kept file.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    _open()  # opened records do not require a recorder
    output = tmp_path / "out.log"
    output.write_bytes(b"FAILED test_x\n")
    before = _tree(repo)
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "build",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 1
    )
    err = capsys.readouterr().err
    assert "recorder" in err and "AGENTMARSHAL_ACTOR" in err
    assert _tree(repo) == before


def test_a_recorder_who_is_not_a_declared_actor_is_accepted_and_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a recorder who is not a declared actor is accepted and named.

    Recorder is provenance, not permission — the record is written
    naming the recorder and its source, and stderr says so.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner-7")
    _open()
    capsys.readouterr()

    assert (
        _record_check("--commit", "HEAD", "--name", "build", "--result", "passed") == 0
    )
    record = _checks(repo)[0]
    assert record["recorded_by"] == "ci-runner-7"
    assert record["recorded_by_source"] == "override"
    assert "not a declared actor" in capsys.readouterr().err


def test_a_declared_actor_records_with_no_undeclared_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a declared actor records with no undeclared note."""

    repo = _repo(
        tmp_path,
        monkeypatch,
        actors={"ci": {"git_identities": ["ci@example.invalid"]}},
    )
    _git(repo, "config", "user.email", "ci@example.invalid")
    _open()
    capsys.readouterr()

    assert (
        _record_check("--commit", "HEAD", "--name", "build", "--result", "passed") == 0
    )
    captured = capsys.readouterr()
    assert "ci" in captured.out
    assert "declared actor" not in captured.err


# -- a refusal leaves nothing behind ----------------------------------------------


@pytest.mark.parametrize(
    ("refusal", "expected"),
    [
        ("unknown task", "unknown task"),
        ("missing commit", "--commit"),
        ("bad result", None),
        ("refused field value", "control characters"),
        ("unreadable output file", "--output-file"),
        ("unreadable project file", "project configuration"),
    ],
)
def test_a_refused_run_leaves_the_journal_the_log_and_the_files_area_untouched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    refusal: str,
    expected: str | None,
) -> None:
    """Scenario: a refused run leaves the journal, the log and the files
    area untouched.

    Every foreseeable refusal — an unknown task, a commit that does not
    resolve, a result outside the vocabulary, a value the record rules
    refuse (a name that could forge a rendered line), an unreadable
    output file, a project file the command cannot read — is decided
    before any write, and every run is asked to keep a real output
    file, so a refusal also proves it keeps no file: the journal is
    byte-identical, no `check-output` event lands, no payload appears
    under `log/files/`, and the journal still validates.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    output = tmp_path / "out.log"
    output.write_bytes(b"FAILED test_x\n")

    task = "CR-001"
    arguments = [
        "--commit",
        "HEAD",
        "--name",
        "build",
        "--result",
        "failed",
        "--output-file",
        str(output),
    ]
    if refusal == "unknown task":
        task = "CR-099"
    elif refusal == "missing commit":
        arguments[arguments.index("--commit") + 1] = "deadbeef" * 5
    elif refusal == "bad result":
        arguments[arguments.index("--result") + 1] = "success"
    elif refusal == "refused field value":
        arguments[arguments.index("--name") + 1] = "check\nforged-approval"
    elif refusal == "unreadable output file":
        arguments[arguments.index("--output-file") + 1] = str(tmp_path / "no-such.log")
    elif refusal == "unreadable project file":
        # A section the command's own configuration read cannot parse:
        # the file reads as JSON but `leak_scan` is malformed, so the
        # refusal lands on the project-configuration read — and the
        # placement the validator resolves still parses.
        (repo / ".agentmarshal" / "project.json").write_text(
            json.dumps({"leak_scan": "broken"}) + "\n",
            encoding="utf-8",
        )
    before = _tree(repo)
    capsys.readouterr()

    if refusal == "bad result":
        # argparse refuses the vocabulary before the command runs.
        with pytest.raises(SystemExit) as exited:
            _record_check(*arguments, task=task)
        assert exited.value.code != 0
    else:
        assert _record_check(*arguments, task=task) == 1
    if expected is not None:
        assert expected in capsys.readouterr().err
    assert _tree(repo) == before
    assert _events(repo) == []
    assert _kept_files(repo) == []
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


def test_a_record_failure_after_the_output_is_kept_names_the_kept_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a record failure after the output is kept names the kept
    file.

    The payload and its event are already down when the record write
    fails — a refusal the command cannot foresee — so the error names
    the kept file, the way a left artifact is named.
    """

    repo = _repo(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    _open()
    output = tmp_path / "out.log"
    output.write_bytes(b"FAILED test_x\n")

    import agentmarshal.record_check as record_check

    def _failing_write(*args: Any, **kwargs: Any) -> Path:
        raise OSError("disk full")

    monkeypatch.setattr(record_check, "write_record", _failing_write)
    capsys.readouterr()

    assert (
        _record_check(
            "--commit",
            "HEAD",
            "--name",
            "build",
            "--result",
            "failed",
            "--output-file",
            str(output),
        )
        == 1
    )
    err = capsys.readouterr().err
    kept = _kept_files(repo)
    assert len(kept) == 1
    assert str(kept[0]) in err
    assert "disk full" in err
    assert _checks(repo) == []
    # The event and the file were already down — the named leftover.
    assert len(_events(repo)) == 1


def test_record_check_lists_its_arguments_in_help(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The command is registered from its own module: --task, --commit,
    --name, --result required; --failed-step, --run-url, --output-file
    optional."""

    from agentmarshal.cli import main

    _repo(tmp_path, monkeypatch)
    with pytest.raises(SystemExit) as exited:
        main(["record-check", "--help"])
    assert exited.value.code == 0
    out = capsys.readouterr().out
    for option in (
        "--task",
        "--commit",
        "--name",
        "--result",
        "--failed-step",
        "--run-url",
        "--output-file",
    ):
        assert option in out
