"""Tests for declared process-extension manifests."""

from __future__ import annotations

from pathlib import Path

import pytest

from agentmarshal.journal.extensions import (
    ExtensionManifestError,
    ExtensionManifestMissing,
    read_extension_manifest,
)


def _write_manifest(
    repo: Path,
    *,
    footprint: str = '["openspec/"]',
    documents: str = '["openspec/specs/"]',
    artifacts: str = '["openspec/changes/archive/"]',
) -> Path:
    path = repo / ".agentmarshal" / "extensions" / "openspec.toml"
    path.parent.mkdir(parents=True)
    path.write_text(
        "schema = 1\n"
        'name = "openspec"\n'
        'version = "1.2.3"\n'
        f"footprint = {footprint}\n"
        f"documents = {documents}\n"
        f"artifacts = {artifacts}\n"
        'install = "npx openspec init"\n'
        'remove = "rm -rf openspec"\n',
        encoding="utf-8",
    )
    return path


def test_read_extension_manifest_returns_every_declared_field(tmp_path: Path) -> None:
    _write_manifest(tmp_path)

    manifest = read_extension_manifest(tmp_path, "openspec")

    assert manifest.schema == 1
    assert manifest.name == "openspec"
    assert manifest.version == "1.2.3"
    assert manifest.footprint == ("openspec/",)
    assert manifest.documents == ("openspec/specs/",)
    assert manifest.artifacts == ("openspec/changes/archive/",)
    assert manifest.install == "npx openspec init"
    assert manifest.remove == "rm -rf openspec"


@pytest.mark.parametrize("field", ["footprint", "documents", "artifacts"])
@pytest.mark.parametrize(
    ("entry", "reason"),
    [
        ("/absolute/", "starts with"),
        ("tree/*", "glob metacharacter"),
        ("tree/file?", "glob metacharacter"),
        ("tree/[ab]", "glob metacharacter"),
        ("tree/../elsewhere/", "'..' component"),
    ],
)
def test_manifest_path_fields_use_scope_syntax(
    tmp_path: Path, field: str, entry: str, reason: str
) -> None:
    values = {
        "footprint": '["tree/"]',
        "documents": "[]",
        "artifacts": "[]",
    }
    values[field] = f"[{entry!r}]"
    _write_manifest(tmp_path, **values)

    with pytest.raises(ExtensionManifestError, match=reason) as raised:
        read_extension_manifest(tmp_path, "openspec")

    assert field in str(raised.value)
    assert entry in str(raised.value)


@pytest.mark.parametrize("field", ["documents", "artifacts"])
def test_manifest_documents_and_artifacts_must_lie_under_footprint(
    tmp_path: Path, field: str
) -> None:
    values = {
        "footprint": '["openspec/exact.md", "openspec/tree/"]',
        "documents": "[]",
        "artifacts": "[]",
    }
    values[field] = '["elsewhere/file.md"]'
    _write_manifest(tmp_path, **values)

    with pytest.raises(ExtensionManifestError, match="not under") as raised:
        read_extension_manifest(tmp_path, "openspec")

    assert field in str(raised.value)
    assert "elsewhere/file.md" in str(raised.value)


def test_manifest_accepts_exact_and_directory_footprint_coverage(
    tmp_path: Path,
) -> None:
    _write_manifest(
        tmp_path,
        footprint='["openspec/exact.md", "openspec/tree/"]',
        documents='["openspec/exact.md", "openspec/tree/docs/"]',
        artifacts='["openspec/tree/archive/item.json"]',
    )

    manifest = read_extension_manifest(tmp_path, "openspec")

    assert manifest.documents == (
        "openspec/exact.md",
        "openspec/tree/docs/",
    )


def test_manifest_name_cannot_escape_the_extensions_directory(tmp_path: Path) -> None:
    with pytest.raises(ExtensionManifestError, match="extension name"):
        read_extension_manifest(tmp_path, "../outside")


def test_manifest_is_read_through_a_symlinked_project_root(tmp_path: Path) -> None:
    """A symlink above the project (a temp dir on some hosts) is not the hazard."""

    real = tmp_path / "real"
    real.mkdir()
    _write_manifest(real)
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)

    assert read_extension_manifest(link, "openspec").name == "openspec"


def test_symlinked_manifest_file_is_refused(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    real = tmp_path / ".agentmarshal" / "extensions" / "openspec.toml"
    real.rename(tmp_path / "elsewhere.toml")
    real.symlink_to(tmp_path / "elsewhere.toml")

    with pytest.raises(ExtensionManifestError, match="symlink"):
        read_extension_manifest(tmp_path, "openspec")


def test_missing_manifest_is_its_own_error(tmp_path: Path) -> None:
    with pytest.raises(ExtensionManifestMissing, match="missing"):
        read_extension_manifest(tmp_path, "openspec")
