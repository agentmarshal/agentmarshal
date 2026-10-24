"""Tests for ``stage run`` — the shared extensions' declared stages."""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

import agentmarshal.stages as stages_module
from agentmarshal.cli import main
from agentmarshal.journal.records import create_acceptance_record, write_record
from agentmarshal.localstate import LocalState
from agentmarshal.process_log import read_events
from test_placement import _host_and_sidecar

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]


def _git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """An initialized repo on ``master``, the working directory inside it."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo


def _manifest(
    name: str = "openspec",
    stages: tuple[tuple[str, str], ...] = (("pre-gate-stop", "bin/check.py"),),
    isolation: str | None = None,
) -> str:
    lines = [
        "schema = 2",
        f'name = "{name}"',
        'version = "1.0.0"',
        'footprint = ["x/"]',
        "documents = []",
    ]
    for phase, command in stages:
        lines.extend(["", "[[stage]]", f'phase = "{phase}"', f'command = "{command}"'])
    if isolation is not None:
        lines.extend(["", isolation])
    return "\n".join(lines) + "\n"


def _extension(
    repo: Path,
    name: str = "openspec",
    manifest: str | None = None,
    files: dict[str, str] | None = None,
) -> Path:
    """Write a directory-form shared extension into the working tree."""

    directory = repo / ".agentmarshal" / "extensions" / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.toml").write_text(
        _manifest(name) if manifest is None else manifest, encoding="utf-8"
    )
    if files is None:
        files = {"bin/check.py": "import sys\nprint('check ran')\nsys.exit(0)\n"}
    for relpath, content in files.items():
        path = directory / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return directory


def _repo_with_extension(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "openspec",
    manifest: str | None = None,
    files: dict[str, str] | None = None,
) -> tuple[Path, str, str]:
    """Project, extension committed on master, candidate branch one commit ahead.

    Returns ``(repo, base, candidate)``; the checkout stays on ``candidate``.
    """

    repo = _project(tmp_path, monkeypatch)
    _extension(repo, name=name, manifest=manifest, files=files)
    base = _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "candidate.txt").write_text("x\n", encoding="utf-8")
    candidate = _commit_all(repo, "candidate")
    return repo, base, candidate


def _stage_run(
    phase: str = "pre-gate",
    task: str = "CR-001",
    commit: str = "HEAD",
    base: str = "master",
) -> int:
    return main(
        [
            "stage",
            "run",
            "--phase",
            phase,
            "--task",
            task,
            "--commit",
            commit,
            "--base",
            base,
        ]
    )


def _ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")


def _workstation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CI", raising=False)


def _trust(monkeypatch: pytest.MonkeyPatch, name: str = "openspec") -> int:
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ops-lead")
    return main(["extension", "trust", name])


def _events(repo: Path) -> list[dict[str, object]]:
    return read_events(LocalState(repo / ".git" / "agentmarshal"))


def _journal_snapshot(repo: Path) -> dict[str, bytes]:
    root = repo / ".agentmarshal" / "journal"
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _accept_pause(
    repo: Path,
    extension: str = "openspec",
    commit: str | None = None,
    party: str = "ops-lead",
    reason: str = "The pause is understood",
    task: str = "CR-001",
) -> Path:
    """Write one ``accepted_pause`` acceptance for *task*; return its path."""

    record = create_acceptance_record(
        task,
        "test",
        commit,
        party,
        None,
        reason,
        accepted_pause=extension,
    )
    return write_record(repo / ".agentmarshal" / "journal", task, record)


# -- the declared stages of the base's shared extensions ---------------------


def test_pre_gate_invokes_the_pre_gate_warn_and_pre_gate_stop_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: pre-gate invokes the pre-gate-warn and pre-gate-stop stages."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(
                ("pre-gate-warn", "bin/warn.py"),
                ("pre-gate-stop", "bin/stop.py"),
                ("post-gate", "bin/post.py"),
            )
        ),
        files={
            "bin/warn.py": "print('warn ran')\n",
            "bin/stop.py": "print('stop ran')\n",
            "bin/post.py": "print('post ran')\n",
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | warn ran" in out
    assert "openspec | stop ran" in out
    assert "post ran" not in out
    assert out.count("openspec: ") == 2


def test_post_gate_invokes_the_post_gate_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: post-gate invokes the post-gate stages."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(
                ("post-gate", "bin/post.py"),
                ("pre-gate-stop", "bin/stop.py"),
            )
        ),
        files={
            "bin/post.py": "print('post ran')\n",
            "bin/stop.py": "print('stop ran')\n",
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(phase="post-gate", commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | post ran" in out
    assert "stop ran" not in out


def test_stages_run_in_extension_name_order_and_manifest_order_within(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: stages run in extension-name order and manifest order within."""
    repo = _project(tmp_path, monkeypatch)
    # Declared out of name order on purpose: zeta first in the tree listing
    # would still run after alpha.
    _extension(
        repo,
        name="zeta",
        manifest=_manifest(name="zeta", stages=(("pre-gate-stop", "bin/z.py"),)),
        files={"bin/z.py": "print('zeta ran')\n"},
    )
    _extension(
        repo,
        name="alpha",
        manifest=_manifest(
            name="alpha",
            stages=(
                ("pre-gate-stop", "bin/first.py"),
                ("pre-gate-stop", "bin/second.py"),
            ),
        ),
        files={
            "bin/first.py": "print('alpha first')\n",
            "bin/second.py": "print('alpha second')\n",
        },
    )
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert (
        out.index("alpha | alpha first")
        < out.index("alpha | alpha second")
        < out.index("zeta | zeta ran")
    )
    assert out.index("alpha: checked") < out.index("zeta: checked")


def test_a_manifest_the_base_cannot_parse_fails_the_run_naming_the_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a manifest the base cannot parse fails the run naming the extension."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        # A well-formed schema-1 manifest: valid to parse, refused in the
        # directory form the moment the tree reader weighs it.
        manifest=(
            "schema = 1\n"
            'name = "openspec"\n'
            'version = "1.0.0"\n'
            'install = "x"\n'
            'remove = "x"\n'
            'footprint = ["x/"]\n'
            "documents = []\n"
            "artifacts = []\n"
        ),
        files={"bin/check.py": "print(1)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 1

    captured = capsys.readouterr()
    assert "openspec" in captured.err
    assert "manifest.toml" in captured.err
    assert "requires" in captured.err
    assert "checked" not in captured.out


def test_a_file_form_extension_has_no_stage_to_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a file-form extension has no stage to run."""
    repo = _project(tmp_path, monkeypatch)
    manifest = repo / ".agentmarshal" / "extensions" / "openspec.toml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "schema = 1\n"
        'name = "openspec"\n'
        'version = "1.0.0"\n'
        'install = "x"\n'
        'remove = "x"\n'
        'footprint = ["openspec/"]\n'
        "documents = []\n"
        "artifacts = []\n",
        encoding="utf-8",
    )
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "no shared extension declares a pre-gate stage" in out


def test_a_sidecar_runs_no_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a sidecar runs no stages."""
    _host, _sidecar, base, head = _host_and_sidecar(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit=head, base=base) == 1

    captured = capsys.readouterr()
    assert "sidecar" in captured.err
    assert "no stages" in captured.err
    assert captured.out == ""


def test_an_invalid_task_identifier_refuses_before_any_stage_is_planned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an invalid task identifier refuses before any stage is planned."""
    # The manifest is malformed too: the task refusal still wins, so the
    # identifier is checked before any manifest is read.
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest='schema = 1\nname = "openspec"\n',
        files={"bin/check.py": "print(1)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(task="not a task", commit="candidate", base="master") == 1

    captured = capsys.readouterr()
    assert "task id" in captured.err
    assert "manifest" not in captured.err
    assert "openspec" not in captured.err
    assert "checked" not in captured.out


# -- materialization ---------------------------------------------------------


def test_the_base_commits_code_runs_not_the_candidates_or_the_working_trees(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the base commit's code runs, not the candidate's or the working tree's."""  # noqa: E501
    repo, _base, _candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "print('BASE')\n"},
    )
    # The candidate changes the script and the manifest; the working tree
    # changes the script again, uncommitted. The base's still runs.
    check = repo / ".agentmarshal" / "extensions" / "openspec" / "bin" / "check.py"
    check.write_text("print('CANDIDATE')\n", encoding="utf-8")
    (repo / ".agentmarshal" / "extensions" / "openspec" / "manifest.toml").write_text(
        _manifest(stages=(("pre-gate-stop", "bin/evil.py"),)),
        encoding="utf-8",
    )
    (repo / ".agentmarshal" / "extensions" / "openspec" / "bin" / "evil.py").write_text(
        "print('EVIL')\n", encoding="utf-8"
    )
    _commit_all(repo, "candidate edits")
    check.write_text("print('WORKTREE')\n", encoding="utf-8")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | BASE" in out
    for forbidden in ("CANDIDATE", "WORKTREE", "EVIL"):
        assert forbidden not in out


def test_the_working_directory_is_a_snapshot_of_the_candidate_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the working directory is a snapshot of the candidate commit."""
    repo, _base, _candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={
            "bin/check.py": (
                "import os\n"
                "print('HAS_CAND', os.path.exists('candidate.txt'))\n"
                "print('HAS_DIRTY', os.path.exists('dirty.txt'))\n"
                "print('CWD', os.getcwd())\n"
            )
        },
    )
    (repo / "dirty.txt").write_text("dirty\n", encoding="utf-8")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | HAS_CAND True" in out
    assert "openspec | HAS_DIRTY False" in out
    assert "openspec | CWD " in out


def test_a_symbolic_link_inside_the_extensions_directory_is_recreated_as_a_link(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a symbolic link inside the extension's directory is recreated as a link."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        manifest=_manifest(stages=(("pre-gate-stop", "bin/sub/check.py"),)),
        files={
            "bin/check.py": "print('bin check')\n",
            "shared/check.py": "print('shared check')\n",
        },
    )
    # ``bin/sub`` is a link to a directory the extension holds: the
    # command resolves through it, so only the directory-level refusal
    # — the link recreated as a link, never a copy — keeps the run on
    # what the base approved, in CI as on a workstation.
    link = repo / ".agentmarshal" / "extensions" / "openspec" / "bin" / "sub"
    link.symlink_to("../shared")
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert "openspec: not run (symlink in extension directory: bin/sub)" in out
    assert "shared check" not in out


def test_a_gitlink_inside_the_extensions_directory_is_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a gitlink inside the extension's directory is not run."""
    repo, base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    _git(repo, "checkout", "--quiet", "master")
    _git(
        repo,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{base},.agentmarshal/extensions/openspec/sub",
    )
    _git(repo, *_WRITER, "commit", "--quiet", "-m", "gitlink")
    # The candidate must descend from the gitlink commit for the merge
    # base to carry it.
    _git(repo, "checkout", "--quiet", "-B", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert "openspec: not run" in out
    assert "gitlink" in out


def test_an_unspellable_symlink_target_is_not_run_not_an_escaped_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a stage that may not run prints not run (<reason>)."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    _git(repo, "add", "-A")
    # A link target git stores but no platform call can spell: the blob
    # carries a NUL, so recreating the entry raises a ValueError inside
    # materialization — a ``not run`` reason, never an escaped
    # exception.
    blob = (
        subprocess.run(
            ["git", "hash-object", "-w", "--stdin"],
            cwd=repo,
            input=b"target\x00inside",
            capture_output=True,
            check=True,
        )
        .stdout.decode("ascii")
        .strip()
    )
    _git(
        repo,
        "update-index",
        "--add",
        "--cacheinfo",
        f"120000,{blob},.agentmarshal/extensions/openspec/bin/bad-link",
    )
    _git(repo, *_WRITER, "commit", "--quiet", "-m", "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert "openspec: not run (cannot materialize:" in out
    assert "null" in out
    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    (event,) = events
    assert event["decision"] == "not-run"
    assert "cannot materialize" in str(event["reason"])


def test_a_snapshot_that_cannot_materialize_is_not_run_not_an_escaped_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a stage that may not run prints not run (<reason>)."""
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)

    def _fail(_root: Path, _commit: str, _snapshot: Path) -> None:
        raise ValueError("tar says no")

    # A snapshot failure the launch error does not wrap — any exception
    # at all is the stage's ``not run`` reason, never an escaped
    # exception.
    monkeypatch.setattr(stages_module, "_extract_snapshot", _fail)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert (
        "openspec: not run (cannot materialize the candidate snapshot: "
        "tar says no)" in out
    )
    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    (event,) = events
    assert event["decision"] == "not-run"
    assert "cannot materialize the candidate snapshot" in str(event["reason"])


def test_the_temporary_directories_are_gone_when_the_command_returns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the temporary directories are gone when the command returns."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={
            "bin/check.py": "import os\nprint(os.environ['AGENTMARSHAL_SNAPSHOT'])\n"
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    snapshot_line = next(
        line for line in out.splitlines() if line.startswith("openspec | /")
    )
    snapshot = Path(snapshot_line.split(" | ", 1)[1])
    assert not snapshot.exists()
    assert not snapshot.parent.exists()


def test_an_earlier_stage_cannot_rewrite_a_later_stages_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an earlier stage cannot rewrite a later stage's command."""
    repo, _base, _candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(
                ("pre-gate-warn", "bin/first.py"),
                ("pre-gate-stop", "bin/second.py"),
            )
        ),
        files={
            # The first stage reaches its own materialized copy through
            # __file__ and rewrites the second stage's command file in it.
            "bin/first.py": (
                "from pathlib import Path\n"
                "target = Path(__file__).resolve().parents[1] / 'bin' / 'second.py'\n"
                "target.write_text(\"print('REWRITTEN')\\n\", encoding='utf-8')\n"
                "print('first ran')\n"
            ),
            "bin/second.py": "print('BASE SECOND')\n",
        },
    )
    # The grant is recorded on master's checkout, where the extension's
    # contents are the base's — the contents each stage's fresh
    # materialization carries and the grant check recomputes on.
    _git(repo, "checkout", "--quiet", "master")
    assert _trust(monkeypatch) == 0
    _git(repo, "checkout", "--quiet", "candidate")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | first ran" in out
    assert "openspec | BASE SECOND" in out
    assert "REWRITTEN" not in out
    assert out.count("openspec: checked") == 2


# -- the argv invocation -----------------------------------------------------


def test_the_command_runs_under_the_cores_interpreter_never_through_a_shell(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the command runs under the core's interpreter, never through a shell."""  # noqa: E501
    repo, _base, _candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={
            "bin/check.py": (
                "import sys\n"
                "print('ARGV0', sys.argv[0])\n"
                "print('INTERP', sys.executable)\n"
            )
        },
    )
    check = repo / ".agentmarshal" / "extensions" / "openspec" / "bin" / "check.py"
    # No shebang, no execute bit: nothing but an explicit interpreter could
    # run it, and no shell expanded it.
    check.chmod(0o644)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | ARGV0 " in out
    assert "check.py" in out
    assert f"openspec | INTERP {sys.executable}" in out
    assert "openspec: checked" in out


def test_the_environment_carries_the_protocol_variables_and_a_minimal_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the environment carries the protocol variables and a minimal PATH."""
    repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={
            "bin/check.py": (
                "import os, json\nprint(json.dumps(sorted(os.environ.items())))\n"
            )
        },
    )
    monkeypatch.setenv("HOME", "/must/not/leak")
    monkeypatch.setenv("STAGE_SECRET", "leak-me-not")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    env_line = next(
        line.split(" | ", 1)[1]
        for line in out.splitlines()
        if line.startswith("openspec | [")
    )
    env = dict(json.loads(env_line))
    merge_base = _git(repo, "merge-base", "master", "candidate")
    assert env["AGENTMARSHAL_PHASE"] == "pre-gate"
    assert env["AGENTMARSHAL_TASK"] == "CR-001"
    assert env["AGENTMARSHAL_COMMIT"] == candidate
    assert env["AGENTMARSHAL_BASE"] == merge_base
    assert env["AGENTMARSHAL_SNAPSHOT"].endswith("snapshot-0")
    # The minimal PATH carries no empty element — an empty element is
    # the stage's own working directory, the candidate snapshot — and
    # no directory the stage runs in.
    assert env["PATH"] == "/usr/bin:/bin"
    assert "" not in env["PATH"].split(":")
    assert env["AGENTMARSHAL_SNAPSHOT"] not in env["PATH"].split(":")
    assert os.getcwd() not in env["PATH"].split(":")
    assert "STAGE_SECRET" not in env
    assert env.get("HOME") != "/must/not/leak"


def test_only_the_environment_variables_the_manifest_names_are_passed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: only the environment variables the manifest names are passed."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            isolation=(
                "[isolation]\n"
                "network = false\n"
                'env = ["STAGE_PASS_ME"]\n'
                'writes = "none"\n'
                "timeout_seconds = 30\n"
            )
        ),
        files={
            "bin/check.py": (
                "import os\n"
                "print('PASS', os.environ.get('STAGE_PASS_ME'))\n"
                "print('NOT', os.environ.get('STAGE_NOT_ME'))\n"
            )
        },
    )
    monkeypatch.setenv("STAGE_PASS_ME", "granted")
    monkeypatch.setenv("STAGE_NOT_ME", "withheld")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | PASS granted" in out
    assert "openspec | NOT None" in out


def test_a_path_named_in_isolation_env_is_not_passed_through(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a PATH named in isolation.env is not passed through."""
    repo = _project(tmp_path, monkeypatch)
    for name in ("alpha", "beta"):
        _extension(
            repo,
            name=name,
            manifest=_manifest(
                name=name,
                isolation=(
                    "[isolation]\n"
                    "network = false\n"
                    'env = ["PATH"]\n'
                    'writes = "none"\n'
                    "timeout_seconds = 30\n"
                ),
            ),
            files={"bin/check.py": "import os\nprint('PATH=' + os.environ['PATH'])\n"},
        )
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    # The caller's PATH keeps git resolvable for the run's own machinery
    # but is not the minimal value the stage must see.
    monkeypatch.setenv("PATH", os.environ["PATH"] + ":/caller/bin")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "alpha | PATH=/usr/bin:/bin" in captured.out
    assert "beta | PATH=/usr/bin:/bin" in captured.out
    assert "/caller/bin" not in captured.out
    # Two extensions declare PATH; the note still appears exactly once.
    assert captured.err.count("PATH is fixed by the core") == 1


def test_a_protocol_variable_cannot_be_overridden_by_a_declared_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a protocol variable cannot be overridden by a declared name."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            isolation=(
                "[isolation]\n"
                "network = false\n"
                'env = ["AGENTMARSHAL_TASK"]\n'
                'writes = "none"\n'
                "timeout_seconds = 30\n"
            )
        ),
        files={"bin/check.py": "import os\nprint(os.environ['AGENTMARSHAL_TASK'])\n"},
    )
    monkeypatch.setenv("AGENTMARSHAL_TASK", "FORGED")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | CR-001" in out
    assert "FORGED" not in out


def test_a_missing_command_is_not_run_naming_why(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a missing command is not run naming why."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("pre-gate-stop", "bin/missing.py"),)),
        files={"bin/other.py": "print(1)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert "openspec: not run" in out
    assert "bin/missing.py" in out


def test_a_symlinked_command_is_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a symlinked command is not run."""
    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        manifest=_manifest(stages=(("pre-gate-stop", "bin/link.py"),)),
        files={"bin/check.py": "print(1)\n"},
    )
    link = repo / ".agentmarshal" / "extensions" / "openspec" / "bin" / "link.py"
    link.symlink_to("check.py")
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert "openspec: not run" in out
    assert "bin/link.py" in out
    assert "symlink in extension directory" in out


def test_exit_status_zero_checks_and_any_other_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: exit status zero checks and any other fails."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(
                ("pre-gate-warn", "bin/warn.py"),
                ("pre-gate-stop", "bin/stop.py"),
            )
        ),
        files={
            "bin/warn.py": "import sys\nsys.exit(7)\n",
            "bin/stop.py": "import sys\nsys.exit(0)\n",
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec: failed (exit 7)" in out
    assert "openspec: checked" in out


# -- the time limit ----------------------------------------------------------


def test_a_stage_over_its_declared_timeout_is_killed_and_did_not_finish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a stage over its declared timeout is killed and did not finish."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            isolation=(
                "[isolation]\n"
                "network = false\n"
                "env = []\n"
                'writes = "none"\n'
                "timeout_seconds = 1\n"
            )
        ),
        files={"bin/check.py": "import time\ntime.sleep(60)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert "openspec: did not finish (timeout)" in out


def test_the_cores_limit_caps_a_longer_declared_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the core's limit caps a longer declared timeout."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            isolation=(
                "[isolation]\n"
                "network = false\n"
                "env = []\n"
                'writes = "none"\n'
                "timeout_seconds = 3600\n"
            )
        ),
        files={"bin/check.py": "import time\ntime.sleep(60)\n"},
    )
    monkeypatch.setattr(stages_module, "STAGE_TIME_LIMIT_SECONDS", 1)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert "openspec: did not finish (timeout)" in out


@pytest.mark.skipif(
    os.name != "posix", reason="the detached grandchild needs fork and setsid"
)
def test_a_detached_child_holding_the_pipes_does_not_hang_the_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A grandchild outside the group still gets `did not finish (timeout)`.

    Not a spec scenario: the regression the bounded drain guards — a
    child that leaves the process group and keeps the stdout pipe open
    must not hold ``stage run`` past the stage's own limit.
    """
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            isolation=(
                "[isolation]\n"
                "network = false\n"
                "env = []\n"
                'writes = "none"\n'
                "timeout_seconds = 1\n"
            )
        ),
        files={
            "bin/check.py": (
                "import os, time\n"
                "if os.fork() == 0:\n"
                "    os.setsid()\n"
                "    time.sleep(60)\n"
                "    os._exit(0)\n"
                "time.sleep(60)\n"
            )
        },
    )
    monkeypatch.setattr(stages_module, "_DRAIN_TIMEOUT_SECONDS", 1)
    _ci(monkeypatch)
    capsys.readouterr()

    started = time.monotonic()
    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert "openspec: did not finish (timeout)" in out
    # The grandchild keeps the pipe for a minute; an unbounded drain
    # would wait it out.
    assert time.monotonic() - started < 30


# -- the grant ---------------------------------------------------------------


def test_no_grant_on_a_workstation_is_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no grant on a workstation is not run."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(
                ("pre-gate-warn", "bin/warn.py"),
                ("pre-gate-stop", "bin/stop.py"),
            )
        ),
        files={
            "bin/warn.py": "print('w')\n",
            "bin/stop.py": "print('s')\n",
        },
    )
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    out = capsys.readouterr().out
    assert out.count("openspec: not run (not granted)") == 2
    assert "openspec | " not in out


def test_a_grant_matching_the_base_contents_runs_the_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a grant matching the base contents runs the stage."""
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    # The grant is recorded on master's checkout — the extension's contents
    # there are the base's, which is what the run materializes.
    _git(repo, "checkout", "--quiet", "master")
    assert _trust(monkeypatch) == 0
    _git(repo, "checkout", "--quiet", "candidate")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | check ran" in out
    assert "openspec: checked" in out


def test_a_grant_for_different_contents_is_not_run_naming_the_changed_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a grant for different contents is not run naming the changed file."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo, files={"bin/check.py": "print('v1')\n"})
    _commit_all(repo, "base v1")
    assert _trust(monkeypatch) == 0
    # The base moves on: the extension at the new merge base differs from
    # the contents the grant approved.
    _extension(repo, files={"bin/check.py": "print('v2')\n"})
    _commit_all(repo, "base v2")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "openspec: not run (changed after approval: bin/check.py)" in captured.out
    # The line keeps the specification's spelling; the kind of the
    # difference rides on the event instead.
    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    assert len(events) == 1
    assert events[0]["decision"] == "not-run"
    assert events[0]["reason"] == "changed after approval: bin/check.py (changed)"


def test_in_ci_no_grant_is_needed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: in CI no grant is needed."""
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "openspec | check ran" in out
    assert "openspec: checked" in out
    assert not (repo / ".git" / "agentmarshal" / "trust.toml").exists()


def test_a_malformed_trust_toml_fails_the_command_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a malformed trust.toml fails the command naming it."""
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    trust_file = repo / ".git" / "agentmarshal" / "trust.toml"
    trust_file.parent.mkdir(parents=True, exist_ok=True)
    trust_file.write_text("this is not toml [", encoding="utf-8")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 1

    captured = capsys.readouterr()
    assert "trust.toml" in captured.err
    assert "checked" not in captured.out
    assert _events(repo) == []


# -- result lines and the frame ----------------------------------------------


def test_a_checked_stage_prints_its_checked_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a checked stage prints its checked line."""
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    assert "openspec: checked" in capsys.readouterr().out


def test_a_failed_stage_prints_failed_exit_n(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a failed stage prints failed (exit <n>)."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(4)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    assert "openspec: failed (exit 4)" in capsys.readouterr().out


def test_a_timed_out_stage_prints_did_not_finish_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a timed-out stage prints did not finish (timeout)."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            isolation=(
                "[isolation]\n"
                "network = false\n"
                "env = []\n"
                'writes = "none"\n'
                "timeout_seconds = 1\n"
            )
        ),
        files={"bin/check.py": "import time\ntime.sleep(60)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    assert "openspec: did not finish (timeout)" in capsys.readouterr().out


def test_a_stage_that_may_not_run_prints_not_run_reason(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a stage that may not run prints not run (<reason>)."""
    _repo_with_extension(tmp_path, monkeypatch)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    assert "openspec: not run (not granted)" in capsys.readouterr().out


def test_the_extensions_output_is_framed_so_it_cannot_read_as_a_result_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the extension's output is framed so it cannot read as a result line."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={
            "bin/check.py": (
                "print('openspec: checked')\n"
                "print('zzz: failed (exit 1)')\n"
                "print('carries a tab\\there')\n"
            )
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    lines = out.splitlines()
    for line in lines:
        if "openspec: checked" in line or "zzz:" in line:
            assert line.startswith("openspec | ") or line == "openspec: checked"
    # The raw result-line forgery appears only inside the frame; the tab is
    # escaped, not a column break.
    assert "openspec | openspec: checked" in out
    assert "openspec | zzz: failed (exit 1)" in out
    assert "carries a tab\\there" in out
    assert "\there" not in out.split("openspec | carries", 1)[-1]


def test_every_stage_gets_exactly_one_result_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: every stage gets exactly one result line."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo, name="alpha", manifest=_manifest(name="alpha"))
    _extension(
        repo,
        name="beta",
        manifest=_manifest(
            name="beta",
            stages=(
                ("pre-gate-stop", "bin/one.py"),
                ("pre-gate-stop", "bin/two.py"),
            ),
        ),
        files={"bin/one.py": "print(1)\n", "bin/two.py": "print(2)\n"},
    )
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    result_lines = [
        line for line in out.splitlines() if line.startswith(("alpha: ", "beta: "))
    ]
    assert len(result_lines) == 3
    assert result_lines.count("alpha: checked") == 1
    assert result_lines.count("beta: checked") == 2


# -- the extension-event -----------------------------------------------------


def test_each_stages_result_appends_one_extension_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: each stage's result appends one extension-event."""
    repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(
                ("pre-gate-warn", "bin/warn.py"),
                ("pre-gate-stop", "bin/stop.py"),
            )
        ),
        files={
            "bin/warn.py": "import sys\nsys.exit(3)\n",
            "bin/stop.py": "print('ok')\n",
        },
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    assert len(events) == 2
    warn_event = events[0]
    stop_event = events[1]
    assert warn_event["extension"] == "openspec"
    assert warn_event["scope"] == "shared"
    assert warn_event["phase"] == "pre-gate-warn"
    assert warn_event["decision"] == "failed"
    assert warn_event["reason"] == "exit 3"
    assert warn_event["commit"] == candidate
    assert warn_event["task"] == "CR-001"
    assert stop_event["phase"] == "pre-gate-stop"
    assert stop_event["decision"] == "checked"
    assert stop_event["reason"] == ""
    assert "result" not in stop_event


def test_a_post_gate_stages_event_carries_the_result_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a post-gate stage's event carries the result field."""
    repo, _base, _candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("post-gate", "bin/post.py"),)),
        files={"bin/post.py": "import sys\nsys.exit(5)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(phase="post-gate", commit="candidate", base="master") == 0

    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    assert len(events) == 1
    event = events[0]
    assert event["phase"] == "post-gate"
    assert event["decision"] == "failed"
    assert event["result"] == "failed (exit 5)"


def test_a_lost_process_log_is_a_warning_not_a_changed_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a lost process log is a warning, not a changed verdict."""
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    # ``log`` as a file makes ensure_directory refuse the writer open.
    (repo / ".git" / "agentmarshal").mkdir(parents=True, exist_ok=True)
    (repo / ".git" / "agentmarshal" / "log").write_text("x\n", encoding="utf-8")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    assert "process log" in captured.err


# -- the pause ---------------------------------------------------------------


def test_a_failed_pre_gate_stop_stage_pauses_the_process_before_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a failed pre-gate-stop stage pauses the process before the gate."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "paused before the gate" in captured.err
    assert "openspec: failed (exit 2)" in captured.out


def test_a_pre_gate_stop_stage_that_did_not_run_pauses_the_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a pre-gate-stop stage that did not run pauses the process."""
    _repo_with_extension(tmp_path, monkeypatch)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "paused before the gate" in captured.err
    assert "openspec: not run (not granted)" in captured.out


def test_a_failed_pre_gate_warn_stage_warns_and_the_exit_is_0(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a failed pre-gate-warn stage warns and the exit is 0."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("pre-gate-warn", "bin/warn.py"),)),
        files={"bin/warn.py": "import sys\nsys.exit(9)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec: failed (exit 9)" in captured.out
    assert "WARNING" in captured.err
    assert "openspec" in captured.err
    assert "paused" not in captured.err


def test_a_checked_pre_gate_stop_stage_does_not_pause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a checked pre-gate-stop stage does not pause."""
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "paused" not in captured.err
    assert "openspec: checked" in captured.out


def test_a_post_gate_stages_outcome_never_pauses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a post-gate stage's outcome never pauses."""
    _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(
            stages=(
                ("post-gate", "bin/fail.py"),
                ("post-gate", "bin/missing.py"),
            )
        ),
        files={"bin/fail.py": "import sys\nsys.exit(6)\n"},
    )
    _ci(monkeypatch)
    capsys.readouterr()

    # One post-gate stage fails and one does not run — neither pauses.
    assert _stage_run(phase="post-gate", commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "paused" not in captured.err
    assert "openspec: failed (exit 6)" in captured.out
    assert "openspec: not run" in captured.out


# -- registration and the journal ---------------------------------------------


def test_the_stage_group_takes_run_phase_task_commit_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the stage group takes run --phase --task --commit --base."""
    _repo_with_extension(tmp_path, monkeypatch)
    _ci(monkeypatch)
    capsys.readouterr()

    assert (
        main(
            [
                "stage",
                "run",
                "--phase",
                "pre-gate",
                "--task",
                "CR-001",
                "--commit",
                "candidate",
                "--base",
                "master",
            ]
        )
        == 0
    )
    with pytest.raises(SystemExit):
        main(["stage", "bogus"])


def test_the_journal_is_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the journal is untouched."""
    repo, _base, _candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    before = _journal_snapshot(repo)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    capsys.readouterr()
    assert _journal_snapshot(repo) == before


# -- an accepted pause ---------------------------------------------------------


def test_an_accepted_pause_lets_the_process_continue_naming_who_accepted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an accepted pause lets the process continue naming who accepted."""
    _repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    _accept_pause(_repo, commit=candidate)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert (
        "openspec: failed (exit 2), pause accepted by ops-lead "
        "(The pause is understood)" in captured.out
    )
    assert "paused" not in captured.err


def test_an_accepted_pause_stands_down_a_did_not_finish_or_not_run_stage_the_same_way(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an accepted pause stands down a did-not-finish or not-run stage the same way."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _extension(
        repo,
        name="alpha",
        manifest=_manifest(name="alpha", stages=(("pre-gate-stop", "bin/missing.py"),)),
        files={"bin/other.py": "print(1)\n"},
    )
    _extension(
        repo,
        name="beta",
        manifest=_manifest(
            name="beta",
            isolation=(
                "[isolation]\n"
                "network = false\n"
                "env = []\n"
                'writes = "none"\n'
                "timeout_seconds = 1\n"
            ),
        ),
        files={"bin/check.py": "import time\ntime.sleep(60)\n"},
    )
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    candidate = _commit_all(repo, "candidate")
    _accept_pause(repo, extension="alpha", commit=candidate, reason="alpha seen")
    _accept_pause(repo, extension="beta", commit=candidate, reason="beta seen")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert (
        "alpha: not run (command bin/missing.py does not exist), "
        "pause accepted by ops-lead (alpha seen)" in captured.out
    )
    assert (
        "beta: did not finish (timeout), pause accepted by ops-lead "
        "(beta seen)" in captured.out
    )
    assert "paused" not in captured.err


def test_the_latest_matching_acceptance_in_journal_order_is_the_one_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the latest matching acceptance in journal order is the one named."""
    repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    _accept_pause(repo, commit=candidate, party="first", reason="earlier word")
    latest = _accept_pause(repo, commit=candidate, party="second", reason="later word")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "pause accepted by second (later word)" in captured.out
    assert "pause accepted by first" not in captured.out
    record_id = latest.name.removesuffix("-acceptance.json")
    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    (event,) = events
    assert str(event["reason"]).endswith(
        f"pause accepted by acceptance record {record_id}"
    )


def test_an_acceptance_bound_to_another_commit_does_not_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acceptance bound to another commit does not count."""
    repo, base, _candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    _accept_pause(repo, commit=base)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "openspec: failed (exit 2)" in captured.out
    assert "pause accepted" not in captured.out
    assert "paused before the gate" in captured.err


def test_an_acceptance_naming_another_extension_does_not_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acceptance naming another extension does not count."""
    repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    _accept_pause(repo, extension="other", commit=candidate)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "openspec: failed (exit 2)" in captured.out
    assert "pause accepted" not in captured.out
    assert "paused before the gate" in captured.err


def test_an_acceptance_of_another_form_does_not_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an acceptance of another form does not count."""
    repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    journal = repo / ".agentmarshal" / "journal"
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001", "test", candidate, "ops-lead", ["F-1"], "over findings"
        ),
    )
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            candidate,
            "ops-lead",
            None,
            "operational",
            operational=True,
        ),
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "openspec: failed (exit 2)" in captured.out
    assert "pause accepted" not in captured.out
    assert "paused before the gate" in captured.err


def test_an_accepted_pause_lifts_no_other_stages_pause(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an accepted pause lifts no other stage's pause."""
    repo = _project(tmp_path, monkeypatch)
    for name in ("alpha", "beta"):
        _extension(
            repo,
            name=name,
            manifest=_manifest(name=name),
            files={"bin/check.py": "import sys\nsys.exit(2)\n"},
        )
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    candidate = _commit_all(repo, "candidate")
    _accept_pause(repo, extension="alpha", commit=candidate)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert (
        "alpha: failed (exit 2), pause accepted by ops-lead "
        "(The pause is understood)" in captured.out
    )
    beta_lines = [
        line for line in captured.out.splitlines() if line.startswith("beta: ")
    ]
    assert beta_lines == ["beta: failed (exit 2)"]
    pauses = [line for line in captured.err.splitlines() if "paused" in line]
    assert len(pauses) == 1
    assert "beta" in pauses[0]
    assert "alpha" not in pauses[0]


def test_a_checked_stages_line_never_mentions_an_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a checked stage's line never mentions an acceptance."""
    repo, _base, candidate = _repo_with_extension(tmp_path, monkeypatch)
    _accept_pause(repo, commit=candidate)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec: checked" in captured.out
    assert "pause accepted" not in captured.out
    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    (event,) = events
    assert event["reason"] == ""


def test_a_pre_gate_warn_stage_is_unchanged_by_an_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a pre-gate-warn stage is unchanged by an acceptance."""
    repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("pre-gate-warn", "bin/warn.py"),)),
        files={"bin/warn.py": "import sys\nsys.exit(9)\n"},
    )
    _accept_pause(repo, commit=candidate)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec: failed (exit 9)" in captured.out
    assert "pause accepted" not in captured.out
    assert "WARNING" in captured.err
    assert "paused" not in captured.err


def test_a_post_gate_stage_is_unchanged_by_an_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a post-gate stage is unchanged by an acceptance."""
    repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("post-gate", "bin/post.py"),)),
        files={"bin/post.py": "import sys\nsys.exit(5)\n"},
    )
    _accept_pause(repo, commit=candidate)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(phase="post-gate", commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "openspec: failed (exit 5)" in captured.out
    assert "pause accepted" not in captured.out


def test_a_switched_off_stage_is_unchanged_by_an_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a switched-off stage is unchanged by an acceptance."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    (repo / ".agentmarshal" / "switches.toml").write_text(
        "format = 1\n\n"
        "[switches.openspec]\n"
        'state = "off"\n'
        'task = "CR-214"\n'
        'reason = "hangs on empty repositories"\n',
        encoding="utf-8",
    )
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    candidate = _commit_all(repo, "candidate")
    _accept_pause(repo, commit=candidate)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert (
        "openspec: switched off (CR-214, hangs on empty repositories)" in captured.out
    )
    assert "pause accepted" not in captured.out
    assert "paused" not in captured.err


def test_the_extension_event_of_an_accepted_pause_names_the_acceptance_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the extension-event of an accepted pause names the acceptance record."""  # noqa: E501
    repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    path = _accept_pause(repo, commit=candidate)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    capsys.readouterr()
    record_id = path.name.removesuffix("-acceptance.json")
    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    (event,) = events
    assert event["decision"] == "failed"
    assert event["reason"] == (
        f"exit 2; pause accepted by acceptance record {record_id}"
    )
    assert event["commit"] == candidate


def test_a_records_values_are_escaped_on_display(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a record's values are escaped on display."""
    _repo, _base, candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    # A record the reader itself would refuse can still reach the render
    # path — the suffix escapes what it shows regardless.
    record = create_acceptance_record(
        "CR-001",
        "test",
        candidate,
        "ops\nlead",
        None,
        "understood\u2028fine",
        accepted_pause="openspec",
    )
    record["id"] = "01J00000000000000000000000"
    monkeypatch.setattr(stages_module, "read_records", lambda *_args, **_keys: [record])
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "pause accepted by ops\\nlead (understood\\u2028fine)" in captured.out
    assert "\nlead" not in captured.out
    assert "\u2028" not in captured.out


def test_a_journal_that_cannot_be_read_names_it_and_every_pause_stands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a journal that cannot be read names it and every pause stands."""
    repo, _base, _candidate = _repo_with_extension(
        tmp_path,
        monkeypatch,
        files={"bin/check.py": "import sys\nsys.exit(2)\n"},
    )
    # A record the reader cannot parse: the journal answers nothing, so
    # the pause stands — the fallback never lifts one.
    records_dir = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    (records_dir / "01J00000000000000000000000-acceptance.json").write_text(
        "this is not json", encoding="utf-8"
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "openspec: failed (exit 2)" in captured.out
    assert "pause accepted" not in captured.out
    journal_lines = [
        line for line in captured.err.splitlines() if "journal cannot be read" in line
    ]
    assert len(journal_lines) == 1
    assert str(repo / ".agentmarshal" / "journal") in journal_lines[0]
    assert "every pause stands" in journal_lines[0]
    assert "paused before the gate" in captured.err
