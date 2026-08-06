import contextlib
import io
import json
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.admission_routing import (
    ADMISSION_ROUTE_CONTRACT,
    MATERIAL_CHARACTERISTICS,
    ROUTING_POLICY_CONTRACT,
    WORK_REQUEST_CONTRACT,
    AdmissionRoutingError,
    apply_fast_track_route,
    build_admission_route,
    render_admission_route_json,
    validate_admission_routing_policy,
    validate_work_request,
)
from agentgov.cli import EXIT_FAIL, EXIT_PASS, main
from agentgov.development_session import apply_start_plan, build_start_plan
from agentgov.task_proposal import apply_task_admission_plan, build_task_admission_plan


ROOT = Path(__file__).resolve().parents[1]


def policy(*, admitted: bool = True, enabled: bool = True) -> dict:
    return {
        "contract": "agentgov.admission-routing-policy",
        "schema_version": "1.0",
        "policy_id": "fixture-admission-routing",
        "owner": "Human product owner",
        "no_task_classes": ["question", "explanation", "status_query", "read_only_diagnosis"],
        "fast_track": {
            "enabled": enabled,
            "allowed_scope_prefixes": ["src", "tests"] if enabled else [],
            "denied_scope_prefixes": ["src/security", "governance", ".github", "release"],
            "validation_command_prefixes": ["python -m unittest"] if enabled else [],
            "max_include_paths": 3 if enabled else 0,
            "max_exclude_paths": 2 if enabled else 0,
            "max_validation_commands": 2 if enabled else 0,
            "max_risk_items": 1 if enabled else 0,
            "max_assumptions": 1 if enabled else 0,
            "require_no_unknowns": True,
            "forbidden_characteristics": sorted(MATERIAL_CHARACTERISTICS),
        },
        "friction_budget": {
            "observe_only_max_human_interruptions": 0,
            "continue_active_max_human_interruptions": 0,
            "fast_track_max_human_interruptions": 0,
            "human_review_max_human_interruptions": 1,
            "full_review_max_human_interruptions": 2,
        },
        "authority": {
            "permits_noninteractive_fast_track_task_creation": enabled,
            "permits_session_start": False,
            "permits_code_change": False,
            "permits_scope_expansion": False,
            "permits_exception": False,
            "permits_git_operations": False,
            "permits_deployment": False,
            "permits_release": False,
        },
        "decision": {
            "state": "admitted" if admitted else "draft",
            "decided_by": "Human product owner",
            "rationale": "The fixture human reviewed these narrow low-risk routing limits.",
        },
    }


def proposal(task_id: str = "small-health-check", *, include: str = "src/app", unknowns=None) -> dict:
    return {
        "contract": "agentgov.task-proposal",
        "schema_version": "1.0",
        "proposal_id": "prp-0123456789abcdef0123456789abcdef",
        "source": {"adapter_id": "fixture-agent", "actor_class": "coding_agent"},
        "task": {
            "task_id": task_id,
            "title": "Add one small health check",
            "requirement_summary": "Add one bounded health check with deterministic focused validation.",
            "scope": {"include_paths": [include, "tests"], "exclude_paths": []},
            "acceptance_signals": ["The bounded health check test passes."],
            "validation_commands": ["python -m unittest tests.test_health -v"],
            "owner": "Human product owner",
            "risk": {"level": "low", "items": []},
            "assumptions": [],
            "unknowns": list(unknowns or []),
        },
        "content_boundary": {
            "contains_raw_prompt": False,
            "contains_transcript": False,
            "contains_source_content": False,
            "contains_credentials": False,
            "contains_absolute_paths": False,
        },
        "authority_boundary": {
            "admits_task": False,
            "starts_session": False,
            "authorizes_code_change": False,
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_git_operations": False,
            "authorizes_deployment": False,
            "authorizes_release": False,
        },
    }


def characteristics(**overrides: bool) -> dict:
    result = {key: False for key in MATERIAL_CHARACTERISTICS}
    result.update(overrides)
    return result


def request(request_class: str, *, task_proposal=None, active_task=None, **flags: bool) -> dict:
    return {
        "contract": "agentgov.work-request",
        "schema_version": "1.0",
        "request_id": "wrq-abcdef0123456789abcdef0123456789",
        "source": {"adapter_id": "fixture-agent", "actor_class": "coding_agent"},
        "request_class": request_class,
        "active_task": active_task,
        "proposal": task_proposal,
        "characteristics": characteristics(**flags),
        "content_boundary": {
            "contains_raw_prompt": False,
            "contains_transcript": False,
            "contains_source_content": False,
            "contains_credentials": False,
            "contains_absolute_paths": False,
        },
        "authority_boundary": {
            "admits_task": False,
            "authorizes_repository_write": False,
            "starts_session": False,
            "authorizes_scope_expansion": False,
            "authorizes_exception": False,
            "authorizes_git_operations": False,
            "authorizes_deployment": False,
            "authorizes_release": False,
        },
    }


def write_json(path: Path, value: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def create_repository(path: Path, *, policy_value=None, commit_policy: bool = True) -> tuple[Path, Path]:
    root = path
    (root / "governance/tasks").mkdir(parents=True)
    (root / "src/app").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "src/app/module.py").write_text("VALUE = 1\n", encoding="utf-8")
    (root / "AGENTS.md").write_text(
        "# Fixture instructions\n\nStay inside the admitted task scope.\n",
        encoding="utf-8",
    )
    policy_path = write_json(root / "governance/admission-policy.json", policy_value or policy())
    subprocess.run(("git", "init", "-q", str(root)), check=True)
    subprocess.run(("git", "-C", str(root), "config", "user.email", "fixture@example.invalid"), check=True)
    subprocess.run(("git", "-C", str(root), "config", "user.name", "Fixture"), check=True)
    if commit_policy:
        subprocess.run(("git", "-C", str(root), "add", "."), check=True)
        subprocess.run(("git", "-C", str(root), "commit", "-q", "-m", "fixture"), check=True)
    return root, policy_path


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(list(args))
    return code, stdout.getvalue(), stderr.getvalue()


class AdmissionRoutingTests(unittest.TestCase):
    def test_contracts_are_strict_and_authority_is_human_owned(self) -> None:
        valid_policy = policy()
        valid_request = request("repository_change", task_proposal=proposal())

        self.assertEqual(validate_admission_routing_policy(valid_policy), [])
        self.assertEqual(validate_work_request(valid_request), [])
        valid_policy["fast_track"]["forbidden_characteristics"].remove("external_write")
        valid_policy["friction_budget"]["fast_track_max_human_interruptions"] = 1
        valid_request["authority_boundary"]["admits_task"] = True

        self.assertTrue(any("every material characteristic" in item for item in validate_admission_routing_policy(valid_policy)))
        self.assertTrue(any("must equal 0" in item for item in validate_admission_routing_policy(valid_policy)))
        self.assertIn("$.authority_boundary.admits_task must equal false", validate_work_request(valid_request))

    def test_no_write_classes_route_without_task_or_human_interruption(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            before = subprocess.check_output(("git", "-C", str(root), "status", "--porcelain", "-uall"))
            for request_class in sorted(("question", "explanation", "status_query", "read_only_diagnosis")):
                route = build_admission_route(root, policy_path=policy_path, request=request(request_class))
                self.assertEqual(route.route, "observe_only")
                self.assertEqual(route.planned_human_interruptions, 0)
                self.assertIsNone(route.admission_plan)
            after = subprocess.check_output(("git", "-C", str(root), "status", "--porcelain", "-uall"))

        self.assertEqual(after, before)

    def test_clean_admitted_policy_fast_tracks_bounded_low_risk_task(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal()),
            )
            payload = json.loads(render_admission_route_json(route))

        self.assertEqual(route.route, "fast_track")
        self.assertTrue(route.policy_tracked_clean)
        self.assertEqual(route.planned_human_interruptions, 0)
        self.assertIsNotNone(route.admission_plan)
        self.assertTrue(payload["authority_boundary"]["standing_policy_authorizes_task_admission"])
        self.assertFalse(payload["authority_boundary"]["decision_applied"])
        self.assertTrue(payload["friction"]["within_budget"])

    def test_untracked_dirty_draft_or_disabled_policy_never_fast_tracks(self) -> None:
        scenarios = (
            (policy(), False, None),
            (policy(admitted=False), True, None),
            (policy(enabled=False), True, None),
            (policy(), True, "dirty"),
        )
        for index, (policy_value, committed, mutation) in enumerate(scenarios):
            with self.subTest(index=index), TemporaryDirectory() as temp_dir:
                root, policy_path = create_repository(
                    Path(temp_dir), policy_value=policy_value, commit_policy=committed
                )
                if mutation:
                    value = json.loads(policy_path.read_text(encoding="utf-8"))
                    value["decision"]["rationale"] += " Changed without review."
                    write_json(policy_path, value)
                route = build_admission_route(
                    root,
                    policy_path=policy_path,
                    request=request("repository_change", task_proposal=proposal()),
                )

                self.assertEqual(route.route, "human_review")
                self.assertEqual(route.planned_human_interruptions, 1)

    def test_material_characteristic_forces_full_review(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request(
                    "repository_change",
                    task_proposal=proposal(),
                    security_boundary_change=True,
                ),
            )

        self.assertEqual(route.route, "full_review")
        self.assertIn("material_security_boundary_change", route.reason_codes)
        self.assertEqual(route.planned_human_interruptions, 1)

    def test_unknowns_must_be_declared_and_force_full_review(self) -> None:
        proposed = proposal(unknowns=["The route name is unknown."])
        invalid = request("repository_change", task_proposal=proposed)
        self.assertTrue(any("unknown_scope must be true" in item for item in validate_work_request(invalid)))
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request(
                    "repository_change", task_proposal=proposed, unknown_scope=True
                ),
            )
        self.assertEqual(route.route, "full_review")

    def test_scope_and_validation_outside_delegation_require_one_review(self) -> None:
        scenarios = [proposal(include="docs"), proposal(), proposal()]
        scenarios[1]["task"]["validation_commands"] = ["npm test"]
        scenarios[2]["task"]["validation_commands"] = [
            "python -m unittest tests.test_health -v; remove everything"
        ]
        for proposed in scenarios:
            with TemporaryDirectory() as temp_dir:
                root, policy_path = create_repository(Path(temp_dir))
                route = build_admission_route(
                    root,
                    policy_path=policy_path,
                    request=request("repository_change", task_proposal=proposed),
                )
            self.assertEqual(route.route, "human_review")
            self.assertEqual(route.max_human_interruptions, 1)

    def test_active_task_continuation_reuses_verified_identity_without_readmission(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            task_plan = build_task_admission_plan(root, proposal(task_id="active-small-task"))
            task_result = apply_task_admission_plan(task_plan)
            start = build_start_plan(root, task=root / task_result.target)
            started = apply_start_plan(start)
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request(
                    "active_task_continuation",
                    active_task={
                        "task_id": started.session.task_id,
                        "task_digest": started.session.task_digest,
                    },
                ),
            )

            self.assertEqual(route.route, "continue_active")
            self.assertEqual(route.planned_human_interruptions, 0)
            self.assertIsNone(route.admission_plan)

    def test_active_task_mismatch_requires_review(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request(
                    "active_task_continuation",
                    active_task={"task_id": "missing-task", "task_digest": "sha256:" + "a" * 64},
                ),
            )
        self.assertEqual(route.route, "human_review")

    def test_fast_track_apply_is_noninteractive_and_creates_only_task(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal()),
            )
            result = apply_fast_track_route(route)

            self.assertTrue((root / result.target).is_file())
            self.assertFalse((root / ".agentgov").exists())
            new_files = subprocess.check_output(
                ("git", "-C", str(root), "ls-files", "--others", "--exclude-standard"),
                text=True,
            ).splitlines()
            self.assertEqual(new_files, [result.target])

    def test_fast_track_revalidates_policy_and_target_races(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal()),
            )
            value = json.loads(policy_path.read_text(encoding="utf-8"))
            value["decision"]["rationale"] += " Drifted."
            write_json(policy_path, value)

            with self.assertRaisesRegex(AdmissionRoutingError, "policy changed"):
                apply_fast_track_route(route)

        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(
                root,
                policy_path=policy_path,
                request=request("repository_change", task_proposal=proposal()),
            )
            target = root / route.admission_plan.target
            target.write_text("someone else\n", encoding="utf-8")
            with self.assertRaisesRegex(AdmissionRoutingError, "target appeared"):
                apply_fast_track_route(route)
            self.assertEqual(target.read_text(encoding="utf-8"), "someone else\n")

    def test_non_fast_route_cannot_be_applied(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            route = build_admission_route(root, policy_path=policy_path, request=request("question"))
            with self.assertRaisesRegex(AdmissionRoutingError, "only a fast_track"):
                apply_fast_track_route(route)

    def test_cli_preview_and_fast_track_apply_have_distinct_write_semantics(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            request_path = write_json(
                root / "request.json",
                request("repository_change", task_proposal=proposal()),
            )
            preview, stdout, stderr = run_cli(
                "route", "request", str(request_path), "--policy", str(policy_path),
                "--repository", str(root), "--format", "json",
            )
            self.assertEqual(preview, EXIT_PASS, stderr)
            self.assertEqual(json.loads(stdout)["route"], "fast_track")
            self.assertFalse((root / "governance/tasks/small-health-check.json").exists())

            applied, applied_stdout, applied_stderr = run_cli(
                "route", "request", str(request_path), "--policy", str(policy_path),
                "--repository", str(root), "--format", "json", "--apply-fast-track",
            )

            self.assertEqual(applied, EXIT_PASS, applied_stderr)
            payload = json.loads(applied_stdout)
            self.assertTrue(payload["authority_boundary"]["decision_applied"])
            self.assertTrue((root / "governance/tasks/small-health-check.json").is_file())
            self.assertFalse((root / ".agentgov").exists())

    def test_cli_refuses_apply_for_human_review_route(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root, policy_path = create_repository(Path(temp_dir))
            request_path = write_json(
                root / "request.json",
                request("repository_change", task_proposal=proposal(include="docs")),
            )
            code, stdout, stderr = run_cli(
                "route", "request", str(request_path), "--policy", str(policy_path),
                "--repository", str(root), "--apply-fast-track",
            )

        self.assertEqual(code, EXIT_FAIL)
        self.assertIn("ROUTE human_review", stdout)
        self.assertIn("cannot use non-interactive fast-track", stderr)

    def test_schema_and_template_contracts_match_runtime(self) -> None:
        policy_template = json.loads(
            (ROOT / "templates/admission-routing-policy.template.json").read_text(encoding="utf-8")
        )
        request_template = json.loads(
            (ROOT / "templates/work-request.template.json").read_text(encoding="utf-8")
        )
        self.assertEqual(validate_admission_routing_policy(policy_template), [])
        self.assertEqual(validate_work_request(request_template), [])
        for name, contract in (
            ("admission-routing-policy.schema.json", ROUTING_POLICY_CONTRACT),
            ("work-request.schema.json", WORK_REQUEST_CONTRACT),
            ("admission-route.schema.json", ADMISSION_ROUTE_CONTRACT),
        ):
            schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(schema["properties"]["contract"]["const"], contract)


if __name__ == "__main__":
    unittest.main()
