# Known defects and how to avoid them

This file lists the kinds of defect that reviews in this repository have
found again and again. It is not a style guide and not a checklist of every
rule: each entry is a class that has cost review rounds, how it showed up,
and what avoids it. Read it before you start; check your change against it
before you finish.

## Statements about the tool

1. **A claim about what the code or a document does, made from memory.**
   Shows up as: "the gate records the verdict" (it records nothing); "the
   journal has five record types" (it has nine); "the tool has no outcome
   value for a provider limit" (one has been documented since an earlier
   release); a mechanism called new that already exists. Avoid: for every
   sentence about present behaviour, open the file it rests on — grep the
   code, read the published ADR or spec — and cite it in your report.
2. **Someone else's observation stated as the tool's fact.** Shows up as: a
   reporter's count of their own journal written as the tool's vocabulary; a
   reporter's check of a provider written as "we evaluated". Avoid: attribute
   what a reporter measured to the reporter; keep their figures verbatim and
   say where they differ from other published figures rather than reconciling
   them silently.
3. **An overstated guarantee.** Shows up as: "proven" where the tool only
   checks what an agent declared; "never" or "at all" where a published
   decision says otherwise. Avoid: say what is checked and against what;
   prefer "declared and cross-checked" when the input is written by an agent.

## Consistency

4. **The same fact said differently in different places.** Shows up as: a
   digest's header, its Disposition section, its Where section and its index
   row disagreeing; the same unpublished decision given two names. Avoid:
   when you change a fact, grep every place it lives and change them together;
   reuse the name already used for a decision.
5. **A new text that contradicts a published decision without saying so.**
   Shows up as: an ADR that changes what an earlier ADR decided (a sandbox it
   rejected, an acceptance it limited, a gate lane count) without naming the
   revision. Avoid: before writing a decision, read the ADRs it touches; when
   you change one, name it in the header as a revision and say what changes.
6. **A reference to something not published.** Shows up as: a number of an
   ADR, proposal or release that does not exist yet. Avoid: describe it ("a
   later decision on …") without a number; check that every linked file
   exists.

## Privacy

7. **An identifier from an adopter's repository.** Shows up as: a path, a
   script or variable name, a record id, a field name from their code, a
   detail that narrows the pseudonym's profile. Avoid: describe it neutrally;
   grep your change for ids, paths and names before you finish.
8. **Something sensitive printed in output.** Shows up as: a file name that
   carries a private marker printed without masking. Avoid: a path the tool
   prints in leak-scan output, or any output that may carry a secret, goes
   through the leak scan's masking.

## Code

9. **Text processing that splits on more than it should.** Shows up as:
   `str.splitlines()` breaking on control bytes, so content after them is
   skipped while the output says it was read. Avoid: when splitting git's
   patch output, split on `"\n"` only; test with the bytes that matter.
10. **A rule reused where its reason does not hold.** Shows up as: the leak
    scan's "only added lines matter" reused for the reviewer, who must also
    be told about removed lines it cannot read. Avoid: for each reused helper,
    ask whether its rule fits the new caller and say so in the design.
11. **A test that cannot fail.** Shows up as: a test whose setup never
    reaches the branch it is named after; a docstring carrying a control
    character instead of its escape. Avoid: make each test fail first against
    the old code; use raw strings for escapes in docstrings.

## Scope

12. **A change outside the task's scope.** Shows up as: aligning wording in a
    file the contract does not name; the gate refuses the candidate. Avoid:
    check `git diff --stat` against the scope before you finish; name a
    needed out-of-scope change in your report instead of making it.

## Form

13. **Text that breaks when rendered.** Shows up as: a line break inside a
    hyphenated compound; a space as a thousands separator. Avoid: no line
    break inside a compound; commas for thousands.
