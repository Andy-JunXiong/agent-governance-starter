# Isolated exploration package verification - 2026-09-22

## Scope and result

Task `p0-exploration-isolated-package-verification-v1` was admitted through
native proposal review and separately started after human `REPLACE`. The
human selected an isolated consumer and permitted necessary build-tool
downloads. The current installed Adapter and client configuration remain
unchanged. This is local synthetic protocol evidence, not a client restart,
model session, automatic tool-selection proof, release, or human acceptance.

Outcome: `BUILD_AND_INSTALL_PASSED` and `PROTOCOL_PASSED`.

## Input identity and historical manifest gap

The existing distribution manifest failed read-only comparison: it omits
`src/agentgov/scope_observation.py`, and its path/content digests are stale.
This result is preserved. The task used the repository's independent
`derive_distribution_inputs` implementation to derive a separate exact
188-path snapshot from current packaging configuration. This does not repair
or validate the historical manifest. Staging copied only those inputs and
verified every copied byte. All 78 package modules and 107 data payloads
matched both the wheel and the installed temporary consumer.

## Execution boundaries

Only necessary binary build-tool packages were downloaded from public PyPI:
setuptools, wheel, and wheel's packaging dependency. Pip configuration and
credentialed indexes were excluded from the subprocess environment. The
project wheel build and consumer installation used no index and no dependency
resolution. Temporary source, tools, installation, and subprocess temporary
files stayed beneath one verified task-owned short root.

The installed CLI ran locally in one bounded STDIO process. Its eight
requests covered initialize, catalog inspection, invalid start, corrected
start, exploratory start, invalid inherited update, corrected update, and a
synthetic exploration selection. The selection is a test fixture only.
Source inputs and 73 original installed-module/configuration hashes were
unchanged. Protocol output was bounded to 1 MiB overall and 256 KiB per line,
with 10-second response and exit limits. No raw protocol payload is retained
here. The process exited normally and emitted no stderr.

## Normalized evidence

```json
{
  "source_input_count": 188,
  "source_path_digest": "sha256:23a850bd924f45a8888fcfe7cbc591ed1edfb30c1735810d60a5833bc210fb54",
  "source_content_digest": "sha256:f222e756b70a8f57ae5ef49db95b257729ad515cdf8066400ab67bf483fb8162",
  "temporary_root_boundary": {
    "contract": "agentgov.short-build-root",
    "schema_version": "1.0",
    "root_name_pattern": "agv-<8-hex>",
    "root_is_direct_temporary_child": true,
    "projected_path_limit": 240,
    "longest_projected_length": 110,
    "authority_boundary": {
      "builds_artifact": false,
      "selects_artifact": false,
      "uses_network": false,
      "authorizes_git_operations": false,
      "authorizes_publication": false,
      "authorizes_release": false,
      "authorizes_deployment": false,
      "authorizes_external_write": false
    }
  },
  "build": {
    "stages": [
      {
        "stage": "create_build_environment",
        "exit_code": 0,
        "stdout_bytes": 0,
        "stderr_bytes": 0
      },
      {
        "stage": "download_build_wheels",
        "exit_code": 0,
        "stdout_bytes": 928,
        "stderr_bytes": 0
      },
      {
        "stage": "install_build_wheels_offline",
        "exit_code": 0,
        "stdout_bytes": 683,
        "stderr_bytes": 0
      },
      {
        "stage": "read_build_versions",
        "exit_code": 0,
        "stdout_bytes": 80,
        "stderr_bytes": 0
      },
      {
        "stage": "build_project_offline",
        "exit_code": 0,
        "stdout_bytes": 818,
        "stderr_bytes": 0
      },
      {
        "stage": "create_consumer_environment",
        "exit_code": 0,
        "stdout_bytes": 0,
        "stderr_bytes": 0
      },
      {
        "stage": "install_project_offline",
        "exit_code": 0,
        "stdout_bytes": 227,
        "stderr_bytes": 0
      }
    ],
    "build_wheels": [
      {
        "filename": "packaging-26.3-py3-none-any.whl",
        "sha256": "d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c",
        "bytes": 129956
      },
      {
        "filename": "setuptools-84.0.0-py3-none-any.whl",
        "sha256": "51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670",
        "bytes": 818216
      },
      {
        "filename": "wheel-0.48.0-py3-none-any.whl",
        "sha256": "3217dcc807155e45db462d7ef2431f5ddda0d7273b700d05a67b271ceb1287ab",
        "bytes": 33320
      }
    ],
    "tool_versions": {
      "python": "3.11.9",
      "setuptools": "84.0.0",
      "wheel": "0.48.0",
      "pip": "24.0"
    },
    "copied_inputs": 188,
    "project_wheel": {
      "filename": "agent_governance_starter-0.3.0rc1-py3-none-any.whl",
      "sha256": "537f185790e78b1bd5c83f17f5c2574cb5a35769442ad31be0b3fd2b702ddd5a",
      "bytes": 543036
    },
    "package_payloads_verified": 78,
    "data_payloads_verified": 107,
    "outcome": "BUILD_AND_INSTALL_PASSED",
    "source_preserved": true,
    "installed_and_config_preserved": true,
    "elapsed_seconds": 27.1
  },
  "protocol": {
    "checks": [
      "adapter_identity",
      "schema_rejects_unusable_option",
      "invalid_start_rejected",
      "invalid_start_rejected_diagnostic",
      "corrected_start_same_process",
      "inherited_update_rejected",
      "inherited_update_rejected_diagnostic",
      "atomic_update_retry",
      "valid_exploration",
      "authority_preserved",
      "clean_process_exit",
      "stderr_empty",
      "existing_install_and_config_unchanged",
      "source_snapshot_unchanged"
    ],
    "synthetic_fixture_choices": true,
    "model_sessions": 0,
    "client_restart": false,
    "adapter_version": "1.7.0",
    "outcome": "PROTOCOL_PASSED",
    "request_count": 8,
    "stdout_bytes": 57706,
    "stderr_bytes": 0,
    "elapsed_seconds": 0.3
  },
  "probe_sha256": {
    "build_probe.py": "67342f18ef4550faeb199de935ec201c21ba6d6915c7adc7c8208fbbf0584722",
    "protocol_probe.py": "21afd90424c9cc3d42b4af2272f60b3aa4f1e23908b3ea641e391a0b1e021367"
  }
}
```

## Limits and cleanup

The download provenance and recorded hashes establish the observed inputs,
not independent supply-chain assurance. One successful local protocol run
does not establish repeatability, production reliability, real-client form
behavior, time savings, or adoption benefit. Current runtime activation
remains unverified. The current local wheel is not a published release.

Cleanup is pending evidence-receipt verification; only the exact task-owned
temporary root may be removed. Repository source and the existing installation
must be preserved.

### Completed cleanup

The pending cleanup statement above is superseded. The exact task-owned
short root was removed after verifying durable evidence identity `sha256:dfdede4f6475d96c93839e8b62bacbb04d15d5d1ba6865be4a47dbe3747a596b`.
The root no longer exists. Original installation/configuration and source
hashes were verified again before cleanup; no broader path was removed.
