import contextlib
import io
import json
import shutil
import subprocess
import sys
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.cli import EXIT_PASS, main
from agentgov.development_event_export import (
    EXPORT_CONTRACT,
    DevelopmentExportPolicyError,
    build_development_event_export,
    development_export_default_output,
    load_development_event_export,
    render_development_event_export_preview,
    request_development_export_confirmation,
    write_development_event_export,
)
from agentgov.event_store import append_governance_event


ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = "2026-08-03T01:02:03.000Z"


class InteractiveInput(io.StringIO):
    def isatty(self) -> bool:
        return True


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


def run_git(repository: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", "-C", str(repository), *args),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", errors="replace"))
    return completed.stdout.decode("utf-8", errors="replace").strip()


def create_repository(parent: Path) -> Path:
    repository = parent / "repository"
    repository.mkdir()
    run_git(repository, "init", "--quiet")
    run_git(repository, "config", "user.email", "fixture@example.invalid")
    run_git(repository, "config", "user.name", "Fixture Author")
    (repository / "README.md").write_text("# Fixture\n", encoding="utf-8")
    run_git(repository, "add", "README.md")
    run_git(repository, "commit", "--quiet", "-m", "baseline")
    return repository


def add_event(repository: Path, *, actor: str = "coding_agent", index: int = 1) -> None:
    append_governance_event(
        repository,
        event_type="scope.checked",
        actor_class=actor,
        actor_label="private-agent-label",
        task_id="fixture-task",
        task_digest="sha256:" + "a" * 64,
        outcome="passed",
        evidence_ref=".agentgov/evidence/evd-" + "b" * 32 + ".json",
        governance_refs=("AGENTS.md", "docs/adr/INVARIANTS.md"),
        reason_codes=("explicit_check_requested",),
        metrics={"changes": index, "failures": 0},
        occurred_at=f"2026-08-03T01:02:0{index}.000Z",
        event_id="evt-" + str(index) * 32,
    )


@unittest.skipUnless(shutil.which("git"), "Git is required for export fixtures")
class DevelopmentEventExportTests(unittest.TestCase):
    def test_build_redacts_free_text_and_local_evidence_but_retains_governance_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(repository)

            bundle = build_development_event_export(repository, created_at=FIXED_TIME)
            preview = render_development_event_export_preview(
                bundle,
                output=development_export_default_output(bundle),
            )
            payload = asdict(bundle)

        self.assertEqual(bundle.contract, EXPORT_CONTRACT)
        self.assertEqual(bundle.source["event_count"], 1)
        self.assertEqual(bundle.redaction["actor_labels_removed"], 1)
        self.assertEqual(bundle.redaction["evidence_refs_removed"], 1)
        self.assertEqual(payload["events"][0]["actor"], {"class": "coding_agent"})
        self.assertIsNone(payload["events"][0]["evidence_ref"])
        self.assertEqual(payload["events"][0]["governance_refs"], ["AGENTS.md", "docs/adr/INVARIANTS.md"])
        self.assertNotIn("private-agent-label", json.dumps(payload))
        self.assertIn("EXCLUDED actor labels", preview)
        self.assertTrue(all(value is False for value in bundle.authority_boundary.values()))

    def test_handoff_is_exported_as_redacted_version_1_2_metadata(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(repository)
            append_governance_event(
                repository,
                event_type="session.handed_off",
                actor_class="human",
                actor_label="private-human-label",
                task_id="fixture-task",
                task_digest="sha256:" + "a" * 64,
                outcome="handed_off",
                evidence_ref=".agentgov/evidence/evd-" + "b" * 32 + ".json",
                reason_codes=("handoff_confirmed", "verified_evidence_fresh"),
                occurred_at="2026-08-03T01:02:09.000Z",
                event_id="evt-" + "9" * 32,
            )

            bundle = build_development_event_export(repository, created_at=FIXED_TIME)

        handoff = bundle.events[-1]
        self.assertEqual(handoff["schema_version"], "1.2")
        self.assertEqual(handoff["event_type"], "session.handed_off")
        self.assertEqual(handoff["outcome"], "handed_off")
        self.assertEqual(handoff["actor"], {"class": "human"})
        self.assertIsNone(handoff["evidence_ref"])

    def test_write_and_load_are_repository_local_immutable_and_integrity_checked(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(repository)
            bundle = build_development_event_export(repository, created_at=FIXED_TIME)
            output = development_export_default_output(bundle)

            written = write_development_event_export(repository, bundle=bundle, output=output)
            loaded = load_development_event_export(repository, output)
            with self.assertRaises(DevelopmentExportPolicyError):
                write_development_event_export(repository, bundle=bundle, output=output)
            with self.assertRaises(DevelopmentExportPolicyError):
                write_development_event_export(
                    repository,
                    bundle=bundle,
                    output=Path("..") / "outside.json",
                )
            with patch("agentgov.development_event_export._is_tracked", return_value=False):
                with patch("agentgov.development_event_export.os.open", side_effect=FileExistsError):
                    with self.assertRaises(DevelopmentExportPolicyError):
                        write_development_event_export(
                            repository,
                            bundle=bundle,
                            output=Path(".agentgov/exports/race.json"),
                        )
            payload = json.loads(written.read_text(encoding="utf-8"))
            payload["events"][0]["metrics"]["changes"] = 999
            written.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(DevelopmentExportPolicyError):
                load_development_event_export(repository, output)

        self.assertEqual(loaded.export_id, bundle.export_id)

    def test_empty_ci_and_oversized_metadata_fail_closed(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            (repository / ".agentgov/events").mkdir(parents=True)
            with self.assertRaises(DevelopmentExportPolicyError):
                build_development_event_export(repository)

        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(repository, actor="ci")
            with self.assertRaises(DevelopmentExportPolicyError):
                build_development_event_export(repository)

    def test_confirmation_requires_exact_word_and_interactive_terminal(self) -> None:
        self.assertFalse(request_development_export_confirmation(
            decision_reader=lambda _: "EXPORT",
            is_interactive_terminal=False,
        ))
        self.assertFalse(request_development_export_confirmation(
            decision_reader=lambda _: "export",
            is_interactive_terminal=True,
        ))
        self.assertTrue(request_development_export_confirmation(
            decision_reader=lambda _: "EXPORT",
            is_interactive_terminal=True,
        ))

    def test_export_schema_declares_strict_redaction_and_denied_authority(self) -> None:
        schema = json.loads(
            (ROOT / "schemas/development-event-export.schema.json").read_text(encoding="utf-8")
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["contract"]["const"], EXPORT_CONTRACT)
        redaction = schema["properties"]["redaction"]["properties"]
        self.assertTrue(all(redaction[field]["const"] is False for field in (
            "source_content_included",
            "validation_output_included",
            "absolute_paths_included",
            "credentials_included",
        )))

    def test_cli_dry_run_writes_nothing_and_exact_confirmation_creates_export(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = create_repository(Path(temp_dir))
            add_event(repository)

            code, stdout, stderr = run_cli(
                "export", "development", "--repository", str(repository), "--dry-run"
            )
            self.assertEqual(list((repository / ".agentgov").glob("exports/*.json")), [])
            with patch.object(sys, "stdin", InteractiveInput("EXPORT\n")):
                confirmed_code, confirmed_stdout, confirmed_stderr = run_cli(
                    "export", "development", "--repository", str(repository)
                )
            exports = list((repository / ".agentgov/exports").glob("exp-*.json"))

        self.assertEqual(code, EXIT_PASS)
        self.assertEqual(stderr, "")
        self.assertIn("DEVELOPMENT EVENT EXPORT PREVIEW", stdout)
        self.assertEqual(confirmed_code, EXIT_PASS)
        self.assertEqual(confirmed_stderr, "")
        self.assertIn("PASS export development", confirmed_stdout)
        self.assertEqual(len(exports), 1)


if __name__ == "__main__":
    unittest.main()
