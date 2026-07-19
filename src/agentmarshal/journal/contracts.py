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
        raise JournalContractError(f"contract header field {field!r} must be a non-empty string")
    return value


def _require_string_array(data: dict[str, object], field: str) -> tuple[str, ...]:
    value = data.get(field)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise JournalContractError(f"contract header field {field!r} must be an array of strings")
    return tuple(cast(list[str], value))


def parse_contract(path: Path) -> ContractHeader:
    """Parse and validate the TOML header from a contract markdown file."""

    with path.open("r", encoding="utf-8-sig", newline=None) as contract_file:
        lines = contract_file.readlines()
    if not lines or lines[0].strip() != "+++":
        raise JournalContractError(f"contract must start with a +++ header delimiter: {path}")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "+++")
    except StopIteration as error:
        raise JournalContractError(f"contract header is missing its closing delimiter: {path}") from error
    try:
        parsed = tomllib.loads("".join(lines[1:end]))
    except tomllib.TOMLDecodeError as error:
        raise JournalContractError(f"invalid TOML contract header: {path}") from error
    if not isinstance(parsed, dict):
        raise JournalContractError(f"contract header must be a TOML table: {path}")

    data = cast(dict[str, object], parsed)
    schema = data.get("schema")
    if type(schema) is not int or schema != 1:
        raise JournalContractError("contract header has an unknown or missing schema version")
    return ContractHeader(
        schema=schema,
        id=_require_string(data, "id"),
        title=_require_string(data, "title"),
        scope=_require_string_array(data, "scope"),
        acceptance=_require_string_array(data, "acceptance"),
    )
