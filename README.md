# 🦞 TaskPad — 会话任务临时记忆自动机

> 你的 Agent 再也不会失忆了。

## 一句话

TaskPad 是一个 OpenClaw Skill，让 Agent 在执行多步骤任务时**自动记录进度 + 断点恢复 + 可视化面板控制**。

Agent 被中断/压缩/换会话后，下次回来会自动提示"上次干到哪了"，不会失忆。

## 安装

```bash
# 1. 创建 workbench 目录
mkdir -p ~/.openclaw/workspace/workbench

# 2. 将 TaskPad 注入到 AGENTS.md
cat ~/.openclaw/workspace/skills/taskpad/templates/agents-inject.md >> ~/.openclaw/workspace/AGENTS.md

# 3. 启动提示板
python3 ~/.openclaw/workspace/skills/taskpad/scripts/panel-server.py &
# 浏览器访问 http://localhost:19999

# 4. 开启守护器 cron
crontab -e
# 添加: */5 * * * * bash ~/.openclaw/workspace/skills/taskpad/scripts/guard.sh
```

## 产品定价

| 版本 | 价格 | 功能 |
|------|------|------|
| 个人版 | ¥19（永久） | 理解器 + 记忆自动机 + 分片执行 |
| 团队版 | ¥99/月 | 加可视化面板 + 守护器 + 多人协作 |
| 企业版 | 定制 | 私有化部署 + 高级守护规则 |

## 依赖

- OpenClaw (任意版本)
- Python 3.8+（用于 panel-server）
- 浏览器（用于可视化面板）

## 反馈

觉得有用？给陈信发个红包 😎

觉得哪里不好用？直接说，我再改。
