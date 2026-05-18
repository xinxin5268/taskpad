---
name: smart-skill-manager
description: 智能 Skill 分类分级分层管理器 — 自动整理、分级加载、场景适配推荐。解决 100+ skill 一次性加载的 token 浪费问题。
---

# 🧠 Smart Skill Manager — 智能分类分级分层管理器

> 不是普通文件管理器，是 Agent 的"技能大脑"。

## 解决什么痛点

| 痛点 | 以前 | 现在 |
|------|------|------|
| 😱 **Skill 太多加载不过来** | 100 个 skill 一次性加载，大量 token 浪费 | 按 **层级+场景** 按需加载，首次只加载核心层 |
| 🧭 **找不到需要的 skill** | 靠文件名猜，实际效果靠碰 | 自动生成每个分类的 **Skill 清单目录** |
| 🤖 **Agent 不知道用什么** | 装了一堆 skill 但 Agent 不会主动调 | 根据当前任务**主动晒出适配清单**让 Agent 选 |
| 🗂️ **分类混乱** | 文件名算分类，没有层级结构 | 三级结构：**层级→分类→技能** |
| 🔄 **跨 Agent 不兼容** | 小宝的 skill 小聪不统一 | 同一份 registry，跨 Agent 同步 |
| 🧪 **弱模型不会选** | 小模型面对一堆 skill 无所适从 | 根据场景自动**排序推荐**，弱模型也能选 |

---

## 架构：三级分层

```
层级 1: 核心层 (Core)       → 必装，始终加载
层级 2: 工具层 (Toolkit)    → 按任务按需加载
层级 3: 场景层 (Scenario)   → 按场景主题批量加载
```

### 第一层：核心层（Core — 始终加载，~5 个）

无论干什么都必须有的基础技能，加载了不浪费 token。

| 分类 | 技能 | 原因 |
|------|------|------|
| 行为控制 | behavior-engine | Agent 不能没有规矩 |
| 记忆系统 | taskpad | 记不住干过的活 |
| 核心工具 | taskflow | 任务调度 |
| 安全 | vuln-scanner | 安全底线 |
| 核心技能 | skill-summoner | 技能召唤 |

**加载策略：** 始终加载，不占"可选的" token 预算。

### 第二层：工具层（Toolkit — 按任务按需加载）

Agent 接到任务后，**自动推荐**可能需要的工具类 skill。

| 分类 | 技能举例 | 触发场景 |
|------|----------|----------|
| 🔧 代码工具 | tdd、debug、diagnose、lint | Agent 检测到当前在处理代码 |
| 🔒 安全工具 | semgrep、gitleaks、nmap、trivy | Agent 检测到"安全/扫描"关键词 |
| 🌐 网络工具 | cloack browser、webhook | Agent 需要访问网络 |
| 📁 文件工具 | nano-pdf、ocr | Agent 需要处理特定文件类型 |
| 🐳 DevOps | docker、deploy、cli-proxy | Agent 检测到部署/运维任务 |
| 🤖 AI Agent | codex、opencode、claude code | Agent 检测到编码/自动化任务 |

**加载策略：** Agent 根据当前命令关键词自动推荐，用户/Agent 选一批加载。

### 第三层：场景层（Scenario — 按场景主题加载）

面向特定使用场景的完整技能包，按主题一键加载。

| 场景 | 包含技能 | 典型用户 |
|------|----------|----------|
| 🎬 内容创作 | media、video、youtube、songsee、manju-studio | 视频/音频创作者 |
| 📊 数据分析 | data-science、jupyter、multi-search-engine | 数据分析师 |
| 🏢 办公文档 | notion、obsidian、note-taking、email | 办公用户 |
| 🛡️ 安全审计 | semgrep、gitleaks、trivy、nmap、vuln-scanner | 安全工程师 |
| 🎨 创意设计 | creative、diagramming、gifs、manju-studio | 设计师 |
| ☁️ DevOps | devops、mihomo、cli-proxy、deploy | 运维工程师 |
| 💬 社交营销 | social-media、blogwatcher、feeds | 运营人员 |
| 🧪 科研 | research、arxiv、blogwatcher | 研究人员 |
| 🏠 智能家居 | smart-home | 家庭自动化 |

**加载策略：** Agent 检测到场景关键词，或用户说"切换到 XX 模式"时批量加载。

---

## 使用流程

```
用户说"帮我写个 Python 爬虫"
  │
  ├─ 1. smart-skill-manager 分析任务
  │     关键词: "写"+"Python"+"爬虫"
  │     └→ 推荐场景: 编码场景
  │
  ├─ 2. 自动晒出适配 Skill 清单
  │     ├─ [核心层] behavior-engine ✅ 已有
  │     ├─ [工具层] tdd(测试) | debug(调试) | cloack-browser(浏览器自动化)
  │     ├─ [场景] 编码创作 (含 tdd + lint + code-review)
  │     └─ ===== 请选择要加载的 skill (可多选) =====
  │
  ├─ 3. Agent/用户选择 → 按需加载
  │     └→ 加载推荐 skill → 开始执行任务
  │
  └─ 4. 任务完成 → 清理未使用的 skill
       └→ 释放 token 空间
```

---

## 自动 Skill 清单

每次 Agent 启动或任务检测时，自动生成最新 `CURRENT_CATALOG.md`：

```
┌─────────────────────────────────┐
│  当前 Skill 目录                │
│                                 │
│  核心层 (始终加载):              │
│  ├─ 🛡️ behavior-engine        │
│  ├─ 🧠 taskpad                 │
│  ├─ 📋 taskflow                │
│                                 │
│  工具层 (按需): 推荐 1 个       │
│  ├─ 🔧 cloack-browser         │
│                                 │
│  场景层 (未加载): 8 个场景可选  │
│  ├─ 🛡️ 安全审计 (4 skills)    │
│  ├─ 📊 数据分析 (2 skills)     │
│  └─ ...                        │
└─────────────────────────────────┘
```

---

## 安装

```bash
# 1. 复制到 skills 目录
cp -r skills/smart-skill-manager ~/.openclaw/workspace/skills/smart-skill-manager

# 2. 注入到 AGENTS.md（自动生效）
cat << 'EOF' >> ~/.openclaw/workspace/AGENTS.md

### 技能管理器（自动生效）
接任务时自动匹配场景→晒出 skill 清单→加载→执行→清理。不使用的 skill 不加载，不占 token。
核心层始终加载，工具层按需加载，场景层按主题加载。
EOF

# 3. 在 openclaw.json 注册
# "skills": { "entries": { "smart-skill-manager": { "enabled": true } } }
```

---

## 环境变量

| 变量 | 效果 |
|------|------|
| `SKILL_MANAGER_DISABLE=true` | 关闭智能管理器 |
| `SKILL_MANAGER_CORE_ONLY=true` | 仅加载核心层 |
| `SKILL_MANAGER_AUTO_CLEANUP=true` | 任务完成后自动清理未用 skill |
| `SKILL_MANAGER_AUTO_RECOMMEND=true` | 自动推荐 skill（默认开） |

---

## 与已有管理器的区别

| | auto-index-v3.py | smart-skill-manager |
|--|-----------------|---------------------|
| 功能 | 静态索引 + 关键词匹配 | **动态加载 + 场景推荐 + 分层管理** |
| 触发方式 | 手动运行 `python3 ... match "任务"` | **自动侦测任务，主动晒清单** |
| 加载方式 | 只提供匹配结果，不管加载 | **按层级按场景按需加载** |
| 清理 | 不回收 | **任务完成自动清理未用 skill** |
| 弱模型适配 | 关键词匹配 | 同上 |
