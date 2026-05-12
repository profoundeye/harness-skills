#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SPRINT_RE = re.compile(r"^SPRINT-(\d{3})$")


def load_json(path, errors):
    if not path.exists():
        errors.append(f"缺少文件：{path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"JSON 格式错误：{path}: {exc}")
        return None


def as_list(value):
    return value if isinstance(value, list) else []


def resolve_source_path(file_value, project_root):
    path = Path(file_value)
    return path if path.is_absolute() else project_root / path


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_root_for_sprint(sprint_dir):
    if sprint_dir.parent.name == "sprints" and sprint_dir.parent.parent.name == "harness":
        return sprint_dir.parent.parent.parent
    return Path.cwd()


def collect_acceptance(requirements):
    ac_ids = set()
    req_to_ac = {}
    for req in requirements:
        ids = set()
        for ac in as_list(req.get("acceptance_criteria")):
            ac_id = ac.get("ac_id")
            if ac_id:
                ids.add(ac_id)
                ac_ids.add(ac_id)
        req_to_ac[req.get("req_id")] = ids
    return ac_ids, req_to_ac


def verify(sprint_dir):
    errors = []
    warnings = []
    sprint_dir = Path(sprint_dir)
    project_root = project_root_for_sprint(sprint_dir)

    sprint = load_json(sprint_dir / "sprint.json", errors) or {}
    sources = load_json(sprint_dir / "sources.json", errors) or {}
    catalog = load_json(sprint_dir / "requirements-catalog.json", errors) or {}
    tasks_doc = load_json(sprint_dir / "tasks.json", errors) or {}
    trace_doc = load_json(sprint_dir / "traceability.json", errors) or {}
    verification_plan = load_json(sprint_dir / "verification-plan.json", errors) or {}
    report_path = sprint_dir / "verification-report.json"
    if report_path.exists():
        load_json(report_path, errors)

    sprint_id = sprint.get("sprint_id")
    if not sprint_id:
        errors.append("sprint.json 缺少 sprint_id")
    elif not SPRINT_RE.match(sprint_id):
        errors.append(f"sprint_id 必须符合 SPRINT-NNN：{sprint_id}")
    elif sprint_dir.name != sprint_id:
        errors.append(f"Sprint 目录名 {sprint_dir.name} 与 sprint_id {sprint_id} 不一致")

    agents_path = project_root / "AGENTS.md"
    if not agents_path.exists():
        errors.append(f"缺少 AGENTS.md：{agents_path}")
    elif sprint_id:
        agents_text = agents_path.read_text(encoding="utf-8")
        expected_sprint_path = f"harness/sprints/{sprint_id}"
        if expected_sprint_path not in agents_text:
            errors.append(f"AGENTS.md 未指向当前 Sprint：{expected_sprint_path}")

    for name, doc in [
        ("sources.json", sources),
        ("requirements-catalog.json", catalog),
        ("tasks.json", tasks_doc),
        ("traceability.json", trace_doc),
        ("verification-plan.json", verification_plan),
    ]:
        if sprint_id and doc.get("sprint_id") and doc.get("sprint_id") != sprint_id:
            errors.append(f"{name} 的 sprint_id {doc.get('sprint_id')} 与 {sprint_id} 不一致")

    source_items = as_list(sources.get("sources"))
    if not source_items:
        errors.append("sources.json 至少需要包含一个 source")

    requirements = as_list(catalog.get("requirements"))
    tasks = as_list(tasks_doc.get("tasks"))
    links = as_list(trace_doc.get("links"))
    verifications = as_list(verification_plan.get("verifications"))

    if not requirements:
        errors.append("requirements-catalog.json 至少需要包含一条 requirement")
    if not tasks:
        errors.append("tasks.json 至少需要包含一个 task")
    if not links:
        errors.append("traceability.json 至少需要包含一条 link")
    if not verifications:
        errors.append("verification-plan.json 至少需要包含一个 verification")

    req_ids = [req.get("req_id") for req in requirements if req.get("req_id")]
    task_ids = [task.get("task_id") for task in tasks if task.get("task_id")]
    verification_ids = [item.get("verification_id") for item in verifications if item.get("verification_id")]
    ac_ids, req_to_ac = collect_acceptance(requirements)

    for label, values in [("需求", req_ids), ("任务", task_ids), ("验证项", verification_ids)]:
        duplicates = sorted({value for value in values if values.count(value) > 1})
        for duplicate in duplicates:
            errors.append(f"重复的{label} ID：{duplicate}")

    req_set = set(req_ids)
    task_set = set(task_ids)
    verification_set = set(verification_ids)
    source_ids = [source.get("source_id") for source in source_items if source.get("source_id")]
    source_set = set(source_ids)

    sprint_num = SPRINT_RE.match(sprint_id).group(1) if sprint_id and SPRINT_RE.match(sprint_id) else None
    if sprint_num:
        for source_id in source_set:
            if not source_id.startswith(f"SRC-{sprint_num}-"):
                errors.append(f"源文件 ID 与 Sprint 编号不一致：{source_id}")
        for req_id in req_set:
            if not req_id.startswith(f"REQ-{sprint_num}-"):
                errors.append(f"需求 ID 与 Sprint 编号不一致：{req_id}")
        for task_id in task_set:
            if not task_id.startswith(f"TASK-{sprint_num}-"):
                errors.append(f"任务 ID 与 Sprint 编号不一致：{task_id}")
        for ac_id in ac_ids:
            if not ac_id.startswith(f"AC-{sprint_num}-"):
                errors.append(f"验收标准 ID 与 Sprint 编号不一致：{ac_id}")
        for verification_id in verification_set:
            if not verification_id.startswith(f"VER-{sprint_num}-"):
                errors.append(f"验证项 ID 与 Sprint 编号不一致：{verification_id}")

    duplicate_sources = sorted({value for value in source_ids if source_ids.count(value) > 1})
    for duplicate in duplicate_sources:
        errors.append(f"重复的源文件 ID：{duplicate}")

    for source in source_items:
        source_id = source.get("source_id", "<缺少 source_id>")
        file_value = source.get("file")
        if not file_value:
            errors.append(f"{source_id} 缺少 file")
            continue
        if not source.get("status"):
            errors.append(f"{source_id} 缺少 status")
        expected_hash = source.get("last_read_sha256")
        expected_size = source.get("last_read_size")
        if not expected_hash:
            errors.append(f"{source_id} 缺少 last_read_sha256")
        if not isinstance(expected_size, int):
            errors.append(f"{source_id} 缺少 last_read_size 或类型不是整数")

        source_path = resolve_source_path(file_value, project_root)
        if not source_path.exists():
            errors.append(f"{source_id} 指向的源文件不存在：{file_value}")
            continue

        if expected_hash and isinstance(expected_size, int):
            current_hash = sha256_file(source_path)
            current_size = source_path.stat().st_size
            if current_hash != expected_hash or current_size != expected_size:
                errors.append(
                    f"{source_id} 源文件内容已变化，请运行 harness-refresh：{file_value}"
                )

    for req in requirements:
        req_id = req.get("req_id", "<缺少 req_id>")
        if not req.get("title"):
            errors.append(f"{req_id} 缺少 title")
        if not as_list(req.get("source_refs")):
            errors.append(f"{req_id} 缺少 source_refs")
        for source_ref in as_list(req.get("source_refs")):
            source_id = source_ref.get("source_id")
            if source_id not in source_set:
                errors.append(f"{req_id} 引用了不存在的源文件 {source_id}")
        if not as_list(req.get("acceptance_criteria")):
            errors.append(f"{req_id} 缺少 acceptance_criteria")

    for task in tasks:
        task_id = task.get("task_id", "<缺少 task_id>")
        refs = as_list(task.get("source_req_ids"))
        if not refs:
            errors.append(f"{task_id} 缺少 source_req_ids")
        for req_id in refs:
            if req_id not in req_set:
                errors.append(f"{task_id} 引用了不存在的需求 {req_id}")

    linked_reqs = set()
    linked_tasks = set()
    linked_acs = set()
    linked_verifications = set()

    for link in links:
        req_id = link.get("req_id")
        if req_id not in req_set:
            errors.append(f"追踪记录引用了不存在的需求 {req_id}")
        else:
            linked_reqs.add(req_id)

        for task_id in as_list(link.get("task_ids")):
            if task_id not in task_set:
                errors.append(f"{req_id} 的追踪记录引用了不存在的任务 {task_id}")
            else:
                linked_tasks.add(task_id)

        for ac_id in as_list(link.get("ac_ids")):
            if ac_id not in ac_ids:
                errors.append(f"{req_id} 的追踪记录引用了不存在的验收标准 {ac_id}")
            else:
                linked_acs.add(ac_id)

        for verification_id in as_list(link.get("verification_ids")):
            if verification_id not in verification_set:
                errors.append(f"{req_id} 的追踪记录引用了不存在的验证项 {verification_id}")
            else:
                linked_verifications.add(verification_id)

    for req_id in sorted(req_set - linked_reqs):
        errors.append(f"{req_id} 没有追踪记录")
    for task_id in sorted(task_set - linked_tasks):
        errors.append(f"{task_id} 没有追踪记录")
    for ac_id in sorted(ac_ids - linked_acs):
        errors.append(f"{ac_id} 没有追踪记录")
    for verification_id in sorted(verification_set - linked_verifications):
        warnings.append(f"{verification_id} 没有被 traceability.json 引用")

    result = {
        "sprint_id": sprint_id,
        "sprint_dir": str(sprint_dir),
        "project_root": str(project_root),
        "ready": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "sources": len(source_items),
            "requirements": len(req_set),
            "acceptance_criteria": len(ac_ids),
            "tasks": len(task_set),
            "verifications": len(verification_set),
            "traceability_links": len(links),
        },
    }
    return result


def main():
    parser = argparse.ArgumentParser(description="校验 Sprint Harness 目录。")
    parser.add_argument("sprint_dir", help="harness/sprints/SPRINT-NNN 的路径")
    args = parser.parse_args()

    result = verify(args.sprint_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
