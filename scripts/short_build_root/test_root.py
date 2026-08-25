from __future__ import annotations

from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from scripts.short_build_root import (
    BuildRootError,
    create_evidence_receipt,
    create_short_build_root,
    remove_short_build_root,
    remove_short_build_root_after_evidence,
)


PACKAGED_TEMPLATE_TARGET = (
    "s/build/bdist.win-amd64/wheel/"
    "agent_governance_starter-0.3.0rc1.data/data/share/"
    "agent-governance-starter/templates/"
    "example-capability.input.schema.template.json"
)


class ShortBuildRootTests(unittest.TestCase):
    @staticmethod
    def _system_temp(base: Path):
        return mock.patch(
            "scripts.short_build_root.root.tempfile.gettempdir",
            return_value=str(base),
        )

    @staticmethod
    def _identity(value: bytes) -> str:
        return "sha256:" + hashlib.sha256(value).hexdigest()

    def test_creation_is_short_unique_direct_child_and_cleanup_is_exact(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            with self._system_temp(base):
                first = create_short_build_root([PACKAGED_TEMPLATE_TARGET])
                second = create_short_build_root([PACKAGED_TEMPLATE_TARGET])

                self.assertEqual(base, first.path.parent)
                self.assertEqual(base, second.path.parent)
                self.assertNotEqual(first.path, second.path)
                self.assertRegex(first.root_name, r"^agv-[0-9a-f]{8}$")
                self.assertLessEqual(len(str(first.path)), 72)
                self.assertLessEqual(first.longest_projected_length, 240)

                remove_short_build_root(first)
                remove_short_build_root(second)
                self.assertEqual([], list(base.iterdir()))

    def test_unsafe_projected_paths_fail_before_any_write(self) -> None:
        unsafe = (
            "",
            " leading/path",
            "trailing/path ",
            "/absolute/path",
            "C:/absolute/path",
            "../escape",
            "safe/../escape",
            "safe\\windows",
            "safe/\x00control",
        )
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            with self._system_temp(base):
                for value in unsafe:
                    with self.subTest(value=repr(value)):
                        with self.assertRaises(BuildRootError):
                            create_short_build_root([value])
                        self.assertEqual([], list(base.iterdir()))

    def test_path_budget_and_long_temporary_base_fail_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            with self._system_temp(base):
                with self.assertRaisesRegex(BuildRootError, "projected build path"):
                    create_short_build_root(
                        [PACKAGED_TEMPLATE_TARGET],
                        maximum_projected_path=len(str(base)) + 20,
                    )
                with self.assertRaisesRegex(BuildRootError, "temporary base is too long"):
                    create_short_build_root(
                        ["s/file"],
                        maximum_root_path=len(str(base)),
                    )
                self.assertEqual([], list(base.iterdir()))

    def test_invalid_token_and_exhausted_collisions_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            with self._system_temp(base):
                with mock.patch(
                    "scripts.short_build_root.root.secrets.token_hex",
                    return_value="NOT-HEX",
                ):
                    with self.assertRaisesRegex(BuildRootError, "eight lowercase hex"):
                        create_short_build_root(["s/file"])
                (base / "agv-deadbeef").mkdir()
                with mock.patch(
                    "scripts.short_build_root.root.secrets.token_hex",
                    return_value="deadbeef",
                ):
                    with self.assertRaisesRegex(BuildRootError, "unique short build-root"):
                        create_short_build_root(["s/file"])
                self.assertEqual(
                    ["agv-deadbeef"], [item.name for item in base.iterdir()]
                )

    def test_repr_and_normalized_report_do_not_expose_host_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            with self._system_temp(base):
                root = create_short_build_root([PACKAGED_TEMPLATE_TARGET])
                rendered = repr(root)
                report = json.dumps(root.normalized_report(), sort_keys=True)

                self.assertNotIn(str(base), rendered)
                self.assertNotIn(str(base), report)
                self.assertNotIn(str(root.path), rendered)
                self.assertNotIn(str(root.path), report)
                self.assertNotIn(root.root_name, report)
                self.assertEqual(
                    "agv-<8-hex>", root.normalized_report()["root_name_pattern"]
                )
                self.assertFalse(
                    any(root.normalized_report()["authority_boundary"].values())
                )
                remove_short_build_root(root)

    def test_cleanup_rejects_forged_out_of_boundary_and_missing_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            with self._system_temp(base):
                root = create_short_build_root(["s/file"])
                outside = base.parent / "agv-deadbeef"
                forged = replace(root, path=outside, root_name="agv-deadbeef")
                with self.assertRaisesRegex(BuildRootError, "direct temporary child"):
                    remove_short_build_root(forged)
                remove_short_build_root(root)
                with self.assertRaisesRegex(BuildRootError, "existing directory"):
                    remove_short_build_root(root)

    def test_cleanup_rejects_a_symbolic_link_root_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            target = base / "target"
            target.mkdir()
            link = base / "agv-deadbeef"
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symbolic links unavailable: {exc}")
            with self._system_temp(base), mock.patch(
                "scripts.short_build_root.root.secrets.token_hex",
                return_value="cafebabe",
            ):
                root = create_short_build_root(["s/file"])
                forged = replace(root, path=link, root_name=link.name)
                with self.assertRaisesRegex(BuildRootError, "symbolic link"):
                    remove_short_build_root(forged)
                remove_short_build_root(root)
                self.assertTrue(target.is_dir())

    def test_evidence_gated_cleanup_ignores_tty_and_closed_input(self) -> None:
        class TtyInput(io.StringIO):
            def isatty(self) -> bool:
                return True

        input_states = (TtyInput("unused"), io.StringIO("redirected"), io.StringIO())
        input_states[-1].close()
        for index, input_state in enumerate(input_states):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as directory:
                base = Path(directory).resolve()
                repository = base / "repository"
                repository.mkdir()
                evidence = repository / "evidence.md"
                content = f"durable evidence {index}".encode("utf-8")
                evidence.write_bytes(content)
                with self._system_temp(base):
                    root = create_short_build_root(["s/file"])
                    receipt = create_evidence_receipt(
                        repository=repository,
                        relative_path="evidence.md",
                        expected_sha256=self._identity(content),
                    )
                    with mock.patch("sys.stdin", input_state), mock.patch(
                        "builtins.input",
                        side_effect=AssertionError("stdin must not be read"),
                    ), mock.patch(
                        "scripts.short_build_root.root.remove_short_build_root",
                        wraps=remove_short_build_root,
                    ) as remove:
                        result = remove_short_build_root_after_evidence(root, receipt)

                remove.assert_called_once_with(root)
                self.assertTrue(result.evidence_revalidated)
                self.assertTrue(result.cleanup_removed)
                self.assertFalse(root.path.exists())
                self.assertFalse(result.normalized_report()["reads_stdin"])
                self.assertFalse(result.normalized_report()["depends_on_tty"])

    def test_evidence_receipt_rejects_unsafe_or_unproven_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            repository = base / "repository"
            repository.mkdir()
            evidence = repository / "evidence.md"
            evidence.write_bytes(b"durable")
            evidence_directory = repository / "not-a-file"
            evidence_directory.mkdir()
            with self._system_temp(base):
                root = create_short_build_root(["s/file"])
                invalid = (
                    ("missing.md", self._identity(b"durable")),
                    (str(evidence.resolve()), self._identity(b"durable")),
                    ("../evidence.md", self._identity(b"durable")),
                    ("not-a-file", self._identity(b"durable")),
                    ("evidence.md", "SHA256:" + "0" * 64),
                    ("evidence.md", "sha256:" + "0" * 64),
                )
                for relative_path, identity in invalid:
                    with self.subTest(relative_path=relative_path, identity=identity):
                        with self.assertRaises(BuildRootError):
                            create_evidence_receipt(
                                repository=repository,
                                relative_path=relative_path,
                                expected_sha256=identity,
                            )
                        self.assertTrue(root.path.is_dir())
                remove_short_build_root(root)

    def test_evidence_is_revalidated_before_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            repository = base / "repository"
            repository.mkdir()
            evidence = repository / "evidence.md"
            evidence.write_bytes(b"first durable bytes")
            with self._system_temp(base):
                root = create_short_build_root(["s/file"])
                receipt = create_evidence_receipt(
                    repository=repository,
                    relative_path="evidence.md",
                    expected_sha256=self._identity(b"first durable bytes"),
                )
                evidence.write_bytes(b"later bytes")
                with mock.patch(
                    "scripts.short_build_root.root.remove_short_build_root",
                    wraps=remove_short_build_root,
                ) as remove:
                    with self.assertRaisesRegex(BuildRootError, "digest does not match"):
                        remove_short_build_root_after_evidence(root, receipt)
                remove.assert_not_called()
                self.assertTrue(root.path.is_dir())
                remove_short_build_root(root)

    def test_evidence_receipt_rejects_symbolic_links_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            repository = base / "repository"
            repository.mkdir()
            target = repository / "target.md"
            target.write_bytes(b"durable")
            link = repository / "evidence.md"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symbolic links unavailable: {exc}")
            with self.assertRaisesRegex(BuildRootError, "symbolic links"):
                create_evidence_receipt(
                    repository=repository,
                    relative_path="evidence.md",
                    expected_sha256=self._identity(b"durable"),
                )

    def test_evidence_reports_do_not_expose_host_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            repository = base / "repository"
            repository.mkdir()
            evidence = repository / "evidence.md"
            evidence.write_bytes(b"durable")
            receipt = create_evidence_receipt(
                repository=repository,
                relative_path="evidence.md",
                expected_sha256=self._identity(b"durable"),
            )
            rendered = repr(receipt)
            report = json.dumps(receipt.normalized_report(), sort_keys=True)
            self.assertNotIn(str(base), rendered)
            self.assertNotIn(str(base), report)
            self.assertNotIn(str(repository), rendered)
            self.assertNotIn(str(repository), report)
            self.assertFalse(receipt.normalized_report()["authorizes_cleanup"])


if __name__ == "__main__":
    unittest.main()
