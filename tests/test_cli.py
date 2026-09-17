"""CLI parser tests."""

import pytest

from agentmarshal.cli import main


def test_review_dry_run_help_says_it_records_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Task 3.4: the dry-run flag says that it records nothing."""

    with pytest.raises(SystemExit) as raised:
        main(["review", "--help"])

    assert raised.value.code == 0
    assert "records nothing" in capsys.readouterr().out
