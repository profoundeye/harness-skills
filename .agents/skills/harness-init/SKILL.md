---
name: harness-init
description: "从任意需求文件初始化轻量 Codex Harness。用户输入 $harness-init、提供需求源文件、或要求 Codex 为某个编号 Sprint 创建 AGENTS.md、按证据生成 docs 文档、需求、任务、追踪、验证和就绪状态 JSON 时使用。"
---

# Harness 初始化

根据用户指定的需求文件，为一个 Sprint 初始化独立的 Harness 工作目录。需求源文件可以任意命名、任意格式、任意语言、任意结构。

## 调用方式

这个技能是在 Codex 聊天框里调用的，不是在终端里运行命令。常见输入如下：

```text
$harness-init

Sprint ID: SPRINT-001
需求源文件：
- docs/payment-v2.md
- notes/founder-comments.md

本 Sprint 目标：
实现支付流程 V2 的第一阶段。
```

## 规则

- Sprint ID 统一使用 `SPRINT-001`、`SPRINT-002` 这种编号格式。
- `requirements-catalog.json` 必须属于单个 Sprint，不要创建项目级需求目录。
- 项目级文件只保存全局索引和当前指针，例如 `harness/project.json`、`harness/source-registry.json`。
- 需求源文件是原始证据。可以读取、引用、索引，但除非用户明确要求，不要修改它们。
- 不要求需求源文件遵守任何模板。
- 机器可读的 Harness 状态优先使用 JSON。
- 范围要收紧：当前 Sprint 只包含用户提供的源文件和用户在本次请求里明确补充的需求。
- 附件文档生成规则只作为文档职责和写法参考；用户规则优先。
- 不强制生成所有 `docs/` 文档；没有证据来源的 Markdown 文档不要生成空模板。
- 不生成 `docs/roadmap.md`。

## 输出目录

创建或更新：

```text
AGENTS.md
docs/                  # 按证据可选创建
  product.md           # 有产品、用户、功能、价值、约束或验收信息时创建
  architecture.md      # 有技术结构、模块、数据流、外部依赖或部署/安全信息时创建
  ui-design.md         # 有 UI、页面、交互、视觉、组件或响应式信息时创建
harness/
  project.json
  source-registry.json
  sprints/
    SPRINT-001/
      sprint.json
      sources.json
      requirements-catalog.json
      tasks.json
      traceability.json
      verification-plan.json
      verification-report.json
      changes.jsonl
      refresh-report.json
      decisions.jsonl
```

不要创建全局 Sprint Manifest。每个 Sprint 用自己的 `sprint.json` 记录 Sprint 信息。

## ID 规则

所有生成 ID 都要带上 Sprint 编号：

```text
REQ-001-001
AC-001-001
TASK-001-001
VER-001-001
```

ID 一旦创建就应保持稳定。后续如果只是改措辞，保留原 ID，只更新记录内容。

## 工作流程

1. 解析用户输入的 Sprint ID、需求源文件列表、目标、依赖和范围说明。
2. 只读取用户指定的源文件。如果某个源文件不存在，停止并报告缺失文件。
3. 从源文件中抽取需求候选项，并分配 `REQ` ID。
4. 为每条需求创建验收标准，并分配 `AC` ID。
5. 创建聚焦的小任务，并分配 `TASK` ID。每个任务至少引用一个 `REQ`。
6. 创建追踪记录，连接 `REQ -> TASK -> AC -> VER`。
7. 创建验证计划，写清楚命令或人工检查方式。
8. 初始化空的验证报告。
9. 初始化空的 `changes.jsonl` 和 `refresh-report.json`，用于后续 Sprint 进行中的需求刷新。
10. 更新 `harness/project.json` 的 `current_sprint`。
11. 更新 `harness/source-registry.json`，登记本 Sprint 的源文件。
12. 按证据可选生成 `docs/` Markdown 文档；只生成输入需求或现有代码能支撑的文档。
13. 初始化或更新根目录 `AGENTS.md`，让它成为短入口，只指向当前 Sprint、核心工作规则和实际存在的 `docs/` 文档。
14. 如果存在 Harness 校验脚本，运行：

```bash
python3 .agents/skills/harness-verify/scripts/verify_harness.py harness/sprints/SPRINT-001
```

15. 最后输出 `Sprint 已就绪`，或列出简短的阻塞问题清单。

## docs/ 文档生成规则

`docs/` 是解释层，面向人和 AI 理解项目；Harness JSON 是执行层，面向 Codex 执行、校验、追踪。二者不要互相替代。

生成 Markdown 文档时遵守：

- 只根据输入需求源文件、用户本次补充说明、现有代码中可验证的信息生成。
- 不凭空补充需求文档没有的信息；缺失内容写入 `requirements-catalog.json` 的 `status: "needs_clarification"`、相关记录备注，或写入 `decisions.jsonl`。
- 每个文档职责单一，不重复其他文档内容，通过引用关联。
- 所有文档放在 `docs/` 下，使用 Markdown，中文撰写，技术术语保留英文。
- 只生成有证据来源的文档；没有对应内容就不创建文件。

各文档生成条件：

- `docs/product.md`：当输入文档包含产品目标、用户、痛点、功能、价值、约束或验收标准时生成。只回答“做什么、为什么做、给谁做”。
- `docs/architecture.md`：当输入文档或现有代码能推导出技术结构、模块、数据流、外部依赖、部署或安全约束时生成。只回答“系统怎么组织”。
- `docs/ui-design.md`：当需求涉及 UI、页面、交互、视觉、组件或响应式时生成。无 UI 项目不生成。
- `docs/task.md`：默认不生成，避免和 `harness/sprints/SPRINT-*/tasks.json` 重复。只有用户明确需要人类可读任务清单时才生成。
- `docs/learnings.md`：初始化时不生成。只有开发中产生真实经验记录时再创建。
- `docs/agents.md`：默认不生成。根目录 `AGENTS.md` 作为 Codex 短入口；只有用户明确需要更详细 AI 开发指引时才生成。
- `docs/roadmap.md`：不生成。

## AGENTS.md 初始化规则

`AGENTS.md` 必须短，像目录和工作协议，不要写成项目百科。参考 Karpathy 风格的四个原则：先想清楚、保持简单、精准修改、用验证闭环。

如果根目录没有 `AGENTS.md`，创建一个短文件：

```md
# AGENTS.md

## 工作原则
- 先确认假设；不清楚就问。
- 优先简单方案，不做未要求的功能。
- 只修改当前任务需要的文件，保持现有风格。
- 每个任务都要有可验证的完成标准。

## Harness
- 当前 Sprint：harness/sprints/SPRINT-001/sprint.json
- 当前任务：harness/sprints/SPRINT-001/tasks.json
- 追踪关系：harness/sprints/SPRINT-001/traceability.json
- 验证计划：harness/sprints/SPRINT-001/verification-plan.json

## 文档入口
- 只列出实际存在的 `docs/` 文档；不要引用不存在的文件。

## 开发循环
- 开发前运行 harness-verify。
- 只做当前 Sprint 范围内的任务。
- 需求源文件变化时，先运行 harness-refresh。
- 验证通过后更新报告、任务状态和提交记录。
```

如果根目录已有 `AGENTS.md`：

- 不要覆盖用户原有规则。
- 如果已有 Harness 段落，只更新当前 Sprint 指针。
- 如果没有 Harness 段落，在文件末尾追加一个简短 `## Harness` 段落。
- `AGENTS.md` 只列出实际存在的 `docs/` 文档入口。
- 保持整个 `AGENTS.md` 精简；详细规则留在 `.agents/skills/` 和 `harness/sprints/SPRINT-*/` 中。

## JSON 约定

`sprint.json`：

```json
{
  "sprint_id": "SPRINT-001",
  "goal": "实现支付流程 V2 第一阶段",
  "status": "initializing",
  "depends_on": [],
  "scope": {
    "included": [],
    "excluded": []
  }
}
```

`requirements-catalog.json`：

```json
{
  "sprint_id": "SPRINT-001",
  "requirements": [
    {
      "req_id": "REQ-001-001",
      "title": "用户可以选择支付方式",
      "description": "一句简短的需求说明。",
      "type": "functional",
      "status": "ready",
      "source_refs": [
        {
          "source_id": "SRC-001-001",
          "file": "docs/payment-v2.md",
          "quote": "来自源文件的简短证据引用或转述。"
        }
      ],
      "acceptance_criteria": [
        {
          "ac_id": "AC-001-001",
          "text": "用户可以在支付页看到可用支付方式。"
        }
      ]
    }
  ]
}
```

`sources.json`：

```json
{
  "sprint_id": "SPRINT-001",
  "sources": [
    {
      "source_id": "SRC-001-001",
      "file": "docs/payment-v2.md",
      "role": "initial",
      "status": "active",
      "first_seen_sprint": "SPRINT-001",
      "added_in_change_id": null,
      "last_read_sha256": "文件内容的 sha256",
      "last_read_size": 1234,
      "last_read_at": "2026-05-12T00:00:00Z",
      "notes": "原始需求源文件，不由 Harness 自动改写。"
    }
  ]
}
```

`harness/source-registry.json`：

```json
{
  "sources": [
    {
      "source_id": "SRC-001-001",
      "file": "docs/payment-v2.md",
      "first_sprint": "SPRINT-001",
      "latest_sprint": "SPRINT-001",
      "status": "active"
    }
  ]
}
```

`tasks.json`：

```json
{
  "sprint_id": "SPRINT-001",
  "tasks": [
    {
      "task_id": "TASK-001-001",
      "title": "实现支付方式选择器",
      "source_req_ids": ["REQ-001-001"],
      "status": "ready",
      "verification": ["VER-001-001"],
      "commit": null
    }
  ]
}
```

`traceability.json`：

```json
{
  "sprint_id": "SPRINT-001",
  "links": [
    {
      "req_id": "REQ-001-001",
      "task_ids": ["TASK-001-001"],
      "ac_ids": ["AC-001-001"],
      "verification_ids": ["VER-001-001"],
      "status": "ready"
    }
  ]
}
```

## 最佳实践倾向

优先使用轻量规则：`REQ -> TASK -> VERIFY -> COMMIT`。初始化时不要引入 Scrum 仪式、故事点、重型 RTM 工具，或复杂的多 Agent DAG 编排。

只有当用户追问为什么这样设计时，才读取 `references/lightweight-harness-rules.md`。
