# Governance benefit evidence

AgentGov does not infer ROI or claim that a repository incident was prevented.
It can compare two versioned repository-report snapshots and expose the exact
finding transitions with their denominator:

```powershell
agentgov benefits compare before.json after.json
agentgov benefits compare before.json after.json --format json
```

The comparison reports:

- finding counts in each input and the number of matched check IDs;
- deterministic failures that changed from `FAIL` to `PASS`;
- deterministic failures that changed from `PASS` to `FAIL`;
- all non-passing findings that changed to `PASS`;
- checks added or removed between versions, without classifying them as an
  improvement or regression;
- every matched status transition.

This is the first monitor slice, not a causal benefit dashboard. GitHub Actions
already preserves the JSON repository report for each run. After real NYC runs
exist, two downloaded snapshots can establish reviewable change evidence.

It does not observe project-test outcomes, PR merge state, runtime incidents,
time saved, false positives, or human decisions. Those require a separate CI
observation event contract and explicit retention policy before any trend or
benefit claim is valid.
