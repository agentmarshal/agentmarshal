AM-001: In `src/agentmarshal/agree.py:156`, drift is checked before `--contract` mismatch, so when the pin, current hash, and supplied hash are all different, the refusal omits the supplied hash; this violates the requirement that a differing `--contract` refusal name both the given and current hashes.

AGENTMARSHAL_VERDICT_BEGIN
{"reviewed_commit":"972a17366c44e995fb3ddeadf12ff7ab5ffbe79b","verdict":"changes_required","findings":["AM-001"]}
AGENTMARSHAL_VERDICT_END
