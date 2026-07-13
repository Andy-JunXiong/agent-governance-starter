# Human ten-minute adoption pilot

## Purpose

This pilot measures whether a first-time human participant can initialize the
starter kit, inspect its honest warnings, export one capability artifact, and
produce a repository report within ten minutes.

It measures bootstrap usability. It does not measure governance completeness,
model quality, compliance, security, or whether every generated placeholder
has been resolved.

## Roles and evidence boundary

- The participant, not an agent, runs the timed commands and inspects the
  generated files.
- A facilitator may prepare the package and observe the session, but must not
  type commands, edit files, or explain a warning during the timed task.
- Any facilitator intervention is recorded and changes the outcome to
  `assisted` or `needs-revision`.
- Automated test duration is supporting diagnostics, not human timing evidence.

## Pilot target

Use a new, non-existent directory for a neutral sample project. Do not run
`git init` before `agentgov init`, because v0.1 initialization intentionally
accepts only a new or empty target. Do not use AI Radar files, private data,
credentials, production prompts, or an existing repository as pilot input.

## Setup outside the timer

The facilitator completes these steps before handing control to the
participant:

1. Install the current wheel in an isolated environment.
2. Confirm `agentgov --help` works from the participant's terminal.
3. Choose a new target path and a non-sensitive project name.
4. Give the participant this document without a walkthrough.
5. Copy `docs/human-adoption-record.template.md` for recording the result.

Package installation, environment troubleshooting, and reading this setup
section are not timed. Record their duration separately if they create
friction.

## Timed pilot

Start the timer immediately before the participant runs the first command.
The example below uses PowerShell; the participant may substitute another new
target path. In the already activated PowerShell terminal, the participant
starts a visible stopwatch, pastes the complete block, and presses Enter. A
missing start or stop time invalidates the timing evidence.

```powershell
$Pilot = Join-Path $PWD "agent-governance-pilot"
agentgov init $Pilot --project-name "Pilot Project"
Set-Location $Pilot

agentgov check capability prompt-governance/capabilities/example-capability.json
agentgov check references prompt-governance/capabilities/example-capability.json --repository .
agentgov check evaluation evaluation/example-capability
agentgov check agent-skills agent-skills
agentgov export capability prompt-governance/capabilities/example-capability.json --repository .
agentgov check artifact prompt-governance/artifacts/example-capability --repository .
agentgov check repository .
agentgov report repository . --output governance-report.md
```

Before stopping the timer, the participant must inspect `AGENTS.md` and
`governance-report.md`, then answer without facilitator help:

1. Which findings still require a human decision?
2. Why are the evaluation and placeholder warnings non-blocking at this stage?
3. Does this scaffold authorize an agent to merge, publish, or deploy?

Stop the timer when the report exists and the three answers have been given.
Do not stop at initialization alone.

## Expected starting result

For the unmodified v0.1 scaffold after artifact export:

- every command returns the non-blocking exit code;
- the final repository summary is
  `PASS=12 WARN=3 FAIL=0 ADVISORY=1`;
- the warnings cover unresolved governance placeholders, absent capability
  evaluation evidence, and honest `needs_seed_cases` readiness;
- the advisory reminds the participant that static checks do not replace human
  review.

The pilot does not require `WARN=0`. Hiding, deleting, or reclassifying these
warnings to improve the result invalidates the pilot.

## Outcome classification

- `pass`: completed in ten minutes or less, no facilitator intervention,
  `FAIL=0`, report created, and all three interpretation questions answered
  correctly;
- `assisted`: completed in ten minutes or less, but required at least one
  facilitator clarification or command correction;
- `needs-revision`: exceeded ten minutes, produced a `FAIL`, did not create the
  report, or left the participant unable to explain the warnings and approval
  boundary;
- `invalid`: setup was not isolated, the participant had already rehearsed the
  exact task, sensitive/reference-project data was used, or timing evidence is
  missing.

A single `pass` is evidence for this participant and environment, not universal
proof of a ten-minute adoption claim. Preserve every result, including
assisted and needs-revision outcomes.

## After the timer

1. Complete the copied adoption record without improving the observed result.
2. Record the first confusing step, any command retry, and every intervention.
3. Separate product friction from machine or package-installation friction.
4. Convert actionable friction into a narrowly scoped issue or development
   proposal.
5. Do not publish participant identity, local paths, or captured terminal data
   without review.
