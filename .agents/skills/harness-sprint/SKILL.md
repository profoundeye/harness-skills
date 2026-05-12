---
name: harness-sprint
description: "通过 Harness 循环执行编号 Sprint 的开发。用户输入 $harness-sprint，或要求 Codex 根据 tasks.json 开始 Sprint 开发、选择任务、实现、验证、失败重试、更新追踪、写验证报告、并为每个完成任务提交一个 Git 提交时使用。"
---

# Harness Sprint 开发

按任务逐个开发当前 Sprint，循环方式是：选择任务、实现、验证、更新记录、提交。

## 定位上下文

如果用户没有指定 Sprint，读取 `harness/project.json`，使用其中的 `current_sprint`。

然后读取：

```text
harness/sprints/SPRINT-001/sprint.json
harness/sprints/SPRINT-001/tasks.json
harness/sprints/SPRINT-001/traceability.json
harness/sprints/SPRINT-001/verification-plan.json
harness/sprints/SPRINT-001/requirements-catalog.json
AGENTS.md
```

## 任务循环

对每个 ready 任务执行：

1. 确认任务关联的需求和验收标准。
2. 修改前先阅读相关代码。
3. 只实现当前任务范围内的内容。
4. 先运行最小相关验证。
5. 如果验证失败，修复后重跑，直到通过或确认存在真实阻塞。
6. 当改动风险较高时，再运行更广的检查。
7. 更新 `verification-report.json`，记录命令、结果、时间和备注。
8. 更新 `tasks.json`，把任务状态改为 `done`，提交后记录 commit hash。
9. 更新 `traceability.json` 中已完成链路的状态。
10. 为完成的任务创建一个聚焦的 Git commit。

提交信息格式：

```text
feat: TASK-001-001 实现支付方式选择器
```

如果能明显判断类型，使用合适的提交类型前缀：`feat`、`fix`、`test`、`docs`、`refactor`、`chore`。

## 子进程

只有当用户在当前请求里明确要求使用子进程、子 Agent、委派或并行开发时，才启动子进程。允许启动时，把独立任务按互不重叠的文件所有权拆分，并提醒子进程不要回滚其他人的改动。

## 验证完整性

- 没有验证证据的任务不能算完成。
- 纯文档改动可以跳过代码测试，但必须在 `verification-report.json` 记录跳过原因。
- 如果缺少验证命令，先补充 `verification-plan.json`，再把任务标记为完成。
- 如果任务暴露出需求缺失或歧义，把任务标记为 `blocked`，并在 `decisions.jsonl` 中写一条简短记录。

## Git 安全

- 不要回滚与当前任务无关的用户改动。
- 提交前先检查 `git status`。
- 只暂存与当前完成任务相关的文件。
- 如果存在无关脏文件，保持不动，并在最终回复中说明。

## 最终输出

报告以下内容：

- Sprint ID
- 已完成的任务 ID
- 已运行的验证
- 每个完成任务对应的提交哈希
- 阻塞或延期任务
