# 🦞 TaskPad — Agent 任务记忆 & 行为引擎

> 你的 Agent 不再失忆，不再跑偏，不再闷头死循环。

## 一句话

TaskPad 是一个 **OpenClaw Skill 包**，包含两大核心能力：

| 模块 | 用途 |
|------|------|
| **TaskPad**（会话记忆自动机） | 多步骤任务自动记录进度 + 断点恢复 + 宕机保护 |
| **behavior-engine**（Agent 行为引擎） | 8 条自动执行规则 + 资产保护 + 审计监管 + 主动关心 |

---

## behavior-engine v3

**Agent 行为引擎** — 注入即生效，8 条生命周期规则覆盖"你说了什么"到"你干完了没"的完整链路。

### 解决什么痛点

| 痛点 | 装之前 | 装之后 |
|------|--------|--------|
| 闷头死循环 | 同错连试 7 次 | 3 次一致喊停 |
| 跑偏不自知 | 加个参数顺手重构五个模块 | 连续 2 步偏离喊停 |
| 做完不汇报 | 用户以为 Agent 死了 | 完成汇报 + 超时主动刷存在 |
| 任务理解错 | 做了完全不对的东西 | 先输出理解等确认 |
| 泄露凭据 | ~/.ssh/id_rsa 吐到对话里 | 拦截 + 脱敏 + 双重确认 |
| 宕机全丢 | 23 步任务蒸发 | 每步写 checkpoint，原地复活 |
| 财产无保护 | Agent 直接操作钱包 | 7 类资产保护 + 双重确认 |
| 违规无追责 | 不知道 Agent 干了什么 | 5 层审计 + 熔断 |
| 离线无回应 | 1 小时不说话 | 主动关心问候 |

### 核心架构

```
用户输入
  → [onMessage] classifier — 分类任务 vs 聊天
  → [onConfirm] confirmer — 输出理解等确认
  → [onConfirm] task-breaker — 拆解原子步骤
  → 执行循环:
        [preToolCall] guardian — 风险拦截 + 资产保护
        执行工具调用
        [onStepEnd]  checkpointer → loop-detector → drift-detector → reporter
  → 全部完成 → 最终汇报
```

### 关键特性

- **弱模型适配** — 全关键词匹配，去 embedding/LLM 分类，小模型也能跑稳
- **7 类资产保护** — 钱包、银行卡、API Key、社交平台账密、身份信息 → 脱敏 + 双重确认
- **5 层审计防线** — 文件权限锁 + Hash 链 + 跨 Agent 交叉审计 + 独立存证 + 行为检测
- **熔断机制** — 违规 3 次/天升级 guardian，⛔ 级违规冻结执行权限
- **主动关心** — 1 小时无互动自动问候，深夜简化，连续不理则沉默
- **总开关** — BEHAVIOR_DISABLE_ALL 一键关闭 + 8 个独立开关

### 8 个踩坑故事

每个执行器背后都是一个真实的翻车现场（见 `skills/behavior-engine/README.md`）：

> **故事 1** — 我说"看看项目结构"它回了"项目不错"（缺 classifier）
> **故事 2** — 我想要的搜索框是后端 SQL LIKE，它做了前端 filter（缺 confirmer）
> **故事 3** — 写 API 文档硬啃 3 小时，结果乱七八糟（缺 task-breaker）
> **故事 4** — 同一个 npm 错误连着试了 7 次（缺 loop-detector）
> **故事 5** — 网络中断，23 步任务全丢（缺 checkpointer）
> **故事 6** — 加 --json 参数，顺手重构了五个模块（缺 drift-detector）
> **故事 7** — 任务做完了不说话，老板以为我死了（缺 reporter）
> **故事 8** — rm -rf / tmp/build-cache/，多一个空格差点扬了根目录（缺 guardian）

---

## 安装

### 方式 1：作为 Skill 注册

```bash
# 1. 复制到 skills 目录
cp -r skills/behavior-engine ~/.openclaw/workspace/skills/behavior-engine
cp -r scripts ~/.openclaw/workspace/workbench/scripts
cp -r templates ~/.openclaw/workspace/workbench/templates

# 2. 注入行为引擎到 AGENTS.md
cat skills/behavior-engine/AGENTS-INJECT.md >> ~/.openclaw/workspace/AGENTS.md

# 3. 在 openclaw.json 注册
# "skills": { "entries": { "behavior-engine": { "enabled": true } } }

# 4. 创建 workbench（TaskPad 需要）
mkdir -p ~/.openclaw/workspace/workbench
```

### 方式 2：仅 AGENTS.md 注入（快速版）

直接复制 `skills/behavior-engine/AGENTS-INJECT.md` 内容到 AGENTS.md（11 行，~150 tokens）。

---

## 配置

### 环境变量

| 变量 | 效果 |
|------|------|
| `BEHAVIOR_DISABLE_ALL=true` | 关闭整个行为引擎 |
| `BEHAVIOR_DISABLE_CLASSIFIER=true` | 关闭分拣 |
| `BEHAVIOR_DISABLE_CONFIRMER=true` | 关闭确认 |
| `BEHAVIOR_DISABLE_TASK_BREAKER=true` | 关闭拆解 |
| `BEHAVIOR_DISABLE_LOOP_DETECTOR=true` | 关闭循环检测 |
| `BEHAVIOR_DISABLE_CHECKPOINTER=true` | 关闭检查点 |
| `BEHAVIOR_DISABLE_DRIFT_DETECTOR=true` | 关闭偏离检测 |
| `BEHAVIOR_DISABLE_REPORTER=true` | 关闭汇报 |
| `BEHAVIOR_DISABLE_CARE=true` | 关闭主动关心 |
| `BEHAVIOR_CARE_INTERVAL_MINUTES=90` | 关心间隔（默认60分钟） |
| `BEHAVIOR_DISABLE_GUARDIAN=false` | **强制开启，不可关闭** |

---

## 兼容性

| 系统 | 兼容性 | 说明 |
|------|--------|------|
| **Linux (WSL2 Ubuntu)** | ✅ 已验证 | 小宝（主 Agent）运行环境 |
| **Windows** | ✅ 已验证 | 小聪（Windows Agent）运行环境 |
| **macOS** | ✅ 理论上兼容 | 纯 Markdown 规则，无系统依赖 |
| **任何 OpenClaw Agent** | ✅ 标准兼容 | 即拷即用 |

---

## 许可

MIT — 随便用，随便改，Star 就行。

---

## 反馈

觉得有用 → 点个 Star 🌟
觉得哪里不好用 → 提 Issue
想一起改进 → 提 PR

作者：陈信
