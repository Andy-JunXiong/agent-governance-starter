# Governed refund task demo

This development-source demo makes one AgentGov boundary visible:

> A coding agent can change files, but capability does not grant authority to
> continue outside the task a human admitted.

The runner creates a disposable refund-service Git repository. It never edits
the AgentGov source checkout. No API key, model call, network service, package
release, or hosted backend is required.

## Run it

From the AgentGov repository root, using the development source:

```powershell
$env:PYTHONPATH = "src"
python examples/governed-refund-demo/run_demo.py
```

The runner requires an interactive terminal for two real operator decisions:

1. confirm the displayed demo-task boundary with the existing `START`
   workflow;
2. select `Decline expansion and narrow the changes` from the real bounded
   scope-resolution prompt.

The demonstration stops if another scope option is selected. It deliberately
does not ask for or record final completion acceptance.

## What is real and what is simulated

| Stage | Provenance |
| --- | --- |
| Task and path boundary | Real AgentGov admitted-task and session contracts, confirmed by the operator |
| Initial code edits | Clearly labelled simulated agent behavior performed by the demo script |
| Changed-file inventory | Real Git facts derived locally by AgentGov |
| Scope mismatch and `blocked` cycle | Real deterministic AgentGov output |
| Narrow-changes choice | Real human selection recorded through the reference single-select contract |
| Restoration of the approval-policy file | Clearly labelled scripted remediation |
| Validation and completion reconciliation | Real AgentGov execution of the task's pre-approved command against an unchanged governed snapshot |
| Final acceptance | Not performed; it remains a separate human decision |

`blocked` means AgentGov refuses to run completion validation while the
working copy exceeds the admitted scope. It does not mean AgentGov prevented,
stopped, or rolled back an external coding-agent tool call.

## Expected story

The terminal output shows:

1. the refund-calculation request;
2. allowed calculation/test paths and denied approval/payment paths;
3. one simulated allowed edit and one simulated out-of-scope edit;
4. a real deterministic FAIL for `refunds/approval_policy.py` and a real
   `BLOCKED` governance cycle;
5. the human's narrow-changes selection;
6. explicitly scripted removal of only the approval-policy change;
7. a real scope PASS, passing pre-approved tests, verified fresh evidence, and
   `REVIEW_READY`;
8. no final acceptance and no commit, merge, release, publication, or
   deployment authority.

## Product boundary

This is a future-0.3 development-source demonstration. It is not behavior
shipped in stable AgentGov 0.2.1. This runner is the M1 executable fixture; the
separate [M2 60-to-90-second HTML walkthrough](../../docs/governed-refund-walkthrough.html)
explains its verified path for a public-facing audience. Neither artifact
establishes first-time-reader comprehension.
