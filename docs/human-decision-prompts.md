# Proactive minimal-input human decisions

AgentGov keeps consequential judgment with the user while moving mechanical
interaction into the system. When a real boundary is reached, the host should
proactively show one concise choice instead of asking the user to remember an
internal command or confirmation word.

## Contracts

`agentgov.human-decision-prompt` 1.0 binds:

- the exact host-interaction request or admission route and its digest;
- what needs a decision and why now;
- two through five bounded options and the exact effect of each;
- one recommended safe default, which is never selected automatically;
- exactly one selection and no required free text;
- the host's real delivery and decision-recording capability;
- zero authority from merely displaying the prompt.

`agentgov.human-decision-result` 1.0 binds:

- the exact prompt ID and digest;
- the exact source request ID and digest;
- one displayed option and its predeclared transition;
- a human actor and the Adapter recording method;
- authority for only that selected transition, with no code, scope-expansion,
  exception, Git, deployment, or release authority.

Unknown fields, agent actors, unavailable hosts, option substitutions, prompt
drift, source drift, transition drift, and target races fail closed. Neither
contract carries raw prompts, transcripts, source content, credentials,
absolute host paths, or the user's raw keystroke.

## User experience

No-write requests, verified active-task continuation, and standing-policy
fast-track show no decision prompt. A planned low-risk human-review route shows
one card:

1. approve the exact reviewed task;
2. request changes;
3. reject it.

The host may render these as buttons, radio choices, or another native
single-select control. The reference terminal presenter uses the numbers
`1`-`3`; it does not accept `ADMIT` or a free-text rationale. Approve creates
only the exact reviewed task after revalidation. The other choices record the
decision and write nothing.

Scope and completion prompts carry a selected option into only the existing
`scope.decision_recorded` or `session.reviewed` Core event. They do not invent
new authority. Material or ambiguous `full_review` work remains a substantive
human review rather than being compressed into a misleading quick approval.

When the meaning itself is unsettled, AgentGov does not force that substantive
discussion into a premature single-select card. It first uses the
[governed clarification protocol](clarification-dialogue.md): one
natural-language question at a time, with the current center and observed
drift visible. Those turns are not governance decision episodes. Only after
material unknowns are resolved and the option effects are stable does this
prompt/result contract record one final re-centering choice.

## Host truthfulness

The reference foreground Adapter declares structured single-selection
recording. A connected host can therefore render the prompt and return the
result without asking the user to compose JSON or type a magic word.

Current Codex lifecycle Hooks remain `context_only` with decision recording
`unavailable` for custom governance choices. They receive the proactive prompt
and option labels as context, but AgentGov does not pretend that Hooks supplied
a trusted button callback. Codex's native tool-permission prompt remains a
separate host-managed permission and is not task, scope, or completion
approval.

Terminal interactivity and host actor declarations are operator attestations,
not cryptographic human identity. Production Adapters remain responsible for
authenticating their own native user session and preserving the exact contract
digests.
