---
name: bt-go-project-deploy
description: >
  在宝塔面板上部署 Go 项目（编译好的二进制，含 Go SDK 版本安装、项目注册、进程启停、域名/外网映射），
  并在项目启动失败时排错。当用户要求把本机编译好的 Go 二进制部署成面板可管理的项目（含 Go SDK 安装、
  端口/运行用户配置、域名绑定），或 Go 项目启动失败/访问异常需要排查根因时使用。
  触发关键词：部署 Go、Go 项目、go build 产物部署、Go 二进制、Gin/Beego/Echo 服务、Go SDK 安装、
  go1.xx、GOPROXY、Go 项目启动失败、error while loading shared libraries、Address already in use。
  日常的启停/状态/日志/改配置/删项目等简单操作不依赖本 SOP，直接按工具描述调用即可。
---

# Go 项目部署与启动排错 SOP

> **停止。执行任何操作前，必须完整阅读本文档。**
> 本 Skill 的工具均指 bt_agent_mcp 插件暴露的 MCP 工具；同一能力在宝塔 AI 内置端可能有不同命名，按当前环境可用工具调用。
> 本 SOP 只覆盖两个主场景：**① 部署 Go 项目（含 Go SDK 安装）；② 项目启动排错**。其他简单操作（状态查看、启停、日志、域名、改配置、删除）不做 SOP，直接使用工具。

---

## 核心规则

1. **先只读侦察，再执行变更** —— 部署前先 `GoProjectInfo` 查是否已存在同名项目、`GoVersion(action=list)` 看 SDK；排错先读日志，不盲目重启。
2. **Go 是编译产物，无源码分析** —— `GoProjectCreate` 不需要分析步骤：给二进制绝对路径 + 端口 + 启动命令（缺省=二进制）直接注册。**不提供 analyze_only。**
3. **Go SDK 安装走 Bash 后台** —— btpygvm 装的是完整预编译包（快），但网络慢仍可能超时：`GoVersion(action=install, version=...)` 返回 `install_command` 后，必须用 `Bash(command=install_command, run_in_background=true)` 后台执行 + `BashStatus(task_id, wait=true)` 轮询；**一次只装一个版本**。
4. **创建即同步启动** —— `GoProjectCreate` 注册后面板同步启动（nohup 脚本 + pid，**无守护、崩了不自愈**）；创建成功 ≠ 进程一定活着，必须 `GoProjectInfo` 核验 `run=true` + 端口在 `listen`。
5. **Go 项目是编译二进制** —— 缺动态库/权限/端口占用是启动失败主因，排错按日志对号入座（场景二）。
6. **改配置即重启** —— `GoProjectModify(action='config')` 面板改完自动 stop+start；改端口后若绑了域名，nginx 反代按新端口重写。
7. **每个任务最多调用 15 次工具**，超出后汇总当前发现并停止。
8. **禁止操作**：删除项目目录/二进制源码、`rm -rf` 项目目录、修改宝塔/插件自身文件、读取插件 `data/` 凭据。

---

# 场景一：部署 Go 项目

## Step 0 —— 预检
1. 确认任务确为"部署 Go 项目"（非排错/运维）。
2. 确认有编译好的**可执行二进制**（`go build` 产物，Linux 目标平台），拿到绝对路径。
3. 确认**端口**（应用监听，10-65535）与**运行用户**（默认 www）。
4. 需要外网域名访问时，确认 Nginx 已安装；否则只能本机/内网访问。

## Step 1 —— Go SDK 确认 / 安装
1. `GoVersion(action='list')`：看 `data.installed` 是否已有可用 Go、`data.used` 当前版本。
2. 没有可用版本 → `GoVersion(action='list')` 的 `data.available` 挑一个稳定版（每项含 `install_command`），再调 `GoVersion(action='install', version=<go1.xx>)` 拿该版本的 install_command。
3. **用 Bash 后台执行**：`Bash(command=<install_command>, run_in_background=true)` → 得到 task_id → `BashStatus(task_id, wait=true)` 轮询到完成（预编译包下载+解压，通常几十秒到几分钟）。
4. 完成后 `GoVersion(action='list')` 确认该版本在 `installed`；需要时 `GoVersion(action='use', version=...)` 切换当前版本；拉依赖慢可 `GoVersion(action='goproxy', goproxy=<源>)` 设置 GOPROXY。

## Step 2 —— 创建项目（注册 + 启动）
调用 `GoProjectCreate(project_name=..., project_exe=<二进制绝对路径>, port=<端口>, ...)`：
- **必填**：`project_name`（字母/数字/下划线）、`project_exe`、`port`。
- **可选**：`project_cmd`（缺省=二进制本身）、`run_user`（默认 www）、`domains`（给则自动开启外网映射，'域名' 或 '域名:端口'）、`env_list`（`[{"k","v"}]`，如 `[{"k":"PORT","v":"9000"}]`，**字符串 "K=V" 会被 schema 拒**）、`env_file`、`is_power_on`（默认 true）、`ps`、`release_firewall`（需外网访问时 true）。

> 返回"创建成功"= 已注册并尝试启动；`data.project` 含 run/listen 运行态。

## Step 3 —— 启动验证（强制）
1. `GoProjectInfo(project_name=...)`：`run=true`、端口在 `listen`。
2. 用返回的 `log_files` 里应用日志路径（`/www/wwwlogs/go/<name>.log`）调 filesystem `Read` 看尾部无致命异常（`error while loading shared libraries`/`Address already in use`/`bind: address already in use`）。
3. 有域名映射的项目核验外网映射（`bind_extranet`）与反代（nginx `go_<name>.conf` 的 `proxy_pass 127.0.0.1:{port}`）。

- 全通过 → 按"完成汇报"收尾。
- 任一失败 → **转场景二排错**。

---

# 场景二：启动排错

> 适用：创建后 run=false、或用户报"Go 项目启动失败/访问异常"。

## Step 0 —— 快速定位现状（只读）
并行收集，不跳过：
1. `GoProjectInfo(project_name=...)`：`run`、`listen`、`project_config`（exe/命令/端口/用户/环境变量）。
2. 读应用日志尾部（`log_files` 里"应用日志"）找根因。
3. 已知配置：二进制路径、启动命令、端口、运行用户、是否绑域名。

收集后按症状进分支。

## 分支 A —— 启动失败（进程起不来 / run=false）
按日志根因对号入座：
| 日志特征 | 根因 | 处置 |
|---|---|---|
| `error while loading shared libraries: libxxx.so` | 缺动态库 | 汇报需装系统库（如 glibc/其他 .so），装后 `GoProjectControl(action='start')` |
| `bind: address already in use` / `EADDRINUSE` | 端口被占 | `GoProjectModify(action='config', port=新端口)`（自动重启） |
| `permission denied` / 无法写入日志 | 运行用户无权限 | `GoProjectModify(action='config', run_user=<有权限用户>)` |
| 启动即退出 / pid 无 | 启动命令错 / 环境变量缺 | 核对 `project_cmd` 与 `env_list`；`GoProjectControl(action='start')` 重试 |
| 二进制非当前平台编译 | 目标平台不符 | 重新 `go build` 目标平台二进制 |

- 修正后回场景一 Step 3 重新验证。**Go 进程无守护，崩了不会自动拉起**——排错后必须手动 start。

## 分支 B —— 访问异常（502/无法访问，但进程活着）
1. `GoProjectInfo`：进程在跑、端口在听吗？→ 不在则回分支 A。
2. **端口/反代核对**：`listen`（实际监听）vs `project_config.port`（反代目标）是否一致；grep `proxy_pass` `nginx/go_<name>.conf` 确认指向 `127.0.0.1:{实际端口}`。
   - 端口改了没同步 → `GoProjectModify(action='config', port=实际端口)`。
   - 反代指向错误端口 → 同上。
3. 域名绑定：`bind_extranet` 是否开、域名是否在 nginx `server_name`（未绑 → `GoProjectModify(action='add_domain', domains=[...])` + `bind_extranet`）。
4. 读 nginx error log（`log_files` 里 `/www/wwwlogs/<name>.error.log`）进一步定位。
5. 修正后验证。

## 分支 C —— 进程在但无响应 / 卡死
1. 应用日志尾部看异常/死锁（filesystem `Read`）。
2. `SystemInfo()` 看系统资源（CPU/内存/负载）。
3. 汇报，建议用户确认后 `GoProjectControl(action='restart')` 重启。

---

# 日常运维速查（简单操作，直接按工具描述调用）

| 需求 | 工具 |
|---|---|
| 查看项目列表/状态 | `GoProjectInfo()`（project_name 留空） |
| 查看单项目详情（run/listen/log_files/配置） | `GoProjectInfo(project_name=...)` |
| 启动 / 停止 / 重启 | `GoProjectControl(project_name, action='start'/'stop'/'restart')` |
| 看应用日志 / nginx 日志 | `GoProjectInfo` 返回 `log_files` → filesystem `Read` |
| 改二进制/命令/端口/用户/开机自启/环境变量/备注（自动重启） | `GoProjectModify(action='config', ...)` |
| 加域名 / 删域名（至少留一个） / 开 / 关外网映射 | `GoProjectModify(action='add_domain'/'remove_domain'/'bind_extranet'/'unbind_extranet', domains=[...])` |
| Go SDK 列表 / 安装（Bash 后台） / 切换 / 卸载 / 设 GOPROXY | `GoVersion(action='list'/'install'/'use'/'uninstall'/'goproxy', ...)` |
| **安装 Go SDK（下载+解压，后台）** | `GoVersion` install 取 `install_command` → `Bash(run_in_background=true)` + `BashStatus` 轮询 |
| 删除项目（**高风险，先确认**；保留二进制与目录） | `GoProjectDelete(project_name=...)` |

---

# 完成汇报模板（部署成功）

返回：项目名 / 二进制路径（project_exe）/ 端口 / 运行用户 / Go SDK 版本；若绑域名：访问地址 + nginx 配置路径；启动验证结果（进程/端口/日志）；遗留隐患提示（GOPROXY 未设、防火墙未放行、依赖库缺失、绑外网未开等）。
