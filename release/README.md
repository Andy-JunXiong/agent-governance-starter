# AgentGov release metadata

This directory contains sanitized fixtures for the machine-readable release
manifest contract. A release manifest declares version-channel identity,
supported source versions, readable repository layouts, the target layout,
and whether repository changes or named migrations are declared.

It does not:

- install or update AgentGov;
- determine an exact repository migration plan before the target version runs;
- authorize repository writes;
- claim that migration is safe for an uninspected repository;
- replace human-readable release notes.

Validate a candidate manifest locally:

```powershell
agentgov check release-manifest release/fixtures/valid-rc.json
```

The distributed schema is
[`schemas/release-manifest.schema.json`](../schemas/release-manifest.schema.json).
Future RC publishing should attach a reviewed manifest conforming to this
contract rather than derive compatibility claims from free-form release text.
