"""Authenticated, draft-only materialization of a validated upgrade plan."""

from __future__ import annotations

import base64
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Protocol

from agentgov import __version__
from agentgov.benefits import compare_repository_reports, load_repository_report_snapshot
from agentgov.consumer_ci import UPGRADE_WORKFLOW_PATH, WORKFLOW_PATH
from agentgov.redaction import redact_evidence_text
from agentgov.upgrade_pr import (
    UpgradeChange,
    UpgradePlanState,
    UpgradePullRequestPlan,
    plan_upgrade_pull_request,
)


UPGRADE_WRITE_CONTRACT_VERSION = "1.1"
_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_ALLOWED_EVENTS = {"schedule", "workflow_dispatch"}


class UpgradeWriteState(str, Enum):
    CURRENT = "current"
    CREATED = "created"
    RECOVERED = "recovered"
    EXISTING = "existing"


@dataclass(frozen=True)
class RemoteFile:
    content: str
    sha: str


@dataclass(frozen=True)
class PullRequest:
    number: int
    url: str
    draft: bool


@dataclass(frozen=True)
class UpgradeWriteResult:
    repository: str
    base_branch: str
    state: UpgradeWriteState
    current_version: str
    available_version: str
    branch: str | None
    pull_request: PullRequest | None
    branch_created: bool
    workflow_commit_created: bool
    pull_request_created: bool
    changed_paths: tuple[str, ...]
    validation: "UpgradeValidationEvidence | None"


@dataclass(frozen=True)
class UpgradeValidationEvidence:
    current_report_sha256: str
    target_report_sha256: str
    current_summary: Mapping[str, int]
    target_summary: Mapping[str, int]
    deterministic_failures_introduced: tuple[str, ...]
    deterministic_failures_resolved: tuple[str, ...]

    @property
    def decision(self) -> str:
        return (
            "attention_required"
            if self.deterministic_failures_introduced
            else "no_new_deterministic_failures"
        )


class UpgradeWriteConflictError(Exception):
    """Raised when a bounded upgrade write is no longer safe."""


class GitHubApiError(Exception):
    """Raised when GitHub cannot complete an authorized API operation."""


class UpgradeGitHubClient(Protocol):
    def get_branch_sha(self, branch: str) -> str | None: ...

    def get_file(self, path: str, *, ref: str) -> RemoteFile: ...

    def create_branch(self, branch: str, *, sha: str) -> None: ...

    def update_file(
        self,
        path: str,
        *,
        branch: str,
        current_sha: str,
        content: str,
        message: str,
    ) -> str: ...

    def compare_changed_paths(self, *, base: str, head: str) -> tuple[str, ...]: ...

    def find_open_pull_request(
        self,
        *,
        branch: str,
        base: str,
    ) -> PullRequest | None: ...

    def create_draft_pull_request(
        self,
        *,
        branch: str,
        base: str,
        title: str,
        body: str,
    ) -> PullRequest: ...


class GitHubApiClient:
    """Minimal GitHub REST client; tokens are never included in errors."""

    def __init__(self, repository: str, *, token: str) -> None:
        if not _REPOSITORY_RE.fullmatch(repository):
            raise ValueError("repository must use owner/name format")
        if not token:
            raise ValueError("GitHub token must not be empty")
        self.repository = repository
        self._owner = repository.split("/", 1)[0]
        self._token = token

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Mapping[str, Any] | None = None,
        *,
        allow_not_found: bool = False,
    ) -> Any:
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            "https://api.github.com" + endpoint,
            data=data,
            method=method,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "application/json",
                "User-Agent": f"agentgov/{__version__}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
        except urllib.error.HTTPError as exc:
            if allow_not_found and exc.code == 404:
                return None
            raise GitHubApiError(
                f"GitHub API {method} {endpoint.split('?', 1)[0]} returned HTTP {exc.code}"
            ) from exc
        except urllib.error.URLError as exc:
            raise GitHubApiError("GitHub API request could not be completed") from exc
        if not body:
            return None
        try:
            return json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubApiError("GitHub API returned an invalid JSON response") from exc

    def get_branch_sha(self, branch: str) -> str | None:
        encoded = urllib.parse.quote(branch, safe="")
        payload = self._request(
            "GET",
            f"/repos/{self.repository}/git/ref/heads/{encoded}",
            allow_not_found=True,
        )
        if payload is None:
            return None
        try:
            return str(payload["object"]["sha"])
        except (KeyError, TypeError) as exc:
            raise GitHubApiError("GitHub branch response is missing its commit SHA") from exc

    def get_file(self, path: str, *, ref: str) -> RemoteFile:
        encoded_path = urllib.parse.quote(path, safe="/")
        encoded_ref = urllib.parse.quote(ref, safe="")
        payload = self._request(
            "GET",
            f"/repos/{self.repository}/contents/{encoded_path}?ref={encoded_ref}",
        )
        try:
            raw_content = base64.b64decode(payload["content"], validate=False)
            content = raw_content.decode("utf-8")
            sha = str(payload["sha"])
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as exc:
            raise GitHubApiError("GitHub file response is not valid UTF-8 content") from exc
        return RemoteFile(content=content, sha=sha)

    def create_branch(self, branch: str, *, sha: str) -> None:
        self._request(
            "POST",
            f"/repos/{self.repository}/git/refs",
            {"ref": f"refs/heads/{branch}", "sha": sha},
        )

    def update_file(
        self,
        path: str,
        *,
        branch: str,
        current_sha: str,
        content: str,
        message: str,
    ) -> str:
        encoded_path = urllib.parse.quote(path, safe="/")
        payload = self._request(
            "PUT",
            f"/repos/{self.repository}/contents/{encoded_path}",
            {
                "message": message,
                "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
                "sha": current_sha,
                "branch": branch,
            },
        )
        try:
            return str(payload["commit"]["sha"])
        except (KeyError, TypeError) as exc:
            raise GitHubApiError("GitHub update response is missing its commit SHA") from exc

    def compare_changed_paths(self, *, base: str, head: str) -> tuple[str, ...]:
        encoded_base = urllib.parse.quote(base, safe="")
        encoded_head = urllib.parse.quote(head, safe="")
        payload = self._request(
            "GET",
            f"/repos/{self.repository}/compare/{encoded_base}...{encoded_head}",
        )
        try:
            files = payload["files"]
            return tuple(str(item["filename"]) for item in files)
        except (KeyError, TypeError) as exc:
            raise GitHubApiError("GitHub comparison response is missing changed files") from exc

    def find_open_pull_request(
        self,
        *,
        branch: str,
        base: str,
    ) -> PullRequest | None:
        query = urllib.parse.urlencode(
            {
                "state": "open",
                "head": f"{self._owner}:{branch}",
                "base": base,
                "per_page": "1",
            }
        )
        payload = self._request(
            "GET",
            f"/repos/{self.repository}/pulls?{query}",
        )
        if not payload:
            return None
        return _pull_request_from_payload(payload[0])

    def create_draft_pull_request(
        self,
        *,
        branch: str,
        base: str,
        title: str,
        body: str,
    ) -> PullRequest:
        payload = self._request(
            "POST",
            f"/repos/{self.repository}/pulls",
            {
                "title": title,
                "head": branch,
                "base": base,
                "body": body,
                "draft": True,
            },
        )
        result = _pull_request_from_payload(payload)
        if not result.draft:
            raise GitHubApiError("GitHub did not create the pull request as a draft")
        return result


def _pull_request_from_payload(payload: Mapping[str, Any]) -> PullRequest:
    try:
        number = int(payload["number"])
        url = str(payload["html_url"])
        draft = bool(payload["draft"])
    except (KeyError, TypeError, ValueError) as exc:
        raise GitHubApiError("GitHub pull request response is incomplete") from exc
    if number < 1 or not url.startswith("https://github.com/"):
        raise GitHubApiError("GitHub pull request response has invalid identity")
    return PullRequest(number=number, url=url, draft=draft)


def _sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_upgrade_validation(
    current_report: Path,
    target_report: Path,
    *,
    current_version: str,
    available_version: str,
) -> UpgradeValidationEvidence:
    current = load_repository_report_snapshot(current_report)
    target = load_repository_report_snapshot(target_report)
    if current.tool_version != current_version:
        raise UpgradeWriteConflictError(
            "current validation report does not identify the managed current version"
        )
    if target.tool_version != available_version:
        raise UpgradeWriteConflictError(
            "target validation report does not identify the proposed target version"
        )
    comparison = compare_repository_reports(current_report, target_report)
    introduced = tuple(
        sorted(
            check_id
            for check_id, status in target.findings.items()
            if status == "FAIL" and current.findings.get(check_id) != "FAIL"
        )
    )
    resolved = tuple(
        sorted(
            check_id
            for check_id, status in current.findings.items()
            if status == "FAIL" and target.findings.get(check_id) != "FAIL"
        )
    )
    if comparison.repository != current.repository:
        raise UpgradeWriteConflictError("upgrade validation repository identity changed")
    return UpgradeValidationEvidence(
        current_report_sha256=_sha256_file(current_report),
        target_report_sha256=_sha256_file(target_report),
        current_summary=current.summary,
        target_summary=target.summary,
        deterministic_failures_introduced=introduced,
        deterministic_failures_resolved=resolved,
    )


def _validation_body(evidence: UpgradeValidationEvidence) -> str:
    current = evidence.current_summary
    target = evidence.target_summary
    introduced = (
        ", ".join(
            f"`{redact_evidence_text(item)}`"
            for item in evidence.deterministic_failures_introduced
        )
        or "none"
    )
    return (
        "\n\n## Target-version dry run\n\n"
        f"Decision: **{evidence.decision}**\n\n"
        "| Version under test | PASS | WARN | FAIL | ADVISORY |\n"
        "|---|---:|---:|---:|---:|\n"
        f"| Current | {current['pass']} | {current['warn']} | {current['fail']} | {current['advisory']} |\n"
        f"| Target | {target['pass']} | {target['warn']} | {target['fail']} | {target['advisory']} |\n\n"
        f"New deterministic failures under the target version: {introduced}.\n\n"
        f"Current report SHA-256: `{evidence.current_report_sha256}`  \n"
        f"Target report SHA-256: `{evidence.target_report_sha256}`\n\n"
        "This dry run validates AgentGov repository findings only. It does not run "
        "project tests or authorize merge, release, or deployment."
    )


def _validate_candidate_shape(
    plan: UpgradePullRequestPlan,
) -> tuple[UpgradeChange, ...]:
    allowed_paths = (WORKFLOW_PATH, UPGRADE_WORKFLOW_PATH)
    paths = tuple(change.path for change in plan.changes)
    if (
        not 1 <= len(plan.changes) <= 2
        or paths != allowed_paths[: len(paths)]
        or any(
            change.action != "update" or change.before_sha256 is None
            for change in plan.changes
        )
        or not plan.branch
        or not plan.title
        or not plan.body
    ):
        raise UpgradeWriteConflictError(
            "upgrade plan is not an exact update of the bounded managed workflow set"
        )
    return plan.changes


def create_upgrade_draft_pull_request(
    root: Path,
    *,
    manifest_path: Path,
    repository: str,
    base_branch: str,
    event_source: str,
    client: UpgradeGitHubClient,
    current_report_path: Path | None = None,
    target_report_path: Path | None = None,
) -> UpgradeWriteResult:
    """Revalidate and materialize only the bounded managed workflow set."""

    if not _REPOSITORY_RE.fullmatch(repository):
        raise ValueError("repository must use owner/name format")
    if not base_branch or base_branch.startswith("-"):
        raise ValueError("base branch must be a non-empty branch name")
    if event_source not in _ALLOWED_EVENTS:
        raise UpgradeWriteConflictError(
            "upgrade PR writes are allowed only for schedule or workflow_dispatch events"
        )

    plan = plan_upgrade_pull_request(root, manifest_path=manifest_path)
    if plan.state is UpgradePlanState.CURRENT:
        return UpgradeWriteResult(
            repository=repository,
            base_branch=base_branch,
            state=UpgradeWriteState.CURRENT,
            current_version=plan.current_version,
            available_version=plan.available_version,
            branch=None,
            pull_request=None,
            branch_created=False,
            workflow_commit_created=False,
            pull_request_created=False,
            changed_paths=(),
            validation=None,
        )
    if plan.state is UpgradePlanState.BLOCKED:
        raise UpgradeWriteConflictError("; ".join(plan.reasons))

    changes = _validate_candidate_shape(plan)
    if current_report_path is None or target_report_path is None:
        raise UpgradeWriteConflictError(
            "current and target-version dry-run reports are required before creating an upgrade PR"
        )
    validation = _load_upgrade_validation(
        current_report_path,
        target_report_path,
        current_version=plan.current_version,
        available_version=plan.available_version,
    )
    branch = plan.branch
    assert branch is not None and plan.title is not None and plan.body is not None
    paths = tuple(change.path.as_posix() for change in changes)

    existing_pr = client.find_open_pull_request(branch=branch, base=base_branch)
    if existing_pr is not None:
        branch_files = {
            change.path.as_posix(): client.get_file(change.path.as_posix(), ref=branch)
            for change in changes
        }
        changed_paths = client.compare_changed_paths(base=base_branch, head=branch)
        if (
            any(
                _sha256_text(branch_files[change.path.as_posix()].content)
                != change.after_sha256
                for change in changes
            )
            or tuple(sorted(changed_paths)) != tuple(sorted(paths))
        ):
            raise UpgradeWriteConflictError(
                "existing upgrade pull request is not the exact managed workflow set"
            )
        return UpgradeWriteResult(
            repository=repository,
            base_branch=base_branch,
            state=UpgradeWriteState.EXISTING,
            current_version=plan.current_version,
            available_version=plan.available_version,
            branch=branch,
            pull_request=existing_pr,
            branch_created=False,
            workflow_commit_created=False,
            pull_request_created=False,
            changed_paths=paths,
            validation=validation,
        )

    base_sha = client.get_branch_sha(base_branch)
    if base_sha is None:
        raise UpgradeWriteConflictError(f"base branch does not exist: {base_branch}")
    base_files = {
        change.path.as_posix(): client.get_file(change.path.as_posix(), ref=base_branch)
        for change in changes
    }
    if any(
        _sha256_text(base_files[change.path.as_posix()].content)
        != change.before_sha256
        for change in changes
    ):
        raise UpgradeWriteConflictError(
            "remote base workflow changed after planning; no branch was written"
        )

    branch_sha = client.get_branch_sha(branch)
    branch_created = False
    commit_created = False
    recovered = False
    if branch_sha is None:
        client.create_branch(branch, sha=base_sha)
        branch_created = True
        branch_sha = base_sha
    branch_files = {
        change.path.as_posix(): client.get_file(change.path.as_posix(), ref=branch)
        for change in changes
    }
    branch_hashes = {
        path: _sha256_text(remote.content) for path, remote in branch_files.items()
    }
    after_paths = tuple(
        change.path.as_posix()
        for change in changes
        if branch_hashes[change.path.as_posix()] == change.after_sha256
    )
    if any(
        branch_hashes[change.path.as_posix()]
        not in (change.before_sha256, change.after_sha256)
        for change in changes
    ):
        raise UpgradeWriteConflictError(
            "existing upgrade branch is not an unchanged base or bounded prior write"
        )
    actual_changed_paths = client.compare_changed_paths(base=base_branch, head=branch)
    if tuple(sorted(actual_changed_paths)) != tuple(sorted(after_paths)):
        raise UpgradeWriteConflictError(
            "existing upgrade branch contains changes outside the managed workflow set"
        )
    if not after_paths and branch_sha != base_sha:
        raise UpgradeWriteConflictError(
            "existing upgrade branch does not point to the unchanged base"
        )
    recovered = len(after_paths) == len(changes)

    if not recovered:
        for change in changes:
            path = change.path.as_posix()
            branch_file = branch_files[path]
            if branch_hashes[path] == change.after_sha256:
                continue
            client.update_file(
                path,
                branch=branch,
                current_sha=branch_file.sha,
                content=change.content,
                message=plan.title,
            )
            commit_created = True
            written_file = client.get_file(path, ref=branch)
            if _sha256_text(written_file.content) != change.after_sha256:
                raise UpgradeWriteConflictError(
                    "remote workflow did not match the validated after hash"
                )
        written_paths = client.compare_changed_paths(base=base_branch, head=branch)
        if tuple(sorted(written_paths)) != tuple(sorted(paths)):
            raise UpgradeWriteConflictError(
                "written branch does not contain exactly the managed workflow set"
            )

    pull_request = client.create_draft_pull_request(
        branch=branch,
        base=base_branch,
        title=plan.title,
        body=plan.body + _validation_body(validation),
    )
    return UpgradeWriteResult(
        repository=repository,
        base_branch=base_branch,
        state=(UpgradeWriteState.RECOVERED if recovered else UpgradeWriteState.CREATED),
        current_version=plan.current_version,
        available_version=plan.available_version,
        branch=branch,
        pull_request=pull_request,
        branch_created=branch_created,
        workflow_commit_created=commit_created,
        pull_request_created=True,
        changed_paths=paths,
        validation=validation,
    )


def upgrade_write_result_document(result: UpgradeWriteResult) -> dict[str, Any]:
    return {
        "contract_version": UPGRADE_WRITE_CONTRACT_VERSION,
        "tool": {"name": "agentgov", "version": __version__},
        "mode": "github_draft_pull_request",
        "repository": result.repository,
        "base_branch": result.base_branch,
        "state": result.state.value,
        "current_version": result.current_version,
        "available_version": result.available_version,
        "branch": result.branch,
        "pull_request": (
            None
            if result.pull_request is None
            else {
                "number": result.pull_request.number,
                "url": result.pull_request.url,
                "draft": result.pull_request.draft,
            }
        ),
        "validation": (
            None
            if result.validation is None
            else {
                "decision": result.validation.decision,
                "current_report_sha256": result.validation.current_report_sha256,
                "target_report_sha256": result.validation.target_report_sha256,
                "current_summary": dict(result.validation.current_summary),
                "target_summary": dict(result.validation.target_summary),
                "deterministic_failures_introduced": list(
                    redact_evidence_text(item)
                    for item in result.validation.deterministic_failures_introduced
                ),
                "deterministic_failures_resolved": list(
                    redact_evidence_text(item)
                    for item in result.validation.deterministic_failures_resolved
                ),
            }
        ),
        "actions": {
            "branch_created": result.branch_created,
            "managed_workflow_commit_created": result.workflow_commit_created,
            "draft_pull_request_created": result.pull_request_created,
        },
        "authority_boundary": {
            "changed_paths": list(result.changed_paths),
            "merge_authorized": False,
            "release_authorized": False,
            "deploy_authorized": False,
            "production_execution_authorized": False,
        },
    }


def render_upgrade_write_result_json(result: UpgradeWriteResult) -> str:
    return json.dumps(
        upgrade_write_result_document(result),
        indent=2,
        ensure_ascii=False,
    ) + "\n"
