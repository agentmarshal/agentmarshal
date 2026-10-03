"""Tests for the merge gate."""

import difflib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal import artifacts as artifacts_module
from agentmarshal.journal import gate as gate_module
from agentmarshal.journal import review as review_module
from agentmarshal.journal.contracts import ContractHeader, scope_covers
from agentmarshal.journal.gate import (
    GateError,
    markers_from_tree,
    run_findings_gate,
    run_gate,
)
from agentmarshal.journal.records import (
    create_abandoned_record,
    create_acceptance_record,
    create_completed_record,
    create_reopened_record,
    create_review_record,
    create_session_record,
    generate_ulid,
    read_records,
    write_record,
)
from agentmarshal.journal.status import TaskStatus, load_task_status
from test_placement import _commit, _host_and_sidecar

_WRITER = ["-c", "user.name=Worker", "-c", "user.email=worker@test.invalid"]
_REVIEWER_EMAIL = "reviewer@test.invalid"


def released_030() -> Path | None:
    """Locate the released 0.3.0 without naming anyone's home directory.

    Looked up in order: ``AGENTMARSHAL_RELEASED_030``, ``agentmarshal`` on
    PATH, the default user-tool location. Since CR-112 a build of this
    repository reports a ``.dev0`` version, so the version check already
    excludes this build. The ``finding`` probe still excludes a candidate that
    reports 0.3.0 without being the release: a checkout built while the tree
    still carried that version already knew the command, and the published
    0.3.0 predates it. A candidate counts only if it reports 0.3.0 and does
    not know that command.
    """

    candidates = [
        os.environ.get("AGENTMARSHAL_RELEASED_030"),
        shutil.which("agentmarshal"),
        str(Path.home() / ".local" / "bin" / "agentmarshal"),
    ]
    for candidate in candidates:
        if not candidate or not Path(candidate).is_file():
            continue
        version = subprocess.run(
            [candidate, "--version"], capture_output=True, text=True, check=False
        )
        if version.returncode != 0 or version.stdout.strip() != "0.3.0":
            continue
        knows_finding = subprocess.run(
            [candidate, "finding", "--help"], capture_output=True, check=False
        )
        if knows_finding.returncode == 0:
            continue
        return Path(candidate)
    return None


SKIP_030 = (
    "released 0.3.0 not found: set AGENTMARSHAL_RELEASED_030 or install it on PATH"
)


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


def _gate_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, scope: list[str]
) -> tuple[Path, str]:
    """Initialized repo with an opened task committed on master."""

    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project["capture"] = {"overrides": {"reviews": "commit"}}
    project_path.write_text(json.dumps(project), encoding="utf-8")
    arguments = ["open", "--title", "Gate task"]
    for entry in scope:
        arguments.extend(["--scope", entry])
    assert main(arguments) == 0
    base = _commit_all(repo, "open task")
    return repo, base


def _write_schema2_contract(
    repo: Path,
    scope: list[str],
    *,
    documents: list[str] | None = None,
    extensions: list[str] | None = None,
) -> None:
    path = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    fields = [
        "+++",
        "schema = 2",
        'id = "CR-001"',
        'title = "Gate task"',
        f"scope = {json.dumps(scope)}",
        "acceptance = []",
    ]
    if documents is not None:
        fields.append(f"documents = {json.dumps(documents)}")
    if extensions is not None:
        fields.append(f"extensions = {json.dumps(extensions)}")
    path.write_text("\n".join((*fields, "+++", "", "Body.\n")), encoding="utf-8")


def _write_extension_manifest(
    repo: Path,
    *,
    footprint: list[str] | None = None,
    documents: list[str] | None = None,
) -> Path:
    path = repo / ".agentmarshal" / "extensions" / "openspec.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "schema = 1\n"
        'name = "openspec"\n'
        'version = "1"\n'
        f"footprint = {json.dumps(footprint or ['openspec/'])}\n"
        f"documents = {json.dumps(documents or [])}\n"
        "artifacts = []\n"
        'install = "install"\n'
        'remove = "remove"\n',
        encoding="utf-8",
    )
    return path


def _implement(repo: Path, path: str, content: str = "code\n") -> str:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return _commit_all(repo, "implement")


def _approve(repo: Path, commit: str, email: str = _REVIEWER_EMAIL) -> None:
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                commit,
                "--verdict",
                "approved",
                "--role",
                "qa",
                "--vendor",
                "test",
                "--model",
                "test-model",
                "--email",
                email,
            ]
        )
        == 0
    )


def _require_changes(
    repo: Path,
    commit: str,
    *findings: str,
    email: str = _REVIEWER_EMAIL,
) -> None:
    arguments = [
        "submit-review",
        "--task",
        "CR-001",
        "--commit",
        commit,
        "--verdict",
        "changes_required",
        "--role",
        "qa",
        "--vendor",
        "test",
        "--model",
        "test-model",
        "--email",
        email,
    ]
    for finding in findings:
        arguments.extend(["--finding", finding])
    assert main(arguments) == 0


def _accept(
    repo: Path, commit: str, accepted_by: str = "operator@example.invalid"
) -> None:
    assert (
        main(
            [
                "accept",
                "--task",
                "CR-001",
                "--commit",
                commit,
                "--by",
                accepted_by,
                "--reason",
                "The review loop did not converge",
            ]
        )
        == 0
    )


def _run(
    repo: Path, commit: str, base: str, pipeline_sha: str | None
) -> tuple[bool, str]:
    report = run_gate(repo, "CR-001", commit, base, pipeline_sha)
    return report.passed, "\n".join(report.lines)


GATE_FIXTURES = Path(__file__).parent / "fixtures" / "gate"
UPDATE_FIXTURES_ENV = "AGENTMARSHAL_UPDATE_GATE_FIXTURES"
# A record id is a 26-character ULID (its first digit is 0-7 by construction);
# a time is ISO-8601. Neither is a value the test setup can enumerate, so they
# are replaced by pattern — see _normalize_transcript.
_RECORD_ID = re.compile(r"\b[0-7][0123456789ABCDEFGHJKMNPQRSTVWXYZ]{25}\b")
_TIME = re.compile(
    r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"
)


def _normalize_transcript(text: str, run_values: dict[str, str]) -> str:
    """Substitute run-dependent values in *text* with named placeholders.

    The one substitution applied to a gate run's actual output before it is
    compared with a committed fixture. *run_values* maps each concrete value
    this run produced — the candidate and base commits in full and
    abbreviated form, the temporary repository roots — to the placeholder
    the fixture holds for it; replacements are applied longest-first so an
    abbreviated commit is never claimed inside a longer value. Values the
    setup cannot enumerate are replaced by pattern instead: a record id
    becomes ``<record-id>`` and a time becomes ``<time>`` wherever one
    appears. Everything the substitution does not name must match the
    fixture byte for byte — that is what makes the comparison a pin and not
    a similarity check.
    """

    for value, placeholder in sorted(
        run_values.items(), key=lambda item: len(item[0]), reverse=True
    ):
        text = text.replace(value, placeholder)
    text = _RECORD_ID.sub("<record-id>", text)
    return _TIME.sub("<time>", text)


def _transcript_lines(text: str) -> list[str]:
    # "\n" is the only line separator in a transcript; splitlines would also
    # break on control bytes and misplace them in the reported diff.
    parts = text.split("\n")
    lines = [f"{part}\n" for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def _transcript_diff(label: str, fixture: str, actual: str) -> str:
    return "".join(
        difflib.unified_diff(
            _transcript_lines(fixture),
            _transcript_lines(actual),
            fromfile=f"{label} (fixture)",
            tofile=f"{label} (actual)",
        )
    )


def _compare_transcript(
    fixture_root: Path,
    case: str,
    exit_code: int,
    stdout: str,
    stderr: str,
    run_values: dict[str, str],
) -> None:
    """Hold a gate run's transcript to its fixture — or rewrite the fixture.

    The transcript is compared stream by stream after
    :func:`_normalize_transcript`; any difference fails with a unified diff
    between the fixture and the run. With ``AGENTMARSHAL_UPDATE_GATE_FIXTURES``
    set to a non-empty value other than ``0`` the normalized transcript is
    written to the fixture files first — the explicit act by which a task
    that changes the output on purpose names its change in the reviewed diff.
    Unset, this function never writes: a fixture cannot drift in silence,
    and every file of the triple must exist — a missing fixture fails
    naming it rather than comparing against an empty stream.
    """

    streams = {
        f"{case}.stdout": _normalize_transcript(stdout, run_values),
        f"{case}.stderr": _normalize_transcript(stderr, run_values),
        f"{case}.exit": f"{exit_code}\n",
    }
    if os.environ.get(UPDATE_FIXTURES_ENV) not in (None, "", "0"):
        fixture_root.mkdir(parents=True, exist_ok=True)
        for name, content in streams.items():
            (fixture_root / name).write_text(content, encoding="utf-8")
    missing = [name for name in streams if not (fixture_root / name).is_file()]
    assert not missing, (
        f"fixture files missing for {case}: {', '.join(missing)} — "
        f"regenerate with {UPDATE_FIXTURES_ENV}=1"
    )
    differences = "".join(
        _transcript_diff(
            name,
            (fixture_root / name).read_text(encoding="utf-8"),
            content,
        )
        for name, content in streams.items()
    )
    assert not differences, (
        f"gate transcript differs from the {case} fixture:\n{differences}"
    )


def _gate_arguments(base: str, head: str) -> list[str]:
    return [
        "gate",
        "--task",
        "CR-001",
        "--commit",
        head,
        "--base",
        base,
        "--pipeline-sha",
        head,
    ]


def _run_values(base: str, head: str, roots: dict[Path, str]) -> dict[str, str]:
    # The full sha and its abbreviation map to different placeholders so a
    # transcript that switches between the two forms fails the pin.
    return {
        head: "<head-sha>",
        head[:12]: "<head-sha-12>",
        base: "<base-sha>",
        base[:12]: "<base-sha-12>",
        **{str(root): placeholder for root, placeholder in roots.items()},
    }


def _embedded_implementation_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[str], dict[str, str]]:
    """The embedded diff lane: an approved candidate inside its scope."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)
    return _gate_arguments(base, head), _run_values(
        base, head, {repo: "<repo>", tmp_path: "<tmp-root>"}
    )


def _embedded_journal_only_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[str], dict[str, str]]:
    """The embedded deterministic lane: the candidate touches only the journal."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    note = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "note.md"
    note.write_text("journal-only change\n", encoding="utf-8")
    head = _commit_all(repo, "journal-only")
    return _gate_arguments(base, head), _run_values(
        base, head, {repo: "<repo>", tmp_path: "<tmp-root>"}
    )


def _sidecar_implementation_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[str], dict[str, str]]:
    """The sidecar diff lane: an approved host candidate, judged advisory."""

    host, sidecar, base, head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Sidecar gate", "--scope", "app.txt"]) == 0
    _approve(sidecar, head)
    return _gate_arguments(base, head), _run_values(
        base, head, {host: "<host>", sidecar: "<sidecar>", tmp_path: "<tmp-root>"}
    )


def _sidecar_journal_only_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[str], dict[str, str]]:
    """The candidate that would take the deterministic lane in an embedded journal.

    Built the way test_sidecar_gate_gives_no_deterministic_lane_to_a_host_journal
    builds it — a host diff under .agentmarshal/journal/ only. The lane does
    not exist in a sidecar, so the pinned transcript is a refusal.
    """

    host, sidecar, _base, _head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Private", "--scope", "app.txt"]) == 0
    records = host / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    records.mkdir(parents=True)
    (records / "x.json").write_text("{}\n", encoding="utf-8")
    base = _commit(host, "host journal")
    (records / "y.json").write_text("{}\n", encoding="utf-8")
    head = _commit(host, "host journal again")
    return _gate_arguments(base, head), _run_values(
        base, head, {host: "<host>", sidecar: "<sidecar>", tmp_path: "<tmp-root>"}
    )


_PINNED_TRANSCRIPT_CASES = {
    "embedded-implementation": _embedded_implementation_case,
    "embedded-journal-only": _embedded_journal_only_case,
    "sidecar-implementation": _sidecar_implementation_case,
    "sidecar-journal-only": _sidecar_journal_only_case,
}


def _transcript_for_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> tuple[int, str, str, dict[str, str]]:
    """Run a default gate on one case and return its transcript."""

    arguments, run_values = _PINNED_TRANSCRIPT_CASES[case](tmp_path, monkeypatch)
    capsys.readouterr()
    code = main(arguments)
    transcript = capsys.readouterr()
    return code, transcript.out, transcript.err, run_values


@pytest.mark.parametrize("case", sorted(_PINNED_TRANSCRIPT_CASES))
def test_default_run_transcript_matches_the_committed_fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    """Scenario: the pinned transcript still matches.

    One fixture triple per case pins a default gate run's stdout, stderr
    and exit status — the implementation lane and the journal-only lane in
    the embedded placement; in the sidecar placement the implementation
    lane and the host candidate whose diff touches only the journal, where
    no deterministic lane exists and the fixture pins the refusal.
    """

    # A stray update flag in the caller's environment must not let this
    # test rewrite the fixtures it is pinning.
    monkeypatch.delenv(UPDATE_FIXTURES_ENV, raising=False)
    code, out, err, run_values = _transcript_for_case(
        tmp_path, monkeypatch, capsys, case
    )
    _compare_transcript(GATE_FIXTURES, case, code, out, err, run_values)


@pytest.mark.parametrize("case", sorted(_PINNED_TRANSCRIPT_CASES))
def test_regenerate_the_committed_fixtures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    """Rewrite the pinned fixtures from a run — the deliberate act a task
    that changes the output on purpose performs so the fixture's diff names
    its change in review.

    Runs only when AGENTMARSHAL_UPDATE_GATE_FIXTURES is set to a non-empty
    value other than ``0``; skipped otherwise, so no run rewrites a fixture
    unless it was explicitly asked to."""

    if os.environ.get(UPDATE_FIXTURES_ENV) in (None, "", "0"):
        pytest.skip(f"set {UPDATE_FIXTURES_ENV}=1 to regenerate the fixtures")
    code, out, err, run_values = _transcript_for_case(
        tmp_path, monkeypatch, capsys, case
    )
    _compare_transcript(GATE_FIXTURES, case, code, out, err, run_values)


def test_a_transcript_difference_is_shown_as_a_readable_diff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a transcript difference is shown, not hidden."""

    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    (fixture_root / "case.stdout").write_text(
        "PASS: a line\nPASS: another\ngate: passed\n", encoding="utf-8"
    )
    (fixture_root / "case.stderr").write_text("", encoding="utf-8")
    (fixture_root / "case.exit").write_text("0\n", encoding="utf-8")
    monkeypatch.delenv(UPDATE_FIXTURES_ENV, raising=False)

    with pytest.raises(AssertionError) as raised:
        _compare_transcript(
            fixture_root,
            "case",
            0,
            "PASS: a line\nFAIL: another\ngate: passed\n",
            "",
            {},
        )

    diff = str(raised.value)
    assert "-PASS: another" in diff
    assert "+FAIL: another" in diff


def test_a_fixture_changes_only_when_the_output_changes_on_purpose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a fixture changes only when the output changes on purpose."""

    fixture_root = tmp_path / "fixtures"
    fixture_root.mkdir()
    run_values = {"a" * 12: "<head-sha>"}
    stdout = f"PASS: pipeline attested for {'a' * 12}\ngate: passed\n"

    # Without the flag an absent fixture fails naming the missing files,
    # never a write and never a comparison against an empty stream.
    monkeypatch.delenv(UPDATE_FIXTURES_ENV, raising=False)
    with pytest.raises(AssertionError) as raised:
        _compare_transcript(fixture_root, "case", 0, stdout, "", run_values)
    for name in ("case.stdout", "case.stderr", "case.exit"):
        assert name in str(raised.value)
    assert not list(fixture_root.iterdir())

    # With the flag the run rewrites the fixture — the explicit act a task
    # that changes the output on purpose uses to name it.
    monkeypatch.setenv(UPDATE_FIXTURES_ENV, "1")
    _compare_transcript(fixture_root, "case", 0, stdout, "", run_values)
    assert (fixture_root / "case.stdout").read_text(encoding="utf-8") == (
        "PASS: pipeline attested for <head-sha>\ngate: passed\n"
    )
    assert (fixture_root / "case.exit").read_text(encoding="utf-8") == "0\n"


def _set_review_threshold(repo: Path, value: object) -> None:
    """Write ``review.changes_required_threshold`` into the test project file.

    Left uncommitted on purpose: the gate reads the setting from the
    working tree, and committing it would put ``project.json`` in the
    candidate's diff outside its scope.
    """

    project_path = repo / ".agentmarshal" / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    project.setdefault("review", {})["changes_required_threshold"] = value
    project_path.write_text(json.dumps(project), encoding="utf-8")


def test_the_implementation_lane_prints_the_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the implementation lane prints the count."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "INFO: changes_required verdicts for CR-001: 0 (threshold 3)" in output


def test_the_implementation_lane_prints_the_count_in_a_sidecar(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the implementation lane prints the count.

    The same line in the other placement: the sidecar's project.json
    carries no ``review`` section, so the threshold is the default.
    """

    _host, sidecar, base, head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Sidecar gate", "--scope", "app.txt"]) == 0
    _approve(sidecar, head)
    capsys.readouterr()

    code = main(_gate_arguments(base, head))

    transcript = capsys.readouterr()
    assert code == 0, transcript.err
    assert (
        "INFO: changes_required verdicts for CR-001: 0 (threshold 3)" in transcript.out
    )


def test_the_count_is_over_the_whole_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the count is over the whole task."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    first = _implement(repo, "src/module.py")
    second = _implement(repo, "src/module.py", "more code\n")
    # The earlier commit drew the changes_required verdict; the candidate's
    # own review approves. Both records stay uncommitted, as the launcher
    # leaves them, so the candidate diff stays inside its scope.
    _require_changes(repo, first, "F-001")
    _approve(repo, second)

    passed, output = _run(repo, second, base, second)

    assert passed, output
    assert f"PASS: latest review of {second[:12]} is approved" in output
    assert "INFO: changes_required verdicts for CR-001: 1 (threshold 3)" in output


def test_a_count_at_the_threshold_is_marked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a count at the threshold is marked."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _approve(repo, head)
    _set_review_threshold(repo, 1)
    capsys.readouterr()

    passed, output = _run(repo, head, base, head)

    # The mark is a WARN — a report, never a verdict: an approved
    # candidate at the threshold still passes, and the run still exits 0.
    assert passed, output
    assert (
        "WARN: changes_required verdicts for CR-001: 1 (threshold 1 reached "
        "— stop and revisit the contract)" in output
    )
    assert main(_gate_arguments(base, head)) == 0


def test_a_malformed_threshold_is_reported_on_the_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a malformed threshold is reported on the line."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)
    _set_review_threshold(repo, "high")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert (
        "WARN: changes_required verdicts for CR-001: 0 (threshold unreadable: "
        "project.json key 'review.changes_required_threshold' must be an "
        "integer of at least 1)" in output
    )


def test_the_journal_only_lane_prints_no_count_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the journal-only lane prints no count line."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    note = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "note.md"
    note.write_text("journal-only change\n", encoding="utf-8")
    head = _commit_all(repo, "journal-only")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "changes_required" not in output


def test_a_default_run_prints_the_transcript_it_printed_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the pinned transcript still matches.

    The committed fixtures are the byte-for-byte pin, so this test names the
    scenario and delegates to the fixture comparison for the embedded
    implementation lane."""

    test_default_run_transcript_matches_the_committed_fixture(
        tmp_path, monkeypatch, capsys, "embedded-implementation"
    )


def test_findings_gate_uses_the_public_artifact_resolver() -> None:
    """The gate and launcher hold the artifact resolver's one function object."""

    assert (
        gate_module.artifact_path
        is review_module.artifact_path
        is artifacts_module.artifact_path
    )
    assert not hasattr(gate_module, "_artifact_path")


def test_the_flag_reaches_the_gate_from_the_command_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The flag is wired: the command prints what the mode reports."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    capsys.readouterr()

    code = main(
        [
            "gate",
            "--task",
            "CR-001",
            "--commit",
            head,
            "--base",
            base,
            "--pipeline-sha",
            head,
            "--without-review",
        ]
    )

    output = capsys.readouterr().out
    assert code == 0, output
    assert "NOT EXAMINED: latest review" in output
    # A caller that decides a merge must tell this from a full pass without
    # reading the transcript, which the contract's threat model asks for.
    assert "gate: passed what it examined; the review was not examined" in output
    assert "gate: passed\n" not in output


def test_the_flag_is_refused_on_the_findings_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A lane with no candidate has no review of one to leave unexamined."""

    repo, _base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    monkeypatch.chdir(repo)
    capsys.readouterr()

    code = main(["gate", "--task", "CR-001", "--findings", "--without-review"])

    assert code == 1
    assert "has no candidate" in capsys.readouterr().err


def _run_without_review(
    repo: Path, commit: str, base: str, pipeline_sha: str | None
) -> tuple[bool, str]:
    report = run_gate(repo, "CR-001", commit, base, pipeline_sha, review_required=False)
    return report.passed, "\n".join(report.lines)


def test_a_candidate_with_no_review_passes_what_does_not_need_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a candidate with no review passes the checks that do not need one."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")

    passed, output = _run_without_review(repo, head, base, head)

    assert passed, output
    assert "NOT EXAMINED: latest review" in output
    assert "NOT EXAMINED: reviewer independence" in output
    assert "FAIL" not in output


def test_the_mode_does_not_excuse_a_candidate_that_breaks_another_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the mode does not excuse a candidate that breaks another rule."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    outside = repo / "elsewhere" / "module.py"
    outside.parent.mkdir()
    outside.write_text("x = 1\n", encoding="utf-8")
    head = _commit_all(repo, "change a path outside scope")

    passed, output = _run_without_review(repo, head, base, head)

    assert not passed
    assert "FAIL: paths outside contract scope: elsewhere/module.py" in output


def test_a_non_approving_review_still_refuses_under_the_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a non-approving review still refuses."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")

    passed, output = _run_without_review(repo, head, base, head)

    assert not passed
    assert "NOT EXAMINED: latest review" not in output
    assert f"FAIL: latest review of {head[:12]} is approved" in output


def test_an_approving_review_reports_as_approving_under_the_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an approving review is reported as approving."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)

    passed, output = _run_without_review(repo, head, base, head)

    assert passed, output
    assert f"PASS: latest review of {head[:12]} is approved" in output
    assert "NOT EXAMINED" not in output


def test_gate_passes_a_clean_candidate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    # The review record stays uncommitted in the journal working tree:
    # a review never has to be part of the very diff it attests.
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert output.count("FAIL") == 0

    capsys.readouterr()
    assert (
        main(
            [
                "gate",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--base",
                base,
                "--pipeline-sha",
                head,
            ]
        )
        == 0
    )
    transcript = capsys.readouterr()
    assert transcript.out.endswith("gate: passed\n")
    assert "advisory" not in transcript.out


def test_a_candidate_without_renames_prints_the_transcript_it_printed_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a candidate without renames prints the transcript it printed before.

    The committed fixture for the embedded implementation lane — a candidate
    without renames — is the byte-for-byte demonstration, so this test names
    the scenario and delegates rather than copying it."""

    test_default_run_transcript_matches_the_committed_fixture(
        tmp_path, monkeypatch, capsys, "embedded-implementation"
    )


def test_gate_refuses_a_rename_out_of_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a rename out of scope is refused."""

    repo, _ = _gate_repo(tmp_path, monkeypatch, ["inside/"])
    source = repo / "outside" / "original.py"
    source.parent.mkdir()
    source.write_text("code\n", encoding="utf-8")
    base = _commit_all(repo, "add source outside scope")
    destination = repo / "inside" / "renamed.py"
    destination.parent.mkdir()
    _git(
        repo,
        "mv",
        source.relative_to(repo).as_posix(),
        destination.relative_to(repo).as_posix(),
    )
    head = _commit_all(repo, "rename into scope")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: paths outside contract scope: outside/original.py" in output


def test_gate_passes_a_rename_within_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a rename within scope passes."""

    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    source = repo / "src" / "original.py"
    source.parent.mkdir()
    source.write_text("code\n", encoding="utf-8")
    base = _commit_all(repo, "add source within scope")
    destination = repo / "src" / "renamed.py"
    _git(
        repo,
        "mv",
        source.relative_to(repo).as_posix(),
        destination.relative_to(repo).as_posix(),
    )
    head = _commit_all(repo, "rename within scope")
    _approve(repo, head)

    checked_paths: list[str] = []

    def recording_scope_covers(scope: tuple[str, ...], path: str) -> bool:
        checked_paths.append(path)
        return scope_covers(scope, path)

    monkeypatch.setattr(gate_module, "scope_covers", recording_scope_covers)
    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "PASS: diff within contract scope" in output.splitlines()
    assert checked_paths == ["src/original.py", "src/renamed.py"]


def test_move_into_the_journal_takes_the_diff_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a move into the journal takes the diff lane."""

    repo, _ = _gate_repo(tmp_path, monkeypatch, [".agentmarshal/journal/"])
    source = repo / "staging" / "note.md"
    source.parent.mkdir()
    source.write_text("note\n", encoding="utf-8")
    base = _commit_all(repo, "add source outside journal")
    destination = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "note.md"
    _git(
        repo,
        "mv",
        source.relative_to(repo).as_posix(),
        destination.relative_to(repo).as_posix(),
    )
    head = _commit_all(repo, "move note into journal")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: paths outside contract scope: staging/note.md" in output
    assert "journal-only transaction" not in output


def _empty_scope_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, list[str]]:
    """A host change offered under an empty-scope task, with its gate call."""

    repo, base = _gate_repo(tmp_path, monkeypatch, [])
    head = _implement(repo, "host-change.py")
    _approve(repo, head)
    return repo, _gate_arguments(base, head)


def test_empty_scope_candidate_takes_the_diff_lane_and_is_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The guard against host changes riding under an empty-scope task."""

    _, arguments = _empty_scope_candidate(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(arguments) == 1
    transcript = capsys.readouterr()
    assert "paths outside contract scope: host-change.py" in transcript.out
    assert "findings lane" not in transcript.out
    assert "gate: passed" not in transcript.out


def test_gate_refuses_path_outside_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "outside/module.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "outside contract scope" in output


def test_named_extension_footprint_joins_effective_scope_from_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_schema2_contract(repo, ["src/"], extensions=["openspec"])
    _write_extension_manifest(repo)
    base = _commit_all(repo, "name extension")
    head = _implement(repo, "openspec/change.md")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed
    assert "diff within contract scope (extensions: openspec)" in output


def test_candidate_manifest_edit_cannot_widen_its_own_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest_path = ".agentmarshal/extensions/openspec.toml"
    repo, _ = _gate_repo(tmp_path, monkeypatch, [manifest_path])
    _write_schema2_contract(repo, [manifest_path], extensions=["openspec"])
    manifest = _write_extension_manifest(repo)
    base = _commit_all(repo, "name extension")
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'footprint = ["openspec/"]', 'footprint = ["candidate-only/"]'
        ),
        encoding="utf-8",
    )
    candidate_path = repo / "candidate-only" / "change.md"
    candidate_path.parent.mkdir()
    candidate_path.write_text("change\n", encoding="utf-8")
    head = _commit_all(repo, "try to widen manifest")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "paths outside contract scope: candidate-only/change.md" in output
    assert "extensions: openspec" in output


def test_candidate_manifest_edit_cannot_silence_base_side_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest_path = ".agentmarshal/extensions/openspec.toml"
    repo, _ = _gate_repo(tmp_path, monkeypatch, [manifest_path])
    _write_schema2_contract(repo, [manifest_path], extensions=["openspec"])
    manifest = _write_extension_manifest(repo, documents=["openspec/specs/"])
    base = _commit_all(repo, "name extension documents")
    manifest.write_text(
        manifest.read_text(encoding="utf-8").replace(
            'documents = ["openspec/specs/"]', "documents = []"
        ),
        encoding="utf-8",
    )
    code = repo / "openspec" / "code.py"
    code.parent.mkdir()
    code.write_text("change\n", encoding="utf-8")
    head = _commit_all(repo, "try to silence documents")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: named documents untouched: openspec/specs/" in output


@pytest.mark.parametrize("manifest_state", ["missing", "malformed"])
def test_gate_refuses_an_unreadable_base_side_named_manifest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    manifest_state: str,
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_schema2_contract(repo, ["src/"], extensions=["openspec"])
    if manifest_state == "malformed":
        manifest = _write_extension_manifest(repo)
        manifest.write_text("schema = [\n", encoding="utf-8")
    base = _commit_all(repo, f"{manifest_state} manifest at base")
    head = _implement(repo, "src/change.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "named extension 'openspec' manifest unreadable" in output
    assert manifest_state in output or "invalid TOML" in output


def test_unnamed_extension_footprint_does_not_join_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_extension_manifest(repo)
    base = _commit_all(repo, "install unrequested extension")
    head = _implement(repo, "openspec/change.md")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "paths outside contract scope: openspec/change.md" in output


@pytest.mark.parametrize("touch_document", [False, True])
def test_gate_reports_whether_named_documents_are_touched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    touch_document: bool,
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/", "docs/"])
    _write_schema2_contract(repo, ["src/", "docs/"], documents=["docs/guide.md"])
    base = _commit_all(repo, "name document")
    path = "docs/guide.md" if touch_document else "src/change.py"
    head = _implement(repo, path)
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed is touch_document
    expected = (
        "PASS: named documents touched (docs/guide.md)"
        if touch_document
        else "FAIL: named documents untouched: docs/guide.md"
    )
    assert expected in output


def test_deleting_a_named_document_counts_as_touched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["docs/"])
    _write_schema2_contract(repo, ["docs/"], documents=["docs/guide.md"])
    guide = repo / "docs" / "guide.md"
    guide.parent.mkdir()
    guide.write_text("guide\n", encoding="utf-8")
    base = _commit_all(repo, "name document")
    guide.unlink()
    head = _commit_all(repo, "delete document")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed
    assert "PASS: named documents touched (docs/guide.md)" in output


def test_journal_only_lane_prints_nothing_about_named_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["docs/"])
    _write_schema2_contract(repo, ["docs/"], documents=["docs/guide.md"])
    base = _commit_all(repo, "name document")
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8") + "Journal-only clarification.\n",
        encoding="utf-8",
    )
    head = _commit_all(repo, "clarify contract")

    passed, output = _run(repo, head, base, head)

    assert passed
    assert "named documents" not in output


@pytest.mark.parametrize("leave_footprint", [False, True])
def test_manifest_deletion_checks_candidate_tree_for_remaining_footprint(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    leave_footprint: bool,
) -> None:
    manifest_path = ".agentmarshal/extensions/openspec.toml"
    repo, _ = _gate_repo(tmp_path, monkeypatch, [manifest_path])
    _write_schema2_contract(repo, [manifest_path], extensions=["openspec"])
    manifest = _write_extension_manifest(repo)
    first = repo / "openspec" / "first.md"
    second = repo / "openspec" / "second.md"
    first.parent.mkdir()
    first.write_text("first\n", encoding="utf-8")
    second.write_text("second\n", encoding="utf-8")
    base = _commit_all(repo, "installed extension")
    manifest.unlink()
    first.unlink()
    if not leave_footprint:
        second.unlink()
    head = _commit_all(repo, "remove extension")
    if not leave_footprint:
        # An uncommitted recreation must not affect the candidate-tree check.
        second.parent.mkdir(exist_ok=True)
        second.write_text("working tree only\n", encoding="utf-8")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed is not leave_footprint
    if leave_footprint:
        assert "FAIL: extension 'openspec' removal incomplete" in output
        assert "openspec/second.md" in output
    else:
        assert "PASS: extension 'openspec' removal complete" in output


def test_editing_footprint_without_deleting_manifest_has_no_removal_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_schema2_contract(repo, ["src/"], extensions=["openspec"])
    _write_extension_manifest(repo)
    base = _commit_all(repo, "installed extension")
    head = _implement(repo, "openspec/change.md")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed
    assert "removal" not in output


def test_deleting_an_unnamed_base_manifest_still_checks_its_footprint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest_path = ".agentmarshal/extensions/openspec.toml"
    repo, _ = _gate_repo(tmp_path, monkeypatch, [manifest_path, "openspec/"])
    manifest = _write_extension_manifest(repo)
    footprint_file = repo / "openspec" / "remaining.md"
    footprint_file.parent.mkdir()
    footprint_file.write_text("still here\n", encoding="utf-8")
    base = _commit_all(repo, "installed extension")
    manifest.unlink()
    head = _commit_all(repo, "delete only manifest")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: extension 'openspec' removal incomplete" in output
    assert "openspec/remaining.md" in output


def test_gate_refuses_undeclared_journal_change_in_mixed_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "module.py").write_text("code\n", encoding="utf-8")
    # A journal document under the task dir that the base contract scope
    # does not list, bundled with the in-scope code change.
    (repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "extra.md").write_text(
        "undeclared\n", encoding="utf-8"
    )
    head = _commit_all(repo, "mixed candidate with undeclared journal change")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "outside contract scope" in output


def test_gate_refuses_missing_and_stale_reviews(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")

    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "no review record" in output

    _approve(repo, head)
    stale_head = _commit_all(repo, "record review")

    # The review targets the previous head, not the candidate head.
    passed, output = _run(repo, stale_head, base, stale_head)
    assert not passed
    assert "no review record" in output


def test_gate_refuses_non_approved_latest_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)
    _require_changes(repo, head, "F-001")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert f"FAIL: latest review of {head[:12]} is approved" in output


def test_gate_passes_valid_acceptance_without_reporting_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001", "F-002")
    _accept(repo, head, accepted_by="operator@example.invalid")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert (
        "PASS: accepted over findings F-001, F-002 by "
        "operator@example.invalid; not an approving review"
    ) in output
    assert f"latest review of {head[:12]} is approved" not in output


@pytest.mark.parametrize(
    ("review_findings", "acceptance_findings"),
    [
        (("F-001", "F-002"), ["F-001"]),
        (("F-001",), ["F-001", "F-002"]),
    ],
)
def test_gate_re_derives_acceptance_findings_exactly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    review_findings: tuple[str, ...],
    acceptance_findings: list[str],
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, *review_findings)
    journal = repo / ".agentmarshal" / "journal"
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            head,
            "operator@example.invalid",
            acceptance_findings,
            "Crafted without the accept command's validation",
        ),
    )

    passed, output = _run(repo, head, base, head)

    assert not passed
    # The acceptance exists but does not cover what is outstanding, and the
    # refusal says so rather than reporting only a missing approval.
    assert f"FAIL: acceptance of {head[:12]} does not cover the latest" in output
    assert "accepted over findings" not in output


def test_gate_refuses_acceptance_made_stale_by_a_later_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _accept(repo, head)
    _require_changes(repo, head, "F-001", "F-002")

    passed, output = _run(repo, head, base, head)

    assert not passed
    # The acceptance exists but does not cover what is outstanding, and the
    # refusal says so rather than reporting only a missing approval.
    assert f"FAIL: acceptance of {head[:12]} does not cover the latest" in output
    assert "accepted over findings" not in output


def test_gate_refuses_acceptance_for_a_different_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    journal = repo / ".agentmarshal" / "journal"
    write_record(
        journal,
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "test",
            "a" * 40,
            "operator@example.invalid",
            ["F-001"],
            "Acceptance of another commit",
        ),
    )

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert f"FAIL: latest review of {head[:12]} is approved" in output


def test_gate_still_refuses_dependent_reviewer_with_valid_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001", email="worker@test.invalid")
    _accept(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "accepted over findings" in output
    assert "declared reviewer identity differs" in output


def test_gate_refuses_dependent_reviewer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head, email="worker@test.invalid")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "declared reviewer identity differs" in output


def test_gate_refuses_missing_or_wrong_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, None)
    assert not passed
    assert "attestation" in output

    passed, output = _run(repo, head, base, "0" * 40)
    assert not passed
    assert "attestation" in output


def test_gate_ci_required_delegates_attestation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)

    # No pipeline_sha at all, yet ci-required delegates attestation:
    report = run_gate(repo, "CR-001", head, base, None, attestation="ci-required")

    assert report.passed, "\n".join(report.lines)
    assert "delegated to the provider's required checks" in "\n".join(report.lines)


def test_gate_ci_required_still_enforces_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")  # no review recorded

    report = run_gate(repo, "CR-001", head, base, None, attestation="ci-required")

    assert not report.passed
    assert "no review record" in "\n".join(report.lines)


def test_gate_ci_required_still_enforces_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "outside/bad.py")
    _approve(repo, head)

    report = run_gate(repo, "CR-001", head, base, None, attestation="ci-required")

    assert not report.passed
    assert "outside contract scope" in "\n".join(report.lines)


def test_gate_unknown_attestation_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")

    with pytest.raises(GateError, match="unknown attestation mode"):
        run_gate(repo, "CR-001", head, base, head, attestation="bogus")


def test_gate_journal_only_lane_needs_no_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    note = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "note.md"
    note.write_text("journal-only change\n", encoding="utf-8")
    head = _commit_all(repo, "journal-only")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "deterministic lane" in output


def test_old_journal_reads_as_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an old journal reads as before.

    The candidate here is the one the embedded-implementation fixture
    pins, and its review record carries no ``artifacts`` — so the gate's
    transcript for it is demonstrated byte for byte against the committed
    fixture, beside the ``status``/``report`` checks."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head)
    review = read_records(repo / ".agentmarshal" / "journal", "CR-001")[-1]
    assert "artifacts" not in review
    monkeypatch.delenv(UPDATE_FIXTURES_ENV, raising=False)
    capsys.readouterr()

    assert main(["status", "CR-001"]) == 0
    assert "artifacts=" not in capsys.readouterr().out
    assert main(["report", "--task", "CR-001"]) == 0
    assert "artifacts=" not in capsys.readouterr().out

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


def test_gate_detects_record_path_collision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])

    # A second task opened on master after the candidate forks: its
    # record path exists on the target tip but not at the merge base.
    assert main(["open", "--title", "Other task"]) == 0
    other_records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-002" / "records"
    record_file = next(other_records.glob("*-opened.json"))
    record_relative = record_file.relative_to(repo)
    record_content = record_file.read_text(encoding="utf-8")
    _commit_all(repo, "open other task on master")

    # The candidate, forked before that, independently creates the same
    # record path (journal-only, so only the collision check applies).
    _git(repo, "switch", "--quiet", "-c", "candidate", base)
    (repo / record_relative).parent.mkdir(parents=True)
    (repo / record_relative).write_text(record_content, encoding="utf-8")
    contract_source = (
        repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    )
    contract_target = (
        repo / ".agentmarshal" / "journal" / "tasks" / "CR-002" / "contract.md"
    )
    contract_target.write_text(
        contract_source.read_text(encoding="utf-8").replace("CR-001", "CR-002"),
        encoding="utf-8",
    )
    head = _commit_all(repo, "independently open other task")

    passed, output = _run(repo, head, "master", head)

    assert not passed
    assert "already exist" in output


def test_two_candidates_add_the_same_artifact_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: two candidates add the same artifact path."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    artifact = (
        repo
        / ".agentmarshal"
        / "journal"
        / "tasks"
        / "CR-001"
        / "artifacts"
        / "shared-review.md"
    )
    artifact.parent.mkdir()
    artifact.write_bytes(b"base candidate\n")
    _commit_all(repo, "add artifact on master")

    _git(repo, "switch", "--quiet", "-c", "artifact-candidate", base)
    artifact.parent.mkdir()
    artifact.write_bytes(b"other candidate\n")
    head = _commit_all(repo, "independently add same artifact")

    passed, output = _run(repo, head, "master", head)

    relative = artifact.relative_to(repo).as_posix()
    assert not passed
    assert f"record paths already exist on the base: {relative}" in output


def _candidate_head(repo: Path, branch: str, base: str, mutate: object) -> str:
    """Commit a candidate on its own branch, evaluate from a clean master."""

    _git(repo, "switch", "--quiet", "-c", branch, base)
    mutate()  # type: ignore[operator]
    head = _commit_all(repo, branch)
    _git(repo, "switch", "--quiet", "master")
    return head


def test_gate_refuses_record_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    opened = next(records.glob("*-opened.json"))

    def modify() -> None:
        opened.write_text(opened.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    head = _candidate_head(repo, "tamperer", base, modify)
    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "append-only" in output

    def delete() -> None:
        _git(repo, "rm", "--quiet", str(opened.relative_to(repo)))

    head = _candidate_head(repo, "deleter", base, delete)
    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "append-only" in output


@pytest.mark.parametrize("operation", ["modify", "delete"])
def test_gate_refuses_a_modified_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    operation: str,
) -> None:
    """Scenario: the gate refuses a modified artifact."""

    repo, opened = _gate_repo(tmp_path, monkeypatch, ["src/"])
    prose = tmp_path / "review.md"
    prose.write_bytes(b"review evidence\n")
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
                "--commit",
                opened,
                "--verdict",
                "approved",
                "--role",
                "qa",
                "--vendor",
                "human",
                "--model",
                "none",
                "--email",
                _REVIEWER_EMAIL,
                "--prose",
                str(prose),
            ]
        )
        == 0
    )
    artifact = next(
        (
            repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts"
        ).iterdir()
    )
    base = _commit_all(repo, "record review evidence")

    def tamper() -> None:
        if operation == "modify":
            artifact.write_bytes(b"changed\n")
        else:
            artifact.unlink()

    head = _candidate_head(repo, f"artifact-{operation}", base, tamper)
    passed, output = _run(repo, head, base, head)

    assert not passed
    relative = artifact.relative_to(repo).as_posix()
    assert (
        f"FAIL: append-only violation, records modified, deleted or renamed: {relative}"
    ) in output


def test_gate_refuses_record_rename_out_of_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    opened = next(records.glob("*-opened.json"))

    def rename_out() -> None:
        _git(
            repo,
            "mv",
            str(opened.relative_to(repo)),
            ".agentmarshal/journal/tasks/CR-001/evacuated.json",
        )

    head = _candidate_head(repo, "evacuator", base, rename_out)
    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "append-only" in output


def test_gate_refuses_case_variant_reviewer_email(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _approve(repo, head, email="Worker@Test.INVALID")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "declared reviewer identity differs" in output


def test_gate_refuses_invalid_added_records(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    opened = next(records.glob("*-opened.json"))
    crafted_name = "01" + "A" * 24 + "-opened.json"

    def add_malformed() -> None:
        (records / crafted_name).write_text("not json\n", encoding="utf-8")

    head = _candidate_head(repo, "malformed", base, add_malformed)
    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "invalid added records" in output

    original = opened.read_text(encoding="utf-8")

    def add_mismatched() -> None:
        (records / crafted_name).write_text(
            original.replace("CR-001", "CR-002"), encoding="utf-8"
        )

    head = _candidate_head(repo, "mismatched", base, add_mismatched)
    passed, output = _run(repo, head, base, head)
    assert not passed
    assert "does not match its directory" in output


def test_the_gate_checks_added_records_by_the_current_rules(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a record a candidate adds is checked by every current rule.

    The gate's check of added records is a write-side check — the author can
    still fix the input — so a coordination session stamped 3 and a record
    bound to a finding stamped 3 are refused, while the same records already
    in the journal are read under their own schema's rules.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    session = create_session_record(
        "CR-001", "test", "role", "actor", "coordination", "done", 1, 2, 3
    )
    session["schema"] = 3
    completed = create_completed_record(
        "CR-001", "test", None, completed_finding="01J00000000000000000000000"
    )
    completed["schema"] = 3
    added = {
        f"{generate_ulid()}-session.json": session,
        f"{generate_ulid()}-completed.json": completed,
    }

    def add_low_schema_records() -> None:
        for name, record in added.items():
            (records / name).write_text(json.dumps(record), encoding="utf-8")

    head = _candidate_head(repo, "low-schema", base, add_low_schema_records)
    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "invalid added records" in output
    assert "requires schema 6" in output
    assert "require schema 4" in output

    for name, record in added.items():
        (records / name).write_text(json.dumps(record), encoding="utf-8")
    journal_root = repo / ".agentmarshal" / "journal"
    read_types = {
        record["record_type"] for record in read_records(journal_root, "CR-001")
    }
    assert {"session", "completed"} <= read_types


def test_gate_reports_malformed_base_contract_without_traceback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    contract = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    valid_contract = contract.read_text(encoding="utf-8")

    # The base tree carries a malformed contract; the candidate restores
    # a valid one in the working tree, so the failure is reached only at
    # the base-tree scope check, not at working-tree status loading.
    contract.write_text("no header here\n", encoding="utf-8")
    base = _commit_all(repo, "corrupt contract on base")
    _implement(repo, "src/module.py")
    contract.write_text(valid_contract, encoding="utf-8")
    head = _commit_all(repo, "restore valid contract in working tree")
    capsys.readouterr()

    assert (
        main(
            [
                "gate",
                "--task",
                "CR-001",
                "--commit",
                head,
                "--base",
                base,
                "--pipeline-sha",
                head,
            ]
        )
        == 1
    )

    error_output = capsys.readouterr().err
    assert "contract in the base tree is invalid" in error_output
    assert "Traceback" not in error_output


def test_gate_refuses_second_opened_record(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"
    opened = next(records.glob("*-opened.json"))
    original = opened.read_text(encoding="utf-8")

    # A second, individually valid opened record: passes isolation checks
    # but makes the task unreadable after merge.
    def add_second_opened() -> None:
        (records / ("01" + "B" * 24 + "-opened.json")).write_text(
            original, encoding="utf-8"
        )

    head = _candidate_head(repo, "double-open", base, add_second_opened)
    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "multiple opened records" in output


def test_gate_refuses_non_utf8_git_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Git output that is not UTF-8 is a controlled refusal, never a traceback.

    The `-z` listings are the exception — a name's raw bytes are kept for
    matching rather than refused. Every other output still decodes
    strictly: a record whose bytes `git show` cannot return as UTF-8 is
    refused by name on the invalid-records line.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    records = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "records"

    def add_undecodable_record() -> None:
        (records / ("01" + "A" * 24 + "-session.json")).write_bytes(
            b"\xff\xfe not utf-8"
        )

    head = _candidate_head(repo, "bad-record", base, add_undecodable_record)
    capsys.readouterr()

    code = main(
        [
            "gate",
            "--task",
            "CR-001",
            "--commit",
            head,
            "--base",
            "master",
            "--pipeline-sha",
            head,
        ]
    )

    transcript = capsys.readouterr()
    assert code == 1
    assert "invalid added records" in transcript.out
    assert "non-UTF-8" in transcript.out
    assert "Traceback" not in transcript.out + transcript.err


def test_gate_requires_contract_in_base_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    base = _commit_all(repo, "seed without journal")
    assert main(["open", "--title", "Gate task"]) == 0
    head = _implement(repo, "src/module.py")

    with pytest.raises(GateError, match="base tree"):
        run_gate(repo, "CR-001", head, base, head)


def test_gate_allows_completion_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A completion transaction appends a terminal record to a task that is
    # open at the base; the open->done transition must pass, not trip the
    # base-state check.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    _git(repo, "switch", "--quiet", "-c", "completion", base)
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    head = _commit_all(repo, "complete CR-001")

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "task CR-001 is not closed at base" in output


def test_gate_refuses_candidate_on_a_task_closed_at_base(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Once a task is closed on the base tree, no non-measurement candidate
    # may merge against it (a session-only append is the exception below).
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "after-close", closed_base)
    head = _implement(repo, "src/more.py")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_allows_session_only_append_to_closed_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: measurements still accrue after completion."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "measure", closed_base)
    write_record(
        journal,
        "CR-001",
        create_session_record(
            "CR-001", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "record session for CR-001")

    passed, output = _run(repo, head, closed_base, head)

    assert passed, output
    assert "measurements-only append to a task closed at base" in output
    assert output.count("FAIL") == 0


def test_gate_allows_reopening_only_append_to_completed_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a reopening lands through the gate.

    The completed record is committed into the base. The candidate adds only
    the reopening record, so the test exercises the base-state check.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "reopen", closed_base)
    assert main(["reopen", "--task", "CR-001", "--reason", "More work found"]) == 0
    head = _commit_all(repo, "reopen CR-001")

    candidate_paths = _git(repo, "diff", "--name-only", closed_base, head).splitlines()
    assert len(candidate_paths) == 1
    assert candidate_paths[0].startswith(".agentmarshal/journal/tasks/CR-001/records/")
    assert candidate_paths[0].endswith("-reopened.json")

    passed, output = _run(repo, head, closed_base, head)

    assert passed, output
    assert (
        "PASS: reopening append to a task completed at base "
        "(reopening is admitted post-terminal)" in output
    )
    assert load_task_status(journal, "CR-001").state == "open"


def test_the_admission_rule_refuses_a_reopening_after_abandonment() -> None:
    """The rule both the projection and the gate apply, pinned on its own.

    Through the gate this case never reaches the base-state branch — the
    candidate's projection refuses it first — so the branch's rule is tested
    here rather than only by an outcome another check produces."""

    from agentmarshal.journal.status import record_type_is_admitted_after_terminal

    assert record_type_is_admitted_after_terminal("reopened", "done")
    assert not record_type_is_admitted_after_terminal("reopened", "abandoned")
    assert record_type_is_admitted_after_terminal("session", "done")
    assert record_type_is_admitted_after_terminal("session", "abandoned")
    assert not record_type_is_admitted_after_terminal("review", "done")


def test_gate_refuses_reopening_only_append_to_abandoned_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an abandoned task cannot be reopened through the gate.

    End to end, the refusal comes from the candidate's own projection, which
    the gate loads before any base-state check: a reopening after abandonment
    makes that projection invalid. The gate's base-state branch for the same
    case is therefore defence in depth, and the rule it applies is pinned
    directly by test_the_admission_rule_refuses_a_reopening_after_abandonment.
    """

    repo, _base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_abandoned_record("CR-001", "test", "Stop"))
    abandoned_base = _commit_all(repo, "abandon CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "reopen", abandoned_base)
    write_record(journal, "CR-001", create_reopened_record("CR-001", "test", "Retry"))
    head = _commit_all(repo, "try to reopen CR-001")

    with pytest.raises(GateError, match="an abandoned task cannot be reopened"):
        _run(repo, head, abandoned_base, head)


def test_gate_refuses_review_only_append_to_closed_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: other work on a closed task is still refused.

    As with the abandoned reopening, the candidate's own projection refuses a
    review after a terminal record before the base-state check runs; this pins
    the end-to-end outcome, not which of the two checks produced it.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "review", closed_base)
    write_record(
        journal,
        "CR-001",
        create_review_record(
            "CR-001",
            "test",
            closed_base,
            "approved",
            "qa",
            "test",
            "test-model",
            _REVIEWER_EMAIL,
            [],
        ),
    )
    head = _commit_all(repo, "review CR-001 after completion")

    with pytest.raises(GateError, match="lifecycle record after a terminal record"):
        _run(repo, head, closed_base, head)


def test_gate_refuses_measurements_lane_with_another_tasks_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The measurements exception is per-task: a session record belonging to
    # a different task must not authorize a change against a closed one.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "cross-task", closed_base)
    write_record(
        journal,
        "CR-002",
        create_session_record(
            "CR-002", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "record a CR-002 session while gating closed CR-001")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_refuses_artifact_only_append_to_closed_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The measurements lane requires at least one session record: a
    # journal candidate adding only a non-record document to a closed task
    # is not a measurement and is still refused by the base-state check.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "note", closed_base)
    (journal / "tasks" / "CR-001" / "note.md").write_text("late\n", encoding="utf-8")
    head = _commit_all(repo, "add a note to a closed task")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_passes_approved_review_with_advisory_findings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Advisory findings never block a merge: an approved review carrying
    # them still passes the gate's review check.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    assert (
        main(
            [
                "submit-review",
                "--task",
                "CR-001",
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
                "--advisory-finding",
                "F1",
                "--advisory-finding",
                "F2",
            ]
        )
        == 0
    )

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert output.count("FAIL") == 0


def test_gate_measurements_lane_allows_a_new_supplementary_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A session record plus a genuinely new supplementary artifact under
    # the task directory is a valid measurements append to a closed task.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "measure-artifact", closed_base)
    artifact = journal / "tasks" / "CR-001" / "artifacts" / "prompt.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("prompt\n", encoding="utf-8")
    write_record(
        journal,
        "CR-001",
        create_session_record(
            "CR-001", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "record session and a new artifact")

    passed, output = _run(repo, head, closed_base, head)

    assert passed, output
    assert "measurements-only append to a task closed at base" in output


def test_gate_measurements_lane_refuses_modifying_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Appended evidence must never authorize a mutation of an existing
    # file: a session record bundled with a contract.md change on a closed
    # task is refused because the change is not strictly additive.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 on master")

    _git(repo, "switch", "--quiet", "-c", "tamper-contract", closed_base)
    contract = journal / "tasks" / "CR-001" / "contract.md"
    contract.write_text(
        contract.read_text(encoding="utf-8") + "\nmutated\n", encoding="utf-8"
    )
    write_record(
        journal,
        "CR-001",
        create_session_record(
            "CR-001", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "session plus a contract mutation")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_measurements_lane_refuses_modifying_existing_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Modifying an existing artifact (not adding one) is not additive and
    # is refused even alongside a session record.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    artifact = journal / "tasks" / "CR-001" / "artifacts" / "prompt.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("original\n", encoding="utf-8")
    write_record(journal, "CR-001", create_completed_record("CR-001", "test", base))
    closed_base = _commit_all(repo, "complete CR-001 with an artifact")

    _git(repo, "switch", "--quiet", "-c", "mutate-artifact", closed_base)
    artifact.write_text("changed\n", encoding="utf-8")
    write_record(
        journal,
        "CR-001",
        create_session_record(
            "CR-001", "test", "lead", "opus", "implementation", "done", 10, 20, 30
        ),
    )
    head = _commit_all(repo, "session plus an artifact mutation")

    passed, output = _run(repo, head, closed_base, head)

    assert not passed
    assert "already closed at base" in output


def test_gate_warns_on_leak_without_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    # An added line trips the built-in secret signatures.
    head = _implement(repo, "src/module.py", "aws_key = 'AKIAIOSFODNN7EXAMPLE'\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    # Advisory: the gate warns but still passes, and never emits a FAIL.
    assert passed, output
    assert output.count("FAIL") == 0
    assert "WARN: possible leak in candidate additions" in output
    assert "aws-access-key-id" in output


def test_the_merge_boundary_reports_the_same_detail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the merge boundary reports the same detail."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    secret = "AKIAIOSFODNN7EXAMPLE"
    head = _implement(repo, "src/module.py", f"key = '{secret}'\n")
    _approve(repo, head)

    passed, gate_output = _run(repo, head, base, head)
    capsys.readouterr()
    assert main(["leak-scan", "--base", base, "--commit", head]) == 1
    standalone = capsys.readouterr()

    detail = "src/module.py: aws-access-key-id"
    gate_line = next(
        line for line in gate_output.splitlines() if line.startswith("WARN:")
    )
    assert passed, gate_output
    assert gate_line == (
        f"WARN: possible leak in candidate additions (advisory, not blocking): {detail}"
    )
    assert standalone.out == (
        f"leak-scan: possible leaks in added content (file: what matched): {detail}\n"
    )
    assert secret not in gate_output
    assert secret not in standalone.out


def test_the_transcripts_line_is_bounded_and_says_what_it_left_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the transcript's line is bounded and says what it left out."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    for index in range(21):
        head = _implement(
            repo,
            f"src/secret{index:02}.py",
            "key = 'AKIAIOSFODNN7EXAMPLE'\n",
        )
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    gate_line = next(line for line in output.splitlines() if line.startswith("WARN:"))
    assert passed, output
    assert "src/secret00.py: aws-access-key-id" in gate_line
    assert "src/secret20.py: aws-access-key-id" not in gate_line
    assert gate_line.endswith(", and 1 more not shown")


def test_gate_leak_scan_is_clean_for_benign_additions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py", "def add(a, b):\n    return a + b\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "WARN:" not in output


def test_gate_leak_scan_uses_configured_private_markers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": ["internal.example.invalid"]}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # Commit the config into the base so the marker only trips on the
    # candidate's own added content, not on the config declaration itself.
    base = _commit_all(repo, "configure private markers")
    head = _implement(repo, "src/host.py", "HOST = 'internal.example.invalid'\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "WARN: possible leak in candidate additions" in output
    assert "private-marker" in output


def test_gate_leak_scan_names_the_file_whatever_prefix_the_repo_configures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A repository's own diff prefix does not reach the scan's path parsing.

    The parser strips "b/", and diff.dstPrefix can make git emit anything;
    "-c diff.noprefix=false" does not override it, so the callers fix the
    prefix with --src-prefix/--dst-prefix instead."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    # Repository configuration, not content: it changes what git's own diff
    # headers look like for every caller that does not override it.
    _git(repo, "config", "diff.dstPrefix", "candidate/")
    _git(repo, "config", "diff.srcPrefix", "baseline/")
    head = _implement(repo, "src/keys.py", "KEY = 'AKIAIOSFODNN7EXAMPLE'\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "src/keys.py: aws-access-key-id" in output
    assert "candidate/src/keys.py" not in output


def test_gate_leak_scan_reads_markers_from_base_not_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/", ".agentmarshal/"])
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": ["internal.example.invalid"]}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    base = _commit_all(repo, "configure private markers")

    # The candidate tries to weaken its own scan: drop the marker from config
    # and, in the same change, add content the base-configured marker catches.
    data["leak_scan"] = {"private_markers": []}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    src = repo / "src"
    src.mkdir(exist_ok=True)
    (src / "host.py").write_text(
        "HOST = 'internal.example.invalid'\n", encoding="utf-8"
    )
    head = _commit_all(repo, "weaken config and add marked content")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    # Config comes from the base tree, so the candidate cannot suppress the
    # warning by editing its own project.json.
    assert passed, output
    assert "WARN: possible leak in candidate additions" in output
    assert "private-marker" in output


def test_gate_leak_scan_scans_binary_marked_file_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A candidate marks its file 'binary' in .gitattributes; without --text
    # git would emit "Binary files differ" and hide the secret. --text forces
    # content, so the added secret is still scanned.
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/", ".gitattributes"])
    (repo / ".gitattributes").write_text("src/secret.py binary\n", encoding="utf-8")
    src = repo / "src"
    src.mkdir(exist_ok=True)
    (src / "secret.py").write_text("key = 'AKIAIOSFODNN7EXAMPLE'\n", encoding="utf-8")
    head = _commit_all(repo, "binary-marked secret")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "WARN: possible leak in candidate additions" in output
    assert "aws-access-key-id" in output


def test_markers_from_tree_absent_project_json_yields_no_markers(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    (repo / "file.txt").write_text("x\n", encoding="utf-8")
    # A commit that deliberately has no .agentmarshal/project.json.
    ref = _commit_all(repo, "no project file")

    assert markers_from_tree(repo, ref) == ()


def test_markers_from_tree_bad_ref_raises_rather_than_dropping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    # An unknown ref is a real failure, surfaced — not silently "no markers".
    with pytest.raises(GateError):
        markers_from_tree(repo, "definitely-not-a-ref")


def test_gate_leak_scan_degrades_to_warning_on_bad_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": "not-a-list"}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    base = _commit_all(repo, "malformed leak_scan config")
    head = _implement(repo, "src/module.py", "code\n")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    # A malformed advisory config never blocks a merge: it degrades to a warn.
    assert passed, output
    assert output.count("FAIL") == 0
    assert "WARN: leak-scan skipped" in output


def test_one_undecodable_file_does_not_switch_the_scan_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: one file that does not decode does not switch the scan off.

    The reproduction published as proposal 026's fourth finding: a commit
    adding a text file holding a GitHub-token-shaped string and a file of
    random bytes must report the string — the binary file no longer leaves
    every other file unscanned."""
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    src = repo / "src"
    src.mkdir(exist_ok=True)
    (src / "secret.py").write_text(f"key = 'ghp_{'A1' * 18}'\n", encoding="utf-8")
    (src / "blob.bin").write_bytes(bytes(range(256)))
    head = _commit_all(repo, "secret plus binary")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "src/secret.py: github-token" in output
    assert "leak-scan skipped" not in output


def test_a_file_that_does_not_decode_is_named_not_passed_over_in_silence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a file that does not decode is named, not passed over in
    silence."""
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    src = repo / "src"
    src.mkdir(exist_ok=True)
    (src / "blob.bin").write_bytes(b"\xff\xfe\x00\x01 binary content \x80")
    head = _commit_all(repo, "binary only")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)
    capsys.readouterr()
    assert main(["leak-scan", "--base", base, "--commit", head]) == 0
    command = capsys.readouterr()

    assert passed, output
    assert "could not decode" in output
    assert "src/blob.bin" in output
    assert "could not decode" in command.err
    assert "src/blob.bin" in command.err


def test_the_gates_scan_stays_advisory_over_undecodable_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: the gate's scan stays advisory over undecodable files."""
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    src = repo / "src"
    src.mkdir(exist_ok=True)
    (src / "blob.bin").write_bytes(b"\xff\xfe\x00\x01 binary content \x80")
    head = _commit_all(repo, "binary only")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert output.count("FAIL") == 0
    assert "WARN: leak-scan could not decode" in output


def test_an_undecodable_path_that_carries_a_marker_is_described_not_printed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an undecodable path that carries a marker is described, not
    printed."""
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": ["internal.corp.invalid"]}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    base = _commit_all(repo, "configure private markers")
    asset = repo / "src" / "vendor" / "internal.corp.invalid"
    asset.mkdir(parents=True)
    (asset / "logo.bin").write_bytes(b"\xff\xfe\x00\x01 \x80")
    head = _commit_all(repo, "binary asset under a marker-named directory")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "WARN: leak-scan could not decode" in output
    assert "internal.corp.invalid" not in output
    assert "src/vendor/<private marker #1>/logo.bin" in output


def test_an_undecodable_path_that_is_itself_a_key_is_described_not_printed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an undecodable path that is itself a key is described, not
    printed."""
    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    keys = repo / "src" / "keys"
    keys.mkdir(parents=True)
    (keys / "AKIAIOSFODNN7EXAMPLE.bin").write_bytes(b"\xff\xfe\x00\x80")
    head = _commit_all(repo, "key-named binary")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "WARN: leak-scan could not decode" in output
    assert "AKIAIOSFODNN7EXAMPLE" not in output
    assert "src/keys/<aws-access-key-id>.bin" in output


def test_gate_judges_the_latest_acceptance_and_does_not_hunt_for_a_fitting_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An older valid acceptance must not rescue a later record that does not fit.

    Searching a record set for whichever entry justifies a merge is the opposite
    of what a merge authority does, so the last acceptance is judged as it
    stands — the same rule the review check already follows.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    _require_changes(repo, head, "F-001")
    _accept(repo, head)
    write_record(
        repo / ".agentmarshal" / "journal",
        "CR-001",
        create_acceptance_record(
            "CR-001",
            "0.1.0",
            head,
            "operator@example.invalid",
            ["F-999"],
            "a later acceptance that does not fit",
        ),
    )

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "does not cover the latest" in output
    assert "accepted over findings" not in output


def test_gate_sees_a_reopening_and_lets_work_land_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Closed-ness at base is the latest lifecycle record, not a terminal one.

    A task completed and then reopened projects as open, and the gate must
    agree — otherwise the reopening would be a projection with no effect and
    every candidate would still be refused.
    """

    repo, _base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal = repo / ".agentmarshal" / "journal"
    write_record(
        journal, "CR-001", create_completed_record("CR-001", "0.1.0", "0" * 40)
    )
    assert main(["reopen", "--task", "CR-001", "--reason", "not usable"]) == 0
    _git(repo, "add", ".agentmarshal")
    _git(repo, *_WRITER, "commit", "--quiet", "-m", "close and reopen CR-001")
    base = _git(repo, "rev-parse", "HEAD")
    head = _implement(repo, "src/module.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed, output
    assert "PASS: task CR-001 is not closed at base" in output


def test_renaming_a_named_document_counts_as_touched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["docs/"])
    _write_schema2_contract(repo, ["docs/"], documents=["docs/guide.md"])
    guide = repo / "docs" / "guide.md"
    guide.parent.mkdir()
    guide.write_text("guide\n", encoding="utf-8")
    base = _commit_all(repo, "name document")
    guide.rename(repo / "docs" / "other.md")
    head = _commit_all(repo, "rename document")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed
    assert "PASS: named documents touched (docs/guide.md)" in output


def test_deleting_an_invalid_base_side_manifest_is_not_examined_not_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The base holds bytes the candidate cannot repair; no footprint is declared."""

    manifest_path = ".agentmarshal/extensions/openspec.toml"
    repo, _ = _gate_repo(tmp_path, monkeypatch, [manifest_path])
    manifest = _write_extension_manifest(repo)
    manifest.write_text("schema = [\n", encoding="utf-8")
    base = _commit_all(repo, "parked an invalid manifest")
    manifest.unlink()
    head = _commit_all(repo, "delete it")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed
    assert "NOT EXAMINED: removal of extension 'openspec'" in output
    assert "removal incomplete" not in output


def test_named_manifest_that_git_cannot_show_as_text_is_a_refusal_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_schema2_contract(repo, ["src/"], extensions=["openspec"])
    manifest = _write_extension_manifest(repo)
    manifest.write_bytes(b"\xff\xfe not text")
    base = _commit_all(repo, "binary manifest at base")
    head = _implement(repo, "src/change.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: named extension 'openspec' manifest unreadable" in output


def test_named_manifest_with_a_bracket_in_its_name_is_read_as_an_object(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`<tree>:<path>` is an object name: a bracket is a character, not a glob."""

    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_schema2_contract(repo, ["src/"], extensions=["open[spec]"])
    manifest = repo / ".agentmarshal" / "extensions" / "open[spec].toml"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        "schema = 1\n"
        'name = "open[spec]"\n'
        'version = "1"\n'
        'footprint = ["openspec/"]\n'
        "documents = []\n"
        "artifacts = []\n"
        'install = "install"\n'
        'remove = "remove"\n',
        encoding="utf-8",
    )
    base = _commit_all(repo, "name a bracketed extension")
    head = _implement(repo, "openspec/change.md")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert passed
    assert "extensions: open[spec]" in output


def test_removal_check_sees_a_surviving_footprint_path_with_a_non_ascii_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """git C-quotes such a path unless asked for NUL separation; quoted, it
    would hide from the matcher and the removal would read as complete."""

    manifest_path = ".agentmarshal/extensions/openspec.toml"
    repo, _ = _gate_repo(tmp_path, monkeypatch, [manifest_path])
    _write_schema2_contract(repo, [manifest_path], extensions=["openspec"])
    manifest = _write_extension_manifest(repo)
    survivor = repo / "openspec" / "caf\u00e9.md"
    survivor.parent.mkdir()
    survivor.write_text("still here\n", encoding="utf-8")
    base = _commit_all(repo, "installed extension")
    manifest.unlink()
    head = _commit_all(repo, "delete the manifest, keep a file")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: extension 'openspec' removal incomplete" in output
    assert "openspec/caf\u00e9.md" in output


def test_a_symlink_at_the_manifest_path_on_the_base_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_schema2_contract(repo, ["src/"], extensions=["openspec"])
    real = _write_extension_manifest(repo)
    target = repo / "elsewhere.toml"
    real.rename(target)
    real.symlink_to(target)
    base = _commit_all(repo, "manifest is a symlink at base")
    head = _implement(repo, "src/change.py")
    _approve(repo, head)

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: named extension 'openspec' manifest unreadable" in output
    assert "symlink" in output


def test_sidecar_history_sees_an_artifact_replaced_by_a_symlink(tmp_path: Path) -> None:
    """A type change (file → symlink) in a committed sidecar history is tampering."""

    from agentmarshal.journal.gate import _sidecar_history_tampering

    repo = tmp_path / "sidecar"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    writer = ["-c", "user.name=T", "-c", "user.email=t@t.invalid"]
    artifact = (
        repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts" / "r.md"
    )
    artifact.parent.mkdir(parents=True)
    artifact.write_text("prose\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", *writer, "commit", "-q", "-m", "evidence"], cwd=repo, check=True
    )
    artifact.unlink()
    (repo / "elsewhere.md").write_text("other\n", encoding="utf-8")
    artifact.symlink_to(repo / "elsewhere.md")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", *writer, "commit", "-q", "-m", "swap"], cwd=repo, check=True)

    tampered = _sidecar_history_tampering(repo, ".agentmarshal/journal")

    assert ".agentmarshal/journal/tasks/CR-001/artifacts/r.md" in tampered


def test_findings_gate_escapes_record_and_contract_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a refused character prints escaped in the gate's transcript.

    The records are built in memory — today's read rules would refuse the
    finding id, the finding ids and the acceptance fields on disk — which is
    the shape a journal written before the rule existed, or a record written
    around the writer with a lowered schema, can hand the findings gate.
    """

    repo, _base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    journal_root = repo / ".agentmarshal" / "journal"
    task = TaskStatus(
        task_id="CR-001",
        contract=ContractHeader(
            schema=1,
            id="CR-001",
            title="Gate task",
            scope=("src/\u202ex", "lib\nforged"),
            acceptance=(),
        ),
        records=(
            {"id": "r-open", "record_type": "opened", "created_at": "t0"},
            {
                "id": "r-f\n1\u202e",
                "record_type": "finding",
                "created_at": "t1",
                "summary": "claimed\n\u202e",
                "artifacts": [{"ref": "evidence/x\ny\u202e.md", "hash": "0" * 64}],
            },
            {
                "id": "r-review",
                "record_type": "review",
                "created_at": "t2",
                "reviewed_finding": "r-f\n1\u202e",
                "verdict": "changes_required",
                "findings": ["F-1\nforged", "F-2\u202e"],
                "reviewer": {
                    "role": "qa",
                    "vendor": "v",
                    "model": "m",
                    "email": "outsider@test.invalid",
                },
            },
            {
                "id": "r-acceptance",
                "record_type": "acceptance",
                "created_at": "t3",
                "accepted_finding": "r-f\n1\u202e",
                "accepted_by": "op\nerator\u202e",
                "findings": ["F-1\nforged", "F-2\u202e"],
                "reason": "looks\nfine\u202e",
            },
        ),
        state="open",
    )
    monkeypatch.setattr(gate_module, "load_task_status", lambda *_args, **_keys: task)

    report = run_findings_gate(journal_root, "CR-001")

    transcript = "\n".join(report.lines)
    assert (
        "FAIL: findings lane requires an empty scope; declared scope: "
        "src/\\u202ex, lib\\nforged" in report.lines
    )
    assert (
        "PASS: accepted over findings F-1\\nforged, F-2\\u202e by "
        "op\\nerator\\u202e; not an approving review" in report.lines
    )
    assert (
        "NOT VERIFIED: artifact evidence/x\\ny\\u202e.md does not resolve "
        "locally" in report.lines
    )
    # No refused character reaches the transcript raw: nothing prints as a
    # line the tool never said or in an order its bytes do not have.
    assert "\u202e" not in transcript


def test_gate_escapes_record_text_in_the_diff_lane(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a refused character prints escaped in the gate's transcript.

    Same scenario, other lane: the candidate's records are handed to the
    gate in memory — a journal that read rules older than the refusal wrote
    them, or a writer around the writer, lands exactly this shape.
    """

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    head = _implement(repo, "src/module.py")
    hostile_records = [
        {
            "record_type": "review",
            "reviewed_commit": head,
            "verdict": "changes_required",
            "findings": ["F-1\n\u202e", "F-2"],
            "reviewer": {
                "role": "qa",
                "vendor": "v",
                "model": "m",
                "email": "outsider@test.invalid",
            },
        },
        {
            "record_type": "acceptance",
            "accepted_commit": head,
            "accepted_by": "op\nerator\u202e",
            "findings": ["F-1\n\u202e"],
            "reason": "settled\n\u202e",
        },
    ]
    monkeypatch.setattr(
        gate_module, "read_records", lambda *_args, **_keys: hostile_records
    )

    report = run_gate(repo, "CR-001", head, base, head)

    transcript = "\n".join(report.lines)
    assert (
        f"FAIL: acceptance of {head[:12]} does not cover the latest review's "
        "findings (outstanding: F-1\\n\\u202e, F-2; accepted: F-1\\n\\u202e)"
        in report.lines
    )
    assert "\u202e" not in transcript


def _write_or_skip(repo: Path, name: str) -> None:
    """Commit-ready file at *name*, or skip where the filesystem refuses it.

    A newline or a bidirectional override is a legal character in a Linux
    file name and git accepts both — the candidate could carry either — but
    a filesystem may refuse one, and what the scenario demonstrates is what
    the gate prints for the name, not whether this platform allows it.
    """

    try:
        (repo / name).write_text("x = 1\n", encoding="utf-8")
    except OSError:
        pytest.skip(f"the filesystem refuses a file named {name!r}")


def _write_bytes_or_skip(directory: Path, name: bytes, content: bytes) -> None:
    """Commit-ready file at a byte name, or skip where it is refused.

    A raw 0xFF byte is a legal Linux file name — git stores it — so the
    candidate and the base tree could both carry one; a filesystem that
    refuses it only changes whether this platform can show what the gate
    prints for the name, not what the gate should print.
    """

    try:
        descriptor = os.open(
            os.path.join(os.fsencode(directory), name),
            os.O_CREAT | os.O_WRONLY,
            0o644,
        )
        os.write(descriptor, content)
        os.close(descriptor)
    except OSError:
        pytest.skip(f"the filesystem refuses a file named {name!r}")


def test_a_candidate_path_that_would_forge_a_line_is_named_in_escaped_form(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a candidate path that would forge a line is named in escaped form.

    A file named with a newline could print a line the gate never said —
    `gate: passed` among them. Named in escaped form on the scope line, it
    stays on the line that names it."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_or_skip(repo, "forged\ngate: passed")
    head = _commit_all(repo, "a name that fights the transcript")
    capsys.readouterr()

    code = main(_gate_arguments(base, head))

    transcript = capsys.readouterr()
    assert code == 1
    assert "forged\\ngate: passed" in transcript.out
    assert "forged\ngate: passed" not in transcript.out
    # No line the name forged appears: the escaped form is part of the FAIL
    # line, and the verdict is the refusal this run actually reached.
    printed_lines = transcript.out.split("\n") + transcript.err.split("\n")
    assert "gate: passed" not in printed_lines
    assert "gate: refused" in transcript.err


def test_a_path_carrying_a_refused_character_is_named_in_escaped_form(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a path carrying a refused character is named in escaped form.

    A right-to-left override would make the scope line read in an order its
    bytes do not have; named in escaped form, the override prints as
    `\\u202e`."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_or_skip(repo, "spoof\u202e.py")
    head = _commit_all(repo, "a name with an override")
    capsys.readouterr()

    code = main(_gate_arguments(base, head))

    transcript = capsys.readouterr()
    assert code == 1
    assert "spoof\\u202e.py" in transcript.out
    assert "\u202e" not in transcript.out


def test_a_rename_source_carrying_a_refused_character_is_named_in_escaped_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a rename's source or target carrying a refused character is
    named in escaped form.

    The scope line names a rename's source among the paths outside contract
    scope; a source named with a newline is named escaped there."""

    repo, _ = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_or_skip(repo, "moved\ngate: passed")
    base = _commit_all(repo, "a file outside scope")
    destination = repo / "src" / "renamed.py"
    destination.parent.mkdir()
    _git(repo, "mv", "moved\ngate: passed", "src/renamed.py")
    head = _commit_all(repo, "rename into scope")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "FAIL: paths outside contract scope: moved\\ngate: passed" in output
    assert "moved\ngate: passed" not in output


def test_a_refusal_names_a_forgeable_value_in_escaped_form(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a refusal names a forgeable value in escaped form.

    A `--commit` value is echoed in the failed git command the refusal
    names; a newline in it would print a line the gate never wrote. The
    escaped message is the same whether the CLI prints it or a caller reads
    the exception — the escape happens in `GateError` itself."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    forged = "not-a-commit\ngate: passed"
    with pytest.raises(GateError) as raised:
        run_gate(repo, "CR-001", forged, base, None)
    message = str(raised.value)
    assert "not-a-commit\\ngate: passed" in message
    assert "not-a-commit\ngate: passed" not in message

    capsys.readouterr()
    code = main(
        [
            "gate",
            "--task",
            "CR-001",
            "--commit",
            forged,
            "--base",
            base,
        ]
    )

    transcript = capsys.readouterr()
    assert code == 1
    assert "not-a-commit\\ngate: passed" in transcript.err
    assert "not-a-commit\ngate: passed" not in transcript.err
    assert "gate: passed" not in transcript.err.split("\n")


def test_a_candidate_whose_values_carry_no_refused_character_prints_as_before(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a candidate whose values carry no refused character prints as before.

    The committed fixture for the embedded implementation lane is the
    byte-for-byte demonstration, so this test names the scenario and
    delegates rather than copying it."""

    test_default_run_transcript_matches_the_committed_fixture(
        tmp_path, monkeypatch, capsys, "embedded-implementation"
    )


def test_a_placement_refusal_names_a_forgeable_host_in_escaped_form(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a refusal names a forgeable value in escaped form.

    A sidecar project's host comes from project.json — configuration the
    candidate's tree carries — and the gate prints the placement refusal
    as it stands. A host carrying a newline would print lines the gate
    never wrote, `gate: passed` among them; the refusal escapes the value
    where the CLI prints it."""

    project = tmp_path / "project"
    (project / ".agentmarshal").mkdir(parents=True)
    host = "/not-a-host\ngate: passed\nforged"
    (project / ".agentmarshal" / "project.json").write_text(
        json.dumps({"placement": "sidecar", "host": host}), encoding="utf-8"
    )
    monkeypatch.chdir(project)

    code = main(["gate", "--task", "CR-001", "--commit", "c", "--base", "b"])

    transcript = capsys.readouterr()
    assert code == 1
    assert (
        "sidecar host /not-a-host\\ngate: passed\\nforged: path does not exist"
        in transcript.err
    )
    assert "gate: passed" not in transcript.err.split("\n")


def test_a_record_collision_names_a_path_carrying_a_refused_character_in_escaped_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a candidate path that would forge a line is named in escaped form.

    The record-collision line names a path the candidate adds that the
    base tree already holds. The base listing must read the name raw — a
    name git C-quotes never equals the raw name the candidate's diff
    returns, and the collision would go unseen."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    artifact = (
        repo
        / ".agentmarshal"
        / "journal"
        / "tasks"
        / "CR-001"
        / "artifacts"
        / "forged\ngate: passed.md"
    )
    artifact.parent.mkdir(parents=True, exist_ok=True)
    try:
        artifact.write_text("base candidate\n", encoding="utf-8")
    except OSError:
        pytest.skip(f"the filesystem refuses a file named {artifact.name!r}")
    _commit_all(repo, "add artifact on master")

    _git(repo, "switch", "--quiet", "-c", "candidate", base)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("other candidate\n", encoding="utf-8")
    head = _commit_all(repo, "independently add same artifact")

    passed, output = _run(repo, head, "master", head)

    relative = artifact.relative_to(repo).as_posix().replace("\n", "\\n")
    assert not passed
    assert f"record paths already exist on the base: {relative}" in output
    assert "forged\ngate: passed" not in output


def test_a_tampered_evidence_path_carrying_a_refused_character_is_named_in_escaped_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a path carrying a refused character is named in escaped form.

    The append-only line names evidence a sidecar's committed history
    shows modified. The history listing must read the name raw — a name
    git C-quotes fails the evidence-path test, and the line would report
    integrity the check never examined."""

    host, sidecar, base, head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Sidecar gate", "--scope", "app.txt"]) == 0
    artifact = (
        sidecar
        / ".agentmarshal"
        / "journal"
        / "tasks"
        / "CR-001"
        / "artifacts"
        / "forged\ngate: passed.md"
    )
    artifact.parent.mkdir(parents=True, exist_ok=True)
    try:
        artifact.write_text("evidence\n", encoding="utf-8")
    except OSError:
        pytest.skip(f"the filesystem refuses a file named {artifact.name!r}")
    _commit_all(sidecar, "evidence")
    artifact.write_text("rewritten\n", encoding="utf-8")
    _commit_all(sidecar, "rewrite evidence")

    report = run_gate(
        host,
        "CR-001",
        head,
        base,
        head,
        journal_root=sidecar / ".agentmarshal" / "journal",
        review_required=False,
    )
    output = "\n".join(report.lines)

    assert not report.passed
    assert (
        "append-only violation, records modified, deleted or renamed: "
        ".agentmarshal/journal/tasks/CR-001/artifacts/forged\\ngate: passed.md"
        in output
    )
    assert "forged\ngate: passed" not in output


def test_a_path_whose_bytes_are_not_utf8_is_named_in_escaped_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a path whose bytes are not UTF-8 is named in escaped form.

    The candidate diff's `-z` listing returns the name's raw bytes; a
    strict decode would refuse the run over a name the scope check only
    had to compare. Decoded with the bytes kept for matching, the name
    reaches the scope line, where the undecodable byte prints escaped."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    _write_bytes_or_skip(repo, b"\xff.py", b"x = 1\n")
    head = _commit_all(repo, "a name that is not UTF-8")

    passed, output = _run(repo, head, base, head)

    assert not passed
    assert "paths outside contract scope: \\udcff.py" in output


def test_a_base_tree_path_whose_bytes_are_not_utf8_is_named_in_escaped_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a path whose bytes are not UTF-8 is named in escaped form.

    Same scenario from the trusted side: the base tree's `ls-tree -z`
    listing holds the name's raw bytes, and a base tree carrying one used
    to refuse every run at the decode. Kept for matching instead, the run
    reaches its verdict and the collision line names the byte escaped."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    artifacts = repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "artifacts"
    artifacts.mkdir()
    _write_bytes_or_skip(artifacts, b"\xff.md", b"base candidate\n")
    _commit_all(repo, "add artifact on master")

    _git(repo, "switch", "--quiet", "-c", "candidate", base)
    artifacts.mkdir(exist_ok=True)
    _write_bytes_or_skip(artifacts, b"\xff.md", b"other candidate\n")
    head = _commit_all(repo, "independently add same artifact")

    passed, output = _run(repo, head, "master", head)

    assert not passed
    assert (
        "record paths already exist on the base: "
        ".agentmarshal/journal/tasks/CR-001/artifacts/\\udcff.md" in output
    )


def test_an_unusual_file_name_is_matched_by_its_real_path_not_gits_quoted_form(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: an unusual file name is matched by its real path, not git's
    quoted form.

    `café` carries no refused character, but git C-quotes the name in a
    plain listing; read NUL-separated, the base tree holds the path itself
    and a collision the quoted form would have hidden is found."""

    repo, base = _gate_repo(tmp_path, monkeypatch, ["src/"])
    artifact = (
        repo
        / ".agentmarshal"
        / "journal"
        / "tasks"
        / "CR-001"
        / "artifacts"
        / "café.md"
    )
    artifact.parent.mkdir()
    artifact.write_text("base candidate\n", encoding="utf-8")
    _commit_all(repo, "add artifact on master")

    _git(repo, "switch", "--quiet", "-c", "candidate", base)
    artifact.parent.mkdir(exist_ok=True)
    artifact.write_text("other candidate\n", encoding="utf-8")
    head = _commit_all(repo, "independently add same artifact")

    passed, output = _run(repo, head, "master", head)

    assert not passed
    assert (
        "record paths already exist on the base: "
        ".agentmarshal/journal/tasks/CR-001/artifacts/café.md" in output
    )
