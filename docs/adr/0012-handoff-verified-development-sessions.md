# ADR-0012: Handoff verified development sessions without deleting identity

Status: Accepted

Date: 2026-08-05

Implementation status: completed in development source on 2026-08-05; not
included in published stable 0.2.1.

## Decision gate

Define how a verified working-copy session stops owning `agentgov next` after
Monitor without deleting evidence, inventing approval, or automatically
restarting the same admitted task.

## Context

ADR-0010 routes a verified completion to `monitor development`. Monitor is a
derived read model and intentionally appends no progress event. The active
`.agentgov/current-task.json` pointer therefore remains valid and the latest
session event remains `completion.reconciled: verified`. Running `next` again
returns Monitor forever.

Simply deleting the pointer is unsafe. Task discovery reads valid admitted
task files, so a repository with one completed task would immediately discover
and recommend that same task again. Deletion would also discard the explicit
working-copy link between the exact task digest, comparison base, start time,
and its event sequence.

Making Monitor append a “reviewed” event is also dishonest. Generating a file
does not prove that a human read it, agreed with it, approved the implementation,
or accepted requirement and architecture conclusions. Monitor must remain a
read model rather than an authority or hidden workflow-state writer.

## Decision

### Handoff meaning

The development source implements an explicit `govern handoff` transition whose only durable
write is one immutable `session.handed_off` event for the exact active task
digest. Its outcome is `handed_off`.

Handoff means only:

> the confirming human ended automatic routing responsibility for this exact
> working-copy development session and permits `next` to offer another task.

It does not mean that the requirement is satisfied, architecture is correct,
the implementation is approved, Monitor was read, a commit is authorized, or
the task artifact should be closed, deleted, or edited.

### Admission and freshness gates

A handoff preview is valid only when all of these facts still hold:

- the session pointer is untracked, structurally valid, and resolves the exact
  admitted task id, digest, and comparison-base commit;
- the current-session event stream has one matching start and its latest
  completion is `completion.reconciled: verified`;
- the completion evidence referenced by that event still matches the current
  task, HEAD, index, worktree, rename, and non-ignored untracked identities;
- every governed changed path remains inside task scope;
- no later validation, completion, handoff, malformed event, task drift, or
  unsupported progress conflicts with the verified state.

If evidence is stale or scope has changed, the command fails closed and points
back to `govern finish`. It never converts an old verified event into current
freshness by assertion.

### Preview, confirmation, and atomic write

The command shape is:

```text
agentgov govern handoff --repository . --dry-run
agentgov govern handoff --repository .
```

Preview names the task id/digest, verified evidence reference, retained pointer,
and the single new event target. The real command requires exact `HANDOFF` from
a real interactive terminal. Dry-run, redirected input, cancellation,
non-interactive execution, changed preview state, and repeated invocation write
nothing.

The implementation appends the event through the existing exclusive-create,
fsync-backed local event store. It does not delete, archive, rename, or rewrite
the session pointer, task contract, completion evidence, Monitor output, or any
prior event. Because the transition has one append-only target, it does not
need a multi-file commit protocol. A matching existing handoff is idempotent.

The event actor class is `human`; its authority boundary keeps code change,
exception, commit, merge, and deployment false. Reason codes describe exact
confirmation and fresh verified evidence, not approval.

### Rollover routing

After `session.handed_off`, the retained pointer becomes terminal session
identity rather than active work. `next` may recommend a new start preview with
`--replace-active`:

- exclude the exact handed-off task digest from automatic discovery;
- if one other admitted task remains, name it exactly;
- if several remain, emit `<TASK_JSON>` and require explicit human choice;
- if none remain, offer compact-task title and scope placeholders;
- permit a changed task digest only through normal reviewed start and exact
  `REPLACE` confirmation;
- never infer that the task artifact itself is complete or should change its
  admitted decision state.

The existing `govern start --replace-active` apply path owns the later pointer
replacement and new `task.started` event. Handoff does not perform rollover in
the same write.

### Monitor relationship

Monitor continues to render only validated events and partial-history limits.
Once the new event contract is implemented, it may display a separate handoff
count and the `session.handed_off` timeline entry while keeping latest
completion state `verified` distinct from latest routing state `handed_off`.

A successful local-session Monitor CLI invocation may print
`agentgov govern handoff --repository . --dry-run` as its next command. That is
guidance, not proof that the output was read and not authority to append the
handoff event.

## Implemented contracts

The implementation updates together:

- event validation with a versioned `session.handed_off` / `handed_off` pair;
- handoff preview, JSON/text authority boundary, exact confirmation, exclusive
  append, freshness reconciliation, and idempotence;
- Monitor schema/renderers with separate handoff and completion meanings;
- `next` routing and handed-off-digest filtering;
- CLI help and user guidance;
- fixtures for pass, stale, invalid, redirected, cancelled, duplicate,
  one/many/zero next-task, changed-digest, tracked-state, and no-Git-mutation
  behavior.

Compatibility must be explicit: older valid event versions remain readable,
and a newer unsupported event fails closed rather than disappearing.

## Rejected alternatives

- Delete `.agentgov/current-task.json`: rejected because identity is lost and
  the same admitted task can be rediscovered automatically.
- Rewrite the pointer with a status field: rejected because it turns one
  mutable pointer into the only terminal-history fact and requires a multi-file
  pointer/event transaction.
- Change the task decision from admitted to completed: rejected because session
  routing must not edit the human-owned task contract or conflate local evidence
  with semantic task approval.
- Make Monitor append an implicit review event: rejected because generation is
  not human review and Monitor must remain a derived read model.
- Start the next task inside handoff: rejected because human task choice and
  pointer replacement retain their existing separate preview/confirmation
  boundary.

## Consequences

- The verified task can stop owning `next` without deleting any identity or
  evidence.
- Human meaning is explicit but narrowly bounded to routing responsibility.
- Rollover remains deterministic and reuses reviewed start replacement.
- The same handed-off digest cannot silently restart.
- Future installed update routing gains a definable “no active work” state.
- Development-source runtime now implements the transition; stable 0.2.1,
  workflows, releases, and consumers remain unchanged.

## Validation

Implementation tests protect pointer preservation, append-only atomicity,
freshness, exact confirmation, idempotence, no-approval semantics, event-version
compatibility, task-choice behavior, Monitor separation, and read-only routing.

## Rollback or replacement

A later ADR may replace the retained-pointer approach only if it proves an
equally durable session identity, atomic failure recovery, no implicit approval,
and no automatic rediscovery of the same handed-off task digest.

## Relationship to existing decisions

This decision extends ADR-0010 after verified completion and satisfies the
terminal-session prerequisite in ADR-0011. It does not change ADR-0005's
read-only `next` boundary or ADR-0009's separation of deterministic evidence
from human architecture and requirement judgment.
