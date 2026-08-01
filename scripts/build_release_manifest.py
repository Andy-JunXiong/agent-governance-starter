"""Generate a deterministic release manifest for one built wheel."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


_STABLE_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_RC_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+rc[0-9]+$")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--metadata",
        type=Path,
        help="bundled release metadata whose compatibility list should be preserved",
    )
    parser.add_argument(
        "--channel",
        choices=("release-candidate", "stable"),
        default="stable",
    )
    args = parser.parse_args()

    filename = args.wheel.name
    expected_filename = (
        f"agent_governance_starter-{args.version}-py3-none-any.whl"
    )
    if filename != expected_filename:
        parser.error(
            "wheel filename must match --version exactly: "
            f"expected {expected_filename}"
        )
    if args.channel == "stable" and not _STABLE_VERSION_RE.fullmatch(args.version):
        parser.error("stable channel requires a final major.minor.patch version")
    if args.channel == "release-candidate" and not _RC_VERSION_RE.fullmatch(
        args.version
    ):
        parser.error("release-candidate channel requires an rc version")
    digest = hashlib.sha256(args.wheel.read_bytes()).hexdigest()
    tag = f"v{args.version}"
    supported_from = ["0.1.0"]
    if args.metadata is not None:
        try:
            metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            parser.error(f"cannot read --metadata: {error}")
        if not isinstance(metadata, dict):
            parser.error("--metadata root must be an object")
        if metadata.get("tool_version") != args.version:
            parser.error("--metadata tool_version must match --version")
        if metadata.get("channel") != args.channel:
            parser.error("--metadata channel must match --channel")
        declared_supported_from = metadata.get("supported_from")
        if (
            not isinstance(declared_supported_from, list)
            or not declared_supported_from
            or any(not isinstance(item, str) for item in declared_supported_from)
        ):
            parser.error("--metadata supported_from must be a non-empty string array")
        supported_from = declared_supported_from
    document = {
        "contract": "agentgov.release-manifest",
        "schema_version": "1.0",
        "distribution_name": "agent-governance-starter",
        "tool_version": args.version,
        "channel": args.channel,
        "supported_from": supported_from,
        "readable_layout_versions": ["1.0"],
        "target_layout_version": "1.0",
        "repository_changes_declared": False,
        "declared_migrations": [],
        "release_notes_url": (
            "https://github.com/Andy-JunXiong/"
            f"agent-governance-starter/releases/tag/{tag}"
        ),
        "artifact": {
            "filename": filename,
            "url": (
                "https://github.com/Andy-JunXiong/agent-governance-starter/"
                f"releases/download/{tag}/{filename}"
            ),
            "sha256": digest,
            "install_method": "pipx",
        },
    }
    args.output.write_text(
        json.dumps(document, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
