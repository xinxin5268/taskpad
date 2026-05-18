# behavior-engine 与 smart-skill-manager 联动方案

> 目标：behavior-engine 的 classifier 分拣出任务类型后 → 自动调用 smart-skill-manager 推荐 skill → 确认后加载 → 执行 → 完成后清理

---

## 流程

```
用户输入
  │
  ├─ [behavior-engine] classifier
  │     命中 task 关键词 → 分类任务类型
  │     ↓
  ├─ [behavior-engine] confirmer
  │     输出理解："我理解你要：XXX"
  │     ↓
  ├─ [behavior-engine] confirmer 确认后
  │     ↓
  ├─ [smart-skill-manager] classifier.py match "XXX"
  │     自动扫描当前上下文 + 推荐 skill
  │     ┌─────────────────────────────────────┐
  │     │ 🏆 核心层: behavior-engine ✅ 已有 │
  │     │ 🛠️ 工具层推荐:                     │
  │     │   1. semgrep (安全工具) 匹配度: 4  │
  │     │   2. vuln-scanner (安全工具) 匹配:3│
  │     │ 📦 场景推荐: 安全审计 (4个skill)   │
  │     └─────────────────────────────────────┘
  │     ↓
  ├─ [behavior-engine] task-breaker
  │     拆解步骤 + 需要加载的 skill 对应步骤
  │     ↓
  ├─ [smart-skill-manager] 按需加载推荐 skill
  │     加载选中的 skill → 更新上下文
  │     ↓
  ├─ 执行循环（guardian → tool call → checkpoint → loop → drift → report）
  │     ↓
  └─ [smart-skill-manager] 任务完成后清理
       回收未使用的 skill → 释放 token
       保留核心层
```

---

## 交互设计

### 何时触发
- behavior-engine 的 classifier 命中 task → 输出 `[任务类型]`
- 若 `SKILL_MANAGER_AUTO_RECOMMEND=true`（默认开）→ 调用 smart-skill-manager 推荐

### 何时跳过
- task 仅为简单的读/查操作 → 不触发（不需要额外 skill）
- `SKILL_MANAGER_DISABLE=true` → 关闭推荐
- 核心层 skill 已满足需求（匹配度 ≥5 的工具已在上下文中）→ 不推荐更多

### 推荐格式
```
[Skill 推荐] 任务 "XXX" 可能需要：
🛠️ 工具: <技能名> (<分类>) — 匹配度 N
📦 场景: <场景名> — 含 N 个 skill
输入 "加载 <技能名>" 开始使用，或直接跳过。
```

### 加载方式
- 加载单个 skill：`load skill <name>`
- 加载整个场景：`load scene <场景名>`
- 跳过不加载：直接执行任务

### 清理规则
- 任务完成后：清理**非核心层**且**本次任务未调用的** skill
- 核心层 skill 不清理
- 工具层 skill 如果在执行中实际被调用了 → 保留到对话结束
- 场景层 skill 如果只加载了部分 → 仅保留实际用到的

---

## 环境变量

| 变量 | 默认值 | 效果 |
|------|--------|------|
| `SKILL_MANAGER_AUTO_RECOMMEND` | `true` | 自动推荐 skill |
| `SKILL_MANAGER_AUTO_CLEANUP` | `true` | 任务完成自动清理 |
| `SKILL_MANAGER_MAX_RECOMMEND` | `5` | 弱模型最大推荐数量 |
| `SKILL_MANAGER_CORE_ONLY` | `false` | 仅加载核心层 |

---

## 实现注意事项

1. **弱模型适配** — 推荐数量不超过 5 个，按匹配度排序，第一个标"最推荐"
2. **不打断执行** — 推荐在 confirmer 确认后、task-breaker 拆解前插入，不额外增加确认轮次
3. **幂等加载** — 已经在上下文中的 skill 不重复加载
4. **加载失败回退** — skill 文件不存在或损坏时跳过，不影响主任务执行
