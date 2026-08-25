from __future__ import annotations

import argparse
import json
from pathlib import Path

from .manifest import ManifestError, check_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the exact distribution-input manifest.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="derive current inputs and compare them exactly")
    check.add_argument("--repository", default=".")
    check.add_argument("--manifest", required=True)
    args = parser.parse_args()

    try:
        result = check_manifest(Path(args.repository), Path(args.manifest))
    except ManifestError as exc:
        result = {
            "contract": "agentgov.distribution-input-manifest-check-result",
            "schema_version": "1.0",
            "status": "FAIL",
            "errors": [str(exc)],
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
