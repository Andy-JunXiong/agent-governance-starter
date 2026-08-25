"""Internal short build-root contract for Windows-sensitive artifact work."""

from .root import (
    DEFAULT_MAX_PROJECTED_PATH,
    DEFAULT_MAX_ROOT_PATH,
    BuildRootError,
    EvidenceGatedCleanupResult,
    EvidenceReceipt,
    ShortBuildRoot,
    create_evidence_receipt,
    create_short_build_root,
    remove_short_build_root,
    remove_short_build_root_after_evidence,
)

__all__ = [
    "DEFAULT_MAX_PROJECTED_PATH",
    "DEFAULT_MAX_ROOT_PATH",
    "BuildRootError",
    "EvidenceGatedCleanupResult",
    "EvidenceReceipt",
    "ShortBuildRoot",
    "create_evidence_receipt",
    "create_short_build_root",
    "remove_short_build_root",
    "remove_short_build_root_after_evidence",
]
