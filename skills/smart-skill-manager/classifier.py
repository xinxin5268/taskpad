#!/usr/bin/env python3
"""
智能 Skill 分类分级分层管理器 v1
================================

功能：
  1. 扫描所有 SKILL.md，提取 name/description
  2. 三级分类：核心层(Core) / 工具层(Toolkit) / 场景层(Scenario)
  3. 智能分类（精确匹配 > 关键词 > 路径兜底）
  4. 生成 CURRENT_CATALOG.md（当前 Skill 清单目录）
  5. 根据任务描述推荐适配 Skill
  6. Agent 启动时自动调用

用法：
  python3 classifier.py                     # 扫描+分类+生成目录
  python3 classifier.py match "写Python爬虫" # 根据任务推荐 skill
  python3 classifier.py catalog              # 仅生成目录
  python3 classifier.py stats                # 统计
"""

import os
import sys
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime

# ─── 配置 ─────────────────────────────────────────────
WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
SKILL_DIRS = [
    os.path.join(WORKSPACE, "skills"),
    os.path.expanduser("~/.agents/skills"),
    os.path.expanduser("~/.hermes/hermes-agent/skills"),
]
OUTPUT_DIR = os.path.join(WORKSPACE, "workbench", "_catalog")
CORE_SKILLS_FILE = os.path.join(OUTPUT_DIR, "core-skills.json")
CATALOG_FILE = os.path.join(OUTPUT_DIR, "CURRENT_CATALOG.md")
REGISTRY_FILE = os.path.join(OUTPUT_DIR, "registry.json")

# ─── 三级分层定义 ─────────────────────────────────────

# 第一层：核心层 — 始终加载
CORE_SKILLS = {
    "behavior-engine": {"description": "Agent 行为引擎", "tier": "core"},
    "taskpad": {"description": "会话记忆自动机", "tier": "core"},
    "taskflow": {"description": "任务调度", "tier": "core"},
    "skill-summoner": {"description": "技能召唤", "tier": "core"},
}

# 第二层：工具层 — 按任务按需加载
TOOLKIT_CLASSIFICATION = {
    # 分类名 → (触发关键词, 技能前缀关键词)
    "代码工具": (["代码", "编码", "python", "typescript", "test", "debug", "重构", "review", "pr", "issue"],
                  ["tdd", "debug", "diagnose", "lint", "gitnexus", "triage", "to-issues", "to-prd", "code-review"]),
    "安全工具": (["安全", "扫描", "vuln", "audit", "nmap", "secret", "渗透", "漏洞", "firebase"],
                  ["semgrep", "gitleaks", "trivy", "nmap", "vuln-scanner", "firebase", "audit-website", "security"]),
    "网络工具": (["网络", "web", "浏览器", "http", "api", "请求", "爬虫", "抓取"],
                  ["cloakbrowser", "webhook", "web-fetch", "scrapling", "multi-search"]),
    "DevOps":   (["部署", "docker", "容器", "ci", "cd", "运维", "服务器", "nginx", "域名"],
                  ["docker", "deploy", "cli-proxy", "mihomo", "gateway", "nginx", "domain"]),
    "AI Agent": (["agent", "AI", "模型", "大模型", "autonomous", "orchestrator", "codex"],
                  ["codex", "claude-code", "opencode", "hermes", "orchestrator", "autonomous"]),
    "数据处理": (["数据分析", "数据", "csv", "json", "excel", "报表", "可视化", "chart"],
                  ["jupyter", "nano-pdf", "ocr", "data-science", "diagramming"]),
    "文档工具": (["文档", "报告", "论文", "writing", "阅读", "生成"],
                  ["nano-pdf", "ocr", "notion", "obsidian", "note-taking", "research-paper"]),
}

# 第三层：场景层 — 按场景主题加载
SCENARIO_CLASSIFICATION = {
    "🎬 内容创作": (["视频", "音频", "创作", "内容", "youtube", "media", "音乐"],
                     ["youtube", "songsee", "manju-studio", "heartmula", "media", "video", "gifs"]),
    "📊 数据分析": (["数据分析", "数据", "分析", "报表", "统计", "图表"],
                     ["jupyter", "data-science", "multi-search-engine", "diagramming"]),
    "🛡️ 安全审计": (["安全", "审计", "渗透", "扫描", "漏洞"],
                     ["semgrep", "gitleaks", "trivy", "nmap", "vuln-scanner", "audit-website", "firebase", "security"]),
    "🏢 办公文档": (["文档", "笔记", "notion", "obsidian", "办公", "写作", "邮件"],
                     ["notion", "obsidian", "note-taking", "email", "nano-pdf", "ocr"]),
    "☁️ DevOps":   (["部署", "运维", "docker", "ci/cd", "服务器", "域名"],
                     ["devops", "docker", "deploy", "cli-proxy", "gateway", "mihomo"]),
    "💬 社交营销": (["社交", "营销", "推广", "内容", "博客", "rss"],
                     ["social-media", "blogwatcher", "feeds", "multi-search-engine"]),
    "🧪 科研":     (["研究", "论文", "arxiv", "科研", "学术", "调研"],
                     ["research", "arxiv", "blogwatcher", "multi-search-engine", "reseach-paper"]),
    "🏠 智能家居": (["智能家居", "home", "家居", "自动化"],
                     ["smart-home", "openhue"]),
}


# ─── 扫描函数 ─────────────────────────────────────────

def scan_skills():
    """扫描所有 SKILL.md 文件，返回技能列表"""
    skills = []
    seen = set()
    
    for skill_dir in SKILL_DIRS:
        if not os.path.isdir(skill_dir):
            continue
        for name in os.listdir(skill_dir):
            skill_path = os.path.join(skill_dir, name)
            skill_file = os.path.join(skill_path, "SKILL.md")
            if not os.path.isfile(skill_file):
                continue
            
            # 去重（基于路径归一化）
            norm_path = os.path.normpath(skill_path)
            if norm_path in seen:
                continue
            seen.add(norm_path)
            
            # 读取 SKILL.md 头部的 YAML frontmatter
            desc = ""
            tags = []
            fm_name = name
            
            with open(skill_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2000)  # 只读前 2000 字符
            
            # 提取 YAML frontmatter
            fm = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
            if fm:
                fm_text = fm.group(1)
                desc_match = re.search(r'^description:\s*["\']?(.+?)["\']?\s*$', fm_text, re.MULTILINE)
                if desc_match:
                    desc = desc_match.group(1).strip()
                name_match = re.search(r'^name:\s*(.+)', fm_text, re.MULTILINE)
                if name_match:
                    fm_name = name_match.group(1).strip()
                tags_match = re.search(r'^tags:\s*\n((?:\s*-\s*.+\n?)*)', fm_text, re.MULTILINE)
                if tags_match:
                    tags = [t.strip().lstrip('- ').strip() for t in tags_match.group(1).split('\n') if t.strip().startswith('-')]
            
            skills.append({
                "name": fm_name,
                "dir_name": name,
                "path": skill_path,
                "description": desc,
                "tags": tags,
                "content": content,
            })
    
    return skills


# ─── 分类函数 ─────────────────────────────────────────

def classify_skill(skill: dict) -> dict:
    """分类：三级分层"""
    name = skill["name"].lower()
    dir_name = skill["dir_name"].lower()
    desc = skill["description"].lower()
    tags = [t.lower() for t in skill["tags"]]
    
    # 检查是否核心层
    if skill["dir_name"] in CORE_SKILLS or skill["name"] in CORE_SKILLS:
        return {"tier": "core", "category": "核心", "scene": ""}
    
    # 检查是否工具层
    for cat, (_, prefixes) in TOOLKIT_CLASSIFICATION.items():
        for prefix in prefixes:
            if name.startswith(prefix) or dir_name.startswith(prefix):
                return {"tier": "toolkit", "category": cat, "scene": ""}
    
    # 检查是否场景层
    for scene, (_, skill_names) in SCENARIO_CLASSIFICATION.items():
        for sname in skill_names:
            if name == sname or dir_name == sname:
                return {"tier": "scenario", "category": "", "scene": scene}
    
    # 关键词兜底
    for cat, (keywords, _) in TOOLKIT_CLASSIFICATION.items():
        full_text = f"{name} {dir_name} {desc} {' '.join(tags)}"
        for kw in keywords:
            if kw in full_text:
                return {"tier": "toolkit", "category": cat, "scene": ""}
    
    # 最后兜底：工具层-通用
    return {"tier": "toolkit", "category": "通用工具", "scene": ""}


# ─── 根据任务推荐 Skill ───────────────────────────────

def recommend_skills(task: str, skills: list):
    """根据任务描述推荐适配 Skill"""
    task_lower = task.lower()
    recommendations = {
        "core": [],
        "toolkit": [],
        "scenario": [],
    }
    
    for skill in skills:
        classification = classify_skill(skill)
        tier = classification["tier"]
        name_lower = skill["name"].lower()
        dir_lower = skill["dir_name"].lower()
        
        # 核心层始终推荐
        if tier == "core":
            recommendations["core"].append(skill["dir_name"])
            continue
        
        # 工具层和场景层：匹配关键词
        score = 0
        
        # 检查工具层触发关键词
        if tier == "toolkit":
            cat = classification["category"]
            for cname, (keywords, prefixes) in TOOLKIT_CLASSIFICATION.items():
                if cname != cat:
                    continue
                for kw in keywords:
                    if kw in task_lower:
                        score += 1
                for p in prefixes:
                    if p in name_lower or p in dir_lower:
                        score += 1
        
        # 检查场景层
        if tier == "scenario":
            scene = classification["scene"]
            for sname, (keywords, _) in SCENARIO_CLASSIFICATION.items():
                if sname != scene:
                    continue
                for kw in keywords:
                    if kw in task_lower:
                        score += 1
        
        # 检查 description 匹配
        if skill["description"]:
            for word in task_lower.split():
                if len(word) > 2 and word in skill["description"].lower():
                    score += 1
        
        if score > 0:
            if tier == "toolkit":
                recommendations["toolkit"].append((skill["dir_name"], classification["category"], score))
            elif tier == "scenario":
                recommendations["scenario"].append((skill["dir_name"], classification["scene"], score))
    
    return recommendations


# ─── 生成目录 ─────────────────────────────────────────

def generate_catalog(skills: list):
    """生成 CURRENT_CATALOG.md"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 分类所有 skill
    core_skills = []
    toolkit_skills = {}  # category → [skills]
    scenario_skills = {}  # scene → [skills]
    
    for skill in skills:
        c = classify_skill(skill)
        if c["tier"] == "core":
            core_skills.append(skill)
        elif c["tier"] == "toolkit":
            cat = c["category"]
            if cat not in toolkit_skills:
                toolkit_skills[cat] = []
            toolkit_skills[cat].append(skill)
        elif c["tier"] == "scenario":
            scene = c["scene"]
            if scene not in scenario_skills:
                scenario_skills[scene] = []
            scenario_skills[scene].append(skill)
    
    # 写入目录
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# 📋 当前 Skill 目录 ({len(skills)} 个技能)",
        f"",
        f"> 更新时间: {timestamp}",
        f"> 加载策略: core(始终) → toolkit(按需) → scenario(场景)",
        f"",
        f"---",
        f"",
        f"## 🏆 核心层 (Core) — 始终加载 — {len(core_skills)} 个",
        f"",
    ]
    
    for s in core_skills:
        desc = s["description"][:60] if s["description"] else "无描述"
        lines.append(f"- **{s['dir_name']}** — {desc}")
    
    lines += ["", "---", "", "## 🛠️ 工具层 (Toolkit) — 按任务按需加载", ""]
    
    for cat in sorted(toolkit_skills.keys()):
        skills_list = toolkit_skills[cat]
        lines.append(f"### {cat} — {len(skills_list)} 个")
        for s in skills_list:
            desc = s["description"][:60] if s["description"] else "无描述"
            lines.append(f"  - `{s['dir_name']}` — {desc}")
        lines.append("")
    
    lines += ["---", "", "## 🎯 场景层 (Scenario) — 按主题场景加载", ""]
    
    for scene in sorted(scenario_skills.keys()):
        skills_list = scenario_skills[scene]
        lines.append(f"### {scene} — {len(skills_list)} 个")
        for s in skills_list:
            desc = s["description"][:60] if s["description"] else "无描述"
            lines.append(f"  - `{s['dir_name']}` — {desc}")
        lines.append("")
    
    lines += ["", "---", "", "## 📋 按场景适配推荐", ""]
    lines += ["| 你说什么 | 可能需要的 skills |", "|----------|-------------------|"]
    examples = [
        ("\"帮我写个 Python 爬虫\"", "编码工具 + 浏览器自动化"),
        ("\"扫描这个项目安全漏洞\"", "安全工具包 (semgrep + gitleaks + trivy)"),
        ("\"发一封邮件给客户\"", "核心 (behavior-engine) + 通讯工具"),
        ("\"分析这份数据出报表\"", "数据处理 (jupyter + diagramming)"),
        ("\"部署到生产环境\"", "DevOps (docker + deploy + cli-proxy)"),
        ("\"帮我做个视频\"", "内容创作 (youtube + manju-studio)"),
    ]
    for example, need in examples:
        lines.append(f"| {example} | {need} |")
    
    content = "\n".join(lines)
    
    with open(CATALOG_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return core_skills, toolkit_skills, scenario_skills


# ─── 注册表生成 ───────────────────────────────────────

def generate_registry(skills: list):
    """生成 registry.json"""
    registry = {
        "generated_at": datetime.now().isoformat(),
        "total": len(skills),
        "skills": {},
    }
    
    for skill in skills:
        c = classify_skill(skill)
        registry["skills"][skill["dir_name"]] = {
            "name": skill["name"],
            "description": skill["description"],
            "tier": c["tier"],
            "category": c["category"],
            "scene": c["scene"],
            "path": skill["path"],
            "tags": skill["tags"],
        }
    
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    
    return registry


# ─── 统计 ─────────────────────────────────────────────

def print_stats(skills: list):
    """打印统计信息"""
    core_count = 0
    toolkit_count = 0
    scenario_count = 0
    
    for s in skills:
        c = classify_skill(s)
        if c["tier"] == "core":
            core_count += 1
        elif c["tier"] == "toolkit":
            toolkit_count += 1
        elif c["tier"] == "scenario":
            scenario_count += 1
    
    print(f"\n📊 Skill 统计")
    print(f"{'='*40}")
    print(f"  总技能数:      {len(skills)}")
    print(f"  🏆 核心层:     {core_count} (始终加载)")
    print(f"  🛠️  工具层:     {toolkit_count} (按需加载)")
    print(f"  🎯 场景层:     {scenario_count} (场景加载)")
    print(f"{'='*40}")
    print(f"  catalog: {CATALOG_FILE}")
    print(f"  registry: {REGISTRY_FILE}")


# ─── 主入口 ───────────────────────────────────────────

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        skills = scan_skills()
        print_stats(skills)
        return
    
    if len(sys.argv) > 1 and sys.argv[1] == "match":
        if len(sys.argv) < 3:
            print("用法: python3 classifier.py match \"你的任务描述\"")
            sys.exit(1)
        task = sys.argv[2]
        skills = scan_skills()
        recs = recommend_skills(task, skills)
        
        print(f"\n🧠 任务: \"{task}\"")
        print(f"{'='*50}")
        
        print(f"\n🏆 [核心层] 始终可用:")
        for s in recs["core"]:
            print(f"  ✅ {s}")
        
        toolkit_sorted = sorted(recs["toolkit"], key=lambda x: -x[2])
        print(f"\n🛠️  [工具层] 推荐 ({len(toolkit_sorted)} 个):")
        for name, cat, score in toolkit_sorted:
            print(f"  🔧 {name} [{cat}] (匹配度: {score})")
        
        scenario_sorted = sorted(recs["scenario"], key=lambda x: -x[2])
        print(f"\n🎯 [场景层] 推荐 ({len(scenario_sorted)} 个):")
        for name, scene, score in scenario_sorted:
            print(f"  📦 {name} ← {scene} (匹配度: {score})")
        
        print(f"\n💡 推荐加载命令:")
        print(f"  BEHAVIOR_DISABLE_ALL=true  # 关行为引擎（调试用）")
        print(f"  python3 classifier.py     # 重新扫描")
        return
    
    # 默认：扫描 + 分类 + 生成
    print("🔍 扫描 Skill 目录...")
    skills = scan_skills()
    print(f"   发现 {len(skills)} 个技能")
    
    print("\n🏷️  分类中...")
    for s in skills:
        c = classify_skill(s)
        tier_icon = {"core": "🏆", "toolkit": "🛠️", "scenario": "🎯"}.get(c["tier"], "📦")
        cat_info = c["scene"] if c["scene"] else c["category"]
        print(f"  {tier_icon} {s['dir_name']:30s} → [{c['tier']}] {cat_info}")
    
    print("\n📋 生成目录...")
    generate_catalog(skills)
    
    print("\n📦 生成注册表...")
    generate_registry(skills)
    
    print_stats(skills)
    print("\n✅ 完成")


if __name__ == "__main__":
    main()
