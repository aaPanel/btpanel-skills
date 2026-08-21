---
name: bt-python-project-deploy
description: >
  在宝塔面板上部署 Python 项目（uwsgi/gunicorn/command 三种运行方式，含虚拟环境配置、
  Python 版本安装、requirements 依赖、Nginx 域名/反代），并在环境准备或启动失败时排错。
  当用户要求把本机已有的 Python 项目目录部署成面板可管理的项目（含 Python 版本安装、
  虚拟环境创建、pip 依赖、uwsgi/gunicorn 托管或自定义命令启动），或 Python 项目
  启动失败/访问异常/环境准备失败需要排查根因时使用。
  触发关键词：部署 Python、Python 项目部署、django/flask/fastapi/sanic 部署、
  uvicorn/gunicorn/uwsgi、虚拟环境 venv、pip install、Python 项目启动失败、
  ImportError、ModuleNotFoundError、502、访问异常、celery、关联进程、requirements。
  日常的启停/状态/日志/改配置/装包等简单操作不依赖本 SOP，直接按工具描述调用即可。
---

# Python 项目部署与启动排错 SOP

> **停止。执行任何操作前，必须完整阅读本文档。**
> 本 Skill 的工具均指 bt_agent_mcp 插件暴露的 MCP 工具；同一能力在宝塔 AI 内置端可能有不同命名，按当前环境可用工具调用。
> 本 SOP 只覆盖两个主场景：**① 部署 Python 项目；② 环境准备/启动排错**。其他简单操作（状态查看、启停、日志、域名、改配置、装包、删除）不做 SOP，直接使用工具。

---

## 核心规则

1. **先只读侦察，再执行变更** —— 部署前必须完成项目分析；排错先读日志，不盲目重启。
2. **创建成功 ≠ 启动成功** —— Python 创建项目后环境准备（装依赖+生成启动脚本+尝试启动）是**后台异步**的。必须用 `PythonProjectInfo` 轮询 `prep_status` 到 `complete`，再核验进程存活 + 监听端口 + 日志无致命错误；`prep_status=failure` 立即转场景二。**这是本场景最容易栽的坑。**
3. **建项目前必须有虚拟环境** —— 面板要求 `python_bin` 是已托管的 venv/conda（`can_use_directly`）。部署顺序：版本 → 环境 → 项目。
4. **Python 版本安装走 Bash 后台** —— 源码编译极慢（10-30 分钟），不得用同步工具卡住；必须 `Bash(run_in_background=true)` + `BashStatus` 轮询。
5. **删除项目保留虚拟环境** —— venv 与项目非强绑定（可复用/共享），删除不删 venv（面板语义）；如需移除单独用 `PythonEnv(action='remove')`。删除本身仍高风险（停进程/清配置/删记录），先确认。
6. **绑域名 = 外网映射 + 反代** —— `add_domain` 只写域名，需 `bind_extranet` 生成 nginx 配置（proxy 到 127.0.0.1:port）；path→port 反代（`add_proxy`）**必须先开启外网映射**。
7. **每个任务最多调用 15 次工具**，超出后汇总当前发现并停止。
8. **禁止操作**：删除项目目录/源码、`rm -rf` 项目目录、修改宝塔/插件自身文件、读取插件 `data/` 凭据。

---

# 场景一：部署 Python 项目

## Step 0 —— 预检
1. 确认任务确为"部署新 Python 项目"（非排错/运维）。
2. 确定**运行方式 `stype`**：`uwsgi` / `gunicorn` / `command`（直跑，python 文件方式已并入 command）。
3. 确认**协议**：`wsgi`（Flask/Django 传统）/ `asgi`（FastAPI/Sanic/uvicorn）。
4. 需要外网域名访问时，确认 Nginx 已安装；否则只能本机/内网访问。

## Step 1 —— 定位项目目录
- 用户给出 `project_path`（项目根，含 `*.py`），或：
- 用文件工具 `Glob(pattern='**/*.py')` / `LS(path=...)` 定位（排除 `node_modules`、`dist`、`.venv`、`venv` 等）。
- **校验**：目录存在、含入口 `*.py`（或 `requirements.txt`）、非敏感目录（`/etc`、`/boot`、插件 `data/` 等）。

## Step 2 —— 分析项目（部署前必须）
调用 `PythonProjectCreate(project_path=..., analyze_only=true)`（只读，不创建）。返回：
1. `framework`：django/flask/sanic/fastapi 等（按 requirement/入口代码识别）。
2. `runfile`：入口文件、`xsgi`（wsgi/asgi）、`call_app`（可调用对象名）。
3. `requirement_path`：requirements 文件（缺 → 需先补）。
4. `has_venv` / `port` / `port_hints`：目录是否自带 venv、启发式端口（仅供参考）。

**决策**：
- 选 `stype`：Django/Flask 传统 → `gunicorn`（或 `uwsgi`）；FastAPI/Sanic → `gunicorn` + `xsgi='asgi'`；无框架/自写 socket → `command`（`project_cmd='{python_bin} -u {runfile} {parm}'`）。
- 确认 `rfile`（启动文件绝对路径）与 `call_app`（app/application，或自动探测）。
- 无端口或启发式不准 → 询问用户，创建时显式传 `port`（uwsgi/gunicorn 必填；command 可空）。

## Step 3 —— Python 版本确认 / 虚拟环境准备
1. `PythonVersion(action='list')` 查看已装 Python 版本与当前默认；返回含 `install_hint`。
2. 需要新版本时 `PythonVersion(action='online', ...)` 浏览可安装版本（每项含 `install_command`），**用 Bash 后台安装**：
   - `Bash(command=<install_command>, run_in_background=true)` → 得到 `task_id`；
   - `BashStatus(task_id, wait=true)` 轮询到完成（后台最长 30 分钟，超时强杀；若超时汇报并让用户决定重跑/换源）。
3. `PythonEnv(action='list')` 查看虚拟环境：找 `can_use_directly=true` 的 venv；若需新建，看每项 `source` 与顶层 `source_priority` 判断源优先级。
4. 没有可用 venv → `PythonEnv(action='create', venv_name=<项目名或自定义>, python_bin=<源环境bin>, ps=<备注>)` 创建，得到 `python_bin`（venv_path + python_bin）。创建较慢（venv + ensurepip），**创建成功返回后必须再跑一次 `PythonEnv(action='list')` 确认该 venv 出现在列表里且目录真实存在**——工具已规避面板 `create_venv_sync` 的"只写记录不建目录"假成功缺陷并做磁盘校验，但仍建议复核。
   **源 python_bin 选择优先级（重要）**：① 面板安装的 Python 版本（`source=panel_installed`，如 `/www/server/pyporject_evn/versions/<ver>/bin/python`，**推荐**）→ ② 系统 Python（`source=system`，如 `/usr/bin/python3`，需有 venv/pip，缺则自动安装可能失败）→ ③ 面板自带 pyenv（`source=panel_pyenv`，`/www/server/panel/pyenv`——打包时移除过大量非必要文件，**不适合普通用户**，工具会直接拒绝）。优先用 `PythonVersion` 装好版本再作源。

## Step 4 —— 创建项目（注册）
调用 `PythonProjectCreate(project_name=..., project_path=..., python_bin=<第3步的venv>, stype=..., ...)`。
按类型传参：
- **uwsgi**：`rfile` + `call_app` + `port`（+ `processes`/`threads`）。
- **gunicorn**：`rfile` + `call_app` + `port`；FastAPI/Sanic 加 `xsgi='asgi'`。
- **command**：`project_cmd`（如 `'{python_bin} -u {runfile}'`，**占位符由工具替换为实际路径**），`port` 可留 0。
- **通用**：`user`（默认 root）、`env_list=[{"k","v"}]`（**必须 dict 格式**，如 `[{"k":"PORT","v":"9000"}]`，字符串 "K=V" 会被 schema 拒绝）、`env_file`、`requirement_path`（有则自动装依赖）、`auto_run`、`release_firewall`（需外网访问时 true）、`initialize`（可选初始化命令）。
创建返回 `prep_status=running`（或 complete/failure）+ `prep_log` 路径。

## Step 5 —— 环境准备等待 + 启动验证（强制）
1. `PythonProjectInfo(project_name=...)` 轮询 `prep_status`：**`running` → 等待后重查**（本地 sleep 即可，不调长工具）；到 `complete` 继续，到 `failure` **立即转场景二分支 A**。
2. 核验启动：`run=true`、应用端口在 `listen` 列表。
3. 用返回的 `log_files` 里应用日志路径，调 filesystem `Read` 看尾部无致命异常（`ImportError`/`ModuleNotFoundError`/`Address already in use`/`Error: [Errno 98]`）。
4. 有域名映射的项目核验 `services`（关联进程）与反代。

- 全通过 → 按"完成汇报"收尾。
- 任一失败 → **转场景二排错**。

---

# 场景二：环境准备 / 启动排错

> 适用：部署后验证失败（prep_status=failure / run=false）、或用户报"Python 项目启动失败/访问异常"。

## Step 0 —— 快速定位现状（只读）
并行收集，不跳过：
1. `PythonProjectInfo(project_name=...)`：`prep_status`、`run`、`listen`、`log_files`（区分"环境没准备好 / 进程没起来 / 起来了但访问不了"）。
2. 按症状读日志：`prep_status=failure` 读**环境准备日志**（`log_files` 里 "环境准备日志"）；`run=false` 读**应用日志**（`log_files` 里 stype 对应项：error.log / uwsgi.log / gunicorn_error.log）。
3. 已知配置：stype、入口文件、虚拟环境、端口、是否已装依赖。

收集后按症状进分支。

## 分支 A —— 环境准备失败（prep_status=failure）
- 读 `log_files` 里的"环境准备日志"（`/www/server/python_project/vhost/logs/<name>.log`）找根因：
  | 日志特征 | 根因 | 处置 |
  |---|---|---|
  | `pip ... Could not find a version that satisfies` | 依赖源/包名错 | 换 pip 源或 `PythonEnv` 手动装对应包；`PythonProjectControl(action='restart')` 重拉 |
  | `ImportError` / `ModuleNotFoundError: No module named 'x'` | 缺依赖 | `PythonEnv(action='package', python_bin=<env>, package_action='install', package_name='x')` 后重启 |
  | `configure: error` / `make: *** Error`（装托管依赖失败） | 编译缺系统库 | 汇报，需安装系统依赖库后再 `re_prep_env` 或重建 |
  | `uwsgi/gunicorn` 命令 not found | 托管依赖没装上 | 同上 |
- 修复后 `PythonProjectControl(action='restart')`（或 `action='start'`）重新拉取，回场景一 Step 5 复检。

## 分支 B —— 启动失败（进程起不来 / run=false，但 prep_status=complete）
按应用日志根因对号入座：
| 日志特征 | 根因 | 处置 |
|---|---|---|
| `ModuleNotFoundError` / `ImportError: No module named 'x'` | 依赖未装 | `PythonEnv(action='package', python_bin=..., package_action='install', package_name='x')` 后重启 |
| `Error: [Errno 98] Address already in use` | 端口被占 | `PythonProjectModify(action='config', port=新端口)` 后 `PythonProjectControl(action='restart')` |
| `[Errno 13] Permission denied` | 目录/日志权限 | `PythonProjectModify(action='config', user=<有权限用户>)` 或修目录属主 |
| `No module named 'app'` / `gunicorn.errors.HaltServer` | rfile/call_app 错 | `PythonProjectModify(action='config', rfile=/call_app=正确值)` |
| `Command '('...')' returned non-zero exit status` | command 命令本身失败 | 检查 `project_cmd` 与环境变量 |
| `django.core.exceptions.ImproperlyConfigured` | Django settings 问题 | 检查 env_list 里的 DJANGO_SETTINGS_MODULE 等 |
| 进程起来但 pid 无/端口没监听 | 启动后立即退出 | 读日志尾找 `Traceback` 根因 |

- 无明确报错 → 查 `PythonProjectInfo`：run、listen、启动脚本（`project_config`）是否完整。
- 修复后回场景一 Step 5 重新验证。

## 分支 C —— 访问异常（502/无法访问，但进程活着）
1. `PythonProjectInfo`：进程在跑、端口在听吗？→ 不在则回分支 B。
2. **映射/反代核对**：
   - 域名是否绑定、`bind_extranet` 是否开启（未开启 → `PythonProjectModify(action='add_domain', domains=[...])` + `action='bind_extranet'`）。
   - `listen`（实际监听端口）vs `project_config.port`（反代目标）是否一致；grep `proxy_pass` `python_<name>.conf`（`/www/server/panel/vhost/nginx/python_<name>.conf`）确认反代指向 `127.0.0.1:{实际端口}`。
   - path→port 反代缺失/指错 → `PythonProjectModify(action='add_proxy', proxy_path='/', proxy_port=实际端口)`（**需已开启外网映射**）。
3. 读 nginx error log（`/www/wwwlogs/<name>.error.log`）进一步定位。
4. 修正后验证。

## 分支 D —— 关联进程异常（celery worker 等）
1. `PythonProjectService(project_name=..., action='list')` 看各服务 pid/ports（主服务 sid='main' 之外为关联进程）。
2. 某服务异常 → `action='log'`（`sid=...`）读服务日志；`action='start'/'stop'/'restart'`（`sid=...`）重拉。
3. 缺 celery → `PythonEnv(action='package', python_bin=..., package_action='install', package_name='celery')`。
4. 修正后 `action='list'` 复检 pid 存在。

## 分支 E —— 依赖问题（环境内包管理）
- `PythonEnv(action='package', python_bin=<虚拟环境>, package_action='list')` 看已装包。
- `package_action='install'`（`package_name` + 可选 `package_version` + 可选 `pip_source`）/ `package_action='uninstall'`（`package_name`）。安装慢，返回 `log_tail`。
- 修完回场景一 Step 5 验证。

---

# 日常运维速查（简单操作，直接按工具描述调用）

| 需求 | 工具 |
|---|---|
| 查看项目列表/状态 | `PythonProjectInfo()`（project_name 留空） |
| 查看单项目详情（prep_status/run/listen/日志路径/服务） | `PythonProjectInfo(project_name=...)` |
| 启动 / 停止 / 重启（含关联进程） | `PythonProjectControl(project_name, action='start'/'stop'/'restart')` |
| 只启动 / 只停止主服务 | `PythonProjectControl(project_name, action='start_main'/'stop_main')` |
| 看应用 / 环境准备 / 服务日志 | `PythonProjectInfo` 返回 `log_files` → filesystem `Read` |
| 改端口/启动方式/入口/用户/环境变量/日志路径 | `PythonProjectModify(action='config', ...)`（重启生效） |
| 加 / 删域名、开 / 关外网映射、path→port 反代 | `PythonProjectModify(action='add_domain'/'remove_domain'/'bind_extranet'/'unbind_extranet'/'add_proxy', ...)` |
| Python 版本检测 / 在线浏览 / 移除 | `PythonVersion(action='list'/'online'/'remove', ...)` |
| **安装 Python 版本（编译慢，后台）** | `PythonVersion` online 取 `install_command` → `Bash(run_in_background=true)` + `BashStatus` 轮询 |
| 虚拟环境列表 / 创建 / 移除 / 设默认 | `PythonEnv(action='list'/'create'/'remove'/'set_default', ...)` |
| 环境内 pip 装 / 卸 / 列表 | `PythonEnv(action='package', python_bin=<env>, package_action='install'/'uninstall'/'list', ...)` |
| 关联进程列表 / 启停 / 日志 / **删除（先停再删）** | `PythonProjectService(project_name, action='list'/'start'/'stop'/'restart'/'log'/'remove', sid=...)` |
| 删除项目（**高风险，先确认**；保留虚拟环境，需删除用 `PythonEnv(action='remove')`） | `PythonProjectDelete(project_name=...)`（保留目录源码） |

> ⚠️ **remove_domain 注意**：面板移除域名会连带停止项目服务（主服务+协同服务，与是否剩最后一个域名无关，已实证、根因待定位）。工具**不自动恢复**（避免掩盖根因）：移除后必须用 `PythonProjectInfo` 复核运行态，被停则手动 `PythonProjectControl(action='start')` 拉起。
> **add_domain 注意**：对已存在的域名面板返回"已存在"=实际已绑定/可访问，工具按逐域结果如实上报（非失败）；只有格式错误等才报错。

---

# 完成汇报模板（部署成功）

返回：项目名 / 运行方式（stype）/ 目录 / 虚拟环境 python_bin / 运行用户 / 监听端口；若绑域名：访问地址 + nginx 配置路径；环境准备状态（prep_status=complete）与启动验证结果（进程/端口/日志）；关联进程清单；遗留隐患提示（依赖未装、requirements 缺失、env 未注入、端口启发不准等）。
