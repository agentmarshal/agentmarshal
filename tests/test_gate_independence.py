"""Tests for the gate's declared independence rules (ADR-0018 D3, ADR-0022 s5).

A schema-3 contract's `independence` names the rules in force; the gate
prints one line per declared rule other than `reviewer-not-writer`, judging
the latest review against the task's implementer sessions — the session
records whose `commit` is a commit of the candidate's range.
"""

import json
from pathlib import Path

import pytest

from agentmarshal import __version__
from agentmarshal.cli import main
from agentmarshal.journal.gate import run_gate
from agentmarshal.journal.records import create_session_record, write_record
from test_gate import (
    _REVIEWER_EMAIL,
    GATE_FIXTURES,
    _approve,
    _commit_all,
    _compare_transcript,
    _gate_arguments,
    _git,
    _implement,
    _run_values,
)
from test_placement import _host_and_sidecar


def _journal(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal"


def _write_schema3_contract(
    repo: Path, scope: list[str], independence: list[str] | None
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
    if independence is not None:
        fields.append(f"independence = {json.dumps(independence)}")
    path.write_text("\n".join((*fields, "+++", "", "Body.\n")), encoding="utf-8")


def _independence_repo(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scope: list[str],
    independence: list[str] | None,
    *,
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
    _write_schema3_contract(repo, scope, independence)
    base = _commit_all(repo, "open task")
    return repo, base


def _session(
    repo: Path,
    commit: str,
    *,
    actor: str = "worker-impl",
    provider: str | None = "impl-co",
    model: str | None = "impl-model",
) -> None:
    """Write an implementer session record against the given commit."""

    record = create_session_record(
        "CR-001",
        __version__,
        "implementer",
        actor,
        "implementation",
        "implemented",
        1,
        2,
        0,
        usage_provider=provider,
        usage_method="measured" if provider is not None else None,
        commit=commit,
        model=model,
    )
    write_record(_journal(repo), "CR-001", record)


def _submit(
    repo: Path,
    commit: str,
    *,
    vendor: str = "review-co",
    model: str = "review-model",
    actor: str | None = None,
    verdict: str = "approved",
    findings: tuple[str, ...] = (),
    email: str = _REVIEWER_EMAIL,
) -> None:
    """Submit a review of *commit*, with the reviewer fields the rules read."""

    arguments = [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        commit,
        "--verdict",
        verdict,
        "--role",
        "qa",
        "--vendor",
        vendor,
        "--model",
        model,
        "--email",
        email,
    ]
    if actor is not None:
        arguments.extend(["--actor", actor])
    for finding in findings:
        arguments.extend(["--finding", finding])
    assert main(arguments) == 0


def _run(
    repo: Path, commit: str, base: str, *, review_required: bool = True
) -> tuple[bool, str]:
    report = run_gate(
        repo,
        "CR-001",
        commit,
        base,
        commit,
        review_required=review_required,
    )
    return report.passed, "\n".join(report.lines)


def _rule_lines(output: str) -> list[str]:
    return [line for line in output.splitlines() if "independence rule" in line]


def test_a_declared_rule_that_holds_passes_naming_the_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a declared rule that holds passes naming the rule."""

    repo, base = _independence_repo(
        tmp_path, monkeypatch, ["src/"], ["distinct-vendor"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, provider="impl-co")
    _submit(repo, head, vendor="review-co")

    passed, output = _run(repo, head, base)

    assert passed
    assert (
        "PASS: independence rule 'distinct-vendor' (declared reviewer vendor "
        "'review-co' differs from every in-range implementer session's "
        "declared vendor)" in output
    )


def test_a_rule_failing_against_one_session_refuses_the_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a rule failing against one session refuses the candidate."""

    repo, base = _independence_repo(
        tmp_path, monkeypatch, ["src/"], ["distinct-vendor"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, provider="shared-co")
    _submit(repo, head, vendor="shared-co")

    passed, output = _run(repo, head, base)

    assert not passed
    line = _rule_lines(output)[0]
    assert line.startswith("FAIL: independence rule 'distinct-vendor'")
    assert "'shared-co'" in line and line.count("'shared-co'") == 2


def test_every_in_range_implementer_session_is_judged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: every in-range implementer session is judged."""

    repo, base = _independence_repo(tmp_path, monkeypatch, ["src/"], ["distinct-model"])
    first = _implement(repo, "src/first.py")
    head = _implement(repo, "src/second.py")
    _session(repo, first, model="impl-model")
    _session(repo, head, model="review-model")
    _submit(repo, head, model="review-model")

    passed, output = _run(repo, head, base)

    assert not passed
    assert "FAIL: independence rule 'distinct-model'" in output


def test_a_session_outside_the_candidates_range_is_not_judged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a session outside the candidate's range is not judged."""

    repo, base = _independence_repo(
        tmp_path, monkeypatch, ["src/"], ["distinct-vendor"]
    )
    head = _implement(repo, "src/module.py")
    # The base commit is not in `merge-base..candidate`, so a session naming
    # it is no implementer session of this candidate — its vendor matching
    # the reviewer's must not fail the rule.
    _session(repo, base, provider="review-co")
    _session(repo, head, provider="impl-co")
    _submit(repo, head, vendor="review-co")

    passed, output = _run(repo, head, base)

    assert passed
    assert "PASS: independence rule 'distinct-vendor'" in output


def test_the_comparison_is_case_normalised(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the comparison is case-normalised."""

    repo, base = _independence_repo(tmp_path, monkeypatch, ["src/"], ["distinct-model"])
    head = _implement(repo, "src/module.py")
    _session(repo, head, model="IMPL-Model")
    _submit(repo, head, model="impl-model")

    passed, output = _run(repo, head, base)

    assert not passed
    assert "FAIL: independence rule 'distinct-model'" in output


def test_the_rule_lines_keep_the_declared_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the rule lines keep the declared order."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-model", "distinct-vendor"],
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head)
    _submit(repo, head)

    passed, output = _run(repo, head, base)

    assert passed
    lines = _rule_lines(output)
    assert len(lines) == 2
    assert "'distinct-model'" in lines[0] and "'distinct-vendor'" in lines[1]


def test_distinct_actor_compares_declared_actors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: distinct-actor compares declared actors."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-actor"],
        actors=("reviewer-one", "worker-one"),
        name="pass-repo",
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="worker-one")
    _submit(repo, head, actor="reviewer-one")

    passed, output = _run(repo, head, base)

    assert passed
    assert "PASS: independence rule 'distinct-actor'" in output

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-actor"],
        actors=("shared-actor",),
        name="fail-repo",
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="shared-actor")
    _submit(repo, head, actor="shared-actor")

    passed, output = _run(repo, head, base)

    assert not passed
    assert "FAIL: independence rule 'distinct-actor'" in output


def test_the_review_judged_is_the_latest_review_of_the_candidates_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the review judged is the latest review of the candidate's commit."""

    repo, base = _independence_repo(
        tmp_path, monkeypatch, ["src/"], ["distinct-vendor"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, provider="impl-co")
    _submit(repo, head, vendor="review-co")
    _submit(
        repo,
        head,
        vendor="impl-co",
        verdict="changes_required",
        findings=("F-1",),
    )

    passed, output = _run(repo, head, base)

    assert not passed
    assert "FAIL: independence rule 'distinct-vendor'" in output
    assert "'impl-co'" in output


def test_values_from_records_are_escaped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: values from records are escaped."""

    repo, base = _independence_repo(
        tmp_path, monkeypatch, ["src/"], ["distinct-vendor"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, provider="impl-co\u200f")
    _submit(repo, head, vendor="impl-co\u200f")

    _passed, output = _run(repo, head, base)

    assert "impl-co\\u200f" in output
    assert "impl-co\u200f" not in output


def test_a_sidecars_declared_rules_judge_its_own_journals_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a sidecar's declared rules judge its own journal's records."""

    _host, sidecar, base, head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Sidecar gate", "--scope", "app.txt"]) == 0
    _write_schema3_contract(sidecar, ["app.txt"], ["distinct-actor"])
    project_path = sidecar / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["actors"] = {
        "reviewer-one": {"git_identities": []},
        "worker-one": {"git_identities": []},
    }
    project["capture"] = {"overrides": {"reviews": "commit"}}
    project_path.write_text(json.dumps(project), encoding="utf-8")
    _session(sidecar, head, actor="worker-one")
    _submit(sidecar, head, actor="reviewer-one")
    capsys.readouterr()

    code = main(_gate_arguments(base, head))
    output = capsys.readouterr().out

    assert code == 0
    assert "PASS: independence rule 'distinct-actor'" in output


def test_no_implementer_session_carries_a_commit_in_the_range(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: no implementer session carries a commit in the range."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-vendor", "distinct-model"],
    )
    head = _implement(repo, "src/module.py")
    _session(repo, base)  # out of range: the merge base's own commit
    _submit(repo, head)

    passed, output = _run(repo, head, base)

    assert passed
    lines = _rule_lines(output)
    assert len(lines) == 2
    for line in lines:
        assert line.startswith("NOT CHECKED: independence rule '")
        assert "no implementer session carries a commit" in line


def test_a_compared_field_absent_on_the_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a compared field absent on the review."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-actor"],
        actors=("worker-one",),
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="worker-one")
    _submit(repo, head)  # no --actor: the review carries no reviewer.actor

    passed, output = _run(repo, head, base)

    assert passed
    assert (
        "NOT CHECKED: independence rule 'distinct-actor' (the latest review "
        "carries no 'reviewer.actor')" in output
    )


def test_a_compared_field_absent_on_a_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a compared field absent on a session."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-model", "distinct-vendor"],
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, model=None, provider=None)
    _submit(repo, head)

    passed, output = _run(repo, head, base)

    assert passed
    assert (
        "NOT CHECKED: independence rule 'distinct-model'" in output
        and "'model'" in output
    )
    assert "NOT CHECKED: independence rule 'distinct-vendor'" in output
    assert "usage.provider" in output


def test_a_sessions_actor_is_not_a_declared_actor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a session's actor is not a declared actor."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-actor"],
        actors=("reviewer-one",),
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="undeclared-worker")
    _submit(repo, head, actor="reviewer-one")

    passed, output = _run(repo, head, base)

    assert passed
    line = _rule_lines(output)[0]
    assert line.startswith("NOT CHECKED: independence rule 'distinct-actor'")
    assert "'undeclared-worker'" in line
    assert "not a declared actor" in line


def test_the_reviews_actor_is_not_a_declared_actor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the review's actor is not a declared actor."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-actor"],
        actors=("worker-one",),
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, actor="worker-one")
    _submit(repo, head, actor="undeclared-reviewer")

    passed, output = _run(repo, head, base)

    assert passed
    line = _rule_lines(output)[0]
    assert line.startswith("NOT CHECKED: independence rule 'distinct-actor'")
    assert "'undeclared-reviewer'" in line
    assert "not a declared actor" in line


def test_a_failing_session_outranks_an_unjudgeable_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a failing session outranks an unjudgeable one."""

    repo, base = _independence_repo(tmp_path, monkeypatch, ["src/"], ["distinct-model"])
    head = _implement(repo, "src/module.py")
    _session(repo, head, model=None)
    _session(repo, head, model="review-model")
    _submit(repo, head, model="review-model")

    passed, output = _run(repo, head, base)

    assert not passed
    assert "FAIL: independence rule 'distinct-model'" in output
    assert "NOT CHECKED" not in output


def test_the_declared_rules_are_not_examined_without_a_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the declared rules are not examined without a review."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["distinct-vendor", "distinct-model"],
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head)

    passed, output = _run(repo, head, base, review_required=False)

    assert passed
    lines = _rule_lines(output)
    assert len(lines) == 2
    for line in lines:
        assert line.startswith("NOT EXAMINED: independence rule '")
        assert "no review record" in line


def test_a_review_is_judged_however_the_run_was_asked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a review is judged however the run was asked."""

    repo, base = _independence_repo(
        tmp_path, monkeypatch, ["src/"], ["distinct-vendor"]
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head, provider="review-co")
    _submit(repo, head, vendor="review-co")

    passed, output = _run(repo, head, base, review_required=False)

    assert not passed
    assert "FAIL: independence rule 'distinct-vendor'" in output


def test_the_header_naming_reviewer_not_writer_adds_no_second_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the header naming reviewer-not-writer adds no second line."""

    repo, base = _independence_repo(
        tmp_path,
        monkeypatch,
        ["src/"],
        ["reviewer-not-writer", "distinct-vendor"],
    )
    head = _implement(repo, "src/module.py")
    _session(repo, head)
    _submit(repo, head)

    passed, output = _run(repo, head, base)

    assert passed
    assert output.count("declared reviewer identity differs") == 1
    assert "independence rule 'reviewer-not-writer'" not in output
    assert len(_rule_lines(output)) == 1


def test_a_contract_without_independence_prints_todays_transcript(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a contract without independence prints today's transcript.

    A schema-3 contract carrying no `independence` is the default case too:
    its transcript is held to the pinned embedded-implementation fixture.
    """

    monkeypatch.delenv("AGENTMARSHAL_UPDATE_GATE_FIXTURES", raising=False)
    repo, base = _independence_repo(tmp_path, monkeypatch, ["src/"], independence=None)
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
