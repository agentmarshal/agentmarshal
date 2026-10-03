"""Tests for the ``agentmarshal outbox`` command group."""

from __future__ import annotations

import json
import platform
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from agentmarshal import __version__
from agentmarshal.cli import main

_TOKEN = f"ghp_{'A1' * 18}"


def _git(repo: Path, *arguments: str) -> None:
    subprocess.run(["git", *arguments], cwd=repo, check=True, capture_output=True)


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "master")
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    return repo


def _outbox(repo: Path) -> Path:
    return repo / ".agentmarshal" / "upstream"


def _conforming_draft(outbox: Path, name: str = "0001-filled.md") -> Path:
    draft = outbox / name
    draft.write_text(
        "# filled\n\n"
        "## Symptom\n\nit broke\n\n"
        "## Measurements\n\n3 of 7 runs\n\n"
        "## Version\n\n0.0.0\n\n"
        "## Environment\n\na machine\n\n"
        "## Expected\n\nit works\n",
        encoding="utf-8",
    )
    return draft


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


def test_outbox_help_lists_both_subcommands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as raised:
        main(["outbox", "--help"])

    assert raised.value.code == 0
    out = capsys.readouterr().out
    assert "new" in out
    assert "check" in out
