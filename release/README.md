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

`current.json` is the reviewed compatibility baseline bundled with the tool.
For a stable installed version it intentionally leaves `artifact` null: a
wheel cannot contain its own final SHA-256. Only this recognized bundled file
uses the installed-metadata validator. Public stable release manifests remain
strict and must name the fixed-tag wheel asset and its final SHA-256.
The normal update path discovers `release-manifest.json` from the latest stable
GitHub Release; `--manifest` remains an explicit offline/test override. The
stable manifest names a fixed-tag wheel asset and its SHA-256. The tag-triggered
release workflow runs tests, builds the wheel, generates the manifest after the
wheel exists, validates it, and publishes both assets. Non-anchor layout
migrations remain outside the implemented slice.
