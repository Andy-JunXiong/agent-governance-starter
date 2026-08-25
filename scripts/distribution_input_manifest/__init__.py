"""Read-only distribution-input manifest validation."""

from .manifest import ManifestError, check_manifest, derive_distribution_inputs

__all__ = ["ManifestError", "check_manifest", "derive_distribution_inputs"]
