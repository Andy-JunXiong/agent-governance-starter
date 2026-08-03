import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
IMAGE_URL = (
    "https://andy-junxiong.github.io/agent-governance-starter/"
    "assets/agentgov-social-preview.jpg"
)


def jpeg_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if not data.startswith(b"\xff\xd8"):
        raise ValueError("not a JPEG")

    position = 2
    start_of_frame = {
        0xC0,
        0xC1,
        0xC2,
        0xC3,
        0xC5,
        0xC6,
        0xC7,
        0xC9,
        0xCA,
        0xCB,
        0xCD,
        0xCE,
        0xCF,
    }
    while position + 4 < len(data):
        if data[position] != 0xFF:
            position += 1
            continue

        marker = data[position + 1]
        position += 2
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            continue

        segment_length = int.from_bytes(data[position : position + 2], "big")
        if segment_length < 2 or position + segment_length > len(data):
            raise ValueError("invalid JPEG segment")
        if marker in start_of_frame:
            height = int.from_bytes(data[position + 3 : position + 5], "big")
            width = int.from_bytes(data[position + 5 : position + 7], "big")
            return width, height
        position += segment_length

    raise ValueError("JPEG dimensions not found")


class SocialPreviewTests(unittest.TestCase):
    def test_social_preview_asset_matches_github_contract(self) -> None:
        asset = DOCS / "assets" / "agentgov-social-preview.jpg"

        self.assertTrue(asset.is_file())
        self.assertLess(asset.stat().st_size, 1_000_000)
        self.assertEqual((1280, 640), jpeg_dimensions(asset))

    def test_public_entry_pages_publish_large_image_metadata(self) -> None:
        for page_name, canonical in (
            (
                "index.html",
                "https://andy-junxiong.github.io/agent-governance-starter/",
            ),
            (
                "portfolio.html",
                "https://andy-junxiong.github.io/agent-governance-starter/portfolio.html",
            ),
        ):
            with self.subTest(page=page_name):
                content = (DOCS / page_name).read_text(encoding="utf-8")
                self.assertIn(f'href="{canonical}"', content)
                self.assertIn(f'property="og:url"\n      content="{canonical}"', content)
                self.assertIn(f'property="og:image"\n      content="{IMAGE_URL}"', content)
                self.assertIn('property="og:image:width" content="1280"', content)
                self.assertIn('property="og:image:height" content="640"', content)
                self.assertIn('name="twitter:card" content="summary_large_image"', content)
                self.assertIn(f'name="twitter:image"\n      content="{IMAGE_URL}"', content)

    def test_reference_layout_uses_the_same_absolute_preview(self) -> None:
        layout = (DOCS / "_layouts" / "reference.html").read_text(encoding="utf-8")

        self.assertIn(
            "https://andy-junxiong.github.io/agent-governance-starter{{ page.url }}",
            layout,
        )
        self.assertEqual(2, layout.count(IMAGE_URL))
        self.assertIn('name="twitter:card" content="summary_large_image"', layout)

    def test_readme_uses_the_social_preview_asset(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("docs/assets/agentgov-social-preview.jpg", readme)


if __name__ == "__main__":
    unittest.main()
