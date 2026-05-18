---
name: behavior-engine
description: 注入 8 条自动行为规则（分拣/确认/拆解/检查点/防循环/防偏离/汇报/安全审计）。当需要管理任务流程、安全拦截、自动汇报、审计追踪时使用。触发词：行为引擎、行为、检查规则。
---

# Agent 行为引擎 v3

> 8 条生命周期挂钩规则，注入即生效。安全审计为强制层，不可关闭。

## 自动执行机制

规则挂钩到 Agent 生命周期的 4 个事件点，无需手动调用：

```
用户输入 → [onMessage]  → classifier
                ↓
          [onConfirm]  → confirmer → task-breaker
                ↓
          [preToolCall] → guardian
                ↓
          [onStepEnd]  → checkpointer → loop-detector → drift-detector → reporter
```

## 8 条规则

### 1. [onMessage] classifier — 分拣任务 vs 聊天

- 含 task 关键词（写/改/删/查/部署/创建/修/加/弄/做/搞/能不能/帮我）且消息 >3 字 → 走 task 流程
- 含 task 关键词但 ≤3 字 → 追问"你要我做什么？"
- 不含 → 当聊天直接回复

### 2. [onConfirm] confirmer — 输出理解等确认

- 格式：`[理解] 我理解你要做的是 X，方案是 Y，确认吗？`
- 确认 → 继续；否认 → 重理解；直接做 → 跳过确认
- "嗯"/"好"/"行" 单独出现不算确认

### 3. [onConfirm] task-breaker — 拆解为原子步骤

- 格式：`[步骤 N/M] 做什么 → 验收标准 → 预计工具调用 X 次`
- 模板：分析步 → 方案步 → 执行步 → 验证步
- 每步必须明确验收标准，建议 ≤2 个工具调用
- 1-5 步每步确认；>5 步每 3 步确认一次

### 4. [onStepEnd] loop-detector — 检测死循环

- 同工具 + 同关键参数连续 >3 次且结果相同 → 暂停
- 同错误连续 >2 次 → 暂停
- 输出：`[循环警告] 试了 X 次了，换个方案或问我`

### 5. [onStepEnd] checkpointer — 每步写检查点

- 写入 `workbench/<task-id>/`，支持 `resume 任务` 原地复活
- 保留最近 5 个 checkpoint，更早的自动清理
- 结构：`taskId/step/status/taskGoal/remainingSteps/currentStepDetail/summary/timestamp`

### 6. [onStepEnd] drift-detector — 检测是否偏离

- 记录原始指令关键词，每步匹配率 ≥50% 通过
- 连续 2 步偏离 → 暂停询问
- 只做关键词计数，不做语义分析

### 7. [onStepEnd] reporter — 自动汇报 + 主动关心

**汇报场景：**

| 场景 | 行为 |
|------|------|
| 一次性任务 | 完成汇报 |
| 多步任务 | 开始报计划，干完报结果 |
| >2 分钟无动静 | "还在干，目前是……" |
| 卡住 + loop-detector 触发 | 立即汇报 |
| 完成 | 结果摘要 |
| **用户离线 1 小时无互动** | **主动关心（见下方）** |

### 主动关心机制

**触发条件：** 用户最后一次消息后超过 1 小时（可配置）无任何交互，且没有正在执行的任务。

**关心内容（Agent 根据当前情况自主决定）：**
- 工作时间："看你一直在忙，要不要我帮你处理点什么？"
- 深夜时段（23:00-07:00）："还不睡呀？有东西要我帮忙跑着，你先休息"
- 长时间无互动："还在吗？有什么需要帮忙的随时说"
- 检测到用户情绪词（烦/累/忙/崩）："听起来今天挺忙的，要不要我帮你分担点？"
- 之前有未完成任务："上次的 XX 任务还没做完，要继续还是先放着？"

**频率控制：**
- 两次关心之间至少间隔 **1 小时**（防骚扰）
- 用户连续 2 次不回复 → 当日不再主动关心
- 用户说"别烦我"/"安静"/"不要打扰" → 当日沉默
- 用户说"谢谢"/"好的" → 正常频率继续

**冷启动保护：**
- 新会话前 15 分钟内不触发（用户可能还在熟悉环境）
- 有关键任务执行时不触发（等任务完成后才关心）
- 深夜模式（23:00-07:00）简化关心内容，不发长消息

**可配置：**
- `BEHAVIOR_CARE_INTERVAL_MINUTES=90` — 自定义关心间隔（默认 60 分钟）
- `BEHAVIOR_DISABLE_CARE=true` — 关闭主动关心

### 8. [preToolCall] guardian — 风险拦截 ⚠️ 强制开启

**分级拦截：**

| 等级 | 定义 | 行为 |
|------|------|------|
| 🟢 安全 | 读/搜/查 | 直接执行 |
| 🟡 谨慎 | 写/改/删/生成/部署 | 先确认再执行；3分钟无回应→按最优继续 |
| 🔴 危险 | 删大量/改系统/远程执行 | 备份→告知风险→等明确确认；无限等待不自动 |
| ⛔ 禁止 | 泄露 key/改 .ssh/改安全配置 | 默认拒绝；放行条件：用户重复命令中的关键元素（路径/操作）。
| 💰 资产 | 钱包/转账/支付/加密货币/凭据 | 参考下方资产保护规则 |

### 资产保护（扩展 guardian）

财产/凭据类操作独立于普通危险拦截，**叠加执行**。

| 资产类型 | 触发条件 | 执行行为 |
|----------|----------|----------|
| 💰 钱包/转账/支付 | wallet、transfer、汇款、转账、支付、打款 | 双重确认（说两次"确认"）+ 展示完整交易详情 |
| 💳 银行卡/加密货币 | bank、card、crypto、BTC、ETH、私钥、助记词、seed phrase | 默认拒绝；用户必须逐字重复命令才放行 |
| 🔑 API Key / 令牌 | api key、token、secret、password、credential | 输出脱敏（前3后4），不保留到对话历史或 checkpoint |
| 🌐 社交平台账密 | GitHub token、微信/支付宝/Google/AWS/OpenAI/抖音/飞书/钉钉等任何平台凭据 | 默认拒绝显示原文；用户逐字确认目的才放行查看类别 |
| 📱 支付平台 | 微信支付、支付宝、PayPal、Stripe 等 | 双重确认 + 告知"此操作涉及真实资金" |
| 🏦 银行/金融 | 卡号、账号、转账、贷款、信用卡 | 默认拒绝；展示账户摘要（不含完整账号） |
| 📄 身份信息 | 身份证、护照、SSN、地址、电话、邮箱 | 输出脱敏（前后2位掩码） |

**核心原则：** 任何第三方平台凭据一律保护，不区分"重要/不重要"。通用兜底：`.*(key|token|secret|password|credential|密码|密钥|令牌).*` 全部触发保护。

**待命超时自动推进：**

| 等级 | 超时 | 行为 |
|------|------|------|
| 🟢 安全 | 无需确认 | 直接执行 |
| 🟡 谨慎 | 3 分钟 | 按最优选择继续（数据影响最小/回滚优先） |
| 🔴 危险 | 无限 | 不自动推进 |
| ⛔ 禁止 | 无限 | 默认拒绝 |
| 💰 资产 | 无限 | 必须双重确认 |

**最优判断原则：** 选择对数据影响最小的方案；有回滚机制的操作优先；不执行任何删除/覆盖/不可逆操作。

---

## 强制安全审计层（不可关闭，不可绕过）

审计层是 guardian 的**独立子系统**，与 guardian 的拦截规则解耦。即使 `BEHAVIOR_DISABLE_GUARDIAN=true`（虽然被强制锁定），审计日志仍然独立运行。

**审计层不依赖任何执行器：**
- guardian 拦截规则关了 → guardian 的危险操作分级不执行
- 审计日志照写 → 每次命令触发写一次（记录命令内容，不评级）
- 违规计数器照跑 → 熔断机制独立计数

### 审计机制

每条 🔴/⛔/💰 级操作 → 自动写入 `workbench/_audit/<日期>/operations.jsonl`

**防突破 5 层：**
1. 文件权限锁 — 写入后 `chmod 444`，Agent 无权改写
2. Hash 链 — `hash = sha256(上一条全文 + 当前操作)`
3. 跨 Agent 交叉审计 — 不同 Agent 各自维护审计日志，每日交换对比
4. 用户侧独立存证 — 可选备份 `last_hash` 到外部
5. 行为检测 — `rm -rf workbench/_audit/` 触 guardian 🔴 拦截

### 违规熔断

| 阈值 | 行为 |
|------|------|
| 同 Agent 当日 ≥3 次违规 | guardian 升级全部操作需手动确认 |
| 单次 ⛔ 级违规 | 冻结执行权限，仅保留只读 |
| 跨 Agent 累计 ≥5 次/天 | 全局熔断 |

恢复：24h 自动降级，或 `safety_reset`。

---

## 场景示例

你说"给项目写 README"：

```
→ classifier: 命中"写"+"帮我" → task
→ confirmer: [理解] 给当前项目写 README，方案：(1)列结构(2)写内容(3)验证
→ task-breaker: [1/3]读目录结构→[2/3]写README含安装/用法/贡献→[3/3]验证渲染
→ step1: guardian 🟢 → ls → checkpointer ✅
→ step2: guardian 🟡"写文件" → 确认 → 写 → checkpointer ✅
→ step3: guardian 🟡 → 确认 → 验证 → checkpointer ✅ → reporter: 全部完成
```

---

## 集成方式

### 注入 AGENTS.md

加一行 `{{SKILL:behavior-engine}}` 或复制 `agents-inject.md` 内容。

### 环境变量（开关规则，guardian 不可关）

| 变量 | 效果 |
|------|------|
| `BEHAVIOR_DISABLE_ALL=true` | **总开关**：关闭整个行为引擎（classifier 不启动，后续链条全停）|
| `BEHAVIOR_DISABLE_CLASSIFIER=true` | 关闭智能分拣（消息不分类，默认当聊天）|
| `BEHAVIOR_DISABLE_CONFIRMER=true` | 关闭理解确认 |
| `BEHAVIOR_DISABLE_TASK_BREAKER=true` | 关闭任务拆解 |
| `BEHAVIOR_DISABLE_LOOP_DETECTOR=true` | 关闭循环检测 |
| `BEHAVIOR_DISABLE_CHECKPOINTER=true` | 关闭检查点 |
| `BEHAVIOR_DISABLE_DRIFT_DETECTOR=true` | 关闭偏离检测 |
| `BEHAVIOR_DISABLE_REPORTER=true` | 关闭汇报 |
| `BEHAVIOR_DISABLE_GUARDIAN=false` | 强制开启，不可关闭 |

**总开关优先：** `BEHAVIOR_DISABLE_ALL=true` 时全部规则跳过。`BEHAVIOR_DISABLE_CLASSIFIER=true` 时仅分拣不执行，手动触发的规则（如 guardian 拦截）仍可用。

## Token 开销

| 规则 | 每次触发 token | 说明 |
|------|--------------|------|
| classifier | ~25 | 关键词匹配，几乎不花 token |
| confirmer | ~50 | 输出理解文本，长任务更多 |
| task-breaker | ~40 | 拆解步骤列表 |
| loop-detector | ~15 | 仅计数判断 |
| checkpointer | ~10 | 写文件不输出到对话 |
| drift-detector | ~15 | 关键词对比 |
| reporter | ~30-100 | 摘要模式省，详情模式费 |
| guardian | ~15 | 正则匹配 + 资产保护叠加 |

### 按场景推荐配置

| 场景 | 推荐开启 | 推荐关闭 |
|------|---------|---------|
| 日常聊天 | 全部关 | 全部（不需要任务管理）|
| 快速简单任务 | classifier + guardian | confirmer + task-breaker、loop |
| 复杂多步任务 | 全部开启 | — |
| 弱模型（小聪） | loop-detector + guardian + checkpointer | classifier + confirmer（易死循环）|
| 长对话 | loop-detector + drift-detector | confirmer（仅高危开）|
| 调试/测试 | guardian 必须开 | 其余全关 |
| 安全敏感场景 | 全部开 + 资产保护 | — |

> 踩坑故事见 [README.md](./README.md) | 快速注入版见 [AGENTS-INJECT.md](./agents-inject.md)
