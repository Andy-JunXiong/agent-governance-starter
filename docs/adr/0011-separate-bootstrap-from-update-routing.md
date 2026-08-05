# ADR-0011: Separate bootstrap from installed update routing

Status: Accepted

Date: 2026-08-05

## Decision gate

Decide where installation and update guidance belong after the exact-wheel
guided-next rehearsal, without adding runtime behavior or implying that an
unpublished 0.3 release exists.

## Context

The installed rehearsal proved that `agentgov next` can route repository state
only after an AgentGov executable already exists. It cannot inspect Python,
pipx, PATH, package availability, or trust decisions before installation
because there is no CLI process to run. Treating that state as an action inside
`next` would create a circular bootstrap claim.

Installed AgentGov already exposes `agentgov update --check .`. The check is
read-only and distinguishes the executable environment, installed and
available versions, release channel, manifest source, artifact identity,
repository layout readability, and refresh need. It grants neither tool-update
nor repository-write authority.

The current bundled development manifest truthfully declares
`0.3.0.dev0`, channel `development`, and `artifact: null`. It cannot authorize
or even identify a distributable update. Stable 0.2.1 must not be presented as
newer than development source, and no future 0.3 URL or digest may be invented.

Two progress problems also block immediate `next` integration:

1. recommending only `agentgov update --check` cannot change observed state,
   so following the recommendation returns the same recommendation forever;
2. a verified development session remains the active working-copy session,
   while `monitor development` records no handoff or closure event. Update
   availability cannot safely displace that terminal task or prove that its
   review is complete.

## Decision

### Pre-install bootstrap

Pre-install bootstrap belongs to a reviewed public installation surface, not
to `agentgov next`. The stable path remains an isolated pipx installation of a
fixed release wheel, pinned to a reviewed version and immutable release URL.
The public Quickstart and README must present installation before any
`agentgov` command: installation necessarily happens before `agentgov next`
can run.

Development-source execution remains explicitly separate. A source checkout,
local wheel rehearsal, branch URL, or `0.3.0.dev0` identity is not a stable
release pin and must not replace the published stable command.

AgentGov does not repair or activate the adopting project's `.venv`, install
its dependencies, choose a package source dynamically, or claim that a mutable
branch is an update channel.

### Installed update inspection

After installation, `agentgov update --check .` remains the explicit read-only
surface for inspecting tool and repository update state. It may use bundled
installed release metadata or an explicitly supplied, strictly validated
manifest. The check does not download, install, refresh, write, or authorize a
later update.

The current future-0.3 development source keeps update inspection separate
from `agentgov next`. No `next` precedence or schema change is authorized by
this decision.

### Gates for any future `next` update route

Update availability may enter `agentgov next` only after a separate admitted
implementation proves all of the following:

- the CLI is already running from the supported isolated tool environment and
  is not shadowed by the target project's virtual environment;
- a strictly validated stable manifest identifies a version newer than the
  installed version, a fixed-tag HTTPS wheel URL, exact wheel filename,
  lowercase SHA-256, pipx installation method, readable current layout, and a
  declared target layout;
- the manifest source is immutable and reviewable; `next` does not infer
  “latest” from a mutable branch, fabricate coordinates, or silently turn a
  network response into release authority;
- adoption conflicts, missing required scaffold, deterministic repository
  `FAIL`, invalid local session/event state, and active development work retain
  their documented precedence;
- a verified session has an explicit, separately designed terminal handoff or
  rollover contract, so update routing never interrupts an active task and
  Monitor review cannot loop forever;
- the selected update recommendation leads to an observable state transition
  after existing exact interactive confirmation and process relaunch; a
  read-only check alone is not treated as progress;
- cancellation, redirected input, and non-interactive execution remain
  zero-write results, and `next` itself still never executes the recommendation;
- repository refresh, consumer migration, workflow changes, release, merge,
  and deployment remain separate authority decisions.

Until every gate is satisfied, update state may remain visible through
`agentgov update --check`, `status`, CI evidence, and release review, but it
does not displace the guided development action selected by `next`.

## Owns

- The boundary between public pre-install bootstrap and installed CLI state.
- The continued use of isolated, fixed-release stable installation.
- The read-only installed update-inspection entry point.
- Admission gates and stop conditions for future `next` update routing.
- The conclusion that current development metadata cannot justify an update
  action.

## Does not own

- A new installer, bootstrap script, package index, release-discovery service,
  update cache, acknowledgement file, or local event type.
- Terminal session handoff, rollover, Monitor acknowledgement, or action-loop
  self-reporting behavior.
- Tool installation, update execution, repository refresh, workflow mutation,
  consumer migration, release, merge, or deployment.

## Consequences

- Stable users continue to install before invoking AgentGov; no impossible
  pre-install `next` step is documented.
- Existing `next`, update, schema, and manifest behavior remains unchanged.
- The exact-wheel rehearsal supports installed routing mechanics but does not
  become a release claim.
- A future update-routing slice is blocked by both trustworthy stable artifact
  identity and a non-looping terminal-session transition.
- The next product-defining implementation should solve verified-session
  handoff/rollover before adding more precedence branches.

## Validation

Documentation tests must protect the stable-install-first order, isolated pipx
boundary, explicit `agentgov update --check`, `artifact: null` development
limit, no-active-work gate, non-looping progress requirement, and denied
execution/release authority.

The full source suite and repository governance checks remain required even
though this decision changes no runtime code.

## Rollback or replacement

A later ADR may admit update routing only with observed stable-release and
session-handoff evidence. It must preserve immutable artifact verification,
read-only `next`, explicit interactive update authority, environment isolation,
and every existing governance/active-work precedence boundary.

## Relationship to existing decisions

This decision refines ADR-0004's installer ownership without replacing its
isolated-tool requirement. It refines ADR-0005 and ADR-0010 only by declaring
what does not yet enter `next`; their current onboarding and development
precedence remains unchanged.

ADR-0012 now defines the retained-pointer, append-only handoff contract that a
future implementation must satisfy before the active-work gate can be used by
update routing.
