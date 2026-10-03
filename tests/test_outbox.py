"""Tests for the ``agentmarshal outbox`` command group."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from agentmarshal import __version__
from agentmarshal import outbox as outbox_module
from agentmarshal.cli import main

_TOKEN = f"ghp_{'A1' * 18}"

_CONFORMING = (
    "# filled\n\n"
    "## Symptom\n\nit broke\n\n"
    "## Measurements\n\n3 of 7 runs\n\n"
    "## Version\n\n0.0.0\n\n"
    "## Environment\n\na machine\n\n"
    "## Expected\n\nit works\n"
)


def _git(repo: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)


def _git_out(repo: Path, *arguments: str) -> str:
    return (
        subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)
        .stdout.decode("utf-8")
        .strip()
    )


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    _git(repo, "config", "user.name", "Adopter")
    _git(repo, "config", "user.email", "adopter@test.invalid")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo


def _project_sha256(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A project in a sha256-format repository.

    Skips when this git cannot ``init --object-format=sha256`` — the
    object format is the fixture's whole point, so a git without it runs
    no test rather than a weaker one.
    """

    repo = tmp_path / "repo"
    repo.mkdir()
    initialized = subprocess.run(
        ["git", "init", "--quiet", "-b", "master", "--object-format=sha256"],
        cwd=repo,
        check=False,
        capture_output=True,
    )
    if initialized.returncode != 0:
        pytest.skip("git init does not support --object-format=sha256")
    _git(repo, "config", "user.name", "Adopter")
    _git(repo, "config", "user.email", "adopter@test.invalid")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo


def _outbox(repo: Path) -> Path:
    return repo / ".agentmarshal" / "upstream"


def _conforming_draft(outbox: Path, name: str = "0001-filled.md") -> Path:
    draft = outbox / name
    draft.write_text(_CONFORMING, encoding="utf-8")
    return draft


def _byte_named_file(outbox: Path, name: bytes, content: bytes) -> None:
    """Create a file whose name is not UTF-8, the way one exists on disk."""

    fd = os.open(
        os.fsencode(outbox) + b"/" + name, os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    )
    with os.fdopen(fd, "wb") as handle:
        handle.write(content)


def _configure_markers(repo: Path, markers: list[str]) -> None:
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"private_markers": markers}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def test_a_draft_is_named_with_the_next_free_number_and_a_slug_of_the_gist(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a draft is named with the next free number and a slug of the gist."""
    repo = _project(tmp_path, monkeypatch)

    assert main(["outbox", "new", "gate hangs on amend"]) == 0
    assert main(["outbox", "new", "gate hangs on amend"]) == 0

    assert (_outbox(repo) / "0001-gate-hangs-on-amend.md").is_file()
    assert (_outbox(repo) / "0002-gate-hangs-on-amend.md").is_file()


def test_a_scaffolded_draft_carries_the_five_fields_filled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a scaffolded draft carries the five fields with Version and
    Environment filled."""
    repo = _project(tmp_path, monkeypatch)
    main(["outbox", "new", "gate hangs on amend"])

    text = (_outbox(repo) / "0001-gate-hangs-on-amend.md").read_text(encoding="utf-8")
    for field in ("Symptom", "Measurements", "Version", "Environment", "Expected"):
        assert f"\n## {field}\n" in f"\n{text}"
    assert f"\n{__version__}\n" in text
    assert platform.python_version() in text
    assert "<!--" in text


def test_new_prints_the_path_it_wrote(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: new prints the path it wrote."""
    repo = _project(tmp_path, monkeypatch)

    assert main(["outbox", "new", "gate hangs"]) == 0

    draft = _outbox(repo) / "0001-gate-hangs.md"
    printed = capsys.readouterr().out.strip().splitlines()[-1]
    assert Path(printed).resolve() == draft.resolve()


def test_a_second_draft_never_overwrites_the_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a second draft never overwrites the first."""
    repo = _project(tmp_path, monkeypatch)
    main(["outbox", "new", "gate hangs"])
    first = _outbox(repo) / "0001-gate-hangs.md"
    before = first.read_text(encoding="utf-8")

    assert main(["outbox", "new", "gate hangs"]) == 0

    assert first.read_text(encoding="utf-8") == before
    assert (_outbox(repo) / "0002-gate-hangs.md").is_file()


def test_new_refuses_when_there_is_no_outbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: new refuses when there is no outbox."""
    repo = _project(tmp_path, monkeypatch)
    shutil.rmtree(_outbox(repo))

    assert main(["outbox", "new", "gate hangs"]) == 1
    assert "no outbox" in capsys.readouterr().err


def test_in_a_sidecar_the_draft_lands_in_the_journal_repositorys_outbox(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: in a sidecar the draft lands in the journal repository's outbox."""
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    for repo in (host, sidecar):
        repo.mkdir()
        _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0

    assert main(["outbox", "new", "gate hangs"]) == 0

    drafts = list((sidecar / ".agentmarshal" / "upstream").glob("0001-*.md"))
    assert len(drafts) == 1
    assert not (host / ".agentmarshal").exists()


def test_a_freshly_scaffolded_draft_is_unfilled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a freshly scaffolded draft is unfilled in Symptom,
    Measurements and Expected."""
    _project(tmp_path, monkeypatch)
    main(["outbox", "new", "gate hangs"])

    assert main(["outbox", "check"]) == 1

    out = capsys.readouterr().out
    assert "0001-gate-hangs.md: unfilled Symptom, Measurements, Expected" in out
    assert "missing" not in out
    assert "Version" not in out
    assert "Environment" not in out


def test_a_draft_that_dropped_a_field_is_named_with_the_missing_field(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a draft that dropped a field is named with the missing field."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    text = draft.read_text(encoding="utf-8")
    draft.write_text(re.sub(r"## Expected\n\n[^\n]+\n", "", text), encoding="utf-8")

    assert main(["outbox", "check"]) == 1

    assert "0001-filled.md: missing Expected" in capsys.readouterr().out


def test_a_field_emptied_by_hand_is_unfilled(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a field emptied by hand is unfilled."""
    repo = _project(tmp_path, monkeypatch)
    main(["outbox", "new", "gate hangs"])
    draft = _outbox(repo) / "0001-gate-hangs.md"
    draft.write_text(
        draft.read_text(encoding="utf-8").replace(__version__, ""),
        encoding="utf-8",
    )

    assert main(["outbox", "check"]) == 1

    out = capsys.readouterr().out
    assert "unfilled Symptom, Measurements, Version, Expected" in out


def test_the_readme_init_writes_is_not_a_draft(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the README init writes is not a draft."""
    repo = _project(tmp_path, monkeypatch)
    assert (_outbox(repo) / "README.md").is_file()
    capsys.readouterr()  # drain init's output — it mentions the README itself

    assert main(["outbox", "check"]) == 0
    assert "README" not in capsys.readouterr().out


def test_the_readme_leaves_with_the_batch_and_is_leak_scanned(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The README's fields are not checked, but its name and content leave
    with the batch, so a marker in its content is a hit like any draft's."""
    repo = _project(tmp_path, monkeypatch)
    _configure_markers(repo, ["internal.example.invalid"])
    readme = _outbox(repo) / "README.md"
    readme.write_text(
        readme.read_text(encoding="utf-8") + "\ninternal.example.invalid\n",
        encoding="utf-8",
    )
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "README.md: private-marker #1" in captured.out
    assert "internal.example.invalid" not in captured.out
    assert "internal.example.invalid" not in captured.err


def test_check_refuses_when_there_is_no_outbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: check refuses when there is no outbox."""
    repo = _project(tmp_path, monkeypatch)
    shutil.rmtree(_outbox(repo))

    assert main(["outbox", "check"]) == 1
    assert "no outbox" in capsys.readouterr().err


def test_a_hit_names_the_file_and_what_matched_never_the_matched_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a hit names the file and what matched, never the matched text."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    draft.write_text(
        draft.read_text(encoding="utf-8") + f"\nkey = '{_TOKEN}'\n",
        encoding="utf-8",
    )

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "0001-filled.md: github-token" in captured.out
    assert _TOKEN not in captured.out
    assert _TOKEN not in captured.err


def test_a_configured_private_marker_is_named_by_position_not_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a configured private marker is named by position, not value."""
    repo = _project(tmp_path, monkeypatch)
    _configure_markers(repo, ["internal.example.invalid"])
    draft = _conforming_draft(_outbox(repo))
    draft.write_text(
        draft.read_text(encoding="utf-8") + "\nHOST = 'internal.example.invalid'\n",
        encoding="utf-8",
    )

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "0001-filled.md: private-marker #1" in captured.out
    assert "internal.example.invalid" not in captured.out
    assert "internal.example.invalid" not in captured.err


def test_a_name_that_carries_a_secret_is_described_not_printed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a name that carries a secret is described, not printed."""
    repo = _project(tmp_path, monkeypatch)
    _configure_markers(repo, ["internal.example.invalid"])
    (_outbox(repo) / "internal.example.invalid.md").write_text(
        "internal.example.invalid\n", encoding="utf-8"
    )

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "internal.example.invalid" not in captured.out
    assert "internal.example.invalid" not in captured.err
    assert "<private marker #1>.md" in captured.out


def test_a_draft_that_is_not_utf8_text_is_named_and_still_searched(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a draft that is not UTF-8 text is named and still searched."""
    repo = _project(tmp_path, monkeypatch)
    (_outbox(repo) / "blob.md").write_bytes(b"\xff\xfe" + _TOKEN.encode() + b"\x80\x00")

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "blob.md: not UTF-8 text" in captured.out
    assert "blob.md: github-token" in captured.out


def test_conforming_drafts_with_a_clean_scan_exit_0(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: conforming drafts with a clean scan exit 0."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))

    assert main(["outbox", "check"]) == 0
    assert "all conform" in capsys.readouterr().out


def test_a_non_conforming_draft_fails_the_check_even_when_nothing_leaks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a non-conforming draft fails the check even when nothing leaks."""
    repo = _project(tmp_path, monkeypatch)
    (_outbox(repo) / "0001-empty.md").write_text("# nothing\n", encoding="utf-8")

    assert main(["outbox", "check"]) == 1
    assert "possible leaks" not in capsys.readouterr().out


def test_a_leak_fails_the_check_even_when_every_draft_conforms(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: a leak fails the check even when every draft conforms."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    draft.write_text(
        draft.read_text(encoding="utf-8") + f"\nkey = '{_TOKEN}'\n",
        encoding="utf-8",
    )

    assert main(["outbox", "check"]) == 1


def test_a_file_name_that_carries_a_secret_is_a_hit_even_with_clean_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a file name that carries a secret is a hit even with clean
    content."""
    repo = _project(tmp_path, monkeypatch)
    _configure_markers(repo, ["internal.example.invalid"])
    _conforming_draft(_outbox(repo), name="internal.example.invalid.md")

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "<private marker #1>.md: private-marker #1" in captured.out
    assert "internal.example.invalid" not in captured.out
    assert "internal.example.invalid" not in captured.err


def test_a_file_name_matching_a_signature_is_a_hit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A name matching a built-in signature — not only a configured
    marker — is a hit by itself, described by the signature's identifier."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo), name=f"{_TOKEN}.md")
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "<github-token>.md: github-token" in captured.out
    assert _TOKEN not in captured.out
    assert _TOKEN not in captured.err


def test_an_entry_that_is_not_a_regular_file_is_named_as_not_checked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an entry that is not a regular file is named as not checked."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    (_outbox(repo) / "bundled").mkdir()
    (_outbox(repo) / "linked.md").symlink_to("missing-target")

    assert main(["outbox", "check"]) == 1

    out = capsys.readouterr().out
    assert "bundled: not a draft, not checked" in out
    assert "linked.md: not a draft, not checked" in out


@pytest.mark.skipif(
    getattr(os, "geteuid", lambda: -1)() == 0,
    reason="root can read a permission-denied file",
)
def test_an_unreadable_draft_is_named_without_the_errors_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an unreadable draft is named without the error's path text."""
    repo = _project(tmp_path, monkeypatch)
    _configure_markers(repo, ["internal.example.invalid"])
    draft = _conforming_draft(_outbox(repo), name="internal.example.invalid.md")
    draft.chmod(0)
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "<private marker #1>.md: cannot be read: Permission denied" in captured.out
    assert "internal.example.invalid" not in captured.out
    assert "internal.example.invalid" not in captured.err
    assert str(repo) not in captured.out
    assert str(repo) not in captured.err


def test_a_date_prefixed_name_is_not_read_as_a_draft_number(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A hand-written `2026-10-03-note.md` is not number 2026 — only the
    exact scheme `new` writes counts."""
    repo = _project(tmp_path, monkeypatch)
    (_outbox(repo) / "2026-10-03-note.md").write_text("# x\n", encoding="utf-8")

    assert main(["outbox", "new", "gate hangs"]) == 0

    assert (_outbox(repo) / "0001-gate-hangs.md").is_file()
    assert not (_outbox(repo) / "2027-gate-hangs.md").exists()


def test_outbox_requires_an_initialized_project(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plain = tmp_path / "plain"
    plain.mkdir()
    monkeypatch.chdir(plain)

    assert main(["outbox", "new", "gist"]) == 1
    assert "must be run inside an initialized project" in capsys.readouterr().err


def test_new_refuses_an_empty_gist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _project(tmp_path, monkeypatch)

    assert main(["outbox", "new", "   "]) == 1
    assert "gist" in capsys.readouterr().err


def test_a_non_latin_gist_falls_back_to_the_draft_slug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _project(tmp_path, monkeypatch)

    assert main(["outbox", "new", "зависает"]) == 0

    assert (_outbox(repo) / "0001-draft.md").is_file()


def test_gaps_in_numbering_are_not_refilled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _project(tmp_path, monkeypatch)
    (_outbox(repo) / "0009-placed-by-hand.md").write_text("# x\n", encoding="utf-8")

    assert main(["outbox", "new", "gate hangs"]) == 0

    assert (_outbox(repo) / "0010-gate-hangs.md").is_file()


def test_a_slug_opening_with_digit_groups_still_counts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`new` itself emits `-NN-NN-` after the number — gist "12 34 widget"
    slugs to `12-34-widget` — so the counter reads every name `new` could
    have written; a zero-padded `NNNN` is its padding, never a date."""
    repo = _project(tmp_path, monkeypatch)

    assert main(["outbox", "new", "12 34 widget"]) == 0
    assert main(["outbox", "new", "10 03 note"]) == 0
    assert main(["outbox", "new", "other"]) == 0

    assert (_outbox(repo) / "0001-12-34-widget.md").is_file()
    assert (_outbox(repo) / "0002-10-03-note.md").is_file()
    assert (_outbox(repo) / "0003-other.md").is_file()


def test_a_malformed_leak_scan_section_is_described_without_its_text(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A malformed leak_scan section is a fixed diagnosis — the
    CaptureError's text echoes the unknown configured keys and none of it
    is printed."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    project_file = repo / ".agentmarshal" / "project.json"
    data = json.loads(project_file.read_text(encoding="utf-8"))
    data["leak_scan"] = {"hidden-team-name.invalid": []}
    project_file.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "malformed" in captured.err
    assert "hidden-team-name.invalid" not in captured.out
    assert "hidden-team-name.invalid" not in captured.err


def test_an_unreadable_project_config_is_described_without_its_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A project.json that cannot be parsed is described by the cause's
    kind — the GateError wrapping the failure embeds the path and its text
    is never printed."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    (repo / ".agentmarshal" / "project.json").write_text(
        "{ not json\n", encoding="utf-8"
    )
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "cannot read project config" in captured.err
    assert "JSONDecodeError" in captured.err
    assert str(repo) not in captured.out
    assert str(repo) not in captured.err


def test_a_file_name_that_is_not_utf8_is_named_escaped_and_still_masked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a file name that is not UTF-8 is named escaped and still
    masked."""
    repo = _project(tmp_path, monkeypatch)
    _configure_markers(repo, ["internal.example.invalid"])
    outbox = _outbox(repo)
    _byte_named_file(outbox, b"\xffinternal.example.invalid.md", _CONFORMING.encode())
    _byte_named_file(outbox, b"\xffnote.md", b"# nothing\n")
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "check"]) == 1

    captured = capsys.readouterr()
    assert "internal.example.invalid" not in captured.out
    assert "internal.example.invalid" not in captured.err
    assert "\\xff<private marker #1>.md: private-marker #1" in captured.out
    assert "\\xffnote.md: missing" in captured.out


def test_send_refuses_when_the_check_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: send refuses when the check fails."""
    repo = _project(tmp_path, monkeypatch)
    (_outbox(repo) / "0001-empty.md").write_text("# nothing\n", encoding="utf-8")

    assert main(["outbox", "send"]) == 1

    captured = capsys.readouterr()
    assert "outbox send: refused" in captured.err
    assert _git_out(repo, "rev-list", "--count", "--all") == "0"


def test_send_refuses_when_something_outside_the_outbox_is_staged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: send refuses when something outside the outbox is staged."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    (repo / "journalish.txt").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "journalish.txt")

    assert main(["outbox", "send"]) == 1

    captured = capsys.readouterr()
    assert "staged outside the outbox" in captured.err
    assert "journalish.txt" in captured.err
    # Nothing was committed and the staged set is the operator's, untouched.
    assert _git_out(repo, "rev-list", "--count", "--all") == "0"
    assert _git_out(repo, "diff", "--cached", "--name-only") == "journalish.txt"


def test_send_makes_exactly_one_commit_of_the_batch_and_prints_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: send makes exactly one commit of the batch and prints it."""
    repo = _project(tmp_path, monkeypatch)
    (repo / "tracked.txt").write_text("v1\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "base")
    _conforming_draft(_outbox(repo))
    (repo / "tracked.txt").write_text("v2\n", encoding="utf-8")

    assert main(["outbox", "send"]) == 0

    out = capsys.readouterr().out
    assert "all conform" in out
    assert out.strip().splitlines()[-1] == _git_out(repo, "rev-parse", "HEAD")
    assert _git_out(repo, "rev-list", "--count", "HEAD") == "2"
    message = _git_out(repo, "show", "-s", "--format=%B", "HEAD")
    assert ".agentmarshal/upstream/0001-filled.md" in message
    assert ".agentmarshal/upstream/README.md" in message
    committed = _git_out(
        repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
    )
    assert committed
    assert all(
        path.startswith(".agentmarshal/upstream/") for path in committed.splitlines()
    )
    # The unstaged modification outside the outbox is still unstaged —
    # raw output, since stripping would eat the leading status column.
    porcelain = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout.decode("utf-8")
    assert " M tracked.txt" in porcelain.splitlines()


def test_send_refuses_an_empty_batch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: send refuses an empty batch."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    _git(repo, "add", ".agentmarshal/upstream")
    _git(repo, "commit", "-m", "an earlier batch")

    assert main(["outbox", "send"]) == 1

    assert "nothing to send" in capsys.readouterr().err
    assert _git_out(repo, "rev-list", "--count", "HEAD") == "1"


def test_send_refuses_when_the_outbox_holds_no_drafts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: send refuses when the outbox holds no drafts."""
    repo = _project(tmp_path, monkeypatch)
    assert list(_outbox(repo).iterdir()) == [_outbox(repo) / "README.md"]
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 1

    assert "no drafts to send" in capsys.readouterr().err
    assert _git_out(repo, "rev-list", "--count", "--all") == "0"


def test_a_failed_commit_leaves_the_index_as_send_found_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a failed commit leaves the index as send found it."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    _conforming_draft(_outbox(repo), name="0002-also-filled.md")
    # Staged inside the outbox before the send: the operator's, and the
    # restore must leave it staged.
    _git(repo, "add", ".agentmarshal/upstream/0001-filled.md")
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 1

    err = capsys.readouterr().err
    assert "outbox send:" in err
    # The git error names the subcommand, never the arguments — the
    # commit's message must not be echoed back.
    assert "findings batch" not in err
    assert _git_out(repo, "rev-list", "--count", "--all") == "0"
    # Exactly what the operator staged remains; what send staged is gone.
    assert (
        _git_out(repo, "diff", "--cached", "--name-only")
        == ".agentmarshal/upstream/0001-filled.md"
    )


def test_in_a_sidecar_the_commit_lands_in_the_journal_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scenario: in a sidecar the commit lands in the journal repository."""
    host = tmp_path / "host"
    sidecar = tmp_path / "sidecar"
    for repo in (host, sidecar):
        repo.mkdir()
        _git(repo, "init", "--quiet", "-b", "master")
        _git(repo, "config", "user.name", "Adopter")
        _git(repo, "config", "user.email", "adopter@test.invalid")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    _conforming_draft(sidecar / ".agentmarshal" / "upstream")

    assert main(["outbox", "send"]) == 0

    assert _git_out(sidecar, "rev-list", "--count", "HEAD") == "1"
    committed = _git_out(sidecar, "ls-tree", "-r", "--name-only", "HEAD")
    assert ".agentmarshal/upstream/0001-filled.md" in committed.splitlines()
    # The host gains no commit and no project directory at all.
    assert (
        subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=host,
            capture_output=True,
            check=False,
        ).returncode
        != 0
    )
    assert not (host / ".agentmarshal").exists()


def test_a_file_whose_name_is_not_utf8_is_sent_under_its_escaped_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a file whose name is not UTF-8 is sent under its escaped
    name."""
    repo = _project(tmp_path, monkeypatch)
    _byte_named_file(_outbox(repo), b"\xffdraft.md", _CONFORMING.encode())
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 0

    staged = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo, check=True, capture_output=True
    ).stdout
    assert b".agentmarshal/upstream/\xffdraft.md" in staged
    message = _git_out(repo, "show", "-s", "--format=%B", "HEAD")
    assert "\\xffdraft.md" in message


def test_a_failed_commit_leaves_the_index_as_send_found_it_in_sha256(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a failed commit leaves the index as send found it."""
    repo = _project_sha256(tmp_path, monkeypatch)
    assert _git_out(repo, "rev-parse", "--show-object-format") == "sha256"
    _conforming_draft(_outbox(repo))
    _conforming_draft(_outbox(repo), name="0002-also-filled.md")
    _git(repo, "add", ".agentmarshal/upstream/0001-filled.md")
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 1

    assert "outbox send:" in capsys.readouterr().err
    assert _git_out(repo, "rev-list", "--count", "--all") == "0"
    assert (
        _git_out(repo, "diff", "--cached", "--name-only")
        == ".agentmarshal/upstream/0001-filled.md"
    )


def test_send_refuses_when_a_draft_changed_since_the_check(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: send refuses when a draft changed since the check."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    run_git = outbox_module._git

    def mutate_on_add(
        project_root: Path, arguments: list[str], feed: bytes = b""
    ) -> bytes:
        if arguments[0] == "add":
            draft.write_text(_CONFORMING + "\nedited late\n", encoding="utf-8")
        return run_git(project_root, arguments, feed)

    monkeypatch.setattr(outbox_module, "_git", mutate_on_add)
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 1

    captured = capsys.readouterr()
    assert "changed since the check" in captured.err
    assert "0001-filled.md" in captured.err
    assert _git_out(repo, "rev-list", "--count", "--all") == "0"
    # What the send staged is put back — the changed draft is unstaged.
    assert _git_out(repo, "diff", "--cached", "--name-only") == ""


def test_send_pins_the_bytes_the_check_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The pin is the blob id of the very bytes the check read — a draft
    edited between that read and the staging is refused, where a pin
    taken by re-reading the file later would bless the edit."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    read_bytes = Path.read_bytes

    def mutate_after_read(self: Path) -> bytes:
        raw = read_bytes(self)
        if self.name == draft.name:
            self.write_text(_CONFORMING + "\nedited late\n", encoding="utf-8")
        return raw

    monkeypatch.setattr(Path, "read_bytes", mutate_after_read)
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 1

    captured = capsys.readouterr()
    assert "changed since the check" in captured.err
    assert "0001-filled.md" in captured.err
    assert _git_out(repo, "rev-list", "--count", "--all") == "0"
    # What the send staged is put back — the changed draft is unstaged.
    assert _git_out(repo, "diff", "--cached", "--name-only") == ""


def test_a_draft_renamed_since_the_last_batch_is_sent_as_a_rename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A staged rename's paths are both counted: a draft renamed inside
    the outbox since the last batch is inside on both ends — it sends as
    one rename and the message names both its paths."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    assert main(["outbox", "send"]) == 0
    _git(
        repo,
        "mv",
        ".agentmarshal/upstream/0001-filled.md",
        ".agentmarshal/upstream/0002-renamed.md",
    )
    capsys.readouterr()

    assert main(["outbox", "send"]) == 0

    assert _git_out(repo, "rev-list", "--count", "HEAD") == "2"
    message = _git_out(repo, "show", "-s", "--format=%B", "HEAD")
    assert ".agentmarshal/upstream/0001-filled.md" in message
    assert ".agentmarshal/upstream/0002-renamed.md" in message
    committed = _git_out(
        repo, "diff-tree", "-M", "--no-commit-id", "--name-status", "-r", "HEAD"
    )
    assert "R100" in committed
    assert ".agentmarshal/upstream/0001-filled.md" in committed
    assert ".agentmarshal/upstream/0002-renamed.md" in committed


def test_send_refuses_a_staged_rename_reaching_outside_the_outbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Both halves of a staged rename are judged: a rename whose source
    sits outside the outbox refuses the send, naming the outside path,
    even though the name it lands on is inside the outbox."""
    repo = _project(tmp_path, monkeypatch)
    (repo / "tracked.md").write_text(_CONFORMING, encoding="utf-8")
    _git(repo, "add", "tracked.md")
    _git(repo, "commit", "-m", "base")
    _conforming_draft(_outbox(repo))
    _git(repo, "mv", "tracked.md", ".agentmarshal/upstream/0009-moved.md")
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 1

    captured = capsys.readouterr()
    assert "staged outside the outbox" in captured.err
    assert "tracked.md" in captured.err
    assert _git_out(repo, "rev-list", "--count", "HEAD") == "1"
    # The operator's staged rename is untouched — nothing send added.
    assert ".agentmarshal/upstream/0009-moved.md" in _git_out(
        repo, "diff", "--cached", "--name-only"
    )


def test_a_made_commit_is_never_put_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a made commit is never put back."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    run_git = outbox_module._git

    def fail_rev_parse(
        project_root: Path, arguments: list[str], feed: bytes = b""
    ) -> bytes:
        if arguments == ["rev-parse", "HEAD"]:
            raise outbox_module._OutboxGitError("rev-parse refused")
        return run_git(project_root, arguments, feed)

    monkeypatch.setattr(outbox_module, "_git", fail_rev_parse)
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 1

    captured = capsys.readouterr()
    assert "committed" in captured.err
    assert _git_out(repo, "rev-list", "--count", "HEAD") == "1"
    # The index is what the commit left — the refused read put nothing
    # back: the batch files are still index entries, nothing is staged.
    staged = subprocess.run(
        ["git", "ls-files", "-z"], cwd=repo, check=True, capture_output=True
    ).stdout
    assert b".agentmarshal/upstream/0001-filled.md" in staged
    assert _git_out(repo, "diff", "--cached", "--name-only") == ""


def test_a_gitignored_draft_is_checked_and_sent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a gitignored draft is checked and sent like every file."""
    repo = _project(tmp_path, monkeypatch)
    (repo / ".gitignore").write_text(
        ".agentmarshal/upstream/ignored.md\n", encoding="utf-8"
    )
    _conforming_draft(_outbox(repo), name="ignored.md")
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "send"]) == 0

    committed = _git_out(repo, "ls-tree", "-r", "--name-only", "HEAD")
    assert ".agentmarshal/upstream/ignored.md" in committed.splitlines()


def test_a_file_the_index_claims_is_named_with_the_entry_claiming_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a file the index claims is named with the entry claiming it."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    digest = hashlib.sha256(draft.read_bytes()).hexdigest()
    index = tmp_path / "index.txt"
    index.write_text(f"# index\nSource: sha256:{digest}\n", encoding="utf-8")

    assert main(["outbox", "status", "--index", str(index)]) == 0

    assert "0001-filled.md: claimed by index line 2" in capsys.readouterr().out


def test_a_file_no_entry_claims_is_reported_unclaimed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a file no entry claims is reported unclaimed."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    index = tmp_path / "index.txt"
    index.write_text("# index\n", encoding="utf-8")

    assert main(["outbox", "status", "--index", str(index)]) == 0

    out = capsys.readouterr().out
    assert "0001-filled.md: no index entry" in out
    assert "README.md: no index entry" in out


def test_index_entries_matching_no_file_are_listed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: index entries matching no file are listed."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    digest = hashlib.sha256(draft.read_bytes()).hexdigest()
    other = hashlib.sha256(b"not in the outbox").hexdigest()
    index = tmp_path / "index.txt"
    index.write_text(
        f"Source: sha256:{digest}\nSource: sha256:{other}\n", encoding="utf-8"
    )

    assert main(["outbox", "status", "--index", str(index)]) == 0

    out = capsys.readouterr().out
    assert "0001-filled.md: claimed by index line 1" in out
    assert f"index line 2: sha256:{other} claims no outbox file" in out


def test_two_digests_on_one_index_line_are_two_entries(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: two digests on one index line are two entries."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    digest = hashlib.sha256(draft.read_bytes()).hexdigest()
    other = hashlib.sha256(b"not in the outbox").hexdigest()
    index = tmp_path / "index.txt"
    index.write_text(
        f"Source: sha256:{digest} · Source: sha256:{other}\n", encoding="utf-8"
    )

    assert main(["outbox", "status", "--index", str(index)]) == 0

    out = capsys.readouterr().out
    assert "0001-filled.md: claimed by index line 1" in out
    assert f"index line 1: sha256:{other} claims no outbox file" in out


def test_a_digest_on_several_index_lines_is_listed_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a digest on several index lines is listed once."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    other = hashlib.sha256(b"not in the outbox").hexdigest()
    index = tmp_path / "index.txt"
    index.write_text(
        f"Source: sha256:{other}\n**Source:** `sha256:{other}`\n",
        encoding="utf-8",
    )

    assert main(["outbox", "status", "--index", str(index)]) == 0

    out = capsys.readouterr().out
    assert f"index lines 1, 2: sha256:{other} claims no outbox file" in out
    assert out.count("claims no outbox file") == 1


def test_the_markdown_decorated_source_line_is_parsed_like_the_bare_one(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: the markdown-decorated Source line is parsed like the bare
    one."""
    repo = _project(tmp_path, monkeypatch)
    draft = _conforming_draft(_outbox(repo))
    digest = hashlib.sha256(draft.read_bytes()).hexdigest()
    index = tmp_path / "index.txt"
    index.write_text(
        f"- **Reporter:** Adopter A · **Source:** `sha256:{digest}` · "
        "**Disposition:** accepted\n",
        encoding="utf-8",
    )

    assert main(["outbox", "status", "--index", str(index)]) == 0

    assert "0001-filled.md: claimed by index line 1" in capsys.readouterr().out


def test_status_refuses_a_missing_or_unreadable_index(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: status refuses a missing or unreadable index."""
    _project(tmp_path, monkeypatch)

    missing = tmp_path / "missing.txt"
    assert main(["outbox", "status", "--index", str(missing)]) == 1
    assert "cannot read the index" in capsys.readouterr().err

    assert main(["outbox", "status", "--index", str(tmp_path)]) == 1
    assert "cannot read the index" in capsys.readouterr().err


def test_an_entry_that_is_not_a_regular_file_is_named_as_not_hashed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: an entry that is not a regular file is named as not hashed."""
    repo = _project(tmp_path, monkeypatch)
    _conforming_draft(_outbox(repo))
    (_outbox(repo) / "bundled").mkdir()
    (_outbox(repo) / "linked.md").symlink_to("missing-target")
    index = tmp_path / "index.txt"
    index.write_text("# index\n", encoding="utf-8")

    assert main(["outbox", "status", "--index", str(index)]) == 1

    captured = capsys.readouterr()
    assert "bundled: not a regular file, not hashed" in captured.out
    assert "linked.md: not a regular file, not hashed" in captured.out
    assert "outbox status: refused" in captured.err


def test_a_name_that_is_not_utf8_is_printed_escaped_under_the_masking(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: a name that is not UTF-8 is printed escaped under the
    masking."""
    repo = _project(tmp_path, monkeypatch)
    _configure_markers(repo, ["internal.example.invalid"])
    _byte_named_file(_outbox(repo), b"\xffinternal.example.invalid.md", b"# nothing\n")
    index = tmp_path / "index.txt"
    index.write_text("# index\n", encoding="utf-8")
    capsys.readouterr()  # drain init's output — it names the project path

    assert main(["outbox", "status", "--index", str(index)]) == 0

    captured = capsys.readouterr()
    assert "internal.example.invalid" not in captured.out
    assert "internal.example.invalid" not in captured.err
    assert "\\xff<private marker #1>.md: no index entry" in captured.out


def test_status_refuses_when_there_is_no_outbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Scenario: status refuses when there is no outbox."""
    repo = _project(tmp_path, monkeypatch)
    shutil.rmtree(_outbox(repo))
    index = tmp_path / "index.txt"
    index.write_text("# index\n", encoding="utf-8")

    assert main(["outbox", "status", "--index", str(index)]) == 1
    assert "no outbox" in capsys.readouterr().err


def test_outbox_help_lists_all_four_subcommands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The group's help names every subcommand — new, check, send, status —
    so the registration in outbox.py is covered, not only the dispatch."""
    with pytest.raises(SystemExit) as raised:
        main(["outbox", "--help"])

    assert raised.value.code == 0
    out = capsys.readouterr().out
    for name in ("new", "check", "send", "status"):
        assert name in out
