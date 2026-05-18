# Smart Skill Manager — 核心规则（自动注入）

## 三级分层 + 自动推荐
1. 接任务时自动扫描上下文 → 分类匹配 → 晒出适配 skill 清单让 Agent 选
2. 核心层始终加载，工具层按需加载，场景层按主题加载
3. 工具层推荐不超过 SKILL_MANAGER_MAX_RECOMMEND（默认 5）个
4. 推荐按匹配度排序，第一个标"最推荐"
5. 任务完成后自动清理未用的 toolkit/scenario skill
6. `SKILL_MANAGER_DISABLE=true` 关闭管理器
7. `SKILL_MANAGER_AUTO_CLEANUP=true` 自动清理（默认开）
