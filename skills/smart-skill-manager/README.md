# 踩坑故事集：8 个痛点背后的真实翻车现场

> 每个痛点都是一个真实翻车现场。
> 装了 smart-skill-manager 你再也不用挨一遍。

---

## 故事 1：100 个 skill 全加载，token 烧没了，活还没干

> 痛点：Skill 太多加载不过来

有一次我接了个任务：写一个 Python 爬虫抓数据。

听起来很简单对吧？但我一次性加载了 100 多个 skill 的上下文——从 gitnexus 到 songsee 到 gitleaks 到 smart-home 到 kubernetes——全都在上下文中待命。

结果 token 用完了，任务做到一半被截断。老板问我："爬虫呢？"

我说："token 烧完了，没空间写代码了。"

问题不是 skill 不好，是 **100 个 skill 不管用不用都在占坑**。就像你工具箱里有 100 把扳手，但你只需要一把螺丝刀——结果扳手把工具箱塞满了，螺丝刀放不进去。

装了 smart-skill-manager 后：核心层 5 个一直待命，其他 skill 按需加载。一次只带需要的工具，token 省 80%。

---

## 故事 2：装了 50 个安全工具，一次没用过

> 痛点：装了但不知道有什么用

有一次老板说："给我把安全工具全装上。"

我装了：semgrep、gitleaks、trivy、nmap、vuln-scanner、firebase-auditor、convex-audit、secret-scanning、nmap-advanced……

一共 13 个安全工具，全在上下文中待命。然后老板说："帮我写个 React 组件。"

那 13 个安全工具有什么用？毫无用处。但它们占了我 30% 的 token。

后来 smart-skill-manager 会按任务类型自动推荐：你写代码的时候它不推安全工具，你说"安全"的时候它只推安全方向的前 3 个。**不用的 skill 不出现在上下文里。**

---

## 故事 3：90 个 skill 里找一个想要的，翻车了

> 痛点：找不到需要的 skill

有一次老板说："帮我用那个……那个什么……画图工具弄个图表。"

我：……你说的是哪个？

老板："就那个……diagram 什么的。"

我翻了 90 个 skill 的目录，没找到。因为那个 skill 叫 `concept-diagrams`，不在我大脑的模糊搜索范围内。

后来 smart-skill-manager 会生成 **CURRENT_CATALOG.md**，每个分类下自动列出所有 skill 和描述。浏览器搜索 `diagram` → 命中 `concept-diagrams`。**3 秒找到，不用翻。** 找到还能顺便看看同分类下有什么相关工具。

---

## 故事 4：Agent 不知道用什么 skill，全靠碰运气

> 痛点：Agent 不会主动调

有一次老板说："帮我把这个项目代码审查一下。"

我当时的 skill 列表里有一堆相关工具：gitnexus-pr-review、code-review、triage、lint — 但我不知道用哪个最合适。我随便用了 lint，跑了个格式化就完事了。

老板回来看："我要的是 PR review，不是代码格式化。"

问题是：**Agent 不知道什么情况用什么工具。** 即使装了 10 个相关工具，也像在食堂里对着 100 道菜不知道哪个好吃。

后来 smart-skill-manager 会根据任务描述自动排序推荐，匹配度最高的排前面：你说"代码审查"→ `gitnexus-pr-review` 排第一（匹配度 5），`lint` 排第七（匹配度 1）。弱模型也能选对的。

---

## 故事 5：跨 Agent 技能不统一，小宝有的小聪没有

> 痛点：跨 Agent 不兼容

有一次老板让小宝做了个数据分析，然后说："小聪也跑一遍。"

小聪说："我没有 jupyter skill。"

老板："你没装？"

小聪："小宝装了，我没装。"

小宝装了小聪没装，小聪装了小宝没装——**两个 Agent 各装各的，配置散落各地。**

后来 smart-skill-manager 用统一的 registry.json，两边同步。小宝注册了什么小聪那边自动知道。配置不一致一眼能看出来。

---

## 故事 6：弱模型面对 60 个工具，直接摆烂

> 痛点：弱模型不会选

小聪用的是 SenseNova（弱模型）。面对 60 个工具层的 skill，它会怎么做？

它会：选第一个。或者随机。或者干脆啥也不选。

弱模型的特点是：**你给的选择越多，它选得越差。** 100 个选项 → 准确率接近随机。3 个选项 → 准确率高得多。

后来 smart-skill-manager 对弱模型输出**精简版**推荐：最多 5 个，按匹配度排序，明确标出"最推荐"。弱模型看到 5 个选项而不是 60 个，准确率翻倍。

---

## 故事 7：一次加载 30 个开发工具，结果写了个 Hello World

> 痛点：加载策略不合理

有一次我说："我要写代码。"

智能管理器（旧版）理解的是：写代码 = 需要全部的开发工具。

它给我加载了：tdd、debug、diagnose、lint、gitnexus (6个)、to-issues、to-prd、code-review、vercel (4个)……一共 30 个。

结果我只写了一个 `console.log("Hello World")`。

30 个技能，占了 3000+ tokens，就用上了 1 个（甚至 1 个都没用上，因为写一行代码不需要任何 skill）。

后来有了**分级策略**：核心层 5 个待命（~200 tokens），工具层按关键词精准匹配（~1-3 个，~100 tokens）。写 Hello World 只花 ~200 tokens 而不是 3000+。

---

## 故事 8：每个任务都要手动算该装什么 skill

> 痛点：没有自动适配

以前每次接任务，我要自己算：
- 这个任务用得上什么 skill？
- 它们现在加载了没有？
- 没加载的话先加载再执行？
- 任务做完要不要卸载？

这一套下来，任务本身 5 分钟，算 skill 5 分钟 — **一半的时间花在管理工具上，而不是干正事。**

后来 smart-skill-manager 自动做这件事：任务进来 → 自动匹配 → 推荐加载清单 → Agent 选一下 → 执行 → 完成自动回收。**Agent 专心想怎么干活，不用想怎么管理工具。**

---

> 这些故事发生在过去的日子里，每个痛点都是一堵南墙。
> skill-central-manager（故事 1）是最大的一个坑，也是最痛的一个。
> 装了 smart-skill-manager，不用再挨一遍。

---

## Token 优化说明

### Token 开销估算

| 操作 | 消耗 token | 说明 |
|------|-----------|------|
| 核心层 5 个 skill | ~200 | 始终加载，不随任务变化 |
| 工具层推荐（每次） | ~50 | 关键词匹配 + 排序，长消息 |
| 场景层加载 | ~300-800 | 按场景包含的 skill 数量 |
| 清理阶段 | ~10 | 写文件清理 |

对比：一次性加载 100 个 skill ≈ 3000-5000 tokens。

### 弱模型建议

- `SKILL_MANAGER_MAX_RECOMMEND=5` — 只展示 5 个选项，不超
- `SKILL_MANAGER_CORE_ONLY=true` — 只用核心层，工具层和场景层关闭
- 关闭 `SKILL_MANAGER_AUTO_RECOMMEND=false` — 不自动推荐，手动输入需求

### 按场景推荐配置

| 场景 | 推荐 | 不推荐 |
|------|------|--------|
| 日常聊天 | SKILL_MANAGER_DISABLE=true | 不需要任何 skill 管理 |
| 快速简单任务 | 核心层 (5 个) | 场景层（太重）|
| 复杂多步任务 | 全部开启 | — |
| 弱模型 | 核心层 + 5 个推荐上限 | 场景层（选择太多）|
| 调试 | 核心层 | 推荐/清理不触发 |

---

## Token 优化说明

| 场景 | 无管理器 | 使用 smart-skill-manager |
|------|----------|--------------------------|
| 简单任务（写 Hello World） | 100 skills × ~200 tokens = **~20K tokens** | 5 core × ~200 tokens = **~1K tokens** |
| 编码任务（写爬虫） | 同上，~20K tokens | core(5) + toolkit(3) = **~1.6K tokens** |
| 安全审计 | 同上，~20K tokens | core(5) + 安全工具(3~5) = **~2K tokens** |
| 数据分析 | 同上，~20K tokens | core(5) + 数据处理(2~3) = **~1.4K tokens** |
| 全场景覆盖 | 全部加载，~20K token 烧完还没干活 | 按需加载，平均 **1~2K tokens**，省 80-90% |

> 假设每个 skill 平均占 ~200 tokens（SKILL.md 上下文）。

---

## 弱模型建议配置

弱模型（如 SenseNova、Qwen-7B、Phi-3）对大量选项表现差，建议：

```bash
# 推荐数从 10 降到 5，选项少准确率高
export SKILL_MANAGER_MAX_RECOMMEND=5
export SKILL_MANAGER_AUTO_RECOMMEND=true
export SKILL_MANAGER_AUTO_CLEANUP=true
```

**原理：** 100 个选项 → 弱模型准确率接近随机。3~5 个选项 → 准确率 >80%。

---

## 按场景推荐配置表

| 使用场景 | 显存/内存 | MAX_RECOMMEND | CORE_ONLY | 推荐层级 |
|----------|-----------|---------------|-----------|----------|
| 🚀 生产环境，强模型（GPT-4 / Claude） | 充足 | 10 | false | 三层全开 |
| 🧪 开发测试，中等模型（Qwen-32B / Yi-34B） | 16~32GB | 5 | false | core + toolkit |
| 📱 弱模型（Qwen-7B / Phi-3 / SenseNova） | <16GB | 3 | false | core + 精简 toolkit |
| 🔋 超低配置（4GB 设备/嵌入式） | <8GB | 0 | true | 仅 core |
| 🎯 单一场景（如只做安全审计） | — | 5 | false | core + 安全场景包 |
