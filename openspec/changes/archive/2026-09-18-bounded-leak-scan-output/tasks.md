## 1. The bound moves to the caller

- [x] 1.1 `render_leak_hits` takes the limit as a parameter; the gate passes its bound and the standalone command passes none — verify: capture tests on both shapes.
- [x] 1.2 The gate's bounded line says how many hits it did not show, in the same line — verify: gate test on a candidate with more hits than the bound.
- [x] 1.3 The standalone command prints every hit past the gate's bound — verify: leak-scan test asserting the last hit of a long list appears.

## 2. The debts that travel with it

- [x] 2.1 `docs/sidecar.md` describes the gate's warning as it is now (file and what matched, not "the markers it matched") — verify: read the line against the gate's own test expectation.
- [x] 2.2 `LaunchedReview` is exported from the journal package beside `launch_review` — verify: import it from `agentmarshal.journal` in a test.
