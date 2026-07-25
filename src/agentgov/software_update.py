"""Verified GitHub Release download and pipx installation helpers."""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Mapping


LATEST_MANIFEST_URL = (
    "https://github.com/Andy-JunXiong/agent-governance-starter/"
    "releases/latest/download/release-manifest.json"
)
MAX_MANIFEST_BYTES = 128 * 1024
MAX_WHEEL_BYTES = 25 * 1024 * 1024


class SoftwareUpdateError(Exception):
    """Raised when verified software update cannot safely continue."""


def download_https(url: str, destination: Path, *, maximum_bytes: int) -> str:
    """Download one bounded HTTPS resource and return its SHA-256."""

    if not url.startswith("https://"):
        raise SoftwareUpdateError("download URL must use HTTPS")
    digest = hashlib.sha256()
    written = 0
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            final_url = response.geturl()
            if not final_url.startswith("https://"):
                raise SoftwareUpdateError("download redirected away from HTTPS")
            with destination.open("xb") as output:
                while chunk := response.read(64 * 1024):
                    written += len(chunk)
                    if written > maximum_bytes:
                        raise SoftwareUpdateError("download exceeds the allowed size")
                    digest.update(chunk)
                    output.write(chunk)
    except SoftwareUpdateError:
        destination.unlink(missing_ok=True)
        raise
    except (OSError, ValueError) as exc:
        destination.unlink(missing_ok=True)
        raise SoftwareUpdateError(f"download failed: {exc}") from exc
    return digest.hexdigest()


def download_release_manifest(destination: Path) -> None:
    download_https(
        LATEST_MANIFEST_URL,
        destination,
        maximum_bytes=MAX_MANIFEST_BYTES,
    )


def download_verified_wheel(artifact: Mapping[str, str], destination: Path) -> None:
    digest = download_https(
        artifact["url"],
        destination,
        maximum_bytes=MAX_WHEEL_BYTES,
    )
    if digest != artifact["sha256"]:
        destination.unlink(missing_ok=True)
        raise SoftwareUpdateError(
            f"SHA-256 mismatch: expected {artifact['sha256']}, received {digest}"
        )


def install_wheel_with_pipx(wheel: Path, *, expected_version: str) -> Path:
    """Upgrade the pipx environment, then verify the exposed command."""

    pipx = shutil.which("pipx")
    if pipx is None:
        raise SoftwareUpdateError("pipx is not available on PATH")
    invoked = Path(sys.argv[0])
    executable = (
        str(invoked.resolve())
        if invoked.name.lower() in {"agentgov", "agentgov.exe"} and invoked.exists()
        else shutil.which("agentgov")
    )
    completed = subprocess.run(
        [
            pipx,
            "runpip",
            "agent-governance-starter",
            "install",
            "--upgrade",
            str(wheel),
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    if completed.returncode != 0:
        preserved = False
        if executable:
            probe = subprocess.run(
                [executable, "--version"],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            preserved = probe.returncode == 0
        detail = completed.stderr.strip() or completed.stdout.strip() or "pipx failed"
        state = "previous AgentGov remains executable" if preserved else (
            "previous AgentGov could not be verified"
        )
        raise SoftwareUpdateError(f"pipx installation failed; {state}: {detail}")
    if executable is None:
        raise SoftwareUpdateError("pipx completed but agentgov is not on PATH")
    probe = subprocess.run(
        [executable, "--version"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if probe.returncode != 0 or probe.stdout.strip() != f"agentgov {expected_version}":
        raise SoftwareUpdateError(
            "installed command did not report the expected AgentGov version"
        )
    return Path(executable).resolve()


def relaunch_updated_agentgov(
    executable: Path,
    *,
    repository: Path,
    manifest: Path,
    resume_token: str,
) -> int:
    env = os.environ.copy()
    env["AGENTGOV_UPDATE_RESUME_TOKEN"] = resume_token
    completed = subprocess.run(
        [
            str(executable),
            "update",
            str(repository),
            "--manifest",
            str(manifest),
            "--resume-after-tool-update",
            resume_token,
        ],
        env=env,
        check=False,
    )
    return completed.returncode
