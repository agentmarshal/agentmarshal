"""``complete`` runs the declared extension stages around its gate.

ADR-0013 decision 2: ``complete --task --commit --base`` invokes the
shared stage runner once for ``pre-gate`` before the gate check and any
journal write, and once for ``post-gate`` after the ``completed``
record — the same run ``stage run`` performs, rendered by the caller.

Every scenario the delta spec names is exercised by one test whose
docstring names it.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import NoReturn, TextIO

import pytest

import agentmarshal.stages as stages_module
import test_stages as stage_helpers
from agentmarshal.cli import main
from agentmarshal.journal.placement import Placement
from agentmarshal.journal.records import read_records
from agentmarshal.localstate import LocalState
from agentmarshal.process_log import read_events
from test_stages import _commit_all, _extension, _git, _manifest

_REVIEWER_EMAIL = "reviewer@test.invalid"


def _repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    manifest: str | None = None,
    files: dict[str, str] | None = None,
    name: str = "openspec",
) -> tuple[Path, str, str]:
    """An open task and the extension committed at base; candidate ahead.

    Returns ``(repo, base, head)``; the checkout stays on ``candidate``.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Loop task", "--scope", "src/"]) == 0
    _extension(repo, name=name, manifest=manifest, files=files)
    base = _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "src").mkdir()
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    head = _commit_all(repo, "implement")
    return repo, base, head


def _review(head: str, task: str = "CR-001") -> None:
    assert (
        main(
            [
                "submit-review",
                "--task",
                task,
                "--commit",
                head,
                "--verdict",
                "approved",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                _REVIEWER_EMAIL,
            ]
        )
        == 0
    )


def _complete(
    head: str,
    base: str,
    task: str = "CR-001",
    pipeline: str | None = None,
    target: str | None = None,
) -> int:
    arguments = [
        "complete",
        "--task",
        task,
        "--commit",
        head,
        "--base",
        base,
        "--pipeline-sha",
        head if pipeline is None else pipeline,
    ]
    if target is not None:
        arguments += ["--target", target]
    return main(arguments)


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _events(repo: Path) -> list[dict[str, object]]:
    return read_events(LocalState(repo / ".git" / "agentmarshal"))


def _ci(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CI", "true")


_FAILING = {"bin/check.py": "import sys\nprint('check ran')\nsys.exit(1)\n"}


# -- the one runner ------------------------------------------------------------


def test_stage_runs_transcript_is_unchanged_by_the_shared_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: stage run's transcript is unchanged by the shared runner."""
    _repo_path, base, head = _repo(tmp_path, monkeypatch, files=_FAILING)
    _ci(monkeypatch)
    capsys.readouterr()

    assert stage_helpers._stage_run(task="CR-001", commit=head, base=base) == 3
    captured = capsys.readouterr()
    assert "openspec | check ran" in captured.out
    assert "openspec: failed (exit 1)" in captured.out
    assert (
        "stage run: the process is paused before the gate — "
        "openspec: failed (exit 1)" in captured.err
    )

    (tmp_path / "second").mkdir()
    bare = stage_helpers._project(tmp_path / "second", monkeypatch)
    (bare / "x.txt").write_text("x\n", encoding="utf-8")
    _commit_all(bare, "init")
    capsys.readouterr()

    assert stage_helpers._stage_run(commit="HEAD", base="master") == 0
    out = capsys.readouterr().out
    assert "stage run: no shared extension declares a pre-gate stage" in out


def test_both_commands_go_through_the_one_runner(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: both commands go through the one runner."""
    repo, base, head = _repo(tmp_path, monkeypatch)
    _review(head)
    _ci(monkeypatch)
    calls: list[tuple[str, bool]] = []
    original = stages_module.run_stages

    def spy(
        placement: Placement,
        state: LocalState,
        task_id: str,
        commit: str,
        base_ref: str,
        phase: str,
        stderr: TextIO,
        *,
        quiet: bool = False,
    ) -> stages_module.StageRunResult:
        calls.append((phase, quiet))
        return original(
            placement, state, task_id, commit, base_ref, phase, stderr, quiet=quiet
        )

    monkeypatch.setattr(stages_module, "run_stages", spy)
    capsys.readouterr()

    assert stage_helpers._stage_run(task="CR-001", commit=head, base=base) == 0
    assert _complete(head, base) == 0
    assert calls == [
        ("pre-gate", False),
        ("pre-gate", True),
        ("post-gate", True),
    ]
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


# -- pre-gate before the gate ---------------------------------------------------


def test_the_pre_gate_stages_run_before_the_gates_transcript_and_before_any_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the pre-gate stages run before the gate's transcript and before any write."""  # noqa: E501
    repo, base, head = _repo(tmp_path, monkeypatch)
    _review(head)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    out = capsys.readouterr().out
    assert out.index("openspec | check ran") < out.index("PASS:")
    assert out.index("openspec: checked") < out.index("PASS:")
    records = read_records(_journal(repo), "CR-001")
    assert records[-1]["record_type"] == "completed"


def test_a_run_whose_machinery_refused_refuses_the_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a run whose machinery refused refuses the completion."""
    repo, base, head = _repo(
        tmp_path,
        monkeypatch,
        # A well-formed schema-1 manifest in the directory form: the base's
        # manifest read refuses, which is the run's own machinery failing.
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
    )
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 1

    captured = capsys.readouterr()
    assert "openspec" in captured.err
    assert "complete: pre-gate stage run refused; task not completed" in captured.err
    assert "PASS:" not in captured.out
    assert all(
        record["record_type"] != "completed"
        for record in read_records(_journal(repo), "CR-001")
    )


def test_a_plan_matching_no_stage_prints_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a plan matching no stage prints nothing."""
    repo, base, head = _repo(
        tmp_path,
        monkeypatch,
        # A shared extension declaring no stage at all: both runs reach an
        # empty plan and the no-stage line is the caller's to withhold.
        manifest=(
            "schema = 2\n"
            'name = "openspec"\n'
            'version = "1.0.0"\n'
            'footprint = ["x/"]\n'
            "documents = []\n"
        ),
    )
    _review(head)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert "stage run:" not in captured.out
    assert "openspec" not in captured.out
    assert captured.out.endswith("completed\n")
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


def test_an_operational_changes_completion_skips_the_pre_gate_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an operational change's completion skips the pre-gate stages."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    # A stage that would pause — the manifest names a file the directory
    # does not hold — must not block the operational CR switching it off.
    _extension(repo, files={})
    base = _commit_all(repo, "base")
    assert main(["extension", "switch", "off", "openspec", "--reason", "hangs"]) == 0
    head = _commit_all(repo, "switch off")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    captured = capsys.readouterr()
    assert (
        "stage run: pre-gate stages do not run on an operational change" in captured.out
    )
    assert "openspec: not run" not in captured.out
    assert "paused" not in captured.err
    assert captured.out.endswith("completed\n")
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


def test_an_operational_change_with_no_stage_to_skip_prints_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an operational change with no stage to skip prints nothing."""
    repo = stage_helpers._project(tmp_path, monkeypatch)
    # The shared extension's manifest declares no stage at all, so no
    # pre-gate stage would run even off the operational lane — and the
    # invocation owes no line at all, not even the operational one.
    _extension(
        repo,
        manifest=(
            "schema = 2\n"
            'name = "openspec"\n'
            'version = "1.0.0"\n'
            'footprint = ["x/"]\n'
            "documents = []\n"
        ),
        files={},
    )
    base = _commit_all(repo, "base")
    assert main(["extension", "switch", "off", "openspec", "--reason", "unused"]) == 0
    head = _commit_all(repo, "switch off")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    captured = capsys.readouterr()
    assert "stage run:" not in captured.out
    assert "stage run:" not in captured.err
    assert "openspec" not in captured.out
    assert captured.out.endswith("completed\n")
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


def test_an_unresolvable_ref_is_refused_as_complete_refuses_it_today(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unresolvable ref is refused as complete refuses it today."""
    repo, base, head = _repo(tmp_path, monkeypatch, files=_FAILING)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete("no-such-ref", base) == 1
    assert _complete(head, "no-such-base") == 1

    captured = capsys.readouterr()
    # The refusal is the gate's own resolution failure under complete's
    # voice, before any extension line — the stage machinery is never
    # reached and nothing is written.
    lines = captured.err.splitlines()
    assert lines[0].startswith("git rev-parse --verify no-such-ref^{commit} failed:")
    assert lines[1].startswith("git rev-parse --verify no-such-base^{commit} failed:")
    assert "stage run:" not in captured.out
    assert "stage run:" not in captured.err
    assert "openspec" not in captured.out
    assert all(
        record["record_type"] != "completed"
        for record in read_records(_journal(repo), "CR-001")
    )


def test_the_findings_lane_invokes_no_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the findings lane invokes no stage."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    _git(repo, "config", "user.name", "Recorder")
    _git(repo, "config", "user.email", "recorder@test.invalid")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "researcher")
    assert main(["init"]) == 0
    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["capture"] = {"overrides": {"reviews": "commit"}}
    project["actors"] = {"researcher": {"git_identities": ["recorder@test.invalid"]}}
    project_path.write_text(json.dumps(project), encoding="utf-8")
    _extension(repo)
    assert main(["open", "--title", "Research"]) == 0
    _commit_all(repo, "base")
    _ci(monkeypatch)

    artifact = repo / "evidence" / "result.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("conclusion\n", encoding="utf-8")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert (
        main(
            [
                "finding",
                "--task",
                "CR-001",
                "--summary",
                "The conclusion",
                "--artifact",
                f"evidence/result.md={digest}",
            ]
        )
        == 0
    )
    finding = str(read_records(_journal(repo), "CR-001")[-1]["id"])
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--reviewed-finding",
                finding,
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
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert main(["complete", "--task", "CR-001", "--findings"]) == 0

    captured = capsys.readouterr()
    assert "stage run:" not in captured.out
    assert "stage run:" not in captured.err
    assert "openspec" not in captured.out
    assert "completed through findings" in captured.out
    assert not [event for event in _events(repo) if event["event"] == "extension-event"]


def test_a_sidecar_invokes_no_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a sidecar invokes no stage."""
    host = tmp_path / "host"
    host.mkdir()
    _git(host, "init", "--quiet", "-b", "master")
    _extension(host)
    (host / "src").mkdir()
    base = _commit_all(host, "base")
    (host / "src" / "change.py").write_text("change\n", encoding="utf-8")
    head = _commit_all(host, "implement")

    sidecar = tmp_path / "sidecar"
    sidecar.mkdir()
    _git(sidecar, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    assert main(["open", "--title", "Sidecar task", "--scope", "src/"]) == 0
    _review(head)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    captured = capsys.readouterr()
    assert "completed after advisory checks; decides no merge" in captured.out
    assert "stage run:" not in captured.out
    assert "stage run:" not in captured.err
    assert "openspec" not in captured.out
    assert not [
        event
        for event in read_events(LocalState(sidecar / ".git" / "agentmarshal"))
        if event["event"] == "extension-event"
    ]


def test_the_stages_environment_is_the_resolved_candidates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the stage's environment is the resolved candidate's."""
    _repo_path, base, head = _repo(
        tmp_path,
        monkeypatch,
        files={
            "bin/check.py": (
                "import os\n"
                "print('PHASE', os.environ['AGENTMARSHAL_PHASE'])\n"
                "print('TASK', os.environ['AGENTMARSHAL_TASK'])\n"
                "print('COMMIT', os.environ['AGENTMARSHAL_COMMIT'])\n"
                "print('BASE', os.environ['AGENTMARSHAL_BASE'])\n"
                "print('IN_SNAPSHOT', os.path.exists('src/module.py'))\n"
            )
        },
    )
    _review(head)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete("candidate", "master", pipeline=head) == 0

    out = capsys.readouterr().out
    assert "openspec | PHASE pre-gate" in out
    assert "openspec | TASK CR-001" in out
    assert f"openspec | COMMIT {head}" in out
    assert f"openspec | BASE {base}" in out
    assert "openspec | IN_SNAPSHOT True" in out


# -- the pause, refused or warned -----------------------------------------------


def test_a_pause_while_the_candidate_is_not_an_ancestor_refuses_the_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a pause while the candidate is not an ancestor refuses the completion."""  # noqa: E501
    repo, base, head = _repo(tmp_path, monkeypatch, files=_FAILING)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 3

    captured = capsys.readouterr()
    assert "openspec | check ran" in captured.out
    assert "openspec: failed (exit 1)" in captured.out
    assert (
        "complete: the completion is paused before the gate — "
        "openspec: failed (exit 1)" in captured.err
    )
    assert "PASS:" not in captured.out
    records = read_records(_journal(repo), "CR-001")
    assert all(record["record_type"] != "completed" for record in records)
    assert not [
        event
        for event in _events(repo)
        if event["event"] == "extension-event" and event["phase"] == "post-gate"
    ]


def test_the_pause_line_names_every_paused_stage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the pause line names every paused stage."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert main(["open", "--title", "Loop task", "--scope", "src/"]) == 0
    _extension(
        repo,
        name="alpha",
        manifest=_manifest(name="alpha"),
        files=_FAILING,
    )
    _extension(
        repo,
        name="zeta",
        manifest=_manifest(name="zeta"),
        files=_FAILING,
    )
    base = _commit_all(repo, "base")
    _git(repo, "checkout", "--quiet", "-b", "candidate")
    (repo / "src").mkdir()
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    head = _commit_all(repo, "implement")
    _ci(monkeypatch)
    capsys.readouterr()

    # A ``--target`` that cannot resolve reads as not merged — the pause
    # stands rather than being silently lifted.
    assert _complete(head, base, target="no-such-branch") == 3

    err = capsys.readouterr().err
    line = next(
        entry
        for entry in err.splitlines()
        if "the completion is paused before the gate" in entry
    )
    assert line.index("alpha: failed (exit 1)") < line.index("zeta: failed (exit 1)")
    assert all(
        record["record_type"] != "completed"
        for record in read_records(_journal(repo), "CR-001")
    )


def test_a_pause_on_an_already_merged_candidate_is_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a pause on an already-merged candidate is a warning."""
    repo, base, head = _repo(tmp_path, monkeypatch, files=_FAILING)
    _review(head)
    # The candidate is already on the target: ``master`` is moved onto
    # the candidate commit, so ``--is-ancestor`` answers yes. ``--base``
    # still names the pre-merge merge base — what the gate diffs
    # against — which a merge wrapper passes even after the merge.
    _git(repo, "branch", "-f", "master", "candidate")
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base, target="master") == 0

    captured = capsys.readouterr()
    assert "openspec | check ran" in captured.out
    assert "openspec: failed (exit 1)" in captured.out
    assert (
        "complete: WARNING: extension at pre-gate-stop — "
        "openspec: failed (exit 1) — the candidate is already merged into "
        "the target" in captured.err
    )
    assert "the completion is paused" not in captured.err
    assert captured.out.endswith("completed\n")
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


def test_an_accepted_pause_stands_down_in_complete_as_in_stage_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an accepted pause stands down in complete as in stage run."""
    repo, base, head = _repo(tmp_path, monkeypatch, files=_FAILING)
    _review(head)
    stage_helpers._accept_pause(repo, commit=head)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    captured = capsys.readouterr()
    assert "pause accepted by ops-lead" in captured.out
    assert "the completion is paused" not in captured.err
    assert "WARNING" not in captured.err
    assert captured.out.endswith("completed\n")
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


# -- post-gate after the record ---------------------------------------------------


def test_the_post_gate_stages_run_after_the_completed_record_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the post-gate stages run after the completed record is written."""
    repo, base, head = _repo(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("post-gate", "bin/post.py"),)),
        files={"bin/post.py": "print('post ran')\n"},
    )
    _review(head)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    out = capsys.readouterr().out
    assert out.index("completed") < out.index("openspec | post ran")
    assert out.index("completed") < out.index("openspec: checked")
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"
    (event,) = [event for event in _events(repo) if event["event"] == "extension-event"]
    assert event["phase"] == "post-gate"
    assert event["decision"] == "checked"


def test_a_post_gate_result_changes_neither_the_record_nor_the_exit_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a post-gate result changes neither the record nor the exit status."""
    repo, base, head = _repo(
        tmp_path,
        monkeypatch,
        manifest=_manifest(stages=(("post-gate", "bin/post.py"),)),
        files={"bin/post.py": "import sys\nprint('post ran')\nsys.exit(9)\n"},
    )
    _review(head)
    _ci(monkeypatch)
    capsys.readouterr()

    assert _complete(head, base) == 0

    out = capsys.readouterr().out
    assert "openspec | post ran" in out
    assert "openspec: failed (exit 9)" in out
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"


def test_a_post_gate_run_that_raises_leaves_the_completion_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Not a spec scenario: a post-gate run that raises — the stage's
    temporary directory is created inside the runner — is reported on one
    stderr line and changes neither the record nor the exit status
    (CR-225 F3)."""
    repo, base, head = _repo(
        tmp_path,
        monkeypatch,
        # Only a post-gate stage: the pre-gate plan is empty, so the run's
        # temporary directory is first asked for after ``completed``.
        manifest=_manifest(stages=(("post-gate", "bin/post.py"),)),
        files={"bin/post.py": "print('post ran')\n"},
    )
    _review(head)
    _ci(monkeypatch)

    def refuse(*_args: object, **_keys: object) -> NoReturn:
        raise OSError("no space left on device")

    monkeypatch.setattr(tempfile, "TemporaryDirectory", refuse)
    capsys.readouterr()

    assert _complete(head, base) == 0

    captured = capsys.readouterr()
    assert captured.out.endswith("completed\n")
    assert "post ran" not in captured.out
    assert captured.err.splitlines() == [
        "complete: the post-gate stage run could not finish (no space left on device)"
    ]
    assert read_records(_journal(repo), "CR-001")[-1]["record_type"] == "completed"
