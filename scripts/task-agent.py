#!/usr/bin/env python3
"""
task-agent.py — TaskPad 任务理解 + 调研 + 分解执行引擎

这个脚本不是一个独立的运行程序，而是一个可以被 Agent 调用的辅助工具。
它提供：
1. task_id 生成（基于时间戳）
2. 方案解析与校验
3. 步骤状态管理
4. 执行历史记录

用法（被 Agent 调用）:
  python3 task-agent.py init <task-desc>     # 初始化任务
  python3 task-agent.py status <task-id>     # 查看任务状态
  python3 task-agent.py next <task-id>       # 获取下一步
  python3 task-agent.py complete <task-id> <step>  # 标记步骤完成
  python3 task-agent.py fail <task-id> <step>      # 标记步骤失败
"""

import json
import os
import sys
from datetime import datetime

WORKBENCH = os.path.expanduser("~/.openclaw/workspace/workbench")


def ensure_task_dir(task_id):
    """确保任务目录存在"""
    task_dir = os.path.join(WORKBENCH, task_id)
    os.makedirs(os.path.join(task_dir, "steps"), exist_ok=True)
    os.makedirs(os.path.join(task_dir, "artifacts"), exist_ok=True)
    return task_dir


def generate_task_id(desc: str) -> str:
    """生成可读的任务 ID"""
    ts = datetime.now().strftime("%H%M%S")
    # 取描述前 3 个中文/英文词做前缀
    short = "".join(c for c in desc[:12] if c.isalnum() or '\u4e00' <= c <= '\u9fff')
    return f"tsk-{short}-{ts}"


def cmd_init(args):
    """初始化新任务"""
    desc = " ".join(args) if args else "unnamed"
    task_id = generate_task_id(desc)
    task_dir = ensure_task_dir(task_id)

    # 创建理解文档
    understanding = {
        "task_id": task_id,
        "task_description": desc,
        "status": "understood",
        "created_at": datetime.now().isoformat(),
        "steps": []
    }
    with open(os.path.join(task_dir, "understanding.md"), "w") as f:
        f.write(f"# 任务理解确认\n\n")
        f.write(f"- 任务ID: {task_id}\n")
        f.write(f"- 描述: {desc}\n")
        f.write(f"- 状态: 已理解，等待用户确认\n")
        f.write(f"- 创建时间: {datetime.now().isoformat()}\n")

    print(f"✅ 任务已初始化: {task_id}")
    print(f"📋 {desc}")
    print(f"📁 {task_dir}")
    print(f"\n确认理解后执行:")
    print(f"  python3 {sys.argv[0]} plan {task_id} '<方案描述>'")


def cmd_plan(args):
    """设置执行方案（由调研器生成的方案）"""
    if len(args) < 2:
        print("用法: task-agent.py plan <task-id> '<json-plan>'")
        sys.exit(1)

    task_id = args[0]
    plan_json = " ".join(args[1:])
    task_dir = ensure_task_dir(task_id)

    try:
        plan = json.loads(plan_json)
    except json.JSONDecodeError:
        # 不是 JSON，当纯文本处理
        plan = {"description": plan_json, "steps": []}

    with open(os.path.join(task_dir, "plan.md"), "w") as f:
        f.write(f"# 执行方案\n\n")
        f.write(f"- 任务ID: {task_id}\n")
        f.write(f"- 状态: ready\n\n")

        if "steps" in plan and isinstance(plan["steps"], list):
            for i, step in enumerate(plan["steps"], 1):
                desc = step.get("description", step) if isinstance(step, dict) else step
                dep = step.get("dependencies", []) if isinstance(step, dict) else []
                est = step.get("estimated_minutes", "?") if isinstance(step, dict) else "?"
                f.write(f"## 步骤 {i}\n")
                f.write(f"- 描述: {desc}\n")
                f.write(f"- 预估: {est}min\n")
                f.write(f"- 依赖: {', '.join(dep) if dep else '无'}\n")
                f.write(f"- 状态: pending\n\n")

        print(f"✅ 方案已写入: {task_dir}/plan.md")
        print(f"共 {len(plan.get('steps', []))} 个步骤")

    # 初始化检查点
    steps = plan.get("steps", [])
    from scripts.memory_engine import write_checkpoint
    # Shell fallback
    os.system(f"bash {os.path.expanduser('~')}/.openclaw/workspace/skills/taskpad/scripts/memory-engine.sh "
              f"write {task_id} 1 {len(steps)} executing '方案就绪，开始执行'")


def cmd_status(args):
    """查看任务状态"""
    if not args:
        # 列出所有活跃任务
        active_file = os.path.join(WORKBENCH, "_active.json")
        if os.path.exists(active_file):
            with open(active_file) as f:
                data = json.load(f)
            for t in data.get("tasks", []):
                bar = "█" * int(t["progress_pct"] / 5) + "░" * (20 - int(t["progress_pct"] / 5))
                print(f"{t['icon']} {t['task_id']}")
                print(f"   {bar} {t['current_step']}/{t['total_steps']} · {t['progress_pct']}%")
                print(f"   状态: {t['status']} · 更新: {t['updated_at']}")
        else:
            print("📭 没有活跃任务")
        return

    task_id = args[0]
    cp_file = os.path.join(WORKBENCH, task_id, "checkpoint.json")
    if not os.path.exists(cp_file):
        print(f"⚠️ 任务 {task_id} 不存在或没有检查点")
        return

    with open(cp_file) as f:
        cp = json.load(f)

    print(f"\n📋 任务: {cp['task_id']}")
    print(f"进度: {cp['current_step']}/{cp['total_steps']} ({cp['progress_pct']}%)")
    print(f"状态: {cp['status']}")
    if cp.get('last_completed'):
        print(f"上次完成: {cp['last_completed']}")
    print(f"下一步: {cp['next_action']}")


def cmd_next(args):
    """获取下一步操作（用于 Agent 恢复时）"""
    if not args:
        print("用法: task-agent.py next <task-id>")
        sys.exit(1)

    task_id = args[0]
    cp_file = os.path.join(WORKBENCH, task_id, "checkpoint.json")
    if not os.path.exists(cp_file):
        print(f"⚠️ 任务 {task_id} 没有检查点")
        sys.exit(1)

    with open(cp_file) as f:
        cp = json.load(f)

    print(f"▶️ 下一步: {cp['next_action']}")
    print(f"步骤 {cp['current_step']}/{cp['total_steps']}")

    plan_file = os.path.join(WORKBENCH, task_id, "plan.md")
    if os.path.exists(plan_file):
        with open(plan_file) as f:
            lines = f.readlines()
        # 找到当前步骤的描述
        current = cp['current_step']
        for i, line in enumerate(lines):
            if f"## 步骤 {current}" in line:
                # 打印接下来的几行
                for j in range(i + 1, min(i + 6, len(lines))):
                    print(f"  {lines[j].strip()}")
                break


def cmd_complete(args):
    """标记步骤完成"""
    if len(args) < 2:
        print("用法: task-agent.py complete <task-id> <step> [detail]")
        sys.exit(1)

    task_id = args[0]
    step = args[1]
    detail = " ".join(args[2:]) if len(args) > 2 else f"步骤 {step} 完成"

    # 读取当前检查点
    cp_file = os.path.join(WORKBENCH, task_id, "checkpoint.json")
    if os.path.exists(cp_file):
        with open(cp_file) as f:
            cp = json.load(f)
        current_step = cp.get("current_step", int(step))
        total_steps = cp.get("total_steps", int(step))
    else:
        current_step = int(step)
        total_steps = int(step)

    # 写步骤完成记录
    step_file = os.path.join(WORKBENCH, task_id, "steps", f"step-{int(step):03d}.md")
    with open(step_file, "w") as f:
        f.write(f"# 步骤 {step}\n\n")
        f.write(f"- 状态: completed\n")
        f.write(f"- 完成时间: {datetime.now().isoformat()}\n")
        f.write(f"- 详情: {detail}\n")

    next_step = int(step) + 1
    if next_step > total_steps:
        # 任务完成
        os.system(f"bash {os.path.expanduser('~')}/.openclaw/workspace/skills/taskpad/scripts/memory-engine.sh "
                  f"write {task_id} {next_step} {total_steps} completed '全部完成'")
        print(f"✅ 任务 {task_id} 全部完成！")
    else:
        os.system(f"bash {os.path.expanduser('~')}/.openclaw/workspace/skills/taskpad/scripts/memory-engine.sh "
                  f"write {task_id} {next_step} {total_steps} executing '{detail}'")
        print(f"✅ 步骤 {step}/{total_steps} 完成")
        print(f"▶️ 下一步: {next_step}")


def cmd_fail(args):
    """标记步骤失败"""
    if len(args) < 2:
        print("用法: task-agent.py fail <task-id> <step> [reason]")
        sys.exit(1)

    task_id = args[0]
    step = args[1]
    reason = " ".join(args[2:]) if len(args) > 2 else "未知错误"

    step_file = os.path.join(WORKBENCH, task_id, "steps", f"step-{int(step):03d}.md")
    with open(step_file, "w") as f:
        f.write(f"# 步骤 {step}\n\n")
        f.write(f"- 状态: failed\n")
        f.write(f"- 失败时间: {datetime.now().isoformat()}\n")
        f.write(f"- 原因: {reason}\n")

    print(f"❌ 步骤 {step} 失败: {reason}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("TaskPad Agent Engine v0.1")
        print("")
        print("用法:")
        print(f"  {sys.argv[0]} init <task-description>")
        print(f"  {sys.argv[0]} plan <task-id> '<json-plan>'")
        print(f"  {sys.argv[0]} status [task-id]")
        print(f"  {sys.argv[0]} next <task-id>")
        print(f"  {sys.argv[0]} complete <task-id> <step> [detail]")
        print(f"  {sys.argv[0]} fail <task-id> <step> [reason]")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "init": cmd_init,
        "plan": cmd_plan,
        "status": cmd_status,
        "next": cmd_next,
        "complete": cmd_complete,
        "fail": cmd_fail,
    }

    if cmd in commands:
        commands[cmd](args)
    else:
        print(f"未知命令: {cmd}")
        sys.exit(1)
