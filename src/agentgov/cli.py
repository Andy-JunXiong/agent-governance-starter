"""Command-line interface for Agent Governance Starter Kit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from agentgov.agent_skills import check_agent_skills
from agentgov.artifacts import (
    ArtifactConflictError,
    ArtifactPolicyError,
    check_capability_artifact,
    export_capability_artifact,
)
from agentgov.capability import load_capability_manifest, validate_capability_manifest
from agentgov.initializer import InitConflictError, initialize_project
from agentgov.evaluation import EvaluationStatus, check_evaluation_bundle
from agentgov.repository import FindingStatus, check_repository
from agentgov.references import (
    ReferencePolicyError,
    ReferenceStatus,
    check_capability_references,
)
from agentgov.reporting import (
    ReportConflictError,
    render_repository_report,
    write_markdown_report,
)


EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_ERROR = 2


def _check_capability(path: Path) -> int:
    try:
        manifest = load_capability_manifest(path)
    except FileNotFoundError:
        print(f"ERROR capability: file not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except PermissionError:
        print(f"ERROR capability: permission denied: {path}", file=sys.stderr)
        return EXIT_ERROR
    except UnicodeError as exc:
        print(f"ERROR capability: file is not valid UTF-8: {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR capability: invalid JSON: {path}:{exc.lineno}:{exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR capability: {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except OSError as exc:
        print(f"ERROR capability: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    errors = validate_capability_manifest(manifest)
    if errors:
        print(f"FAIL capability: {path}")
        for error in errors:
            print(f"  - {error}")
        return EXIT_FAIL

    print(f"PASS capability: {path}")
    return EXIT_PASS


def _check_evaluation(path: Path) -> int:
    try:
        result = check_evaluation_bundle(path)
    except FileNotFoundError:
        print(f"ERROR evaluation: path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR evaluation: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR evaluation: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    print(f"{result.status.value} evaluation:{result.readiness}: {path}")
    for message in result.messages:
        print(f"  - {message}")
    return EXIT_FAIL if result.status is EvaluationStatus.FAIL else EXIT_PASS


def _check_agent_skills(path: Path) -> int:
    try:
        report = check_agent_skills(path)
    except FileNotFoundError:
        print(f"ERROR agent-skills: path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR agent-skills: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR agent-skills: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for finding in report.findings:
        status = "PASS" if finding.passed else "FAIL"
        print(f"{status} {finding.check_id}: {finding.message}")
    pass_count = sum(finding.passed for finding in report.findings)
    fail_count = len(report.findings) - pass_count
    print(f"SUMMARY PASS={pass_count} FAIL={fail_count}")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _export_capability(
    manifest: Path,
    *,
    repository: Path,
    output: Path,
    replace: bool,
) -> int:
    try:
        result = export_capability_artifact(
            manifest,
            repository=repository,
            output=output,
            replace=replace,
        )
    except FileNotFoundError as exc:
        print(f"ERROR export capability: path not found: {exc.filename or exc}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR export capability: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except (ArtifactPolicyError, ArtifactConflictError) as exc:
        print(f"FAIL export capability: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR export capability: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR export capability: cannot export artifact: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for path in result.files:
        print(f"EXPORT {path}")
    print(f"SOURCE {result.source_hash}")
    print(f"PASS export capability: {result.capability_name}")
    return EXIT_PASS


def _check_artifact(path: Path, *, repository: Path) -> int:
    try:
        result = check_capability_artifact(path, repository=repository)
    except FileNotFoundError:
        print(f"ERROR artifact: path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR artifact: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except ArtifactPolicyError as exc:
        print(f"FAIL artifact: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR artifact: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR artifact: cannot check {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    status = "PASS" if result.passed else "FAIL"
    print(f"{status} artifact: {result.directory}")
    for message in result.messages:
        print(f"  - {message}")
    return EXIT_PASS if result.passed else EXIT_FAIL


def _check_references(manifest: Path, *, repository: Path) -> int:
    try:
        report = check_capability_references(manifest, repository=repository)
    except FileNotFoundError:
        print(f"ERROR references: path not found: {manifest}", file=sys.stderr)
        return EXIT_ERROR
    except json.JSONDecodeError as exc:
        print(
            f"ERROR references: invalid JSON at line {exc.lineno}, "
            f"column {exc.colno}: {exc.msg}",
            file=sys.stderr,
        )
        return EXIT_ERROR
    except ReferencePolicyError as exc:
        print(f"FAIL references: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR references: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR references: cannot check {manifest}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for finding in report.findings:
        print(f"{finding.status.value} {finding.check_id}: {finding.message}")
    summary = " ".join(
        f"{status.value}={report.count(status)}"
        for status in (
            ReferenceStatus.PASS,
            ReferenceStatus.WARN,
            ReferenceStatus.FAIL,
        )
    )
    print(f"SUMMARY {summary}")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _init_project(target: Path, *, project_name: str, dry_run: bool) -> int:
    try:
        report = initialize_project(
            target,
            project_name=project_name,
            dry_run=dry_run,
        )
    except InitConflictError as exc:
        print(f"FAIL init: {exc}")
        return EXIT_FAIL
    except ValueError as exc:
        print(f"ERROR init: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR init: cannot create governance scaffold: {exc}", file=sys.stderr)
        return EXIT_ERROR

    action = "PLAN" if report.dry_run else "CREATE"
    for generated_file in report.files:
        print(f"{action} {generated_file.relative_path.as_posix()}")

    if report.unresolved_placeholders:
        print(
            "WARN init: "
            f"{len(report.unresolved_placeholders)} unresolved governance placeholder(s) "
            "require human review"
        )

    if report.dry_run:
        print(f"PASS init dry-run: {report.target}")
    else:
        print(f"PASS init: {report.target}")
    return EXIT_PASS


def _check_repository(path: Path) -> int:
    try:
        report = check_repository(path)
    except FileNotFoundError:
        print(f"ERROR repository: path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR repository: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR repository: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    for finding in report.findings:
        print(f"{finding.status.value} {finding.check_id}: {finding.message}")

    summary = " ".join(
        f"{status.value}={report.count(status)}"
        for status in (
            FindingStatus.PASS,
            FindingStatus.WARN,
            FindingStatus.FAIL,
            FindingStatus.ADVISORY,
        )
    )
    print(f"SUMMARY {summary}")
    return EXIT_FAIL if report.has_failures else EXIT_PASS


def _report_repository(path: Path, *, output: Path | None) -> int:
    try:
        report = check_repository(path)
        content = render_repository_report(report)
    except FileNotFoundError:
        print(f"ERROR report: repository path not found: {path}", file=sys.stderr)
        return EXIT_ERROR
    except ValueError as exc:
        print(f"ERROR report: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except (OSError, UnicodeError) as exc:
        print(f"ERROR report: cannot read {path}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if output is None:
        print(content, end="")
    else:
        try:
            write_markdown_report(output, content)
        except ReportConflictError as exc:
            print(f"FAIL report: {exc}")
            return EXIT_FAIL
        except (OSError, UnicodeError) as exc:
            print(f"ERROR report: cannot write {output}: {exc}", file=sys.stderr)
            return EXIT_ERROR
        print(f"REPORT {output}")

    return EXIT_FAIL if report.has_failures else EXIT_PASS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agentgov",
        description="Check repository-native AI governance contracts.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    init_parser = commands.add_parser(
        "init",
        help="Create a governance scaffold in a new or empty directory.",
    )
    init_parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        default=Path("."),
        help="New or empty target directory (default: current directory).",
    )
    init_parser.add_argument(
        "--project-name",
        required=True,
        help="Human-readable project name used in generated documents.",
    )
    init_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned files without creating the target directory.",
    )
    init_parser.set_defaults(
        handler=lambda args: _init_project(
            args.target,
            project_name=args.project_name,
            dry_run=args.dry_run,
        )
    )

    export_parser = commands.add_parser(
        "export",
        help="Generate repository-local governance artifacts.",
    )
    export_targets = export_parser.add_subparsers(dest="export_target", required=True)
    export_capability_parser = export_targets.add_parser(
        "capability",
        help="Export one prompt capability as deterministic review artifacts.",
    )
    export_capability_parser.add_argument(
        "manifest",
        type=Path,
        help="Capability manifest located inside the repository root.",
    )
    export_capability_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root used for path and source resolution (default: current directory).",
    )
    export_capability_parser.add_argument(
        "--output",
        type=Path,
        default=Path("prompt-governance/artifacts"),
        help="Output root inside the repository.",
    )
    export_capability_parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace only the generated CAPABILITY.md and artifact.json files.",
    )
    export_capability_parser.set_defaults(
        handler=lambda args: _export_capability(
            args.manifest,
            repository=args.repository,
            output=args.output,
            replace=args.replace,
        )
    )

    check_parser = commands.add_parser("check", help="Run a deterministic governance check.")
    check_targets = check_parser.add_subparsers(dest="check_target", required=True)

    capability_parser = check_targets.add_parser(
        "capability",
        help="Validate one prompt capability manifest.",
    )
    capability_parser.add_argument("manifest", type=Path, help="Path to a capability JSON file.")
    capability_parser.set_defaults(handler=lambda args: _check_capability(args.manifest))

    evaluation_parser = check_targets.add_parser(
        "evaluation",
        help="Validate an evaluation bundle and its declared readiness.",
    )
    evaluation_parser.add_argument(
        "bundle",
        type=Path,
        help="Directory containing evaluation-manifest.json and referenced cases.",
    )
    evaluation_parser.set_defaults(handler=lambda args: _check_evaluation(args.bundle))

    agent_skills_parser = check_targets.add_parser(
        "agent-skills",
        help="Validate repository-native agent operating protocols.",
    )
    agent_skills_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("agent-skills"),
        help="Agent skills directory (default: agent-skills).",
    )
    agent_skills_parser.set_defaults(handler=lambda args: _check_agent_skills(args.path))

    artifact_parser = check_targets.add_parser(
        "artifact",
        help="Check a capability artifact for manifest, source, or generated-file drift.",
    )
    artifact_parser.add_argument(
        "path",
        type=Path,
        help="Capability artifact directory containing artifact.json.",
    )
    artifact_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root used for path and source resolution (default: current directory).",
    )
    artifact_parser.set_defaults(
        handler=lambda args: _check_artifact(args.path, repository=args.repository)
    )

    references_parser = check_targets.add_parser(
        "references",
        help="Check repository-local capability schema, caller, source, and evidence paths.",
    )
    references_parser.add_argument(
        "manifest",
        type=Path,
        help="Capability manifest located inside the repository root.",
    )
    references_parser.add_argument(
        "--repository",
        type=Path,
        default=Path("."),
        help="Repository root used for reference resolution (default: current directory).",
    )
    references_parser.set_defaults(
        handler=lambda args: _check_references(
            args.manifest,
            repository=args.repository,
        )
    )

    repository_parser = check_targets.add_parser(
        "repository",
        help="Check required governance files, placeholders, and capability manifests.",
    )
    repository_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to check (default: current directory).",
    )
    repository_parser.set_defaults(handler=lambda args: _check_repository(args.path))

    report_parser = commands.add_parser(
        "report",
        help="Render governance findings as a Markdown report.",
    )
    report_targets = report_parser.add_subparsers(dest="report_target", required=True)
    report_repository_parser = report_targets.add_parser(
        "repository",
        help="Render a repository governance report.",
    )
    report_repository_parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=Path("."),
        help="Repository directory to report on (default: current directory).",
    )
    report_repository_parser.add_argument(
        "--output",
        type=Path,
        help="Write a new Markdown file instead of printing to standard output.",
    )
    report_repository_parser.set_defaults(
        handler=lambda args: _report_repository(args.path, output=args.output)
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a stable process exit code."""

    args = build_parser().parse_args(argv)
    return int(args.handler(args))
