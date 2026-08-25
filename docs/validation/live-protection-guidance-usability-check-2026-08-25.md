# Live protection-guidance usability check - 2026-08-25

## Result

`USER_REPORTED_INSUFFICIENT`

The bounded current-browser check established that Monitor 1.6 internal
navigation works, but the product owner did not find the reached Task Detail
sufficient for choosing the next human action. This is usability evidence for
one fixture-backed current-browser experience, not production, cross-browser,
causal-benefit, or cross-event resolution evidence.

## Governed boundary

- Alignment journey: `mcpj-a722d873f52c46f1b8d38e5e13867f8d`
- Task: `p0-live-protection-guidance-usability-check-v1`
- Proposal: `prp-4b6286564aaf49d1bd98e2c7c81ea6b9`
- Task-start baseline:
  `sha256:f2f707ec4575a573a972b7cdc43cc411bd1225bc7d5ba2a32ec4802adc0bd5cc`

The first capture command used the check-phase `--baseline` option and was
rejected by argument parsing before any file was written. The immediate retry
changed only that option to capture-phase `--output` and created the baseline.

## Agent-observed behavior

A task-owned temporary repository produced one self-contained Monitor 1.6 page
with one deterministic `scope_boundary` Protection Event. Its status remained
`observed_resolution_unknown`, and its guidance target was `task_detail`.

The temporary HTTP server bound only to loopback and returned HTTP 200. In the
current browser, the page exposed exactly one guidance link labeled `Review
task scope and changed paths` with internal target `#tasks`. The first click:

- changed the address fragment to `#tasks`;
- resolved to one present Task Detail target;
- placed the target within the Agent-observed viewport;
- exposed zero external links, zero buttons, and zero forms.

Those deterministic observations prove only that the internal link worked.
They do not prove that the human noticed the destination or could act on it.

After the product owner reported not seeing Task Detail, a bounded visual
recheck found the browser far below that heading in the expanded embedded
machine-readable Monitor. The address still retained `#tasks`, but the heading
was outside the current viewport. Re-activating the same guidance placed Task
Detail at the viewport top for the separate content-sufficiency judgment. No
page state or screenshot is retained as durable evidence.

## User-reported behavior

The product owner reported:

- the guidance label was clear;
- Task Detail was not seen after the first handoff;
- the long embedded machine-readable block required explanation; and
- after Task Detail was made visible and its contents were explained, the
  current detail was insufficient for choosing the next action.

The accepted product interpretation is that successful anchor navigation is
not sufficient usability. The destination is not prominent enough in the
observed journey, the technical audit block can dominate attention when
expanded, and the visible Task Detail gives high-level status and counters but
not the exact failed boundary, affected paths, or smallest concrete next human
action.

## Cleanup and authority

The browser test tab was closed, the loopback process was stopped, and the
task-owned temporary directory was deleted. The temporary content is not
recoverable. No raw event payload, source content, absolute temporary path,
browser identity, screenshot, credential, or host identity is retained here.

This check changed no Monitor source, schema, test, package, installation,
consumer, Git, publication, release, deployment, or external state. It grants
no remediation, task, scope, exception, Git, publication, release, deployment,
or external-write authority.

## Validation and advisory review

- Focused Monitor and user-documentation tests: 70 passed.
- Task governance: `PASS=3 WARN=1 FAIL=0 ADVISORY=3`.
- Repository governance: `PASS=26 WARN=2 FAIL=0 ADVISORY=4`.
- Task-start scope: `PASS=6 PRESERVED=13 FAIL=0 TOTAL=19`.
- Task JSON, bounded privacy scanning with zero findings, and
  `git diff --check`: passed.
- Native current-Agent self-review:
  `srv-e9e53298a6beb41ffd3df19cc5734f86`.

The review found the requirement, human-versus-Agent evidence attribution,
scope, privacy, implementation non-change, and denied authority consistent. It
is advisory current-Agent judgment, not independent assurance, and it does not
authorize the recommended repair.
