---
name: harness-verify
description: "在开发前或开发过程中校验编号 Sprint Harness。用户输入 $harness-verify、询问 Sprint 是否就绪、或需要检查 JSON 合法性、需求-任务-验收-验证追踪链、孤立记录、重复 ID、缺失验证证据时使用。"
---

# Harness 校验

校验某个 Sprint Harness 是否内部一致，是否可以进入开发。

## 输入

接受以下任意一种输入：

- Sprint 路径，例如 `harness/sprints/SPRINT-001`
- Sprint ID，例如 `SPRINT-001`
- 如果用户没有指定 Sprint，就读取 `harness/project.json`，使用其中的 `current_sprint`

## 工作流程

1. 定位 Sprint 目录。
2. 运行校验脚本：

```bash
python3 .agents/skills/harness-verify/scripts/verify_harness.py harness/sprints/SPRINT-001
```

3. 如果脚本报告阻塞问题，按文件和 ID 简要总结。
4. 如果用户要求修复问题，用最小改动修补 JSON 记录。
5. 如果脚本通过，报告 `Sprint 已就绪`。

## 就绪规则

只有满足以下条件时，Sprint 才算就绪：

- Sprint ID 符合 `SPRINT-NNN`。
- 根目录存在 `AGENTS.md`，并且指向当前 Sprint。
- 必需 JSON 文件存在，并且可以正常解析。
- 每条需求至少有一个源文件引用。
- `sources.json` 中每个源文件都记录 `source_id`、`file`、`status`、`last_read_sha256`、`last_read_size`。
- 源文件当前内容不能和 `sources.json` 记录的哈希不一致；如果不一致，先运行 `harness-refresh`。
- 每条需求至少有一条验收标准。
- 每个 ready 任务至少引用一条需求。
- 每条追踪记录都引用真实存在的 `REQ`、`TASK`、`AC`、`VER` ID。
- 每条需求的 `source_refs` 都引用真实存在的 `SRC` ID。
- 每条需求至少出现在一条追踪记录中。
- 每个任务至少出现在一条追踪记录中。
- 每条验收标准至少出现在一条追踪记录中。
- 每个验证项都能连接到任务或追踪记录。

## 输出

通过时使用简短输出：

```text
Sprint 已就绪：SPRINT-001
```

未通过时使用：

```text
Sprint 未就绪：SPRINT-001

阻塞问题：
- REQ-001-003 没有对应任务
- TASK-001-002 引用了不存在的 REQ-001-999
- AC-001-004 没有验证链接
```

除非用户明确要求，不要编辑原始需求源文件。
