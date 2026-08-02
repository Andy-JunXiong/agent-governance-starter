import json
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.git_snapshot import (
    GIT_SNAPSHOT_FORMAT,
    capture_git_snapshot,
    explain_snapshot_difference,
    snapshot_to_payload,
)


def run_git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("ascii", errors="replace").strip()


def write(repository: Path, relative: str, content: str) -> Path:
    path = repository.joinpath(*relative.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def create_repository(parent: Path) -> tuple[Path, str]:
    repository = parent / "repository"
    repository.mkdir()
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.email", "fixture@example.invalid")
    run_git(repository, "config", "user.name", "Fixture Author")
    write(repository, ".gitignore", ".cache/\n")
    write(repository, "src/app.py", "VALUE = 1\n")
    write(repository, "src/old.py", "OLD = True\n")
    run_git(repository, "add", ".")
    run_git(repository, "commit", "--quiet", "-m", "baseline")
    return repository, run_git(repository, "rev-parse", "HEAD")


@unittest.skipUnless(shutil.which("git"), "Git is required for snapshot fixtures")
class GitSnapshotTests(unittest.TestCase):
    def test_snapshot_is_deterministic_and_covers_all_git_layers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, base = create_repository(Path(temp_dir))
            write(repository, "src/committed.py", "COMMITTED = True\n")
            run_git(repository, "add", "src/committed.py")
            run_git(repository, "commit", "--quiet", "-m", "task commit")
            write(repository, "src/staged.py", "STAGED = True\n")
            run_git(repository, "add", "src/staged.py")
            write(repository, "src/app.py", "VALUE = 2\n")
            write(repository, "src/untracked.py", "UNTRACKED = True\n")
            run_git(repository, "mv", "src/old.py", "src/renamed.py")
            before_status = run_git(repository, "status", "--porcelain=v1")

            first = capture_git_snapshot(repository, comparison_base=base)
            second = capture_git_snapshot(repository, comparison_base=base)
            after_status = run_git(repository, "status", "--porcelain=v1")

        self.assertEqual(first, second)
        self.assertEqual(before_status, after_status)
        self.assertEqual(first.format_version, GIT_SNAPSHOT_FORMAT)
        layers = {layer.name: layer for layer in first.layers}
        self.assertTrue(layers["committed"].changes)
        self.assertTrue(layers["staged"].changes)
        self.assertTrue(layers["unstaged"].changes)
        self.assertTrue(layers["untracked"].changes)
        self.assertTrue(any(change.status == "renamed" for change in layers["staged"].changes))

    def test_local_agentgov_and_ignored_outputs_are_excluded_but_tracked_state_is_not(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, base = create_repository(Path(temp_dir))
            initial = capture_git_snapshot(repository, comparison_base=base)
            write(repository, ".agentgov/events/local.json", "local event\n")
            write(repository, ".cache/output.txt", "ignored\n")

            excluded = capture_git_snapshot(repository, comparison_base=base)

            write(repository, ".agentgov/tracked.txt", "tracked baseline\n")
            run_git(repository, "add", "-f", ".agentgov/tracked.txt")
            run_git(repository, "commit", "--quiet", "-m", "track governance fixture")
            tracked_base = run_git(repository, "rev-parse", "HEAD")
            write(repository, ".agentgov/tracked.txt", "tracked changed\n")
            included = capture_git_snapshot(repository, comparison_base=tracked_base)

        self.assertEqual(initial.change_set_digest, excluded.change_set_digest)
        self.assertNotEqual(excluded.change_set_digest, included.change_set_digest)
        self.assertIn(".agentgov/tracked.txt", json.dumps(snapshot_to_payload(included)))
        self.assertNotIn("local event", json.dumps(snapshot_to_payload(excluded)))

    def test_difference_explains_head_gitignore_and_untracked_changes_without_content(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository, base = create_repository(Path(temp_dir))
            before = capture_git_snapshot(repository, comparison_base=base)
            write(repository, ".gitignore", ".cache/\nbuild/\n")
            write(repository, "generated.txt", "password=must-not-appear\n")
            after = capture_git_snapshot(repository, comparison_base=base)
            serialized = json.dumps(snapshot_to_payload(after), sort_keys=True)

        reasons = explain_snapshot_difference(before, after)
        self.assertTrue(any("unstaged" in reason and ".gitignore" in reason for reason in reasons))
        self.assertTrue(any("untracked" in reason and "generated.txt" in reason for reason in reasons))
        self.assertNotIn("must-not-appear", serialized)


if __name__ == "__main__":
    unittest.main()
