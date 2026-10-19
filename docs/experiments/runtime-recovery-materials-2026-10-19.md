# Runtime recovery materials - 2026-10-19

Task `p0-runtime-recovery-materials-reprepare-v1` prepares fresh recovery
material only. Outcome: `VERIFIED_RECOVERY_MATERIALS_PREPARED`.
Installation, process control, restoration execution and current-client
activation have not occurred.

## Evidence boundary and recovery locator

The reviewed 188-input source manifest still matches the admitted identities.
The original isolated installation, launcher and configuration match the
historical preparation checkpoint. The old temporary recovery root was not
located in accessible temporary locations; access-denied locations prevent a
claim that it was deleted or absent everywhere.

A fresh task-owned direct child of the operating-system temporary directory is
retained as **`agv-fa6298a1`**. This non-sensitive basename is the recovery
locator, not proof that the material will still exist later. Resolve it under
the operating-system temporary directory and verify `owner.json` names this
exact task and task digest before using any file. Do not substitute another
similarly named directory.

Private host paths and per-file recovery metadata stay inside that root.
Repository evidence contains only the basename, versions, hashes, counts and
bounded observations. The original runtime contains 272 files, totaling
4,673,348 bytes, with no detected link or reparse entry. Its file set and
per-file hashes matched before copying, after copying and after the build.
The backup copy, exposed launcher copy and pipx metadata were rechecked.
This establishes byte preservation; an actual restore has not been exercised.

## Normalized preparation result

```json
{
  "background_installer_created": false,
  "backup_bytes": 4673348,
  "backup_file_count": 272,
  "backup_manifest_digest": "sha256:a185375fef77659343d2961b0f32fbda43e149949bd1a09cbeabb88e6e2a5d31",
  "backup_restore_execution_verified": false,
  "backup_verified": true,
  "build_wheels": [
    {
      "bytes": 129956,
      "filename": "packaging-26.3-py3-none-any.whl",
      "sha256": "d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c"
    },
    {
      "bytes": 818216,
      "filename": "setuptools-84.0.0-py3-none-any.whl",
      "sha256": "51a52592b3b99e102b609654876bd65f19f999935166d1352678931132b0c670"
    },
    {
      "bytes": 33320,
      "filename": "wheel-0.48.0-py3-none-any.whl",
      "sha256": "3217dcc807155e45db462d7ef2431f5ddda0d7273b700d05a67b271ceb1287ab"
    }
  ],
  "client_activation_verified": false,
  "configuration_preserved": true,
  "configuration_sha256": "4cca2d57edeaddfe52d3e6c4dd4d774192bbdbcab4e84e07df73e14a861c0348",
  "installation_performed": false,
  "installed_adapter_sha256": "d3ff1956c6a80f4f01f08dae2cbf203da61f021fdf5980a05c9667be0722d00b",
  "launcher_preserved": true,
  "launcher_sha256": "7dada88a8ccff3dfa40dd52783719e5aced5b293202979ba3d5b75f027b498e7",
  "live_installation_preserved": true,
  "outcome": "VERIFIED_RECOVERY_MATERIALS_PREPARED",
  "package_modules_verified": 78,
  "package_version": "0.3.0rc1",
  "pipx_metadata_sha256": "cdd7b0e8acc1a5500b573df34b6ae85e7bb033af3dea78c3efa6d939a1ce80ce",
  "prepared_adapter_version": "1.7.0",
  "process_control_performed": false,
  "protocol_version": "2026-07-28",
  "recovery_manifest_sha256": "5d3b050f83f665c2ff26409a36a9082b4bd9cd14626ea49b4bf41e326f7f40ed",
  "runtime_dependencies": [],
  "shared_data_files_verified": 107,
  "source_content_digest": "sha256:f222e756b70a8f57ae5ef49db95b257729ad515cdf8066400ab67bf483fb8162",
  "source_input_count": 188,
  "source_path_digest": "sha256:23a850bd924f45a8888fcfe7cbc591ed1edfb30c1735810d60a5833bc210fb54",
  "staged_input_count": 188,
  "stages": [
    {
      "exit_code": 0,
      "stage": "create_build_environment",
      "stderr_bytes": 0,
      "stdout_bytes": 0
    },
    {
      "exit_code": 0,
      "stage": "install_pinned_build_wheels_offline",
      "stderr_bytes": 0,
      "stdout_bytes": 598
    },
    {
      "exit_code": 0,
      "stage": "build_exact_project_offline",
      "stderr_bytes": 0,
      "stdout_bytes": 822
    }
  ],
  "task_id": "p0-runtime-recovery-materials-reprepare-v1",
  "temporary_material_retained": true,
  "temporary_root_basename": "agv-fa6298a1",
  "wheel": {
    "bytes": 543036,
    "filename": "agent_governance_starter-0.3.0rc1-py3-none-any.whl",
    "sha256": "35f6914712616edc84728f5b2b12c1851d6e72c688e765d1b170ca52289fb9aa"
  }
}
```

The backup manifest digest above hashes the relative-file mapping with
SHA-256 over UTF-8 JSON using sorted keys and compact separators. Each mapping
value contains `bytes` and `sha256`. The separate recovery-manifest digest
binds the exact private manifest file. A changed archive hash relative to the
September build does not imply changed payloads: all expected modules and
shared data were compared directly with this staging snapshot.

Only the three historically pinned public build wheels were downloaded,
into this root, and their exact hashes were verified. The isolated build
environment then installed those wheels without an index or dependencies.
Project build used no index, dependency installation or build isolation.
User pip configuration and credentialed indexes were not used.

## Retained material layout

| Relative location | Purpose |
| --- | --- |
| `owner.json` | Exact task identity, local target locators and root contract |
| `backup/environment/` | Byte-verified original isolated environment, including pipx metadata |
| `backup/agentgov.exe` | Byte-verified original exposed launcher |
| `recovery-manifest.json` | Private original file set, per-file hashes and control-file hashes |
| `stage/` and `source-hashes.json` | Reviewed source snapshot and its per-file identities |
| `tools/` and `build-env/` | Hash-pinned build wheels and isolated tooling |
| `wheel/` | Verified local-only candidate wheel |
| `result.json` | Normalized preparation result |
| `prepare.py` and stage logs | Local preparation evidence; not an installer and not an idempotent rerun entry point |

No retained script installs into the live environment, stops a process or
waits for a future disconnect. There is no background or delayed installer.
Do not rerun `prepare.py`: exclusive copy destinations intentionally reject
reuse. Further preparation requires its own reviewed execution context.

## Foreground maintenance handoff (not executed)

1. Review the completed preparation and establish the exact applicable
   installation task, recovery-material identity and host permissions. This
   preparation task does not authorize replacement or process control. The
   earlier installation record must not silently acquire this task's new
   recovery baseline.
2. Before disconnecting anything, independently re-read the owner/task
   binding, source manifest, candidate wheel hash, full backup manifest and
   launcher hashes. Confirm that the original live file set, pipx metadata,
   launcher and project configuration still match the recovery snapshot.
   Stop on any difference or missing material.
3. Choose a bounded foreground maintenance context that can remain open
   while the target MCP connection is disconnected. Identify which sessions
   share the installed environment. Do not close unrelated Codex sessions.
   Restarting this project normally can reconnect the old MCP runtime.
   This handoff grants no authority to change persistent configuration or
   terminate processes; agree on the exact disconnect operation separately.
4. Immediately before replacement, obtain a fresh zero-process observation
   covering executable paths and arguments for both the isolated environment
   and exposed launcher. If any target process remains, stop. Do not use a
   background watcher, scheduled installer or delayed write.
5. At that verified boundary, the later admitted operation may install only
   the hash-verified local wheel into the exact existing isolated environment
   using `--force-reinstall --no-deps --no-index`. Preserve configuration,
   tool allowlist and pipx metadata. Refresh the exposed launcher only if the
   later task explicitly allows it and its verified inner counterpart
   requires that refresh.
6. Verify every installed package module and shared data file against the
   exact staged snapshot, package identity `0.3.0rc1`, Adapter `1.7.0`,
   protocol `2026-07-28`, and empty runtime dependencies. Then perform
   bounded no-model fresh-process initialization, discovery and exploration
   rejection/correction checks. These are separate from current-client
   activation.
7. If replacement or checks fail, restore only this verified original
   snapshot at a fresh safe zero-process boundary, and recheck the original
   file set and launcher. If safe restoration cannot be proved, stop and
   retain material; do not improvise destructive cleanup.
8. Reconnect the intended client and establish activation separately.
   Retain recovery materials until activation and durable evidence are
   complete. Any eventual cleanup must verify the exact absolute resolved
   target remains the task-owned temporary child; no cleanup is performed
   by this preparation task.

## Validation and limits

Task-declared repository validation and the distinct native advisory review
are recorded in the dated development log. Preparation does not prove
installation success, rollback execution, live-client activation, correction
of the host's missing approval controls, broad product benefit or acceptance.
The next feature remains undecided; this handoff is review input only.

## End-of-day retention checkpoint

The original preparation evidence above remains valid as a historical
checkpoint. The human paused further development on 2026-10-19. Recovery
child `agv-fa6298a1` remains retained; no live installation or restore was
performed. See `runtime-foreground-install-2026-10-19.md` for the stopped
maintenance attempt, corrected helper and unresolved review boundary.
Fresh verification remains mandatory before any later use.
