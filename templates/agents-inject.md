<!-- TASKPAD SKILL INJECT (开始) -->
## TaskPad — 会话任务临时记忆自动机

### 触发条件
当你需要执行多步骤任务时，自动使用 TaskPad 记忆系统。

### 核心流程

#### 1. 任务理解
收到任务后，先不执行，输出"我理解你要做的是……"：
- 复述任务内容
- 列出你认为要做的步骤
- 等待用户确认后再继续

#### 2. 调研与方案
理解确认后，先调研再出方案：
- 查相关资料
- 制定可执行步骤列表
- 包括每步预估、依赖、文件输出
- 写入 workbench/<task-id>/plan.md

#### 3. 自切分执行
执行时检测 Context 用量：
- < 50%: 继续执行
- 50-70%: 执行1步后检查
- 70-85%: 执行完当前步就保存+暂停
- > 85%: 立即保存+暂停

#### 4. 每步写临时记忆
每完成一步调用 scripts/memory-engine.sh write：
```bash
bash ~/.openclaw/workspace/skills/taskpad/scripts/memory-engine.sh write <task-id> <step> <total> executing '<完成内容>'
```

#### 5. 恢复时自动提示
会话启动或恢复时，先检查 workbench/ 目录：
```bash
bash ~/.openclaw/workspace/skills/taskpad/scripts/memory-engine.sh list
```

如果有未完成任务，自动提示：
- 读取 checkpoint.json
- 输出恢复提示
- 让用户选择：继续/修改/丢弃

#### 6. 守护器
- 超时检测: 单步执行超预估 3 倍就暂停
- 偏航检测: 执行内容偏离 plan.md 就暂停请示
- 死循环检测: 连续 3 次重复操作就暂停

### 功能开关
所有功能可在 TaskPad 面板中独立开关：
- 任务理解器（默认 ON）
- 调研方案器（默认 ON）
- 自切分执行器（默认 ON）
- 临时记忆自动机（默认 ON）
- 任务守护器（默认 ON）
- 恢复提示（默认 ON）

### 提示板
面板地址: http://localhost:19999
启动: python3 scripts/panel-server.py
<!-- TASKPAD SKILL INJECT (结束) -->
