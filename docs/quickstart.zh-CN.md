# Agent Governance Starter Kit 中文快速开始

本指南帮助首次使用者在新仓库或已有仓库中完成最小接入。静态检查成功只代表契约已执行，不代表治理完成，也不授权合并、发布或部署。

## 1. 安装

在项目源码目录中安装当前版本：

```powershell
python -m pip install --no-deps .
agentgov --help
```

如果不希望安装，可以在源码目录中运行：

```powershell
$env:PYTHONPATH = "src"
python -m agentgov --help
```

## 2. 已有仓库接入

先执行只读检查：

```powershell
agentgov inspect path/to/project
```

结果含义：

- `PRESENT`：路径已经存在，接入时必须保留；
- `MISSING`：尚未配置，是非阻断的接入信息；
- `DISCOVERED`：发现其他工具的仓库指令，需要人工审阅；
- `CONFLICT`：路径类型错误或使用符号链接，必须先处理。

预览将创建和保留的文件：

```powershell
agentgov adopt path/to/project --project-name "项目名称" --dry-run
```

确认计划后，创建缺失文件：

```powershell
agentgov adopt path/to/project --project-name "项目名称"
```

该命令不覆盖已有普通文件、不合并 `CLAUDE.md` 或 Copilot/Cursor 指令，也不运行 Git 命令。

接着验证并生成报告：

```powershell
agentgov check repository path/to/project
agentgov report repository path/to/project --output path/to/project/governance-report.md
agentgov report repository path/to/project --format html --output path/to/project/governance-report.html
```

打开 `AGENTS.md` 和 `governance-report.html`。HTML 报告会用可视化方式解释四种状态、需要处理的事项和人工授权边界。处理或明确延后所有 `WARN`，并对 `ADVISORY` 记录人工判断。

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

更完整的说明见：

- [已有仓库接入指南](existing-repository-adoption.md)
- [生成文件填写指南](generated-files-guide.md)
- [故障排查](troubleshooting.md)
