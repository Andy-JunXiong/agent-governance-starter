# Agent Governance interview walkthrough

This guide is the repository source for a five-to-ten-minute interview demo.
Use the [English web guide](interview-guide.html) or the
[中文网页讲解](interview-guide.zh-CN.html) when presenting from GitHub Pages.

## Thirty-second positioning

Agent Governance is a repository-native control layer for AI-assisted software
development. It connects a human-owned requirement to architecture context,
bounded file scope, fresh validation evidence, and an explicit completion
review. Deterministic checks report facts; advisory findings preserve decisions
for people. No report or task record authorizes merge, publication, release, or
deployment.

Stable `0.2.1` provides the installable repository-governance CLI. Published
prerelease `0.3.0rc1` and newer development source extend that foundation into
coding-agent lifecycle governance. Do not present development-source behavior
as stable package behavior.

## Five-to-ten-minute story

1. **Problem — 60 seconds.** AI coding can be fast while task ownership, scope,
   evidence, and authority remain implicit. Passing tests do not answer who
   admitted the work or whether the tested change still matches it.
2. **Architecture — 90 seconds.** Repository files own the truth. A small Python
   CLI performs deterministic checks. Host adapters mediate native human
   decisions. Humans retain semantic and consequential authority.
3. **Stable demo — 2 minutes.** Open the
   [sample report](demo-governance-report.html), filter PASS/WARN/FAIL/ADVISORY,
   and explain that the report is an illustrative `0.3.0rc1` fixture snapshot,
   not proof of the newest development workflow.
4. **Development journey — 2 minutes.** Show one admitted task flowing through
   alignment, exact scope, fresh validation, advisory self-review, status, and
   a paused task. Use [STATUS.md](../STATUS.md) and the
   [evidence portfolio](portfolio.html) as the current evidence map.
5. **Latest safety slice — 90 seconds.** Explain the development-source replay
   chain: immutable reservation, create-only claim, then a separate immutable
   recovery record. Recovery preserves the original claim, creates no
   replacement owner, and grants no replay authority.
6. **Close honestly — 30 seconds.** Name what is not proven: real-consumer
   recovery, authenticated operator identity, network-filesystem exclusivity,
   power-loss durability, and interview-outcome improvement.

## Architecture map

```text
Human intent
  -> task admission / alignment
  -> repository-owned architecture context
  -> deterministic scope observation
  -> fresh validation bound to the change snapshot
  -> advisory review and human completion decision
  -> PR/CI independently replay deterministic facts
```

Responsibility is deliberately split:

- **Core contracts:** portable task, finding, evidence, and authority semantics.
- **Policy:** risk and routing decisions owned by the repository.
- **Adapters:** host-specific interaction and native decision mediation.
- **Product surfaces:** CLI, Monitor, HTML reports, and public documentation.
- **Humans:** requirements, architecture judgment, exceptions, Git, release,
  deployment, and other consequential authority.

## Reproducible demo script

Install the published stable wheel in an isolated environment:

```powershell
pipx install "https://github.com/Andy-JunXiong/agent-governance-starter/releases/download/v0.2.1/agent_governance_starter-0.2.1-py3-none-any.whl"
agentgov --version
agentgov inspect .
agentgov check repository .
```

When demonstrating current development source from the starter repository:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov --help
python -m unittest discover -s tests -v
```

The replay-safety commands are preview-first and development-source only:

```powershell
python -m agentgov reserve replay-correlation path/to/reservation-plan.json --repository path/to/consumer --format json
python -m agentgov claim replay-correlation path/to/claim-plan.json --repository path/to/consumer --format json
python -m agentgov recover replay-claim path/to/recovery-plan.json --repository path/to/consumer --format json
```

Do not use `--apply` in an interview unless a separate disposable-consumer task
and human confirmation explicitly authorize that write. Preview results do not
authorize replay, Git operations, release, or deployment.

## Evidence to open

- [Product home](index.html): concise product and interview story.
- [Evidence portfolio](portfolio.html): lifecycle, cases, and claim boundaries.
- [Sample report](demo-governance-report.html): interactive finding semantics.
- [README](../README.md): full commands, architecture, and project navigation.
- [Current status](../STATUS.md): latest validated repository reality.
- [Replay preflight and recovery guide](clean-target-replay-preflight.md): exact
  reservation, claim, and recovery boundaries.
- [Harness Contract v1](harness-contract-v1.md): privacy-bounded replay evidence.

## Likely interviewer questions

### Why is this not just another linter?

Linters usually validate code or configuration. Agent Governance also binds the
human-owned task, allowed path scope, architecture context, validation snapshot,
advisory review, and authority boundary. It still refuses to claim semantic
correctness from static checks.

### Why keep PASS, WARN, FAIL, and ADVISORY separate?

A single score would hide the difference between a satisfied contract, honest
incompleteness, a deterministic failure, and a judgment that only a person can
make.

### What is the strongest engineering evidence?

Strict schemas and dependency-free Python implementations are protected by
fixture-driven tests, race and stale-evidence tests, complete regression runs,
scope reconciliation, secret-safety checks, and explicit advisory reviews.

### What would you build next?

The next product decision is not yet authorized. The strongest candidate is a
recovered-correlation re-ownership contract before any claim-to-Harness consume
transition. It must preserve the create-only claim and immutable recovery
evidence rather than silently taking ownership.

## Honest limitations

- Static checks cannot prove requirement value, architecture quality, reviewer
  comprehension, or test sufficiency.
- Stable `0.2.1` does not contain the newest development-source lifecycle.
- The sample report is illustrative and sanitized.
- Recovery does not authenticate the individual operator or authorize replay.
- No external evidence proves that this documentation improves interview
  outcomes.

---

# 中文面试讲解

## 30 秒定位

Agent Governance 是面向 AI 辅助开发的仓库原生控制层。它把人工拥有的需求、
架构上下文、允许修改的文件范围、与变更快照绑定的新鲜验证证据，以及明确的
完成复核连接起来。确定性检查只报告事实；建议性发现把判断留给人。任何报告
或任务记录都不自动授权合并、发布、release 或部署。

稳定版 `0.2.1` 提供可安装的仓库治理 CLI；公开预发行版 `0.3.0rc1` 与更新的
开发源继续扩展 Coding Agent 生命周期治理。演示时必须清楚区分稳定能力和开发
源能力。

## 5–10 分钟演示顺序

1. 说明问题：AI 写代码很快，但需求归属、范围、证据和权限经常仍是隐含的。
2. 说明架构：仓库文件拥有事实，Python CLI 检查确定性契约，Adapter 负责宿主
   交互，人保留语义判断和高后果权限。
3. 打开[示例报告](demo-governance-report.zh-CN.html)，说明四种 finding 状态。
4. 用 [STATUS.md](../STATUS.md) 和[证据作品集](portfolio.html)展示任务如何经过
   对齐、范围验证、完整回归、自审和暂停。
5. 展示最新开发链：不可变 reservation、create-only claim、单独的不可变
   recovery record。恢复不删除原 claim、不创建新 owner，也不授权 replay。
6. 主动说明未知项：真实消费者恢复、身份认证、网络文件系统独占语义、断电
   耐久性，以及文档是否改善面试结果。

## 推荐结尾

下一项产品需求尚未授权。最自然的候选是在 claim-to-Harness consume 之前定义
恢复后 correlation 的重新取得所有权契约，同时保留 create-only claim 与
immutable recovery evidence 的不可变事实。
