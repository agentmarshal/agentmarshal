"""Tests for implementer briefings."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from agentmarshal.cli import main
from agentmarshal.journal.brief import build_brief
from agentmarshal.journal.contracts import JournalContractError


def _repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
    monkeypatch.chdir(repo)
    assert main(["init"]) == 0
    assert (
        main(
            [
                "open",
                "--title",
                "Brief task",
                "--scope",
                "src/app.py",
                "--scope",
                "tests/test_app.py",
            ]
        )
        == 0
    )
    return repo


def _contract(repo: Path) -> Path:
    return repo / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"


def _write_contract(repo: Path) -> str:
    body = (
        "\n# CR-001: Brief task\n\n"
        "## Threat model and boundaries\n\n"
        "Keep <prompt-like> text exactly.\n\n"
        "## Non-Goals\n\n"
        "- Do not add another format.\n"
    )
    _contract(repo).write_text(
        "+++\n"
        "schema = 1\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        'scope = ["src/app.py", "tests/test_app.py"]\n'
        'acceptance = ["prints the body", "names every rule"]\n'
        "+++\n"
        f"{body}",
        encoding="utf-8",
    )
    return body


def test_brief_prints_complete_contract_and_governance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    body = _write_contract(repo)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.endswith(body)
    assert "Task id: CR-001" in captured.out
    assert "- src/app.py" in captured.out
    assert "- tests/test_app.py" in captured.out
    assert "- prints the body" in captured.out
    assert "- names every rule" in captured.out
    assert "only these paths may change" in captured.out
    assert "the journal is not the implementer's to edit" in captured.out
    assert "they are the definition of done" in captured.out


@pytest.mark.parametrize(("state", "reason"), [("abandoned", "superseded")])
def test_brief_refuses_a_task_that_is_not_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    state: str,
    reason: str,
) -> None:
    _repo(tmp_path, monkeypatch)
    assert main(["abandon", "--task", "CR-001", "--reason", reason]) == 0
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert state in captured.err


def test_brief_refuses_unknown_task_and_names_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _repo(tmp_path, monkeypatch)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-999"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "unknown task id: CR-999" in captured.err


def test_malformed_contract_raises_contract_error_and_cli_reports_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _contract(repo).write_text("not a contract\n", encoding="utf-8")
    journal = repo / ".agentmarshal" / "journal"
    capsys.readouterr()

    with pytest.raises(JournalContractError):
        build_brief(journal, "CR-001")
    assert main(["brief", "--task", "CR-001"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "contract must start with a +++ header delimiter" in captured.err


def test_an_empty_scope_is_briefed_as_the_strictest_limit_not_as_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """An empty scope forbids every path; a dash would read as no limit at all."""

    repo = _repo(tmp_path, monkeypatch)
    # _repo already opened CR-001 with a scope; this one declares none.
    assert main(["open", "--title", "No scope declared"]) == 0
    capsys.readouterr()

    assert main(["brief", "--task", "CR-002"]) == 0

    briefing = capsys.readouterr().out
    assert "Declared scope: empty" in briefing
    assert "no file may" in briefing
    assert "only these paths may change" not in briefing
    # "(none)" is honest for acceptance criteria, which the gate does not
    # enforce; it is not honest for a scope, which the gate enforces absolutely.
    scope_section = briefing.split("Acceptance criteria")[0]
    assert "(none)" not in scope_section
    assert (repo / ".agentmarshal").is_dir()


def test_brief_appends_named_decisions_and_contract_and_extension_documents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    body = "\n# Body\n\nBody sentinel.\n"
    _contract(repo).write_text(
        "+++\n"
        "schema = 2\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        'scope = ["src/app.py"]\n'
        "acceptance = []\n"
        'decisions = ["ADR-0042"]\n'
        'documents = ["docs/guide.md"]\n'
        'extensions = ["openspec"]\n'
        "+++\n"
        f"{body}",
        encoding="utf-8",
    )
    adr = repo / "docs" / "adr" / "ADR-0042-answer.md"
    adr.parent.mkdir(parents=True)
    adr.write_text("Decision sentinel.\n", encoding="utf-8")
    guide = repo / "docs" / "guide.md"
    guide.write_text("Guide sentinel.\n", encoding="utf-8")
    extension_document = repo / "openspec" / "specs" / "feature.md"
    extension_document.parent.mkdir(parents=True)
    extension_document.write_text("Extension sentinel.\n", encoding="utf-8")
    manifest = repo / ".agentmarshal" / "extensions" / "openspec.toml"
    manifest.parent.mkdir()
    manifest.write_text(
        "schema = 1\n"
        'name = "openspec"\n'
        'version = "1"\n'
        'footprint = ["openspec/"]\n'
        'documents = ["openspec/specs/"]\n'
        "artifacts = []\n"
        'install = "install"\n'
        'remove = "remove"\n',
        encoding="utf-8",
    )
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "## Named decision: ADR-0042" in briefing
    assert "### docs/adr/ADR-0042-answer.md" in briefing
    assert "Decision sentinel." in briefing
    assert "## Named document: docs/guide.md" in briefing
    assert "Guide sentinel." in briefing
    assert "## Named document: openspec/specs/feature.md" in briefing
    assert "Extension sentinel." in briefing
    assert briefing.index("Body sentinel.") < briefing.index("## Named decision")
    assert briefing.index("## Named decision") < briefing.index("docs/guide.md")
    assert briefing.index("docs/guide.md") < briefing.index("openspec/specs/feature.md")


def test_brief_reports_missing_named_decisions_and_documents(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _contract(repo).write_text(
        "+++\n"
        "schema = 2\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        "scope = []\n"
        "acceptance = []\n"
        'decisions = ["ADR-9999"]\n'
        'documents = ["docs/missing.md", "missing-tree/"]\n'
        "+++\n\nBody.\n",
        encoding="utf-8",
    )
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "MISSING: docs/adr/ADR-9999-*.md" in briefing
    assert "MISSING: docs/missing.md" in briefing
    assert "MISSING: missing-tree/" in briefing


def test_brief_reports_a_document_it_cannot_decode_instead_of_failing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A documents directory can hold anything; a binary file is reported."""

    repo = _repo(tmp_path, monkeypatch)
    _contract(repo).write_text(
        "+++\n"
        "schema = 2\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        "scope = []\n"
        "acceptance = []\n"
        'documents = ["specs/"]\n'
        "+++\n\nBody.\n",
        encoding="utf-8",
    )
    specs = repo / "specs"
    specs.mkdir()
    (specs / "feature.md").write_text("Spec sentinel.\n", encoding="utf-8")
    (specs / "diagram.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "Spec sentinel." in briefing
    assert "UNREADABLE (not UTF-8): specs/diagram.png" in briefing


def _git_repo(path: Path) -> None:
    path.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=path, check=True)


def test_sidecar_brief_reads_decisions_and_documents_from_the_host(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Decisions and documents live in the governed tree, manifests in the journal."""

    host = tmp_path / "host"
    _git_repo(host)
    adr = host / "docs" / "adr" / "ADR-0042-answer.md"
    adr.parent.mkdir(parents=True)
    adr.write_text("Host decision sentinel.\n", encoding="utf-8")
    (host / "docs" / "guide.md").write_text("Host guide sentinel.\n", encoding="utf-8")
    spec = host / "openspec" / "specs" / "feature.md"
    spec.parent.mkdir(parents=True)
    spec.write_text("Host spec sentinel.\n", encoding="utf-8")
    sidecar = tmp_path / "sidecar"
    _git_repo(sidecar)
    # A same-named file in the sidecar must not be mistaken for the host's.
    decoy = sidecar / "docs" / "guide.md"
    decoy.parent.mkdir(parents=True)
    decoy.write_text("Sidecar decoy.\n", encoding="utf-8")
    monkeypatch.chdir(sidecar)
    assert main(["init", "--host", str(host)]) == 0
    assert main(["open", "--title", "Sidecar task", "--scope", "docs/guide.md"]) == 0
    contract = (
        sidecar / ".agentmarshal" / "journal" / "tasks" / "CR-001" / "contract.md"
    )
    contract.write_text(
        contract.read_text(encoding="utf-8").replace(
            "schema = 1\n",
            "schema = 2\n"
            'decisions = ["ADR-0042"]\n'
            'documents = ["docs/guide.md"]\n'
            'extensions = ["openspec"]\n',
        ),
        encoding="utf-8",
    )
    manifest = sidecar / ".agentmarshal" / "extensions" / "openspec.toml"
    manifest.parent.mkdir()
    manifest.write_text(
        "schema = 1\n"
        'name = "openspec"\n'
        'version = "1"\n'
        'footprint = ["openspec/"]\n'
        'documents = ["openspec/specs/"]\n'
        "artifacts = []\n"
        'install = "install"\n'
        'remove = "remove"\n',
        encoding="utf-8",
    )
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "Host decision sentinel." in briefing
    assert "Host guide sentinel." in briefing
    assert "Host spec sentinel." in briefing
    assert "Sidecar decoy." not in briefing
    assert "MISSING" not in briefing


def test_brief_reports_a_missing_extension_manifest_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _contract(repo).write_text(
        "+++\n"
        "schema = 2\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        "scope = []\n"
        "acceptance = []\n"
        'documents = ["docs/guide.md"]\n'
        'extensions = ["openspec"]\n'
        "+++\n\nBody.\n",
        encoding="utf-8",
    )
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("Guide sentinel.\n", encoding="utf-8")
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "MISSING: .agentmarshal/extensions/openspec.toml" in briefing
    assert "Guide sentinel." in briefing


def test_brief_reports_an_undecodable_decision_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _contract(repo).write_text(
        "+++\n"
        "schema = 2\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        "scope = []\n"
        "acceptance = []\n"
        'decisions = ["ADR-0042"]\n'
        "+++\n\nBody.\n",
        encoding="utf-8",
    )
    adr = repo / "docs" / "adr" / "ADR-0042-binary.md"
    adr.parent.mkdir(parents=True)
    adr.write_bytes(b"\xff\xfe not text")
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    assert (
        "UNREADABLE (not UTF-8): docs/adr/ADR-0042-binary.md" in capsys.readouterr().out
    )


def _schema2_contract(repo: Path, header_fields: str) -> None:
    _contract(repo).write_text(
        "+++\n"
        "schema = 2\n"
        'id = "CR-001"\n'
        'title = "Brief task"\n'
        "scope = []\n"
        "acceptance = []\n"
        f"{header_fields}"
        "+++\n\nBody.\n",
        encoding="utf-8",
    )


def test_brief_does_not_inline_a_decision_file_linked_outside_the_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(repo, 'decisions = ["ADR-0042"]\n')
    outside = tmp_path / "outside.md"
    outside.write_text("Outside sentinel.\n", encoding="utf-8")
    adr = repo / "docs" / "adr" / "ADR-0042-linked.md"
    adr.parent.mkdir(parents=True)
    adr.symlink_to(outside)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "UNRESOLVABLE" in briefing
    assert "docs/adr/ADR-0042-linked.md" in briefing
    assert "Outside sentinel." not in briefing


def test_brief_treats_a_trailing_slash_entry_naming_a_file_as_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(repo, 'documents = ["docs/guide.md/"]\n')
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("Guide sentinel.\n", encoding="utf-8")
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "MISSING: docs/guide.md/" in briefing
    assert "Guide sentinel." not in briefing


def test_brief_reports_a_malformed_manifest_and_continues(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(
        repo, 'documents = ["docs/guide.md"]\nextensions = ["openspec"]\n'
    )
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("Guide sentinel.\n", encoding="utf-8")
    manifest = repo / ".agentmarshal" / "extensions" / "openspec.toml"
    manifest.parent.mkdir()
    manifest.write_text("schema = 1\nname = [\n", encoding="utf-8")
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "## Named extension: openspec" in briefing
    assert "MALFORMED:" in briefing
    assert "Guide sentinel." in briefing


def test_brief_reports_a_document_it_cannot_resolve_inside_a_named_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(repo, 'documents = ["specs/"]\n')
    specs = repo / "specs"
    specs.mkdir()
    (specs / "feature.md").write_text("Spec sentinel.\n", encoding="utf-8")
    (specs / "dangling.md").symlink_to(tmp_path / "nowhere.md")
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "Spec sentinel." in briefing
    assert (
        "UNRESOLVABLE (outside the tree, a broken link, or a cycle): specs/dangling.md"
        in briefing
    )


def test_brief_does_not_walk_a_linked_subdirectory_inside_the_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(repo, 'documents = ["specs/"]\n')
    shared = repo / "shared"
    shared.mkdir()
    (shared / "common.md").write_text("Common sentinel.\n", encoding="utf-8")
    specs = repo / "specs"
    specs.mkdir()
    (specs / "link").symlink_to(shared, target_is_directory=True)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "Common sentinel." not in briefing
    assert "LINKED DIRECTORY (not followed; name its target): specs/link" in briefing


def test_brief_distinguishes_an_empty_directory_and_an_outside_link_from_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(
        repo, 'documents = ["empty/", "docs/linked.md", "docs/absent.md"]\n'
    )
    (repo / "empty").mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("Outside sentinel.\n", encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "linked.md").symlink_to(outside)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "EMPTY: empty/" in briefing
    assert (
        "UNRESOLVABLE (outside the tree, a broken link, or a cycle): docs/linked.md"
        in briefing
    )
    assert "MISSING: docs/absent.md" in briefing
    assert "Outside sentinel." not in briefing


def test_brief_reports_a_symlink_cycle_instead_of_recursing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(repo, 'documents = ["specs/"]\n')
    specs = repo / "specs"
    (specs / "nested").mkdir(parents=True)
    (specs / "nested" / "leaf.md").write_text("Leaf sentinel.\n", encoding="utf-8")
    (specs / "nested" / "up").symlink_to(specs, target_is_directory=True)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert briefing.count("Leaf sentinel.") == 1
    # A link to an ancestor is a linked directory like any other: not followed,
    # so it cannot recurse, and it is reported under that name.
    assert "LINKED DIRECTORY (not followed; name its target): specs/nested/up" in (
        briefing
    )


def test_brief_reports_a_symlink_loop_at_a_document_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(repo, 'documents = ["docs/loop.md"]\n')
    loop = repo / "docs" / "loop.md"
    loop.parent.mkdir()
    loop.symlink_to(loop)
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "UNRESOLVABLE" in briefing
    assert "docs/loop.md" in briefing


def test_brief_names_a_directory_given_without_a_trailing_slash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repo = _repo(tmp_path, monkeypatch)
    _schema2_contract(repo, 'documents = ["specs"]\n')
    (repo / "specs").mkdir()
    (repo / "specs" / "feature.md").write_text("Spec sentinel.\n", encoding="utf-8")
    capsys.readouterr()

    assert main(["brief", "--task", "CR-001"]) == 0

    briefing = capsys.readouterr().out
    assert "DIRECTORY (name it with a trailing slash): specs" in briefing
    assert "Spec sentinel." not in briefing
