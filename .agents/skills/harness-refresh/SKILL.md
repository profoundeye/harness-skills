---
name: harness-refresh
description: "在 Sprint 进行中刷新 Harness。用户输入 $harness-refresh，或在已修改原需求文档、追加新需求文档、需要重读当前 Sprint 源文件、追加需求、重新规划任务、更新 traceability、生成 changes.jsonl 和 refresh-report.json 时使用。"
---

# Harness 刷新

在 Sprint 已经初始化、甚至已经开始开发之后，把新的需求变化安全地追加到当前 Sprint。刷新时不要无痕覆盖历史，要保留变更记录。

## 输入参数

支持一个源文件处理参数；如果用户不写，就按默认值处理：

```text
source_mode: refresh_existing
```

可选值：

- `refresh_existing`：默认值。重读当前 Sprint 的 `sources.json` 中已有源文件，适合“我直接修改了原来的需求文档”。
- `append_sources`：只追加新的需求源文件，适合“我新增了一个需求文档”。
- `refresh_and_append`：先重读已有源文件，再追加新源文件，适合“我既改了旧文档，又加了新文档”。

中文别名也要识别：

- `刷新原源文件` = `refresh_existing`
- `追加新源文件` = `append_sources`
- `刷新并追加` = `refresh_and_append`

常见输入：

```text
$harness-refresh

Sprint ID: SPRINT-001
source_mode: refresh_existing
说明：
我修改了原来的需求文档，请重新检查当前 Sprint。
```

追加文档时：

```text
$harness-refresh

Sprint ID: SPRINT-001
source_mode: append_sources
追加需求源文件：
- docs/payment-risk-review.md
说明：
新增支付风控补充需求。
```

## 工作原则

- 不要重建整个 Sprint。
- 不要删除已完成任务的历史。
- 不要让新需求无痕覆盖旧需求。
- 已有 `REQ`、`AC`、`TASK`、`VER` ID 尽量保持稳定。
- 新增内容使用新的 ID。
- 对已完成任务产生影响时，新建补充任务，不要改写历史任务为“仿佛一开始就是这样”。
- 每次刷新都要写入 `changes.jsonl`。
- 每次刷新都要更新 `refresh-report.json`。
- 刷新后必须运行 `harness-verify`。

## 需要读取

定位 Sprint 后，读取：

```text
harness/project.json
harness/source-registry.json
harness/sprints/SPRINT-001/sprint.json
harness/sprints/SPRINT-001/sources.json
harness/sprints/SPRINT-001/requirements-catalog.json
harness/sprints/SPRINT-001/tasks.json
harness/sprints/SPRINT-001/traceability.json
harness/sprints/SPRINT-001/verification-plan.json
harness/sprints/SPRINT-001/verification-report.json
harness/sprints/SPRINT-001/changes.jsonl
```

如果用户没有指定 Sprint，就读取 `harness/project.json` 的 `current_sprint`。

## 刷新已有源文件

当 `source_mode` 是 `refresh_existing`：

1. 读取当前 Sprint `sources.json` 中所有 `status = active` 的源文件。
2. 重新计算每个源文件的 `sha256` 和文件大小。
3. 和 `sources.json` 里的 `last_read_sha256`、`last_read_size` 比较。
4. 只处理发生变化的源文件。
5. 抽取新增、修改、删除或冲突的需求。
6. 生成一个 `CHG` 变更记录。
7. 更新受影响的需求、验收标准、任务、追踪链和验证计划。

## 追加新源文件

当 `source_mode` 是 `append_sources`：

1. 要求用户提供 `追加需求源文件` 列表。
2. 检查这些文件是否存在。
3. 为每个新增源文件分配新的 `SRC` ID。
4. 追加到当前 Sprint 的 `sources.json`。
5. 更新项目级 `harness/source-registry.json`。
6. 只从新增源文件中抽取新需求。
7. 为新需求创建新的 `REQ`、`AC`、`TASK`、`VER`。
8. 更新 `traceability.json`。

## 刷新并追加

当 `source_mode` 是 `refresh_and_append`：

1. 先按 `refresh_existing` 处理已有源文件变化。
2. 再按 `append_sources` 处理新增源文件。
3. 在同一个 `refresh-report.json` 中说明两类变化。
4. 可以写入一个或多个 `CHG` 记录，但要保持 ID 连续。

## 变更处理规则

- 新增需求：新增 `REQ`、`AC`、`TASK`、`VER`，并补充追踪链。
- 修改未开始需求：保留原 `REQ` ID，更新说明、验收标准和任务。
- 修改正在开发的需求：把相关任务标记为 `needs_replan`，更新任务说明和验证计划。
- 修改已完成需求：保留已完成任务历史，新建补充任务处理差异。
- 删除或撤销需求：不要直接删除历史记录；将相关需求标记为 `superseded` 或 `cancelled`，并在 `changes.jsonl` 说明原因。
- 范围扩大过大或需求冲突：标记为 `needs_user_confirmation`，让用户决定放进当前 Sprint 还是下个 Sprint。

## changes.jsonl

每次刷新至少追加一行：

```json
{"change_id":"CHG-001-001","sprint_id":"SPRINT-001","source_mode":"refresh_existing","type":"update_sources","summary":"重读已有需求源文件，发现 1 条新增需求","source_files":["docs/payment-v2.md"],"status":"accepted","created_at":"2026-05-12T00:00:00Z"}
```

`CHG` ID 也使用 Sprint 编号：

```text
CHG-001-001
CHG-001-002
```

## refresh-report.json

刷新后写入本次刷新摘要：

```json
{
  "sprint_id": "SPRINT-001",
  "latest_change_id": "CHG-001-001",
  "source_mode": "refresh_existing",
  "changed_sources": ["docs/payment-v2.md"],
  "added_sources": [],
  "impact": {
    "new_requirements": ["REQ-001-004"],
    "updated_requirements": [],
    "cancelled_requirements": [],
    "new_tasks": ["TASK-001-006"],
    "updated_tasks": [],
    "affected_done_tasks": [],
    "needs_user_confirmation": false
  },
  "verify": {
    "command": "python3 .agents/skills/harness-verify/scripts/verify_harness.py harness/sprints/SPRINT-001",
    "status": "passed"
  }
}
```

## 最终输出

输出要简短：

```text
Sprint 已刷新：SPRINT-001

变更：
- CHG-001-001：从 docs/payment-v2.md 新增 1 条需求

影响：
- 新增需求：REQ-001-004
- 新增任务：TASK-001-006

校验：
- harness-verify 通过
```

如果需要用户确认：

```text
Sprint 刷新暂停：SPRINT-001

需要确认：
- 新需求会扩大当前 Sprint 范围，建议延期到 SPRINT-002
```
