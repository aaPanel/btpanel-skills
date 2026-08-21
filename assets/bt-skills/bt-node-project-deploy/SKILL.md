---
name: bt-node-project-deploy
description: >
  在宝塔面板上部署 Node.js 项目（nodejs/general/pm2 三种类型，含 Nginx 域名/反代），
  并在项目启动失败或访问异常时排错。
  当用户要求把本机已有的 Node 项目目录部署成面板可管理的项目（含 node 版本、依赖安装、
  Nginx 代理/域名、pm2 守护），或 Node 项目启动失败/访问异常需要排查根因时使用。
  触发关键词：部署 Node、Node 项目部署、nodejs 部署、npm 项目部署、PM2 部署、
  Node 项目启动失败、npm 起不来、Node 报错、502、访问异常、pm2 errored、Cannot find module。
  日常的启停/状态/日志/改配置等简单操作不依赖本 SOP，直接按工具描述调用即可。
---

# Node.js 项目部署与启动排错 SOP

> **停止。执行任何操作前，必须完整阅读本文档。**
> 本 Skill 的工具均指 bt_agent_mcp 插件暴露的 MCP 工具；同一能力在宝塔 AI 内置端可能有不同命名，按当前环境可用工具调用。
> 本 SOP 只覆盖两个主场景：**① 部署 Node 项目；② 启动排错**。其他简单操作（状态查看、启停、日志、域名、改配置、删除）不做 SOP，直接使用工具。

---

## 核心规则

1. **先只读侦察，再执行变更** —— 部署前必须完成项目分析；排错先读日志，不盲目重启。
2. **创建后必须验证启动** —— "创建成功"不算完，必须确认进程存活 + 监听端口 + 日志无致命错误；验证失败即转入场景二。
3. **删除项目属高风险**，必须先获得用户明确确认；启停/重启/改配置属中风险，操作前说明影响。
4. **Node 版本匹配** —— 创建前用 `NodeVersion(action='list')` 检测已装版本；`package.json` 的 `engines.node` 不符时优先换已装版本或安装。
5. **端口唯一性** —— 创建/改端口前检查占用；**绑外网必须有端口**（`bind_extranet` 依赖 `port`）。
6. **绑域名 = 自动反代** —— Node 的反代由 nginx 模板按 `project_config.port` 自动生成（`proxy_pass http://127.0.0.1:{port}`），**无独立反代步骤**。访问异常时核对：`NodeProjectInfo` 的 `listen`（实际监听端口）vs 配置端口（反代目标）是否一致，不一致 = 502。
7. **依赖先行** —— nodejs 类型缺 `node_modules` 启动必失败。创建时 `install_deps=true` 或创建后装依赖再启动。
8. **每个任务最多调用 15 次工具**，超出后汇总当前发现并停止。
9. **禁止操作**：删除项目目录/源码、`rm -rf` 项目目录、修改宝塔/插件自身文件、读取插件 `data/` 凭据。

---

# 场景一：部署 Node 项目

## Step 0 —— 预检
1. 确认任务确为"部署新 Node 项目"（非排错/运维）。
2. 确定**项目类型**：`nodejs`（package.json scripts）/ `general`（直接指定启动文件）/ `pm2`（守护+cluster+自愈）。
3. 需要外网域名访问时，确认 Nginx 已安装；否则只能本机/内网访问。

## Step 1 —— 定位项目目录
- 用户给出 `project_cwd`（项目根，含 package.json），或：
- 用文件工具 `Glob(pattern='**/package.json')` / `LS(path=...)` 定位（排除 `node_modules`、`dist`、`build` 等构建目录）。
- **校验**：目录存在、含 `package.json`（nodejs/pm2 必需；general 可没有）、非敏感目录（`/etc`、`/boot`、插件 `data/` 等）。

## Step 2 —— 分析项目（部署前必须）
调用 `NodeProjectCreate(project_cwd=..., analyze_only=true)`（只读，不创建）。返回：
1. `package.json` 的 `name/version`、`engines.node`、`dependencies` 数量。
2. `scripts` 启动项列表（nodejs 类型的 `project_script` 从这里选）。
3. `node_modules` 是否存在（缺 → 需先装依赖）。
4. `port`/`port_hints`：从入口文件启发式探测的端口（仅供参考）。

**决策**：
- nodejs 类型：确认启动脚本名（`start`/`dev`/自定义），即 `project_script`。
- pm2 类型：确认入口文件（js 或 ecosystem 配置）与 `cluster` 实例数。
- 无端口或启发式不准 → 询问用户，创建时显式传 `port`（绑外网必需）。

## Step 3 —— Node 版本确认 / 安装
1. `NodeVersion(action='list')` 检测已装版本与可用包管理器（npm/yarn/pnpm）。
2. 若返回 `plugin_installed=false`：nodejs 版本管理器插件未装，**先调 `SoftwareInstall(name='nodejs')` 安装插件**（可再用 `SoftwareList(name='nodejs')` 查进度），装完继续。
3. 需要新装版本时，用 `NodeVersion(action='online', lts_only=true, page=...)` 浏览可安装版本（按版本从新到旧排序、本地分页，`lts_only=false` 看全部；每项 `installed` 标记是否已装），从中挑选稳定版。
4. 对照 `engines.node`（无则默认 LTS）。
5. 已装 → 记录版本号（如 `v20.15.0`）；无 → 询问用户后 `NodeVersion(action='install', version=..., install_pm2=<pm2 类型时 true>)`（插件安装，较慢，装完用 list 确认）。

## Step 4 —— 创建项目（注册）
调用 `NodeProjectCreate(project_type=..., project_name=..., project_cwd=..., nodejs_version=..., ...)`。
按类型传参：
- **nodejs**：`project_script`（scripts key，如 `'start'`）、`pkg_manager`（npm/yarn/pnpm）。
- **general**：`project_file`（启动文件绝对路径）、`project_args`（可选）。**同时必须传 `nodejs_version`**（三类型均必填、须已安装——general 漏传会直接报错，不是可选项）。
- **pm2**：`project_file`（js 入口或 ecosystem 配置，内容检测自动路由）、`cluster`、`watch`、`max_memory_limit`。**pm2 类型项目启动依赖该 node 版本已全局安装 pm2**——创建工具会自动检测，该版本缺 pm2 时自动调插件安装（结果 `data.pm2_auto_installed` 标记）；也可手动 `NodeVersion(action='module', version=<nodejs_version>, modules=['pm2'])`。
- **通用**：`port`（绑外网必需）、`run_user`（默认 www）、`env`（**注意：面板对 nodejs 类型的 env 注入有缺陷——存了但不写进启动脚本，需要环境变量的项目建议用 general 类型**）、`install_deps`（package.json 有依赖且未装 node_modules 时给 true）、`release_firewall`（需放行端口时）、`domains=['域名']`（绑域名+自动反代）。

**外网映射**：要域名访问 → 传 `domains`（自动写 `server_name` + `proxy_pass 127.0.0.1:{port}`，**无需额外反代步骤**）。`install_deps=true` 较慢（npm install），可接受等待。

## Step 5 —— 启动验证（强制）
创建后调用 `NodeProjectInfo(project_name=...)` 依次确认：
1. 进程存活（`run=true`）。
2. 应用端口在 `listen` 列表（`listen_ok=true`）。
3. 用返回的 `log_files` 里应用日志路径，调 filesystem `Read` 看尾部无致命异常（`Cannot find module`/`EADDRINUSE`/`throw er`）。

⚠️ **pm2 类型不要信创建返回的「已自动启动」**：daemon 可能未持久化（`run:false`、`listen` 空但 `listen_ok=true`）。创建后必须：
① 立即 `NodeProjectInfo` 核验 `run=true`；
② 间隔几秒**再次** `NodeProjectInfo` 复检持久化（本地等待即可，不调长工具）；
③ 不持久 → `NodeProjectControl(action='start')` 重拉再复检。

- 全通过 → 按"完成汇报"收尾。
- 任一失败 → **转场景二排错**。

---

# 场景二：启动排错

> 适用：部署后验证失败、或用户报"Node 项目启动失败/访问异常"。

## Step 0 —— 快速定位现状（只读）
并行收集，不跳过：
1. `NodeProjectInfo(project_name=...)`：`run`、`listen`、`listen_ok`（区分"进程没起来"与"起来了但访问不了"）；pm2 项目看状态。
2. 读应用日志尾部：用返回的 `log_files` 应用日志路径调 filesystem `Read`，找异常堆栈根因。
3. 已知配置：项目类型、入口/脚本、node 版本、端口、是否已装依赖。

收集后按症状进分支。

## 分支 A —— 启动失败（进程起不来 / run=false）
按日志根因对号入座：
| 日志特征 | 根因 | 处置 |
|---|---|---|
| `Error: Cannot find module 'x'` | 依赖未安装 | `NodeProjectCreate(project_cwd=<项目目录>, nodejs_version=..., project_script=..., install_deps=true)` 或装依赖后重启 |
| `EADDRINUSE` / `Port 3000 is already in use` | 端口被占 | `NodeProjectModify(action='config', port=新端口)` 后 `NodeProjectControl(action='restart')` |
| `npm ERR! Missing script: "start"` | scripts key 名错 | `NodeProjectModify(action='config', project_script=正确key)` |
| `throw er; Unhandled 'error' event` | 启动即崩（端口/环境） | 看堆栈中具体原因；换端口或补 env |
| `ERR_REQUIRE_ESM` / 语法错误 | 模块系统/代码问题 | 检查入口与 `package.json` 的 `type` 字段 |
| node 版本引擎不符 | `engines.node` 不匹配 | `NodeProjectModify(action='config', nodejs_version=匹配版本)` 或 `NodeVersion(action='install')` |
| 进程起来但 pid 无/端口没监听 | 启动后立即退出 | 读日志尾找 `exit`/`Error` 根因 |

- 无明确报错 → 查 `NodeProjectInfo`：run、listen、启动命令是否完整；`log_files` 有无 pm2 err.log。
- 修复后回到场景一 Step 5 重新验证。

## 分支 B —— 访问异常（502/无法访问，但进程活着）
1. `NodeProjectInfo`：进程在跑、端口在听吗？→ 不在则回分支 A。
2. **反代端口匹配**：看 `listen`（实际监听）vs `project_config.port`（反代目标）是否一致；grep `proxy_pass` `node_<name>.conf`（`/www/server/panel/vhost/nginx/node_<name>.conf`）确认反代指向 `127.0.0.1:{实际端口}`。
   - 端口改了没同步 → `NodeProjectModify(action='config', port=实际端口)`（有 domains 时自动重写反代）。
   - 反代指向错误端口 → 同上。
3. **域名绑定**：`bind_extranet` 是否开、域名是否在 nginx `server_name`（未绑 → `NodeProjectModify(action='add_domain', domains=[...])`）。
4. 读 nginx error log（`log_files` 里 `/www/wwwlogs/<name>.error.log`）进一步定位。
5. 修正后验证。

## 分支 C —— PM2 项目异常
1. `NodeProjectInfo` 看 pm2 状态（online/stopped/errored）。
2. `errored`（崩溃超限）→ 读 `log_files` 里 pm2 `err.log` 找根因；修复后用 `NodeProjectControl(action='restart')` 重启。
3. 读 `/www/wwwlogs/pm2/<name>/out.log|err.log`。
4. 依赖问题 → 同分支 A。

## 分支 D —— 进程在但无响应 / 卡死
1. 应用日志尾部看异常/死锁（filesystem `Read`）。
2. `SystemInfo()` 看系统资源（CPU/内存/负载）。
3. 汇报，建议用户确认后 `NodeProjectControl(action='restart')` 重启。

---

# 日常运维速查（简单操作，直接按工具描述调用）

| 需求 | 工具 |
|---|---|
| 查看项目列表/状态 | `NodeProjectInfo()`（project_name 留空） |
| 查看单项目详情（含日志路径） | `NodeProjectInfo(project_name=...)` |
| 启动 / 停止 / 重启 | `NodeProjectControl(project_name, action='start'/'stop'/'restart')` |
| 看应用日志 / pm2 / nginx 日志 | `NodeProjectInfo` 返回 `log_files` → filesystem `Read` |
| 改脚本/参数/node 版本/端口/用户/环境/内存 | `NodeProjectModify(action='config', ...)`（重启生效） |
| 加域名 / 删域名（至少留一个） | `NodeProjectModify(action='add_domain'/'remove_domain', domains=[...])` |
| node 版本检测 / 在线浏览 / 安装 | `NodeVersion(action='list'/'online'/'install', ...)` |
| 给 node 版本装全局模块（pm2/pnpm/yarn 等） | `NodeVersion(action='module', version=<nodejs_version>, modules=['pm2'])` |
| 删除项目（**高风险，先确认**） | `NodeProjectDelete(project_name=...)`（保留目录源码） |

---

# 完成汇报模板（部署成功）

返回：项目名 / 项目类型 / 目录 / node 版本 / 运行用户 / 监听端口；若绑域名：访问地址 + nginx 配置路径；应用日志路径；启动验证结果（进程/端口/日志）；遗留隐患提示（依赖未装、env 未注入等）。
