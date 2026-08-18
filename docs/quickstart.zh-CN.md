# Agent Governance Starter Kit 中文快速开始

本指南帮助首次使用者完成稳定版接入。检查成功只代表确定性契约已执行，
不代表治理完成，也不授权合并、发布、release 或部署。

## 选择目标

- **已有仓库接入**：`inspect → adopt --dry-run → adopt → check`
- **创建新仓库**：`init → check`
- **生成报告**：`check → report`
- **查看开发功能**：直接前往本文末尾的独立成熟度与证据链接。

## 1. 安装

在需要治理的仓库根目录打开终端，把已发布的稳定版安装到隔离的
pipx 环境。不要把 starter 克隆到目标仓库内部。

```powershell
python --version
pipx install "https://github.com/Andy-JunXiong/agent-governance-starter/releases/download/v0.2.1/agent_governance_starter-0.2.1-py3-none-any.whl"
agentgov --version
agentgov --help
```

只有开发 starter 本身时，才应将它克隆到独立且较短的路径，不要放进被治理仓库，
并从包含 `src` 的 starter 根目录运行：

```powershell
$env:PYTHONPATH = "src"
python -m agentgov --help
```

## 2. 已有仓库接入

先执行只读检查：

```powershell
agentgov inspect .
```

结果含义：

- `PRESENT`：路径已经存在，接入时必须保留；
- `MISSING`：尚未配置，是非阻断的接入信息；
- `DISCOVERED`：发现其他工具的仓库指令，需要人工审阅；
- `CONFLICT`：路径类型错误或使用符号链接，必须先处理。

预览将创建和保留的文件：

```powershell
agentgov adopt . --project-name "项目名称" --dry-run
```

稳定版 0.2.1 针对空仓库预览的真实选取行：

```text
PLAN governance/contract.json
PLAN AGENTS.md
SUMMARY CREATE=26 PRESERVE=0
NOTE adopt dry-run: no repository files were created or modified
NOTE adopt: adoption does not authorize merge, publish, release, or deploy
```

确认计划后，创建缺失文件：

```powershell
agentgov adopt . --project-name "项目名称"
```

该命令不覆盖已有普通文件、不合并 `CLAUDE.md` 或 Copilot/Cursor 指令，也不运行 Git 命令。

接着验证并生成报告：

```powershell
agentgov check repository .
agentgov report repository . --output governance-report.md
agentgov report repository . --format html --output governance-report.html
```

打开 `AGENTS.md` 和 `governance-report.html`。报告会显示确定性事实、不完整证据和仍需人类决定的事项。处理或明确延后所有 `WARN`，并对 `ADVISORY` 记录人工判断。

首次检查出现 PASS、WARN 和 ADVISORY 的组合是正常的。`FAIL=0` 只说明没有确定性失败，不表示治理已经配置完成。还需要把示例 capability、占位符、evaluation cases、artifacts 和人工审批边界改成项目的真实情况。

## 3. 新仓库接入

`init` 只接受不存在或为空的目录：

```powershell
$Project = Join-Path $PWD "governed-project"
agentgov init $Project --project-name "项目名称"
agentgov check repository $Project
agentgov report repository $Project --output "$Project/governance-report.md"
```

生成结果会故意保留 placeholder 和早期 evaluation readiness。必须根据真实项目修改，而不是为了得到全绿结果而删除警告。

## 4. 必须人工完成的事项

1. 替换或明确延后 `{{PLACEHOLDER}}`；
2. 确认 AGENTS.md 与现有指令文件的权威关系；
3. 声明真实 capability、owner、risk 和 human-review 阶段；
4. 添加经过审阅的 evaluation cases 和 evidence；
5. 对合并、发布、release 和 deploy 分别取得明确人工授权。

## 5. 继续稳定路径

- [已有仓库接入指南](existing-repository-adoption.md)
- [生成文件填写指南](generated-files-guide.md)
- [故障排查](troubleshooting.md)
- [中文面试讲解](interview-guide.zh-CN.html)

## 6. 维护已接入仓库

```powershell
agentgov update --check .
# 审阅计划后：
agentgov update .
```

检查命令只读。更新仍需要真实终端中的精确确认，会验证稳定 release，
只应用有边界的计划并重新运行检查。

## 7. 开发预览

稳定版 `0.2.1` 仍是受支持的安装和接入路径。公开的 `0.3.0rc1` 是独立、
不可变的预发行快照。开发源继续加入 Coding Agent 生命周期、Adapter、
drift review 和 replay 安全能力，并有独立证据边界。本地已安装或已预检模块
不等于稳定发布或消费者已启用能力；新的无指导主要产品真人试用仍未证明。

- [自动化产品方向](product-requirements-automatic-governance.md)
- [成熟度与证据作品集](portfolio.html#boundary)
- [Adapter 详情](governance-mcp-adapter.md)
- [Replay 安全证据](clean-target-replay-preflight.md)
- [Drift review 提醒](drift-review-reminders.md)

Replay 安全证据覆盖 reservation、claim 和 recovery 的非授权边界。这些开发
记录都不授权 Git、合并、发布、release、replay 或部署。
