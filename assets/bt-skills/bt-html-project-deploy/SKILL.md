---
name: bt-html-project-deploy
description: >
  在宝塔面板上管理 Html(静态)项目：创建静态站点（域名 + 网站根目录）、把前端构建产物部署到站点目录、
  编辑伪静态 rewrite 配置（SPA try_files / 自定义 location / 缓存）、改域名/网站根目录/运行目录/启停，
  并在静态站点访问异常（404 / SPA 刷新 404 / 伪静态不生效 / 目录权限）时排错。
  当用户要求把前端静态页面（HTML/SPA/单页应用）挂到域名上，或静态站点访问异常需要排查时使用。
  触发关键词：静态网站、HTML项目、部署前端、SPA、单页应用、伪静态、rewrite、运行目录、静态站 404、
  SPA 404、BT-Html-Project-Deploy。
  日常的查看/启停/改备注等简单操作不依赖本 SOP，直接按工具描述调用即可。
---

# Html(静态)项目运维 SOP

> **停止。执行任何操作前，必须完整阅读本文档。**
> 本 Skill 的工具均指 bt_agent_mcp 插件暴露的 MCP 工具；同一能力在宝塔 AI 内置端可能有不同命名，按当前环境可用工具调用。
> 本 SOP 覆盖三个主场景：**① 创建静态项目；② 配置编辑（伪静态 rewrite / 主 conf）；③ 静态站点访问异常排错**。其他简单操作（状态查看、启停、改备注、绑删域名、改目录、运行目录、删除）不做 SOP，直接使用工具。

---

## 核心规则

1. **先只读侦察，再执行变更** —— 操作前先 `HtmlProjectInfo`（site_name 留空）列项目找到站点名（可能带 `_<端口>` 后缀），再 `HtmlProjectInfo(site_name=...)` 看当前域名/路径/运行目录/SSL；排错先读日志，不盲目重写配置。
2. **静态站点本质 = 网站根目录 + nginx/apache conf + rewrite 文件** —— nginx 主 conf 在 `/www/server/panel/vhost/nginx/html_<name>.conf`（模板渲染产物），**伪静态 rewrite 文件在 `/www/server/panel/vhost/rewrite/html_<name>.conf`（面板官方自定义配置入口，被主 conf include）**。
3. **改配置优先写 rewrite 文件** —— SPA `try_files`、自定义 `location`、静态资源缓存等写 rewrite 文件（面板创建的注释即引导"请将伪静态规则或自定义NGINX配置填写到此处"）；**只有确实要改 listen/root/自定义 server 段才动主 conf，且改前必须 filesystem `Read` 留基线**（面板 SSL/域名/改目录操作会重写覆盖主 conf）。
4. **域名/路径/启停/运行目录走 `HtmlProjectModify`** —— 面板方法同步 domain 表与 nginx/apache server_name；**不要用 filesystem 直接改主 conf 来加域名**，会与面板不同步。
5. **创建即生效** —— `HtmlProjectCreate` 成功即写 nginx/apache 配置 + 建目录（目录不存在自动创建）+ 非 80 端口放行防火墙 + 重载服务；返回的 `site_name_hint` 仅供参考，**实际站点名以 `HtmlProjectInfo` 列表返回的 name 为准**（主域名重名会带 `_<端口>`）。
6. **每个任务最多调用 15 次工具**，超出后汇总当前发现并停止。
7. **禁止操作**：`rm -rf` 站点根目录外的路径、修改宝塔/插件自身文件、读取插件 `data/` 凭据、直接写 nginx 主 conf 来改域名（走 Modify）。

---

# 场景一：创建静态项目

## Step 0 —— 预检
1. 确认任务确为"创建 Html(静态)项目"。
2. 拿到**要对外暴露的域名**（可带 `:端口`，非 80 端口会成为监听端口）与**网站根目录**（绝对路径，目录不存在会自动创建；也可指向已有前端目录）。
3. 确认 Nginx/Apache 已安装（静态站依赖 web 服务）。

## Step 1 —— 调用创建
`HtmlProjectCreate(domains=[...], path=...)`：
- **必填**：`domains`（list，首项为主域名，如 `'example.com'` 或 `'example.com:8080'`）、`path`（网站根目录绝对路径，如 `/www/wwwroot/demo.example.com`）。
- **可选**：`ps`（备注）、`type_id`（项目分类，默认 0）。

> 返回"创建成功"= 已写 nginx/apache 配置 + 建目录 + 放行端口 + 重载。`site_name_hint` 仅供参考。

## Step 2 —— 部署静态文件
1. 把前端构建产物（如 `dist/` 下文件）上传到站点根目录 `path`：
   - 文件已在本机：用文件上传（PrepareUpload 分块上传）到站点目录，或用 filesystem 移动。
   - 远端构建：先下载到本机再上传，或直接把站点 `path` 指到已有构建目录。
2. 确认 `index.html` 已在根目录（或运行目录，见场景二 set_run_path）。

## Step 3 —— 验证（强制）
1. `HtmlProjectInfo`（site_name 留空）确认站点出现，记下真实 `name`。
2. `HtmlProjectInfo(site_name=...)` 看域名/路径/SSL。
3. 访问域名验证首页正常返回。

- 全通过 → 按"完成汇报"收尾。
- 访问异常 → 转场景三排错。

---

# 场景二：配置编辑（伪静态 rewrite / 主 conf）

## Step 0 —— 拿基线与现状
1. `HtmlProjectInfo(site_name=...)`：拿到 `rewrite_file`（伪静态/自定义入口）、`config_file`（nginx 主 conf）、`apache_config_file` 路径，以及当前域名/路径/运行目录。
2. filesystem `Read` `rewrite_file` 与 `config_file` 看当前配置。

## Step 1 —— 改配置（优先 rewrite 文件）
按「常用静态站点 nginx 配置速查」（见文末）在 **rewrite 文件**里加/改规则。常见操作：
- **SPA 路由重写**（刷新子路由 404）：`location / { try_files $uri $uri/ /index.html; }`。
- **自定义 location**：如 `location /api { proxy_pass http://127.0.0.1:9000; ... }`（把某路径转发到后端）。
- **静态资源缓存**：`location ~* \.(js|css|png|jpg|svg|woff2)$ { expires 30d; add_header Cache-Control "public, max-age=2592000"; }`。
- **开启 gzip**：`gzip on; gzip_types text/css application/javascript image/svg+xml;`。

> 只有确实要改 `listen` / `root` / `server_name` 之外的 server 层配置才动**主 conf**：filesystem `Read` `config_file` 留基线 → 改 → filesystem `Write` 回写。**改主 conf 前必须 Read**，写坏可恢复。

## Step 2 —— 回传并验证
1. filesystem `Write` 回写修改后的文件（rewrite 或主 conf）。
2. `Bash` 执行 `nginx -t` 确认配置语法通过；失败按报错行修文件重写。
3. `Bash` `nginx -s reload`（如有需要）让新配置生效。
4. 访问验证（如有域名）：确认新规则生效、旧规则仍在。

- 配置写坏导致站点异常 → 用 Read 留的基线恢复重写；主 conf 被面板覆盖 → 用 `HtmlProjectModify(action='change_path'/'set_run_path')` 走面板。

## Step 3 —— 面板操作走 Modify（域名/路径/启停/运行目录）
| 需求 | 调用 |
|---|---|
| 加域名 | `HtmlProjectModify(site_name, action='add_domain', domains=['www.example.com'])` |
| 删域名 | `HtmlProjectModify(site_name, action='remove_domain', domain='www.example.com')` |
| 启/停/重启 | `HtmlProjectModify(site_name, action='start'/'stop'/'restart')` |
| 改网站根目录 | `HtmlProjectModify(site_name, action='change_path', path='/www/wwwroot/new')`（**目标目录必须已存在**） |
| 设运行目录（子目录） | `HtmlProjectModify(site_name, action='set_run_path', run_path='/dist')` |

---

# 场景三：静态站点访问异常排错

## Step 0 —— 只读侦察（不盲改）
1. `HtmlProjectInfo` 确认项目存在、域名/路径/运行目录现状。
2. `Bash` 读 nginx 错误日志 `/www/wwwlogs/<name>.error.log` 与访问日志 `/www/wwwlogs/<name>.log` 尾部。

## Step 1 —— 按症状对号入座

| 症状 | 常见根因 | 处置 |
|---|---|---|
| **首页 404 / 空白** | 前端文件没传到根目录、`index.html` 缺失、运行目录不对 | 确认文件在站点根目录（或运行目录）；`HtmlProjectModify(action='set_run_path', run_path=...)` 指到实际构建目录 |
| **子路由刷新 404（SPA）** | 没配 `try_files` 回退 index.html | 场景二在 rewrite 文件加 `location / { try_files $uri $uri/ /index.html; }` |
| **伪静态不生效** | rewrite 文件没写对/没 include、nginx 没重载 | `nginx -t` + `nginx -s reload`；确认 rewrite 文件语法 |
| **静态资源 404 / 403** | 目录权限不对、资源在子目录但 root 指错 | `Bash` `ls -la` 站点目录、`chown -R www:www` 站点目录 |
| **只对本机/内网生效** | 域名未绑定、非 80 端口防火墙未放行 | `HtmlProjectModify(action='add_domain')` 补域名；`Bash` 查防火墙端口放行状态 |
| **HTTPS 不生效** | 证书未部署（MCP 不封装 SSL） | 证书部署走面板，MCP 只读 ssl 状态 |

## Step 2 —— 修复与验证
1. 按上表定位根因，**改配置文件必须 filesystem Read 基线 → 改 → Write → `nginx -t`**，改域名/路径走 `HtmlProjectModify`。
2. 修复后重访验证；仍异常则回到 Step 0 换角度（读实时日志尾部 `tail -f`）。

---

# 运维速查

| 需求 | 调用 |
|---|---|
| 列表/找站点名 | `HtmlProjectInfo(search=..., page=...)`（site_name 留空） |
| 查看详情/域名/路径/conf 路径 | `HtmlProjectInfo(site_name=...)` |
| 创建静态项目 | `HtmlProjectCreate(domains=[...], path=...)` |
| 读/改伪静态（优先） | filesystem `Read`/`Write` `rewrite_file`（`/www/server/panel/vhost/rewrite/html_<name>.conf`） |
| 读/改 nginx 主 conf | filesystem `Read` 留基线 → 改 → `Write` `config_file`（`/www/server/panel/vhost/nginx/html_<name>.conf`） |
| 验证语法 | `Bash` `nginx -t` |
| 加删域名 / 启停 / 改目录 / 运行目录 | `HtmlProjectModify(site_name=..., action=..., ...)` |
| 删除项目 | `HtmlProjectDelete(site_name=...)`（高风险，确认后；不删站点目录，需删目录用文件系统工具） |

---

# 常用静态站点 nginx 配置格式与位置速查

**位置**：
- **rewrite 文件**（`/www/server/panel/vhost/rewrite/html_<name>.conf`）：被 nginx 主 conf include 在 server 块内，**伪静态/自定义 location/缓存优先写这里**。
- **nginx 主 conf**（`/www/server/panel/vhost/nginx/html_<name>.conf`）：完整 server 块（listen/server_name/root/ssl/日志/include），模板渲染产物。

**典型片段**（写进 rewrite 文件即可）：

```nginx
# SPA 单页应用：子路由刷新回退到 index.html（最常用）
location / {
    try_files $uri $uri/ /index.html;
}

# 静态资源缓存
location ~* \.(js|css|png|jpg|jpeg|gif|svg|woff2|ico)$ {
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
}

# 自定义 location：把某路径转发到后端
location /api {
    proxy_pass http://127.0.0.1:9000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# 开启 gzip 压缩（server 层，放 rewrite 文件顶部即可）
gzip on;
gzip_types text/plain text/css application/javascript application/json image/svg+xml;
```

**规则**：
- `location / { try_files $uri $uri/ /index.html; }` 是 SPA（Vue/React 等 history 路由）部署后**必配**的伪静态规则，否则刷新子路由 404。
- 伪静态/缓存/自定义 location 一律写 rewrite 文件，**不改主 conf**；只有要动 listen/root/自定义 server 段才碰主 conf，且先 `Read` 留基线。
- 改完**必须** `nginx -t` 验证，再确认访问生效。
- 涉及域名/路径/运行目录的变更走 `HtmlProjectModify`，不要手改主 conf。

---

# 完成汇报模板

汇报固定四段（每段 1-3 行，用一次工具查证一个结论，不堆 log）：

- **现状**：静态项目 `<name>`，域名 `<域名:端口>`，网站根目录 `<path>`，状态（运行中/已停止）。
- **变更**：`<创建了静态项目 / 部署了前端文件到 <path> / 添加了 SPA try_files 伪静态 / 修改了网站根目录 / 启停了项目 / 绑定了域名>`。
- **验证**：`nginx -t` 通过 / `HtmlProjectInfo` 复查域名与路径 / 访问 `<域名>` 返回预期。
- **遗留**：`<若有：SSL 证书未部署需面板处理 / 后端服务未监听需确认>；否则无`。
