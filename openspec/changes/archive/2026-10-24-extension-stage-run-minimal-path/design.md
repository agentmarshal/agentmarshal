## Context

Criterion 3 of the CR-211 contract did not say what happens when
`isolation.env` names `PATH`; the contract amendment of 2026-10-24
records the coordinator's resolution — the core always sets the
minimal `PATH` of `/usr/bin:/bin`, a named `PATH` is not passed
through, and the stage's output says so. `stages.py` already
implements it: `_MINIMAL_PATH` is the fixed value, `_stage_env` skips
a declared `PATH`, and `_run_stages` prints the note once when a
planned manifest names it. The test
`test_a_path_named_in_isolation_env_is_not_passed_through` pins all
three; the requirement's wording predates the amendment, and the
archived `extension-stage-run` design still claims the caller's named
`PATH` is copied.

## Decisions

- The environment clause names the value and the refusal together:
  `PATH` is a minimal `/usr/bin:/bin` the core always sets; a `PATH`
  named in `isolation.env` is not passed through — the run's output
  says so — and every other declared name still receives the caller's
  value.
- The new scenario is demonstrated by the existing test, whose
  docstring is renamed to it; the archived design's contrary sentence
  gets a dated correction line rather than a rewrite.
