import hashlib
import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from agentgov.software_update import (
    SoftwareUpdateError,
    download_https,
    download_verified_wheel,
    install_wheel_with_pipx,
)


class FakeResponse:
    def __init__(self, payload: bytes, url: str = "https://github.com/asset") -> None:
        self.stream = io.BytesIO(payload)
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size: int) -> bytes:
        return self.stream.read(size)

    def geturl(self) -> str:
        return self.url


class SoftwareDownloadTests(unittest.TestCase):
    def test_https_download_returns_digest(self) -> None:
        payload = b"verified wheel"
        with TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "artifact.whl"
            with patch(
                "urllib.request.urlopen",
                return_value=FakeResponse(payload),
            ):
                digest = download_https(
                    "https://github.com/example",
                    destination,
                    maximum_bytes=1024,
                )

            self.assertEqual(destination.read_bytes(), payload)

        self.assertEqual(digest, hashlib.sha256(payload).hexdigest())

    def test_digest_mismatch_removes_download(self) -> None:
        payload = b"tampered"
        artifact = {
            "url": "https://github.com/example",
            "sha256": "0" * 64,
        }
        with TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "artifact.whl"
            with patch(
                "urllib.request.urlopen",
                return_value=FakeResponse(payload),
            ):
                with self.assertRaises(SoftwareUpdateError):
                    download_verified_wheel(artifact, destination)

            self.assertFalse(destination.exists())

    def test_failed_pipx_install_verifies_previous_command(self) -> None:
        failed = type("Result", (), {"returncode": 1, "stdout": "", "stderr": "failed"})()
        preserved = type(
            "Result",
            (),
            {"returncode": 0, "stdout": "agentgov 0.1.0\n", "stderr": ""},
        )()
        with patch("shutil.which", side_effect=["pipx", "agentgov"]), patch(
            "subprocess.run",
            side_effect=[failed, preserved],
        ):
            with self.assertRaisesRegex(
                SoftwareUpdateError,
                "previous AgentGov remains executable",
            ):
                install_wheel_with_pipx(
                    Path("candidate.whl"),
                    expected_version="0.1.1",
                )


if __name__ == "__main__":
    unittest.main()
