# Internal adoption rehearsal record

> **Evidence status:** Invalid as human adoption evidence. This assisted
> internal rehearsal records product learning, not independent user validation.

## Session

- Date: 2026-07-13
- Participant identifier or pseudonym: internal-operator-01
- Prior familiarity with this project: experienced (internal operator rehearsal)
- Facilitator: Codex
- Operating system: Windows
- Python version: 3.13.7
- Starter-kit version or commit: 0.1.0.dev0, current uncommitted working tree
- Isolated installation method: locally built wheel installed in a temporary venv
- Rehearsal target was new and non-sensitive: yes

## Timing

- Setup duration, not timed as adoption: not measured
- Timed start: not recorded
- Timed stop: not recorded
- Timed elapsed duration: not measured; participant reported that it finished very quickly
- Timing evidence source: participant recollection and terminal screenshots; no stopwatch evidence

## Observed command results

| Step | First-attempt result | Retry needed | Participant observation |
|---|---|---|---|
| Initialize scaffold | PASS with 47-placeholder WARN | no | Scaffold created in the isolated target |
| Check capability | PASS | no | Capability contract accepted |
| Check references | PASS=3 WARN=1 FAIL=0 | no | Evaluation evidence is not yet declared |
| Check evaluation | WARN | no | `needs_seed_cases` is valid but incomplete |
| Check agent skills | PASS=4 FAIL=0 | no | Four packaged skills satisfy the contract |
| Export capability | PASS | no | Markdown and artifact JSON exported |
| Check artifact | PASS | no | Manifest, source hash, and Markdown are current |
| Check repository | PASS=12 WARN=3 FAIL=0 ADVISORY=1 | no | Honest warnings and human-review advisory remained visible |
| Write report | PASS | no | `governance-report.md` created and inspected |

## Final findings

- Final `PASS` count: 12
- Final `WARN` count: 3
- Final `FAIL` count: 0
- Final `ADVISORY` count: 1
- Report created: yes
- Governance placeholders remained visible: yes
- Evaluation readiness remained honest: yes

## Human interpretation

- Findings the participant identified as requiring a human decision: none identified;
  the participant interpreted the fast successful run as requiring no further
  human decision.
- Participant explanation of non-blocking warnings: participant did not know.
- Participant explanation of merge, publish, and deploy authority: participant
  did not know.

## Friction and assistance

- First confusing step: how to run the provided PowerShell command block
- Commands retried: none observed in the submitted screenshots
- Facilitator interventions, including exact timing and reason: before the
  command run, the participant asked how to run it; the facilitator explained
  using the activated VS Code PowerShell terminal and pasting the command block.
- Product friction: the rehearsal handoff did not make the paste-and-run
  interaction sufficiently obvious. More importantly, successful command completion was
  mistaken for governance completion; the report did not make the remaining
  human decisions, warning meaning, and authority boundary sufficiently clear
  to this participant.
- Environment or installation friction: The facilitator process did not inherit
  a stable Python PATH; absolute interpreter paths were used. Python 3.12 and
  3.13 lacked setuptools, so pip build isolation downloaded the declared build
  dependency. An initial piped help check was falsely flagged because output
  truncation affected the PowerShell pipeline; a direct `agentgov --help`
  check subsequently returned exit code 0.
- Sensitive information captured: no

## Outcome

- Classification: invalid (missing timing evidence), with a needs-revision
  comprehension signal
- Evidence supporting the classification: terminal screenshots and the generated
  report confirm `PASS=12 WARN=3 FAIL=0 ADVISORY=1`; facilitator execution
  guidance was required, exact timing was not recorded, no remaining human
  decisions were identified, and the warning and authority questions could not
  be answered.
- Smallest recommended improvement: add an explicit paste-and-run instruction
  before the timer and a concise interpretation section that distinguishes
  successful static checks from unresolved human decisions, explains why the
  current warnings are non-blocking, and states the merge/publish/deploy authority
  boundary.
- Retest required: yes, after the interpretation guidance is improved, using an
  unfamiliar participant and explicit stopwatch evidence
- Reviewer: Codex
- Review date: 2026-07-13

This record is one observed session. It must not be presented as universal
proof, a governance coverage percentage, or evidence of model quality.
