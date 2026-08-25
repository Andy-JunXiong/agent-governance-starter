# Replayable distribution-input manifest v1

Date: 2026-08-25

## Outcome

`CURRENT_DISTRIBUTION_INPUT_MANIFEST_MATCHED`

The repository now owns an exact, independently checkable declaration of its
current supported distribution inputs. The declaration contains 186 safe,
sorted, unique repository-relative regular-file paths. The read-only checker
derives the same set from the current supported `pyproject.toml` subset.

Canonical identities:

- path list:
  `sha256:cfea3a3632bd75d1f4db51168d257c465987d3fe620fda2449abcd86f42fcd03`;
- path plus per-file content identity:
  `sha256:a986da7096e257b90e984084373f923ad460ff4c95f172a08fe4cf2d1fccacaf`.

At observation time the set contained 178 committed inputs, 5 tracked deltas,
3 untracked current overlays, and 0 deletions. These are Git-layer
classifications, not approval, correctness, or release claims.

## Supersession and limits

The manifest supersedes the earlier durable evidence that retained a count of
199 and a digest but omitted the exact paths. It does not recover, reconstruct,
or identify those historical paths. The preceding rehearsal therefore remains
stopped; no result was rewritten.

The checker intentionally supports only the current string readme,
package-find roots, and setuptools data-file patterns. Python `*` globbing is
non-recursive unless `**` is explicit. Unsupported selection configuration,
unsafe paths, links, missing or extra inputs, deletions, digest drift, or a
changing Git/filesystem observation fail closed. Cross-version setuptools
parity remains unknown without an artifact build.

## Validation and authority

Task-start baseline is
`sha256:ea8ce40944cdc31860614c3d2e03fb0e0e6f409f62e42b4d284f00a2b0e400f7`.
The current checker passes. Eleven isolated fixtures pass with one
platform-limited symbolic-link skip; they cover exact pass, missing, extra,
unsafe, duplicate, unsorted, unsupported configuration, non-recursive glob,
untracked overlay, tracked deletion, link rejection, digest drift, privacy,
and read-only behavior. The focused package, initializer, and documentation
run passes all 70 tests. The complete supported Python 3.11 suite passes 1102
tests with 5 platform-limited skips in 167.313 seconds. Task governance is
`PASS=3 WARN=1 FAIL=0 ADVISORY=3`; repository governance is
`PASS=26 WARN=2 FAIL=0 ADVISORY=4`. Final captured scope is
`PASS=23 PRESERVED=33 FAIL=0 TOTAL=56`; both JSON checks and
`git diff --check` pass.

Distinct native current-Agent advisory review
`srv-7256959ad87fdc6eff08d2835b596493` found the selected requirement,
supported-subset boundary, exact identities, scope, privacy, and denied
authority consistent. It retained cross-version artifact parity, future
journey behavior, adoption, reliability improvement, time savings, causal
benefit, and return on investment as unknown. This is not independent
assurance. The native task completion-record tool is unavailable in this
session, so no completion record is claimed or fabricated.

No package declaration, runtime source, consumer, user configuration,
credential, build, installed artifact, model call, Git write, commit, push,
publication, release, deployment, or external write occurred. The manifest
and this evidence grant none of those authorities.
