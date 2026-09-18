"""The quickstart's governed loop, run as written.

Every shell block of "The governed loop" is executed verbatim in one bash
session against this source tree, so the page cannot drift from the tool it
describes: the gate's output must equal the transcript the page prints, and
the two branches the main path cannot reach — `accept` and `reopen` — run
from their own blocks.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

QUICKSTART = Path(__file__).parents[1] / "docs" / "quickstart.md"
_FENCE = re.compile(r"^```(\w*)\n(.*?)^```\n", re.MULTILINE | re.DOTALL)
_MARKER = "::quickstart-block::"


def _loop_blocks() -> list[tuple[str, str]]:
    """(language, body) of every fenced block in "The governed loop"."""

    text = QUICKSTART.read_text(encoding="utf-8")
    loop = text.split("## The governed loop", 1)[1].split("\n## ", 1)[0]
    return [(match[1], match[2]) for match in _FENCE.finditer(loop)]


def _shell_block(needle: str) -> str:
    matches = [body for lang, body in _loop_blocks() if lang == "sh" and needle in body]
    assert len(matches) == 1, needle
    return matches[0]


def _transcript_after(needle: str) -> str:
    """The unlabelled block that follows the shell block containing needle."""

    blocks = _loop_blocks()
    for index, (lang, body) in enumerate(blocks):
        if lang == "sh" and needle in body:
            following_lang, following = blocks[index + 1]
            assert following_lang == ""
            return following
    raise AssertionError(needle)


def _run(tmp_path: Path, blocks: list[str]) -> list[str]:
    """Run blocks in one bash session in a fresh repository; stdout per block."""

    shim_dir = tmp_path / "bin"
    shim_dir.mkdir()
    shim = shim_dir / "agentmarshal"
    shim.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" -m agentmarshal "$@"\n', encoding="utf-8"
    )
    shim.chmod(0o755)
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "--quiet", "-b", "master"], cwd=repo, check=True)
    source = Path(__file__).parents[1] / "src"
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("AGENTMARSHAL_", "GIT_"))
    }
    env.update(
        PATH=f"{shim_dir}{os.pathsep}{env.get('PATH', '')}",
        PYTHONPATH=str(source),
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_AUTHOR_NAME="Dev Example",
        GIT_AUTHOR_EMAIL="dev@example.com",
        GIT_COMMITTER_NAME="Dev Example",
        GIT_COMMITTER_EMAIL="dev@example.com",
    )
    script = "set -euo pipefail\nsome-agent() { cat > /dev/null; }\n" + "".join(
        f"{body}echo {_MARKER}\n" for body in blocks
    )
    result = subprocess.run(
        ["bash", "-c", script],
        cwd=repo,
        env=env,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    outputs = result.stdout.split(f"{_MARKER}\n")
    assert outputs.pop() == ""
    return outputs


def _without_shas(output: str) -> str:
    return re.sub(r"\b[0-9a-f]{12}\b", "<sha>", output)


def _main_path() -> list[str]:
    return [
        body
        for lang, body in _loop_blocks()
        if lang == "sh"
        and "agentmarshal accept" not in body
        and "agentmarshal reopen" not in body
    ]


@pytest.mark.skipif(
    sys.platform == "win32", reason="the guide's commands are POSIX shell"
)
def test_the_main_path_prints_the_documented_gate_transcript(tmp_path: Path) -> None:
    blocks = _main_path()
    outputs = _run(tmp_path, blocks)
    gate_block = _shell_block("agentmarshal gate --task")

    assert _without_shas(outputs[blocks.index(gate_block)]) == _transcript_after(
        "agentmarshal gate --task"
    )
    status = outputs[blocks.index(_shell_block("agentmarshal status CR-001"))]
    assert "Status: done" in status
    assert "validate: passed" in status


@pytest.mark.skipif(
    sys.platform == "win32", reason="the guide's commands are POSIX shell"
)
def test_reopen_runs_from_the_state_the_main_path_arrives_at(tmp_path: Path) -> None:
    blocks = [
        *_main_path(),
        _shell_block("agentmarshal reopen"),
        "agentmarshal status CR-001\n",
    ]
    outputs = _run(tmp_path, blocks)

    assert "Status: open" in outputs[-1]


@pytest.mark.skipif(
    sys.platform == "win32", reason="the guide's commands are POSIX shell"
)
def test_accept_over_a_non_approving_review_prints_the_documented_line(
    tmp_path: Path,
) -> None:
    through_the_work = _main_path()
    through_the_work = through_the_work[
        : through_the_work.index(_shell_block("agentmarshal submit-review"))
    ]
    non_approving = (
        'agentmarshal submit-review --task CR-001 --commit "$IMPL" '
        "--verdict changes_required --finding F-001 --role reviewer "
        "--vendor human --model none --email reviewer@example.com\n"
    )
    gate_block = _shell_block("agentmarshal gate --task")
    blocks = [
        *through_the_work,
        non_approving,
        _shell_block("agentmarshal accept"),
        gate_block,
    ]
    outputs = _run(tmp_path, blocks)

    (accepted_line,) = [
        body
        for lang, body in _loop_blocks()
        if lang == "" and "accepted over findings" in body
    ]
    assert accepted_line.strip() in outputs[-1]
    assert outputs[-1].endswith("gate: passed\n")
