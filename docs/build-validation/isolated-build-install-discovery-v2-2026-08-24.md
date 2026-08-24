# Isolated build, install, and no-model discovery v2 - 2026-08-24

## Outcome

`PASSED_ISOLATED_BUILD_INSTALL_DISCOVERY`

Native proposal review admitted exact task
`p0-isolated-build-install-discovery-v2` through proposal
`prp-3f2e5504ce3c46e2b20af4068bff7771`. The product owner separately
instructed the Agent to execute it. The non-executed v1 task remains preserved:
its declared AgentGov checks used an inert module entry, so v2 replaced those
commands before any v1 build or installation attempt.

## Deterministic preparation

The retained binary-safe staging root was still inside the operating-system
temporary boundary. Its file-backed archive SHA-256 remained
`19233A360DCD824913E7CD400FF11C0FD4963A9B58233B01B98E6CDADDB114CB`.
The source still contained 231 files. Current and staged hashes matched for the
two exact `change_scope` and `governance_mcp` overlays. Required package
surfaces were present, and all four excluded schema-diagnostic and
process-observation modules remained absent.

One fresh task temporary root was then created. The only dependency-download
command saved one `setuptools 84.0.0` wheel with SHA-256
`51A52592B3B99E102B609654876BD65F19F999935166D1352678931132B0C670`.
All later package operations set pip to no-index mode. The verified source was
copied into the new task root so the retained staging source remained
unchanged.

## Build, install, and discovery result

| Observation | Result |
| --- | --- |
| Build Python | `3.11.9` |
| Build backend | `setuptools 84.0.0` from the task cache |
| Built wheel | `agent_governance_starter-0.3.0rc1-py3-none-any.whl` |
| Wheel SHA-256 | `2C05FD3816D2006402F447788721B7D63DE1DF08CC31990B4DD38A86F6744C94` |
| Wheel size | 490726 bytes |
| Install Python | `3.11.9` in a separate fresh environment |
| Install mode | offline, no index, no dependencies |
| Installed distribution | `agent-governance-starter 0.3.0rc1` |
| Declared runtime dependencies | none |
| Installed Adapter | `1.7.0` |
| Tools without form elicitation | 6 |
| Tools with form elicitation | 8 |
| Completion tool | `agentgov_task_completion_record` |
| Completion input | only `task_path` |
| Completion destructive hint | false |

The discovery probe used the installed package with Python isolated mode and
dispatched only MCP `initialize` and `tools/list` requests. It did not call an
AgentGov tool or an external model. The first temporary probe invocation
stopped at Python parsing because PowerShell removed embedded double quotes;
no installed module was imported and no MCP request ran. Correcting only the
temporary probe quoting produced the result above. No product source, test,
package, or consumer repair occurred.

## Preservation and limits

The task root retains one dependency cache, two virtual environments, one
built wheel, the copied build source, and build by-products. It contains no Git
directory and has no running Python process. The original staging source still
contains 231 files, with no build directory or egg-info directory. Both
predecessor task records remained byte-identical during execution.

Consumer cloning or writing, consumer MCP binding, Codex or external-model
sessions and turns, completion-tool calls, completion records, cleanup, Git
operations, publication, release, and deployment remain at zero. This result
proves that the current staged Adapter can build, install, and expose its
expected tool inventory in isolation. It does not prove installed STDIO
process integration in a consumer, model-to-MCP initialization, completion-card
behavior, the full automatic journey, cross-host behavior, causal benefit, or
return on investment.

This record contains no raw command output, source content, credential, user
identity, absolute host or temporary path, prompt, response, transcript,
screenshot, or model-private reasoning.

## Starter validation and review

All 67 user-documentation and public-documentation freshness tests pass. The
complete supported Python 3.11 suite passes all 1083 tests with 4
platform-limited skips in 175.761 seconds. Task governance reports
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance reports
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Scope passes all 8 admitted changed paths
and reports 44 exact excluded pre-existing paths; all 52 current paths are
classified with zero unclassified. The scope command's nonzero exit reflects
those declared exclusions, not an unclassified or unauthorized task write.
Task JSON, the bounded task-change privacy scan, predecessor hashes, retained
temporary-state checks, and `git diff --check` pass.

Because this fully specified low-risk task did not start a new alignment
journey, no native self-review completion is claimed. A separate bounded
current-Agent pass found the requirement result exact, Kernel and Adapter
source unchanged, the wheel built and installed from the verified source,
installed discovery consistent with the expected 6/8 inventory, and every
working-tree path classified. It also found one disclosed temporary probe
quoting error before installed code execution. Network use stayed at the one
admitted dependency download, while consumer, model, completion, cleanup, and
Git authority remained unused. This advisory pass is not independent assurance
and leaves downstream consumer and completion behavior unknown.
