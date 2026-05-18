#!/usr/bin/env python3
"""
panel-server.py — TaskPad 可视化任务提示板 HTTP 服务器

提供：
- /         → 面板页面 (panel.html)
- /api/tasks → JSON 任务列表
- /api/task/<id> → 单个任务详情
- /api/action → 任务操作接口

启动:
  python3 panel-server.py [port]
  默认端口: 19999
"""

import json
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

WORKBENCH = os.path.expanduser("~/.openclaw/workspace/workbench")
SKILL_DIR = os.path.expanduser("~/.openclaw/workspace/skills/taskpad")


class TaskPadHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    def log_message(self, format, *args):
        """静默日志，只打印重要信息"""
        pass

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _send_html(self, html, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _read_file(self, path):
        try:
            with open(path) as f:
                return f.read()
        except Exception:
            return None

    def do_GET(self):
        if self.path == "/" or self.path == "/panel":
            # 返回面板页面
            html = self._read_file(os.path.join(SKILL_DIR, "web", "panel.html"))
            if html:
                self._send_html(html)
            else:
                self._send_html("<h1>TaskPad Panel</h1><p>panel.html not found</p>", 404)

        elif self.path.startswith("/api/tasks"):
            # 返回任务列表
            tasks = []
            active_file = os.path.join(WORKBENCH, "_active.json")
            if os.path.exists(active_file):
                with open(active_file) as f:
                    data = json.load(f)
                tasks = data.get("tasks", [])

            # 补充详情
            enriched = []
            for t in tasks:
                cp_file = os.path.join(WORKBENCH, t["task_id"], "checkpoint.json")
                detail = {}
                if os.path.exists(cp_file):
                    with open(cp_file) as f:
                        detail = json.load(f)
                enriched.append({**t, **detail})

            # 扫描目录获取不在活跃列表中的任务
            if os.path.exists(WORKBENCH):
                for entry in os.listdir(WORKBENCH):
                    task_dir = os.path.join(WORKBENCH, entry)
                    cp_file = os.path.join(task_dir, "checkpoint.json")
                    if os.path.isdir(task_dir) and entry.startswith("tsk-") and os.path.exists(cp_file):
                        if not any(t["task_id"] == entry for t in enriched):
                            with open(cp_file) as f:
                                detail = json.load(f)
                            enriched.append(detail)

            self._send_json({"tasks": enriched, "count": len(enriched)})

        elif self.path.startswith("/api/task/"):
            # 返回单个任务详情
            task_id = self.path[len("/api/task/"):]
            cp_file = os.path.join(WORKBENCH, task_id, "checkpoint.json")
            plan_file = os.path.join(WORKBENCH, task_id, "plan.md")
            understanding_file = os.path.join(WORKBENCH, task_id, "understanding.md")

            data = {"task_id": task_id, "exists": False}

            if os.path.exists(cp_file):
                with open(cp_file) as f:
                    data.update(json.load(f))
                data["exists"] = True

            if os.path.exists(plan_file):
                with open(plan_file) as f:
                    data["plan"] = f.read()[:2000]  # 限制大小

            if os.path.exists(understanding_file):
                with open(understanding_file) as f:
                    data["understanding"] = f.read()[:1000]

            # 列出步骤
            steps_dir = os.path.join(WORKBENCH, task_id, "steps")
            if os.path.exists(steps_dir):
                steps = sorted(os.listdir(steps_dir))
                data["steps"] = steps
                # 读取最新步骤的内容
                if steps:
                    last_step = os.path.join(steps_dir, steps[-1])
                    with open(last_step) as f:
                        data["last_step_content"] = f.read()[:1000]

            self._send_json(data)

        elif self.path == "/api/status":
            # 系统状态
            active_count = 0
            if os.path.exists(os.path.join(WORKBENCH, "_active.json")):
                with open(os.path.join(WORKBENCH, "_active.json")) as f:
                    active_count = len(json.load(f).get("tasks", []))

            self._send_json({
                "status": "running",
                "workbench": WORKBENCH,
                "active_tasks": active_count,
                "timestamp": datetime.now().isoformat()
            })

        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/action":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                body = self.rfile.read(content_length)
                try:
                    data = json.loads(body)
                    action = data.get("action", "")
                    task_id = data.get("task_id", "")

                    mem_engine = os.path.join(SKILL_DIR, "scripts", "memory-engine.sh")
                    cp_file = os.path.join(WORKBENCH, task_id, "checkpoint.json")

                    if action == "pause":
                        os.system(f"bash {mem_engine} write {task_id} 0 0 paused '用户手动暂停'")
                        self._send_json({"success": True, "message": "任务已暂停"})

                    elif action == "resume":
                        os.system(f"bash {mem_engine} write {task_id} 0 0 executing '用户手动恢复'")
                        self._send_json({"success": True, "message": "任务已恢复"})

                    elif action == "stop":
                        os.system(f"bash {mem_engine} write {task_id} 0 0 cancelled '用户手动取消'")
                        self._send_json({"success": True, "message": "任务已取消"})

                    elif action == "note" and "note" in data:
                        # 添加备注到任务
                        note_file = os.path.join(WORKBENCH, task_id, "notes.md")
                        with open(note_file, "a") as f:
                            f.write(f"\n## {datetime.now().isoformat()}\n")
                            f.write(f"{data['note']}\n")
                        self._send_json({"success": True, "message": "备注已添加"})

                    else:
                        self._send_json({"success": False, "error": f"未知操作: {action}"}, 400)

                except json.JSONDecodeError:
                    self._send_json({"success": False, "error": "JSON 格式错误"}, 400)
            else:
                self._send_json({"success": False, "error": "请求体为空"}, 400)
        else:
            self._send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def run_server(port=19999):
    server = HTTPServer(("0.0.0.0", port), TaskPadHandler)
    print(f"🦞 TaskPad Panel Server running on http://localhost:{port}")
    print(f"   📋 任务列表: http://localhost:{port}/api/tasks")
    print(f"   🖥️  面板: http://localhost:{port}/")
    print(f"   ⚡ 状态: http://localhost:{port}/api/status")
    print("   Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
        server.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 19999
    run_server(port)
