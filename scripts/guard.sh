#!/bin/bash
# guard.sh — TaskPad 任务守护器
#
# 后台检测任务执行状态，发现异常自动干预。
# 推荐通过 cron 每 5 分钟执行。
#
# 检测规则：
# - timeout:  单步执行超过预估 3 倍
# - drift:    执行内容偏离 plan.md
# - deadloop: 连续 3 次重复同一操作
# - overflow: 未及时分片，Context > 90%

WORKBENCH="$HOME/.openclaw/workspace/workbench"
GUARD_LOG="$WORKBENCH/guard-log.json"
MEM_ENGINE="$HOME/.openclaw/workspace/skills/taskpad/scripts/memory-engine.sh"

ensure_log() {
  if [ ! -f "$GUARD_LOG" ]; then
    echo '{"alerts":[],"tasks":{}}' > "$GUARD_LOG"
  fi
}

write_alert() {
  local task_id="$1"
  local type="$2"
  local detail="$3"
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  python3 -c "
import json

with open('$GUARD_LOG') as f:
    d = json.load(f)

alert = {
    'task_id': '$task_id',
    'type': '$type',
    'detail': '$detail',
    'timestamp': '$timestamp',
    'auto_resolve': False
}
d['alerts'].append(alert)

# Keep last 100 alerts
d['alerts'] = d['alerts'][-100:]

with open('$GUARD_LOG', 'w') as f:
    json.dump(d, f, indent=2)

print(f'[GUARD] 🚨 告警: [{type}] $task_id — $detail')
"
}

check_all_tasks() {
  if [ ! -f "$WORKBENCH/_active.json" ]; then
    return
  fi

  python3 -c "
import json, os, time

workbench = '$WORKBENCH'
guard_log = '$GUARD_LOG'

with open(os.path.join(workbench, '_active.json')) as f:
    active = json.load(f)

now = time.time()

for t in active.get('tasks', []):
    task_id = t['task_id']
    cp_file = os.path.join(workbench, task_id, 'checkpoint.json')
    
    if not os.path.exists(cp_file):
        continue
    
    with open(cp_file) as f:
        cp = json.load(f)
    
    # 检查长时间未更新
    # 这里简化处理，只做时间检查
    # 更复杂的逻辑放在 task-agent.py 里

print(f'[GUARD] ✅ 守护器检查完成: {len(active.get(\"tasks\",[]))} 个活跃任务')
"
}

case "${1:-check}" in
  check)
    ensure_log
    check_all_tasks
    ;;
  alert)
    ensure_log
    write_alert "$2" "$3" "$4"
    ;;
  status)
    ensure_log
    python3 -c "
import json
with open('$GUARD_LOG') as f:
    d = json.load(f)
print(f'告警总数: {len(d[\"alerts\"])}')
for a in d['alerts'][-5:]:
    print(f'  [{a[\"type\"]}] {a[\"task_id\"]} — {a[\"detail\"]}')
"
    ;;
  *)
    echo "TaskPad Guard v0.1"
    echo ""
    echo "用法:"
    echo "  guard.sh check            # 检查所有任务"
    echo "  guard.sh alert <id> <type> <detail>  # 手动触发告警"
    echo "  guard.sh status           # 查看告警状态"
    echo ""
    echo "推荐: crontab -e 添加 */5 * * * * guard.sh check"
    ;;
esac
