/**
 * panel.js — TaskPad 任务提示板 JavaScript
 * 
 * 功能：
 * - 自动轮询 /api/tasks 获取任务列表
 * - 渲染任务卡片（进度条 + 操作按钮）
 * - 功能开关设置（localStorage 持久化）
 * - 面板最小化/关闭/拖拽
 * - 操作按钮调用 /api/action
 */

const API_BASE = '';
let refreshInterval = null;

// ====== 设置管理 ======
function loadSettings() {
  const keys = [
    'switch-understander', 'switch-researcher', 'switch-slicer',
    'switch-memory', 'switch-guard', 'switch-hint',
    'switch-notify', 'switch-alert'
  ];
  keys.forEach(key => {
    const el = document.getElementById(key);
    if (!el) return;
    const saved = localStorage.getItem(key);
    if (saved !== null) {
      el.checked = saved === 'true';
    }
  });
}

function saveSettings() {
  const keys = [
    'switch-understander', 'switch-researcher', 'switch-slicer',
    'switch-memory', 'switch-guard', 'switch-hint',
    'switch-notify', 'switch-alert'
  ];
  keys.forEach(key => {
    const el = document.getElementById(key);
    if (el) {
      localStorage.setItem(key, el.checked);
    }
  });
}

function toggleSettings() {
  const panel = document.getElementById('settings-panel');
  panel.classList.toggle('hidden');
}

// ====== 面板管理 ======
let isMinimized = false;

function toggleMinimize() {
  isMinimized = !isMinimized;
  const content = document.getElementById('content');
  const btn = document.getElementById('minimize-btn');
  if (isMinimized) {
    content.classList.add('hidden');
    btn.textContent = '□';
  } else {
    content.classList.remove('hidden');
    btn.textContent = '─';
  }
}

function closePanel() {
  document.getElementById('app').style.display = 'none';
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
}

// ====== 任务 API ======
async function fetchTasks() {
  try {
    const resp = await fetch(`${API_BASE}/api/tasks`);
    const data = await resp.json();
    return data.tasks || [];
  } catch (err) {
    console.error('Failed to fetch tasks:', err);
    return [];
  }
}

async function executeAction(taskId, action, extra = {}) {
  try {
    const resp = await fetch(`${API_BASE}/api/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId, action, ...extra })
    });
    const data = await resp.json();
    if (data.success) {
      refreshTasks();
    }
    return data;
  } catch (err) {
    console.error('Action failed:', err);
    return { success: false, error: err.message };
  }
}

// ====== 渲染 ======
function getProgressClass(pct) {
  if (pct < 50) return 'green';
  if (pct < 75) return 'yellow';
  if (pct < 90) return 'orange';
  return 'red';
}

function getIcon(status) {
  const map = {
    'executing': '🔵',
    'paused': '🟡',
    'completed': '✅',
    'cancelled': '⛔',
    'failed': '🔴',
    'understood': '📋',
    'planning': '📝'
  };
  return map[status] || '⚪';
}

function renderTasks(tasks) {
  const container = document.getElementById('tasks-container');
  const empty = document.getElementById('empty-state');
  const count = document.getElementById('task-count');

  count.textContent = tasks.length;

  if (tasks.length === 0) {
    container.innerHTML = '';
    container.appendChild(empty.cloneNode(true));
    return;
  }

  // Sort: executing first, then paused, then others
  const sorted = [...tasks].sort((a, b) => {
    const order = { 'executing': 0, 'paused': 1, 'understood': 2, 'planning': 3, 'completed': 4, 'cancelled': 5, 'failed': 6 };
    return (order[a.status] || 99) - (order[b.status] || 99);
  });

  container.innerHTML = sorted.map(task => {
    const pct = task.progress_pct || 0;
    const icon = task.icon || getIcon(task.status);
    const statusMap = {
      'executing': '执行中',
      'paused': '已暂停',
      'completed': '已完成',
      'cancelled': '已取消',
      'failed': '失败',
      'understood': '已理解',
      'planning': '规划中'
    };
    const statusText = statusMap[task.status] || task.status;
    const stepInfo = task.current_step && task.total_steps
      ? `步骤 ${task.current_step}/${task.total_steps}`
      : '';

    return `
      <div class="task-card" data-task-id="${task.task_id}">
        <div class="task-card-header">
          <span class="task-icon">${icon}</span>
          <span class="task-id">${task.task_id}</span>
          <span class="task-time">${task.updated_at || ''}</span>
        </div>
        <div class="progress-bar">
          <div class="progress-track">
            <div class="progress-fill ${getProgressClass(pct)}" style="width: ${pct}%"></div>
          </div>
          <span class="progress-text">${pct}%</span>
        </div>
        <div class="task-status">${statusText} · ${stepInfo}</div>
        ${task.detail ? `<div class="task-step-info">${task.detail}</div>` : ''}
        <div class="task-actions">
          ${task.status === 'paused' ? `<button class="task-btn play" onclick="execAction('${task.task_id}','resume')">▶️ 继续</button>` : ''}
          ${task.status === 'executing' ? `<button class="task-btn pause" onclick="execAction('${task.task_id}','pause')">⏸️ 暂停</button>` : ''}
          ${task.status !== 'completed' && task.status !== 'cancelled' && task.status !== 'failed'
            ? `<button class="task-btn stop" onclick="execAction('${task.task_id}','stop')">🛑 停止</button>` : ''}
          <button class="task-btn edit" onclick="editTask('${task.task_id}')">✏️ 修改</button>
          <button class="task-btn edit" onclick="addNote('${task.task_id}')">📝 备注</button>
        </div>
      </div>
    `;
  }).join('');
}

async function execAction(taskId, action) {
  const result = await executeAction(taskId, action);
  if (result.success) {
    refreshTasks();
  } else {
    console.error('Action failed:', result);
  }
}

function editTask(taskId) {
  const note = prompt(`编辑任务 ${taskId}（输入修改内容或新步骤）：`);
  if (note) {
    executeAction(taskId, 'note', { note: `[修改] ${note}` });
  }
}

function addNote(taskId) {
  const note = prompt(`为任务 ${taskId} 添加备注：`);
  if (note) {
    executeAction(taskId, 'note', { note });
  }
}

// ====== 轮询 ======
async function refreshTasks() {
  const tasks = await fetchTasks();
  renderTasks(tasks);

  const now = new Date();
  document.getElementById('last-update').textContent =
    now.toTimeString().slice(0, 8);
}

function startPolling(intervalMs = 3000) {
  if (refreshInterval) clearInterval(refreshInterval);
  refreshTasks();
  refreshInterval = setInterval(refreshTasks, intervalMs);
}

// ====== 初始化 ======
document.addEventListener('DOMContentLoaded', () => {
  loadSettings();
  startPolling(3000);

  // 状态更新
  setInterval(async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/status`);
      const data = await resp.json();
      const indicator = document.getElementById('status-indicator');
      const text = document.getElementById('status-text');
      if (data.status === 'running') {
        indicator.className = 'green';
        text.textContent = `运行中 · ${data.active_tasks} 个任务`;
      }
    } catch (e) {
      document.getElementById('status-indicator').className = 'red';
      document.getElementById('status-text').textContent = '离线';
    }
  }, 5000);
});
