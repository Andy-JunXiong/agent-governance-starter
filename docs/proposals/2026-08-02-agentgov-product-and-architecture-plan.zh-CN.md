# AgentGov 产品与架构方案（Revision 3）

状态：第二轮 Claude Review 已通过；Phase 1 可开始，Phase 2/3 前置规范已记录
日期：2026-08-02
范围：汇总原始 AI Radar governance 迁移目标、已完成能力、架构偏移修正和新增 Monitor/Dashboard 需求
决策依据：[ADR-0009](../adr/0009-govern-coding-agents-during-development.md)
首个反例：[AG-DRIFT-001](../case-studies/0001-pr-center-architecture-drift.md)

## Review Resolution

第一轮 Claude Review 确认了方向，同时指出四个执行 blocker 和若干结构性风险。本次修订处理如下：

| Feedback | Resolution |
|---|---|
| `scope.changed` 只有 machine-checkable scope 才能 FAIL | 接受原则，修正具体机制。当前 task contract 已要求精确 repository-relative path/path prefix，并拒绝 glob；v1 继续采用跨平台语义更简单的精确前缀，而不是引入 glob。只有该结构化范围可产生 deterministic FAIL，任务语义描述只能产生 ADVISORY。 |
| `architecture.candidate` 缺少可解释检测机制 | 接受。v1 仅由 task 显式引用或 changed path 与 artifact 自身声明的 `applies-to` path overlap 触发，结果固定为 ADVISORY。禁止全文语义推断。 |
| gitignored development events 会让 CI Dashboard 偏向 CI | 接受。Dashboard 必须声明 observation scope；未显式 export 时，CI 只能显示 `ci_only` 视角，并禁止计算 pre-code versus CI discovery 指标。 |
| fresh validation evidence 没有可测试定义 | 接受问题，修正建议。不能只依赖文件 mtime 或 `HEAD`：dirty working tree 是主要开发场景。Freshness 必须绑定 task digest、comparison base、snapshot HEAD 和包含 staged/unstaged/untracked/renamed 内容哈希的 change-set digest。 |
| Contract 和 source-of-truth 数量增长 | 接受。声明只存在于 artifact 自身；Registry 永远是内存派生索引，不增加 `registry.json`。Context 和 Event 是派生输出 contract，不拥有 trigger 或 applies-to 声明。 |
| Compact mode 太晚 | 接受。一个 task schema 支持 `compact`/`standard` profile；compact profile 成为 Phase 1 交付物。 |
| Coding Agent 消费测试太晚 | 接受。Phase 1 必须让真实 Coding Agent 使用 context output 完成一个小任务，并记录约束遵守和上下文噪声。 |
| 命令、actor、stagnation、版本和 core-file 建议 | 接受：保留 `govern start/check/finish`；actor 使用三类加可选 label；stagnation v1 仅显式自报并产生 ADVISORY；0.3 重定义为 development-governance release；core-file v1 只输出 patch 建议。 |
| Dashboard 首版范围过大 | 接受大部分。MVP 只做 Overview、Timeline、Task Detail；效果的最小 observed facts 合并到 Task Detail。完整 Skill Usage、Effect Evidence 和 benefit-monitor 复用延后。基础 secret/path redaction 仍是任何 export 的阻塞要求。 |

第二轮 Claude Review 确认方案骨架可以进入 Phase 1，并提出后续 Phase 的实现语义。Revision 3 的处置如下：

| Feedback | Resolution |
|---|---|
| change-set digest 会被 `.agentgov/` 和 validation artifact 污染 | 接受。把 digest scope 拆为独立 hard-gate spec：tracked change 始终计入，普通 untracked 只读取 `git ls-files --others --exclude-standard`，未跟踪的 `.agentgov/` 本地工具状态显式排除；validation 产生 tracked/non-ignored artifact 时 evidence 变 stale 并给出可操作提示。 |
| path prefix 必须按 segment 匹配并定义 include/exclude 优先级 | 接受。新增独立 trigger/routing spec：禁止 raw `startswith`，exclude 始终覆盖 include，rename 同时检查 old/new endpoint，并规定 Phase 2 policy fixtures。 |
| validate 与 commit 顺序需要说明 | 接受问题并修正为更一般的规则：`validate -> finish -> commit` 与 `commit -> validate -> finish` 都合法；validation 与 finish 之间任何 task、HEAD、index 或 worktree snapshot 变化都会 stale，必须重新验证。 |
| Registry 的 `last validation` 与内存派生冲突 | 接受。Registry 只保存当前运行可派生的 source hash/validation status；历史 validation 只能在 Phase 3 后由 Event Store 派生，不进入 Registry 声明。 |
| `current-task.json` 暗含单任务限制 | 接受。v1 明确为每个 working copy 只允许一个 active task；Git worktree 之间可以各自持有本地 pointer，多任务并行留作后续设计。 |
| 主文档同时承担产品、架构 spec 和 review log | 接受。触发目录和 fresh-evidence contract 已拆为独立 spec；本文件保留产品责任、阶段 gate 和 review resolution。 |

## 1. 执行摘要

AgentGov 应当是一个用户可以直接从 GitHub 下载并安装的、独立于 AI
Radar 的 repository-native Coding Agent governance 产品。

产品核心不是 PR 分析，也不是一组互不关联的 Schema，而是一个完整闭环：

```text
GitHub 下载与安装
  -> 接入用户仓库
  -> Govern：在开发前和开发中管理需求、架构、技能和代码范围
  -> Observe：记录治理何时、为何、如何触发以及人类如何决定
  -> Monitor：展示治理活动、未决问题和可辩护的效果证据
  -> PR/CI：独立重放确定性事实并保留证据
```

一句话产品定义：

> AgentGov 把仓库中的需求、`AGENTS.md`、ADR、Invariants、Agent Skills、
> AI Capability 和验证证据，按当前开发任务选择并交给 Coding Agent，
> 在开发过程中发现偏移，记录治理事件，并通过 Dashboard 展示发生了什么和结果如何。

## 2. 用户需求汇总

### 2.1 最终用户体验

用户应当能够：

1. 从 GitHub Release 下载或通过固定版本 wheel 安装 AgentGov；
2. 在新仓库或已有仓库中安全接入，不复制 AgentGov 源码；
3. 在开发任务开始时明确需求、目标、范围、风险、验收和人工边界；
4. 让 Coding Agent 自动获得与任务相关的治理上下文，而不是读取全部仓库文档；
5. 根据任务状态触发合适的 Agent Skill；
6. 在代码尚未进入 PR 前发现需求、架构、范围、证据或执行循环偏移；
7. 在 Coding Agent 声称完成前进行 fresh-evidence 和 invariant reconciliation；
8. 在 GitHub CI 中独立重放确定性检查；
9. 通过 Monitor/Dashboard 查看治理何时触发、如何使用、发现了什么以及结果如何。

### 2.2 必须包含的治理来源

AgentGov 应包含 AI Radar governance 中可移植的责任模型，但不机械复制其内容。

| 治理来源 | AgentGov 中的责任 | 初始触发规则 |
|---|---|---|
| `AGENTS.md` | 仓库宪法、权限、禁止事项、工作模式、人工授权边界 | 每个任务始终加载 |
| Development Task | 当前需求、父目标、范围、风险、验收、审批和停止条件 | 每个有意义的开发任务开始时 |
| `AI_CONTEXT.md` 或架构总览 | 模块地图、入口、source of truth 和跨模块关系 | 架构相关任务开始时，并作为 ADR 选择的导航输入 |
| ADR | 长期架构决策、取舍和所有权 | 被任务显式引用，或与任务路径/能力相关时 |
| `INVARIANTS.md` | 普通任务不得破坏的跨 ADR 约束 | 开发前、范围改变和完成前 |
| `grill-before-sprint` 类协议 | 需求是否具体、为什么现在做、最小切片和验证方法 | 新需求进入实现前 |
| `context-first-review` | 选择相关代码、架构、约束和冲突 | 设计或实现开始前 |
| `development-slice` 与 closed loop | 约束 Coding Agent 的执行与验证循环 | 任务 admitted 后 |
| action-loop stagnation | 识别重复假设、反复失败、虚假完成和过早 handoff | 多次尝试没有新证据时 |
| reconcile-invariants | 核对任务、代码、ADR、Invariants 和证据 | Coding Agent 请求完成时 |
| Capability / Control / Dependency | 与任务相关的 AI 能力、控制和依赖声明 | 任务涉及相应能力或路径时 |
| Evaluation | 测试、模型或 Prompt 的证据成熟度与决策 | 相关 capability 改变时 |
| PR/CI replay | 防止本地跳过并保留独立证据 | push、PR、默认分支或显式运行时 |

“包含”表示 AgentGov 能发现、校验、选择、触发、记录使用并检查漂移；不表示每次把所有文件全部放入 Agent 上下文，也不表示 AgentGov 可以自动重写核心治理文件。

## 3. 产品原则

1. **Development-time first**：第一次治理交互发生在编码前或编码中，而不是 PR 后。
2. **GitHub-distributed**：一个公开仓库、固定 Release、可验证 wheel、清晰安装和更新路径。
3. **Repo-native**：治理权威和可复现事实留在用户仓库；v1 不依赖 SaaS 控制面。
4. **Selective context**：只向当前任务提供相关上下文，并说明选择原因。
5. **Deterministic versus advisory**：路径、Schema、Git 事实和证据状态可确定性检查；需求含义、架构充分性和效果归因保留给人。
6. **Human-controlled**：核心治理修改、scope 扩大、override、commit、merge、release 和 deploy 保持人工权限。
7. **Observe without surveillance**：记录治理事件和结果，不收集 Prompt、私有代码、凭证或不必要的个人数据。
8. **One meaning, multiple surfaces**：本地 CLI、Dashboard 和 CI 复用同一事实与状态语义。

## 4. 当前资产与真实状态

### 4.1 已发布并可下载

稳定版 `0.2.1` 已具备：

- GitHub Release 固定 wheel 和 SHA-256 验证；
- pipx 隔离安装与更新；
- `doctor`、`onboard`、`next`、`init` 和 existing-repository adoption；
- repository/capability/reference/evaluation/agent-skill/artifact checks；
- `PASS`、`WARN`、`FAIL`、`ADVISORY`；
- Markdown、JSON、HTML repository report；
- 只读 GitHub Actions consumer CI 和状态展示。

这些能力解决分发、接入、静态治理事实和 CI 复核，可以保留并复用。

### 4.2 当前 development source 已实现

- 严格的 development task contract；
- `agentgov check task <task.json> --repository .`；
- requirement、parent objective、scope、architecture refs、risk、approval、stop 和 admission 校验；
- `AG-DRIFT-001` 自我治理场景；
- 尚未发布的 persona-aware PR、upgrade proposal 和 benefit-monitor 基础设施。

### 4.3 尚未实现

- Governance Registry 和任务相关 context selection；
- Agent Skill 的条件匹配与触发解释；
- staged/unstaged/untracked/renamed changed-file scope check；
- action-loop stagnation 观察；
- fresh validation evidence 与 completion reconciliation；
- development governance event store；
- 面向开发治理的 Monitor/Dashboard；
- 本地事实与 CI replay 的统一 task/change/event contract；
- 一个独立用户仓库中的端到端实测。

### 4.4 已有 PR 工作如何处理

不删除已有 PR/CI 和升级代码，但停止把它们作为产品中心继续扩张。

| 现有资产 | 处理决定 |
|---|---|
| Repository checks/reporting | 保留，作为 Govern 和 Monitor 的确定性基础 |
| GitHub consumer CI | 保留，改为重放本地 development facts |
| HTML reporting | 复用为静态 Dashboard 渲染基础 |
| Redaction | 复用到 governance event export |
| Benefit monitor | 首版不复用；等 event 和 observed-outcome 语义稳定后再评估序列化或趋势组件 |
| Upgrade review / Draft PR writer | 冻结为次要维护能力；核心闭环完成前不继续产品化 |
| PR persona findings | 保留为最终 backstop 视图，不定义新的治理语义 |

## 5. 目标架构

```text
┌──────────────────────────────────────────────────────────────┐
│ 1. Distribution & Adoption                                  │
│ GitHub Release -> pipx -> doctor/onboard -> repo scaffold    │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│ 2. Governance Registry                                      │
│ AGENTS | Tasks | AI_CONTEXT | ADRs | Invariants | Skills    │
│ Capabilities | Controls | Dependencies | Evaluations       │
└──────────────────────────────┬───────────────────────────────┘
                               │ discover / validate / classify
┌──────────────────────────────▼───────────────────────────────┐
│ 3. Governance Router                                        │
│ current task + declared scope + repo facts                  │
│ -> select context -> match skills -> explain why            │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│ 4. Development Governance Loop                              │
│ Admit -> Ground -> Bound -> Implement -> Verify -> Reconcile│
└───────────────────────┬───────────────────┬──────────────────┘
                        │                   │
             ┌──────────▼─────────┐  ┌──────▼─────────────────┐
             │ 5. Event Store     │  │ 6. PR/CI Replay        │
             │ triggers/findings  │  │ same deterministic facts│
             │ decisions/outcomes │  │ independent evidence    │
             └──────────┬─────────┘  └──────┬─────────────────┘
                        │                   │
                        └─────────┬─────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │ 7. Monitor / Dashboard     │
                    │ activity, drift, decisions,│
                    │ timing, outcomes, limits   │
                    └────────────────────────────┘
```

### 5.1 Distribution & Adoption

目标是让用户只需要一个 GitHub 仓库和固定 Release：

```powershell
pipx install "https://github.com/<owner>/agent-governance-starter/releases/download/<version>/<wheel>"
agentgov onboard .
```

接入行为必须：

- inspect 和 dry-run 优先；
- create-missing-only；
- 不覆盖用户已有 `AGENTS.md`、ADR 或 Skill；
- 检测已有治理文件并提出 reconcile 建议；
- 说明哪些能力来自稳定版，哪些仍为 preview。

### 5.2 Governance Registry

Registry 是从治理 artifact 自身派生的内存索引，不是文件、运行时数据库或第二个 source of truth。声明所有权如下：

- `SKILL.md` frontmatter 拥有 skill trigger、non-trigger 和 applies-to 声明；
- ADR/Invariant 自身的结构化 metadata 拥有 applies-to path/capability；
- task JSON 拥有显式引用、当前 scope 和人工 decision；
- capability/control/dependency/evaluation contract 拥有自己的 identity 和关系；
- `AGENTS.md` 和架构总览拥有仓库级默认边界；
- Registry 只读取这些声明并建立内存索引，不允许用户编辑 `registry.json`。

派生索引中的逻辑记录包括：

- artifact type，包括 constitution、architecture overview、decision、invariant、skill、task 和 capability governance；
- repository-relative path；
- contract/version；
- owner 和修改权限；
- trigger conditions 与 non-trigger conditions；
- applies-to paths/capabilities/task types；
- deterministic/advisory 分类；
- 当前运行从 source 计算的 hash 和 validation status；
- 是否属于 core governance file。

Registry 首版只从 artifact 自身的结构化声明和固定路径惯例发现，不通过全文语义猜测自动建立架构关系。Context JSON 和 governance event 可以序列化派生结果，但不能反向成为 trigger 或 applies-to 的权威来源。Registry 不保存跨运行的 `last validation`；Phase 3 之后的历史 validation 只能从 Event Store 派生。

### 5.3 Governance Router

Router 负责回答：本次任务需要哪些治理上下文，以及为什么。

初始选择顺序：

1. 始终包含根 `AGENTS.md` 和当前 admitted task；
2. 包含 task 显式声明的 ADR、Invariant、requirement 和 approval refs；
3. 根据 task scope 与 artifact 自身声明的 applies-to path 做精确 path-prefix overlap，选择额外 ADR/Skills/Capabilities；
4. 根据 capability identity 连接 Control、Dependency 和 Evaluation；
5. 对可能相关但不能确定的内容产生候选 `ADVISORY`，不自动宣称适用；
6. 输出每个选择项的 reason 和 selection mode：`required`、`declared`、`path_match`、`capability_link` 或 `advisory_candidate`。

Router 输出必须是稳定 JSON，可进一步渲染为终端和 Markdown。它不修改治理文件。

### 5.4 Trigger 与 Agent Skill

首版“触发”是显式 CLI/Agent protocol 调用后的条件路由，不是后台监控进程或强制 Hook。

完整 trigger catalog、segment-aware path prefix、include/exclude 优先级、rename endpoint 和 Phase 2 policy fixtures 由 [Development Trigger and Routing Semantics v1](../specs/development-trigger-routing-v1.md) 单独定义。核心约束是：

- `scope.changed` 只由 Git path 与 admitted structured scope 的确定性比较产生；自然语言 scope 不参与 FAIL；
- prefix 必须按完整 path segment 匹配，不能使用 raw string `startswith`；
- exclude 始终覆盖 include，rename 的 old/new endpoint 都必须在 scope 内；
- `architecture.candidate` 只由显式 task ref 或 changed-path/applies-to overlap 触发，并固定为 ADVISORY；v1 禁止全文语义推断；
- `action_loop.stagnating` 只接收 Coding Agent 对 attempt、hypothesis 和 evidence 的结构化自报，并固定为 ADVISORY。

每个 Skill 必须声明 trigger、non-trigger、required context、workflow、stop、output 和 authority boundary。

### 5.5 Development Governance Loop

第一轮 Review 接受以下产品级主命令：

```text
agentgov govern start   # preview + 人工确认后创建/选择 task 和 context
agentgov govern check   # 开发中只读检查并记录事件
agentgov govern finish  # fresh evidence 和 completion reconciliation
agentgov monitor build  # 从事件生成静态 dashboard
```

现有低层命令 `agentgov check task` 保留，供测试、CI 和高级用户使用。用户主路径不应要求理解所有内部 contract。

`govern start` 是显式写操作，必须 preview、列出目标文件并要求确认；`govern check` 和 `govern finish` 的检查部分不得修改源码、Git index 或分支。启用 Observe 时，它们只能向预先披露的 `.agentgov/events/` 追加工具状态。`finish` 不能仅凭 task 自述将状态变为 verified。

## 6. Observe：治理事件模型

### 6.1 为什么需要独立事件层

Dashboard 不能从最终 PR 或当前文件状态反推“什么时候触发了治理、当时看到了什么”。每次治理交互必须产生不可歧义的 observation event。

### 6.2 最小事件字段

建议 contract：`agentgov.governance-event`。

```json
{
  "contract": "agentgov.governance-event",
  "schema_version": "1.0",
  "event_id": "immutable-id",
  "occurred_at": "RFC3339 UTC",
  "repository": "portable repository identity",
  "task_id": "task-id",
  "stage": "admit|ground|bound|verify|reconcile|ci",
  "trigger": "completion.requested",
  "actor_type": "human|coding_agent|ci",
  "actor_label": "optional free-text label",
  "tool_version": "x.y.z",
  "selected_governance": [],
  "findings": [],
  "decision": null,
  "evidence_refs": [],
  "authority_boundary": {}
}
```

v1 的 actor authority 只使用 `human`、`coding_agent`、`ci` 三类；`actor_label` 可选且必须经过 portable/redaction 检查。Agent vendor 不进入必选 enum，避免厂商耦合。

事件应记录事实而不是 Prompt 全文。默认禁止：

- Secret、Token、Authorization header；
- 用户 home/runner 的绝对路径；
- 私有 Prompt、源代码内容和上传数据；
- 无必要的个人身份信息；
- 未经声明的遥测上传。

### 6.3 本地存储与 GitHub

首版建议：

- 本地 append-only JSONL 或小型 JSON event bundle；
- 默认位于 `.agentgov/events/` 并建议 gitignore，避免把个人开发活动自动提交；
- 用户显式执行 export 后生成经过 redaction 的 portable observation bundle；
- GitHub Actions 上传 redacted event/report artifact，并在 job summary 显示本次 replay；
- 不在 v1 建立中央 SaaS telemetry 服务。

具体存储格式需要在实现前做 crash recovery、并发写、重复事件和隐私 review。

Event bundle 和 Dashboard 必须携带 observation scope：

- `local_session`：仅当前机器的未 export development events；
- `exported_development`：用户显式导出的 development events；
- `ci_only`：CI 只能看到本次和可恢复的 CI replay events；
- `combined`：显式 development export 与 CI replay 合并。

未 export 时，CI Dashboard 只能诚实显示 `ci_only`，不能暗示 development-time 历史完整，也不能计算“问题首次发现于 pre-code、development 还是 PR/CI”。换机器同样不会自动获得本地历史。Dashboard 必须展示 observation 起止时间、event 数量和缺失来源。

任何 event export 在 v1 都必须具备基础 redaction：secret/token shape、credential assignment、用户/runner 绝对路径和未声明内容字段必须被拒绝或清除。复杂的可配置 redaction pipeline 可以延后，基础安全边界不能延后。

### 6.4 Fresh validation evidence

`fresh` 是可重复验证的 snapshot 关系，不是“最近运行过测试”的自然语言声明。完整 evidence identity、canonical exclusions、`S0/S1/S2` snapshot 关系、validation artifact 行为和 Phase 3 policy fixtures 由 [Fresh Validation Evidence Semantics v1](../specs/fresh-validation-evidence-v1.md) 单独定义，并作为 Phase 3 hard gate。

摘要约束：

- 明确区分 task change-set 的 `comparison_base_sha` 与验证时的 `snapshot_head_sha`；
- change-set digest 覆盖 committed-since-base、staged、unstaged、rename 和 non-ignored untracked Git facts；
- untracked discovery 使用 `git ls-files --others --exclude-standard`；未跟踪的 `.agentgov/` 本地工具状态排除，但 tracked `.agentgov/` change 和 tracked `.gitignore` change 仍计入；
- validation command 产生 tracked 或 non-ignored artifact 时 evidence 自动 stale，并提示用户检查、移除或有意加入 ignore 后重新验证；AgentGov 不自动编辑 `.gitignore`；
- `validate -> finish -> commit` 和 `commit -> validate -> finish` 均合法，真正的约束是 validation 到 finish 之间 task、HEAD、index、worktree 和 non-ignored untracked snapshot 不得变化；
- 文件 mtime 不能作为主要 freshness oracle，`HEAD` 相等也不足以表示 dirty working tree 未变化；
- 没有匹配当前 task 和 snapshot 的 fresh evidence 时只能报告 `claimed` 或 `needs_evidence`，不能报告 `verified`。

## 7. Monitor / Dashboard

### 7.1 首版形式

优先实现本地生成的单文件静态 HTML Dashboard：

```powershell
agentgov monitor build . --output agentgov-dashboard.html
```

理由：

- 复用已有 HTML renderer；
- 无服务器、数据库和账号系统；
- 可在本地打开，也可作为 GitHub Actions artifact 下载；
- 后续可选 GitHub Pages 或 SaaS，而不改变事件合同。

### 7.2 Dashboard 页面

MVP 只包含：

1. **Overview**：active tasks、最近治理时间、未解决 FAIL/WARN/ADVISORY；
2. **Activity Timeline**：每次 trigger、stage、actor、selected governance 和结果；
3. **Task Detail**：requirement、ADR/Invariants、Skill、scope、checks、decisions、completion，以及最小 observed outcome：发现阶段、解决状态、处理时间、项目测试记录和人工 outcome。

每个页面固定显示 observation scope 和 Limits。独立的 Drift、Skill Usage、Effect Evidence 视图，以及 benefit-monitor 趋势复用，延后到事件语义经过真实使用验证之后。

### 7.3 可以展示的效果

可直接观察并展示：

- governance trigger 数量和时间；
- task 数、stage 分布和完成状态；
- 选择了哪些 ADR/Invariants/Skills，以及原因；
- FAIL/WARN/ADVISORY 的产生、解决和 override；
- 问题首次发现于 pre-code、development、completion 还是 PR/CI；
- detection-to-decision 和 detection-to-resolution 时间；
- scope drift、stagnation 和 completion rejection 次数；
- 项目测试命令及其记录状态；
- 人工记录的 outcome。

不能自动宣称：

- 避免了多少事故；
- 提高了多少代码质量；
- 节省了多少人工时间；
- 产生了多少 ROI；
- Governance coverage 百分比；
- Architecture 是“正确的”。

这些结论需要定义 denominator、对照和外部证据。Dashboard 必须把 observed facts 与 inferred benefit 分开。

## 8. 文件与权限模型

建议逻辑布局：

```text
AGENTS.md
docs/adr/
  INVARIANTS.md
agent-skills/
governance/
  tasks/
  capabilities/
  controls/
  dependencies/
evaluation/
.agentgov/
  events/                    # 默认本地、建议 gitignore
  current-task.json          # v1 本地 pointer；每个 working copy 一个 active task
  dashboard/                 # 可再生成
```

Registry 在运行时从上述 artifact 派生，不落 `governance/registry.json`。

`current-task.json` 只定位当前 working copy 的 active task，不拥有 task 声明。v1 明确不支持同一 working copy 内多个 active task；不同 Git worktree 可以拥有各自的本地 pointer。该限制必须由 `govern start` 明示，不得静默覆盖已有 active task。

权限边界：

- discover/check/context/monitor：只读；
- start/create/export：明确 preview 和人工确认后才写指定文件；
- 修改 `AGENTS.md`、ADR、Invariants、Skill：v1 只生成建议 patch，不自动应用；受限 apply 需要独立 threat model 和 ADR；
- commit、push、PR、merge、release、deploy：保持独立授权；
- Hook、watch daemon、IDE interception：需要新的 ADR、threat model 和 opt-in。

## 9. 分阶段交付计划

### Phase 0：冻结偏移并保持可安装

目标：不破坏稳定 `0.2.1` 用户，不继续扩大 PR-centered 0.3。

- 保留现有 GitHub Release、update 和 consumer CI；
- 保持全部既有回归测试；
- 将未发布 PR writer 标为 supporting/experimental；
- 不发布新的 PR-centered release。

完成标准：现有稳定用户仍可安装、运行和更新；产品文档不再把 PR 作为核心。

### Phase 1：Governance Registry + Context Selection

目标：Coding Agent 在开发前拿到相关治理上下文。

- 从 artifact 自身派生内存 Registry，inventory `AGENTS.md`、architecture overview、tasks、ADR、Invariants、Skills、Capabilities、Controls、Dependencies、Evaluation；
- 在 artifact 自身定义 applies-to 和 trigger metadata，不增加 `registry.json` 或 mapping source of truth；
- 在同一个 task schema 中交付 `compact` 和 `standard` profile。Compact 至少包含 requirement summary、精确 include path prefixes、一条 acceptance/validation command、人工 owner/decision；仍不得使用自然语言 scope 产生 deterministic FAIL；
- 输出稳定 context JSON、terminal 和 Markdown；
- 每个选择项带 reason；
- 不做全文语义推断或自动修改。

完成标准：当前 P0 task 只得到相关上下文；无关仓库文档不进入 task-specific output；AI Radar 和独立仓库均能使用；一个真实 Coding Agent 使用 context output 完成小型任务，并记录 selected constraints 是否被遵守、哪些 context 被忽略以及输出是否过长。该消费测试是 Phase 1 gate，不延后到发布 pilot。

### Phase 2：Scope Check + Skill Trigger

目标：在开发中发现范围和执行循环偏移。

- 只读检查 staged、unstaged、untracked、renamed；
- 将 actual changed paths 与 admitted task 的精确 include/exclude path prefixes 比较；只有结构化 path contract 可以产生 deterministic FAIL；
- 支持显式 exception；
- `architecture.candidate` 仅通过显式 task ref 或 changed-path/applies-to overlap 路由 context-first ADVISORY；
- 路由 development-slice；stagnation 仅接收 Agent 结构化自报 attempts 并输出 ADVISORY；
- 输出 trigger reason 和 deterministic/advisory 分类。

实现前置 gate：[Development Trigger and Routing Semantics v1](../specs/development-trigger-routing-v1.md) 中的 segment match、exclude precedence、rename endpoint 和 classification fixtures 必须先通过。

完成标准：scope 外路径确定性暴露；architecture relevance 不被伪装成 FAIL；无 Git mutation。

### Phase 3：Completion Reconciliation + Event Store

目标：Coding Agent 不能仅凭自述宣称完成，并为 Monitor 产生可靠事件。

- 按 [Fresh Validation Evidence Semantics v1](../specs/fresh-validation-evidence-v1.md) 实现 task/comparison-base/snapshot-HEAD/change-set digest 绑定的 fresh validation evidence；
- reconcile task、changed files、ADR、Invariants、Capability 和 unresolved findings；
- append governance events；
- 记录 human continue/narrow/pause/override；
- 处理重复、崩溃恢复、并发和 redaction。

实现前置 hard gate：canonical Git layer、`.agentgov/` 与 gitignore exclusion、validation-generated artifact、snapshot ordering 和 actionable stale reason fixtures 必须先通过。

完成标准：没有匹配当前 task、comparison base、snapshot HEAD 和完整 change-set digest 的 fresh evidence 不能报告 verified completion；本机记录的阶段可重建；export 经过基础 redaction。跨机器或 CI 的历史完整性只在显式 export 后成立。

### Phase 4：Monitor / Dashboard

目标：用户能看到治理如何被使用以及观察到的结果。

- 生成静态 HTML Dashboard；
- MVP 只交付 Overview、Activity Timeline 和 Task Detail；
- 支持本地和 GitHub Actions artifact；
- 固定显示 `local_session`、`exported_development`、`ci_only` 或 `combined` observation scope；
- 明确 observed/inferred/unknown；
- 不提供 approval 或治理核心文件写按钮。

完成标准：在当前 observation scope 内，用户可回答“什么时候触发、为什么触发、用了什么、发现什么、如何处理、目前结果如何”；CI-only 数据不展示跨阶段 discovery 对比。

### Phase 5：GitHub Release + 两仓库 Pilot

目标：形成真正可下载、可使用、可验证的产品版本。

- 固定 GitHub Release wheel 和 manifest；
- 将 `0.3` 定义为 development-governance release；未发布的 PR-centered writer 延后到 `0.4` 或在独立价值验证前保持 experimental；
- 从公开安装路径执行全流程；
- AI Radar 只读 bounded replay；
- 一个无 AI Radar 背景的独立仓库 pilot；
- CI 重放相同 deterministic facts；
- 记录使用摩擦、false positive、missed constraint、override 和 handling time。

完成标准：新用户无需理解 AgentGov 源仓库即可安装、govern 一个真实任务并生成 Dashboard。

## 10. 端到端验收场景

### 场景 A：AgentGov 自身架构偏移

使用 `AG-DRIFT-001`：

- 原始目标是 development-time coding-agent governance；
- 连续 supporting tasks 转向 adoption、CI 和 upgrade PR；
- 系统显示任务、父目标、changed surfaces 和 supporting/core 声明；
- 在 PR 前产生 architecture-drift advisory；
- 人工决定 restore core priority；
- Dashboard 显示发现阶段、决定和后续任务。

### 场景 B：AI Radar bounded replay

- requirement admission；
- context-first architecture selection；
- development slice；
- fresh evidence；
- action-loop correction；
- invariant reconciliation；
- 不复制 AI Radar 业务 gate、AWS、runtime data 或个人 policy。

### 场景 C：独立用户仓库

- 从 GitHub 安装；
- existing-repository onboarding；
- 创建一个小型 admitted task；
- 选择通用 `AGENTS.md`、ADR 和 Skill；
- 发现一个 scope drift 或 missing evidence；
- 人工处理；
- 完成 reconciliation；
- 生成 Dashboard 和 CI replay。

## 11. AI Radar 一致性与排除项

一致的是责任分离：

```text
需求准入 -> 架构 grounding -> 有界开发 -> fresh verification
-> completion reconciliation -> human decision -> PR/CI replay
```

不复制：

- AI Radar 产品业务 gate 和 workflow；
- AWS account、bucket、deployment path 或 credentials；
- runtime prompts、用户数据、signals、insights 或 cognitive logs；
- 个体专用规则；
- 自动 merge、release、deploy 或 mechanical interruption 权限。

AgentGov 管理可移植的 governance contract 和触发责任；AI Radar 继续是只读 reference implementation。

## 12. 主要风险与缓解

| 风险 | 缓解 |
|---|---|
| 又演变成通用配置 linter | 每个新增能力必须直接服务 Govern、Observe 或 Monitor |
| 全量上下文造成噪声 | Selective router、reason 字段、task-specific output |
| 把语义判断做成 FAIL | 固定 deterministic/advisory policy tests；path scope 使用 segment match、exclude precedence 和 rename endpoint fixtures |
| 事件记录泄露隐私 | 默认本地、最小字段、redaction、显式 export |
| Dashboard 指标误导 | observed/inferred/unknown 分层和 claim limits |
| 开发流程过重 | risk-proportional task contract，保留 compact mode |
| PR/升级代码继续吞噬路线图 | 在 core loop 和 Dashboard 完成前冻结功能扩张 |
| 与某个 Coding Agent 厂商耦合 | repo-native JSON/Markdown/CLI，vendor adapter 后置 |
| 自动触发引入过大权限 | 首版显式命令和 Skill routing，Hook/daemon 单独决策 |
| Registry/Context/Event 形成重复 source of truth | 声明只存在于 artifact 自身；其余全部是带 provenance 的派生输出 |
| CI Dashboard 缺少本地事件却显示完整历史 | 强制 observation scope；`ci_only` 禁止跨阶段 discovery 指标 |
| Freshness 依赖不可靠的 mtime 或 clean HEAD | 绑定 task/comparison-base/snapshot-HEAD/change-set canonical digest，并按独立 evidence spec 在验证前后及 finish 时重算 |
| 工具事件或 validation artifact 污染 change-set digest | 只排除未跟踪的本地工具状态和标准 ignored untracked；tracked/non-ignored artifact 使 evidence stale 并返回可操作路径 |

## 13. 建议当前决策

建议本次 review 接受以下产品级决定：

1. AgentGov 的唯一核心闭环是 `Govern -> Observe -> Monitor`；
2. GitHub Release 是首要分发渠道；
3. `AGENTS.md`、Task、`AI_CONTEXT.md`/架构总览、ADR、Invariants、Skills、Capabilities、Controls、Dependencies 和 Evaluation 是一等治理对象；
4. Governance Router 负责选择和解释，不能自动判断架构正确性；
5. development governance event 是 Monitor 的事实来源；
6. 首版 Dashboard 是本地生成、可由 GitHub Actions 上传的静态 HTML；
7. PR/CI 是独立 replay/backstop；upgrade PR automation 暂停扩张；
8. 首版 trigger 是显式调用后的条件路由，不引入强制后台 Hook；
9. AI Radar 提供责任模型和验证场景，不成为运行时依赖；
10. Registry 是从 artifact 自身派生的内存索引，不落 `registry.json`；
11. `scope.changed` 只比较 admitted task 的精确 path prefixes；自然语言 scope 不产生 FAIL；
12. `architecture.candidate` v1 只由显式引用或 path overlap 触发，并固定为 ADVISORY；
13. Fresh evidence 绑定 task digest、comparison base、snapshot HEAD 和完整 dirty-worktree change-set digest，并使用 canonical exclusion 防止本地工具状态自我污染；
14. 一个 task schema 提供 compact/standard profile，compact mode 属于 Phase 1；
15. v1 actor 仅为 `human/coding_agent/ci` 加可选 label，stagnation 仅显式自报；
16. v1 core-file update 只生成 patch 建议；
17. 将 0.3 定义为 development-governance release，PR writer 延后到 0.4 或继续 experimental；
18. 只有完成独立仓库端到端 pilot 后，才发布新的稳定 Release。

## 14. Review 后仍开放的问题

以下问题仍需要实现证据或产品负责人决定：

1. **Compact profile 细节**：最小字段、默认 stop boundary 和 acceptance command 如何表达，才能既低摩擦又不伪造人工决定？
2. **事件存储实现**：JSONL、one-event-per-file 或 bundle；如何处理并发、去重、崩溃恢复和显式 export？
3. **Dashboard 分发**：本地单文件 HTML + Actions artifact 是否足够；GitHub Pages 延后到什么证据出现时？
4. **最小效果证据**：哪些 project-test、resolution 和 human outcome 字段足以支持 Task Detail，同时不引入因果或 ROI 暗示？
5. **Context consumption gate**：选择哪个小任务和 Coding Agent 做 Phase 1 实测，以及如何记录 constraint adherence 和 context noise？
6. **并行 task 模型**：什么实际证据足以扩展 v1 的“每个 working copy 一个 active task”；未来是 worktree-local pointer、显式 session ID，还是不支持共享 worktree 并行？

## 15. 给 Claude 的 Review Prompt

可以将本文件路径和下面的提示一起交给 Claude：

```text
请 review 这份 AgentGov 产品与架构方案。重点检查：
1. 它是否忠实表达“GitHub 可下载、AI Radar 类开发期 governance、带 Monitor/Dashboard”的产品需求；
2. Govern、Observe、Monitor、PR/CI replay 的责任是否清晰且没有重复的 source of truth；
3. AGENTS.md、AI_CONTEXT、Task、ADR、Invariants、Agent Skills、Capabilities、Controls、Dependencies、Evaluation 的发现、选择和触发是否足够具体；
4. 哪些规则错误地把语义判断当成 deterministic fact；
5. governance event 和 Dashboard 是否能回答何时触发、如何使用、发现什么、如何处理、效果如何，同时避免不成立的因果或 ROI 声明；
6. 路线图是否保持一个可下载、十分钟可接入的轻量产品，而不是继续堆积独立 contracts；
7. 指出阻塞性问题、建议修改和可以延后的复杂度。不要默认批准，给出具体反例。
```

## 16. Review 后的下一步

第二轮外部 Review 已确认 Phase 1 可以开始。当前不继续扩展 PR writer、benefit monitor 或与 Phase 1 无关的新 governance schema；Phase 2/3 分别受独立 trigger 与 evidence spec gate 约束。

下一纵向切片是：

```text
Governance Registry
  -> 读取当前 admitted task
  -> 选择 AGENTS.md + AI_CONTEXT + 显式 ADR/Invariants + 匹配 Skills
  -> 输出带 selection reason 的只读 context JSON/Markdown
  -> 用一个真实 Coding Agent 执行小任务并记录 context consumption 结果
```

该切片不新增可编辑 Registry 文件，也不提前建设完整 Event Store。Context output 保留未来 event 所需的 provenance，但 event persistence 在 Phase 3 统一实现。这样可以先验证 Coding Agent 是否真正消费治理上下文，避免再次出现“基础设施先于产品闭环”的架构偏移。
