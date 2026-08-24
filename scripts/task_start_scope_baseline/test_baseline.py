from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
for candidate in (str(REPOSITORY_ROOT), str(SOURCE_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from agentgov.git_snapshot import (  # noqa: E402
    CanonicalGitSnapshot,
    SnapshotChange,
    SnapshotLayer,
)
from scripts.task_start_scope_baseline import baseline  # noqa: E402


SHA_A = "a" * 40
SHA_B = "b" * 40


def digest(character: str) -> str:
    return "sha256:" + character * 64


def identity(
    layer: str,
    status: str,
    path: str,
    character: str,
    *,
    old_path: str | None = None,
    kind: str | None = None,
) -> baseline.PathIdentity:
    return baseline.PathIdentity(
        layer=layer,
        status=status,
        path=path,
        old_path=old_path,
        identity_digest=digest(character),
        identity_kind=kind or ("file" if layer == "untracked" else "patch"),
    )


def layers(*changes: baseline.PathIdentity) -> tuple[baseline.IdentityLayer, ...]:
    grouped = {name: [] for name in baseline._LAYERS}
    for change in changes:
        grouped[change.layer].append(change)
    return tuple(
        baseline.IdentityLayer(
            name=name,
            changes=tuple(sorted(grouped[name], key=baseline._identity_sort_key)),
        )
        for name in baseline._LAYERS
    )


def state(
    *changes: baseline.PathIdentity,
    head: str = SHA_A,
    change_set: str = digest("1"),
) -> baseline.CapturedState:
    return baseline.CapturedState(
        comparison_base_sha=SHA_A,
        snapshot_head_sha=head,
        snapshot_change_set_digest=change_set,
        layers=layers(*changes),
        exclusions=baseline._SNAPSHOT_EXCLUSIONS,
    )


def make_baseline(
    *changes: baseline.PathIdentity,
    includes: tuple[str, ...] = ("allowed",),
    excludes: tuple[str, ...] = ("legacy",),
) -> baseline.TaskStartBaseline:
    value = baseline.TaskStartBaseline(
        contract=baseline.BASELINE_CONTRACT,
        schema_version=baseline.BASELINE_SCHEMA_VERSION,
        task=baseline.TaskBinding(
            "governance/tasks/example.json", "example", digest("2")
        ),
        comparison_base_sha=SHA_A,
        snapshot_head_sha=SHA_A,
        snapshot_change_set_digest=digest("1"),
        scope=baseline.ScopeBinding(tuple(sorted(includes)), tuple(sorted(excludes))),
        layers=layers(*changes),
        exclusions=baseline._SNAPSHOT_EXCLUSIONS,
        capture_claim=baseline.CAPTURE_CLAIM,
        baseline_digest="",
    )
    return replace(value, baseline_digest=baseline._baseline_digest(value))


def task_binding(*, digest_value: str = digest("2")) -> baseline.TaskBinding:
    return baseline.TaskBinding(
        "governance/tasks/example.json", "example", digest_value
    )


def task_document(
    *,
    includes: list[str] | None = None,
    excludes: list[str] | None = None,
) -> dict[str, object]:
    return {
        "acceptance_signals": ["The fixture boundary is deterministic."],
        "contract": "agentgov.development-task",
        "decision": {
            "decided_by": "Human product owner",
            "rationale": "The human admitted the exact fixture task for testing.",
            "state": "admitted",
        },
        "owner": "Human product owner",
        "profile": "compact",
        "requirement": {"source_refs": [], "summary": "Exercise a fixture task boundary safely."},
        "risk": {"items": [], "level": "low"},
        "schema_version": "1.1",
        "scope": {
            "exclude_paths": excludes or ["legacy"],
            "include_paths": includes or ["allowed", "governance/tasks/example.json"],
        },
        "task_id": "example",
        "title": "Example fixture task",
        "validation_commands": ["fixture validation"],
    }


class BaselineComparisonTests(unittest.TestCase):
    def test_preserves_unchanged_excluded_and_allows_included_delta(self) -> None:
        legacy = identity("unstaged", "modified", "legacy/old.py", "a")
        added = identity("untracked", "untracked", "allowed/new.py", "b")
        report = baseline.compare_task_start_baseline(
            make_baseline(legacy),
            state(legacy, added),
            current_task=task_binding(),
        )
        self.assertFalse(report.has_failures)
        statuses = {item.status for item in report.findings}
        self.assertIn(baseline.FindingStatus.PRESERVED, statuses)
        self.assertIn(baseline.FindingStatus.PASS, statuses)

    def test_changed_or_removed_excluded_identity_fails_closed(self) -> None:
        before = identity("staged", "modified", "legacy/config.py", "a")
        after = identity("staged", "modified", "legacy/config.py", "b")
        changed = baseline.compare_task_start_baseline(
            make_baseline(before), state(after), current_task=task_binding()
        )
        removed = baseline.compare_task_start_baseline(
            make_baseline(before), state(), current_task=task_binding()
        )
        self.assertTrue(changed.has_failures)
        self.assertTrue(removed.has_failures)
        self.assertTrue(any("pre-existing excluded" in item.message for item in changed.findings))

    def test_new_excluded_and_unclassified_paths_fail(self) -> None:
        report = baseline.compare_task_start_baseline(
            make_baseline(),
            state(
                identity("untracked", "untracked", "legacy/new.txt", "a"),
                identity("unstaged", "modified", "outside.txt", "b"),
            ),
            current_task=task_binding(),
        )
        self.assertEqual(2, sum(item.status is baseline.FindingStatus.FAIL for item in report.findings))

    def test_rename_and_copy_require_both_endpoints_to_be_admitted(self) -> None:
        rename = identity(
            "staged",
            "renamed",
            "allowed/new.py",
            "a",
            old_path="legacy/old.py",
        )
        copied = identity(
            "committed",
            "copied",
            "allowed/copy.py",
            "b",
            old_path="allowed/source.py",
        )
        report = baseline.compare_task_start_baseline(
            make_baseline(), state(rename, copied), current_task=task_binding()
        )
        findings = {item.path: item.status for item in report.findings}
        self.assertIs(baseline.FindingStatus.FAIL, findings["allowed/new.py"])
        self.assertIs(baseline.FindingStatus.PASS, findings["allowed/copy.py"])

    def test_staged_unstaged_and_untracked_predecessors_are_separate(self) -> None:
        changes = (
            identity("staged", "modified", "legacy/both.py", "a"),
            identity("unstaged", "modified", "legacy/both.py", "b"),
            identity("untracked", "untracked", "legacy/new.txt", "c"),
        )
        report = baseline.compare_task_start_baseline(
            make_baseline(*changes), state(*changes), current_task=task_binding()
        )
        self.assertEqual(3, sum(item.status is baseline.FindingStatus.PRESERVED for item in report.findings))
        self.assertFalse(report.has_failures)

    def test_task_digest_and_head_drift_are_distinct_failures(self) -> None:
        report = baseline.compare_task_start_baseline(
            make_baseline(),
            state(head=SHA_B),
            current_task=task_binding(digest_value=digest("3")),
        )
        ids = {item.check_id for item in report.findings if item.status is baseline.FindingStatus.FAIL}
        self.assertEqual({"binding:task-digest", "binding:head"}, ids)

    def test_deletion_inside_include_scope_is_allowed(self) -> None:
        deleted = identity("unstaged", "deleted", "allowed/old.py", "a")
        report = baseline.compare_task_start_baseline(
            make_baseline(), state(deleted), current_task=task_binding()
        )
        self.assertFalse(report.has_failures)
        self.assertIs(baseline.FindingStatus.PASS, report.findings[0].status)


class BaselinePersistenceTests(unittest.TestCase):
    def test_round_trip_is_strict_and_contains_no_raw_patch(self) -> None:
        value = make_baseline(identity("unstaged", "modified", "allowed/file.py", "a"))
        payload = baseline.baseline_to_payload(value)
        loaded = baseline.baseline_from_payload(payload)
        self.assertEqual(value, loaded)
        rendered = json.dumps(payload)
        self.assertNotIn("diff --git", rendered)
        self.assertNotIn(str(REPOSITORY_ROOT), rendered)

    def test_malformed_digest_and_unsafe_path_are_rejected(self) -> None:
        payload = baseline.baseline_to_payload(make_baseline())
        payload["baseline_digest"] = digest("3")
        with self.assertRaisesRegex(baseline.BaselineError, "digest does not match"):
            baseline.baseline_from_payload(payload)

        payload = baseline.baseline_to_payload(make_baseline())
        payload["task"]["path"] = "../outside.json"
        with self.assertRaisesRegex(baseline.BaselineError, "parent traversal"):
            baseline.baseline_from_payload(payload)

    def test_write_is_exclusive_and_load_requires_existing_local_file(self) -> None:
        with tempfile.TemporaryDirectory(prefix="baseline-persist-") as directory:
            root = Path(directory)
            value = make_baseline()
            relative = ".agentgov/scope-baselines/example.json"
            baseline.write_baseline(value, repository=root, output_path=relative)
            self.assertEqual(value, baseline.load_baseline(repository=root, baseline_path=relative))
            with self.assertRaisesRegex(baseline.BaselineError, "overwrite is forbidden"):
                baseline.write_baseline(value, repository=root, output_path=relative)
            with self.assertRaisesRegex(baseline.BaselineError, "existing regular file"):
                baseline.load_baseline(
                    repository=root,
                    baseline_path=".agentgov/scope-baselines/missing.json",
                )

    def test_paths_outside_local_baseline_directory_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="baseline-path-") as directory:
            with self.assertRaisesRegex(baseline.BaselineError, "must be beneath"):
                baseline.write_baseline(
                    make_baseline(),
                    repository=Path(directory),
                    output_path="docs/baseline.json",
                )

    def test_symlink_baseline_target_is_rejected_when_supported(self) -> None:
        with tempfile.TemporaryDirectory(prefix="baseline-link-") as directory:
            root = Path(directory)
            parent = root / ".agentgov" / "scope-baselines"
            parent.mkdir(parents=True)
            target = parent / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = parent / "link.json"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symbolic links are unavailable on this host")
            with self.assertRaisesRegex(baseline.BaselineError, "symbolic link"):
                baseline.load_baseline(
                    repository=root,
                    baseline_path=".agentgov/scope-baselines/link.json",
                )


class BaselineCaptureTests(unittest.TestCase):
    def _write_task(self, root: Path, **kwargs: object) -> str:
        relative = "governance/tasks/example.json"
        path = root / "governance" / "tasks" / "example.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(task_document(**kwargs)), encoding="utf-8")
        return relative

    def _snapshot(self, *, change_set: str = digest("1")) -> CanonicalGitSnapshot:
        committed = SnapshotChange("committed", "modified", "allowed/committed.py", None)
        staged = SnapshotChange("staged", "modified", "legacy/staged.py", None)
        unstaged = SnapshotChange("unstaged", "modified", "allowed/unstaged.py", None)
        untracked = SnapshotChange(
            "untracked", "untracked", "allowed/new.txt", None, digest("e"), "file"
        )
        return CanonicalGitSnapshot(
            format_version="agentgov.git-change-set.v1",
            comparison_base_sha=SHA_A,
            snapshot_head_sha=SHA_A,
            change_set_digest=change_set,
            layers=(
                SnapshotLayer("committed", digest("a"), (committed,)),
                SnapshotLayer("staged", digest("b"), (staged,)),
                SnapshotLayer("unstaged", digest("c"), (unstaged,)),
                SnapshotLayer("untracked", digest("d"), (untracked,)),
            ),
            exclusions=baseline._SNAPSHOT_EXCLUSIONS,
        )

    def test_capture_binds_task_and_all_git_layers_without_raw_patch(self) -> None:
        with tempfile.TemporaryDirectory(prefix="baseline-capture-") as directory:
            root = Path(directory)
            task_path = self._write_task(root)
            snapshot = self._snapshot()
            private_patch = b"private source contents 7f39"
            with mock.patch.object(
                baseline, "capture_git_snapshot", side_effect=(snapshot, snapshot)
            ), mock.patch.object(
                baseline, "_run_git_identity", return_value=private_patch
            ):
                captured = baseline.capture_task_start_baseline(
                    root, task_path=task_path
                )
            self.assertEqual(baseline._LAYERS, tuple(item.name for item in captured.layers))
            self.assertEqual(4, len(baseline._all_identities(captured.layers)))
            self.assertNotIn(private_patch.decode(), json.dumps(baseline.baseline_to_payload(captured)))
            self.assertEqual(
                baseline.canonical_task_digest(task_document()), captured.task.digest
            )

    def test_unstable_capture_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="baseline-unstable-") as directory:
            root = Path(directory)
            task_path = self._write_task(root)
            with mock.patch.object(
                baseline,
                "capture_git_snapshot",
                side_effect=(self._snapshot(), self._snapshot(change_set=digest("2"))),
            ), mock.patch.object(baseline, "_run_git_identity", return_value=b"patch"):
                with self.assertRaisesRegex(baseline.BaselineError, "changed during capture"):
                    baseline.capture_task_start_baseline(root, task_path=task_path)

    def test_each_tracked_layer_uses_a_distinct_read_only_diff(self) -> None:
        snapshot = self._snapshot()
        committed = snapshot.layers[0].changes[0]
        staged = snapshot.layers[1].changes[0]
        unstaged = snapshot.layers[2].changes[0]
        committed_args = baseline._tracked_patch_arguments(snapshot, committed)
        staged_args = baseline._tracked_patch_arguments(snapshot, staged)
        unstaged_args = baseline._tracked_patch_arguments(snapshot, unstaged)
        self.assertIn(snapshot.comparison_base_sha, committed_args)
        self.assertIn(snapshot.snapshot_head_sha, committed_args)
        self.assertIn("--cached", staged_args)
        self.assertNotIn("--cached", unstaged_args)
        self.assertEqual("--", unstaged_args[-2])

    def test_capture_rejects_unclassified_current_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="baseline-unclassified-") as directory:
            root = Path(directory)
            task_path = self._write_task(root)
            snapshot = self._snapshot()
            unclassified = replace(
                snapshot,
                layers=(
                    replace(
                        snapshot.layers[0],
                        changes=(
                            SnapshotChange(
                                "committed", "modified", "outside.py", None
                            ),
                        ),
                    ),
                    *snapshot.layers[1:],
                ),
            )
            with mock.patch.object(
                baseline, "capture_git_snapshot", side_effect=(unclassified, unclassified)
            ), mock.patch.object(baseline, "_run_git_identity", return_value=b"patch"):
                with self.assertRaisesRegex(baseline.BaselineError, "unclassified"):
                    baseline.capture_task_start_baseline(root, task_path=task_path)

    def test_task_change_during_capture_fails_closed(self) -> None:
        binding_before = baseline.TaskBinding(
            "governance/tasks/example.json", "example", digest("a")
        )
        binding_after = replace(binding_before, digest=digest("b"))
        scope = baseline.ScopeBinding(("allowed",), ("legacy",))
        with tempfile.TemporaryDirectory(prefix="baseline-task-race-") as directory:
            root = Path(directory)
            with mock.patch.object(
                baseline,
                "_load_task_binding",
                side_effect=((binding_before, scope, {}), (binding_after, scope, {})),
            ), mock.patch.object(baseline, "_capture_state", return_value=state()):
                with self.assertRaisesRegex(baseline.BaselineError, "task record changed"):
                    baseline.capture_task_start_baseline(
                        root, task_path="governance/tasks/example.json"
                    )


if __name__ == "__main__":
    unittest.main()
