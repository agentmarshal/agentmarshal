"""The contract hash: one function, and the schema-7 field on the records
that establish a contract (ADR-0018 decision 1, ADR-0022 section 2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from agentmarshal.journal.contracts import JournalContractError, contract_sha256
from agentmarshal.journal.records import (
    JournalRecordError,
    create_amendment_record,
    create_opened_record,
    generate_ulid,
    read_records,
    write_record,
)

_CONTRACT = b"+++\nschema = 1\n+++\n\n# CR-001: a task\n\nBody text.\n"
_HASH = "b" * 64


# --- the hash function ---------------------------------------------------


def test_a_contract_checked_out_with_crlf_hashes_as_the_same_contract_with_lf() -> None:
    """Scenario: a contract checked out with CRLF line endings hashes as the
    same contract with LF.

    CRLF and a lone CR translate to LF the way text reading translates
    them, so the checkout's line-ending convention cannot move the hash.
    """

    lf = _CONTRACT
    mixed = _CONTRACT.replace(b"\n", b"\r\n").replace(
        b"Body text.\r\n", b"Body text.\r"
    )

    assert contract_sha256(mixed, "contract.md") == contract_sha256(lf, "contract.md")
    assert contract_sha256(lf, "contract.md") == hashlib.sha256(lf).hexdigest()


def test_a_byte_order_mark_is_kept_as_text_reading_keeps_it(tmp_path: Path) -> None:
    """Scenario: a byte-order mark is kept as text reading keeps it.

    `read_text(encoding="utf-8")` keeps the mark as U+FEFF, so it is part
    of the hashed text — the hash differs from the mark-stripped one and
    equals the hash of the text the launcher would have read.
    """

    contract_path = tmp_path / "contract.md"
    contract_path.write_bytes(b"\xef\xbb\xbf" + _CONTRACT)
    text = contract_path.read_text(encoding="utf-8")

    assert (
        contract_sha256(contract_path.read_bytes(), "contract.md")
        == hashlib.sha256(text.encode("utf-8")).hexdigest()
    )
    assert contract_sha256(
        contract_path.read_bytes(), "contract.md"
    ) != contract_sha256(_CONTRACT, "contract.md")


def test_undecodable_bytes_are_refused_naming_the_source() -> None:
    """Scenario: undecodable bytes are refused naming the source."""

    with pytest.raises(JournalContractError, match=r"UTF-8.*tasks/CR-001/contract\.md"):
        contract_sha256(b"\xff\xfe" + _CONTRACT, "tasks/CR-001/contract.md")


@pytest.mark.parametrize(
    "content",
    [
        _CONTRACT,
        _CONTRACT.replace(b"\n", b"\r\n"),
        b"\xef\xbb\xbf" + _CONTRACT,
    ],
    ids=["lf", "crlf", "bom"],
)
def test_the_launchers_reviewed_contract_is_unchanged(
    content: bytes, tmp_path: Path
) -> None:
    """Scenario: the launcher's reviewed_contract is unchanged.

    The launcher reads the contract with `read_text(encoding="utf-8")` and
    used to hash the text's UTF-8 encoding; computing both ways on the
    stored bytes gives the same digest for every contract it reads today.
    """

    contract_path = tmp_path / "contract.md"
    contract_path.write_bytes(content)

    old = hashlib.sha256(
        contract_path.read_text(encoding="utf-8").encode("utf-8")
    ).hexdigest()
    new = contract_sha256(contract_path.read_bytes(), str(contract_path))
    assert new == old


# --- the contract field on opened and amendment --------------------------

_CONTRACT_TYPES = ("opened", "amendment")


def _record(record_type: str, **fields: Any) -> dict[str, object]:
    if record_type == "opened":
        record = create_opened_record("CR-001", "test", **fields)
    else:
        record = create_amendment_record("CR-001", "test", "a reason", **fields)
    return record


def _journal_with(tmp_path: Path, record: dict[str, object]) -> Path:
    records_dir = tmp_path / "journal" / "tasks" / "CR-001" / "records"
    records_dir.mkdir(parents=True)
    filename = f"{generate_ulid()}-{record['record_type']}.json"
    (records_dir / filename).write_text(
        json.dumps(record, ensure_ascii=False), encoding="utf-8"
    )
    return tmp_path / "journal"


@pytest.mark.parametrize("record_type", _CONTRACT_TYPES)
def test_an_opened_or_amendment_record_carrying_the_hash_is_written_and_read_back(
    record_type: str, tmp_path: Path
) -> None:
    """Scenario: an opened or amendment record carrying the contract's hash
    is written and read back."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _record(record_type, contract=_HASH))

    stored = read_records(journal_root, "CR-001")[0]
    assert stored["contract"] == _HASH
    assert stored["schema"] == 7


@pytest.mark.parametrize("record_type", _CONTRACT_TYPES)
def test_the_field_is_optional(record_type: str, tmp_path: Path) -> None:
    """Scenario: the field is optional."""

    journal_root = tmp_path / "journal"
    write_record(journal_root, "CR-001", _record(record_type))

    stored = read_records(journal_root, "CR-001")[0]
    assert "contract" not in stored


@pytest.mark.parametrize("record_type", _CONTRACT_TYPES)
@pytest.mark.parametrize(
    "contract", ["a" * 63, "a" * 65, "A" * 64, "g" * 64, "a" * 64 + " ", 64]
)
def test_a_contract_hash_that_is_not_64_lowercase_hex_is_refused(
    record_type: str, contract: object, tmp_path: Path
) -> None:
    """Scenario: a contract hash that is not 64 lowercase hex is refused."""

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"64 .*lowercase hex"):
        write_record(journal_root, "CR-001", _record(record_type, contract=contract))

    assert not journal_root.exists()


@pytest.mark.parametrize("record_type", _CONTRACT_TYPES)
def test_a_contract_that_could_forge_a_rendered_line_is_refused(
    record_type: str, tmp_path: Path
) -> None:
    """Scenario: a contract that could forge a rendered line is refused.

    `contract` registers under the forgeable-text rule keyed
    `("opened"|"amendment", "contract")`; its entry never fires, the
    64-hex shape rule refusing the forgeable character first.
    """

    journal_root = tmp_path / "journal"
    with pytest.raises(JournalRecordError, match=r"control characters|lowercase hex"):
        write_record(
            journal_root, "CR-001", _record(record_type, contract="ok\nforged")
        )

    assert not journal_root.exists()


@pytest.mark.parametrize("record_type", _CONTRACT_TYPES)
def test_a_record_carrying_the_contract_field_stamps_schema_7(
    record_type: str,
) -> None:
    """Scenario: a record carrying the contract field stamps schema 7."""

    assert _record(record_type, contract=_HASH)["schema"] == 7


@pytest.mark.parametrize("record_type", _CONTRACT_TYPES)
def test_the_field_on_a_record_below_schema_7_is_refused_at_write(
    record_type: str, tmp_path: Path
) -> None:
    """Scenario: the field on a record below schema 7 is refused at write."""

    journal_root = tmp_path / "journal"
    record = _record(record_type, contract=_HASH)
    record["schema"] = 6
    with pytest.raises(JournalRecordError, match="unsupported fields"):
        write_record(journal_root, "CR-001", record)

    assert not journal_root.exists()


@pytest.mark.parametrize("record_type", _CONTRACT_TYPES)
def test_the_field_on_a_record_below_schema_7_is_refused_on_read(
    record_type: str, tmp_path: Path
) -> None:
    """Scenario: the field on a record below schema 7 is refused on read."""

    record = _record(record_type, contract=_HASH)
    record["schema"] = 6
    journal_root = _journal_with(tmp_path, record)

    with pytest.raises(JournalRecordError, match="unsupported fields"):
        read_records(journal_root, "CR-001")


@pytest.mark.parametrize("record_type", _CONTRACT_TYPES)
def test_a_record_without_the_field_keeps_its_schema(record_type: str) -> None:
    """Scenario: a record without the field keeps its schema."""

    assert _record(record_type)["schema"] == 3
