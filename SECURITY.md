# Security policy

## Reporting a vulnerability

Report vulnerabilities only through GitHub private vulnerability reporting: use
the **Report a vulnerability** button on the repository's **Security** tab.
Do not include a vulnerability report in a public issue. This project is
maintained by one person, and no response-time promise is made.

For AgentMarshal, a vulnerability includes:

- bypassing the gate;
- changing or removing an evidence record that is already in the journal, or
  making a review, acceptance or completion count for a commit it does not
  name, without the gate refusing — the gate claims append-only records and
  verdicts bound to an exact commit, and a way around either is in scope;
- leak-scan output that prints what it exists to withhold, such as a matched
  secret or a private marker's value; or
- a command that leaves a journal invalid or unreadable.

The documented trust boundary is out of scope: a `human` reviewer is a
self-declaration, and recorders and the reviewed tree are operator-trusted.
Writing a new record under a made-up reviewer identity is therefore not a
vulnerability — the gate compares identity strings and does not authenticate
who recorded a review, as the README states. That is documented behaviour, and
signing is on the roadmap rather than in this release.
