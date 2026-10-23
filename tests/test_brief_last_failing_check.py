"""Tests for the brief's last-failing-check section (CR-189; ADR-0017 D2, D3)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.brief import render_last_failing_check
from agentmarshal.journal.records import create_check_record, write_record

_COMMIT_A = "a" * 40
_COMMIT_B = "b" * 40
_COMMIT_C = "c" * 40

_BODY = "\n# CR-001: Brief task\n\nBody sentinel.\n"


@pytest.fixture(autouse=True)
def _actor_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    A check record requires a resolvable recorder, and the ambient
    `AGENTMARSHAL_ACTOR` must not decide whether a test resolves one —
    every test that needs a recorder names the actor itself.
    """

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ci-runner")
    assert main(["init"]) == 0
    assert main(["open", "--title", "Brief task", "--scope", "src/app.py"]) == 0
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        "+++\n"
        "schema = 1\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        'scope = ["src/app.py"]\n'
        'acceptance = ["prints the body"]\n'
        "+++\n"
        f"{_BODY}",
        encoding="utf-8",
    )
    return repo


def _write_check(
    repo: Path,
    record_id: str,
    commit: str,
    name: str,
    result: str,
    **fields: str,
) -> None:
    write_record(
        repo / ".agentmarshal" / "journal",
        "CR-001",
        create_check_record("CR-001", "test", commit, name, result, **fields),
        record_id=record_id,
    )


def _brief(capsys: pytest.CaptureFixture[str]) -> str:
    assert main(["brief", "--task", "CR-001"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    return captured.out


def _section(briefing: str) -> str:
    return briefing.split("## Last failing check\n", 1)[1]


def _expected_brief(body: str) -> str:
    """The brief a task without check records carries, byte for byte."""

    return (
        "You are implementing one governed AgentMarshal task.\n\n"
        "Task id: CR-001\n\n"
        "Declared scope (only these paths may change):\n"
        "- src/app.py\n\n"
        "Acceptance criteria (the definition of done):\n"
        "- prints the body\n\n"
        "Rules enforced by AgentMarshal:\n"
        "- Change only paths declared in the scope above.\n"
        "- Journal records and artifacts are append-only.\n"
        "- Merging requires an approving review of this exact commit.\n\n"
        "Rules the project follows:\n"
        "- Satisfy every acceptance criterion; they are the definition of "
        "done.\n"
        "- Nothing under .agentmarshal/journal/ is the implementer's to edit; "
        "the evidence journal is append-only and is written by agentmarshal "
        "commands. Another file under .agentmarshal/ may change only when the "
        "task's scope names it.\n\n"
        "Contract body (verbatim):\n"
        f"{body}"
    )


def test_the_brief_names_the_last_failing_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the brief names the last failing check."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
        failed_step="pytest",
        excerpt="FAILED test_x",
        run_url="https://ci.example/run/1",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert "- name: unit-tests" in section
    assert "- result: failed" in section
    assert "- commit: aaaaaaa" in section
    assert "- failed_step: pytest" in section
    assert "- run_url: https://ci.example/run/1" in section
    assert "- excerpt: FAILED test_x" in section


def test_an_error_result_is_a_failing_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an error result is a failing check."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "error",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert "- name: unit-tests" in section
    assert "- result: error" in section


def test_the_most_recent_failing_record_is_the_one_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the most recent failing record is the one named."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    _write_check(
        repo,
        "01J00000000000000000000002",
        _COMMIT_B,
        "integration",
        "error",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert "- name: integration" in section
    assert "- result: error" in section
    assert "- commit: bbbbbbb" in section
    assert "- name: unit-tests" not in section
    assert "- commit: aaaaaaa" not in section


def test_the_optional_fields_are_absent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the optional fields are absent."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert "- name: unit-tests" in section
    assert "- result: failed" in section
    assert "- commit: aaaaaaa" in section
    assert "- failed_step:" not in section
    assert "- run_url:" not in section
    assert "- excerpt:" not in section


def test_the_section_says_the_record_is_a_declaration(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the section says the record is a declaration."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert (
        "A check record is the observer's declaration of what the pipeline "
        "found on the commit, not proof of it.\n" in section
    )


def test_a_check_records_values_stay_on_their_own_lines() -> None:
    """Scenario: a check record's values stay on their own lines.

    A check record a journal could still hold — written around the
    writer or under a schema the rules of today cannot reach — can carry
    a character the forgeable-text rule refuses; the renderer escapes it
    rather than letting it add a line.
    """

    section = render_last_failing_check(
        [
            {
                "record_type": "check",
                "name": "unit\ntests",
                "result": "failed",
                "commit": _COMMIT_A,
                "failed_step": "py\u202etest",
                "excerpt": "line one\nline two",
                "run_url": "https://ci.example/\u202erun",
            }
        ]
    )

    assert "- name: unit\\ntests" in section
    assert "- failed_step: py\\u202etest" in section
    assert "- excerpt: line one\\nline two" in section
    assert "- run_url: https://ci.example/\\u202erun" in section
    assert "\u202e" not in section
    # Heading, gap, caveat, gap and six bullets: the section's own lines
    # only — a record's values add none of their own.
    assert section.count("\n") == 10


def test_a_later_pass_on_a_later_commit_is_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a later pass on a later commit is named."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    _write_check(
        repo,
        "01J00000000000000000000002",
        _COMMIT_B,
        "unit-tests",
        "passed",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert (
        "A later check of the same name passed on commit bbbbbbb; "
        "this failure may already be fixed." in section
    )


def test_the_latest_later_pass_is_the_one_named(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the latest later pass is the one named."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    _write_check(
        repo,
        "01J00000000000000000000002",
        _COMMIT_B,
        "unit-tests",
        "passed",
    )
    _write_check(
        repo,
        "01J00000000000000000000003",
        _COMMIT_C,
        "unit-tests",
        "passed",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert "commit ccccccc" in section
    assert "commit bbbbbbb; " not in section


def test_a_pass_on_the_same_commit_is_not_a_fix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a pass on the same commit is not a fix."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    _write_check(
        repo,
        "01J00000000000000000000002",
        _COMMIT_A,
        "unit-tests",
        "passed",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert "- result: failed" in section
    assert "already be fixed" not in section


def test_a_pass_under_another_name_is_not_a_fix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a pass under another name is not a fix."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    _write_check(
        repo,
        "01J00000000000000000000002",
        _COMMIT_B,
        "lint",
        "passed",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert "already be fixed" not in section


def test_a_pass_recorded_before_the_failure_is_not_a_fix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a pass recorded before the failure is not a fix."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_B,
        "unit-tests",
        "passed",
    )
    _write_check(
        repo,
        "01J00000000000000000000002",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    capsys.readouterr()

    section = _section(_brief(capsys))
    assert "already be fixed" not in section


def test_no_check_records_means_no_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: no check records means no section."""

    _repo(tmp_path, monkeypatch)
    capsys.readouterr()

    briefing = _brief(capsys)
    assert "## Last failing check" not in briefing
    assert briefing == _expected_brief(_BODY)


def test_only_passing_and_skipped_checks_mean_no_section(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: only passing and skipped checks mean no section."""

    repo = _repo(tmp_path, monkeypatch)
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "passed",
    )
    _write_check(
        repo,
        "01J00000000000000000000002",
        _COMMIT_B,
        "lint",
        "skipped",
    )
    capsys.readouterr()

    briefing = _brief(capsys)
    assert "## Last failing check" not in briefing
    assert briefing == _expected_brief(_BODY)


def test_the_section_lands_before_the_named_material(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The section follows the contract material; the named material last."""

    repo = _repo(tmp_path, monkeypatch)
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(
            "schema = 1\n", 'schema = 2\ndocuments = ["docs/guide.md"]\n'
        ),
        encoding="utf-8",
    )
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("Guide sentinel.\n", encoding="utf-8")
    _write_check(
        repo,
        "01J00000000000000000000001",
        _COMMIT_A,
        "unit-tests",
        "failed",
    )
    capsys.readouterr()

    briefing = _brief(capsys)
    assert briefing.index("Body sentinel.") < briefing.index("## Last failing check")
    assert briefing.index("## Last failing check") < briefing.index(
        "## Named document: docs/guide.md"
    )
