# Optional outline ledger

Use only when a complex structural revision benefits from an explicit, reviewable inventory. This is a local organizational diagnostic, not automatic scientific reasoning.

```json
{
  "questions": [{"id":"q1","text":"Which change is distinguishable?","status":"answered","claim_ids":["c1"]}],
  "claims": [{"id":"c1","text":"Supplied result","status":"supported","evidence_ids":["e1"],"condition_ids":["a1"]}],
  "evidence": [{"id":"e1","text":"Supplied calculation or observation"}],
  "conditions": [{"id":"a1","text":"Supplied regime"}],
  "sections": [{"id":"s1","purpose":"Develop the calculation","claim_ids":["c1"],"evidence_ids":["e1"],"condition_ids":["a1"]}],
  "dependencies": [],
  "deferred_material": []
}
```

Every list can be empty where the task warrants it. Question status: answered/open/uncertain. Claim status: supported/proposed/open; “supported” means the supplied material identifies its support, not that the helper verified it. Dependency `{ "from":"c1", "to":"c2" }` can refer to claim, condition or evidence IDs and records prerequisite→dependent. A forward reference is legitimate and is not rejected.

`deferred_material` entries contain `id`, `reason`, `destination`, and `available` (boolean). `available: false` is disclosed as unwritten material, never silently treated as available proof.

```bash
python3 /path/to/physwhen/scripts/check_outline.py outline.json
```

Errors indicate malformed/dangling IDs, conflicting identity, a claimed answer without a claim, a declared supported claim without identified evidence, or a selected claim/condition/evidence absent from the outline. A hint about unwritten deferred material is not an automatic rejection. The helper cannot tell whether an evidence ID actually supports a claim, whether conditions are sufficient, whether sections are coherent, or whether readers prefer the result.
