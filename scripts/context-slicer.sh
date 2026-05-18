#!/bin/bash
# context-slicer.sh — TaskPad Context 感知分片器
#
# 检测当前 Context 使用量，自动决定是否分片。
#
# 用法:
#   context-slicer.sh check <context-percent>
#   context-slicer.sh slice  <task-id> <step> <total>
#
# Context 分片规则:
#   < 50%:  正常执行下一批
#   50-70%: 执行 1 步后检查
#   70-85%: 执行完当前步就保存+暂停
#   > 85%:  立即保存+暂停

WORKBENCH="$HOME/.openclaw/workspace/workbench"
MEM_ENGINE="$HOME/.openclaw/workspace/skills/taskpad/scripts/memory-engine.sh"

check_context() {
  local context_pct="$1"
  
  # 这里用传入的百分比做判断
  # 实际使用中由 Agent 估算后传入

  if [ "$context_pct" -lt 50 ]; then
    echo "CONTEXT_STATUS=green"
    echo "ACTION=continue"
    echo "MESSAGE=Context 充裕 (${context_pct}%)，继续执行"
  elif [ "$context_pct" -lt 70 ]; then
    echo "CONTEXT_STATUS=yellow"
    echo "ACTION=continue-then-check"
    echo "MESSAGE=Context 中等 (${context_pct}%)，执行完下一步后重新检查"
  elif [ "$context_pct" -lt 85 ]; then
    echo "CONTEXT_STATUS=orange"
    echo "ACTION=save-and-pause"
    echo "MESSAGE=Context 较高 (${context_pct}%)，执行完当前步后保存暂停"
  else
    echo "CONTEXT_STATUS=red"
    echo "ACTION=emergency-save"
    echo "MESSAGE=Context 即将溢出 (${context_pct}%)，立即保存暂停"
  fi
}

slice_task() {
  local task_id="$1"
  local current_step="$2"
  local total_steps="$3"

  # 写入检查点标记为 paused
  bash "$MEM_ENGINE" write "$task_id" "$current_step" "$total_steps" "paused" "Context 分片自动暂停"

  echo "[SLICER] ✂️ 任务已分片保存: $task_id (步骤 $current_step/$total_steps)"
  echo "[SLICER] 恢复时读取 memory-engine.sh read $task_id"
}

case "${1:-help}" in
  check)
    check_context "$2"
    ;;
  slice)
    slice_task "$2" "$3" "$4"
    ;;
  *)
    echo "TaskPad Context Slicer v0.1"
    echo ""
    echo "用法:"
    echo "  context-slicer.sh check <percent>"
    echo "  context-slicer.sh slice <task-id> <step> <total>"
    echo ""
    echo "示例:"
    echo "  context-slicer.sh check 72"
    echo "  context-slicer.sh slice scan-project 4 12"
    ;;
esac
