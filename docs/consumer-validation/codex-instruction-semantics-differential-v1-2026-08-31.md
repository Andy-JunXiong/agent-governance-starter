# Codex instruction-semantics differential v1 - 2026-08-31

## Outcome

`INSTRUCTION_SEMANTICS_SHARE_16_OF_18_CATEGORIES_CURRENT_ADDS_TWO_INVENTORY_SAFEGUARDS`

The configured installed AgentGov binding and current source each started
exactly once for one local, initialize-only request. Both exited `0`, emitted
one JSON response line, and had empty standard error. No retry, real Codex
client, AgentGov tool call, or stateful workflow occurred.

The analyzer held each instruction scalar only in process memory. Its output
allow-list contained the server version, JSON-encoded byte length and SHA-256,
sentence counts and SHA-256 set comparisons, fixed-category presence, process
shape, and standard-error length and SHA-256. It retained no instruction text,
raw request, raw response, transcript, absolute path, credential, or local
configuration content.

## Deterministic observations

The fixed 18-category rule set has SHA-256
`36cf7d2906c3e9e1b1fa8f83122f8e26de808577d70faecfe2f2700e2fa0f707`.
It was defined before either process started.

| Observation | Installed binding | Current source |
| --- | ---: | ---: |
| Adapter version | `1.6.0` | `1.7.0` |
| Protocol | `2025-11-25` | `2025-11-25` |
| Exit code | `0` | `0` |
| JSON response lines | `1` | `1` |
| Standard-error bytes | `0` | `0` |
| Instruction JSON bytes | `2435` | `2661` |
| Instruction SHA-256 | `501dbb994307b54c2fb050a90765f85e8a3fa12a3d645d0f2d68c3d197e1ad88` | `de376b10ca9261c1ddf35565ecfcdb6213192b8ca5fb31ac5b5878e261960d27` |
| Sentence count | `19` | `20` |
| Unique sentence-digest count | `19` | `20` |

All 19 installed sentence digests were present in current source. The
installed-only sentence-digest count was `0`; the current-only count was `1`.
The current-only sentence SHA-256 was
`2ae13e9b3f465db6aed300f633f14055da0523c67bd909b96934dfaeb71e9dc5`.

Sixteen categories were present in both bindings:

- automatic tool use;
- alignment trigger;
- read-only alignment exemption;
- human direction ownership;
- distinct completion review;
- resolved-alignment self-review;
- required-call fail-closed behavior;
- raw-input privacy;
- exact task record before repository write;
- direct chat is not task admission;
- proposal-review fallback;
- read-only proposal exemption;
- human task admission;
- completion-record boundary;
- drift-review human choice;
- downstream authority non-grants.

No category was installed-only or absent from both bindings. Current source
alone contained these two fixed categories:

- changed paths must be classified by proposed include or exclude scope
  before the native admission form opens;
- the same privacy-bounded path inventory is revalidated immediately before
  admission.

These are deterministic substring-presence results under the fixed rule set.
They are not a general semantic-equivalence proof.

## Advisory interpretation

The one additional current-source sentence maps to two related inventory
safeguards. At this bounded category level, current source adds a precondition
and freshness check; it does not remove or contradict an installed category.
That supports describing the observed policy change as additive rather than a
policy conflict.

This interpretation remains advisory. Fixed indicators can miss paraphrase,
scope, ordering, host behavior, or meaning outside the category set. The
comparison does not establish that instruction bytes, the added safeguards,
or Adapter version caused the real Codex client's current-source `-32603`
initialize closure. The real-client root cause remains unknown.

## Preservation and next review boundary

The configured launcher retained SHA-256
`7dada88a8ccff3dfa40dd52783719e5aced5b293202979ba3d5b75f027b498e7`.
No runtime source, package, Codex configuration, tool allow-list, or external
system changed. Local `.agentgov` and `.codex` state remains outside product
scope.

The next product review may decide whether the byte-level difference warrants
a separately admitted controlled real-client compatibility test. This record
does not authorize that replay, a runtime or configuration change, Git,
publication, release, or deployment.
