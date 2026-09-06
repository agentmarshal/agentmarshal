"""Declared process-extension manifests."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from agentmarshal.journal.contracts import (
    JournalContractError,
    reject_control_characters,
    scope_covers,
    validate_scope_entry,
)


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


def _require_string(data: dict[str, object], field: str, source: str | Path) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise ExtensionManifestError(
            f"extension manifest field {field!r} must be a non-empty string: {source}"
        )
    return value


def _require_string_array(
    data: dict[str, object], field: str, source: str | Path
) -> tuple[str, ...]:
    value = data.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ExtensionManifestError(
            f"extension manifest field {field!r} must be an array of strings: {source}"
        )
    return tuple(cast(list[str], value))


def _validate_entries(entries: tuple[str, ...], field: str, source: str | Path) -> None:
    for entry in entries:
        try:
            validate_scope_entry(entry, f"extension manifest field {field!r}")
        except JournalContractError as error:
            raise ExtensionManifestError(f"{error}: {source}") from error


def _validate_name(name: str) -> None:
    try:
        reject_control_characters(name, "extension name")
    except JournalContractError as error:
        raise ExtensionManifestError(str(error)) from error
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ExtensionManifestError(
            f"extension name {name!r} must be one non-empty path component"
        )


def extension_manifest_path(name: str) -> str:
    """Return a validated manifest's repository-relative path."""

    _validate_name(name)
    return f".agentmarshal/extensions/{name}.toml"


def parse_extension_manifest_text(
    text: str, name: str, source: str | Path
) -> ExtensionManifest:
    """Parse and validate one manifest already read from a trusted source."""

    extension_manifest_path(name)
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        raise ExtensionManifestError(
            f"invalid TOML extension manifest: {source}"
        ) from error
    data = cast(dict[str, object], parsed)
    schema = data.get("schema")
    if type(schema) is not int or schema != 1:
        raise ExtensionManifestError(
            f"extension manifest has an unknown or missing schema version: {source}"
        )

    declared_name = _require_string(data, "name", source)
    if declared_name != name:
        raise ExtensionManifestError(
            f"extension manifest name {declared_name!r} does not match {name!r}: "
            f"{source}"
        )
    footprint = _require_string_array(data, "footprint", source)
    documents = _require_string_array(data, "documents", source)
    artifacts = _require_string_array(data, "artifacts", source)
    for field, entries in (
        ("footprint", footprint),
        ("documents", documents),
        ("artifacts", artifacts),
    ):
        _validate_entries(entries, field, source)
    for field, entries in (("documents", documents), ("artifacts", artifacts)):
        for entry in entries:
            if not scope_covers(footprint, entry):
                raise ExtensionManifestError(
                    f"extension manifest {field} entry {entry!r} is not under its "
                    f"footprint: {source}"
                )

    return ExtensionManifest(
        schema=schema,
        name=declared_name,
        version=_require_string(data, "version", source),
        footprint=footprint,
        documents=documents,
        artifacts=artifacts,
        install=_require_string(data, "install", source),
        remove=_require_string(data, "remove", source),
    )


def read_extension_manifest(project_root: Path, name: str) -> ExtensionManifest:
    """Read and validate ``.agentmarshal/extensions/<name>.toml``.

    Brief and review call this filesystem reader against their contextual working
    tree or reviewed snapshot. A sidecar gate calls it against the trusted sidecar
    working tree; an embedded gate obtains the blob with ``git show`` from its
    merge-base and passes that text to :func:`parse_extension_manifest_text`.
    """

    relative_path = extension_manifest_path(name)
    # Resolve the root first: a symlink in an ancestor of the project (a
    # temporary directory on some hosts) is not the hazard; a symlinked
    # extensions directory or manifest file is.
    # Strict resolution reports a symlink loop the same way on every Python
    # this project supports (RuntimeError on one release, ELOOP on the next);
    # an absent file is the one resolution failure that means "missing".
    if (project_root / relative_path).is_symlink():
        # Dangling or not, a link at the manifest path is refused as a link,
        # before strict resolution could report a dangling one as missing.
        raise ExtensionManifestError(
            f"refusing to read through a symlink: {project_root / relative_path}"
        )
    try:
        root = project_root.resolve(strict=True)
        path = root / relative_path
        resolved = path.resolve(strict=True)
    except FileNotFoundError:
        raise ExtensionManifestMissing(
            f"extension manifest {name!r} is missing: {project_root / relative_path}"
        ) from None
    except (OSError, RuntimeError) as error:
        raise ExtensionManifestError(
            f"cannot resolve extension manifest {name!r}: {error}"
        ) from error
    if resolved != path:
        raise ExtensionManifestError(f"refusing to read through a symlink: {path}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise ExtensionManifestError(
            f"cannot read extension manifest {name!r}: {error}"
        ) from error
    return parse_extension_manifest_text(text, name, path)
