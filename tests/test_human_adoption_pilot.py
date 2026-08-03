import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "docs/human-adoption-pilot.md"
RECORD = ROOT / "docs/human-adoption-record.template.md"
HANDOUT = ROOT / "docs/uncoached-onboarding-handout.md"
INTERNAL_REHEARSAL = (
    ROOT / "docs/adoption-records/2026-07-13-internal-operator-01.md"
)
CASE_STUDY = ROOT / "docs/case-study.md"
README = ROOT / "README.md"


class HumanAdoptionPilotContractTests(unittest.TestCase):
    def test_pilot_separates_human_timing_from_automated_validation(self) -> None:
        text = PILOT.read_text(encoding="utf-8")

        self.assertIn("first-time human participant", text)
        self.assertIn("## Evidence boundary", text)
        self.assertIn("## Facilitator setup", text)
        self.assertIn("must not type", text)
        self.assertIn("Start the timer", text)
        self.assertIn("Automated tests", text)
        self.assertIn("not human usability evidence", text)
        self.assertIn("not universal proof", text)

    def test_pilot_preserves_honest_warning_and_authority_boundaries(self) -> None:
        text = PILOT.read_text(encoding="utf-8")

        self.assertIn("doctor", text)
        self.assertIn("onboard --dry-run", text)
        self.assertIn("exact ADOPT", text)
        self.assertIn("automatic first repository check", text)
        self.assertIn("Preserve wrong turns", text)
        self.assertIn("merge/release authority", text)
        self.assertIn("`pass`", text)
        self.assertIn("`assisted`", text)
        self.assertIn("`needs-revision`", text)
        self.assertIn("`invalid`", text)

    def test_record_captures_timing_friction_assistance_and_final_counts(self) -> None:
        text = RECORD.read_text(encoding="utf-8")

        for required in (
            "Total elapsed duration:",
            "Installation duration:",
            "Guided-adoption duration:",
            "Final `PASS` count:",
            "Final `WARN` count:",
            "Final `FAIL` count:",
            "Exact confirmation entered:",
            "Facilitator interventions",
            "Product friction:",
            "Environment or installation friction:",
            "Classification: pass / assisted / needs-revision / invalid",
        ):
            self.assertIn(required, text)

    def test_participant_handout_is_bounded_and_contains_no_live_coaching(
        self,
    ) -> None:
        text = HANDOUT.read_text(encoding="utf-8")

        self.assertIn("Complete the task without asking the facilitator", text)
        self.assertIn("Run a dry-run before authorizing onboarding", text)
        self.assertIn("Do not stage, commit, push, merge", text)
        self.assertIn("the single action selected by `next`", text)
        self.assertIn("Can AgentGov authorize merge, release, or deployment?", text)
        self.assertNotIn("agentgov onboard ", text)

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
        self.assertIn("docs/uncoached-onboarding-handout.md", text)
        self.assertIn(
            'pipx install "https://github.com/Andy-JunXiong/'
            "agent-governance-starter/releases/download/v0.2.1/"
            'agent_governance_starter-0.2.1-py3-none-any.whl"',
            text,
        )
        self.assertIn("paste the block into the\nterminal and press Enter", text)
        self.assertIn("does not mean governance is\ncomplete", text)
        self.assertIn(
            "No\ncheck result authorizes an agent to merge, publish, release, or deploy",
            text,
        )


if __name__ == "__main__":
    unittest.main()
