# Sensitive-token boundary repair v1 - 2026-09-01

## Goal and authority

Resume the human-selected Active Task comprehension review without hiding,
moving, deleting, or waiving a preserved governance record. Alignment journey
`mcpj-a1cd67fd42e7414bb3d39faef928f349` recorded the product owner's choice to
split one narrow matcher repair from the still-current review outcome. Native
proposal `prp-a707d9a11cc14c089ed40c802d103ecf` admitted exact task
`p0-sensitive-token-boundary-repair-v1`, and the product owner separately
supplied exact `REPLACE` to take it up.

The task grants no Git, publication, release, deployment, dependency, record
deletion, or scope-exception authority. The two admitted review task records,
local AgentGov and Codex state, and unrelated user paths remain excluded and
preserved.

## Observed blocker

The first review proposal used the portable identifier
`p0-active-task-view-uncoached-comprehension-review-v1`. The existing shared
local-record detector searched for `sk-` followed by at least 20 allowed
characters without a left lexical boundary. It therefore began matching at
the final two characters of `task-` inside the task identifier and rejected a
safe `task.started` event as secret-like. Start rollback was complete.

A replacement safe identifier allowed the review task to start, but the
preserved first proposal path still appeared in its truthful working-copy
scope report. The same detector then rejected persistence of the complete
path-level scope artifact. `govern check` failed closed with no scope event,
so no participant page was generated or presented as trustworthy.

## Bounded repair

The `sk-` branch now requires the token prefix to begin at the start of text or
after a non-alphanumeric, non-underscore separator. Its existing minimum
length and allowed characters are unchanged. GitHub-style tokens, AWS access
keys, bearer tokens, JWT-like values, private-key headers, credential
assignments, and absolute Windows or POSIX paths retain their existing
patterns.

Regression coverage now proves three layers:

- the event store accepts the exact safe `task-view` identifier while still
  rejecting a real `sk-` token at text start and after an assignment/quote
  separator;
- governed start appends `task.started` for that safe identifier;
- scope observation persists and reloads a report containing the safe path,
  while a path component with a real `sk-` token shape remains fail-closed.

The repaired real-repository `govern check` persisted a complete immutable
scope artifact and one evidence-bound `scope.checked` event. It reported five
admitted paths as PASS and retained three pre-existing explicitly excluded
paths as FAIL: `.codex/config.toml` and the two review task records. Those
failures were not hidden, waived, deleted, staged, or claimed by the repair.

## Validation and residual limits

All 27 focused event-store, scope-observation, and development-session tests
passed. The complete supported Python 3.11 suite passed all 1,147 tests with
six platform-conditioned skips. Task governance reported
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reported
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Task JSON parsing and
`git diff --check` passed.

The current callable native tool inventory did not expose
`agentgov_task_completion_record`, so no native completion result was
fabricated. The existing governed `govern finish` path ran the exact six
task-declared commands and reconciled the task-start baseline as `verified`.
It preserved all three non-owned excluded paths byte-identically, admitted the
seven exact task paths, and reported fresh task, HEAD, index, worktree, rename,
and non-ignored untracked identities. This verifies declared commands on one
unchanged snapshot; it does not prove requirement satisfaction, architecture
correctness, security completeness, or human acceptance.

The repair deliberately assumes a supported `sk-` token begins at text start
or after a separator rather than in the middle of an ordinary alphanumeric or
underscore word. It does not claim exhaustive secret detection, scan source
content, alter retention, or prove independent security assurance. The
unchanged fail-closed tests preserve real token-shaped path rejection.

## Review boundary and next step

The uncoached comprehension review has not occurred. Participant identity,
browser behavior, timing, answers, confusion, assistance, comprehension,
adoption, time savings, error reduction, causal benefit, governance
completeness, and ROI remain unknown.

After this repair is completed and reviewed, the next product step is to
resume admitted task `p0-active-view-uncoached-review-v1`, generate its exact
evidence-bound Active Task page, and stop for real participant observations.
This record grants no authority to start that task, recruit a participant,
modify the product, or perform Git or external actions.
