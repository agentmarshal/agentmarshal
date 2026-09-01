# Sidecar journals (experimental)

> **Experimental.** This placement is new in 0.3.0. Its command surface, its
> output wording and its record content may change. Do not build automation on
> it that you are not prepared to fix, and do not rely on a sidecar journal as
> your only copy of anything.

The [Quickstart](quickstart.md) assumes the journal lives inside the repository
it governs — `.agentmarshal/` committed alongside the code. That is the
**embedded** placement, it is the default, and where you control the repository
it is the stronger arrangement. Nothing about it changes here.

A **sidecar** journal is the same journal in a repository of its own, naming
one **host repository** it records evidence about. The host is never written
to.

## Who this is for

Two situations the embedded placement cannot serve: **your working evidence is
private and the project is not** (research notes, pre-registered findings,
anything naming people or clients), and **you do not control the repository**
(an employer's, where you cannot install a directory, a config file, or an
ignore rule). Both otherwise end as loose files, where the material that most
needs timestamps and immutability has neither.

The reasoning is [ADR-0008](adr/ADR-0008-journal-placements.md). This document
is how to run it.

## What a sidecar establishes, and what it does not

Read this before the install instructions, not after.

A sidecar records the **same declarations** an embedded journal does: who is
said to have reviewed which commit, with what verdict, recorded by whom, at
what time — bound to the host's commit SHAs, and append-only within the
sidecar's own history. As everywhere in AgentMarshal, identities are
**declared, not authenticated** (see [ADR-0006](adr/ADR-0006-actors-and-identity.md)
and the README's trust boundary).

It does **not** establish that any of this was enforced:

- **The gate decides no merge.** It computes every check it can and says so in
  words on every run — `Sidecar checks are advisory and decide no merge.` The
  merge belongs to the host's own process, which a sidecar operator generally
  does not control. An advisory pass never prints as the authority's pass.
- **The contract is not pinned to a base commit.** Embedded, the gate reads a
  task's contract from the base side of the same history the candidate belongs
  to, so a change cannot widen its own scope. A sidecar's contract is not in
  the host's history at all, so it is read from the sidecar working tree. The
  gate transcript says this on the scope line rather than leaving you to infer
  it. Scope discipline in a sidecar rests on the sidecar's own commit history,
  not on the gate.
- **Append-only is only as strong as the sidecar's governance.** The gate
  checks that the sidecar's own history added records rather than editing them.
  Whoever owns the sidecar can decline to run that check.
- **Nothing about the host is attested beyond what its SHAs pin.** The host
  merged whatever its own process merged.

That is materially weaker than the embedded, gated arrangement, and materially
stronger than a directory of files with dates typed into them. Both halves of
that sentence are true and neither should be dropped when quoting it.

## Install

The tool is the same tool — one package, one command surface, one record
schema. There is no "lite" build.

Until 0.3.0 reaches the package index, `pip install agentmarshal` will **not**
give you a build that has this placement. Install from the repository — pinned to the commit this document was
verified against, because `master` moves and an experimental surface moves with
it:

```sh
pip install "git+https://github.com/agentmarshal/agentmarshal@3dfeadda6ab10342bd288b6777681175b63d9582"
```

That address is not this document's word alone: the repository declares it in
`[project.urls]` of `pyproject.toml`. Check it there — the pinned commit
predates that line, so the package you install from the pin carries no URL in
its own metadata.

That commit is the one whose behaviour this document describes and whose output
it quotes; the document itself lands after it. Replace the pin with `@master`
when you want the newest build, and accept that what you read here may already
have changed.

Requirements are unchanged: **Python ≥ 3.12** and **git** on your `PATH`. You
install it for yourself, not into the host repository, so a user-level install
(`pipx`, `uv tool install`, a virtualenv you own) is the normal choice.

Both the pinned build and the last published release report `0.2.0`, so
`agentmarshal --version` cannot tell you which one you have. This can:

```sh
agentmarshal init --help | grep -- --host
```

A build with the placement prints the `--host` option; the published 0.2.0
prints nothing.

## Set up the sidecar

Paths, email addresses and model names below are placeholders — `~/src/work-repo`
is your host, `~/work-journal` is your sidecar. Substitute your own; everything
shown was run that way.

The sidecar is an ordinary git repository somewhere you control. It must live
**outside the host's working tree** — not inside it under an ignore rule, which
is one careless `git add -A` away from becoming public history, and whose
ignore rule would itself disclose that something exists.

```sh
mkdir ~/work-journal && cd ~/work-journal
git init
agentmarshal init --host ~/src/work-repo
```

`init` refuses a host that does not exist, is not a directory, or is not a git
worktree. It also refuses two arrangements that would put your commits in the
host's repository: a journal inside the host's tree, and a journal that is a
linked worktree of the host (which sits elsewhere on disk but shares the host's
object database).

`init` also scaffolds `.agentmarshal/upstream/`, an outbox for findings about
AgentMarshal itself, and names it on stdout alongside the project it
initialized; the commit you make later includes it. The configuration it writes
is `.agentmarshal/project.json`:

```json
{
  "framework": {
    "version": "0.2.0"
  },
  "host": "/home/you/src/work-repo",
  "placement": "sidecar",
  "schema": 1
}
```

`framework.version` records the build that wrote the file, so yours says
whichever version you installed. `host` is written absolute. A relative value is supported for a hand-edited
file and resolves against the project root — never against your shell's working
directory, which would mean different repositories from different
subdirectories.

Run every `agentmarshal` command **from the sidecar**, naming host commits by
SHA. The host is only ever read.

## The loop

The steps are the Quickstart's steps. What follows is only what differs; for
contracts, acceptance criteria, the reviewer verdict protocol and record
semantics, the Quickstart remains the reference.

### Open the task in the sidecar

```sh
cd ~/work-journal
agentmarshal open --title "Add a greeting helper" --scope src/
git add -A && git commit -m "open CR-001"
```

Scope is checked against the **host's** working tree, so its warnings are about
host paths — and this example earns one, because the host has no `src/` until a
later step creates it:

```
warning: scope entry 'src/' matches no path in the working tree
```

The task opens anyway: a scope may legitimately name a path the work is about
to create. Numbering is the sidecar's own: this journal's `CR-001` has no
relationship to any `CR-001` in the host.

### Brief the implementer, work in the host

```sh
agentmarshal brief --task CR-001
```

The output is only the briefing, so pipe it into whichever agent you use.

The work happens in the host repository, on a host branch, exactly as it would
without AgentMarshal. Note the two commits you need:

```sh
cd ~/src/work-repo
BASE=$(git rev-parse HEAD)                  # what the work branches from
git switch -c feat/greeting

# the change itself, inside the declared scope
mkdir -p src
printf 'def greet(name):\n    return f"Hello, {name}!"\n' >> src/app.py

git add -A && git commit -m "implement the greeting helper"
IMPL=$(git rev-parse HEAD)                  # the candidate
```

`BASE` is read before branching, so this works whatever the host's default
branch is called. Both are **host** commits, and every command from here names
them by SHA from the sidecar — keep them in the shell you run the journal from.

### Record the review in the sidecar

```sh
cd ~/work-journal
agentmarshal submit-review --task CR-001 --commit "$IMPL" \
  --verdict approved --role reviewer --vendor human --model none \
  --email reviewer@example.com
```

`submit-review` records the verdict and checks nothing about it. The
independence comparison happens later, when the gate runs, between the recorded
reviewer's email and the **host** commit's declared writers — recording a
verdict never establishes that it passes anything. `agentmarshal review` (the
model-reviewer path) likewise snapshots the host tree and writes the record to
the sidecar.

### Run the gate — advisory

```sh
AGENTMARSHAL_PIPELINE_OK_SHA="$IMPL" \
  agentmarshal gate --task CR-001 --commit "$IMPL" --base "$BASE"
```

```
Sidecar checks are advisory and decide no merge.
PASS: task CR-001 is not closed at base
PASS: diff within contract scope (contract read from the sidecar working tree, not pinned to a commit)
PASS: latest review of efab8ed0ad00 is approved
PASS: declared reviewer identity differs from the candidate's declared writers
PASS: pipeline attested for efab8ed0ad00
PASS: evidence records are append-only
PASS: added records are valid (none examined: a host journal is not this journal's evidence)
PASS: no record-path collisions (none examined: the candidate adds no record to this journal)
PASS: task lifecycle records are consistent
gate: advisory checks passed; decides no merge
```

The SHAs in that transcript are from an actual run on a throwaway pair of
repositories; yours will differ.

The gate also runs the advisory leak scan over the candidate's added content.
It appends nothing when there is no hit, which is why the transcript above has
no such line; on a hit it adds `WARN: possible leak in candidate additions
(advisory, not blocking)` with the markers it matched, and on a scan it could
not perform, `WARN: leak-scan skipped`. Neither blocks.

Two lines say "none examined" rather than `PASS` in the ordinary sense: the
candidate is a host diff, and a host diff adds no records to this journal.
Saying `PASS` without saying what was looked at would be a check that examined
nothing reading as a check that found nothing.

Running this **before opening the pull request in the host** is the point of
the command in this placement.

`--task` is required here. Embedded, the gate can derive the task from the
branch name; a host branch named `feat/CR-001-x` names a task in the host's
numbering, and binding it to this journal's unrelated `CR-001` would be exactly
the cross-journal conflation ADR-0008 rules out.

**About the attestation check.** `AGENTMARSHAL_PIPELINE_OK_SHA` is your
statement that a green pipeline ran for that exact commit — set it once you
have seen that, not before. `--attestation ci-required` passes the check by
delegating it to the provider's required checks; in a sidecar over a repository
whose branch protection you do not control, that delegation is a claim you
cannot back, so prefer attesting the commit yourself.

### Complete, and record what it cost

```sh
AGENTMARSHAL_PIPELINE_OK_SHA="$IMPL" \
  agentmarshal complete --task CR-001 --commit "$IMPL" --base "$BASE"
```

It prints the advisory notice and the same nine check lines the gate printed,
then the path of the record it wrote, and ends:

```
completed after advisory checks; decides no merge
```

Then the session record, and a commit — a record in a working tree is not
evidence:

```sh
agentmarshal record-session --task CR-001 --role implementer \
  --actor your/model --activity implementation --outcome implemented \
  --input-tokens 1200 --output-tokens 300 \
  --usage-provider your-provider --usage-method reported
git add -A && git commit -m "review, complete and cost CR-001"
```

### Inspect the evidence

```sh
agentmarshal status CR-001
```

```
Placement: sidecar
ID: CR-001
Status: done
Title: Add a greeting helper
Scope:
- src/
Records:
- 01M1EB6XRAPZCQSCBSASJ7ZFNC opened 2026-09-01T11:21:00.426680Z
- 01M1EB6XWYBSZ54QKH71FFJ8KN review 2026-09-01T11:21:00.574048Z reviewed_commit=efab8ed verdict=approved findings=0 advisory=0
- 01M1EB6Y4Z99FKM6K7JTWBJ9DX completed 2026-09-01T11:21:00.831134Z completed_commit=efab8ed
- 01M1EB6YAK9S5TA7G61TDFRQZT session 2026-09-01T11:21:01.011350Z
```

```sh
agentmarshal report --task CR-001
```

```
Placement: sidecar
CR-001	done	reviews=1	tokens=1500	usage=reported	decision=approved
```

```sh
agentmarshal validate
```

```
OK: CR-001 (done, 4 records)
validate: passed
```

`status` and `report` are the two commands that state the placement, and they
state it on **stderr**, so the machine-readable stdout formats stay unchanged
for anything that parses them. `validate` prints no placement line at all: it is
the whole-journal integrity check, and in a sidecar it checks the sidecar's
journal — the host has none to check.

## What the host never gets

The invariant is absolute: **the host repository carries no reference to, and
no marker of the existence of, any sidecar** — not a link, not a config key,
not an ignore rule, which would disclose exactly what it hides.

The tool holds up its end: it **writes** nothing to the host. It reads it
mostly through git, and directly from the filesystem where a check needs to —
resolving the configured host path, and checking whether the paths a scope
declares exist. Reads either way; writes never. After a full loop, a host
repository has no modified files, and a host that did not contain the string
`agentmarshal` before still does not after. What the host already said about
AgentMarshal is its own business — the tool adds nothing and removes nothing.

`prune --delete` is refused in a sidecar for the same reason. It prints the
refusal and stops, printing no report at all — run plain `agentmarshal prune`
for that.

Your end is the part the tool cannot enforce:

- Never `git add` anything AgentMarshal-related in the host.
- Do not put the sidecar inside the host's tree, even ignored.
- Do not name the sidecar in host commit messages, pull request descriptions,
  or CI configuration.
- References flow **private → public only**. A sidecar quotes host paths, SHAs
  and task ids freely; nothing goes the other way by default.

One deliberate exception exists: a hash-pinned artifact reference from a public
record to private material discloses that the material **exists**, though not
what it says. It is an explicit opt-in, and nothing writes one for you.

Publishing something from a sidecar later — a proposal, an incident write-up —
is **declassification by hand**. The tool does not sanitize for you;
`agentmarshal leak-scan` is an advisory scan of added content, not a
declassification review.

## Command differences, in one place

| Command | In a sidecar |
|---|---|
| `init --host PATH` | Creates the sidecar project; refuses a host that is missing, not a git worktree, contains the journal, or shares its object database |
| `open` | Numbering is the sidecar's own; scope warnings are checked against the host tree |
| `gate` | **Advisory.** Requires `--task`; reads the contract from the sidecar working tree, not from a pinned base |
| `complete` | Same advisory checks; writes `completed` only to the sidecar |
| `prune` | Reports; `--delete` is refused, because the host stays read-only |
| `status`, `report` | Print `Placement: sidecar` on stderr; stdout unchanged |
| `leak-scan` | Scans the **host's** added content, with the private markers read from the sidecar's own `project.json` |
| `submit-review`, `review`, `accept`, `amend`, `reopen`, `abandon`, `record-session`, `validate` | Unchanged, writing to the sidecar and reading host git facts where needed |

## Known rough edges

Found by running our own research journal as a sidecar over this repository.
They are real and unfixed; better to read them here than to meet them.

**The vocabulary assumes the task changes the host.** `brief` opens with "You
are implementing one governed AgentMarshal task" and explains an empty scope as
"the contract needs a scope before work can land"; `open` warns that "no change
can land until one is declared". For a task that produces a conclusion rather
than a diff, all three are the wrong sentence.

**A research finding has no commit to bind to.** Every review record requires a
40-character `reviewed_commit`. Analysis is not about a host commit and not
about the sidecar's own HEAD, so there is currently **no way to record that a
research conclusion was checked**. A record type for this is
[proposal 005](proposals/005-research-findings-have-no-record-type.md) and it
is accepted, not built.

**Scope is host-relative, so research tasks have none.** A task touching no
host path declares an empty scope and cannot be gated — the gate reports every
host path as out of scope. That is the correct answer to the wrong question,
and it follows from the previous point.

**`doctor` does not know about placement.** It checks the sidecar repository
and reports nothing about the configured host or whether it is reachable.
