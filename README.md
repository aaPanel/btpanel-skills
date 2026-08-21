# btpanel-skill

面向 AI Agent 的宝塔面板（aaPanel / BT Panel）运维 Skill。它帮助 Agent 安全地管理网站、文件、数据库、Docker、计划任务和服务器环境，并支持部署宝塔 MCP 服务以及接入 Claude Code、Codex、Cursor、WorkBuddy 等客户端。

## 功能

- 查询宝塔面板、网站、数据库、容器和服务器状态
- 排查网站、反向代理、数据库及运行环境故障
- 安全部署或升级宝塔面板与 MCP 服务
- 校验 TLS、来源白名单、安装包 SHA-256 和敏感凭据处理
- 提供 Go、HTML、Java、Node.js、Python 项目部署等配套 Skills

## 安装

### 一键安装（推荐）

已安装 Node.js 的用户可以通过 [Skills CLI](https://www.skills.sh/docs/cli) 安装：

```bash
npx skills add aaPanel/btpanel-skills
```

CLI 会检测支持的 Agent，并让你选择安装目标和范围。

### 手动安装

也可以将仓库克隆到 Agent 的 Skills 目录。以 Codex 为例：

```bash
git clone https://github.com/aaPanel/btpanel-skills.git "$CODEX_HOME/skills/btpanel"
```

也可以从主维护仓库获取：

```bash
git clone https://cnb.cool/btpanel/skill/btpanel-skill "$CODEX_HOME/skills/btpanel"
```

其他 Agent 请将仓库放入其用户级或项目级 Skills 目录。安装后重启或刷新 Agent 会话，并确认 `btpanel` Skill 已被发现。

## 使用

直接向 Agent 描述目标，例如：

- “检查这台宝塔服务器上的网站和数据库状态。”
- “帮我排查 Nginx 反向代理返回 502 的原因。”
- “在远程服务器安装宝塔 MCP，并接入当前 Agent。”
- “安装 Python 项目部署的配套 Skill。”

涉及安装、重启、端口、配置修改或删除资源时，Skill 会先说明影响并要求确认；Token、密码和私钥不会在输出中回显。

## 仓库结构

```text
.
├── SKILL.md                         # 主 Skill
├── assets/bt-skills/                # 配套部署与排障 Skills
├── references/vendor-sources.md     # 官方来源与固定校验信息
└── scripts/bt_mcp_setup.py          # 宝塔 MCP 安全部署编排器
```

## 维护方式

项目的主维护仓库已迁移至 [CNB](https://cnb.cool/btpanel/skill/btpanel-skill)，GitHub 仓库用于代码同步和版本发布。原有 GitHub PR 与 Issue 不再作为当前维护入口。

## 安全说明

本项目可能操作服务器、面板和敏感配置。使用前请完整阅读 [SKILL.md](SKILL.md) 中的安全边界；生产环境应采用最小权限、最小网络白名单、可信 TLS 证书和可回退的变更流程。

## License

本项目使用 [MIT License](LICENSE)。
