# Installed shared-data path contract diagnostic v1

Date: 2026-08-25

## Outcome

`PATH_ASSUMPTION_SUPPORTED_PRESENCE_AND_DIGEST_UNRESOLVED`

Without building or installing an AgentGov wheel, the available local
contracts support the prior validation target:

```text
<runtime>/share/agent-governance-starter/templates/
```

That is the expected destination for a wheel member under the `data` scheme
whose subpath begins `share/agent-governance-starter/templates/` when pip 24.0
installs into the inspected Python 3.11 Windows virtual-environment scheme.
This is a contract-level conclusion, not retroactive proof about the removed
runtime.

The removed runtime and wheel cannot establish whether the exact installed
template existed or whether its bytes matched the source template. Those two
questions remain unknown.

## Method and boundaries

The diagnostic used only repository-local declarations, sanitized prior build
evidence, and import-time inspection of the already installed local Python
3.11, pip 24.0, and `sysconfig` implementations. Synthetic prefix strings on
two drive letters were passed to read-only scheme calculations; neither path
was created. The previous wheel and runtime were not reconstructed or reused.

No AgentGov wheel build or installation, virtual-environment creation, source
or packaging change, network request, credential access, external model call,
consumer rehearsal, Git mutation, publication, release, deployment, or
external write occurred.

## Contract chain

| Layer | Observed local contract | Bounded conclusion |
| --- | --- | --- |
| Repository packaging declaration | `pyproject.toml` maps `templates/*.template.json`, `templates/*.template.md`, and `templates/tasks.keep` to `share/agent-governance-starter/templates`. | The intended shared-data subpath is explicit. |
| Wheel data-key shape | The short-root contract measures the current packaging target as `<dist>.data/data/share/agent-governance-starter/templates/example-capability.input.schema.template.json`. A prior sanitized wheel inventory independently records the same `.data/data/share/.../templates/` shape for an earlier build. | The shared template uses the wheel `data` scheme key. The earlier inventory is supporting precedent, not proof of the removed current wheel's exact member list. |
| pip 24.0 wheel installer | Local source inspection shows that pip parses `.data/<scheme-key>/<subpath>` and calculates the destination as `scheme_paths[scheme_key]` joined with the subpath. | A wheel `data/share/...` member installs under `scheme.data/share/...`. |
| pip 24.0 scheme calculation | For two synthetic Windows runtime prefixes, `get_scheme(..., prefix=<runtime>).data` equaled the exact supplied prefix. | Under the inspected pip contract, the data base is the runtime root, not `Scripts`, `Lib`, or `site-packages`. |
| Python 3.11 `sysconfig` | `get_paths("nt_venv", vars={"base": <runtime>, "platbase": <runtime>})["data"]` equaled the exact runtime prefix. The preferred local prefix scheme was `nt`. | The standard Windows venv scheme independently agrees with pip's data base. |

The source template used by the earlier gate remains present in the repository
with SHA-256
`e596a428f37f914c6652d650c36df7a47261d6d75118858b6a6ebf99abd91fd6`.
There is no retained installed counterpart against which that digest can be
compared.

## Decomposed gate

| Question | Result | Evidence limit |
| --- | --- | --- |
| Was `<runtime>/share/agent-governance-starter/templates/...` the correct path assumption? | **Supported** for the inspected Python 3.11 / pip 24.0 Windows scheme. | Static and local-tool contract evidence does not prove the removed runtime's exact configuration. |
| Did the removed runtime contain the exact shared template? | **Unknown**. | The combined gate did not retain the presence sub-result, and the runtime was removed. |
| Did installed bytes match the source bytes? | **Unknown**. | The combined gate did not retain the digest sub-result, and no installed file remains. |
| Was the stop caused by a wrong standard venv data-root assumption? | **Not supported by the inspected contracts**. | This narrows the likely branch but does not establish absence or mismatch. |

The previous result therefore narrows from three equally open explanations to
one path branch that is contract-supported plus two historical facts that
remain unresolved. It must not be rewritten as installed-template success.

## Required next evidence

If the product owner wants deterministic closure before independent rehearsal
v2, a separately admitted exact-current-source build/install inspection is
still necessary. That inspection should retain the wheel and runtime until it
records three independent gates:

1. the exact wheel member is present under `.data/data/share/...`;
2. the runtime's actual `scheme.data` and resulting destination are recorded
   in normalized form;
3. installed-file presence and source/installed byte identity are recorded as
   separate results.

This recommendation is product-review input only. It grants no build,
installation, rehearsal, source, Git, publication, release, deployment, or
external-write authority.

## Validation and process boundary

- the short-root helper suite passed all 7 tests with 1 platform-limited
  symbolic-link skip;
- the complete supported Python 3.11 product suite passed all 1102 tests with
  5 platform-limited skips in 168.423 seconds;
- task governance returned `PASS=3 WARN=1 FAIL=0 ADVISORY=3`;
- repository governance returned `PASS=26 WARN=2 FAIL=0 ADVISORY=4`;
- task JSON parsing and `git diff --check` passed;
- the previous build evidence, helper implementation, and helper tests retained
  exact SHA-256 values `105b8170...c0c74c`, `634bc63e...92161daf`, and
  `ecd3115d...9ff180c` respectively.

The admitted validation list used an unavailable `python` launcher and two
nonexistent CLI forms, `agentgov task validate` and `agentgov repo validate`.
Those declared invocations failed before validation and wrote nothing. The
current repository's actual equivalents use `py -3.11`, `agentgov check task`,
and `agentgov check repository`; all equivalent checks above passed. The
admitted task record was not altered to hide this contract defect.

The task-start scope baseline was also not captured before initial read-only
diagnosis and document drafting. The three task document changes were exactly
reverted before capture, then restored. Baseline
`sha256:761b45d804b4aadf13d40e58e2eecd6c275373d9965c758546d80e908edc0795`
truthfully begins only at its recorded capture and does not claim to prove
earlier state. Final post-capture scope comparison is
`PASS=19 PRESERVED=22 FAIL=0 TOTAL=41`.

Distinct native current-Agent advisory review
`srv-eac6541cb05f7f95fa5851dd19c12e9e` found the requirement decomposition,
documentation-only architecture, post-capture scope, toolchain inference,
privacy boundary, retained unknowns, and denied authority consistent. It also
preserved the validation-command defect and delayed-capture limit rather than
treating them as exceptions. This is a separate self-review pass, not
independent assurance. The native task-completion-record tool is unavailable
in this session, and no completion record is claimed.
