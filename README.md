# 🚀 cxpSkills

> 沉淀高价值工作流的个人 AI Agent Skill 仓库。
> 这里不收集花里胡哨的闲聊 Prompt，只存放真正能解决硬核痛点、经过实战检验的专业 AI 技能。

---

## 📦 现有技能列表

### 🛡️ [cxpPattenWrite](./cxpPattenWrite/) (专利交底书外挂)

**别把写代码的脑子直接用来写专利。** 
这是一个专为工程师和研究员打造的专利写作 Skill。它能把你的聊天记录、零散脑图、技术笔记，强行拉入“问题-方法-效果”的专业框架，并榨取出“方法、技术、系统”三层保护点。

👉 [查看完整说明文档与使用防坑指南](./cxpPattenWrite/README.md)

---

## 🛠️ 如何获取与安装 (Git Commands)

如果你觉得这个技能对你有用，可以通过简单的 Git 命令将它拉取到本地，并配置到你的 AI IDE（如 Trae 或 Windsurf）中。

### 1. 克隆仓库到本地

打开你的终端（Terminal 或 PowerShell），执行以下命令将整个仓库拉取下来：

```bash
# 从 GitHub 克隆本项目
git clone https://github.com/你的用户名/cxpSkills.git

# 进入目录
cd cxpSkills
```
*(注：请将上述链接中的 `你的用户名` 替换为真实的 GitHub 仓库地址)*

### 2. 将 Skill 安装进 IDE

AI IDE 通常在用户目录下有一个专门存放自定义 Skill 的文件夹。你需要将本仓库里的具体 Skill 文件夹（例如 `cxpPattenWrite`）复制过去。

**💻 Windows 环境 (PowerShell):**
如果你用的是 Windsurf，可以执行以下命令：
```powershell
# 将专利撰写技能复制到 Windsurf 的全局 skills 目录
Copy-Item -Path ".\cxpPattenWrite" -Destination "$env:USERPROFILE\.windsurf\skills\cxpPattenWrite" -Recurse -Force
```

**🍎 Mac / Linux 环境:**
```bash
# 将专利撰写技能复制到 IDE 的 skills 目录
cp -r ./cxpPattenWrite ~/.windsurf/skills/
```
*(注：如果你用的是 Trae 或其他 IDE，请将 `.windsurf` 替换为对应的隐藏目录如 `.trae`)*

### 3. 生效与使用

1. 完成文件复制后，**重启你的 IDE**（或重新加载工作区）。
2. 在 AI 对话面板中，输入触发命令（例如直接输入 `cxpPattenWrite` 或 `/` 选择该技能）。
3. 贴入你的零散技术草稿，即可体验“降维打击”式的专利整理！

---

## 🤝 贡献与分享

如果你也有压箱底的私藏工作流、好用的结构化 Prompt 框架，欢迎 `Fork` 本仓库，添加你的 Skill 文件夹后提交 `Pull Request`！
