---
name: harness-garden
description: "长期维护轻量 Codex Harness 记录。用户输入 $harness-garden，或要求清理、审查、修复、刷新 Sprint Harness 状态、过期 JSON 记录、源文件登记表、重复 ID、孤立需求、延期任务、旧验证报告、AGENTS.md Sprint 指针时使用。"
---

# Harness 整理

在不改变产品行为的前提下，清理和改进 Harness 记录。

## 工作流程

1. 读取 `harness/project.json`、`harness/source-registry.json`，以及所有 `harness/sprints/SPRINT-*/` 目录。
2. 如果可用，对活跃或最近变更过的 Sprint 运行 `harness-verify`。
3. 找出陈旧或不一致记录：
   - 重复 ID
   - 孤立需求
   - 没有源需求的任务
   - 没有验证的验收标准
   - 已完成但没有提交哈希的任务
   - 没有命令证据的验证报告
   - `AGENTS.md` 当前 Sprint 指针不一致
4. 提出最小修复方案。
5. 只有当用户要求清理、修复或维护时，才 patch JSON。
6. 除非用户明确要求，不要编辑原始需求源文件。

## 维护倾向

优先做小而机械的更新，不做大规模重构。项目级文件只做索引和指针，Sprint 专属状态都放在各自 Sprint 目录里。

## 输出

使用：

```text
Harness 整理报告

健康：
- SPRINT-001 追踪链通过校验

需要清理：
- SPRINT-002 的 TASK-002-003 已完成，但没有提交哈希
- AGENTS.md 指向 SPRINT-001，但 project.json 的 current_sprint 是 SPRINT-002

已应用：
- 更新 project.json 的 current_sprint
```
