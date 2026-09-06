"""Declared process-extension manifests."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from agentmarshal.journal.contracts import (
    JournalContractError,
    reject_control_characters,
    validate_scope_entry,
)
from agentmarshal.journal.gate import _scope_covers


class ExtensionManifestError(ValueError):
    """Raised when an extension manifest is missing or malformed."""


class ExtensionManifestMissing(ExtensionManifestError):
    """Raised when the named manifest file does not exist.

    Kept apart from a malformed manifest so a context-building reader such as
    ``brief`` can report the absence and continue, while an authority path
    keeps failing loudly.
    """


@dataclass(frozen=True)
class ExtensionManifest:
    """The fields declared by one process-extension manifest."""

    schema: int
    name: str
    version: str
    footprint: tuple[str, ...]
    documents: tuple[str, ...]
    artifacts: tuple[str, ...]
    install: str
    remove: str


def _require_string(data: dict[str, object], field: str, source: Path) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise ExtensionManifestError(
            f"extension manifest field {field!r} must be a non-empty string: {source}"
        )
    return value


def _require_string_array(
    data: dict[str, object], field: str, source: Path
) -> tuple[str, ...]:
    value = data.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ExtensionManifestError(
            f"extension manifest field {field!r} must be an array of strings: {source}"
        )
    return tuple(cast(list[str], value))


def _validate_entries(entries: tuple[str, ...], field: str, source: Path) -> None:
    for entry in entries:
        try:
            validate_scope_entry(entry, f"extension manifest field {field!r}")
        except JournalContractError as error:
            raise ExtensionManifestError(f"{error}: {source}") from error


def read_extension_manifest(project_root: Path, name: str) -> ExtensionManifest:
    """Read and validate ``.agentmarshal/extensions/<name>.toml``."""

    try:
        reject_control_characters(name, "extension name")
    except JournalContractError as error:
        raise ExtensionManifestError(str(error)) from error
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ExtensionManifestError(
            f"extension name {name!r} must be one non-empty path component"
        )
    # Resolve the root first: a symlink in an ancestor of the project (a
    # temporary directory on some hosts) is not the hazard; a symlinked
    # extensions directory or manifest file is.
    path = project_root.resolve() / ".agentmarshal" / "extensions" / f"{name}.toml"
    if path.resolve() != path:
        raise ExtensionManifestError(f"refusing to read through a symlink: {path}")
    if not path.exists():
        raise ExtensionManifestMissing(
            f"extension manifest {name!r} is missing: {path}"
        )
    try:
        with path.open("rb") as manifest_file:
            parsed = tomllib.load(manifest_file)
    except tomllib.TOMLDecodeError as error:
        raise ExtensionManifestError(
            f"invalid TOML extension manifest: {path}"
        ) from error
    except OSError as error:
        raise ExtensionManifestError(
            f"cannot read extension manifest {name!r}: {error}"
        ) from error
    data = cast(dict[str, object], parsed)
    schema = data.get("schema")
    if type(schema) is not int or schema != 1:
        raise ExtensionManifestError(
            f"extension manifest has an unknown or missing schema version: {path}"
        )

    declared_name = _require_string(data, "name", path)
    if declared_name != name:
        raise ExtensionManifestError(
            f"extension manifest name {declared_name!r} does not match {name!r}: {path}"
        )
    footprint = _require_string_array(data, "footprint", path)
    documents = _require_string_array(data, "documents", path)
    artifacts = _require_string_array(data, "artifacts", path)
    for field, entries in (
        ("footprint", footprint),
        ("documents", documents),
        ("artifacts", artifacts),
    ):
        _validate_entries(entries, field, path)
    for field, entries in (("documents", documents), ("artifacts", artifacts)):
        for entry in entries:
            if not _scope_covers(footprint, entry):
                raise ExtensionManifestError(
                    f"extension manifest {field} entry {entry!r} is not under its "
                    f"footprint: {path}"
                )

    return ExtensionManifest(
        schema=schema,
        name=declared_name,
        version=_require_string(data, "version", path),
        footprint=footprint,
        documents=documents,
        artifacts=artifacts,
        install=_require_string(data, "install", path),
        remove=_require_string(data, "remove", path),
    )


def extension_document_entries(
    project_root: Path, names: tuple[str, ...]
) -> tuple[str, ...]:
    """Return named extensions' document entries in declaration order."""

    entries: list[str] = []
    for name in names:
        entries.extend(read_extension_manifest(project_root, name).documents)
    return tuple(entries)
