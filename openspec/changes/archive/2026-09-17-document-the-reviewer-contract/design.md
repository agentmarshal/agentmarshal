## Context

`launch_review` resolves the command template, extracts a snapshot, writes a
prompt file, runs the command and records a verdict. The parts an operator needs
to exercise are the template resolution and the verdict parsing; the parts that
must not run in a dry run are the snapshot, the journal and the record.

## Decisions

- **A dry run shares the parser, not the launcher.** It resolves the template,
  writes a synthetic prompt to a temporary file, runs the command, and hands the
  output to the same verdict parser the real path uses. It does not build a
  snapshot: there is no commit, and a synthetic prompt needs no tree.
- **The synthetic prompt is the real prompt over a fixed example.** Same
  structure, same verdict protocol, a placeholder contract and diff. A command
  that fails on it would have failed on a real one.
- **The dry run touches no journal.** No task is required, nothing is written,
  and the command refuses nothing about the journal's state. This is why the
  flag lives on `review` and not on a task-bound path.
- **The placeholder error names the token by the same rule that rejected it.**
  The template is formatted with a known set of names; the refusal reports the
  name that was not in the set, not a guess at what the operator meant.

## Risks

- [A dry run that pretends to be evidence] → it writes nothing and says so in
  its output; the flag's help says it records nothing.
- [Divergence between the dry-run prompt and the real one] → both come from the
  same module constant, which CR-089 made a single source.
