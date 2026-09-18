# Security policy

## Reporting a vulnerability

Report vulnerabilities only through GitHub private vulnerability reporting: use
the **Report a vulnerability** button on the repository's **Security** tab.
Do not include a vulnerability report in a public issue. This project is
maintained by one person, and no response-time promise is made.

For AgentMarshal, a vulnerability includes:

- bypassing the gate;
- a candidate the gate admits although its own documented checks, run on that
  candidate, should refuse it — for example one that changes or removes an
  evidence record already in the journal, adds a review, acceptance or
  completion record the task's lifecycle does not allow, or makes a verdict
  count for a commit it does not name;
- leak-scan output that prints what it exists to withhold, such as a matched
  secret or a private marker's value; or
- a command that leaves a journal invalid or unreadable.

The documented trust boundary is out of scope: a `human` reviewer is a
self-declaration, and recorders and the reviewed tree are operator-trusted.
That a person with write access to the repository can author a record — a
review, an acceptance, a completion — under any identity they choose is
therefore not a vulnerability: the gate compares identity strings and does not
authenticate who recorded anything, as the README states. The line is whether
the gate's own checks hold, not whether a record's author is who it says.
Signing is on the roadmap rather than in this release.
