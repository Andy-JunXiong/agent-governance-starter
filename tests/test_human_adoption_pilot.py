import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "docs/human-adoption-pilot.md"
RECORD = ROOT / "docs/human-adoption-record.template.md"
INTERNAL_REHEARSAL = (
    ROOT / "docs/adoption-records/2026-07-13-internal-operator-01.md"
)
CASE_STUDY = ROOT / "docs/case-study.md"
README = ROOT / "README.md"


class HumanAdoptionPilotContractTests(unittest.TestCase):
    def test_pilot_separates_human_timing_from_automated_validation(self) -> None:
        text = PILOT.read_text(encoding="utf-8")

        self.assertIn("The participant, not an agent", text)
        self.assertIn("## Setup outside the timer", text)
        self.assertIn("## Timed pilot", text)
        self.assertIn("pastes the complete block, and presses Enter", text)
        self.assertIn("starts a visible stopwatch", text)
        self.assertIn("invalidates the timing evidence", text)
        self.assertIn("Do not stop at initialization alone", text)
        self.assertIn("not universal\nproof", text)

    def test_pilot_preserves_honest_warning_and_authority_boundaries(self) -> None:
        text = PILOT.read_text(encoding="utf-8")

        self.assertIn("PASS=12 WARN=3 FAIL=0 ADVISORY=1", text)
        self.assertIn("The pilot does not require `WARN=0`", text)
        self.assertIn("merge, publish, or deploy", text)
        self.assertIn("`pass`", text)
        self.assertIn("`assisted`", text)
        self.assertIn("`needs-revision`", text)
        self.assertIn("`invalid`", text)

    def test_record_captures_timing_friction_assistance_and_final_counts(self) -> None:
        text = RECORD.read_text(encoding="utf-8")

        for required in (
            "Timed elapsed duration:",
            "Final `PASS` count:",
            "Final `WARN` count:",
            "Final `FAIL` count:",
            "Facilitator interventions",
            "Product friction:",
            "Environment or installation friction:",
            "Classification: pass / assisted / needs-revision / invalid",
        ):
            self.assertIn(required, text)

    def test_internal_rehearsal_is_not_presented_as_adoption_evidence(self) -> None:
        record = INTERNAL_REHEARSAL.read_text(encoding="utf-8")
        case_study = CASE_STUDY.read_text(encoding="utf-8")

        self.assertTrue(record.startswith("# Internal adoption rehearsal record\n"))
        self.assertIn("Invalid as human adoption evidence", record)
        self.assertIn("not independent user validation", record)
        self.assertIn(
            "An internal usability rehearsal did not establish the ten-minute "
            "adoption claim",
            case_study,
        )
        self.assertNotIn("The first internal human-adoption pilot", case_study)

    def test_readme_links_the_human_pilot_and_record_template(self) -> None:
        text = README.read_text(encoding="utf-8")

        self.assertIn("docs/human-adoption-pilot.md", text)
        self.assertIn("docs/human-adoption-record.template.md", text)
        self.assertIn("python -m pip install --no-deps .", text)
        self.assertIn("paste the block into the\nterminal and press Enter", text)
        self.assertIn("does not mean governance is\ncomplete", text)
        self.assertIn(
            "No\ncheck result authorizes an agent to merge, publish, release, or deploy",
            text,
        )


if __name__ == "__main__":
    unittest.main()
