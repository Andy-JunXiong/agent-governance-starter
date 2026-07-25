# Fresh uncoached guided-onboarding pilot

## Purpose

This pilot measures whether a first-time human participant can install the
reviewed AgentGov build, diagnose a test repository, preview every planned
write, authorize create-missing-only onboarding, complete the first repository
check, and identify one next action without live coaching.

It measures one observed adoption experience. It does not prove governance
completeness, model quality, security, compliance, or universal ten-minute
adoption.

## Evidence boundary

- The participant receives only the repository URL, the participant handout,
  and a fresh non-sensitive test repository.
- The facilitator may observe and keep time but must not type, point to a
  command, explain a finding, or correct a mistake during the session.
- Every intervention changes the outcome from `pass` to `assisted` or
  `needs-revision`.
- Automated tests and the packaged Windows rehearsal are supporting
  implementation evidence, not human usability evidence.
- Preserve wrong turns, retries, WARN, FAIL, and ADVISORY results exactly as
  observed.

## Pilot inputs

Prepare:

1. a participant who has not rehearsed the current guided workflow;
2. a supported Windows, Linux, or macOS environment with Python 3.11 or newer;
3. `pipx`, installed before the session but without AgentGov installed;
4. a fresh local Git repository containing only a harmless README;
5. [the participant handout](uncoached-onboarding-handout.md);
6. a copy of
   [the observation record](human-adoption-record.template.md).

Do not use AI Radar files, private data, credentials, production prompts, or a
repository whose contents the participant is not authorized to change.

## Facilitator setup

Record the exact AgentGov commit under test. The participant must install that
reviewed commit rather than an unpinned branch. Confirm only that Python and
`pipx` are available; do not install AgentGov, open the Quickstart at the
relevant section, or run an AgentGov command for the participant.

Give the participant:

- `https://github.com/Andy-JunXiong/agent-governance-starter`;
- `docs/uncoached-onboarding-handout.md`;
- the path to the prepared test repository.

Start the timer when the participant begins reading the handout. Stop when the
participant has generated a repository report and answered the interpretation
questions in the handout. Record installation time and guided-adoption time
separately as well as total elapsed time.

## Required observed sequence

The participant should independently reach this lifecycle:

```text
install reviewed commit
doctor
onboard --dry-run
onboard
exact ADOPT decision
automatic first repository check
next
report repository
interpret findings and authority boundary
```

Do not mark the session failed merely because the participant uses help,
retries a command, or takes a different safe route. Record what happened and
apply the outcome rules below.

## Required evidence

The completed record must include:

- total, installation, and guided-adoption duration;
- commands actually entered, including mistakes;
- first-attempt exit and visible result for every stage;
- whether dry-run wrote any file;
- whether the participant trusted and understood the exact `ADOPT` boundary;
- whether redirected or non-interactive input was attempted;
- files created by confirmed onboarding;
- first repository-check summary;
- `next` action and source finding;
- final report path and finding counts;
- every facilitator intervention;
- the participant's answers about scaffold completeness, finding semantics,
  and merge/release authority.

## Outcome classification

- `pass`: completed without facilitator intervention, produced the report,
  retained `FAIL=0`, and correctly explained dry-run, scaffold incompleteness,
  finding semantics, and the human authority boundary;
- `assisted`: completed with `FAIL=0`, but required at least one facilitator
  clarification or command correction;
- `needs-revision`: could not complete the workflow, retained a product-caused
  FAIL, did not produce a report, or could not explain the authority boundary;
- `invalid`: the participant had rehearsed the workflow, timing evidence is
  missing, the tested commit is unknown, the target was not fresh and
  non-sensitive, or the facilitator performed the task.

Record elapsed time as evidence; do not change the classification solely to
make a ten-minute claim pass. One successful session is evidence for that
participant and environment, not universal proof.

## After the session

1. Complete the observation record without improving the result.
2. Separate product friction from environment and installation friction.
3. Identify the first point where the participant stopped knowing what to do.
4. Propose only the smallest evidence-supported correction.
5. Retest with a fresh participant if behavior or primary guidance changes.
6. Do not promote guided onboarding from development preview until the record
   is reviewed and its unresolved findings are explicitly accepted or fixed.
