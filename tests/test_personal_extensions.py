"""The clone's personal extensions and personal switches (CR-233).

ADR-0013 decisions 9, 10 and 11: directory-form manifests under the clone's
``.git/agentmarshal/extensions/<name>/`` — ``LocalState.extensions`` —
run on a workstation through the same ``_run_stage`` path a shared stage
takes, no grant asked, each result line marked ``(personal)`` and each
``extension-event`` scoped ``personal``. The clone's
``switches.toml`` — ``LocalState.switches_file`` — holds the personal
``off`` entries ``extension disable`` writes and ``extension enable``
removes; ``--skip-ext`` on ``stage run`` and ``complete`` passes an
extension over for one run. ``doctor`` lists the personal extensions
after the shared lines and checks each manifest the clone-side way.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.records import read_records
from test_complete_stages import _review
from test_stages import (
    _accept_pause,
    _ci,
    _commit_all,
    _events,
    _extension,
    _git,
    _journal_snapshot,
    _project,
    _repo_with_extension,
    _stage_run,
    _trust,
    _workstation,
)


def _personal_manifest(
    name: str = "mycheck",
    stages: tuple[tuple[str, str], ...] = (("pre-gate-stop", "bin/check.py"),),
    records: tuple[str, ...] = (),
) -> str:
    """A schema-2 directory-form manifest with no footprint fields.

    A personal manifest carries no ``footprint``, ``documents`` or
    ``artifacts`` (ADR-0013 decision 10) — the clone's reader refuses
    one that declares them.
    """

    lines = ["schema = 2", f'name = "{name}"', 'version = "1.0.0"']
    for phase, command in stages:
        lines.extend(["", "[[stage]]", f'phase = "{phase}"', f'command = "{command}"'])
    if records:
        kinds = ", ".join(f'"{kind}"' for kind in records)
        lines.extend(["", "[records]", f"kinds = [{kinds}]"])
    return "\n".join(lines) + "\n"


def _personal_extension(
    repo: Path,
    name: str = "mycheck",
    manifest: str | None = None,
    files: dict[str, str] | None = None,
) -> Path:
    """Write one personal extension under the clone's local state."""

    directory = repo / ".git" / "agentmarshal" / "extensions" / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "manifest.toml").write_text(
        _personal_manifest(name) if manifest is None else manifest,
        encoding="utf-8",
    )
    if files is None:
        files = {"bin/check.py": "print('check ran')\n"}
    for relpath, content in files.items():
        path = directory / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return directory


def _switches_file(repo: Path) -> Path:
    return repo / ".git" / "agentmarshal" / "switches.toml"


def _stage_run_skip(
    *names: str,
    phase: str = "pre-gate",
    task: str = "CR-001",
    commit: str = "HEAD",
    base: str = "master",
) -> int:
    arguments = [
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
    for name in names:
        arguments += ["--skip-ext", name]
    return main(arguments)


def _repo_for_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, str, str]:
    """An open task and commits ahead; no shared extension.

    Returns ``(repo, base, head)``; the checkout stays on ``candidate``.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Loop task", "--scope", "src/"]) == 0
    base = _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "src").mkdir()
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    head = _commit_all(repo, "implement")
    return repo, base, head


def _complete(
    head: str,
    base: str,
    task: str = "CR-001",
    skip: tuple[str, ...] = (),
    target: str | None = None,
    findings: bool = False,
) -> int:
    arguments = ["complete", "--task", task]
    if findings:
        arguments.append("--findings")
    else:
        arguments += [
            "--commit",
            head,
            "--base",
            base,
            "--pipeline-sha",
            head,
        ]
    for name in skip:
        arguments += ["--skip-ext", name]
    if target is not None:
        arguments += ["--target", target]
    return main(arguments)


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _preconditions(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The checks ``doctor`` owes a clean run: workflow, actor, reviewer."""

    workflow = repo / ".github" / "workflows" / "governance.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "jobs:\n  validate:\n    run: agentmarshal validate\n", encoding="utf-8"
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "implementation-agent")
    monkeypatch.setenv(
        "AGENTMARSHAL_REVIEWER_CMD", "reviewer --model {model} {prompt_file}"
    )


# -- the clone's personal extensions' stages run on a workstation -------------


def test_a_personal_extensions_stage_runs_on_a_workstation_without_a_grant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal extension's stage runs on a workstation without a grant."""
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    _personal_extension(repo)
    # The shared extension's grant is given on master's checkout, the way
    # the shared-scope tests record it.
    _git(repo, "checkout", "--quiet", "master")
    assert _trust(monkeypatch) == 0
    _git(repo, "checkout", "--quiet", "candidate")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    assert "mycheck | check ran" in out
    assert "mycheck: checked (personal)" in out
    # The personal pass follows the shared stages at its sorted slot.
    assert out.index("openspec: checked") < out.index("mycheck | check ran")


def test_the_clones_directory_is_what_runs_never_the_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the clone's directory is what runs, never the base."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    # The extension is created after every commit — only the clone's own
    # directory can have supplied it.
    directory = _personal_extension(repo)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    assert "mycheck | check ran" in capsys.readouterr().out
    # And it is the directory the clone holds, reread each run: an edit
    # lands on the next invocation without any commit.
    (directory / "bin" / "check.py").write_text("print('v2')\n", encoding="utf-8")
    assert _stage_run(commit="candidate", base="master") == 0
    assert "mycheck | v2" in capsys.readouterr().out


def test_a_personal_stage_is_invoked_at_the_phase_its_manifest_declares(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal stage is invoked at the phase its manifest declares."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _personal_extension(
        repo,
        manifest=_personal_manifest(stages=(("post-gate", "bin/post.py"),)),
        files={"bin/post.py": "print('post ran')\n"},
    )
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0
    out = capsys.readouterr().out
    assert "mycheck" not in out

    assert _stage_run(phase="post-gate", commit="candidate", base="master") == 0
    out = capsys.readouterr().out
    assert "mycheck | post ran" in out
    assert "mycheck: checked (personal)" in out


def test_no_personal_stage_is_planned_or_printed_in_ci(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no personal stage is planned or printed in CI."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _personal_extension(repo)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert "mycheck" not in captured.out
    assert "mycheck" not in captured.err
    assert "personal" not in captured.out
    assert "personal" not in captured.err
    assert "no shared extension declares a pre-gate stage" in captured.out
    assert _events(repo) == []


def test_complete_runs_the_personal_stages_through_the_shared_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: complete runs the personal stages through the shared runner."""
    repo, base, head = _repo_for_complete(tmp_path, monkeypatch)
    _personal_extension(
        repo,
        manifest=_personal_manifest(
            stages=(
                ("pre-gate-stop", "bin/stop.py"),
                ("post-gate", "bin/post.py"),
            )
        ),
        files={
            "bin/stop.py": "print('stop ran')\n",
            "bin/post.py": "print('post ran')\n",
        },
    )
    _review(head)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    out = capsys.readouterr().out
    # Pre-gate before the gate's transcript; post-gate after the record.
    assert out.index("mycheck | stop ran") < out.index("PASS:")
    assert out.index("mycheck: checked (personal)") < out.index("PASS:")
    assert out.index("completed") < out.index("mycheck | post ran")
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


def test_an_operational_change_runs_no_personal_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an operational change runs no personal stage."""
    repo = _project(tmp_path, monkeypatch)
    # A shared extension whose stage would pause — its command file is
    # missing — must not block the operational CR switching it off.
    _extension(repo, files={})
    base = _commit_all(repo, "base")
    assert main(["extension", "switch", "off", "openspec", "--reason", "hangs"]) == 0
    head = _commit_all(repo, "switch off")
    _personal_extension(repo)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(task="CR-001", commit=head, base=base) == 0

    captured = capsys.readouterr()
    assert "pre-gate stages do not run on an operational change" in captured.out
    assert "mycheck" not in captured.out
    assert "mycheck" not in captured.err
    assert "personal" not in captured.out
    assert "personal" not in captured.err
    assert _events(repo) == []


# -- a personal manifest that cannot be read ----------------------------------


def test_a_personal_manifest_that_cannot_be_read_is_named_on_one_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal manifest that cannot be read is named on one line."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    _personal_extension(repo, manifest="this is not = toml [unclosed\n")
    _personal_extension(repo, name="other", manifest=_personal_manifest(name="other"))
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    line = next(
        line for line in out.splitlines() if line.startswith("mycheck: not run")
    )
    assert line.startswith("mycheck: not run (")
    assert line.endswith("(personal)")
    assert "invalid TOML" in line
    # The run continues past it to the other stages.
    assert "other | check ran" in out
    assert "other: checked (personal)" in out


def test_an_extensions_directory_that_cannot_be_enumerated_is_named_on_one_note_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an extensions directory that cannot be enumerated is named on one note line."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(repo, "candidate")
    state = repo / ".git" / "agentmarshal"
    state.mkdir(parents=True, exist_ok=True)
    (state / "extensions").write_text("a file, not a directory\n", encoding="utf-8")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    captured = capsys.readouterr()
    assert (
        "stage run: note: the clone's personal extensions cannot be enumerated "
        in captured.err
    )
    assert "is not a directory" in captured.err
    assert "no shared extension declares a pre-gate stage" in captured.out


# -- every personal stage's result is marked personal --------------------------


def test_a_checked_personal_stages_line_is_marked_personal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a checked personal stage's line is marked personal."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    assert "mycheck: checked (personal)" in capsys.readouterr().out


def test_a_failed_personal_stages_line_is_marked_personal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a failed personal stage's line is marked personal."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo, files={"bin/check.py": "import sys\nsys.exit(4)\n"})
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 3

    assert "mycheck: failed (exit 4) (personal)" in capsys.readouterr().out


def test_a_pausing_personal_pre_gate_stop_stage_pauses_the_local_run_marked_personal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a pausing personal pre-gate-stop stage pauses the local run marked personal."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    candidate = _commit_all(repo, "candidate")
    _personal_extension(repo, files={"bin/check.py": "import sys\nsys.exit(2)\n"})
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 3

    captured = capsys.readouterr()
    assert "mycheck: failed (exit 2) (personal)" in captured.out
    assert (
        "the process is paused before the gate — "
        "mycheck: failed (exit 2) (personal)" in captured.err
    )

    # An acceptance naming the extension and the run's commit stands it
    # down the shared way.
    _accept_pause(repo, extension="mycheck", commit=candidate)
    assert _stage_run(commit="candidate", base="master") == 0
    captured = capsys.readouterr()
    assert (
        "mycheck: failed (exit 2), pause accepted by ops-lead "
        "(The pause is understood) (personal)" in captured.out
    )
    assert "paused" not in captured.err


def test_a_personal_pre_gate_warn_failure_warns_marked_personal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal pre-gate-warn failure warns marked personal."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(
        repo,
        manifest=_personal_manifest(stages=(("pre-gate-warn", "bin/warn.py"),)),
        files={"bin/warn.py": "import sys\nsys.exit(9)\n"},
    )
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    captured = capsys.readouterr()
    assert "mycheck: failed (exit 9) (personal)" in captured.out
    assert (
        "stage run: WARNING: extension at pre-gate-warn — "
        "mycheck: failed (exit 9) (personal)" in captured.err
    )
    assert "paused" not in captured.err


def test_a_personal_pause_refuses_complete_while_the_candidate_is_not_merged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal pause refuses complete while the candidate is not merged."""
    repo, base, head = _repo_for_complete(tmp_path, monkeypatch)
    _personal_extension(repo, files={"bin/check.py": "import sys\nsys.exit(1)\n"})
    _review(head)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 3

    captured = capsys.readouterr()
    assert (
        "complete: the completion is paused before the gate — "
        "mycheck: failed (exit 1) (personal)" in captured.err
    )
    assert "PASS:" not in captured.out
    assert all(
        record["record_type"] != "completed"
        for record in read_records(_journal(repo), "CR-001")
    )

    # Once the candidate is an ancestor of the target the same pause
    # warns and proceeds — exactly as for a shared stage.
    _git(repo, "branch", "target", "candidate")
    assert _complete(head, base, target="target") == 0
    captured = capsys.readouterr()
    assert (
        "complete: WARNING: extension at pre-gate-stop — "
        "mycheck: failed (exit 1) (personal) — the candidate is already "
        "merged into the target" in captured.err
    )
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


# -- a personal extension named like a shared one is not run -------------------


def test_a_personal_extension_named_like_a_shared_one_is_not_run_and_is_named_on_one_line(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal extension named like a shared one is not run and is named on one line."""  # noqa: E501
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    _personal_extension(repo, name="openspec", manifest=_personal_manifest("openspec"))
    _git(repo, "checkout", "--quiet", "master")
    assert _trust(monkeypatch) == 0
    _git(repo, "checkout", "--quiet", "candidate")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    # The shared extension wins and runs; the personal one is named on
    # one line at its sorted slot and runs no stage.
    assert "openspec | check ran" in out
    assert "openspec: checked" in out
    assert "openspec: not run (a shared extension of this name wins) (personal)" in out
    assert out.index("openspec: checked") < out.index(
        "openspec: not run (a shared extension of this name wins)"
    )


# -- a personal manifest carries no footprint, documents or artifacts ---------


def test_a_personal_manifest_declaring_footprint_documents_or_artifacts_is_refused_and_does_not_run(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal manifest declaring footprint, documents or artifacts is refused and does not run."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    for name, field in (
        ("footext", 'footprint = ["x/"]'),
        ("docext", 'documents = ["x/"]'),
        ("artext", 'artifacts = ["x/"]'),
    ):
        _personal_extension(
            repo,
            name=name,
            manifest=(
                "schema = 2\n"
                f'name = "{name}"\n'
                'version = "1.0.0"\n'
                f"{field}\n"
                "\n"
                "[[stage]]\n"
                'phase = "pre-gate-stop"\n'
                'command = "bin/check.py"\n'
            ),
        )
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    out = capsys.readouterr().out
    for name, field in (
        ("footext", "'footprint'"),
        ("docext", "'documents'"),
        ("artext", "'artifacts'"),
    ):
        line = next(line for line in out.splitlines() if line.startswith(f"{name}: "))
        assert line.startswith(f"{name}: not run (")
        assert field in line
        assert "is not allowed in a personal manifest" in line
        assert line.endswith("(personal)")
    assert "check ran" not in out


def test_doctor_fails_the_check_of_a_personal_manifest_carrying_a_forbidden_field(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: doctor fails the check of a personal manifest carrying a forbidden field."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _personal_extension(
        repo,
        name="footext",
        manifest=(
            "schema = 2\n"
            'name = "footext"\n'
            'version = "1.0.0"\n'
            'footprint = ["x/"]\n'
            "\n"
            "[[stage]]\n"
            'phase = "pre-gate-stop"\n'
            'command = "bin/check.py"\n'
        ),
    )
    capsys.readouterr()

    assert main(["doctor"]) == 1

    captured = capsys.readouterr()
    assert "FAIL: extension manifest footext (personal)" in captured.out
    assert "'footprint'" in captured.out
    assert "is not allowed in a personal manifest" in captured.out
    line = next(
        line
        for line in captured.err.splitlines()
        if line.startswith("extension footext:")
    )
    assert "personal scope" in line
    assert "'footprint'" in line


# -- a personal extension is skippable for a run and switchable off ------------


def test_stage_run_skip_ext_skips_a_personal_extension_for_that_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: stage run --skip-ext skips a personal extension for that run."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run_skip("mycheck", commit="HEAD", base="master") == 0

    captured = capsys.readouterr()
    assert "mycheck: skipped for this run (personal)" in captured.out
    assert "mycheck | " not in captured.out
    # Nothing is written: no switch file, and the next run runs it again.
    assert not _switches_file(repo).exists()
    assert _stage_run(commit="HEAD", base="master") == 0
    assert "mycheck: checked (personal)" in capsys.readouterr().out


def test_complete_skip_ext_skips_a_personal_extension_for_that_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: complete --skip-ext skips a personal extension for that run."""
    repo, base, head = _repo_for_complete(tmp_path, monkeypatch)
    _personal_extension(
        repo,
        manifest=_personal_manifest(
            stages=(
                ("pre-gate-stop", "bin/stop.py"),
                ("post-gate", "bin/post.py"),
            )
        ),
        files={
            "bin/stop.py": "print('stop ran')\n",
            "bin/post.py": "print('post ran')\n",
        },
    )
    _review(head)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base, skip=("mycheck",)) == 0

    captured = capsys.readouterr()
    # The flag reaches both of the runner's phases — the second skipped
    # line is the quiet post-gate run's, after the record.
    assert captured.out.count("mycheck: skipped for this run (personal)") == 2
    assert "mycheck | " not in captured.out
    assert captured.out.index("completed") < captured.out.rindex(
        "mycheck: skipped for this run (personal)"
    )
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"

    # The findings lane takes no --skip-ext at all.
    assert _complete(head, base, skip=("mycheck",), findings=True) == 1
    assert "complete: --findings takes no --skip-ext" in capsys.readouterr().err


def test_extension_disable_writes_the_off_switch_to_the_clones_switches_toml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: extension disable writes the off switch to the clone's switches.toml."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _personal_extension(repo)
    capsys.readouterr()

    assert main(["extension", "disable", "mycheck", "--reason", "too noisy"]) == 0

    out = capsys.readouterr().out
    assert str(_switches_file(repo)) in out
    assert "disabled mycheck" in out
    parsed = tomllib.loads(_switches_file(repo).read_text(encoding="utf-8"))
    assert parsed["format"] == 1
    assert parsed["switches"]["mycheck"] == {
        "state": "off",
        "reason": "too noisy",
    }


def test_a_disabled_personal_extension_prints_disabled_personal_and_does_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a disabled personal extension prints disabled (personal) and does not run."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    assert main(["extension", "disable", "mycheck"]) == 0
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    captured = capsys.readouterr()
    assert "mycheck: disabled (personal)" in captured.out
    assert "mycheck | " not in captured.out
    assert "paused" not in captured.err


def test_extension_enable_removes_the_switch_and_the_extension_runs_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: extension enable removes the switch and the extension runs again."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    assert main(["extension", "disable", "mycheck"]) == 0
    capsys.readouterr()

    assert main(["extension", "enable", "mycheck"]) == 0

    out = capsys.readouterr().out
    assert str(_switches_file(repo)) in out
    assert "enabled mycheck" in out
    # The emptied file still parses — the [switches] table stays.
    parsed = tomllib.loads(_switches_file(repo).read_text(encoding="utf-8"))
    assert parsed["switches"] == {}
    _workstation(monkeypatch)
    assert _stage_run(commit="HEAD", base="master") == 0
    captured = capsys.readouterr()
    assert "mycheck: checked (personal)" in captured.out
    assert "cannot be read" not in captured.err

    # ``enable`` on an extension that is not disabled refuses on one
    # line and writes nothing.
    before = _switches_file(repo).read_bytes()
    assert main(["extension", "enable", "mycheck"]) == 1
    captured = capsys.readouterr()
    assert "extension enable: mycheck is not disabled" in captured.err
    assert _switches_file(repo).read_bytes() == before


# -- the personal switches file ------------------------------------------------


def test_a_missing_personal_switches_file_means_every_personal_extension_is_on(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a missing personal switches file means every personal extension is on."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    assert not _switches_file(repo).exists()
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    captured = capsys.readouterr()
    assert "mycheck: checked (personal)" in captured.out
    assert "disabled" not in captured.out
    assert "skipped" not in captured.out
    assert "switches" not in captured.err


def test_a_personal_switches_file_that_cannot_be_read_leaves_every_personal_extension_on(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal switches file that cannot be read leaves every personal extension on."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    _switches_file(repo).write_bytes(b"this is not = toml [unclosed")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    captured = capsys.readouterr()
    assert (
        "stage run: note: the clone's personal switches cannot be read " in captured.err
    )
    assert "every personal extension is on" in captured.err
    assert "mycheck: checked (personal)" in captured.out


def test_an_entry_naming_no_personal_extension_and_keys_beyond_the_shape_pass_unread(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an entry naming no personal extension and keys beyond the shape pass unread."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    _switches_file(repo).write_text(
        "format = 1\n"
        "\n"
        "[switches]\n"
        "\n"
        "[switches.ghost]\n"
        'state = "off"\n'
        "\n"
        "[switches.mycheck]\n"
        'state = "on"\n'
        'note = "a key the format does not name"\n',
        encoding="utf-8",
    )
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    captured = capsys.readouterr()
    assert "mycheck: checked (personal)" in captured.out
    assert "ghost" not in captured.out
    assert "ghost" not in captured.err
    assert "cannot be read" not in captured.err


# -- a shared extension is never named in a personal switch --------------------


def test_a_shared_name_in_skip_ext_is_refused_before_any_stage_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a shared name in --skip-ext is refused before any stage runs."""
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    _personal_extension(repo)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run_skip("openspec", commit="candidate", base="master") == 1

    captured = capsys.readouterr()
    assert (
        "stage run: openspec: a shared extension is switched off only by "
        "an operational task (extension switch off)" in captured.err
    )
    assert "openspec | " not in captured.out
    assert "mycheck" not in captured.out
    assert _events(repo) == []


def test_a_shared_name_in_extension_disable_is_refused_and_nothing_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a shared name in extension disable is refused and nothing is written."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    capsys.readouterr()

    assert main(["extension", "disable", "openspec"]) == 1

    captured = capsys.readouterr()
    assert (
        "extension disable: openspec: a shared extension is switched off "
        "only by an operational task (extension switch off)" in captured.err
    )
    assert not _switches_file(repo).exists()


def test_a_shared_name_in_extension_enable_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a shared name in extension enable is refused."""
    repo = _project(tmp_path, monkeypatch)
    _extension(repo)
    capsys.readouterr()

    assert main(["extension", "enable", "openspec"]) == 1

    captured = capsys.readouterr()
    assert (
        "extension enable: openspec: a shared extension is switched off "
        "only by an operational task (extension switch off)" in captured.err
    )
    assert not _switches_file(repo).exists()


def test_a_name_no_personal_extension_declares_is_inert_for_skip_ext_and_refused_by_disable(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a name no personal extension declares is inert for --skip-ext and refused by disable."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run_skip("ghost", commit="HEAD", base="master") == 0

    captured = capsys.readouterr()
    assert "mycheck: checked (personal)" in captured.out
    assert "ghost" not in captured.out
    assert "ghost" not in captured.err

    assert main(["extension", "disable", "ghost"]) == 1
    captured = capsys.readouterr()
    assert "extension disable: ghost is not a personal extension" in captured.err
    assert not _switches_file(repo).exists()


# -- doctor lists personal extensions with the personal scope ------------------


def test_doctor_lists_a_personal_extension_with_the_scope_personal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: doctor lists a personal extension with the scope personal."""
    repo = _project(tmp_path, monkeypatch)
    _preconditions(repo, monkeypatch)
    _personal_extension(repo)
    capsys.readouterr()

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    assert (
        "extension mycheck: personal scope, directory form, manifest "
        "schema 2, stages: pre-gate-stop, ext kinds: none" in captured.err
    )
    assert "OK: extension manifest mycheck (personal)" in captured.out


def test_doctor_names_a_disabled_personal_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: doctor names a disabled personal extension."""
    repo = _project(tmp_path, monkeypatch)
    _preconditions(repo, monkeypatch)
    _personal_extension(repo)
    assert main(["extension", "disable", "mycheck"]) == 0
    capsys.readouterr()

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    line = next(
        line
        for line in captured.err.splitlines()
        if line.startswith("extension mycheck:")
    )
    assert line.endswith(", disabled")
    assert "personal scope" in line


def test_a_personal_switches_file_the_parse_refuses_is_named_on_one_line_and_fails_nothing(  # noqa: E501
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal switches file the parse refuses is named on one line and fails nothing."""  # noqa: E501
    repo = _project(tmp_path, monkeypatch)
    _preconditions(repo, monkeypatch)
    _personal_extension(repo)
    _switches_file(repo).write_bytes(b"this is not = toml [unclosed")
    capsys.readouterr()

    assert main(["doctor"]) == 0

    captured = capsys.readouterr()
    assert "personal switches: unavailable (" in captured.err
    line = next(
        line
        for line in captured.err.splitlines()
        if line.startswith("extension mycheck:")
    )
    assert "disabled" not in line
    assert "FAIL" not in captured.out


# -- a clone with no personal extension prints exactly what it prints today ----


def test_a_clone_with_no_personal_extension_prints_exactly_what_it_prints_today(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a clone with no personal extension prints exactly what it prints today."""  # noqa: E501
    repo, base, head = _repo_for_complete(tmp_path, monkeypatch)
    _review(head)
    _workstation(monkeypatch)
    capsys.readouterr()

    # No ``.git/agentmarshal/extensions`` exists at all. (The temp
    # directory's own name contains "personal", so the assertions are on
    # the scope's marks, not the bare word.)
    marks = (
        " (personal)",
        "personal scope",
        "personal switches",
        "personal extensions",
    )
    assert _stage_run(commit=head, base=base) == 0
    captured = capsys.readouterr()
    assert all(mark not in captured.out for mark in marks)
    assert all(mark not in captured.err for mark in marks)
    assert "no shared extension declares a pre-gate stage" in captured.out

    assert _complete(head, base) == 0
    captured = capsys.readouterr()
    assert all(mark not in captured.out for mark in marks)
    assert all(mark not in captured.err for mark in marks)
    assert captured.out.endswith("completed\n")

    _preconditions(repo, monkeypatch)
    assert main(["doctor"]) == 0
    captured = capsys.readouterr()
    assert all(mark not in captured.out for mark in marks)
    assert all(mark not in captured.err for mark in marks)
    assert "extensions: none" in captured.err


def test_the_personal_scope_adds_no_mark_to_a_shared_stages_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the personal scope adds no mark to a shared stage's line."""
    repo, _base, _candidate = _repo_with_extension(tmp_path, monkeypatch)
    _personal_extension(repo)
    _git(repo, "checkout", "--quiet", "master")
    assert _trust(monkeypatch) == 0
    _git(repo, "checkout", "--quiet", "candidate")
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    out = capsys.readouterr().out
    lines = out.splitlines()
    assert "openspec: checked" in lines
    assert "openspec: checked (personal)" not in lines
    assert "mycheck: checked (personal)" in lines


def test_a_personal_extension_declaring_no_matching_stage_prints_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal extension declaring no matching stage prints nothing."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(
        repo,
        manifest=_personal_manifest(stages=(("post-gate", "bin/post.py"),)),
        files={"bin/post.py": "print('post ran')\n"},
    )
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    captured = capsys.readouterr()
    assert "mycheck" not in captured.out
    assert "mycheck" not in captured.err
    assert "no shared extension declares a pre-gate stage" in captured.out
    assert _events(repo) == []


# -- a personal extension has no journal authority -----------------------------


def test_record_ext_refuses_a_kind_only_a_personal_manifest_declares(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: record-ext refuses a kind only a personal manifest declares."""
    repo = _project(tmp_path, monkeypatch)
    _personal_extension(
        repo,
        manifest=_personal_manifest(stages=(), records=("mycheck/thing@1",)),
        files={},
    )
    _commit_all(repo, "base")
    assert main(["open", "--title", "Task", "--scope", "src/"]) == 0
    payload = tmp_path / "payload.json"
    payload.write_text(json.dumps({"outcome": "clean"}), encoding="utf-8")
    capsys.readouterr()

    assert (
        main(
            [
                "record-ext",
                "--task",
                "CR-001",
                "--commit",
                "HEAD",
                "--kind",
                "mycheck/thing@1",
                "--payload-file",
                str(payload),
            ]
        )
        == 1
    )

    captured = capsys.readouterr()
    assert "record-ext:" in captured.err
    assert "mycheck" in captured.err
    assert all(
        record["record_type"] != "ext"
        for record in read_records(_journal(repo), "CR-001")
    )


def test_a_personal_stages_extension_event_carries_the_personal_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal stage's extension-event carries the personal scope."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "x.txt").write_text("x\n", encoding="utf-8")
    candidate = _commit_all(repo, "candidate")
    _personal_extension(repo)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="candidate", base="master") == 0

    capsys.readouterr()
    events = [event for event in _events(repo) if event["event"] == "extension-event"]
    (event,) = events
    assert event["extension"] == "mycheck"
    assert event["scope"] == "personal"
    assert event["phase"] == "pre-gate-stop"
    assert event["decision"] == "checked"
    assert event["reason"] == ""
    assert event["commit"] == candidate
    assert event["task"] == "CR-001"


def test_a_personal_stage_writes_nothing_to_the_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a personal stage writes nothing to the journal."""
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(repo)
    before = _journal_snapshot(repo)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    capsys.readouterr()
    assert _journal_snapshot(repo) == before
    events = _events(repo)
    (event,) = events
    assert event["event"] == "extension-event"
    assert event["scope"] == "personal"


# -- not a spec scenario --------------------------------------------------------


def test_an_earlier_personal_stage_cannot_rewrite_a_later_stages_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Not a spec scenario: the personal copy is per-stage like the shared
    one, so a stage reaching its own copy through ``__file__`` cannot
    rewrite a later stage's command file.
    """
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    _personal_extension(
        repo,
        manifest=_personal_manifest(
            stages=(
                ("pre-gate-warn", "bin/first.py"),
                ("pre-gate-stop", "bin/second.py"),
            )
        ),
        files={
            "bin/first.py": (
                "from pathlib import Path\n"
                "target = Path(__file__).resolve().parents[1] / 'bin' / 'second.py'\n"
                "target.write_text(\"print('REWRITTEN')\\n\", encoding='utf-8')\n"
                "print('first ran')\n"
            ),
            "bin/second.py": "print('SOURCE SECOND')\n",
        },
    )
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    out = capsys.readouterr().out
    assert "mycheck | first ran" in out
    assert "mycheck | SOURCE SECOND" in out
    assert "REWRITTEN" not in out
    # The clone's own file is untouched too.
    source = (
        repo / ".git" / "agentmarshal" / "extensions" / "mycheck" / "bin" / "second.py"
    )
    assert "SOURCE SECOND" in source.read_text(encoding="utf-8")


def test_a_symlinked_personal_extension_directory_is_named_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Not a spec scenario: a link at the personal directory is refused
    the manifest reader's way — one ``not run`` line, no stage.
    """
    repo = _project(tmp_path, monkeypatch)
    _commit_all(repo, "base")
    real = _personal_extension(repo, name="real")
    link = repo / ".git" / "agentmarshal" / "extensions" / "mycheck"
    link.symlink_to(real, target_is_directory=True)
    _workstation(monkeypatch)
    capsys.readouterr()

    assert _stage_run(commit="HEAD", base="master") == 0

    out = capsys.readouterr().out
    line = next(
        line for line in out.splitlines() if line.startswith("mycheck: not run")
    )
    assert "symlink" in line
    assert line.endswith("(personal)")
    assert "real | check ran" in out
    assert "real: checked (personal)" in out
