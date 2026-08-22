from __future__ import annotations

import re
import unittest
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "docs/evidence-freshness-rehearsal.html"
SOURCE_RECORD = ROOT / "governance/evidence/release-candidate-0-3-0rc1.json"
SOURCE_SPEC = ROOT / "docs/specs/evidence-freshness-v1.md"


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.elements: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.elements.append((tag, dict(attrs)))


class EvidenceFreshnessRehearsalPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = PAGE.read_text(encoding="utf-8")
        cls.parser = _PageParser()
        cls.parser.feed(cls.text)
        script_match = re.search(r"<script>(.*?)</script>", cls.text, re.DOTALL)
        assert script_match is not None
        cls.script = script_match.group(1)

    def _embedded_source(self, element_id: str) -> str:
        match = re.search(
            rf'<pre[^>]+id="{re.escape(element_id)}"[^>]*>(.*?)</pre>',
            self.text,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        return unescape(match.group(1))

    def test_page_is_self_contained_local_and_responsive(self) -> None:
        self.assertIn('<html lang="zh-CN">', self.text)
        self.assertIn('name="viewport"', self.text)
        self.assertIn("default-src 'none'", self.text)
        self.assertIn("@media (max-width: 760px)", self.text)
        self.assertIn("@media (prefers-reduced-motion: reduce)", self.text)
        self.assertNotRegex(self.text, r'(?:href|src)="https?://')
        self.assertNotIn("C:\\Users", self.text)

    def test_start_answer_and_result_controls_are_complete(self) -> None:
        ids = {
            attrs["id"]
            for _, attrs in self.parser.elements
            if attrs.get("id") is not None
        }
        for expected in (
            "eligibility",
            "start-button",
            "clock",
            "progress-label",
            "rehearsal-form",
            "participant-questions",
            "first-uncertainty",
            "assistance-notes",
            "confidence",
            "result-output",
            "copy-result",
            "select-result",
            "reset-page",
        ):
            self.assertIn(expected, ids)
        for index in range(1, 7):
            self.assertIn(f"q{index}", ids)
            self.assertRegex(self.text, rf'<label for="q{index}">')

        required_radio_names = {
            attrs.get("name")
            for tag, attrs in self.parser.elements
            if tag == "input" and attrs.get("type") == "radio"
        }
        self.assertEqual(required_radio_names, {"extra_sources", "assistance"})

    def test_timer_progress_and_raw_result_contract_are_present(self) -> None:
        for token in (
            "performance.now()",
            "new Date().toISOString()",
            "window.setInterval",
            "form.checkValidity()",
            'event.preventDefault()',
            '用时（秒）',
            '六个原始答案',
            '参与者问题',
            '第一次不确定',
            '查看页面外资料',
            '观察员协助',
            '信心：',
        ):
            self.assertIn(token, self.text)

    def test_page_has_no_scoring_answer_key_persistence_or_network_logic(self) -> None:
        for forbidden in (
            "expectedAnswers",
            "correctAnswers",
            "calculateScore",
            "localStorage",
            "sessionStorage",
            "document.cookie",
            "fetch(",
            "XMLHttpRequest",
            "WebSocket",
            "sendBeacon",
        ):
            self.assertNotIn(forbidden, self.text)
        self.assertNotRegex(self.text, r"<form[^>]+action=")
        self.assertIn("这里没有标准答案，也不会自动评分", self.text)
        self.assertIn("本页面未评分、未上传、未持久化", self.text)

    def test_friendly_record_layer_preserves_every_source_field(self) -> None:
        for key_path in (
            "contract",
            "schema_version",
            "evidence_id",
            "applicability.status",
            "applicability.reason",
            "evidence_refs",
            "review.reviewed_at",
            "review.review_due_on",
            "validity.expires_on",
            "validity.policy_status",
            "validity.policy_ref",
            "invalidation.declared_events",
            "invalidation.observed_events",
        ):
            self.assertIn(f'<code class="field-key">{key_path}</code>', self.text)

        self.assertNotIn("真实记录摘要", self.text)
        self.assertNotIn("规则速读", self.text)
        self.assertIn("[]（空数组）", self.text)

    def test_friendly_spec_layer_covers_every_source_section(self) -> None:
        for section in (
            "Purpose",
            "Record",
            "First repository trial",
            "Status semantics",
            "Command",
            "Privacy and authority",
        ):
            self.assertIn(f'data-source-section="{section}"', self.text)
        for status in ("PASS", "WARN", "FAIL", "ADVISORY", "NOT_APPLICABLE"):
            self.assertIn(f"<td>{status}</td>", self.text)

    def test_concept_map_distinguishes_paths_events_and_exact_matching(self) -> None:
        concept_match = re.search(
            r'<article class="concept-map".*?</article>', self.text, re.DOTALL
        )
        self.assertIsNotNone(concept_match)
        concept = concept_match.group(0)

        for concept_type in (
            "reference-path",
            "declared-event",
            "observed-event",
        ):
            self.assertIn(f'data-concept="{concept_type}"', concept)
        for source_key in (
            "evidence_refs",
            "validity.policy_ref",
            "invalidation.declared_events",
            "invalidation.observed_events",
        ):
            self.assertIn(source_key, concept)
        for phrase in (
            "路径 ≠ 事件名",
            "检查器不会自动发现或填写",
            "负责任的生产者",
            "只有观察名称精确属于声明集合",
            "相似名称不算",
        ):
            self.assertIn(phrase, concept)

        for answer_identifier in (
            "bundled-compatibility-baseline-changed",
            "release-candidate-notes-corrected",
            "release-channel-policy-changed",
        ):
            self.assertNotIn(answer_identifier, concept)
        self.assertLess(self.text.index('id="concept-map"'), self.text.index('id="record-title"'))

    def test_audit_disclosures_embed_the_exact_repository_sources(self) -> None:
        self.assertEqual(
            self._embedded_source("source-record-json"),
            SOURCE_RECORD.read_text(encoding="utf-8"),
        )
        self.assertEqual(
            self._embedded_source("source-spec-markdown"),
            SOURCE_SPEC.read_text(encoding="utf-8"),
        )
        self.assertIn("展开：完整原始 JSON", self.text)
        self.assertIn("展开：完整规范原文", self.text)
        self.assertIn("核对层不参与评分", self.text)

    def test_clipboard_has_visible_manual_fallback(self) -> None:
        self.assertIn("navigator.clipboard.writeText", self.script)
        self.assertIn('document.execCommand("copy")', self.script)
        self.assertIn("浏览器拒绝自动复制", self.text)
        self.assertIn("点击“选中文本”", self.text)
        self.assertIn('id="result-output" readonly', self.text)


if __name__ == "__main__":
    unittest.main()
