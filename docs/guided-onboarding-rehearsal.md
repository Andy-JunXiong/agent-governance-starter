# Guided onboarding automated rehearsal

## Purpose

This rehearsal verifies the packaged guided onboarding sequence on Windows
from a realistically deep target path. It is automated implementation evidence,
not a human usability pilot and not evidence for a ten-minute adoption claim.

## Contract

Date: 2026-07-25

Environment:

- Windows PowerShell;
- pipx 1.11.1;
- isolated AgentGov `0.1.0.dev0` installation from the current working tree;
- Python 3.13.14 in the final isolated tool environment;
- a target nested through seven additional path segments;
- Git context represented in the target;
- an unrelated empty `.venv` representing a stale project environment.

The non-interactive tool session cannot supply a real human terminal decision.
The confirmation step therefore used the same injectable terminal decision
boundary exercised by the CLI tests. It supplied exact `ADOPT` while reporting
an interactive terminal. This validates installed-package orchestration but
does not replace a fresh uncoached human pilot.

## Sequence exercised

```powershell
agentgov doctor <deep-target> --non-interactive
agentgov onboard <deep-target> --project-name "Guided Windows Rehearsal" --dry-run
agentgov onboard <deep-target> --project-name "Guided Windows Rehearsal"
agentgov next <deep-target> --non-interactive
```

The interactive onboarding command displayed the exact target and 25 planned
files before the injected exact `ADOPT` decision.

## Observed results

| Stage | Result |
|---|---|
| Isolated install | `PASS` |
| Doctor | `PASS=3 WARN=1 FAIL=0 ADVISORY=2` |
| Stale project `.venv` | Detected as advisory; not used or repaired |
| Dry-run | `CREATE=25 PRESERVE=0`; JSON parsed successfully |
| Confirmation | Exact `ADOPT` accepted through injected terminal decision |
| Adoption | 25 reviewed files created |
| Automatic first check | `PASS=14 WARN=4 FAIL=0 ADVISORY=4` |
| Next action | `incomplete_evidence`, source `governance:placeholders` |
| Target `.venv` after run | Empty; zero files created or modified inside it |

## Product correction from the rehearsal

The first run exposed that interactive `onboard` created the reviewed files but
only told the user to run the first repository check separately. ADR-0005 says
onboarding sequences the first check. The CLI was corrected so confirmed
onboarding now runs that read-only check immediately and then points to
`agentgov next`.

The complete sequence was reinstalled and repeated after the correction.

## Documentation decision

The English and Chinese HTML Quickstarts may describe the guided commands as a
development preview because the packaged automated path is verified. They must
not replace the current primary path or claim uncoached human success until a
person completes the fresh pilot and records timing, assistance, wrong turns,
and final understanding.

No commit, push, tag, package publication, release, or deployment was
performed.
