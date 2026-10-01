# 037 — `review` crashes with a traceback when the candidate diff is not UTF-8

- **Reporter:** Adopter D (greenfield project on Linux, Git hosting provider, agent-driven loop with three paid roles) · **Observed on:** 0.4.0 · **Source:** `sha256:4163876a240b38578e897521318837691aefe519ebd07b6a45fdfddbe36a1b98` · **Disposition:** accepted *(a defect; the diff-size limit is deferred)*

## Finding

`agentmarshal review --task <T> --commit <sha> --base <ref>` exited with an
unhandled `UnicodeDecodeError` before the reviewer command was started. The
traceback, as reported:

```
agentmarshal/cli.py:1349 main
agentmarshal/cli.py:731 _run_review
agentmarshal/journal/review.py:1096 launch_review
agentmarshal/journal/review.py:202 _run_git
  ... subprocess.run(..., text=True) -> communicate -> _translate_newlines
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc8 in position 15936543: invalid continuation byte
```

The helper that runs git for `review` reads the output in text mode with the
default strict UTF-8 decoding, so one byte sequence outside UTF-8 — anywhere in
the diff — aborts the command. The candidate contained raw copies of fetched
web pages, some in a legacy Cyrillic encoding (cp1251), so the diff was not
valid UTF-8. No review record was written — which is correct — but the
adopter's wrapper saw only "review failed (exit 1)" and the traceback; nothing
named the file or said what the problem was.

Measurements, as reported:

- One occurrence, on a candidate whose diff was about 16 MB (the traceback
  offset is 15.9 million bytes into git's output).
- A round of the implementer (about 25 minutes) and the review attempt were
  lost before the cause was found by reading the traceback in the wrapper's
  stderr log.

## Proposed

- Git output decoded with an explicit, tolerant policy — for example
  `errors="surrogateescape"`, or bytes with per-file decoding — so a non-UTF-8
  file does not abort the command.
- If the tool decides such content cannot be reviewed, a clear refusal naming
  the file(s) with undecodable content and, ideally, the diff size — the same
  way `leak-scan` names the file that matched.
- Optionally, a configurable limit on the reviewed diff size with a readable
  refusal: a multi-megabyte diff of generated or fetched content is almost
  always a mistake in what was committed, and it is cheaper to say so before
  spending a reviewer run.

The reporter's own workarounds carry the point: asking implementers to
re-encode everything to UTF-8 — what their task contract did — fixes their
case but not the next binary-ish or legacy-encoded file committed by mistake,
and excluding paths through `.gitattributes` (`-diff`) works only when the
adopter knows in advance which paths will contain them.

## Disposition — accepted as a defect, together with proposal 026's fourth finding

The crash is a defect, and it is the same root cause as the skipped leak scan
published as proposal 026's fourth finding: the strictness lives in the UTF-8
decoding each command applies to git's output — `review`'s helper decodes the
merge-base diff strictly before the reviewer is launched, and the gate's own
helper does the same ahead of the scan, where the failure degrades to a
warning that skips the scan whole. One undecodable byte aborts the review run
in the first and leaves every file unscanned in the second.

Upstream reproduced the cause from the scan side, on 2026-10-01 as proposal
026 describes: a commit adding a text file holding a secret-shaped string and
a file of random bytes reported nothing from the scan, while the same commit
without the binary file reported the string. The `review` side was confirmed
by reading the code — the strict decode sits in the git helper where the
traceback puts it — but the reporter's crash itself was not re-run.

The fix is one question for both commands: a diff that is not wholly text must
still reach the reviewer, or be refused, per file — a file that does not
decode should cost its own readability, not every file's review and not the
whole scan. Accepted; not shipped yet.

**The diff-size limit** is deferred — by us. Whether the tool should refuse a
diff on size at all, and at what size, is a policy it would be choosing for
the adopter; the reporter offered it as optional, and its case rests on the
cost of a reviewer run rather than on the crash, which the defect fix covers.

## Where

Nothing here is shipped yet. The decode fix is accepted and shared with the
per-file scan of proposal 026's fourth finding — one root cause, one fix. The
diff-size limit is deferred by us.
