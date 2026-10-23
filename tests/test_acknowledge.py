"""`agentmarshal acknowledge` — a reviewed leak-scan hit, on the record.

ADR-0021 / ADR-0022 section 3: an operator who has verified a hit the
added-content scan reported writes one `acknowledgement` record bound to
the candidate's commit, the file and the hit's identification exactly as
the scan prints it. The command runs the same scan `leak-scan` runs and
writes only when the scan reports that hit; every refusal writes
nothing.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

_GITHUB_TOKEN = f"ghp_{'A1' * 18}"
_AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
_MARKER = "internal.example.invalid"


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


def _add_file(repo: Path, path: str, content: str) -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
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
        f"add {path}",
    )
    return _git(repo, "rev-parse", "HEAD")


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD")


def _open() -> None:
    from agentmarshal.cli import main

    assert main(["open", "--title", "Task"]) == 0


def _acknowledge(*extra: str, task: str = "CR-001") -> int:
    from agentmarshal.cli import main

    return main(["acknowledge", "--task", task, *extra])


def _records(repo: Path, task: str = "CR-001") -> list[dict[str, Any]]:
    records = sorted((_journal(repo) / "tasks" / task / "records").glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in records]


def _acknowledgements(repo: Path, task: str = "CR-001") -> list[dict[str, Any]]:
    return [r for r in _records(repo, task) if r["record_type"] == "acknowledgement"]


def _snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _repo_with_hit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    filename: str = "secret.py",
    content: str = f"key = '{_GITHUB_TOKEN}'\n",
    **kwargs: Any,
) -> tuple[Path, str, str]:
    """A repo whose head commit adds one file tripping the scan."""

    repo = _repo(tmp_path, monkeypatch, **kwargs)
    base = _head(repo)
    head = _add_file(repo, filename, content)
    _open()
    return repo, base, head


def _hit_args(
    base: str,
    head: str,
    *,
    file: str = "secret.py",
    signature: str = "github-token",
    reason: str = "reviewed, not a leak",
) -> list[str]:
    return [
        "--base",
        base,
        "--commit",
        head,
        "--file",
        file,
        "--signature",
        signature,
        "--reason",
        reason,
    ]


# -- the record is written for a reported hit ---------------------------------


def test_an_acknowledgement_is_written_for_a_reported_hit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acknowledgement is written for a reported hit.

    One `acknowledgement` record at schema 7 carrying the full 40-hex
    commit id, the file, the signature and the reason; stdout prints
    the record's path, the commit, the file, the identification and
    the recorder.
    """

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()

    assert _acknowledge(*_hit_args(base, head)) == 0

    acknowledgements = _acknowledgements(repo)
    assert len(acknowledgements) == 1
    record = acknowledgements[0]
    assert record["schema"] == 7
    assert record["commit"] == head
    assert record["file"] == "secret.py"
    assert record["signature"] == "github-token"
    assert "marker" not in record
    assert record["reason"] == "reviewed, not a leak"
    assert record["recorded_by"] == "an-operator"
    assert record["recorded_by_source"] == "override"
    out = capsys.readouterr().out
    printed_path = Path(out.splitlines()[0])
    assert printed_path.exists()
    assert json.loads(printed_path.read_text(encoding="utf-8")) == record
    assert f"commit {head}" in out
    assert "file secret.py" in out
    assert "signature github-token" in out
    assert "an-operator" in out


def test_a_markers_number_acknowledges_a_marker_hit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a marker's number acknowledges a marker hit.

    A hit the scan reports as `private-marker #1` is acknowledged with
    `--marker 1`; the record carries `marker` and no `signature`.
    """

    repo, base, head = _repo_with_hit(
        tmp_path,
        monkeypatch,
        filename="host.py",
        content=f"HOST = '{_MARKER}'\n",
        markers=(_MARKER,),
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")

    assert (
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            "host.py",
            "--marker",
            "1",
            "--reason",
            "internal host, not a leak",
        )
        == 0
    )

    record = _acknowledgements(repo)[0]
    assert record["marker"] == 1
    assert "signature" not in record
    assert record["commit"] == head
    assert record["file"] == "host.py"


def test_a_short_or_symbolic_commit_resolves_to_the_full_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a short or symbolic commit resolves to the full id.

    `--commit HEAD` lands in the record as the full 40-hex id it
    resolves to in the scanned repository.
    """

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")

    assert _acknowledge(*_hit_args(base, "HEAD")) == 0

    assert _acknowledgements(repo)[0]["commit"] == head


def test_both_or_neither_of_signature_and_marker_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: both or neither of --signature and --marker is refused
    before the command runs."""

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    before = _snapshot(_journal(repo))

    with pytest.raises(SystemExit) as exited:
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            "secret.py",
            "--signature",
            "github-token",
            "--marker",
            "1",
            "--reason",
            "reviewed",
        )
    assert exited.value.code != 0
    with pytest.raises(SystemExit) as exited:
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            "secret.py",
            "--reason",
            "reviewed",
        )
    assert exited.value.code != 0
    assert _snapshot(_journal(repo)) == before


def test_an_unknown_task_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unknown task is refused writing nothing."""

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, head), task="CR-099") == 1

    assert "unknown task" in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


@pytest.mark.parametrize("terminal", ["completed", "abandoned"])
def test_a_completed_or_abandoned_task_is_refused_writing_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    terminal: str,
) -> None:
    """Scenario: a completed or abandoned task is refused writing nothing.

    An acknowledgement is admitted after no terminal record — the hit it
    would name belongs to a candidate the task no longer drives.
    """

    from agentmarshal.journal.records import (
        create_abandoned_record,
        create_completed_record,
        write_record,
    )

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    if terminal == "completed":
        record = create_completed_record("CR-001", "test", "e" * 40)
    else:
        record = create_abandoned_record("CR-001", "test", "gone away")
    write_record(_journal(repo), "CR-001", record)
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, head)) == 1

    assert "not open" in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


def test_a_commit_that_does_not_resolve_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a commit that does not resolve is refused writing nothing."""

    repo, base, _head_commit = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, "0" * 40)) == 1

    err = capsys.readouterr().err
    assert "does not resolve" in err
    assert _snapshot(_journal(repo)) == before


def test_a_base_sharing_no_merge_base_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a base sharing no merge base is refused writing nothing.

    An unrelated root commit shares no ancestor with the candidate, so
    there is no `merge-base..commit` range to scan — the refusal names
    both references.
    """

    repo, _base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    # An unrelated root commit in the same object store — no checkout
    # needed, no common ancestor with the candidate's history.
    empty_tree = subprocess.run(
        ["git", "mktree"],
        cwd=repo,
        input="",
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    unrelated = _git(
        repo,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit-tree",
        empty_tree,
        "-m",
        "unrelated root",
    )
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(unrelated, head)) == 1

    err = capsys.readouterr().err
    assert "merge base" in err
    assert _snapshot(_journal(repo)) == before


# -- the hit is checked against the same scan leak-scan runs --------------------


@pytest.mark.parametrize(
    "spelling", ["./secret.py", "secret.py ", "SECRET.py", "subdir/secret.py"]
)
def test_a_hit_is_acknowledged_only_under_its_printed_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    spelling: str,
) -> None:
    """Scenario: a hit is acknowledged only under its printed name.

    A `--file` spelling that is not the path the scan prints — another
    separator, another case, a parent or child path — matches nothing:
    the refusal names the file as given and how many hits the scan
    reported, and no record is written.
    """

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, head, file=spelling)) == 1

    err = capsys.readouterr().err
    assert spelling in err
    assert "the scan reported 1 hit" in err
    assert _snapshot(_journal(repo)) == before


def test_an_identification_the_scan_does_not_report_for_that_file_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an identification the scan does not report for that
    file is refused.

    The file matches but the identification does not — a different
    signature id, or `private-marker #1` where the hit is a signature —
    so the refusal names both and the scan's count.
    """

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, head, signature="aws-access-key-id")) == 1
    err = capsys.readouterr().err
    assert "secret.py" in err
    assert "aws-access-key-id" in err
    assert "the scan reported 1 hit" in err

    assert (
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            "secret.py",
            "--marker",
            "1",
            "--reason",
            "reviewed",
        )
        == 1
    )
    err = capsys.readouterr().err
    assert "private-marker #1" in err
    assert "the scan reported 1 hit" in err
    assert _snapshot(_journal(repo)) == before


def test_a_hit_on_another_commit_is_not_a_hit_here(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a hit on another commit is not a hit here.

    The hit exists on `head`, but the range `base..later` — where the
    file's addition was reverted — reports nothing for it: an
    acknowledgement binds the exact commit whose additions it answers.
    """

    repo, base, _hit_commit = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    (repo / "secret.py").unlink()
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
        "revert",
    )
    later = _head(repo)
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, later)) == 1

    err = capsys.readouterr().err
    assert "the scan reported 0 hits" in err
    assert _snapshot(_journal(repo)) == before


def test_a_clean_scan_reports_no_hit_to_acknowledge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a clean scan reports no hit to acknowledge."""

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    head = _add_file(repo, "module.py", "def add(a, b):\n    return a + b\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, head)) == 1

    err = capsys.readouterr().err
    assert "the scan reported 0 hits" in err
    assert _snapshot(_journal(repo)) == before


def test_the_matched_text_appears_nowhere_in_the_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the matched text appears nowhere in the output.

    Neither the refusal nor the write nor the record itself carries the
    matched text or a marker's value — only the file and the
    identification.
    """

    repo, base, head = _repo_with_hit(
        tmp_path,
        monkeypatch,
        filename="host.py",
        content=f"HOST = '{_MARKER}'\n",
        markers=(_MARKER,),
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()

    assert (
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            "host.py",
            "--signature",
            "aws-access-key-id",
            "--reason",
            "reviewed",
        )
        == 1
    )
    captured = capsys.readouterr()
    assert _MARKER not in captured.out + captured.err

    assert (
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            "host.py",
            "--marker",
            "1",
            "--reason",
            "internal host, not a leak",
        )
        == 0
    )
    captured = capsys.readouterr()
    assert _MARKER not in captured.out + captured.err
    record = _acknowledgements(repo)[0]
    assert _MARKER not in json.dumps(record)


def test_a_file_the_scan_could_not_decode_is_named_beside_the_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a file the scan could not decode is named beside the
    result.

    An undecodable file in the diff is named on stderr as one whose
    bytes were still searched — it is no hit and fails nothing: the
    real hit in the same diff is still acknowledged.
    """

    repo = _repo(tmp_path, monkeypatch)
    base = _head(repo)
    (repo / "secret.py").write_text(f"key = '{_GITHUB_TOKEN}'\n", encoding="utf-8")
    (repo / "blob.bin").write_bytes(b"\xff\xfe\x00\x01 \x80")
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
        "secret plus binary",
    )
    head = _head(repo)
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()

    assert _acknowledge(*_hit_args(base, head)) == 0

    err = capsys.readouterr().err
    assert "could not decode" in err
    assert "blob.bin" in err
    assert len(_acknowledgements(repo)) == 1


def test_a_hit_under_a_marker_named_path_acknowledges_by_the_masked_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a hit under a marker-named path acknowledges by the
    masked name.

    The scan prints the file's path masked — `vendor/<private marker
    #1>/config.py` — so that masked form is the only `--file` that
    matches; the raw path is refused and the marker's value appears
    nowhere in the output.
    """

    repo = _repo(tmp_path, monkeypatch, markers=(_MARKER,))
    base = _head(repo)
    head = _add_file(repo, f"vendor/{_MARKER}/config.py", f"HOST = '{_MARKER}'\n")
    _open()
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    masked = "vendor/<private marker #1>/config.py"

    # The raw path names no hit the scan prints.
    before = _snapshot(_journal(repo))
    assert (
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            f"vendor/{_MARKER}/config.py",
            "--marker",
            "1",
            "--reason",
            "internal host, not a leak",
        )
        == 1
    )
    captured = capsys.readouterr()
    assert _MARKER not in captured.out + captured.err
    assert masked in captured.err
    assert _snapshot(_journal(repo)) == before

    # The masked form is the file the record binds.
    assert (
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            masked,
            "--marker",
            "1",
            "--reason",
            "internal host, not a leak",
        )
        == 0
    )
    captured = capsys.readouterr()
    assert _MARKER not in captured.out + captured.err
    record = _acknowledgements(repo)[0]
    assert record["file"] == masked
    assert record["marker"] == 1


def test_the_standalone_commands_output_and_exit_are_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the standalone command's output and exit are unchanged.

    After an acknowledgement lands, `leak-scan` over the same range
    prints the hit exactly as before and still exits 1 — the
    acknowledgement is not yet honoured on the hit's surfaces.
    """

    from agentmarshal.cli import main

    _, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1
    before_out = capsys.readouterr().out

    assert _acknowledge(*_hit_args(base, head)) == 0
    capsys.readouterr()

    assert main(["leak-scan", "--base", base, "--commit", head]) == 1
    captured = capsys.readouterr()
    assert captured.out == before_out
    assert "secret.py: github-token" in captured.out


def test_in_a_sidecar_the_scan_reads_the_host_and_the_journal_the_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Design decision: a sidecar scans the host's diff and writes its
    own journal.

    The candidate's commits live in the host, so the scan's merge base
    and diff are resolved there and the markers come from the sidecar's
    own configuration; the record lands in the sidecar's journal and
    the host's tree is untouched by it.
    """

    from agentmarshal.cli import main

    host = tmp_path / "host"
    host.mkdir()
    _git(host, "init", "--quiet")
    (host / "readme.md").write_text("host\n", encoding="utf-8")
    _git(host, "add", "-A")
    _git(
        host,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "base",
    )
    base = _head(host)
    (host / "host.py").write_text(f"HOST = '{_MARKER}'\n", encoding="utf-8")
    _git(host, "add", "-A")
    _git(
        host,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "add host.py",
    )
    head = _head(host)

    sidecar = tmp_path / "sidecar"
    sidecar.mkdir()
    _git(sidecar, "init", "--quiet")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    # The private markers come from the sidecar's own configuration —
    # the host's project file, if any, is not the trusted side.
    project_file = sidecar / ".agentmarshal" / "project.json"
    project = json.loads(project_file.read_text(encoding="utf-8"))
    project["leak_scan"] = {"private_markers": [_MARKER]}
    project_file.write_text(json.dumps(project) + "\n", encoding="utf-8")
    assert main(["open", "--title", "Task"]) == 0
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()

    assert (
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            "host.py",
            "--marker",
            "1",
            "--reason",
            "internal host, not a leak",
        )
        == 0
    )

    records = _acknowledgements(sidecar)
    assert len(records) == 1
    assert records[0]["commit"] == head
    assert records[0]["marker"] == 1
    assert _MARKER not in capsys.readouterr().out


# -- the recorder is named, or nothing is written -------------------------------


def test_no_resolvable_recorder_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no resolvable recorder is refused writing nothing."""

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, head)) == 1

    err = capsys.readouterr().err
    assert "recorder" in err and "AGENTMARSHAL_ACTOR" in err
    assert _snapshot(_journal(repo)) == before


def test_a_recorder_who_is_not_a_declared_actor_is_accepted_and_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a recorder who is not a declared actor is accepted and
    named.

    Recorder is provenance, not permission — the record is written and
    the note says so plainly on stderr.
    """

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "a-stranger")
    capsys.readouterr()

    assert _acknowledge(*_hit_args(base, head)) == 0

    assert _acknowledgements(repo)[0]["recorded_by"] == "a-stranger"
    assert "not a declared actor" in capsys.readouterr().err


def test_a_declared_actor_records_with_no_undeclared_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a declared actor records with no undeclared note.

    Whether the actor id resolves through the table or merely *names* a
    declared actor through the override, there is nothing to note.
    """

    repo, base, head = _repo_with_hit(
        tmp_path,
        monkeypatch,
        actors={"lead": {"git_identities": ["lead@example.invalid"]}},
    )
    _git(repo, "config", "user.email", "lead@example.invalid")
    capsys.readouterr()

    assert _acknowledge(*_hit_args(base, head)) == 0
    captured = capsys.readouterr()
    assert "lead" in captured.out
    assert "declared actor" not in captured.err

    # An override that names a declared actor is also quiet.
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "lead")
    assert _acknowledge(*_hit_args(base, head)) == 0
    assert "declared actor" not in capsys.readouterr().err


def test_the_recorder_is_escaped_where_it_could_forge_a_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the recorder is escaped where it could forge a line.

    A recorder containing newline or line-separator bytes must not
    reorder or fabricate output lines — the escaped form is what
    prints, in the recorder line and in the undeclared-actor note
    alike, while the record keeps the true identity bytes.
    """

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "op\nera\u202etor")
    capsys.readouterr()

    assert _acknowledge(*_hit_args(base, head)) == 0

    captured = capsys.readouterr()
    assert "op\nera\u202etor" not in captured.out + captured.err
    assert "op\\nera\\u202etor" in captured.out
    assert "op\\nera\\u202etor" in captured.err
    assert _acknowledgements(repo)[0]["recorded_by"] == "op\nera\u202etor"


# -- a refusal leaves nothing behind --------------------------------------------


def test_a_refused_run_leaves_the_journal_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a refused run leaves the journal untouched.

    Every refusal the command can foresee is decided before any write:
    the journal is byte-identical and `agentmarshal validate` still
    passes.
    """

    from agentmarshal.cli import main

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    # A hit the scan does not report.
    assert _acknowledge(*_hit_args(base, head, file="other.py")) == 1
    # A commit that does not resolve.
    assert _acknowledge(*_hit_args(base, "0" * 40)) == 1
    # An unknown task.
    assert _acknowledge(*_hit_args(base, head), task="CR-099") == 1
    # A value the record rules refuse.
    assert _acknowledge(*_hit_args(base, head, reason="x" * 1001)) == 1

    assert _snapshot(_journal(repo)) == before
    assert main(["validate"]) == 0


def test_a_value_the_record_rules_refuse_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value the record rules refuse writes nothing.

    The reason's 1000-character bound, an empty file or reason, a
    signature the scan does not know and a marker below 1 are each
    refused on the record's rule — not reported as a missing hit.
    """

    repo, base, head = _repo_with_hit(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _acknowledge(*_hit_args(base, head, reason="x" * 1001)) == 1
    err = capsys.readouterr().err
    assert "reason" in err and "1000" in err

    assert _acknowledge(*_hit_args(base, head, file="  ")) == 1
    assert "non-empty" in capsys.readouterr().err

    assert _acknowledge(*_hit_args(base, head, reason="  ")) == 1
    assert "non-empty" in capsys.readouterr().err

    assert _acknowledge(*_hit_args(base, head, signature="not-a-signature")) == 1
    assert "must be one of" in capsys.readouterr().err

    assert (
        _acknowledge(
            "--base",
            base,
            "--commit",
            head,
            "--file",
            "secret.py",
            "--marker",
            "0",
            "--reason",
            "reviewed",
        )
        == 1
    )
    assert "an integer of at least 1" in capsys.readouterr().err

    assert _snapshot(_journal(repo)) == before
    from agentmarshal.cli import main

    assert main(["validate"]) == 0


def test_acknowledge_lists_its_arguments_in_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The command is registered from its own module: every flag."""

    from agentmarshal.cli import main

    with pytest.raises(SystemExit) as exited:
        main(["acknowledge", "--help"])
    assert exited.value.code == 0
    out = capsys.readouterr().out
    for flag in (
        "--task",
        "--base",
        "--commit",
        "--file",
        "--signature",
        "--marker",
        "--reason",
    ):
        assert flag in out
