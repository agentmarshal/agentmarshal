## 1. One builder

- [x] 1.1 `cli.py` drops its private `_acknowledgement_identification`
  and `_acknowledgement_mark` and calls `capture.py`'s
  `_acknowledgement_mark`, which `gate.py` already calls — verify: the
  leak-scan acknowledgement and gate-mark suites pass unchanged
  (pytest).

## 2. The specification says what the code does

- [x] 2.1 The delta restates the command's mark requirement with the
  masking the code applies — who acknowledged and the reason masked by
  the scan and escaped on display — and gains the scenario the
  masked-recorder test names; the gate's requirement states the mark
  is the one mark-builder both surfaces share; the reads requirement
  gains the sidecar scenario — verify: the change validates and every
  scenario has a test whose docstring names it (pytest).
- [x] 2.2 `acknowledge.py`'s docstring no longer says acknowledgements
  are not honoured; each archived design gains a dated correction line
  and nothing else — verify: read them.

## 3. The two gaps close

- [x] 3.1 A test reads acknowledgements in a sidecar placement —
  records in the journal repository's working tree, the candidate
  resolved and scanned in the host — and a test pins `leak-scan
  --help` listing `--task` — verify: pytest.

## 4. Nothing that worked changed

- [x] 4.1 Full check sequence passes: `uv sync --locked`, `uv run
  agentmarshal validate`, `uv run pytest`, `uv run ruff check`,
  `uv run ruff format --check`, `uv run mypy`, plus the suite in CI's
  conditions (`env -u AGENTMARSHAL_ACTOR GIT_CONFIG_GLOBAL=/dev/null
  GIT_CONFIG_NOSYSTEM=1`) — verify: run them.
- [x] 4.2 The change is archived with `openspec archive` — verify:
  `openspec/changes/archive/` holds it and
  `openspec/specs/leak-scan/` carries the new text.
