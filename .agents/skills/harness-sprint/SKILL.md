---
name: harness-sprint
description: "通过 Harness 循环执行编号 Sprint 的开发。用户输入 $harness-sprint，或要求 Codex 根据当前 Sprint 的 Harness JSON 开始开发、先校验 Sprint、处理需求源文件变更、选择任务、实现、验证、失败重试、更新追踪、写验证报告、并为每个完成任务提交一个 Git 提交时使用。"
---

# Harness Sprint 开发

按任务逐个开发当前 Sprint，循环方式是：选择任务、实现、验证、更新记录、提交。

## 启动前检查

开始任何开发前：

1. 定位当前 Sprint。
2. 运行 `harness-verify`：

```bash
python3 .agents/skills/harness-verify/scripts/verify_harness.py harness/sprints/SPRINT-001
```

3. 如果校验提示需求源文件已变化，先运行 `harness-refresh`，不要直接开发。
4. 如果存在阻塞问题，先修复 Harness 记录或向用户确认；不要绕过校验。
5. 如果当前目录不是 Git 仓库，可以继续做计划和验证，但任务完成时不能标记为正式提交；在 `verification-report.json` 记录 `commit_skipped_reason`。

## 定位上下文

如果用户没有指定 Sprint，读取 `harness/project.json`，使用其中的 `current_sprint`。

然后读取：

```text
harness/sprints/SPRINT-001/sprint.json
harness/sprints/SPRINT-001/tasks.json
harness/sprints/SPRINT-001/traceability.json
harness/sprints/SPRINT-001/verification-plan.json
harness/sprints/SPRINT-001/requirements-catalog.json
harness/sprints/SPRINT-001/sources.json
harness/sprints/SPRINT-001/verification-report.json
AGENTS.md
```

如果 `AGENTS.md` 引用 `docs/` 文档，只读取实际存在的文档。`docs/` 是可选解释层，不存在时不要当作错误；以 Harness JSON 为执行依据。

## 任务循环

对每个 ready 任务执行：

1. 确认任务关联的需求和验收标准。
2. 确认任务仍属于当前 Sprint 范围，且没有被 `harness-refresh` 标记为 `needs_replan`、`blocked`、`cancelled` 或 `superseded`。
3. 修改前先阅读相关代码和实际存在的相关 `docs/` 文档。
4. 只实现当前任务范围内的内容；不要实现 `docs/roadmap.md` 或未来 Sprint 才需要的内容。
5. 先运行最小相关验证。
6. 如果验证失败，修复后重跑，直到通过或确认存在真实阻塞。
7. 当改动风险较高时，再运行更广的检查。
8. 更新 `verification-report.json`，记录命令、结果、时间和备注。
9. 更新 `tasks.json`，把任务状态改为 `done`，提交后记录提交哈希；如果不是 Git 仓库，记录跳过原因。
10. 更新 `traceability.json` 中已完成链路的状态。
11. 为完成的任务创建一个聚焦的 Git commit；非 Git 仓库只能记录验证结果，不能声称已提交。

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
- 如果发现需求源文件内容已经变化，停止当前任务并运行 `harness-refresh`。
- 不要创建或依赖 `docs/roadmap.md`。
- 不要把 `docs/` 文档缺失当作开发阻塞；只要 Harness JSON 完整并通过校验即可继续。

## Git 安全

- 不要回滚与当前任务无关的用户改动。
- 如果当前目录不是 Git 仓库，不要尝试伪造提交记录。
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
