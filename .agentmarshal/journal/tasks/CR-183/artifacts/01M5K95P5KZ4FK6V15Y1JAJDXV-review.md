RC-UTF8-01: In `src/agentmarshal/record_check.py:175-179`, `_bounded_tail` discards leading UTF-8 continuation bytes even when no 4 KiB cut occurred; an output such as `b"\x80failed"` therefore omits the required replacement character.

RC-MASK-02: In `src/agentmarshal/journal/capture.py:422-432`, masking can reproduce a configured private marker inside `[masked: private-marker]`—for example, marker `masked` remains visible—so the final excerpt can still trip the leak scan and contain the marker’s value.

RC-OUTPUT-03: In `src/agentmarshal/record_check.py:234-236`, the payload is published before `open_writer` runs its directory sweep; because published payloads may be removed at any age, a sufficiently large output can be deleted immediately and leave a `check-output` event pointing to a nonexistent file.

RC-TEST-04: `tests/test_record_check.py:1023-1058` tests only one refused value and its docstring does not name the archived “a refused run leaves the journal, the log and the files area untouched” scenario; malformed-project and other foreseeable-refusal coverage required by that scenario is also absent.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"0b946ce10c4cf9d7fb06fffbe3b2a71459859c0b","verdict":"changes_required","findings":["RC-UTF8-01","RC-MASK-02","RC-OUTPUT-03","RC-TEST-04"],"classes":{"RC-UTF8-01":"correctness","RC-MASK-02":"correctness","RC-OUTPUT-03":"correctness","RC-TEST-04":"test-gap"}}
AGENTMARSHAL_VERDICT_END
