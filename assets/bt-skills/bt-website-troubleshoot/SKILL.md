---
name: bt-website-troubleshoot
description: >
  诊断并修复 bt panel 网站访问异常和服务启动失败问题。
  当用户报告以下问题时使用此技能：网站无法打开、403/404/500/502/503 错误、
  空白页/白屏、数据库连接错误、nginx 或 php-fpm 启动失败、
  服务启动失败但没有明确原因，或任何网站宕机/访问被拒绝问题。
  触发关键词：网站宕机、网站打不开、网站无法访问、502、
  500、403、404、空白页、白屏、nginx 错误、php-fpm 错误、启动失败、
  数据库连接失败、连接被拒绝、连接数过多、访问被拒绝、
  网站不可达、服务不可用、错误网关、网站异常。
---

# bt panel 网站故障排查

> **停止。在执行任何操作前，必须完整阅读本文档。**
> **第一个动作：若当前环境有 todo 工具（`TodoWrite`），先用它创建诊断任务列表**；没有则直接进入诊断。
> 不要跳过任何章节。按顺序执行决策树。
> 永远不要向用户展示原始命令、btpython 路径或代码块 —— 仅使用自然语言报告。

---

## 核心规则

1. **始终先执行预检查** —— 永远不要跳过 `curl --resolve` 本地回环验证。
2. **修复前先读取** —— 在执行任何修复操作前，先诊断根因。
3. **每个任务最多调用 15 次工具** —— 超出后，汇总当前发现并停止。
4. **绝不让用户手动输入命令** —— 始终通过 `RunCommand/Bash` 执行。
5. **修复过程中发生错误时** —— 向用户报告，不要自动重试。
6. **服务报告“启动失败”时，始终检查原始服务日志** —— 面板提示通常过于模糊，无法直接采取行动。
7. **禁止操作**：删除网站、删除数据库、删除文件、`rm -rf`、`DROP TABLE/DATABASE`。
8. **任务跟踪（可选）** —— 若当前环境提供 todo 工具（`TodoWrite`/`TodoRead`），用它跟踪诊断：开始 Step 0 前建任务列表，保持单任务 `in_progress`，完成后标 `completed`，被中断用 `TodoRead` 恢复。没有 todo 工具则跳过，直接按决策树推进。
9. **工具名双写（两个部署环境）** —— 同一个能力在内置宝塔 AI 端和插件对外接口里名字不同：执行命令是 `RunCommand` / `Bash`，精确编辑是 `SearchReplace` / `Edit`。本文档统一写成 `RunCommand/Bash`、`SearchReplace/Edit`，你按当前手头可用的那个调用即可。

---

## Step 0 —— 预检查（强制）

在任何诊断前，确认网站确实属于当前服务器，并且请求能够到达该服务器。

1. **创建任务列表（若可用）**：若当前有 `TodoWrite` 工具，先列出本次案例的步骤（预检查 → 探测 → 状态码分支 → 修复）；没有则跳过本步，直接进入第 2 步。
2. **执行**：`RunCommand/Bash: curl --resolve <domain>:80:127.0.0.1 -sS -o /dev/null -w '%{http_code}\\n' http://<domain>/`
   - 返回实际到达面板 nginx 的 HTTP 状态码。
3. **列出网站**：`SiteList()` → 找到匹配的 `name`（域名，作为 `site_name` 传给 `SiteGetConfig`）、`path`、`project_type`。
4. **如果网站不在当前面板上**（`curl` 返回连接错误或返回了其他网站）：告知用户该域名可能并未托管在此处，不要继续。

> 仅当用户明确确认网站位于当前服务器，或直接提供了 `site_name`（域名）时，才可跳过预检查。

---

## Step 1 —— 双探针

这些探针是只读验证，不产生持久副作用。创建、测试，并在完成后**删除**。

### 探针 A —— 静态文件（验证域名绑定 + nginx + 根目录）

1. `RunCommand/Bash: echo 'bt Panel probe $(date)' > <site_path>/.probe_static.html`
2. `RunCommand/Bash: chown www:www <site_path>/.probe_static.html && chmod 644 <site_path>/.probe_static.html`
3. `RunCommand/Bash: curl --resolve <domain>:80:127.0.0.1 -sS http://<domain>/.probe_static.html`
4. **预期结果**：返回探针文本，HTTP 状态码为 200。
5. 清理：`RunCommand/Bash: rm -f <site_path>/.probe_static.html`

### 探针 B —— PHP 文件（验证 PHP 运行时 + php-fpm socket）

1. `RunCommand/Bash: echo '<?php echo "bt Panel PHP probe ".PHP_VERSION; ?>' > <site_path>/.probe_php.php`
2. `RunCommand/Bash: chown www:www <site_path>/.probe_php.php && chmod 644 <site_path>/.probe_php.php`
3. `RunCommand/Bash: curl --resolve <domain>:80:127.0.0.1 -sS http://<domain>/.probe_php.php`
4. **预期结果**：返回包含 PHP 版本字符串的探针文本。
5. 清理：`RunCommand/Bash: rm -f <site_path>/.probe_php.php`

> 从 `SiteList` 返回的匹配项 `path` 字段获取 `site_path`。`SiteGetConfig(site_name)` 返回的是**原始虚拟主机配置文本**（不是结构化字段）—— 阅读文本中的 `root`、`access_log` 和 `include enable-php-<ver>.conf;` 指令，以验证根目录。

---

## Step 2 —— 状态码决策树

### 403 Forbidden —— 权限 / 所有权

**目标**：确认 `www` 拥有网站目录树，目录权限为 755、文件权限为 644，并且父目录可读。

1. `SiteGetConfig(site_name)` → 获取 `root` 目录。
2. `RunCommand/Bash: ls -la <root>/` 和 `RunCommand/Bash: ls -la <parent_of_root>/`（父目录同样重要）。
3. 检查：
   - root 及所有父目录的所有者/用户组 = `www:www`
   - 目录权限 = `755`
   - 文件权限 = `644`
4. 如果任一项不正确（自动修复，低风险）：
   - `RunCommand/Bash: chown -R www:www <root>`
   - `RunCommand/Bash: find <root> -type d -exec chmod 755 {} \;`
   - `RunCommand/Bash: find <root> -type f -exec chmod 644 {} \;`
5. 使用预检查 curl 重新测试。如果仍然返回 403，检查 nginx 错误日志：
   - `Read: /www/wwwlogs/<domain>.error.log`（最后 50 行，查找 `directory index of "..." is forbidden` 或 `access denied`）。

### 404 Not Found —— 路径 / Rewrite

**先分类**：缺失的 URL 应该由动态路由（PHP 路由/框架路由）提供，还是由静态文件提供？

- **静态 404**（例如 `/favicon.ico`、`/uploads/foo.jpg`）：
  1. `SiteGetConfig(site_name)` → 检查 `root` 和 `access_log` 的位置。
  2. `RunCommand/Bash: ls -la <root>/<expected_path>` → 文件是否缺失？root 是否错误？
  3. 确认虚拟主机配置中的 `root` 指令与 `SiteList` 返回的实际 `site_path` 一致。

- **动态 404**（例如 `/category/news/`、`/article/123`、`/admin/login`）：
  1. `SiteGetConfig(site_name)` → 查找 `include .../rewrite/<domain>.conf;` 行。
  2. `Read: /www/server/panel/vhost/rewrite/<domain>.conf`（如果存在）。
  3. **常见原因**：框架（WordPress / ThinkPHP / Laravel / Typecho 等）的 rewrite 规则缺失或错误。
  4. 修复（高风险 —— 需要面板确认）：根据框架标准规则使用 `SearchReplace/Edit` 编辑 rewrite 文件，然后执行 `RunCommand/Bash: nginx -t && nginx -s reload`。

### 500 Internal Server Error —— 三个分支

运行预检查 curl，确认返回 500。然后依次检查各分支：

#### 分支 A —— 数据库

1. 读取 `SiteGetConfig` 找到项目根目录，然后查找框架数据库配置：
   - WordPress：`Read: <root>/wp-config.php` → 提取 `DB_NAME`、`DB_USER`、`DB_PASSWORD`、`DB_HOST`。
   - 其他框架：查找 `.env`、`config/database.php`、`application/database.php` 等。
2. `RunCommand/Bash: mysql -h<DB_HOST> -u<DB_USER> -p<DB_PASSWORD> <DB_NAME> -e "SELECT VERSION()"` → 连接成功时返回 MySQL 版本号（即连接测试通过）；失败则按下一步读错误码。
3. 如果连接失败，从 `mysql` 客户端的原始错误输出（形如 `ERROR 1045 (28000): ...`）中读取错误码，按下表判断：
   - `2002` / `2003` → MySQL 未运行。进入**服务启动失败 → MySQL**。
   - `1045` → 密码错误。比较配置中的 `DB_PASSWORD` 与 `databases` 表；如果不一致，向用户报告（不要自动重置数据库密码）。
   - `1146` → 数据表缺失。用 `RunCommand/Bash: mysql -h<DB_HOST> -u<DB_USER> -p<DB_PASSWORD> <DB_NAME> -e "SHOW TABLES"` / `DESC <表名>` 确认（凭据取自上一步 wp-config；RunCommand/Bash 为 high，会触发确认），然后报告。
   - `1040` → 连接数过多。执行 `RunCommand/Bash: mysql -h<DB_HOST> -u<DB_USER> -p<DB_PASSWORD> -e "SHOW GLOBAL STATUS LIKE 'Threads_connected'; SHOW FULL PROCESSLIST"`，查看连接数与连接来源；建议提高 `max_connections`（高风险）。

#### 分支 B —— 代码（未捕获异常）

1. 启用 PHP 错误显示（高风险 —— 需要确认，且仅适用于非生产环境）：
   - `Read: /www/server/php/<ver>/etc/php.ini` → 检查 `display_errors` 和 `error_reporting`。
2. `Read: /www/wwwlogs/<domain>.error.log`（最后 100 行）→ 查找 PHP `Fatal error` / `Parse error` / `Uncaught`。
3. 向用户报告文件、行号和错误信息。不要自动修改网站代码。

#### 分支 C —— 配置（HTTP 200 但页面空白）

1. 这是典型的 **fastcgi.conf 损坏**模式：状态码为 200、响应体为空，并且网站此前正常。
2. `Read: /www/server/nginx/conf/fastcgi.conf` → 检查文件是否被清空或被过度注释。
3. 如果异常，向用户报告。修复需要恢复面板默认的 `fastcgi.conf`（高风险 —— 需要确认，并需要原始文件）。

### 502 / 503 Bad Gateway / Service Unavailable —— PHP-FPM 环境

1. `RunCommand/Bash: ps -ef \| grep php-fpm \| grep -v grep` → php-fpm 是否正在运行？
2. `ServiceStatus("php-fpm-<ver>")` → 确认安装和运行状态。从 `SiteGetConfig` 中的 `include enable-php-<ver>.conf;` 行确定版本。
3. `SiteGetConfig(site_name)` → 检查虚拟主机实际包含的 `enable-php-<ver>.conf` 是否与运行中的版本**一致**。
4. `RunCommand/Bash: curl -sS http://127.0.0.1/phpfpm_<ver>_status` → 检查 active processes、listen queue、max children。
   - 如果 `listen queue` 非零 → 进程池已耗尽。参见**服务启动失败 → php-fpm**中的 OOM。
5. `RunCommand/Bash: free -m` → 查看可用内存；如果少于 200MB，OOM killer 可能已终止 php-fpm。
6. 对于**反向代理 502**：从面板主机执行 `RunCommand/Bash: curl -v <upstream_host>` → 检查上游是否可达（防火墙 / DNS / 上游宕机）。

---

## Step 3 —— 服务启动失败

> **核心原则**：当面板显示“启动失败”但没有有效细节时，**始终先读取原始服务日志**。面板提示通常过于模糊，无法直接采取行动。

### 3.1 nginx

```bash
# 1. 语法检查 —— 可给出任何错误的准确文件和行号
/www/server/nginx/sbin/nginx -t
```

三种常见失败模式：

| 现象 | 原因 | 修复 |
|---|---|---|
| `unknown directive "xxx" in /www/server/panel/vhost/nginx/<site>.conf:N` | 网站虚拟主机配置中存在拼写错误或不受支持的指令 | 使用 `Read` 读取对应行，使用 `SearchReplace/Edit` 修复（高风险），然后重新执行 `nginx -t` |
| `bind() to 0.0.0.0:80 failed` / `bind() to [::]:443 failed` | 端口被占用 | `RunCommand/Bash: netstat -tlnp \| grep -E ':80\|:443'` → 找出冲突进程，并向用户报告 |
| `host not found in upstream "<name>"` | 启动时无法解析上游 DNS | 使用 `RunCommand/Bash: dig +short <name>` 验证；如果无法解析，向用户报告。修复：在虚拟主机中添加 `resolver` 指令，或替换为 IP（高风险） |

修复后，**始终**再次执行 `nginx -t`，然后执行 `RunCommand/Bash: /etc/init.d/nginx restart`（或 `ServiceRestart("nginx")`，高风险 —— 需要确认）。

### 3.2 php-fpm

从故障网站引用的 `enable-php-<ver>.conf` 中获取版本，然后执行：

```bash
# 1. 查看原始 php-fpm 错误日志末尾 —— 信息最完整
tail -n 50 /www/server/php/<ver>/var/log/php-fpm.log
```

| 现象 | 原因 | 修复 |
|---|---|---|
| `Unable to load dynamic library '<ext>.so'` / `segfault (core dumped)` | 新安装的 PHP 扩展损坏 | 二分排查：在面板中进入应用商店 → PHP → 设置 → 扩展，逐个卸载最近新增的扩展，每次卸载后重启（`RunCommand/Bash: /etc/init.d/php-fpm-<ver> restart`） |
| 启动后立即显示 `active (exited)` | 被 OOM killer 终止 | `RunCommand/Bash: dmesg \| grep -E "php\|oom" \| tail -20` + `RunCommand/Bash: free -m` → 降低 `/www/server/php/<ver>/etc/php-fpm.conf` 中的 `pm.max_children`（高风险） |
| `bind() to /tmp/php-cgi-<ver>.sock failed: Address already in use` | 旧 php-fpm 进程仍在运行 | `RunCommand/Bash: pkill php-fpm && sleep 2 && /etc/init.d/php-fpm-<ver> start`（高风险） |
| `ERROR: [/www/server/php/<ver>/etc/php-fpm.conf:N] unknown parameter` | 手动编辑导致指令损坏 | 使用 `Read` 读取对应行，修复或通过面板应用商店 → PHP → 设置 → 配置 → 重置（高风险） |
| `Unable to access php-fpm.sock: Permission denied` | Socket 文件所有者错误 | `RunCommand/Bash: ls -la /tmp/php-cgi-<ver>.sock` → 如果不是 `www:www`，执行 `RunCommand/Bash: chown www:www /tmp/php-cgi-<ver>.sock && chown -R www:www /www/server/php/<ver>/var/log/`（低风险） |

---

## Step 4 —— 工具风险等级

工具由其注册的 `risk_level` 控制，而不是由命令本身的行为控制。

| risk_level | 工具 | 典型用途 | 处理方式 |
|---|---|---|---|
| **low** | `Read`、`SiteGetConfig`、`SiteLogs`、`ServiceStatus`、`TodoRead`、`TodoWrite` | 读取配置/日志、检查服务状态、跟踪任务 | 直接执行 |
| **high** | `RunCommand/Bash`、`ServiceRestart`、`SearchReplace/Edit`、`Write` | 任何 shell 命令（包括只读的 `curl`/`ls`/`netstat`/`ps`/`mysql -e`，以及 `chown`/`chmod`）、重启服务、编辑 nginx/php 配置、写入文件、执行 SQL（读/写） | 每次调用都必须经过面板确认门禁 |
| **forbidden** | — | 删除网站、删除数据库、删除文件、`rm -rf`、`DROP TABLE/DATABASE` | 永不执行 |

- `RunCommand/Bash` 作为工具的 `risk_level="high"`，因此即使是**只读探测**（`curl`、`ls`、`netstat`）也会触发确认门禁。应优先使用低风险读取工具（使用 `Read` 读取日志/配置，使用 `ServiceStatus` 检查状态），在无需确认的情况下收集事实。
- 任何配置编辑（`SearchReplace/Edit`/`Write`）完成后，**必须**执行 `nginx -t` 验证，再进行 reload。

---

## Step 5 —— 输出格式

向用户报告发现时，始终使用以下形式的**自然语言**：

```
根因：<用一句话说明根因>

已执行步骤：
- <步骤 1>
- <步骤 2>
...

建议：
- <预防措施或后续操作>
```

规则：

- **绝不**在面向用户的消息中粘贴原始 shell 命令、btpython 路径或配置差异。
- **绝不**要求用户手动输入命令 —— 如果需要修复，描述修复内容并等待用户确认。
- 如果诊断尚不完整（例如无法复现、日志不明确），必须明确说明。不要编造根因。

---

## 快速参考 —— 常见错误码

这些错误由 `mysql_engine.MYSQL_ERROR_MAP` 自动映射；此处映射仅供 Agent 自身推理使用，**不要向用户原样输出错误码**。

| SQLSTATE / 错误码 | 友好含义 | 下一步 |
|---|---|---|
| `2002` / `2003` | 无法连接 MySQL socket / 端口 | 检查 `ServiceStatus("mysql")` |
| `1045` | 数据库用户密码错误 | 比较 `wp-config.php` 与面板 `databases` 表 |
| `1146` | 数据表不存在 | `RunCommand/Bash: mysql -h<DB_HOST> -u<DB_USER> -p<DB_PASSWORD> <DB_NAME> -e "SHOW TABLES"` / `DESC` 确认 |
| `1040` | 连接数过多 | `RunCommand/Bash: mysql -h<DB_HOST> -u<DB_USER> -p<DB_PASSWORD> -e "SHOW GLOBAL STATUS LIKE 'Threads_connected'; SHOW FULL PROCESSLIST"` |
| `1452` | 外键约束失败 | 检查被引用的数据行，并向用户报告 |

---

## 快速参考 —— 文件 / 日志路径

| 内容 | 路径 |
|---|---|
| Nginx 虚拟主机配置 | `/www/server/panel/vhost/nginx/<domain>.conf` |
| Apache 虚拟主机配置 | `/www/server/panel/vhost/apache/<domain>.conf` |
| Rewrite 规则 | `/www/server/panel/vhost/rewrite/<domain>.conf` |
| Nginx 主配置 | `/www/server/nginx/conf/nginx.conf` |
| Nginx fastcgi 配置（空白页常见原因） | `/www/server/nginx/conf/fastcgi.conf` |
| 网站访问日志 | `/www/wwwlogs/<domain>.log` |
| 网站错误日志 | `/www/wwwlogs/<domain>.error.log` |
| PHP-FPM 错误日志 | `/www/server/php/<ver>/var/log/php-fpm.log` |
| PHP-FPM socket | `/tmp/php-cgi-<ver>.sock` |
| PHP-FPM 进程池配置 | `/www/server/php/<ver>/etc/php-fpm.conf` |
| WordPress 数据库配置 | `<site_root>/wp-config.php` |
