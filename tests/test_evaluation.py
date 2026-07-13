import contextlib
import io
import json
import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agentgov.capability import EVALUATION_READINESS
from agentgov.cli import EXIT_ERROR, EXIT_FAIL, EXIT_PASS, main
from agentgov.evaluation import EvaluationStatus, check_evaluation_bundle


ROOT = Path(__file__).resolve().parents[1]
EVALUATION = ROOT / "evaluation"
FIXTURES = EVALUATION / "fixtures"


def run_cli(*args: str) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(list(args))
    return exit_code, stdout.getvalue(), stderr.getvalue()


class EvaluationSchemaTests(unittest.TestCase):
    def test_all_evaluation_schemas_are_strict_json_schema_documents(self) -> None:
        schema_paths = sorted((EVALUATION / "schemas").glob("*.schema.json"))
        self.assertEqual(len(schema_paths), 4)

        for path in schema_paths:
            with self.subTest(schema=path.name):
                schema = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertFalse(schema["additionalProperties"])

        manifest_schema = json.loads(
            (EVALUATION / "schemas/evaluation-manifest.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            set(manifest_schema["properties"]["declared_readiness"]["enum"]),
            EVALUATION_READINESS,
        )


class EvaluationBundleTests(unittest.TestCase):
    def test_missing_manifest_is_honest_not_configured_warning(self) -> None:
        with TemporaryDirectory() as temp_dir:
            result = check_evaluation_bundle(Path(temp_dir))

        self.assertIs(result.status, EvaluationStatus.WARN)
        self.assertEqual(result.readiness, "not_configured")

    def test_needs_seed_cases_is_non_blocking_warning(self) -> None:
        result = check_evaluation_bundle(FIXTURES / "needs-seed-cases")

        self.assertIs(result.status, EvaluationStatus.WARN)
        self.assertEqual(result.readiness, "needs_seed_cases")

    def test_reviewed_baseline_bundle_passes(self) -> None:
        result = check_evaluation_bundle(FIXTURES / "baseline-ready")

        self.assertIs(result.status, EvaluationStatus.PASS)
        self.assertEqual(result.readiness, "baseline_ready")

    def test_unsupported_baseline_claim_fails(self) -> None:
        result = check_evaluation_bundle(FIXTURES / "invalid-baseline")

        self.assertIs(result.status, EvaluationStatus.FAIL)
        combined = " ".join(result.messages)
        self.assertIn("human_approved must be true", combined)
        self.assertIn("requires at least one reviewed failure case", combined)

    def test_regression_ready_requires_configured_numeric_threshold(self) -> None:
        with TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            shutil.copytree(FIXTURES / "baseline-ready", bundle)
            manifest_path = bundle / "evaluation-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["declared_readiness"] = "regression_ready"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = check_evaluation_bundle(bundle)

        self.assertIs(result.status, EvaluationStatus.FAIL)
        self.assertTrue(
            any("threshold_configured must be true" in message for message in result.messages)
        )

    def test_production_derived_case_must_be_sanitized(self) -> None:
        with TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            shutil.copytree(FIXTURES / "baseline-ready", bundle)
            case_path = bundle / "seed-cases/basic-request.json"
            case = json.loads(case_path.read_text(encoding="utf-8"))
            case["source"]["source_type"] = "production_derived"
            case["source"]["sanitized"] = False
            case_path.write_text(json.dumps(case), encoding="utf-8")

            result = check_evaluation_bundle(bundle)

        self.assertIs(result.status, EvaluationStatus.FAIL)
        self.assertTrue(any("sanitized must be true" in message for message in result.messages))

    def test_case_reference_cannot_escape_bundle(self) -> None:
        with TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            shutil.copytree(FIXTURES / "needs-seed-cases", bundle)
            manifest_path = bundle / "evaluation-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"]["seed"] = ["../outside.json"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = check_evaluation_bundle(bundle)

        self.assertIs(result.status, EvaluationStatus.FAIL)
        self.assertTrue(any("remain inside" in message for message in result.messages))

    def test_wrong_enum_types_return_fail_instead_of_crashing(self) -> None:
        with TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / "bundle"
            shutil.copytree(FIXTURES / "needs-seed-cases", bundle)
            manifest_path = bundle / "evaluation-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["declared_readiness"] = ["baseline_ready"]
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

            result = check_evaluation_bundle(bundle)

        self.assertIs(result.status, EvaluationStatus.FAIL)
        self.assertTrue(
            any("declared_readiness must be one of" in message for message in result.messages)
        )


class EvaluationCliTests(unittest.TestCase):
    def test_cli_returns_pass_for_baseline(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "check", "evaluation", str(FIXTURES / "baseline-ready")
        )
        self.assertEqual(exit_code, EXIT_PASS)
        self.assertIn("PASS evaluation:baseline_ready:", stdout)
        self.assertEqual(stderr, "")

    def test_cli_returns_fail_for_false_maturity_claim(self) -> None:
        exit_code, stdout, stderr = run_cli(
            "check", "evaluation", str(FIXTURES / "invalid-baseline")
        )
        self.assertEqual(exit_code, EXIT_FAIL)
        self.assertIn("FAIL evaluation:baseline_ready:", stdout)
        self.assertEqual(stderr, "")

    def test_cli_returns_error_for_missing_bundle(self) -> None:
        with TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = run_cli(
                "check", "evaluation", str(Path(temp_dir) / "missing")
            )
        self.assertEqual(exit_code, EXIT_ERROR)
        self.assertEqual(stdout, "")
        self.assertIn("ERROR evaluation: path not found:", stderr)


if __name__ == "__main__":
    unittest.main()
