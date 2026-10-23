"""Tests for the gate's declared-assignment membership checks (ADR-0018 D3).

A schema-3 contract's `reviewers` and `implementers` name the declared
actors permitted to review and to implement; the gate prints one line per
declared list, judging the latest review's `reviewer.actor` and every
in-range implementer session's `actor` by exact string equality — the
comparison `status` makes — and refuses where membership cannot be shown.
"""

import json
from pathlib import Path

import pytest

from agentmarshal.cli import main
from test_gate import (
    GATE_FIXTURES,
    _approve,
    _commit_all,
    _compare_transcript,
    _gate_arguments,
    _git,
    _implement,
    _run_values,
)
from test_gate_independence import _run, _session, _submit


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _write_contract(
    repo: Path,
    scope: list[str],
    *,
    implementers: list[str] | None = None,
    reviewers: list[str] | None = None,
    independence: list[str] | None = None,
) -> None:
    """Overwrite the opened task's contract with a schema-3 header."""

    path = _journal(repo) / "tasks" / "CR-001" / "contract.md"
    fields = [
        "+++",
        "schema = 3",
        'id = "CR-001"',
        'title = "Gate task"',
        f"scope = {json.dumps(scope)}",
        "acceptance = []",
    ]
    for field, value in (
        ("implementers", implementers),
        ("reviewers", reviewers),
        ("independence", independence),
    ):
        if value is not None:
            fields.append(f"{field} = {json.dumps(value)}")
    path.write_text("\n".join((*fields, "+++", "", "Body.\n")), encoding="utf-8")


def _membership_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scope: list[str],
    *,
    implementers: list[str] | None = None,
    reviewers: list[str] | None = None,
    independence: list[str] | None = None,
    actors: tuple[str, ...] = (),
    name: str = "repo",
) -> tuple[Path, str]:
    """Repo with a schema-3 contract — and any actors table — committed at base."""

    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["capture"] = {"overrides": {"reviews": "commit"}}
    if actors:
        project["actors"] = {actor_id: {"git_identities": []} for actor_id in actors}
    project_path.write_text(json.dumps(project), encoding="utf-8")
    arguments = ["open", "--title", "Gate task"]
    for entry in scope:
        arguments.extend(["--scope", entry])
    assert main(arguments) == 0
    _write_contract(
        repo,
        scope,
        implementers=implementers,
        reviewers=reviewers,
        independence=independence,
    )
    base = _commit_all(repo, "open task")
    return repo, base


def _membership_lines(output: str) -> list[str]:
    return [
        line
        for line in output.splitlines()
        if "declared reviewers" in line or "declared implementers" in line
    ]


def test_a_reviewer_actor_in_the_declared_list_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a reviewer actor in the declared list passes."""

    repo, base = _membership_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        reviewers=["reviewer-one", "reviewer-two"],
    )
    head = _implement(repo, "src/module.py")
    _submit(repo, head, actor="reviewer-one")

    passed, output = _run(repo, head, base)

    assert passed
    assert (
        "PASS: reviewer actor 'reviewer-one' is in the contract's "
        "declared reviewers" in output
    )


def test_a_reviewer_actor_outside_the_list_refuses_naming_the_actor_and_the_list(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a reviewer outside the list refuses naming the actor and the list."""

    repo, base = _membership_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        reviewers=["reviewer-one", "reviewer-two"],
    )
    head = _implement(repo, "src/module.py")
    _submit(repo, head, actor="stranger")

    passed, output = _run(repo, head, base)

    assert not passed
    assert (
        "FAIL: reviewer actor 'stranger' is not in the contract's "
        "declared reviewers: reviewer-one, reviewer-two" in output
    )


def test_reviewer_membership_compares_actor_ids_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: reviewer membership compares actor ids exactly."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], reviewers=["reviewer-one"]
    )
    head = _implement(repo, "src/module.py")
    _submit(repo, head, actor="Reviewer-One")

    passed, output = _run(repo, head, base)

    assert not passed
    assert "FAIL: reviewer actor 'Reviewer-One' is not in" in output


def test_a_review_carrying_no_actor_refuses_saying_the_review_is_recorded_with_actor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a review carrying no actor refuses naming the --actor path."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], reviewers=["reviewer-one"]
    )
    head = _implement(repo, "src/module.py")
    _submit(repo, head)  # no --actor: the review carries no reviewer.actor

    passed, output = _run(repo, head, base)

    assert not passed
    assert "FAIL: the latest review carries no 'reviewer.actor'" in output
    assert "the review is recorded with --actor" in output


def test_the_review_judged_is_the_latest_whatever_its_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the review judged is the latest whatever its verdict."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], reviewers=["reviewer-one"]
    )
    head = _implement(repo, "src/module.py")
    _submit(repo, head, actor="reviewer-one")
    _submit(
        repo,
        head,
        actor="outsider",
        verdict="changes_required",
        findings=("F-1",),
    )

    passed, output = _run(repo, head, base)

    assert not passed
    assert "FAIL: reviewer actor 'outsider' is not in" in output


def test_without_a_review_the_reviewers_line_reads_not_examined(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: without a review the reviewers line reads not examined."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], reviewers=["reviewer-one"]
    )
    head = _implement(repo, "src/module.py")

    passed, output = _run(repo, head, base, review_required=False)

    assert passed
    assert (
        "NOT EXAMINED: declared reviewers (no review record to judge "
        "the reviewer's actor against the list)" in output
    )


def test_a_reviews_membership_is_judged_however_the_run_was_asked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a review's membership is judged however the run was asked."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], reviewers=["reviewer-one"]
    )
    head = _implement(repo, "src/module.py")
    _submit(repo, head, actor="outsider")

    passed, output = _run(repo, head, base, review_required=False)

    assert not passed
    assert "FAIL: reviewer actor 'outsider' is not in" in output


def test_a_contract_declaring_no_reviewers_prints_no_reviewers_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a contract declaring no reviewers prints no reviewers line."""

    repo, base = _membership_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        implementers=["worker-one"],
        independence=["distinct-model"],
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="worker-one")
    _submit(repo, head)

    passed, output = _run(repo, head, base)

    assert passed
    assert "declared reviewers" not in output
    assert "reviewer actor" not in output


def test_every_in_range_implementer_sessions_actor_in_the_list_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: every in-range implementer session's actor in the list passes."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], implementers=["worker-one", "worker-two"]
    )
    first = _implement(repo, "src/first.py")
    head = _implement(repo, "src/second.py")
    _session(repo, first, actor="worker-one")
    _session(repo, head, actor="worker-two")
    _approve(repo, head)

    passed, output = _run(repo, head, base)

    assert passed
    assert (
        "PASS: every in-range implementer session's actor is in the "
        "contract's declared implementers" in output
    )


def test_a_session_actor_outside_the_list_refuses_naming_the_session_and_the_actor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a session outside the list refuses naming the session and actor."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], implementers=["worker-one"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="rogue-worker")
    _approve(repo, head)

    passed, output = _run(repo, head, base)

    assert not passed
    line = _membership_lines(output)[0]
    assert line.startswith("FAIL: in-range implementer session actors outside")
    assert "'rogue-worker'" in line and "worker-one" in line
    assert "implementer session" in line


def test_each_offending_session_is_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: each offending session is named."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], implementers=["worker-one"]
    )
    first = _implement(repo, "src/first.py")
    head = _implement(repo, "src/second.py")
    _session(repo, first, actor="rogue-one")
    _session(repo, head, actor="rogue-two")
    _approve(repo, head)

    passed, output = _run(repo, head, base)

    assert not passed
    line = _membership_lines(output)[0]
    assert line.startswith("FAIL:")
    assert "'rogue-one'" in line and "'rogue-two'" in line


def test_implementer_membership_compares_actor_ids_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: implementer membership compares actor ids exactly."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], implementers=["worker-one"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="Worker-One")
    _approve(repo, head)

    passed, output = _run(repo, head, base)

    assert not passed
    assert "'Worker-One'" in output


def test_a_session_outside_the_range_is_not_judged_for_membership(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a session outside the range is not judged for membership."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], implementers=["worker-one"]
    )
    head = _implement(repo, "src/module.py")
    # The base commit is not in `merge-base..candidate`: a session naming
    # it is no in-range implementer session, so its undeclared actor must
    # not fail the line.
    _session(repo, base, actor="rogue-worker")
    _session(repo, head, actor="worker-one")
    _approve(repo, head)

    passed, output = _run(repo, head, base)

    assert passed
    assert (
        "PASS: every in-range implementer session's actor is in the "
        "contract's declared implementers" in output
    )


def test_no_in_range_implementer_session_reads_not_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: no in-range implementer session reads not checked."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], implementers=["worker-one"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, base, actor="rogue-worker")  # out of range
    _approve(repo, head)

    passed, output = _run(repo, head, base)

    assert passed
    assert (
        "NOT CHECKED: declared implementers (no implementer session "
        "carries a commit in the candidate's range)" in output
    )
    assert "FAIL" not in [line.split(":")[0] for line in _membership_lines(output)]


def test_the_implementers_line_is_judged_however_the_run_was_asked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the implementers line is judged however the run was asked."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], implementers=["worker-one"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="rogue-worker")

    passed, output = _run(repo, head, base, review_required=False)

    assert not passed
    assert "'rogue-worker'" in output


def test_a_contract_declaring_no_implementers_prints_no_implementers_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a contract declaring no implementers prints no implementers line."""

    repo, base = _membership_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        reviewers=["reviewer-one"],
        independence=["distinct-model"],
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="worker-one")
    _submit(repo, head, actor="reviewer-one")

    passed, output = _run(repo, head, base)

    assert passed
    assert "declared implementers" not in output
    # The independence rule's own mention of the in-range sessions is not
    # the membership line.
    assert "implementer session actors" not in output
    assert "every in-range implementer session's actor" not in output


def test_values_the_membership_lines_print_are_escaped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: values the membership lines print are escaped."""

    repo, base = _membership_repo(
        tmp_path, monkeypatch, ["src/"], implementers=["worker-one"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="rogue\u200f")
    _approve(repo, head)

    _passed, output = _run(repo, head, base)

    assert "rogue\\u200f" in output
    assert "rogue\u200f" not in output


def test_distinct_actor_compares_actor_ids_exactly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: distinct-actor compares actor ids exactly."""

    repo, base = _membership_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        independence=["distinct-actor"],
        actors=("Worker-One", "worker-one"),
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="worker-one")
    _submit(repo, head, actor="Worker-One")

    passed, output = _run(repo, head, base)

    assert passed
    assert "PASS: independence rule 'distinct-actor'" in output


def test_a_contract_declaring_neither_list_prints_todays_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a contract declaring neither list prints today's transcript.

    A schema-3 contract carrying `independence` but neither list is held
    to the pinned embedded-implementation fixture: the membership checks
    add no line.
    """

    monkeypatch.delenv("AGENTMARSHAL_UPDATE_GATE_FIXTURES", raising=False)
    repo, base = _membership_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        independence=["reviewer-not-writer"],
    )
    head = _implement(repo, "src/module.py")
    _approve(repo, head)
    capsys.readouterr()
    code = main(_gate_arguments(base, head))
    transcript = capsys.readouterr()
    _compare_transcript(
        GATE_FIXTURES,
        "embedded-implementation",
        code,
        transcript.out,
        transcript.err,
        _run_values(base, head, {repo: "<repo>", tmp_path: "<tmp-root>"}),
    )
