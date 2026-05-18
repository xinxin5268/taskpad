#!/bin/bash
# memory-engine.sh — TaskPad 临时记忆自动机
# 
# 功能：
# 1. write_checkpoint: 写入当前任务检查点
# 2. read_checkpoint:   读取上次检查点，输出恢复提示
# 3. list_active:       列出所有活跃任务
# 4. clean_task:        清理已完成/已取消的任务
#
# 用法：
#   memory-engine.sh write <task-id> <current-step> <total-steps> <status> [detail]
#   memory-engine.sh read <task-id>
#   memory-engine.sh list
#   memory-engine.sh clean

WORKBENCH="$HOME/.openclaw/workspace/workbench"
TASK_DIR="$WORKBENCH/$2"

ensure_dir() {
  mkdir -p "$WORKBENCH"
}

write_checkpoint() {
  local task_id="$1"
  local current_step="$2"
  local total_steps="$3"
  local status="$4"    # executing / paused / completed / cancelled
  local detail="${5:-}"
  local timestamp
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

  mkdir -p "$WORKBENCH/$task_id/steps" "$WORKBENCH/$task_id/artifacts"

  # Read previous checkpoint if exists
  local prev_next_action=""
  if [ -f "$WORKBENCH/$task_id/checkpoint.json" ]; then
    prev_next_action=$(python3 -c "
import json
try:
    with open('$WORKBENCH/$task_id/checkpoint.json') as f:
        d = json.load(f)
    print(d.get('next_action', ''))
except: pass
" 2>/dev/null)
  fi

  cat > "$WORKBENCH/$task_id/checkpoint.json" << EOF
{
  "task_id": "$task_id",
  "status": "$status",
  "current_step": $current_step,
  "total_steps": $total_steps,
  "completed_steps_count": $((current_step - 1)),
  "progress_pct": $(( (current_step - 1) * 100 / total_steps )),
  "detail": "$detail",
  "last_completed": "$detail",
  "next_action": "继续执行步骤 $current_step",
  "timestamp": "$timestamp",
  "prev_next_action": "$prev_next_action"
}
EOF

  # Update active index
  update_active_index "$task_id" "$status" "$current_step" "$total_steps"
  
  echo "[MEMORY] ✅ 检查点已写入: $task_id (步骤 $current_step/$total_steps)"
}

read_checkpoint() {
  local task_id="$1"
  
  if [ ! -f "$WORKBENCH/$task_id/checkpoint.json" ]; then
    echo "[MEMORY] ⚠️ 未找到检查点: $task_id"
    return 1
  fi

  python3 -c "
import json

with open('$WORKBENCH/$task_id/checkpoint.json') as f:
    d = json.load(f)

print('')
print('┌──────────────────────────────────────────────┐')
print('│  🔄 检测到未完成任务！                         │')
print('├──────────────────────────────────────────────┤')
print(f'│  📋 任务: {d[\"task_id\"]}')
print(f'│  进度: 步骤 {d[\"current_step\"]}/{d[\"total_steps\"]}  ({d[\"progress_pct\"]}%)')
print(f'│  状态: {d[\"status\"]}')
if d.get('last_completed'):
    print(f'│  上次完成: {d[\"last_completed\"]}')
print(f'│  下一步: {d[\"next_action\"]}')
print('│                                              │')
print('│  [▶️ 继续执行]  [✏️ 修改方案]  [🗑️ 丢弃]      │')
print('└──────────────────────────────────────────────┘')
print('')
print(f'TASK_ID={d[\"task_id\"]}')
print(f'RESUME_STEP={d[\"current_step\"]}')
print(f'TOTAL_STEPS={d[\"total_steps\"]}')
"
}

list_active() {
  if [ ! -f "$WORKBENCH/_active.json" ]; then
    echo "[MEMORY] 📭 没有活跃任务"
    return 0
  fi

  python3 -c "
import json

with open('$WORKBENCH/_active.json') as f:
    d = json.load(f)

tasks = d.get('tasks', [])
if not tasks:
    print('[MEMORY] 📭 没有活跃任务')
    return

print('')
print('┌──────────────────────────────────────────────┐')
print('│  🦞 TaskPad · 活跃任务列表                     │')
print('├──────────────────────────────────────────────┤')
for t in tasks:
    bar_len = 20
    filled = int(t['progress_pct'] / 100 * bar_len)
    bar = '█' * filled + '░' * (bar_len - filled)
    print(f'│  {t[\"icon\"]} {t[\"task_id\"]}')
    print(f'│     {bar} 步骤 {t[\"current_step\"]}/{t[\"total_steps\"]} · {t[\"progress_pct\"]}%')
    print(f'│     状态: {t[\"status\"]}  ·  更新: {t[\"updated_at\"]}')
    print('│')
if tasks:
    print('└──────────────────────────────────────────────┘')
"
}

update_active_index() {
  local task_id="$1"
  local status="$2"
  local current_step="$3"
  local total_steps="$4"
  local timestamp
  timestamp=$(date +"%m-%d %H:%M")

  local icon="🟢"
  [ "$status" = "paused" ] && icon="🟡"
  [ "$status" = "completed" ] && icon="✅"
  [ "$status" = "cancelled" ] && icon="❌"
  [ "$status" = "failed" ] && icon="🔴"

  if [ ! -f "$WORKBENCH/_active.json" ]; then
    echo '{"tasks":[]}' > "$WORKBENCH/_active.json"
  fi

  python3 -c "
import json

with open('$WORKBENCH/_active.json') as f:
    d = json.load(f)

# Remove existing entry if any
d['tasks'] = [t for t in d['tasks'] if t['task_id'] != '$task_id']

# Add or update
entry = {
    'task_id': '$task_id',
    'icon': '$icon',
    'status': '$status',
    'current_step': $current_step,
    'total_steps': $total_steps,
    'progress_pct': $(( (current_step - 1) * 100 / total_steps )),
    'updated_at': '$timestamp'
}

if '$status' not in ['completed', 'cancelled', 'failed']:
    d['tasks'].append(entry)

with open('$WORKBENCH/_active.json', 'w') as f:
    json.dump(d, f, indent=2)
"
}

clean_task() {
  local task_id="$1"
  
  if [ -d "$WORKBENCH/$task_id" ]; then
    rm -rf "$WORKBENCH/$task_id"
    echo "[MEMORY] 🗑️ 已清理任务: $task_id"
  else
    echo "[MEMORY] ⚠️ 任务不存在: $task_id"
  fi
}

# Main dispatch
case "${1:-help}" in
  write)
    ensure_dir
    write_checkpoint "$2" "$3" "$4" "$5" "$6"
    ;;
  read)
    ensure_dir
    read_checkpoint "$2"
    ;;
  list)
    ensure_dir
    list_active
    ;;
  clean)
    ensure_dir
    clean_task "$2"
    ;;
  *)
    echo "TaskPad Memory Engine v0.1"
    echo ""
    echo "用法:"
    echo "  memory-engine.sh write <task-id> <step> <total> <status> [detail]"
    echo "  memory-engine.sh read   <task-id>"
    echo "  memory-engine.sh list"
    echo "  memory-engine.sh clean  <task-id>"
    echo ""
    echo "示例:"
    echo "  memory-engine.sh write scan-project 4 12 executing 'semgrep 完成'"
    echo "  memory-engine.sh read  scan-project"
    echo "  memory-engine.sh list"
    ;;
esac
