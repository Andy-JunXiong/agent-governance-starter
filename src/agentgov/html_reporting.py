"""Self-contained HTML presentation for repository governance findings."""

from __future__ import annotations

import html
import json

from agentgov.reporting import REPORT_STATUSES, SCOPE_LIMITATIONS, repository_report_document
from agentgov.repository import FindingStatus, RepositoryReport


_DEFAULT_ACTIONS = {
    FindingStatus.FAIL: (
        "Resolve this deterministic contract violation and rerun the same check.",
        "the file or contract named by the finding",
    ),
    FindingStatus.WARN: (
        "Complete the missing configuration or record an explicit deferral with an owner.",
        "the governance area named by the check",
    ),
    FindingStatus.ADVISORY: (
        "Have an accountable human record the decision, rationale and follow-up.",
        "an ADR or other repository-owned decision record",
    ),
}


def _remediation(status: FindingStatus, check_id: str) -> tuple[str, str]:
    """Return deterministic, check-specific next action and work area."""

    if check_id == "governance:placeholders":
        return (
            "Replace each repository placeholder or explicitly defer it with an owner.",
            "AGENTS.md, ADR/invariant files and capability manifests",
        )
    if check_id.startswith("required:"):
        return (
            "Create or restore the required governance file, then review its project-specific content.",
            "the required path named in the finding",
        )
    if check_id.startswith("references:") and check_id.endswith(":evaluation"):
        return (
            "Declare the capability's evaluation bundle or retain an honest needs_seed_cases state.",
            "the capability manifest and its evaluation/ bundle",
        )
    if check_id.startswith("references:"):
        return (
            "Correct the declared repository reference and verify that the target is readable.",
            "the capability manifest, schema, caller or source path named by the finding",
        )
    if check_id.startswith("evaluation:"):
        return (
            "Add or review seed, golden and failure cases until the declared readiness is supported.",
            "the evaluation bundle named by the finding",
        )
    if check_id.startswith("agent-skill:") or check_id.startswith("agent-skills:"):
        return (
            "Correct the skill contract without weakening its triggers, safety boundaries or handoff.",
            "the corresponding agent-skills/*/SKILL.md",
        )
    if check_id.startswith("artifact:") or check_id.startswith("artifacts:"):
        return (
            "Review the source change and deliberately regenerate the artifact if the change is accepted.",
            "the capability artifact and its declared source files",
        )
    if check_id == "governance:human-review":
        return (
            "Confirm the real approval and escalation boundary with an accountable owner.",
            "a repository ADR or equivalent decision record",
        )
    return _DEFAULT_ACTIONS[status]

_ZH_REPLACEMENTS = {
    '<html lang="en">': '<html lang="zh-CN">',
    "Agent Governance Report - ": "Agent Governance 治理报告 - ",
    "Agent Governance</div>": "Agent Governance Starter Kit</div>",
    "Static | Read only | Local": "静态检查 | 只读 | 本地运行",
    "Repository governance, made visible": "让仓库治理变得可见",
    "Know what is checked.<br>Know what still needs a human.": "看清自动检查了什么。<br>看清哪些仍需要人决定。",
    "Connect repository policy, capability declarations, evidence readiness, and artifact integrity -- without pretending static checks can approve high-risk work.": "连接仓库规则、能力声明、证据成熟度和制品完整性，同时不假装静态检查可以批准高风险工作。",
    "<small>Repository</small>": "<small>仓库</small>",
    "This report does not authorize merge, publish, release, or deploy.": "本报告不授权合并、发布、release 或部署。",
    "How this report was made": "这份报告如何生成",
    "The local CLI inspected declared governance assets in this repository. It did not send source code to an external service.": "本地 CLI 检查了仓库中声明的治理资产，没有把源代码发送到外部服务。",
    "Repository rules and authority": "仓库规则与权威边界",
    "Durable decisions": "长期有效的决策",
    "Properties that must remain true": "必须持续成立的条件",
    "Purpose, owner and risk": "用途、负责人和风险",
    "Contracts and provenance": "契约与来源",
    "Evidence readiness": "证据成熟度",
    "Triggers, workflow and handoff": "触发条件、工作流与交接",
    "Reviewed source hashes": "审阅后的源文件哈希",
    "What it does not prove": "它不能证明什么",
    "The CLI checks declared structure, references, evidence state and drift. It does not run the AI capability, judge output quality, or approve high-risk work.": "CLI 检查声明的结构、引用、证据状态和漂移；它不运行 AI 能力、不判断输出质量，也不批准高风险工作。",
    "How to read this report": "如何阅读这份报告",
    "Use the report as a review map, not as an approval certificate.": "把报告当作审阅地图，而不是批准证书。",
    "Start with Current state": "先看当前状态",
    "See how many deterministic checks passed, warned or failed, and how many questions still need a human.": "了解多少确定性检查通过、警告或失败，以及多少问题仍需人工判断。",
    "Open What needs attention": "再看需要关注的事项",
    "Use each finding's specific next action and work area, then assign an accountable owner.": "按照每条发现的具体下一步和处理区域，指定负责人。",
    "Review All findings": "最后审阅全部发现",
    "Read the exact check, repository fact and scope limitation before making a merge, release or deployment decision.": "在决定合并、发布或部署前，阅读准确检查项、仓库事实和范围限制。",
    "Current state": "当前状态",
    "These counts summarize the repository facts found by the CLI. Select a card to filter the detailed findings table; select it again to reset.": "这些数字汇总 CLI 发现的仓库事实。选择状态卡可筛选详细发现，再次选择可重置。",
    "The declared deterministic contract was satisfied. This is not approval.": "声明的确定性契约已满足，但这不是批准。",
    "Configuration or evidence is honestly incomplete but non-blocking.": "配置或证据仍不完整，但当前非阻断。",
    "A deterministic contract is violated and must be corrected.": "确定性契约被违反，必须修正。",
    "Static checks cannot decide; an accountable human must review.": "静态检查无法决定，必须由负责人审阅。",
    "What needs attention": "需要关注什么",
    "Non-passing findings translated into accountable next actions.": "把非通过发现转换成有明确责任的下一步。",
    "<strong>Next:</strong>": "<strong>下一步：</strong>",
    "<strong>Work in:</strong>": "<strong>处理位置：</strong>",
    "How it works": "工作方式",
    "Automation checks repository facts. People retain judgment and authority.": "自动化检查仓库事实，人保留判断和授权。",
    "What PASS really means": "PASS 真正代表什么",
    "A deterministic contract was satisfied. It is not approval.": "确定性契约已满足，但这不是批准。",
    "Why WARN can be non-blocking": "为什么 WARN 可以非阻断",
    "The state is honestly incomplete and must be completed or explicitly deferred.": "状态被如实标记为不完整，必须完成或明确延期。",
    "What ADVISORY means": "ADVISORY 代表什么",
    "Static analysis cannot make this judgment. An accountable human must review it.": "静态分析无法作出判断，必须由负责人审阅。",
    "All findings": "全部发现",
    "Status</th><th>Check</th><th>Finding": "状态</th><th>检查项</th><th>发现",
    "Scope limitations": "范围限制",
    "Embedded machine-readable report": "内嵌机器可读报告",
    "Generated locally | No governance score | No external network requests": "本地生成 | 不计算治理分数 | 无外部网络请求",
}


def _localize_html(content: str, language: str) -> str:
    if language == "en":
        return content
    if language != "zh-CN":
        raise ValueError(f"unsupported HTML report language: {language}")
    for source, translated in _ZH_REPLACEMENTS.items():
        content = content.replace(source, translated)
    content = content.replace("Showing all ", "显示全部 ").replace(
        " findings.", " 条发现。"
    )
    return content


def render_repository_report_html(
    report: RepositoryReport,
) -> str:
    """Render a deterministic, local-only HTML explanation and report."""

    def esc(value: object) -> str:
        return html.escape(str(value), quote=True)

    cards = "".join(
        f'<button class="metric {status.value.lower()}" data-filter="{status.value}" '
        f'aria-pressed="false"><span>{status.value}</span>'
        f'<strong>{report.count(status)}</strong></button>'
        for status in REPORT_STATUSES
    )
    rows = "".join(
        f'<tr data-status="{finding.status.value}"><td><span class="badge '
        f'{finding.status.value.lower()}">{finding.status.value}</span></td>'
        f'<td><code>{esc(finding.check_id)}</code></td><td>{esc(finding.message)}</td></tr>'
        for finding in report.findings
    )
    gaps = [finding for finding in report.findings if finding.status is not FindingStatus.PASS]
    action_items = []
    for finding in gaps:
        action, work_area = _remediation(finding.status, finding.check_id)
        action_items.append(
            f'<li><span class="badge {finding.status.value.lower()}">'
            f'{finding.status.value}</span><div><code>{esc(finding.check_id)}</code>'
            f'<p><strong>Next:</strong> {esc(action)}</p>'
            f'<small><strong>Work in:</strong> {esc(work_area)}</small></div></li>'
        )
    actions = "".join(action_items) or (
        '<li><span class="badge pass">PASS</span>'
        "<p>No non-passing findings remain.</p></li>"
    )
    limitations = "".join(f"<li>{esc(item)}</li>" for item in SCOPE_LIMITATIONS)
    display_repository = report.root.name or str(report.root)
    document = repository_report_document(report)
    document["repository"] = display_repository
    machine_report = html.escape(
        json.dumps(document, ensure_ascii=False, indent=2),
        quote=False,
    )
    repository = esc(display_repository)

    content = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:">
<title>Agent Governance Report - {repository}</title>
<style>
:root{{--ink:#172033;--muted:#657187;--line:#dfe5ec;--paper:#fff;--wash:#f4f7fa;--navy:#10223f;--blue:#2864dc;--pass:#18794e;--warn:#a15c00;--fail:#c2353d;--advisory:#7253b5}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--wash);color:var(--ink);font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}}code{{font:13px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere}}
.shell{{width:min(1160px,calc(100% - 32px));margin:auto}}header{{background:var(--navy);color:white;padding:18px 0}}header .shell{{display:flex;justify-content:space-between;align-items:center;gap:16px}}.brand{{display:flex;gap:11px;align-items:center;font-weight:800}}.mark{{border:1px solid #7fa6e9;border-radius:9px;padding:4px 6px;color:#c8d9ff;font-size:11px}}.header-tools{{display:flex;align-items:center;gap:14px}}.mode{{color:#b8c7dd;font-size:11px;letter-spacing:.12em;text-transform:uppercase}}.language-switch{{display:inline-flex;gap:2px;padding:3px;border:1px solid #587097;border-radius:999px}}.language-switch a{{min-width:38px;padding:4px 8px;border-radius:999px;color:#c8d9ff;text-align:center;text-decoration:none;font-size:12px;font-weight:750}}.language-switch a[aria-current=page]{{background:white;color:var(--navy)}}
.hero{{padding:60px 0 34px;display:grid;grid-template-columns:1.25fr .75fr;gap:42px;align-items:end}}.eyebrow{{color:var(--blue);font-size:11px;font-weight:850;letter-spacing:.14em;text-transform:uppercase}}h1{{font-size:clamp(38px,6vw,66px);line-height:1.02;letter-spacing:-.055em;margin:12px 0 18px}}.lede{{max-width:720px;color:#4e5b70;font-size:18px}}
.repo{{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:22px;box-shadow:0 12px 30px #10223f12}}.repo small{{display:block;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}}.boundary{{margin-top:18px;padding-top:16px;border-top:1px solid var(--line);color:var(--fail);font-weight:750;font-size:13px}}
h2{{margin:0 0 8px;font-size:23px;letter-spacing:-.025em}}.sub{{color:var(--muted);margin:0 0 22px}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:18px 0 40px}}.metric{{appearance:none;text-align:left;background:var(--paper);border:1px solid var(--line);border-top:4px solid currentColor;border-radius:14px;padding:18px;cursor:pointer}}.metric span{{font-size:11px;font-weight:850;letter-spacing:.08em}}.metric strong{{display:block;font-size:32px;margin-top:5px}}.metric.pass{{color:var(--pass)}}.metric.warn{{color:var(--warn)}}.metric.fail{{color:var(--fail)}}.metric.advisory{{color:var(--advisory)}}.metric[aria-pressed=true]{{outline:3px solid currentColor;outline-offset:2px}}
.orientation{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:0 0 42px}}.orientation h2{{font-size:25px}}.orientation-list{{list-style:none;padding:0;margin:18px 0 0;display:grid;gap:14px}}.orientation-list li{{display:grid;grid-template-columns:34px 1fr;gap:12px;align-items:start}}.orientation-list b{{width:30px;height:30px;display:grid;place-items:center;border-radius:9px;background:#eaf0fb;color:var(--blue);font-size:11px}}.orientation-list strong{{display:block;margin-bottom:3px}}.orientation-list p{{margin:0;color:var(--muted)}}.input-list{{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin-top:18px}}.input-list div{{padding:11px 12px;border-radius:10px;background:#f7f9fc}}.input-list code{{color:var(--blue);font-weight:750}}.not-checked{{margin-top:18px;padding:14px;border-left:4px solid var(--warn);background:#fff8e9;color:#66420c}}
.legend{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:-22px 0 40px}}.legend div{{padding:13px;border-radius:12px;background:var(--paper);border:1px solid var(--line);color:var(--muted);font-size:13px}}.legend strong{{display:block;margin-bottom:4px}}.legend .pass strong{{color:var(--pass)}}.legend .warn strong{{color:var(--warn)}}.legend .fail strong{{color:var(--fail)}}.legend .advisory strong{{color:var(--advisory)}}
.grid{{display:grid;grid-template-columns:.85fr 1.15fr;gap:20px;margin-bottom:20px}}.panel{{background:var(--paper);border:1px solid var(--line);border-radius:18px;padding:26px}}.actions{{list-style:none;padding:0;margin:0;display:grid;gap:15px}}.actions li{{display:flex;gap:12px;align-items:flex-start;padding-bottom:15px;border-bottom:1px solid #edf0f4}}.actions li:last-child{{border:0}}.actions p{{margin:5px 0 2px;color:#526076}}.actions small{{display:block;color:var(--muted);line-height:1.45}}
.badge{{display:inline-block;border-radius:999px;padding:4px 8px;font-size:10px;font-weight:850;letter-spacing:.06em;white-space:nowrap}}.badge.pass{{background:#dff4e9;color:var(--pass)}}.badge.warn{{background:#fff0cf;color:var(--warn)}}.badge.fail{{background:#ffe0e2;color:var(--fail)}}.badge.advisory{{background:#eee6ff;color:var(--advisory)}}
.steps{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:22px}}.step{{background:#f7f9fc;border-radius:12px;padding:14px}}.step b{{display:block;color:var(--blue);font-size:10px;margin-bottom:4px}}details{{border-top:1px solid var(--line);padding:16px 0}}summary{{cursor:pointer;font-weight:750}}
.table-wrap{{overflow:auto}}table{{width:100%;border-collapse:collapse}}th{{text-align:left;color:var(--muted);font-size:10px;letter-spacing:.08em;text-transform:uppercase}}th,td{{padding:13px 10px;border-bottom:1px solid #e9edf2;vertical-align:top}}tr[hidden]{{display:none}}pre{{white-space:pre-wrap;word-break:break-word;background:#f7f9fc;padding:16px;border-radius:12px;font-size:12px}}footer{{padding:30px 0 46px;color:var(--muted);font-size:13px}}
.story{{padding:52px 0}}.story-head{{max-width:760px;margin-bottom:24px}}.story-head h2{{font-size:32px}}.kicker{{color:var(--blue);font-size:11px;font-weight:850;letter-spacing:.14em;text-transform:uppercase;margin-bottom:8px}}
.problem-grid,.file-grid,.role-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.story-card{{background:var(--paper);border:1px solid var(--line);border-radius:16px;padding:22px}}.story-card .number{{color:var(--blue);font-size:11px;font-weight:850}}.story-card h3{{margin:9px 0 7px;font-size:17px}}.story-card p{{color:var(--muted);margin:0}}
.case{{background:var(--navy);color:white;border-radius:24px;padding:32px;margin:10px 0 52px}}.case-label{{color:#a9c6ff;font-size:11px;font-weight:850;letter-spacing:.13em;text-transform:uppercase}}.case h2{{font-size:30px;margin:8px 0}}.case>p{{color:#c5d1e3;max-width:780px}}.compare{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:22px}}.compare article{{border-radius:15px;padding:21px;background:#ffffff0c;border:1px solid #ffffff20}}.compare h3{{margin:0 0 12px}}.compare ul{{margin:0;padding-left:19px;color:#d8e1ef}}.before h3{{color:#ffafb3}}.after h3{{color:#92e2bd}}
.file-grid{{grid-template-columns:repeat(5,1fr)}}.file-card{{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:18px}}.file-card code{{color:var(--blue);font-weight:750}}.file-card p{{font-size:13px;color:var(--muted);margin:9px 0 0}}
.engine{{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;align-items:stretch}}.engine div{{background:#eaf0fb;border-radius:13px;padding:16px;text-align:center;font-weight:750}}.engine .arrow{{background:transparent;display:grid;place-items:center;color:var(--blue);font-size:22px;padding:0}}.journey{{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;counter-reset:journey}}.journey div{{background:var(--paper);border:1px solid var(--line);border-radius:13px;padding:16px;min-height:110px}}.journey div:before{{counter-increment:journey;content:"0" counter(journey);display:block;color:var(--blue);font-size:11px;font-weight:850;margin-bottom:8px}}
.report-divider{{border-top:1px solid var(--line);margin:20px 0 50px;padding-top:54px}}.report-divider h2{{font-size:34px}}.command{{background:#101827;color:#dce8ff;border-radius:13px;padding:15px 18px;margin-top:18px;overflow:auto}}.command code{{white-space:nowrap}}
@media(max-width:900px){{.file-grid{{grid-template-columns:repeat(3,1fr)}}.journey{{grid-template-columns:repeat(3,1fr)}}}}@media(max-width:780px){{.hero,.grid,.compare,.orientation{{grid-template-columns:1fr}}.metrics{{grid-template-columns:repeat(2,1fr)}}.legend{{grid-template-columns:1fr 1fr}}.steps{{grid-template-columns:1fr 1fr}}.problem-grid,.role-grid,.file-grid{{grid-template-columns:1fr}}.engine{{grid-template-columns:1fr}}.engine .arrow{{transform:rotate(90deg)}}.journey{{grid-template-columns:1fr 1fr}}.mode{{display:none}}}}@media(max-width:460px){{.input-list,.legend{{grid-template-columns:1fr}}}}@media print{{body{{background:white}}.shell{{width:100%}}.metric{{cursor:default}}}}
</style>
</head>
<body>
<header><div class="shell"><div class="brand"><span class="mark">AG</span>Agent Governance</div><div class="mode">Static | Read only | Local</div></div></header>
<main class="shell">
<section class="hero"><div><div class="eyebrow">Repository governance, made visible</div><h1>Know what is checked.<br>Know what still needs a human.</h1><p class="lede">Connect repository policy, capability declarations, evidence readiness, and artifact integrity -- without pretending static checks can approve high-risk work.</p></div><aside class="repo"><small>Repository</small><code>{repository}</code><div class="boundary">This report does not authorize merge, publish, release, or deploy.</div></aside></section>
<section class="orientation"><div class="panel"><h2>How this report was made</h2><p class="sub">The local CLI inspected declared governance assets in this repository. It did not send source code to an external service.</p><div class="command"><code>agentgov report repository . --format html --output governance-report.html</code></div><div class="input-list"><div><code>AGENTS.md</code><br>Repository rules and authority</div><div><code>docs/adr/</code><br>Durable decisions</div><div><code>INVARIANTS.md</code><br>Properties that must remain true</div><div><code>capabilities/</code><br>Purpose, owner and risk</div><div><code>schemas + sources</code><br>Contracts and provenance</div><div><code>evaluation/</code><br>Evidence readiness</div><div><code>agent-skills/</code><br>Triggers, workflow and handoff</div><div><code>artifacts/</code><br>Reviewed source hashes</div></div><div class="not-checked"><strong>What it does not prove</strong><br>The CLI checks declared structure, references, evidence state and drift. It does not run the AI capability, judge output quality, or approve high-risk work.</div></div><div class="panel"><h2>How to read this report</h2><p class="sub">Use the report as a review map, not as an approval certificate.</p><ol class="orientation-list"><li><b>1</b><div><strong>Start with Current state</strong><p>See how many deterministic checks passed, warned or failed, and how many questions still need a human.</p></div></li><li><b>2</b><div><strong>Open What needs attention</strong><p>Use each finding's specific next action and work area, then assign an accountable owner.</p></div></li><li><b>3</b><div><strong>Review All findings</strong><p>Read the exact check, repository fact and scope limitation before making a merge, release or deployment decision.</p></div></li></ol></div></section>
<section><h2>Current state</h2><p class="sub">These counts summarize the repository facts found by the CLI. Select a card to filter the detailed findings table; select it again to reset.</p><div class="metrics">{cards}</div><div class="legend"><div class="pass"><strong>PASS</strong>The declared deterministic contract was satisfied. This is not approval.</div><div class="warn"><strong>WARN</strong>Configuration or evidence is honestly incomplete but non-blocking.</div><div class="fail"><strong>FAIL</strong>A deterministic contract is violated and must be corrected.</div><div class="advisory"><strong>ADVISORY</strong>Static checks cannot decide; an accountable human must review.</div></div></section>
<div class="grid"><section class="panel"><h2>What needs attention</h2><p class="sub">Non-passing findings translated into accountable next actions.</p><ol class="actions">{actions}</ol></section><section class="panel"><h2>How it works</h2><p class="sub">Automation checks repository facts. People retain judgment and authority.</p><div class="steps"><div class="step"><b>01 | DECLARE</b>Policy, capability, owner and risk</div><div class="step"><b>02 | CONNECT</b>Sources, schemas and evidence</div><div class="step"><b>03 | VERIFY</b>Contracts, readiness and drift</div><div class="step"><b>04 | DECIDE</b>Human review and explicit authority</div></div><details><summary>What PASS really means</summary><p>A deterministic contract was satisfied. It is not approval.</p></details><details><summary>Why WARN can be non-blocking</summary><p>The state is honestly incomplete and must be completed or explicitly deferred.</p></details><details><summary>What ADVISORY means</summary><p>Static analysis cannot make this judgment. An accountable human must review it.</p></details></section></div>
<section class="panel"><h2>All findings</h2><p class="sub" id="filter-note" aria-live="polite">Showing all {len(report.findings)} findings.</p><div class="table-wrap"><table><thead><tr><th>Status</th><th>Check</th><th>Finding</th></tr></thead><tbody>{rows}</tbody></table></div></section>
<section class="panel" style="margin-top:20px"><h2>Scope limitations</h2><ul>{limitations}</ul><details><summary>Embedded machine-readable report</summary><pre>{machine_report}</pre></details></section>
</main><footer class="shell">Generated locally | No governance score | No external network requests</footer>
<script>const b=[...document.querySelectorAll('[data-filter]')],r=[...document.querySelectorAll('tbody tr')],n=document.querySelector('#filter-note');b.forEach(x=>x.addEventListener('click',()=>{{const a=x.getAttribute('aria-pressed')==='true';b.forEach(y=>y.setAttribute('aria-pressed','false'));const f=a?null:x.dataset.filter;if(f)x.setAttribute('aria-pressed','true');r.forEach(y=>y.hidden=!!f&&y.dataset.status!==f);const c=r.filter(y=>!y.hidden).length;n.textContent=f?`Showing ${{c}} ${{f}} finding${{c===1?'':'s'}}.`:`Showing all ${{c}} findings.`}}));</script>
</body></html>
'''
    return content
