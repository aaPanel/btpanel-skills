---
name: bt-java-project-deploy
description: >
  在宝塔面板上部署 Java jar 项目（Spring Boot），并在项目启动失败时排错。
  当用户要求把本机已有的 jar 包部署成面板可管理的 Java 项目（含 JDK、Nginx 代理/域名），
  或 Java 项目启动失败/访问异常需要排查根因时使用。
  触发关键词：部署 Java、jar 包部署、Spring Boot 部署、Java 项目创建、
  Java 项目启动失败、jar 起不来、jar 启动报错、502、访问异常、JDK 版本不匹配。
  日常的启停/状态/日志/改配置等简单操作不依赖本 SOP，直接按工具描述调用即可。
---

# Java 项目部署与启动排错 SOP

> **停止。执行任何操作前，必须完整阅读本文档。**
> 本 Skill 的工具均指 bt_agent_mcp 插件暴露的 MCP 工具；同一能力在宝塔 AI 内置端可能有不同命名，按当前环境可用工具调用。
> 本 SOP 只覆盖两个主场景：**① 部署 Java 项目；② 项目启动排错**。其他简单操作（状态查看、启停、日志、域名、改配置、删除）不做 SOP，直接使用工具。

---

## 核心规则

1. **先只读侦察，再执行变更** —— 部署前必须完成 jar 分析；排错先读日志，不盲目重启。
2. **创建后必须验证启动** —— "创建成功"不算完，必须确认进程存活 + 监听端口 + 日志无致命错误；验证失败即转入场景二。
3. **删除项目属高风险**，必须先获得用户明确确认；启停/重启/改配置属中风险，操作前说明影响。
4. **JDK 匹配** —— Spring Boot 3.x 需 JDK 17+，Boot 2.x 需 JDK 8/11；安装或切换前先检测本机 JDK。
5. **端口唯一性** —— 创建/改端口前检查占用。
6. **域名可访问 = 三件事** —— ① `add_domain` 写入 `server_name`；② `bind_extranet` 开启外网框架（生成 conf 骨架，**不含反代**）；③ `add_proxy(proxy_port=应用端口)` 真正注入 `proxy_pass http://127.0.0.1:port`。**漏掉 ③ 会访问 403**。创建时带 `domains` 会完成 ①② 并尝试自动建 ③，但**必须验证**（`proxy_list` 或 grep `proxy_pass`），缺失即补 `add_proxy`。
7. **每个任务最多调用 15 次工具**，超出后汇总当前发现并停止。
8. **禁止操作**：删除 jar 源文件、`rm -rf` 项目目录、修改宝塔/插件自身文件、读取插件 `data/` 凭据。

---

# 场景一：部署 Java 项目

## Step 0 —— 预检
1. 确认任务确为"部署新 Java 项目"（非排错/运维）。
2. 需要外网域名访问时，确认 Nginx 已安装；否则只能本机/内网访问。
3. （可用 todo 工具时）建任务列表：定位 jar → 分析 → JDK → 创建 → 验证。

## Step 1 —— 定位 jar 包
- 用户直接给出 jar 绝对路径，或：
- 用文件工具 `Glob(pattern='**/*.jar')` / `LS(path=...)` 在服务器上定位 jar（排除运行目录与 `lib/` 依赖库）。
- **校验**：路径存在、是普通文件、非敏感目录（`/etc`、`/boot`、插件 `data/` 等）。
- 记录 jar 绝对路径与所在目录（jar_path）。

## Step 2 —— 分析 jar（部署前必须）
调用 `JavaProjectCreate(jar_path=..., analyze_only=true)`（只读，不创建）。返回：
1. 是否 Spring Boot 可执行 jar（jar_info）。
2. **应用端口**（`application.yml/properties` 的 `server.port`，或命令行/环境变量覆盖）。
3. 实际生效的配置文件路径与优先级（config_files）。
4. **启动前隐患清单**（tips：数据库/中间件连通性、账号密码疑似错误、profile 缺失等）。

**决策**：
- 解析不出端口 → 询问用户指定，并在创建时显式传 `port`。
- 隐患清单含阻断级（error）→ 向用户说明，确认是否继续。

## Step 3 —— JDK 确认 / 安装
1. `JavaJdk(action='list')` 检测本机 JDK（name/path/operation：0 未装 1 已装 2 系统 3 安装中）。
2. 按 Spring Boot 版本定所需 JDK（Boot3→17+，Boot2→8/11）。
3. 已有 → 记录 path；无 → 询问用户后 `JavaJdk(action='install', version=...)`（异步，用 list 轮询 operation=3→1）。

## Step 4 —— 创建项目（注册）
调用 `JavaProjectCreate(project_name=..., jar_path=..., port=..., [domains=...])`。
创建前确认参数：`project_name`（1-20 字符、不重复）、jar 路径、JDK 路径（缺省自动选已装）、`run_user`（默认 www）、端口（**检查未被占用**）、启动命令（缺省自动拼 `{jdk}/bin/java -jar ... --server.port=<port>`）。
**外网映射决策**：
- 要域名访问 → `domains=['域名']`（或 `['域名:端口']`），创建时绑定域名并开启外网框架（`server_name`）。创建工具会**尝试**自动建反代（`proxy_path` 默认 `'/'` 全站，可改如 `'/api'`；`proxy_path=''` 关闭）。
  **创建后必须验证反代已注入**：`JavaProjectModify(action='proxy_list')` 应有 `proxy_port`，或 grep `proxy_pass` `java_<name>.conf`。缺失 → `JavaProjectModify(action='add_proxy', proxy_port=应用端口, proxy_dir='/')` 补齐，否则访问 403。
- 仅本机 → 不传 domains（`bind_extranet=0`）。

## Step 5 —— 启动验证（强制）
创建后调用 `JavaProjectInfo(project_name=...)` 依次确认：
1. 进程存活（有 pid）。
2. 应用端口在 `listen` 列表。
3. 用返回的 `log_files` 里的应用日志路径，调 filesystem `Read` 看尾部无致命异常（`Exception`/`Caused by`）。
- 全通过 → 按"完成汇报"收尾。
- 任一失败 → **转场景二排错**。

---

# 场景二：项目启动排错

> 适用：部署后验证失败、或用户报"Java 项目启动失败/访问异常"。

## Step 0 —— 快速定位现状（只读）
并行收集 3 项，不跳过：
1. `JavaProjectInfo(project_name=...)`：pid 是否生成、`listen` 端口、运行态（区分"进程没起来"与"进程起来了但访问不了"）。
2. 读应用日志尾部：用返回的 `log_files` 应用日志路径调 filesystem `Read`，找异常堆栈根因。
3. 已知配置：jar 路径、JDK、端口、启动命令。

收集后按症状进分支。

## 分支 A —— 启动失败（进程起不来 / pid 无 / 端口未监听）
按日志根因对号入座：
| 日志特征 | 根因 | 处置 |
|---|---|---|
| `Address already in use` / 端口占用 | 端口被占 | 换端口：`JavaProjectModify(action='config', project_cmd=改 --server.port=)` 或重建 |
| `UnsupportedClassVersionError` | JDK 版本过低/过高 | `JavaProjectModify(action='config', project_jdk=匹配JDK)` 或 `JavaJdk(action='install', version=...)` |
| `ClassNotFoundException` / 缺依赖 | 依赖库缺失 | 检查启动命令 `-Dloader.path` 与 lib 目录，改 `project_cmd` |
| 数据库/中间件连接失败 | 服务未起或账号密码错 | 结合 Step 2 的 tips，确认中间件与账号 |
| 配置缺失 / 环境变量 | 缺配置 | 改 `project_cmd`/`env_file` 补配置后重启 |

- 无明确报错 → 查 `JavaProjectInfo`：pid 是否生成、端口是否监听、启动命令是否完整。
- 修复后回到场景一 Step 5 重新验证。

## 分支 B —— 访问异常（502 / 无法访问，但进程活着）
1. `JavaProjectInfo`：进程在跑、端口在听吗？→ 不在则回分支 A。
2. **nginx 反代目标匹配**：用 `log_files` 或 `JavaProjectInfo` 定位 `java_<name>.conf`，调 filesystem `Read` 看 `proxy_pass` 是否指向 `127.0.0.1:实际端口`。
   - 配置里**没有** `proxy_pass` location（`project_config.proxy_info` 为空）→ 反代缺失，用 `JavaProjectModify(action='add_proxy', proxy_port=实际端口, proxy_dir='/')` 补齐，`action='proxy_list'` 核对。
   - 端口改了但反代没同步 → `JavaProjectModify(action='add_proxy', proxy_port=新端口)` 或改配置重建。
3. **反代是否真注入**：`JavaProjectModify(action='proxy_list')` 看有无 `proxy_port`；`grep proxy_pass /www/server/panel/vhost/nginx/java_<name>.conf`。`bind_extranet` 为开但 `proxy_pass` 为空 → 漏了 `add_proxy`，用 `action='add_proxy', proxy_port=实际端口` 补。
4. **外网绑定状态**：`bind_extranet` 是否为开；域名是否在 nginx `server_name`（未开 → `JavaProjectModify(action='bind_extranet')`）。
5. 读 nginx error log（`log_files` 里的路径）进一步定位。
6. 修正后验证。

## 分支 C —— 进程在但无响应 / 卡死
1. 应用日志尾部看异常/死锁（filesystem `Read`）。
2. `SystemInfo()` 看系统资源（CPU/内存/负载）是否异常。
3. 汇报，建议用户确认后 `JavaProjectControl(action='restart')` 重启。

---

# 日常运维速查（简单操作，直接按工具描述调用）

| 需求 | 工具 |
|---|---|
| 查看项目列表/状态 | `JavaProjectInfo()`（project_name 留空） |
| 查看单项目详情（含日志路径） | `JavaProjectInfo(project_name=...)` |
| 启动 / 停止 / 重启 | `JavaProjectControl(project_name, action='start'/'stop'/'restart')` |
| 看应用日志 / nginx 日志 | `JavaProjectInfo` 返回 `log_files` → filesystem `Read` |
| 加域名 / 删域名（至少留一个） | `JavaProjectModify(action='add_domain'/'remove_domain', domains=[...])` |
| 开/关外网框架（只生成 server_name 骨架，**不注入反代**） | `JavaProjectModify(action='bind_extranet'/'unbind_extranet')` |
| 增反代（真正注入 proxy_pass） | `JavaProjectModify(action='add_proxy', proxy_port=应用端口, proxy_dir='/')` |
| 删反代 | `JavaProjectModify(action='remove_proxy', proxy_id=...)`（id 用 proxy_list 取） |
| 查反代 | `JavaProjectModify(action='proxy_list')` |
| 改 jar / JDK / 启动命令 / 运行用户 / 守护 | `JavaProjectModify(action='config', ...)`（重启生效） |
| 删除项目（**高风险，先确认**） | `JavaProjectDelete(project_name=...)`（保留 jar） |

---

# 完成汇报模板（部署成功）

返回：项目名 / jar 路径 / 运行用户 / JDK 路径 / 监听端口；若绑域名：访问地址 + nginx 配置路径；应用日志路径；启动验证结果（进程/端口/日志）；遗留隐患提示（若有）。
