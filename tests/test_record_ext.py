"""`agentmarshal record-ext` — a shared extension's result, on the record.

ADR-0013 decision 18 / ADR-0022 sections 3 and 8: a shared extension's
result lands as one `ext` record written by the core's command — the
commit resolved to its full id in the journal's repository, the kind
declared by the extension's manifest, the payload masked with the
project's private markers and hash-pinned over its masked canonical
form. Every refusal the command can foresee writes nothing.

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

from agentmarshal.cli import main
from agentmarshal.journal.records import (
    create_abandoned_record,
    create_completed_record,
    write_record,
)

_GITHUB_TOKEN = f"ghp_{'A1' * 18}"
_MARKER = "internal.example.invalid"
_KIND = "linter/result@1"


@pytest.fixture(autouse=True)
def _isolated_actor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the recorder resolution independent of the runner's environment.

    An ext record requires a resolvable recorder, and the ambient
    `AGENTMARSHAL_ACTOR` must not decide whether a test resolves one —
    every test that needs a recorder names the actor itself.
    """

    monkeypatch.delenv("AGENTMARSHAL_ACTOR", raising=False)


def _git(repo: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit(repo: Path, message: str = "commit") -> str:
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
        message,
    )
    return _git(repo, "rev-parse", "HEAD")


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
    _commit(repo, "initial")
    monkeypatch.chdir(repo)
    return repo


def _manifest(
    repo: Path,
    name: str = "linter",
    kinds: tuple[str, ...] = (_KIND,),
    *,
    directory: bool = False,
) -> Path:
    """Write `<name>`'s manifest — the file form, or the directory form."""

    extensions = repo / ".agentmarshal" / "extensions"
    path = (
        extensions / name / "manifest.toml"
        if directory
        else extensions / f"{name}.toml"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    declared = ", ".join(json.dumps(kind) for kind in kinds)
    path.write_text(
        "schema = 2\n"
        f'name = "{name}"\n'
        'version = "1.0.0"\n'
        f'footprint = ["{name}/"]\n'
        f'documents = ["{name}/docs/"]\n'
        "[records]\n"
        f"kinds = [{declared}]\n",
        encoding="utf-8",
    )
    return path


def _payload_file(tmp_path: Path, content: str | bytes) -> Path:
    path = tmp_path / "payload.json"
    if isinstance(content, bytes):
        path.write_bytes(content)
    else:
        path.write_text(content, encoding="utf-8")
    return path


def _open() -> None:
    assert main(["open", "--title", "Task"]) == 0


def _record_ext(*extra: str, task: str = "CR-001", commit: str = "HEAD") -> int:
    return main(
        [
            "record-ext",
            "--task",
            task,
            "--commit",
            commit,
            *extra,
        ]
    )


def _records(repo: Path, task: str = "CR-001") -> list[dict[str, Any]]:
    records = sorted((_journal(repo) / "tasks" / task / "records").glob("*.json"))
    return [json.loads(path.read_text(encoding="utf-8")) for path in records]


def _exts(repo: Path, task: str = "CR-001") -> list[dict[str, Any]]:
    return [r for r in _records(repo, task) if r["record_type"] == "ext"]


def _snapshot(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _canonical_sha256(payload: object) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _ready(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    payload: str = '{"outcome": "clean"}',
    **kwargs: Any,
) -> tuple[Path, Path]:
    """A repo with the manifest declared, the task open and the payload filed."""

    repo = _repo(tmp_path, monkeypatch, **kwargs)
    _manifest(repo)
    _open()
    return repo, _payload_file(tmp_path, payload)


# -- the record is written for a resolved commit -------------------------------


def test_an_ext_record_is_written_for_a_declared_kind_at_the_resolved_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an ext record is written for a declared kind at the
    resolved commit."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    head = _git(repo, "rev-parse", "HEAD")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0

    captured = capsys.readouterr()
    record = _exts(repo)[0]
    assert record["schema"] == 7
    assert record["kind"] == _KIND
    assert record["commit"] == head
    assert record["payload"] == {"outcome": "clean"}
    assert record["payload_sha256"] == _canonical_sha256({"outcome": "clean"})
    assert record["recorded_by"] == "ext-writer"
    record_path = Path(captured.out.splitlines()[0])
    assert record_path.parent == _journal(repo) / "tasks" / "CR-001" / "records"
    assert f"commit {head}" in captured.out
    assert f"kind {_KIND}" in captured.out
    assert f"payload sha256 {record['payload_sha256']}" in captured.out
    assert "recorded by ext-writer" in captured.out


def test_a_short_or_symbolic_commit_resolves_to_the_full_id(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a short or symbolic commit resolves to the full id."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    head = _git(repo, "rev-parse", "HEAD")
    capsys.readouterr()

    assert (
        _record_ext("--kind", _KIND, "--payload-file", str(payload), commit="HEAD") == 0
    )
    assert (
        _record_ext("--kind", _KIND, "--payload-file", str(payload), commit=head[:8])
        == 0
    )
    assert (
        _record_ext(
            "--kind",
            _KIND,
            "--payload-file",
            str(payload),
            commit="HEAD^{commit}",
        )
        == 0
    )

    assert [record["commit"] for record in _exts(repo)] == [head] * 3
    assert f"commit {head}" in capsys.readouterr().out


def test_a_commit_that_does_not_resolve_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a commit that does not resolve is refused writing
    nothing."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert (
        _record_ext("--kind", _KIND, "--payload-file", str(payload), commit="0" * 40)
        == 1
    )

    err = capsys.readouterr().err
    assert "0" * 40 in err and "does not resolve" in err
    assert _snapshot(_journal(repo)) == before


def test_an_unknown_task_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: an unknown task is refused writing nothing."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert (
        _record_ext("--kind", _KIND, "--payload-file", str(payload), task="CR-099") == 1
    )

    assert "CR-099" in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before


@pytest.mark.parametrize("terminal", ["completed", "abandoned"])
def test_a_completed_or_abandoned_task_is_refused_writing_nothing(
    terminal: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a completed or abandoned task is refused writing
    nothing."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    journal = _journal(repo)
    write_record(
        journal,
        "CR-001",
        create_completed_record("CR-001", "test", "a" * 40)
        if terminal == "completed"
        else create_abandoned_record("CR-001", "test", "Superseded"),
    )
    capsys.readouterr()
    before = _snapshot(journal)

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1

    state = "done" if terminal == "completed" else "abandoned"
    assert state in capsys.readouterr().err
    assert _snapshot(journal) == before


def test_in_a_sidecar_the_commit_resolves_in_the_journal_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: in a sidecar the commit resolves in the journal
    repository.

    The sidecar's repository carries its own commits; the host's are
    never asked — a host-only reference is refused and the sidecar's
    own head resolves to its own id.
    """

    host = tmp_path / "host"
    host.mkdir()
    _git(host, "init", "--quiet")
    (host / "readme.md").write_text("host\n", encoding="utf-8")
    _commit(host, "host base")
    host_head = _git(host, "rev-parse", "HEAD")

    sidecar = tmp_path / "sidecar"
    sidecar.mkdir()
    _git(sidecar, "init", "--quiet")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    (sidecar / "notes.txt").write_text("sidecar\n", encoding="utf-8")
    sidecar_head = _commit(sidecar, "sidecar state")
    _manifest(sidecar)
    assert main(["open", "--title", "Task"]) == 0
    payload = _payload_file(tmp_path, '{"outcome": "clean"}')
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0

    assert _exts(sidecar)[0]["commit"] == sidecar_head
    assert sidecar_head != host_head

    # A commit only the host holds does not resolve — the host is never
    # asked.
    assert (
        _record_ext("--kind", _KIND, "--payload-file", str(payload), commit=host_head)
        == 1
    )
    assert "does not resolve" in capsys.readouterr().err
    assert len(_exts(sidecar)) == 1


# -- the kind must be declared by the shared extension's manifest ----------------


def test_a_kind_not_of_the_declared_form_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a kind not of the declared form is refused."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    for kind in ("not-a-kind", "linter/result", "result@1", "a/b/c@1"):
        assert _record_ext("--kind", kind, "--payload-file", str(payload)) == 1
        err = capsys.readouterr().err
        assert kind in err and "<name>/<kind>@<version>" in err

    assert _snapshot(_journal(repo)) == before


def test_a_kind_whose_extension_has_no_manifest_is_refused_naming_the_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a kind whose extension has no manifest is refused naming
    the kind."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _record_ext("--kind", "ghost/result@1", "--payload-file", str(payload)) == 1

    assert "ghost/result@1" in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before


def test_a_kind_absent_from_the_manifests_kinds_is_refused_naming_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a kind absent from the manifest's kinds is refused naming
    it."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _record_ext("--kind", "linter/other@1", "--payload-file", str(payload)) == 1

    err = capsys.readouterr().err
    assert "linter/other@1" in err and "not declared" in err
    assert _snapshot(_journal(repo)) == before


def test_a_manifest_that_cannot_be_read_refuses_the_write_naming_the_kind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a manifest that cannot be read refuses the write naming
    the kind."""

    repo = _repo(tmp_path, monkeypatch)
    manifest = _manifest(repo)
    manifest.write_text("schema = 2\nname = [oops\n", encoding="utf-8")
    _open()
    payload = _payload_file(tmp_path, '{"outcome": "clean"}')
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1

    assert _KIND in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before


def test_a_kind_declared_in_the_directory_form_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a kind declared in the directory form is written."""

    repo = _repo(tmp_path, monkeypatch)
    _manifest(repo, directory=True)
    _open()
    payload = _payload_file(tmp_path, '{"outcome": "clean"}')
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0

    assert _exts(repo)[0]["kind"] == _KIND


# -- the payload is leak-scanned at write, masked where it trips -----------------


def test_a_hit_in_a_string_value_is_masked_and_its_category_named(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a hit in a string value is masked and its category
    named.

    The masked span lands as `[masked: <category>]` and the command
    names the category on stderr — the matched text appears in neither
    the output nor the record.
    """

    repo = _repo(tmp_path, monkeypatch, markers=(_MARKER,))
    _manifest(repo)
    _open()
    payload = _payload_file(
        tmp_path,
        json.dumps({"token": _GITHUB_TOKEN, "host": f"db.{_MARKER}"}),
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0

    captured = capsys.readouterr()
    record = _exts(repo)[0]
    assert record["payload"] == {
        "token": "[masked: github-token]",
        "host": "db.[masked: private-marker]",
    }
    assert "github-token" in captured.err and "private-marker" in captured.err
    assert _GITHUB_TOKEN not in captured.out + captured.err
    assert _MARKER not in captured.out + captured.err
    assert _GITHUB_TOKEN not in json.dumps(record)


def test_a_hit_in_an_object_key_is_masked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a hit in an object key is masked."""

    repo = _repo(tmp_path, monkeypatch, markers=(_MARKER,))
    _manifest(repo)
    _open()
    payload = _payload_file(
        tmp_path, json.dumps({f"db.{_MARKER}": 1, "nested": {_MARKER: 2}})
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0

    record = _exts(repo)[0]
    assert record["payload"] == {
        "db.[masked: private-marker]": 1,
        "nested": {"[masked: private-marker]": 2},
    }
    assert _MARKER not in json.dumps(record)
    assert _MARKER not in capsys.readouterr().out


def test_the_payload_hash_is_computed_after_masking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: the payload hash is computed after masking."""

    repo = _repo(tmp_path, monkeypatch, markers=(_MARKER,))
    _manifest(repo)
    _open()
    payload = _payload_file(tmp_path, json.dumps({"host": _MARKER}))
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0

    masked = {"host": "[masked: private-marker]"}
    record = _exts(repo)[0]
    assert record["payload_sha256"] == _canonical_sha256(masked)
    assert record["payload_sha256"] != _canonical_sha256({"host": _MARKER})


def test_two_keys_that_mask_to_one_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: two keys that mask to one are refused."""

    repo = _repo(tmp_path, monkeypatch, markers=(_MARKER,))
    _manifest(repo)
    _open()
    payload = _payload_file(
        tmp_path,
        json.dumps({f"key-{_MARKER}": 1, "key-[masked: private-marker]": 2}),
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1

    err = capsys.readouterr().err
    assert "merges" in err or "merge" in err
    assert _MARKER not in err
    assert _snapshot(_journal(repo)) == before


def test_a_payload_whose_masked_form_still_trips_the_scan_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a payload whose masked form still trips the scan is
    refused.

    The marker `masked` occurs inside the mask label the masking writes,
    so the masked canonical form still trips the scan; the write is
    refused naming the category, never the matched text.
    """

    repo = _repo(tmp_path, monkeypatch, markers=("masked",))
    _manifest(repo)
    _open()
    payload = _payload_file(tmp_path, '{"note": "the masked value"}')
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1

    err = capsys.readouterr().err
    assert "private-marker" in err and "could not make it clean" in err
    assert _snapshot(_journal(repo)) == before


def test_a_payload_file_that_cannot_be_read_or_parsed_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a payload file that cannot be read or parsed is
    refused."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    missing = tmp_path / "missing.json"
    assert _record_ext("--kind", _KIND, "--payload-file", str(missing)) == 1
    err = capsys.readouterr().err
    assert str(missing) in err and "cannot read" in err

    payload.write_text("not json {\n", encoding="utf-8")
    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1
    err = capsys.readouterr().err
    assert str(payload) in err and "not JSON" in err

    payload.write_bytes(b"\xff\xfe binary")
    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1

    assert _snapshot(_journal(repo)) == before


def test_a_payload_past_64_kib_after_masking_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a payload past 64 KiB after masking is refused."""

    repo, payload = _ready(
        tmp_path, monkeypatch, payload=json.dumps({"blob": "x" * 70000})
    )
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "ext-writer")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1

    err = capsys.readouterr().err
    assert "65536" in err or "64" in err
    assert _snapshot(_journal(repo)) == before


# -- the recorder is named, or nothing is written --------------------------------


def test_no_resolvable_recorder_is_refused_writing_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: no resolvable recorder is refused writing nothing."""

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", os.devnull)
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1

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

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "a-stranger")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0

    assert _exts(repo)[0]["recorded_by"] == "a-stranger"
    assert "not a declared actor" in capsys.readouterr().err


def test_a_declared_actor_records_with_no_undeclared_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a declared actor records with no undeclared note.

    Whether the actor id resolves through the table or merely *names* a
    declared actor through the override, there is nothing to note.
    """

    repo, payload = _ready(
        tmp_path,
        monkeypatch,
        actors={"lead": {"git_identities": ["lead@example.invalid"]}},
    )
    _git(repo, "config", "user.email", "lead@example.invalid")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0
    captured = capsys.readouterr()
    assert "lead" in captured.out
    assert "declared actor" not in captured.err

    # An override that names a declared actor is also quiet.
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "lead")
    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0
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

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "op\nera\u202etor")
    capsys.readouterr()

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 0

    captured = capsys.readouterr()
    assert "op\nera\u202etor" not in captured.out + captured.err
    assert "op\\nera\\u202etor" in captured.out
    assert "op\\nera\\u202etor" in captured.err
    assert _exts(repo)[0]["recorded_by"] == "op\nera\u202etor"


# -- a refusal leaves nothing behind ---------------------------------------------


def test_a_refused_run_leaves_the_journal_untouched(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a refused run leaves the journal untouched.

    Every refusal the command can foresee is decided before any write:
    the journal is byte-identical and `agentmarshal validate` still
    passes.
    """

    repo, payload = _ready(tmp_path, monkeypatch)
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    # A commit that does not resolve.
    assert (
        _record_ext("--kind", _KIND, "--payload-file", str(payload), commit="0" * 40)
        == 1
    )
    # An unknown task.
    assert (
        _record_ext("--kind", _KIND, "--payload-file", str(payload), task="CR-099") == 1
    )
    # A kind no shared extension declares.
    assert _record_ext("--kind", "ghost/result@1", "--payload-file", str(payload)) == 1
    # A payload file that does not parse.
    broken = tmp_path / "broken.json"
    broken.write_text("{\n", encoding="utf-8")
    assert _record_ext("--kind", _KIND, "--payload-file", str(broken)) == 1

    assert _snapshot(_journal(repo)) == before
    assert main(["validate"]) == 0


def test_a_value_the_record_rules_refuse_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Scenario: a value the record rules refuse writes nothing.

    `1e999` parses only under the lenient read — the canonical form the
    record rules require does not exist for the infinity it becomes,
    and the refusal names `payload`.
    """

    repo, payload = _ready(tmp_path, monkeypatch, payload='{"v": 1e999}')
    monkeypatch.setenv("AGENTMARSHAL_ACTOR", "an-operator")
    capsys.readouterr()
    before = _snapshot(_journal(repo))

    assert _record_ext("--kind", _KIND, "--payload-file", str(payload)) == 1

    assert "payload" in capsys.readouterr().err
    assert _snapshot(_journal(repo)) == before
    assert main(["validate"]) == 0


def test_record_ext_lists_its_arguments_in_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The command is registered from its own module: every flag."""

    with pytest.raises(SystemExit) as exited:
        main(["record-ext", "--help"])
    assert exited.value.code == 0
    out = capsys.readouterr().out
    for flag in ("--task", "--commit", "--kind", "--payload-file"):
        assert flag in out
