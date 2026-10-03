"""Declared process-extension manifests."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

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


ExtensionPhase = Literal["post-gate", "pre-gate-warn", "pre-gate-stop"]
ExtensionWrites = Literal["none", "process-log"]

_SCHEMA_2_FIELDS = ("stage", "dependencies", "wraps", "records", "isolation")
_STAGE_PHASES: tuple[ExtensionPhase, ...] = (
    "post-gate",
    "pre-gate-warn",
    "pre-gate-stop",
)
_WRITES_MODES: tuple[ExtensionWrites, ...] = ("none", "process-log")
_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_RECORD_KIND = re.compile(r"[^/@\s]+/[^/@\s]+@[^/@\s]+")
_PLAIN_PATH = re.compile(r"[A-Za-z0-9_./-]+")


@dataclass(frozen=True)
class ExtensionStage:
    """One ``[[stage]]`` entry: when the extension runs and what it runs."""

    phase: ExtensionPhase
    command: str


@dataclass(frozen=True)
class ExtensionDependencies:
    """The lock a directory-form extension's dependencies install from."""

    lock: str


@dataclass(frozen=True)
class ExtensionWraps:
    """The product a wrapper extension adapts (ADR-0013)."""

    product: str
    version: str
    ecosystem: str
    lock: str
    runtime: str
    license: str


@dataclass(frozen=True)
class ExtensionIsolation:
    """The isolation a manifest declares for any stage (ADR-0013)."""

    network: bool
    env: tuple[str, ...]
    writes: ExtensionWrites
    timeout_seconds: int


@dataclass(frozen=True)
class ExtensionManifest:
    """The fields declared by one process-extension manifest."""

    schema: int
    name: str
    version: str
    footprint: tuple[str, ...]
    documents: tuple[str, ...]
    artifacts: tuple[str, ...]
    install: str | None
    remove: str | None
    stages: tuple[ExtensionStage, ...] = ()
    dependencies: ExtensionDependencies | None = None
    wraps: ExtensionWraps | None = None
    record_kinds: tuple[str, ...] = ()
    isolation: ExtensionIsolation | None = None


def _require_string(
    data: dict[str, object],
    field: str,
    source: str | Path,
    label: str | None = None,
) -> str:
    shown = field if label is None else label
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise ExtensionManifestError(
            f"extension manifest field {shown!r} must be a non-empty string: {source}"
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


def _reject_forgeable_text(value: str, what: str, source: str | Path) -> None:
    try:
        reject_control_characters(value, what)
    except JournalContractError as error:
        raise ExtensionManifestError(f"{error}: {source}") from error


def _require_text(
    data: dict[str, object],
    field: str,
    source: str | Path,
    label: str | None = None,
) -> str:
    """A non-empty string field that also passes the control-character rule."""

    shown = field if label is None else label
    value = _require_string(data, field, source, label)
    _reject_forgeable_text(value, f"extension manifest field {shown!r}", source)
    return value


def _optional_text(
    data: dict[str, object], field: str, source: str | Path
) -> str | None:
    if field not in data:
        return None
    return _require_text(data, field, source)


def _optional_table(
    data: dict[str, object], field: str, source: str | Path
) -> dict[str, object] | None:
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ExtensionManifestError(
            f"extension manifest field {field!r} must be a table: {source}"
        )
    return cast(dict[str, object], value)


def _require_directory_file(
    data: dict[str, object],
    field: str,
    directory: str,
    source: str | Path,
    label: str | None = None,
) -> str:
    """A relative path naming a file under one directory of the extension's own.

    ``command`` names only a file in the extension's ``bin/`` and a ``lock``
    only one in its ``lock/`` (ADR-0013 D13): a relative path — no ``PATH``
    lookup — whose first component is the declared directory. The core runs a
    command as an argv path, never through a shell, so the path itself carries
    no whitespace or shell metacharacters either.
    """

    shown = field if label is None else label
    value = _require_string(data, field, source, label)
    try:
        validate_scope_entry(value, f"extension manifest field {shown!r}")
    except JournalContractError as error:
        raise ExtensionManifestError(f"{error}: {source}") from error
    if _PLAIN_PATH.fullmatch(value) is None:
        raise ExtensionManifestError(
            f"extension manifest field {shown!r} must be a plain relative path: "
            "only ASCII letters, digits, '_', '.', '-' and '/' are allowed: "
            f"{source}"
        )
    parts = value.split("/")
    if len(parts) < 2 or parts[0] != directory or any(not part for part in parts):
        raise ExtensionManifestError(
            f"extension manifest field {shown!r} must be a relative path under "
            f"'{directory}/' in the extension's own directory: {source}"
        )
    return value


def _validate_entries(entries: tuple[str, ...], field: str, source: str | Path) -> None:
    for entry in entries:
        try:
            validate_scope_entry(entry, f"extension manifest field {field!r}")
        except JournalContractError as error:
            raise ExtensionManifestError(f"{error}: {source}") from error


def _parse_stages(
    data: dict[str, object], source: str | Path
) -> tuple[ExtensionStage, ...]:
    value = data.get("stage")
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(entry, dict) for entry in value
    ):
        raise ExtensionManifestError(
            f"extension manifest field 'stage' must be an array of tables: {source}"
        )
    stages: list[ExtensionStage] = []
    for entry in cast(list[dict[str, object]], value):
        phase = _require_string(entry, "phase", source)
        if phase not in _STAGE_PHASES:
            raise ExtensionManifestError(
                "extension manifest field 'phase' must be one of 'post-gate', "
                f"'pre-gate-warn' or 'pre-gate-stop': {source}"
            )
        stages.append(
            ExtensionStage(
                phase=phase,
                command=_require_directory_file(entry, "command", "bin", source),
            )
        )
    return tuple(stages)


def _parse_dependencies(
    data: dict[str, object], source: str | Path
) -> ExtensionDependencies | None:
    section = _optional_table(data, "dependencies", source)
    if section is None:
        return None
    return ExtensionDependencies(
        lock=_require_directory_file(
            section, "lock", "lock", source, label="[dependencies].lock"
        )
    )


def _parse_wraps(data: dict[str, object], source: str | Path) -> ExtensionWraps | None:
    section = _optional_table(data, "wraps", source)
    if section is None:
        return None
    product = _require_text(section, "product", source)
    version = _require_text(section, "version", source, label="[wraps].version")
    ecosystem = _require_text(section, "ecosystem", source)
    lock = _require_directory_file(
        section, "lock", "lock", source, label="[wraps].lock"
    )
    runtime = _require_text(section, "runtime", source)
    tokens = runtime.split()
    if len(tokens) != 3 or tokens[1] != ">=":
        raise ExtensionManifestError(
            "extension manifest field 'runtime' must be of the form "
            f"'<name> >= <version>': {source}"
        )
    return ExtensionWraps(
        product=product,
        version=version,
        ecosystem=ecosystem,
        lock=lock,
        runtime=runtime,
        license=_require_text(section, "license", source),
    )


def _parse_record_kinds(
    data: dict[str, object], name: str, source: str | Path
) -> tuple[str, ...]:
    section = _optional_table(data, "records", source)
    if section is None:
        return ()
    kinds = _require_string_array(section, "kinds", source)
    for kind in kinds:
        _reject_forgeable_text(
            kind, f"extension manifest field 'kinds' entry {kind!r}", source
        )
        if _RECORD_KIND.fullmatch(kind) is None:
            raise ExtensionManifestError(
                f"extension manifest field 'kinds' entry {kind!r} must be of "
                f"the form '<name>/<kind>@<version>': {source}"
            )
        if kind.split("/", 1)[0] != name:
            raise ExtensionManifestError(
                f"extension manifest field 'kinds' entry {kind!r} must name "
                f"this extension {name!r}: {source}"
            )
    return kinds


def _parse_isolation(
    data: dict[str, object], source: str | Path
) -> ExtensionIsolation | None:
    section = _optional_table(data, "isolation", source)
    if section is None:
        return None
    network = section.get("network")
    if type(network) is not bool:
        raise ExtensionManifestError(
            f"extension manifest field 'network' must be a boolean: {source}"
        )
    env = _require_string_array(section, "env", source)
    for variable in env:
        if _ENV_NAME.fullmatch(variable) is None:
            raise ExtensionManifestError(
                f"extension manifest field 'env' entry {variable!r} must be an "
                f"environment variable name: {source}"
            )
    writes = _require_string(section, "writes", source)
    if writes not in _WRITES_MODES:
        raise ExtensionManifestError(
            "extension manifest field 'writes' must be 'none' or 'process-log': "
            f"{source}"
        )
    timeout_seconds = section.get("timeout_seconds")
    if type(timeout_seconds) is not int or timeout_seconds <= 0:
        raise ExtensionManifestError(
            "extension manifest field 'timeout_seconds' must be an integer "
            f"above zero: {source}"
        )
    return ExtensionIsolation(
        network=network,
        env=env,
        writes=writes,
        timeout_seconds=timeout_seconds,
    )


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
    if type(schema) is not int or schema not in {1, 2}:
        raise ExtensionManifestError(
            f"extension manifest has an unknown or missing schema version: {source}"
        )
    if schema == 1:
        for field in _SCHEMA_2_FIELDS:
            if field in data:
                raise ExtensionManifestError(
                    f"extension manifest field {field!r} requires schema 2: {source}"
                )

    declared_name = _require_string(data, "name", source)
    if declared_name != name:
        raise ExtensionManifestError(
            f"extension manifest name {declared_name!r} does not match {name!r}: "
            f"{source}"
        )
    footprint = _require_string_array(data, "footprint", source)
    documents = _require_string_array(data, "documents", source)
    if schema == 1 or "artifacts" in data:
        artifacts = _require_string_array(data, "artifacts", source)
    else:
        artifacts = ()
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

    if schema == 1:
        version = _require_string(data, "version", source)
        install: str | None = _require_string(data, "install", source)
        remove: str | None = _require_string(data, "remove", source)
        stages: tuple[ExtensionStage, ...] = ()
        dependencies: ExtensionDependencies | None = None
        wraps: ExtensionWraps | None = None
        record_kinds: tuple[str, ...] = ()
        isolation: ExtensionIsolation | None = None
    else:
        version = _require_text(data, "version", source)
        install = _optional_text(data, "install", source)
        remove = _optional_text(data, "remove", source)
        stages = _parse_stages(data, source)
        dependencies = _parse_dependencies(data, source)
        wraps = _parse_wraps(data, source)
        record_kinds = _parse_record_kinds(data, declared_name, source)
        isolation = _parse_isolation(data, source)

    return ExtensionManifest(
        schema=schema,
        name=declared_name,
        version=version,
        footprint=footprint,
        documents=documents,
        artifacts=artifacts,
        install=install,
        remove=remove,
        stages=stages,
        dependencies=dependencies,
        wraps=wraps,
        record_kinds=record_kinds,
        isolation=isolation,
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
