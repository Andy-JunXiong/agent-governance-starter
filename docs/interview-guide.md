# AgentGov interview guide

This is the presenter-preparation source for an AgentGov interview. The
[guided interview demo](interview-demo.html) owns what the interviewer sees;
this guide owns timing, cut points, role branches, transitions, follow-up
questions, and evidence navigation. The
[whole-project story](project-interview.html) is optional background. Use the
[English web guide](interview-guide.html) or the
[简体中文网页指南](interview-guide.zh-CN.html) while preparing.

## Before you start

- Ask which angle matters most: software and AI engineering, platform and
  infrastructure, or product and technical product.
- Open the [guided interview demo](interview-demo.html) before sharing your
  screen. It is the default interviewer-facing surface.
- Default to the two-minute route. Expand only when the interviewer asks.
- Keep the release boundary visible: stable `0.2.1` is the installable
  repository-governance CLI. Published `0.3.0rc1` and newer development
  source extend it into Coding Agent lifecycle governance.
- AgentGov cannot detect product drift automatically. It verifies bounded task
  facts; deciding whether the right product is being built remains a human
  product judgment.

## Thirty-second positioning

> AI coding agents can write code that passes tests and still do more than the
> person actually asked for. Passing tests also do not tell you whether anyone
> has approved the change to move forward.
>
> I built AgentGov to keep the task, the files allowed for it, the evidence from
> the current run, and the human decision connected inside the repository.
> Software checks the facts it can check. A person still decides what happens
> next.
>
> The harder part came later: I realised I was gradually building more around
> GitHub and delivery while moving away from the original problem I wanted
> AgentGov to solve.

**Cut point 1:** stop here when the interviewer only asks, “What did you build?”

## Two-minute default route

1. **The gap — 0:00–0:30.** A coding agent can produce good code and still do
   something the person did not ask for. Passing tests alone do not tell you
   whether it stayed inside the task, whether the result still describes the
   current code, or whether anybody approved the next step.
2. **What I built first — 0:30–0:55.** I started with the part software could
   check reliably. I built a small Python CLI that reads the task, the files
   allowed for that task, and the evidence produced during the work. It can say
   something passed, failed, or still needs a person. It does not turn those
   checks into “this change is correct.”
3. **How drift happened — 0:55–1:25.** A consumer exercise exposed installation,
   Windows path, and onboarding friction, so I improved those things. Then CI.
   Then PR workflows. The features were useful and their tests stayed green.
   But after several of my normal benefit reviews, I noticed I could explain the
   GitHub mechanics very clearly while finding it harder to connect them to the
   original business problem. I compared the accumulated work with the original
   requirement and confirmed that the product direction had drifted.
4. **What changed and what I learned — 1:25–2:00.** I kept the PR and CI work but
   moved it out of the center. The main product returned to the development
   loop: a person defines the task, the agent works inside an agreed boundary,
   the current files and tests are checked, and a person decides what happens
   next. Verification can prove a feature works; it cannot tell me whether I am
   still building the right product. I now make that product review myself
   instead of trying to automate it as another feature.

**Cut point 2:** this is the complete default answer. Stop before opening a
browser unless the interviewer asks for evidence or architecture.

## Five-to-seven-minute screen-share expansion

1. **0:00–3:00 — Run the observable scenario.** Open the
   [guided interview demo](interview-demo.html) and advance from exact human
   admission through simulated Agent overreach to `REVIEW_READY`.
2. **3:00–3:40 — Name the responsibility split.** Use the four actors already
   visible in the demo: human, simulated Agent, AgentGov, and demo script.
3. **3:40–4:30 — Take the product follow-up only when asked.** Open the
   [whole-project background](project-interview.html) to explain drift and the
   return to the development-time MVP.
4. **4:30–6:00 — Choose one technical proof.** Open the
   [artifact replay deep dive](artifact-replay-interview.html) only for an
   engineering audience. Tell the two-failure repair story; do not lead with
   hashes or the evidence taxonomy.
5. **6:00–6:30 — Trace claims if challenged.** Open the
   [evidence portfolio](portfolio.html). Use it to answer a question, not as a
   second presentation.
6. **6:30–7:00 — Close honestly.** Name the stable/development boundary and one
   relevant unknown. End with the lesson that governance preserves human
   decisions rather than replacing them.

**Cut point 3:** after the guided demo you have a complete product answer.
**Cut point 4:** after artifact replay you have a complete engineering answer.
The portfolio is optional verification, not required theater.

## Choose the role branch

### Software or AI engineering

Emphasize fail-closed boundaries, fresh evidence, deterministic versus advisory
semantics, and the two artifact-replay failures. Say explicitly that the Agent
proposed most low-level artifact repairs and that you reviewed and approved
them. Open the replay page only if asked for implementation depth.

### Platform or infrastructure

Emphasize repository-native contracts, host adapters, CI replay, authority
separation, create-only persistence, and recovery that does not silently replace
ownership. Use Airbnb as one observed workflow, not proof of broad portability.

### Product or technical product

Emphasize the repeated benefit review, verified drift, the decision to restore
the core MVP before detail work, and the limit of task-level verification.
Taxi is product-learning context; it is not a broad adoption claim.

## Architecture map

```text
Human requirement
  -> task admission
  -> repository-owned architecture context
  -> bounded implementation
  -> fresh scope and validation evidence
  -> advisory completion review
  -> human decision
  -> PR / CI replay of deterministic facts
```

The split is deliberate:

- **Core contracts** define portable task, finding, evidence, and authority
  semantics.
- **Repository policy** owns risk, routing, architecture context, and accepted
  scope.
- **Host adapters** mediate native interaction and exact human decisions.
- **Product surfaces** include the CLI, Monitor, reports, and public pages.
- **Humans** retain requirements, product and architecture judgment,
  exceptions, Git, publication, release, and deployment.

## Decision attribution to keep honest

- **Airbnb:** admission before write and preservation of the original human
  admission were human-originated decisions. Stage-specific authority was
  jointly formed. A separate completion marker was Agent-proposed and
  human-approved.
- **Artifact replay:** the fixed module plus JSON-stdin Harness boundary was
  jointly formed. Most low-level transport, manifest, readiness, and filesystem
  repairs were Agent-proposed and human-approved. Separating pre-cleanup from
  post-cleanup evidence was human-originated.
- **Observed behavior is not authorship:** a passing workflow proves only the
  bounded recorded run. It does not prove broad adoption, portability, repeated
  reliability, or independent assurance.

## Reproducible demo commands

Install the published stable wheel in an isolated environment:

```powershell
pipx install "https://github.com/Andy-JunXiong/agent-governance-starter/releases/download/v0.2.1/agent_governance_starter-0.2.1-py3-none-any.whl"
agentgov --version
agentgov inspect .
agentgov check repository .
```

When demonstrating current development source:

```powershell
$env:PYTHONPATH = "src"
python -m agentgov --help
python -m unittest discover -s tests -v
```

Do not use `--apply` during an interview unless a separate disposable-consumer
task and exact human confirmation authorize that write. Preview output grants
no replay, Git, release, or deployment authority.

## Evidence menu

- [Guided interview demo](interview-demo.html): the default shared surface.
- [Whole-project background](project-interview.html): optional product context.
- [Governed refund walkthrough](governed-refund-walkthrough.html): the
  60-to-90-second stable product example.
- [Artifact replay deep dive](artifact-replay-interview.html): the focused
  technical repair story.
- [Evidence portfolio](portfolio.html): lifecycle, cases, and claim boundaries.
- [Illustrative sample report](demo-governance-report.html): the four finding
  semantics in a sanitized `0.3.0rc1` fixture snapshot, not the newest workflow.
- [Current status](../STATUS.md): current validated repository reality.

## Likely interviewer questions

### Why is this more than a linter?

A linter normally checks code or configuration. AgentGov also binds the
human-owned task, architecture context, allowed path scope, evidence freshness,
advisory review, and authority boundary. It still refuses to infer requirement
value or semantic correctness from static checks.

### Why separate PASS, WARN, FAIL, and ADVISORY?

One score would hide the difference between a satisfied deterministic contract,
honest incompleteness, a deterministic failure, and a judgment only a person
can make.

### Why can AgentGov not detect product drift automatically?

Task-level evidence can show that implementation matches an admitted task. It
cannot decide whether a sequence of individually useful tasks still advances
the right product requirement. My repeated benefit review supplied that
cross-feature product judgment.

### What is the strongest engineering evidence?

For a compact product example, use the refund scope boundary. For engineering
depth, use the artifact replay: the restricted worker failed twice on hidden
Git dependencies, the restriction was preserved, trusted facts moved inward,
and the sole post-repair replay completed without retry.

### Who designed the artifact-replay fixes?

The fixed Harness boundary was joint. The Agent proposed most low-level repairs;
I reviewed and approved them. I personally insisted on separating pre-cleanup
and post-cleanup evidence so successful cleanup could not rewrite what was true
before cleanup.

### What would you build next?

The next product requirement is not decided or authorized by this guide. Use
the current product review in [STATUS.md](../STATUS.md), and explain that
completion is the point for a human requirement decision—not automatic feature
continuation.

## Honest limitations

- Static checks cannot prove requirement value, architecture quality,
  reviewer comprehension, or test sufficiency.
- Stable `0.2.1` does not contain the newest development-source lifecycle.
- The sample report is illustrative and sanitized.
- One Airbnb workflow and one artifact replay do not prove broad adoption,
  portability, repeated reliability, or production security.
- The replay recovery chain preserves an immutable reservation, a create-only
  claim, and immutable recovery evidence. Recovery creates no replacement owner
  and grants no replay authority.

---

# AgentGov 中文面试指南

这是你的面试准备控制台，不是给面试官阅读的主页面。
[中文引导式 Demo](interview-demo.zh-CN.html)负责面试官看到什么；这里负责时间、
停顿点、岗位分支、跳转、追问和证据路径。
[中文项目故事](project-interview.zh-CN.html)只作为可选背景。

## 开场前

- 先问对方更关心工程、平台，还是产品。
- 分享屏幕前先打开[中文引导式 Demo](interview-demo.zh-CN.html)，它是默认演示页面。
- 默认只讲两分钟；对方追问时才展开。
- 明确版本边界：稳定版 `0.2.1` 是可安装的仓库治理 CLI；
  `0.3.0rc1` 与更新的开发源才包含 Coding Agent 生命周期扩展。
- 不要把 AgentGov 说成自动产品漂移检测器。它能验证任务事实，不能替人判断
  “我们是不是还在做正确的产品”。

## 30 秒定位

> AI Coding Agent 可以写出测试通过的代码，同时又做了人根本没有要求的事。
> 测试通过也不会告诉你，是不是已经有人同意让这个改动继续往前走。
>
> 我做 AgentGov，是为了把任务、这个任务允许修改的文件、当前运行产生的证据，
> 以及人的决定连在仓库里。软件检查它能检查的事实，下一步仍然由人决定。
>
> 后来更难的问题是，我发现自己逐渐把更多工作放到 GitHub 和交付上，反而离
> AgentGov 最初要解决的问题越来越远。

**停顿点 1：**如果对方只问“你做了什么”，讲到这里即可。

## 默认两分钟

1. **问题（0:00–0:30）：**Coding Agent 可以写出好代码，但仍然做了人没有要求的事。
   只看测试通过，不能知道它是否留在任务内、结果是否仍然对应当前代码，
   或者是否已经有人批准下一步。
2. **我先做了什么（0:30–0:55）：**我从软件能够稳定检查的部分开始，做了一个
   小型 Python CLI。它读取任务、允许修改的文件和工作过程产生的证据，然后说明
   某件事通过、失败，还是仍然需要人判断。它不会把这些检查变成“这个改动是正确的”。
3. **偏移如何发生（0:55–1:25）：**一次 consumer 实验暴露了安装、Windows 路径和
   onboarding 摩擦，所以我先改这些，然后是 CI，再然后是 PR 流程。这些功能确实有用，
   测试也一直通过。但在连续几次常规价值复核中，我发现自己可以很清楚地解释
   GitHub 机制，却越来越难把它们和原始业务问题连起来。我把累积实现和最初需求放在一起检查，
   确认产品方向已经偏移。
4. **我改了什么，学到了什么（1:25–2:00）：**我保留了 PR 和 CI，但把它们移出中心。
   主产品回到开发循环：人定义任务，Agent 在约定边界里工作，当前文件和测试被检查，
   最后人决定下一步。验证能证明一个功能能工作，却不能告诉我是否还在做正确的产品。
   我现在自己做这项产品复核，而不是再把它自动化成一个新功能。

**停顿点 2：**这是完整默认回答。没有追问时，不必打开浏览器。

## 五到七分钟屏幕演示

1. 用 0:00–3:00 打开[中文引导式 Demo](interview-demo.zh-CN.html)，从精确准入
   推进到 `REVIEW_READY`。
2. 用 3:00–3:40 说明 Demo 中四个角色的职责：人、模拟 Agent、AgentGov 和 Demo 脚本。
3. 只有对方追问产品为什么这样设计，才打开
   [中文项目背景](project-interview.zh-CN.html)解释产品漂移与回到 MVP。
4. 工程岗位再打开[artifact replay 深入案例](artifact-replay-interview.zh-CN.html)，
   讲两次失败与修复；不要先讲哈希或证据分类。
5. 只有在对方质疑证据时才打开[证据作品集](portfolio.html)。
6. 最后主动说明版本边界和一个未知项。

**停顿点 3：**引导式 Demo 之后，产品回答已经完整。
**停顿点 4：**artifact replay 之后，工程回答已经完整。作品集只是可选核验。

## 按岗位分支

### 软件或 AI 工程

强调 fail-closed 边界、新鲜证据、确定性与建议性的区别，以及 artifact replay
的两次失败。说明底层修复大多由 Agent 提出、由你审查批准。

### 平台或基础设施

强调仓库原生契约、Adapter、CI 重放、权限分离、create-only 持久化，以及恢复
不能静默替换 owner。Airbnb 只是一次观察到的工作流，不代表广泛可移植性。

### 产品或技术产品

强调持续的价值复核、确认偏移、先回到 MVP 再补细节，以及任务级验证的能力边界。
Taxi 是产品学习背景，不是广泛采用证明。

## 常见追问

### 为什么不只是一个 linter？

因为它除了检查代码或配置，还把人的任务、架构上下文、路径范围、证据新鲜度、
建议性复核和权限边界绑定起来；但它仍拒绝从静态检查推断需求价值。

### 为什么区分 PASS、WARN、FAIL 和 ADVISORY？

因为单一分数会掩盖四件不同的事：契约满足、诚实的不完整、确定性失败，以及只能
由人判断的问题。

### 为什么不能自动检测产品漂移？

任务证据只能说明实现是否匹配已准入任务，不能说明一串各自合理的任务是否仍在
推进正确的产品。跨功能的价值复核才提供这个产品判断。

### 最强的工程证据是什么？

简短产品回答用退款范围边界；工程深挖用 artifact replay：受限 worker 因隐藏
Git 依赖连续失败两次，限制没有被放宽，可信事实被移入边界内，唯一一次修复后
回放无重试完成。

### artifact replay 的修复是谁设计的？

固定 Harness 边界是共同形成的；底层修复大多由 Agent 提出，我审查并批准。
把清理前证据与清理后证据分开，是我坚持的决定。

### 下一步做什么？

本指南不决定也不授权下一项需求。应回到 [STATUS.md](../STATUS.md) 的产品复核，
由人选择下一项要求，而不是在完成后自动继续功能开发。

## 主动说明的限制

- 静态检查不能证明需求价值、架构质量、审阅者理解或测试充分性。
- 稳定版 `0.2.1` 不包含最新开发源生命周期。
- 一次 Airbnb 工作流和一次 artifact replay 不能证明广泛采用、可移植性、
  重复可靠性或生产安全。
- replay 链保留不可变 reservation、create-only claim 和 immutable recovery；
  恢复不创建 replacement owner，也不授权 replay。
