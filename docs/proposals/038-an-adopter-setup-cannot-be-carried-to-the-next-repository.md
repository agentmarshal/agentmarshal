# 038 — An adopter's tuned setup cannot be carried to the next repository

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:55f0c2d6838bcb6b4117bc5dd08bfe6b519babe839591dcbf21277f61e716351` · **Disposition:** accepted *(the need is met by an adopter kit the project supplies; the profile commands are deferred)*

## Finding

`init` writes the project file and creates the outbox; the journal has its
fixed path from the first record written into it. Everything else that makes
the governed loop work in practice lives outside the tool, in the adopter's
repository, grown there task by task. The reporter's inventory of that
layer:

- journal transactions through branches and pull requests on a protected
  base, with resume after an interrupted transaction (the pattern of
  proposal 019);
- implementer launchers — sandboxing, commit identity, session records with
  token usage, provider-limit and truncated-output outcomes;
- reviewer commands for two vendors, a selection rule so a reviewer never
  shares a vendor with the candidate's implementer, and a fallback when one
  is out of quota (proposal 034);
- collection of prompts, reports and usage into task artifacts;
- client-side hooks that forbid direct commits to the base branch, where the
  provider plan has no protection of its own;
- a CI workflow with a journal-only fast lane and a separate gate job;
- the instruction files the implementers and the coordinating agent read;
- regression tests for all of the above.

When the same operator starts a second project, none of it can be taken along
through the tool. The only way is to copy files from the first repository and
edit them by hand — and to know which parts are generic and which are specific
to the first project.

Measurements, as reported — from the first project, after about 130 tasks:

- the adopter layer is **16 wrapper scripts, about 2,700 lines**, plus **about
  3,800 lines of regression tests** for them, **2 hooks** and a **governance
  workflow of about 1,000 lines** with its fast lane;
- almost all of it is project-independent — repository paths are derived from
  the repository location, the framework version read from the project file;
  the project-specific parts are few and concrete: role e-mail addresses
  hard-coded in 3 scripts (12 places, including the rule that picks the
  reviewer from the candidate's author address), the project check script,
  the CI build and smoke steps, and the self-hosted runner label;
- the layer is spread over **six places mixed with project files** — the
  wrappers share a directory with the project's own scripts, and hooks, CI,
  agent settings and instruction files each sit in their own place; only the
  journal and the outbox have a fixed place (`.agentmarshal/journal/`,
  `.agentmarshal/upstream/`), so the hand-over instruction had to list every
  file by path;
- handing it to the second project took a separate instruction document: a
  table of files to copy as is, a list of places to adapt, a list of files not
  to copy, the bootstrap order — the hooks must arrive in the same pull
  request that enables the journal, or the next commit to the base branch is
  refused — and operational lessons that existed only in the first project's
  history. The wrapper paths alone are referenced about 30 times across the
  CI workflow, hooks and instruction files.

## Proposed

A way to export a tuned setup as a **profile** and start a new repository from
it:

- `profile export` — collects the adopter layer the project declares as
  reusable into a versioned bundle, with parameters instead of project
  literals: role identities, the runner label, the check command, reviewer
  and implementer defaults;
- `init --profile <bundle> --set key=value …` — lays the bundle into a new
  repository, substitutes the parameters, enables the hooks and the journal
  in one step, and records in the project file which profile and version it
  came from;
- a manifest in the profile separating **reusable** from **project-specific**
  paths, so the export does not carry the first project's checks, deploy
  steps, journal or outbox;
- `profile diff` — how a repository has drifted from the profile it was
  created from, so improvements made in one project can be carried back and
  to the others.

And a standard place for the adopter layer under `.agentmarshal/`, like the
journal has — a manifest, the tools, the hooks, the CI template and the
instruction sources — created by `init` alongside the journal, empty or from
a profile. With a fixed layout the tool can find the layer without a list of
paths, export it, report drift, check it in `doctor`, and `gate` can treat a
change under it as a change to the governance itself. For adopters who
already have a layer, a `profile adopt` move into the layout — reference
rewrites, thin compatibility shims at the old paths for one release, and the
move as a journal transaction of its own kind, since a relocation from
outside a task's scope is refused today — and `profile upgrade` with a
three-way merge, a dry run and a readable conflict report when a new version
of the layer arrives, with `doctor` saying when a framework upgrade expects
a newer layout or profile format.

## Disposition — the need is accepted, met by a supplied adopter kit; the profile commands are deferred

The measurement answers the design question before it is asked: **16 wrapper
scripts, about 2,700 lines**, **about 3,800** lines of tests, six places, and every
adopter growing the same layer from scratch — the transaction helper of
proposal 019 and the outbox scaffold of proposal 029 are two more pieces of
it. A second repository inheriting "a layout nobody designed" is what a
convention left to memory does.

The need is accepted, and it is met by an adopter kit the project supplies
and checks against its own cycle, rather than by the tool acquiring profile
commands: a standard layout under `.agentmarshal/` for the layer, which
`init` creates as it already creates the outbox; templates of the layer's
parts; a manifest of the layer; and drift reported by `doctor`. The kit is
the first step of the reporter's own proposal in any case — a bundle format
defined before the layout it packages would be designed twice. Accepted; not
shipped yet.

The profile machinery around it — export, a profile-aware `init`, drift as
`profile diff`, `adopt` for existing layers, and `upgrade` with its
three-way merge — is deferred, by us, until the layout has settled: what a
profile is depends on what the layout is, and the kit answers that first.

## Where

Nothing here is shipped yet. The adopter kit — the standard layout under
`.agentmarshal/` that `init` creates, the layer templates, the manifest and
the `doctor` drift check — is accepted. The profile commands are deferred by
us until the layout settles.
