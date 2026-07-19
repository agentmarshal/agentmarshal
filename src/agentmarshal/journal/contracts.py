"""Contract document parsing."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import cast


class JournalContractError(ValueError):
    """Raised when a journal contract is malformed."""


@dataclass(frozen=True)
class ContractHeader:
    """The machine-readable header of a task contract."""

    schema: int
    id: str
    title: str
    scope: tuple[str, ...]
    acceptance: tuple[str, ...]


def _require_string(data: dict[str, object], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise JournalContractError(
            f"contract header field {field!r} must be a non-empty string"
        )
    return value


def _require_string_array(data: dict[str, object], field: str) -> tuple[str, ...]:
    value = data.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise JournalContractError(
            f"contract header field {field!r} must be an array of strings"
        )
    return tuple(cast(list[str], value))


def _ensure_contract_path_is_real(path: Path) -> None:
    """Reject a contract path reachable through a symlink.

    Journal callers build contract paths from resolved project roots. Comparing
    that lexical path with its resolved target detects a symlink in any
    ancestor as well as a symlinked contract file before it can be opened.
    """

    expected_path = path.absolute()
    resolved_path = path.resolve()
    if resolved_path != expected_path:
        raise JournalContractError(f"refusing to read through a symlink: {path}")


def parse_contract_text(text: str, source: str) -> ContractHeader:
    """Parse and validate a contract's TOML header from its text.

    ``source`` names the origin (a path or a git object reference) for
    error messages only.
    """

    lines = text.lstrip("\ufeff").splitlines()
    if not lines or lines[0].strip() != "+++":
        raise JournalContractError(
            f"contract must start with a +++ header delimiter: {source}"
        )
    try:
        end = next(
            index for index, line in enumerate(lines[1:], 1) if line.strip() == "+++"
        )
    except StopIteration as error:
        raise JournalContractError(
            f"contract header is missing its closing delimiter: {source}"
        ) from error
    try:
        parsed = tomllib.loads("\n".join(lines[1:end]))
    except tomllib.TOMLDecodeError as error:
        raise JournalContractError(f"invalid TOML contract header: {source}") from error
    if not isinstance(parsed, dict):
        raise JournalContractError(f"contract header must be a TOML table: {source}")

    data = cast(dict[str, object], parsed)
    schema = data.get("schema")
    if type(schema) is not int or schema != 1:
        raise JournalContractError(
            f"contract header has an unknown or missing schema version: {source}"
        )
    try:
        return ContractHeader(
            schema=schema,
            id=_require_string(data, "id"),
            title=_require_string(data, "title"),
            scope=_require_string_array(data, "scope"),
            acceptance=_require_string_array(data, "acceptance"),
        )
    except JournalContractError as error:
        raise JournalContractError(f"{error}: {source}") from error


def parse_contract(path: Path) -> ContractHeader:
    """Parse and validate the TOML header from a contract markdown file."""

    _ensure_contract_path_is_real(path)
    with path.open("r", encoding="utf-8-sig", newline=None) as contract_file:
        return parse_contract_text(contract_file.read(), str(path))
