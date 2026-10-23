CR194-001: In `src/agentmarshal/journal/status_view.py:528`, sidecar status reads the threshold from `placement.host_root` passed at `cli.py:1202`, while the gate reads it from the journal project root at `gate.py:1509`; status can therefore report a different or unreadable threshold, violating the required gate/status parity.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"4c8174dc530ba1bd062ab1df91e08279085d60e8","verdict":"changes_required","findings":["CR194-001"],"classes":{"CR194-001":"contract-mismatch"}}
AGENTMARSHAL_VERDICT_END
