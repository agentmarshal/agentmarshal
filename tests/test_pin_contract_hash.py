"""The contract's hash pinned where the contract is written.

CR-171 is the transition task of ADR-0018 decision 1: `open`, `amend` and
`migrate` pin the sha256 of the contract they establish, `open
--contract-file` takes a contract written first, and `status` says when the
contract drifted from its last pin.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.contracts import contract_sha256, parse_contract
from agentmarshal.journal.open_task import journal_root
from agentmarshal.journal.records import (
    create_amendment_record,
    create_opened_record,
    read_records,
    write_record,
)
from agentmarshal.migrate import migrate_journal
from test_migrate import write_task
from test_placement import _host_and_sidecar


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(
        ["git", "init", "--quiet"], cwd=repo, check=True, capture_output=True
    )
    project_file = repo / ".agentmarshal" / "project.json"
    project_file.parent.mkdir()
    project_file.write_text('{"schema": 1}\n', encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def _contract_file(tmp_path: Path, task_id: str = "CR-099") -> Path:
    path = tmp_path / "contract.md"
    path.write_text(
        "+++\n"
        "schema = 1\n"
        f'id = "{task_id}"\n'
        'title = "Add a greeting helper"\n'
        'scope = ["src/"]\n'
        'acceptance = ["the helper greets"]\n'
        "+++\n\n"
        "# Add a greeting helper\n\n"
        "## Objective\n\n"
        "Greet.\n",
        encoding="utf-8",
    )
    return path


def _task_contract(repo: Path, task_id: str = "CR-001") -> Path:
    return journal_root(repo) / "tasks" / task_id / "contract.md"


def _pinned_hash(repo: Path, task_id: str = "CR-001") -> str:
    contract_path = _task_contract(repo, task_id)
    return contract_sha256(contract_path.read_bytes(), str(contract_path))


# --- the writers pin the contract they establish -------------------------


def test_open_pins_the_contract_it_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: open pins the contract it writes.

    The `opened` record carries `contract` — the `contract_sha256` of the
    contract the open wrote — and therefore stamps schema 7.
    """

    repo = _repo(tmp_path, monkeypatch)

    assert main(["open", "--title", "Task", "--scope", "src/"]) == 0

    opened = read_records(journal_root(repo), "CR-001")[0]
    assert opened["record_type"] == "opened"
    assert opened["contract"] == _pinned_hash(repo)
    assert opened["schema"] == 7


def test_amend_pins_the_contract_as_it_stands(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: amend pins the contract as it stands.

    The amendment's `contract` is the `contract_sha256` of the task's
    contract.md as it is at that moment — here, of a contract edited after
    the open pinned it.
    """

    repo = _repo(tmp_path, monkeypatch)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()
    contract_path = _task_contract(repo)
    contract_path.write_text(
        contract_path.read_text(encoding="utf-8") + "\nA late note.\n",
        encoding="utf-8",
    )

    assert main(["amend", "--task", "CR-001", "--reason", "a note"]) == 0

    amendment = read_records(journal_root(repo), "CR-001")[-1]
    assert amendment["record_type"] == "amendment"
    assert amendment["contract"] == _pinned_hash(repo)
    assert amendment["schema"] == 7


def test_amend_refuses_a_contract_that_does_not_parse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: amend refuses a contract that does not parse."""

    repo = _repo(tmp_path, monkeypatch)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()
    contract_path = _task_contract(repo)
    contract_path.write_text("not a contract\n", encoding="utf-8")

    assert main(["amend", "--task", "CR-001", "--reason", "a note"]) == 1

    assert [
        record["record_type"] for record in read_records(journal_root(repo), "CR-001")
    ] == ["opened"]


def test_amend_pins_the_journal_repositorys_copy_in_a_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: amend pins the journal repository's copy in a sidecar."""

    _host, sidecar, _base, _head = _host_and_sidecar(tmp_path, monkeypatch)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()

    assert main(["amend", "--task", "CR-001", "--reason", "a note"]) == 0

    journal = sidecar / ".agentmarshal" / "journal"
    contract_path = journal / "tasks" / "CR-001" / "contract.md"
    amendment = read_records(journal, "CR-001")[-1]
    assert amendment["contract"] == contract_sha256(
        contract_path.read_bytes(), str(contract_path)
    )


def test_migrate_pins_each_contract_it_writes(tmp_path: Path) -> None:
    """Scenario: migrate pins each contract it writes."""

    source = tmp_path / "v1"
    target = tmp_path / "v2"
    write_task(source, "open", "CR-001", "open")
    write_task(source, "open", "CR-002", "open")

    migrate_journal(source, target)

    for task_id in ("CR-001", "CR-002"):
        contract_path = target / "tasks" / task_id / "contract.md"
        opened = read_records(target, task_id)[0]
        assert opened["contract"] == contract_sha256(
            contract_path.read_bytes(), str(contract_path)
        )


# --- open takes a contract already written -------------------------------


def test_a_contract_written_first_becomes_the_tasks_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a contract written first becomes the task's contract."""

    repo = _repo(tmp_path, monkeypatch)
    provided = _contract_file(tmp_path)

    assert main(["open", "--contract-file", str(provided)]) == 0

    contract_path = _task_contract(repo)
    header = parse_contract(contract_path)
    assert header.id == "CR-001"
    assert header.title == "Add a greeting helper"
    assert header.scope == ("src/",)
    assert header.acceptance == ("the helper greets",)
    assert contract_path.read_text(encoding="utf-8").endswith("Greet.\n")
    opened = read_records(journal_root(repo), "CR-001")[0]
    assert opened["contract"] == _pinned_hash(repo)


def test_a_different_id_is_replaced_and_named_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a different id is replaced and named on stderr."""

    repo = _repo(tmp_path, monkeypatch)
    provided = _contract_file(tmp_path, task_id="CR-099")

    assert main(["open", "--contract-file", str(provided)]) == 0

    captured = capsys.readouterr()
    assert "CR-099" in captured.err
    assert "CR-001" in captured.err
    header = parse_contract(_task_contract(repo))
    assert header.id == "CR-001"


@pytest.mark.parametrize("extra", [["--title", "Task"], ["--scope", "src/"]])
def test_contract_file_cannot_combine_with_title_or_scope(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    extra: list[str],
) -> None:
    """Scenario: --contract-file cannot combine with --title or --scope."""

    repo = _repo(tmp_path, monkeypatch)
    provided = _contract_file(tmp_path)

    assert main(["open", "--contract-file", str(provided), *extra]) == 1

    assert "--contract-file" in capsys.readouterr().err
    assert not (journal_root(repo) / "tasks").exists()


@pytest.mark.parametrize(
    ("content", "directory"),
    [
        (None, False),
        ("not a contract\n", False),
        ("+++\nschema = 9\n+++\n", False),
        ("+++\nschema = 1\nid = 'CR-001'\n+++\n", False),
        (b"\xff\xfe not utf-8", False),
        (None, True),
    ],
    ids=[
        "missing",
        "no header",
        "unknown schema",
        "incomplete header",
        "not UTF-8",
        "a directory",
    ],
)
def test_a_missing_unreadable_or_invalid_file_is_refused_writing_nothing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    content: str | bytes | None,
    directory: bool,
) -> None:
    """Scenario: a missing, unreadable or invalid file is refused writing
    nothing.

    Unreadable is simulated portably — no chmod, which a suite running as
    root would read through anyway: a read of a directory raises OSError,
    and bytes that do not decode as UTF-8 are refused just the same.
    """

    repo = _repo(tmp_path, monkeypatch)
    provided = tmp_path / "contract.md"
    if directory:
        provided.mkdir()
    elif isinstance(content, bytes):
        provided.write_bytes(content)
    elif content is not None:
        provided.write_text(content, encoding="utf-8")

    assert main(["open", "--contract-file", str(provided)]) == 1

    assert str(provided) in capsys.readouterr().err
    assert not (journal_root(repo) / "tasks").exists()


def test_a_refused_contract_file_writes_nothing_to_an_existing_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a missing, unreadable or invalid file is refused writing
    nothing.

    With a task already opened, a refused ``--contract-file`` leaves the
    journal byte-for-byte as it was — no new task directory, no contract,
    no record.
    """

    repo = _repo(tmp_path, monkeypatch)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()
    journal = journal_root(repo)
    before = {
        path.relative_to(journal): path.read_bytes()
        for path in journal.rglob("*")
        if path.is_file()
    }
    invalid = tmp_path / "invalid.md"
    invalid.write_text("not a contract\n", encoding="utf-8")

    assert main(["open", "--contract-file", str(invalid)]) == 1

    assert capsys.readouterr().err
    after = {
        path.relative_to(journal): path.read_bytes()
        for path in journal.rglob("*")
        if path.is_file()
    }
    assert after == before


@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r"], ids=["LF", "CRLF", "lone-CR"])
def test_open_contract_file_keeps_the_contracts_line_endings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    ending: str,
) -> None:
    """Scenario: a contract written first becomes the task's contract.

    Whatever line ending the provided contract carries — LF, CRLF or a
    lone CR, which ``parse_contract_text`` splits on just the same — the
    written contract differs from the file only in the header's ``id``
    value, and the ``opened`` record pins the written contract's hash.
    """

    repo = _repo(tmp_path, monkeypatch)
    provided = tmp_path / "contract.md"
    original = ending.join(
        [
            "+++",
            "schema = 1",
            'id = "CR-099"',
            'title = "Add a greeting helper"',
            'scope = ["src/"]',
            'acceptance = ["the helper greets"]',
            "+++",
            "",
            "# Add a greeting helper",
            "",
            "Greet.",
            "",
        ]
    )
    provided.write_bytes(original.encode("utf-8"))

    assert main(["open", "--contract-file", str(provided)]) == 0

    contract_bytes = _task_contract(repo).read_bytes()
    expected = original.replace('id = "CR-099"', 'id = "CR-001"', 1)
    assert contract_bytes == expected.encode("utf-8")
    opened = read_records(journal_root(repo), "CR-001")[0]
    assert opened["contract"] == contract_sha256(contract_bytes, "the written contract")


@pytest.mark.parametrize(
    "key",
    ["id", '"id"', "'id'"],
    ids=["bare key", "double-quoted key", "single-quoted key"],
)
def test_the_id_forms_open_rewrites(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    key: str,
) -> None:
    """Scenario: a contract written first becomes the task's contract.

    The `id` written as the key `id`, `"id"` or `'id'` with a one-line
    string value on a line of its own — trailing whitespace and a comment
    kept — is the declaration `open` rewrites; every other byte is the
    author's.
    """

    repo = _repo(tmp_path, monkeypatch)
    provided = tmp_path / "contract.md"
    original = (
        "+++\n"
        "schema = 1\n"
        f"{key} = 'CR-099'   # written by hand\n"
        'title = "Task"\n'
        "scope = []\n"
        "acceptance = []\n"
        "+++\n\n"
        "Body.\n"
    )
    provided.write_text(original, encoding="utf-8")

    assert main(["open", "--contract-file", str(provided)]) == 0

    written = _task_contract(repo).read_text(encoding="utf-8")
    assert written == original.replace("'CR-099'", '"CR-001"', 1)
    opened = read_records(journal_root(repo), "CR-001")[0]
    assert opened["contract"] == _pinned_hash(repo)


@pytest.mark.parametrize(
    "value",
    [
        '"CR-099"',
        "'CR-099'",
        '"""CR-099"""',
        "'''CR-099'''",
        '"""CR-099""""',
        '"""CR-099"""""',
        "'''CR-099''''",
        '"CR-\\"099"',
    ],
    ids=[
        "basic string",
        "literal string",
        "one-line multi-line basic",
        "one-line multi-line literal",
        "a quote before the closing delimiter",
        "two quotes before the closing delimiter",
        "a quote before a literal closing delimiter",
        "escaped quote",
    ],
)
@pytest.mark.parametrize(
    "comment", ["", "   # written by hand"], ids=["bare", "with comment"]
)
def test_the_one_line_string_values_open_rewrites(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    value: str,
    comment: str,
) -> None:
    """Scenario: a contract written first becomes the task's contract.

    Every one-line string form TOML gives the ``id`` value — a basic or
    literal string, a one-line multi-line string of either kind carrying
    up to two quote characters before its closing delimiter, a basic
    string's escaped quote — is rewritten; the contract `open` writes
    differs from the file only in the value, and its hash is pinned.
    """

    repo = _repo(tmp_path, monkeypatch)
    provided = tmp_path / "contract.md"
    original = (
        "+++\n"
        "schema = 1\n"
        f"id = {value}{comment}\n"
        'title = "Task"\n'
        "scope = []\n"
        "acceptance = []\n"
        "+++\n\n"
        "Body.\n"
    )
    provided.write_text(original, encoding="utf-8")

    assert main(["open", "--contract-file", str(provided)]) == 0

    written = _task_contract(repo).read_text(encoding="utf-8")
    assert written == original.replace(value, '"CR-001"', 1)
    opened = read_records(journal_root(repo), "CR-001")[0]
    assert opened["contract"] == _pinned_hash(repo)


@pytest.mark.parametrize(
    "value",
    ['"😀"', '"\\u007f"', '"\\u0000"', '"CR-099\\u0000"'],
    ids=[
        "non-BMP character",
        "escaped DEL",
        "NUL, the probe's own value",
        "an id of the probe's form",
    ],
)
def test_the_id_value_open_rewrites_whatever_it_carries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    value: str,
) -> None:
    """Scenario: a contract written first becomes the task's contract.

    Whatever characters the author's ``id`` carries — a non-BMP
    character, an escaped DEL or NUL, an id that itself ends in NUL —
    the probe locating the declaration is a fixed ASCII value that
    differs from it, so its TOML encoding is always valid and exactly the
    declaration answers it. A line matching the ``id`` pattern inside a
    literal string precedes the declaration: a probe the parsed id could
    equal would name that line instead.
    """

    repo = _repo(tmp_path, monkeypatch)
    provided = tmp_path / "contract.md"
    original = (
        "+++\n"
        "schema = 1\n"
        "note = '''\n"
        'id = "decoy"\n'
        "'''\n"
        f"id = {value}\n"
        'title = "Task"\n'
        "scope = []\n"
        "acceptance = []\n"
        "+++\n\n"
        "Body.\n"
    )
    provided.write_text(original, encoding="utf-8")

    assert main(["open", "--contract-file", str(provided)]) == 0

    written = _task_contract(repo).read_text(encoding="utf-8")
    assert written == original.replace(value, '"CR-001"', 1)
    opened = read_records(journal_root(repo), "CR-001")[0]
    assert opened["contract"] == _pinned_hash(repo)


@pytest.mark.parametrize(
    "id_line",
    ['"i\\u0064" = "CR-099"', 'id = """\nCR-099\n"""'],
    ids=["escaped key", "multi-line value"],
)
def test_an_id_written_another_way_is_refused_naming_the_supported_forms(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    id_line: str,
) -> None:
    """Scenario: an id written any other way is refused naming the supported
    forms.

    A valid contract whose `id` parses but is written as an escaped key or
    a value spanning lines is refused with a message naming the forms
    `open` rewrites, and nothing is written — no task directory, no
    contract, no record.
    """

    repo = _repo(tmp_path, monkeypatch)
    provided = tmp_path / "contract.md"
    provided.write_text(
        "+++\n"
        "schema = 1\n"
        f"{id_line}\n"
        'title = "Task"\n'
        "scope = []\n"
        "acceptance = []\n"
        "+++\n\n"
        "Body.\n",
        encoding="utf-8",
    )

    assert main(["open", "--contract-file", str(provided)]) == 1

    err = capsys.readouterr().err
    assert '`"id"`' in err
    assert "`'id'`" in err
    assert "top-level table" in err
    assert not (journal_root(repo) / "tasks").exists()


# --- status shows when the contract drifted from its last pin ------------


def _open_and_edit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> Path:
    repo = _repo(tmp_path, monkeypatch)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()
    contract_path = _task_contract(repo)
    contract_path.write_text(
        contract_path.read_text(encoding="utf-8") + "\nA late note.\n",
        encoding="utf-8",
    )
    return repo


def test_a_drifted_contract_prints_the_drift_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a drifted contract prints the drift line.

    The line names both short hashes — the pin's and the current
    contract's — and says the edit should be recorded with `amend`.
    """

    repo = _open_and_edit(tmp_path, monkeypatch, capsys)
    pinned = read_records(journal_root(repo), "CR-001")[0]["contract"]

    assert main(["status", "CR-001"]) == 0

    out = capsys.readouterr().out
    drift = [line for line in out.splitlines() if "drift" in line.lower()]
    assert len(drift) == 1
    assert str(pinned)[:7] in drift[0]
    assert _pinned_hash(repo)[:7] in drift[0]
    assert "amend" in drift[0]


def test_a_contract_matching_its_pin_prints_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a contract matching its pin prints nothing."""

    _repo(tmp_path, monkeypatch)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()

    assert main(["status", "CR-001"]) == 0

    out = capsys.readouterr().out
    assert not any("drift" in line.lower() for line in out.splitlines())


def test_a_task_whose_records_carry_no_hash_prints_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a task whose records carry no hash prints nothing."""

    repo = _repo(tmp_path, monkeypatch)
    journal = journal_root(repo)
    task_directory = journal / "tasks" / "CR-001"
    task_directory.mkdir(parents=True)
    contract_path = task_directory / "contract.md"
    contract_path.write_text(
        "+++\nschema = 1\nid = 'CR-001'\ntitle = 'Task'\nscope = []\n"
        "acceptance = []\n+++\n",
        encoding="utf-8",
    )
    write_record(journal, "CR-001", create_opened_record("CR-001", "test"))

    assert main(["status", "CR-001"]) == 0

    out = capsys.readouterr().out
    assert not any("drift" in line.lower() for line in out.splitlines())


def test_a_later_record_without_a_hash_leaves_the_pin(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the latest hash-carrying record is the pin compared.

    An amendment written without `contract` does not erase the pin: the
    drift line still compares against the latest record that carries a
    hash — the opened record's — printing when the contract drifted from
    it and nothing while it matches.
    """

    repo = _repo(tmp_path, monkeypatch)
    journal = journal_root(repo)
    assert main(["open", "--title", "Task"]) == 0
    capsys.readouterr()
    write_record(journal, "CR-001", create_amendment_record("CR-001", "test", "a note"))
    pinned = read_records(journal, "CR-001")[0]["contract"]

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert not any("drift" in line.lower() for line in out.splitlines())

    contract_path = _task_contract(repo)
    contract_path.write_text(
        contract_path.read_text(encoding="utf-8") + "\nA late note.\n",
        encoding="utf-8",
    )

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    drift = [line for line in out.splitlines() if "drift" in line.lower()]
    assert len(drift) == 1
    assert str(pinned)[:7] in drift[0]


def test_the_drift_never_fails_the_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the drift never fails the command.

    A drifted contract is reported, not refused: `status` answers with the
    drift line and exit status 0.
    """

    _open_and_edit(tmp_path, monkeypatch, capsys)

    assert main(["status", "CR-001"]) == 0


def test_the_latest_hash_carrying_record_is_the_pin_compared(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the latest hash-carrying record is the pin compared.

    After `amend` re-pins the edited contract, the drift line compares
    against the amendment's hash — a match — until the contract moves away
    from it too.
    """

    repo = _open_and_edit(tmp_path, monkeypatch, capsys)
    assert main(["amend", "--task", "CR-001", "--reason", "the note stays"]) == 0
    capsys.readouterr()

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    assert not any("drift" in line.lower() for line in out.splitlines())

    contract_path = _task_contract(repo)
    contract_path.write_text(
        contract_path.read_text(encoding="utf-8") + "\nAnother note.\n",
        encoding="utf-8",
    )
    amendment_hash = read_records(journal_root(repo), "CR-001")[-1]["contract"]

    assert main(["status", "CR-001"]) == 0
    out = capsys.readouterr().out
    drift = [line for line in out.splitlines() if "drift" in line.lower()]
    assert len(drift) == 1
    assert str(amendment_hash)[:7] in drift[0]
