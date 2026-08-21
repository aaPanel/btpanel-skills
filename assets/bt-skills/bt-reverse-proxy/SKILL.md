---
name: bt-reverse-proxy
description: >
  在宝塔面板上管理反向代理项目：创建反代站点（域名 + 目标上游）、查看/增删改 URL 级转发规则、
  自由编辑 nginx 反代配置、改备注/启停/绑删域名/强制 HTTPS，并在反代访问异常（502/404/转发不生效）时排错。
  当用户要求把某个域名/路径转发到后端服务（HTTP/HTTPS 或 unix socket），或反代站点访问异常需要排查时使用。
  触发关键词：反向代理、反代、代理转发、proxy_pass、location 转发、域名转发到端口、nginx 反代配置、
  反代 502、反代 404、转发不生效、BT-Reverse-Proxy。
  日常的查看/启停/改备注等简单操作不依赖本 SOP，直接按工具描述调用即可。
---

# 反向代理项目运维 SOP

> **停止。执行任何操作前，必须完整阅读本文档。**
> 本 Skill 的工具均指 bt_agent_mcp 插件暴露的 MCP 工具；同一能力在宝塔 AI 内置端可能有不同命名，按当前环境可用工具调用。
> 本 SOP 覆盖三个主场景：**① 创建反代项目；② 编辑/增删 URL 转发规则（自由配置）；③ 反代访问异常排错**。其他简单操作（状态查看、启停、改备注、绑删域名、强制 HTTPS、删除）不做 SOP，直接使用工具。

---

## 核心规则

1. **先只读侦察，再执行变更** —— 操作前先 `ProxyProjectInfo`（site_name 留空）列项目找到站点名（可能带 `_<端口>` 后缀），再 `ProxyProjectInfo(site_name=...)` 看当前规则/域名/端口/SSL；排错先读日志，不盲目重写配置。
2. **反代项目 = sites 行 + 反代 JSON** —— 真正的配置在 `/www/server/proxy_project/sites/<name>/<name>.json`（`proxy_info[]` 多条 URL 规则）；nginx conf 由它渲染。**改配置必须走 MCP 工具**（ProxyWriteConfig），保持 JSON 与 nginx 同步。
3. **URL 规则增删改走自由配置** —— 不要期待 add/set/del_url_proxy 之类的工具（未提供）。改规则 = 读 conf → 改 location 块 → `ProxyWriteConfig` 回传完整 conf → `Bash` `nginx -t` 验证。**面板保存后会自动把 proxy_info/域名/端口同步回反代 JSON。**
4. **改配置三步走**：`ProxyProjectInfo` 拿 `config_file` 路径 → filesystem `Read` 读当前 conf 作基线 → 修改后 `ProxyWriteConfig(conf_data=<完整 conf>)` → `Bash` 执行 `nginx -t` 验证。**改前必须 Read 留基线**，写坏可恢复。
5. **域名增删走 `ProxyProjectModify`** —— 用 comMod 的方法（会同步反代 JSON）；**不要用通用网站域名工具**（不更新反代 JSON，面板会不同步）。至少保留一个域名。
6. **创建即生效** —— `ProxyProjectCreate` 成功即写 nginx + 放行防火墙 + 重载服务；返回的 `site_name_hint` 是主域名小写形式，**实际站点名以 `ProxyProjectInfo` 列表返回的 name 为准**（非 80 端口会带 `_<端口>`）。
7. **每个任务最多调用 15 次工具**，超出后汇总当前发现并停止。
8. **禁止操作**：`rm -rf` 反代站点根目录外的路径、修改宝塔/插件自身文件、读取插件 `data/` 凭据、直接用 filesystem Write 覆盖反代 nginx conf（必须走 ProxyWriteConfig 保持 JSON 同步）。
9. **反代目标勿指向 bt_agent_mcp 自身端口**（`127.0.0.1:<MCP端口>`，默认 8765）——会把 MCP 服务暴露给该反代域名，且反代 conf 未设 `X-Real-IP` 时来源 IP 白名单会被绕过（仅剩 API Key 鉴权兜底）。**若工具返回 `data.warning` 说明代理目标指向 MCP 自身，须与用户确认意图**；确需经反代暴露 MCP，则在该 location 补 `proxy_set_header X-Real-IP $remote_addr;` 并把真实客户端 IP 加入白名单（`security.ip_allowlist`）。

---

# 场景一：创建反代项目

## Step 0 —— 预检
1. 确认任务确为"创建反向代理项目"。
2. 拿到**要对外暴露的域名**（可带 `:端口`，非 80 端口会成为监听端口）与**目标上游**（http/https URL 或 unix socket 路径）。
3. 确认 Nginx 已安装（反代只支持 nginx）。

## Step 1 —— 调用创建
`ProxyProjectCreate(domains=[...], proxy_pass=...)`：
- **必填**：`domains`（list，`'example.com'` 或 `'example.com:8080'`）、`proxy_pass`（`http://127.0.0.1:8080`、`https://api.example.com`，或 unix 时 `/tmp/app.sock`）。
- **可选**：`proxy_path`（默认 `/`，前缀）、`proxy_host`（默认 `$http_host`，转发 Host）、`proxy_type`（http/unix，默认 http）、`remark`。

> 返回"添加成功"= 已写 nginx conf + 放行端口 + 重载。`site_name_hint` 仅供参考。

## Step 2 —— 验证（强制）
1. `ProxyProjectInfo`（site_name 留空）确认站点出现，记下真实 `name`。
2. `ProxyProjectInfo(site_name=...)` 看 `config`（域名/端口/首条 proxy_info 的 proxy_pass 是否对上）。
3. 需要的话 filesystem `Read` conf 确认 `location { proxy_pass ... }` 已渲染。

- 全通过 → 按"完成汇报"收尾。
- 配置与预期不符 → 转场景二修正配置，或转场景三排错。

---

# 场景二：编辑 / 增删 URL 转发规则（自由配置）

## Step 0 —— 拿基线与现状
1. `ProxyProjectInfo(site_name=...)`：拿到 `config_file` 路径（`/www/server/panel/vhost/nginx/<name>.conf`）、当前 `proxy_info`（每条 proxy_path/proxy_pass/proxy_host/websocket/超时）、域名与端口。
2. filesystem `Read` `config_file` 读当前完整 conf。

## Step 1 —— 修改 conf
按「常用 nginx 反代配置速查」（见文末）在 conf 里**增/删/改 location 块**（或 server/http 层配置）。常见操作：
- **加一条转发规则**：新增 `location /api { proxy_pass http://127.0.0.1:9000; proxy_set_header Host $host; proxy_set_header X-Real-IP $remote_addr; }`。
- **改目标**：改对应 `location` 里的 `proxy_pass`（换后端端口/地址）。
- **删规则**：删掉对应 `location` 块。
- **改超时**：在 location 内加 `proxy_connect_timeout 60s; proxy_read_timeout 600s; proxy_send_timeout 600s;`。
- **开 WebSocket**：加 `proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade; proxy_set_header Connection "upgrade";`（反代 JSON 的 websocket 默认支持）。
- **强制 HTTPS**：优先用 `ProxyProjectModify(action='force_https', force_https=true)`，不要手改 ssl 块。

> 注意：**location 的 proxy_pass 末尾不带 `;` 前不可跟变量**（`proxy_pass http://127.0.0.1:9000;` 可直接跟 URI 或不带 URI；用变量时必须 `resolver`）。简单场景直接写死目标即可。

## Step 2 —— 回传并验证
1. `ProxyWriteConfig(site_name=..., conf_data=<修改后的完整 conf>)` → 面板写 conf 并自动同步反代 JSON。
2. `Bash` 执行 `nginx -t` 确认配置语法通过；失败按报错行修 conf 重存。
3. `ProxyProjectInfo` 复查 `proxy_info` 已同步新规则。
4. 访问验证（如有域名）：确认新规则生效、旧规则仍在。

- 配置写坏导致站点异常 → 用 Read 留的基线恢复后 `ProxyWriteConfig` 重存，或面板历史版本回滚。

---

# 场景三：反代访问异常排错

## Step 0 —— 只读侦察（不盲改）
1. `ProxyProjectInfo` 确认项目存在、域名/端口/规则现状。
2. filesystem `Read` nginx 错误日志 `/www/wwwlogs/<name>.error.log` 与访问日志 `/www/wwwlogs/<name>.log`；必要时 `ProxyWriteConfig` 不变，仅 Read conf 检查 proxy_pass/upstream。

## Step 1 —— 按症状对号入座

| 症状 | 常见根因 | 处置 |
|---|---|---|
| **502 Bad Gateway** | 后端未启动/端口错、proxy_pass 写错、unix socket 不存在、超时太短 | 确认后端进程在监听（`Bash` `ss -tlnp \| grep <port>`）；核对 `ProxyProjectInfo` 的 proxy_pass 与真实后端；unix 路径检查文件存在；长请求调大 `proxy_read_timeout` |
| **404** | proxy_path 前缀与后端路由不匹配、location 前缀未命中、误写 `try_files` | 核对 location 的 `proxy_pass` 是否带 URI 前缀；检查 conf 是否有多余 location 拦截 |
| **转发不生效 / 仍是静态页** | conf 没保存成功、location 与现有规则冲突、缓存 | `nginx -t` + `ProxyProjectInfo` 看 JSON 是否同步；必要时 `Bash` `nginx -s reload` 后重试；缓存类规则先关 `proxy_cache` |
| **只对本机/内网生效** | 域名未绑定外网、防火墙未放行端口 | `ProxyProjectModify(action='add_domain')` 补域名；`Bash` 查防火墙端口放行状态 |
| **HTTPS 不强制 / 证书异常** | SSL 未部署、force_https 未开 | `ProxyProjectModify(action='force_https', force_https=true)`；证书部署走面板 |

## Step 2 —— 修复与验证
1. 按上表定位根因，**改 conf 必须走 ProxyWriteConfig + `nginx -t`**，改域名走 `ProxyProjectModify`。
2. 修复后重访验证；仍异常则回到 Step 0 换角度（读实时日志尾部 `tail`）。

---

# 运维速查

| 需求 | 调用 |
|---|---|
| 列表/找站点名 | `ProxyProjectInfo(search=..., page=...)`（site_name 留空） |
| 查看详情/规则/conf 路径 | `ProxyProjectInfo(site_name=...)` |
| 创建反代 | `ProxyProjectCreate(domains=[...], proxy_pass=...)` |
| 读/改 nginx conf | filesystem `Read` + `ProxyWriteConfig(site_name=..., conf_data=...)` |
| 验证语法 | `Bash` `nginx -t` |
| 改备注 / 启停 / 绑删域名 / 强制 HTTPS | `ProxyProjectModify(site_name=..., action=..., ...)` |
| 删除项目 | `ProxyProjectDelete(site_name=..., remove_path=false)`（高风险，确认后） |

---

# 常用 nginx 反代配置格式与位置速查

**位置**：反代项目的 nginx conf（`/www/server/panel/vhost/nginx/<name>.conf`）是完整 server 块。三块区域：
- **http 层**（`server {` 之前）：upstream 定义、`proxy_cache_path`。
- **server 层**（`server { ... }` 内、location 外）：`listen`、`server_name`、ssl 证书、`proxy_set_header`、`client_max_body_size`。
- **location 层**：每一条 `location <path> { ... }` 是一条 URL 转发规则，对应反代 JSON 的 `proxy_info[]`。

**典型片段**：

```nginx
# location 转发（最常用）：/ 全站转发
location / {
    proxy_pass http://127.0.0.1:8080;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}

# 按路径前缀转发：/api 到另一后端
location /api {
    proxy_pass http://127.0.0.1:9000;
    proxy_set_header Host $host;
}

# 带自定义超时 + WebSocket
location /ws {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_connect_timeout 60s;
    proxy_read_timeout 600s;
    proxy_send_timeout 600s;
}

# server 层常用：限制上传大小、传递真实协议
client_max_body_size 50m;
proxy_set_header X-Forwarded-Proto $scheme;
```

**规则**：
- `proxy_pass` 后**直接写死目标**（`http://IP:端口` 或 `https://域名`）最简单；若需在 URL 中带变量，必须配 `resolver`（一般不需要）。
- **勿把 `proxy_pass` 指向本机 bt_agent_mcp 自身端口**（默认 8765）；若工具返回 `data.warning` 提示目标指向 MCP 自身，先与用户确认，确需暴露则在 location 补 `proxy_set_header X-Real-IP $remote_addr;` 并把真实客户端 IP 加入白名单。
- 改完**必须** `nginx -t` 验证，再确认访问生效。
- 涉及 SSL/强制 HTTPS 用 `ProxyProjectModify(action='force_https')`，别手改 ssl 块。

---

# 完成汇报模板

汇报固定四段（每段 1-3 行，用一次工具查证一个结论，不堆 log）：

- **现状**：反代项目 `<name>`，域名 `<域名:端口>`，转发目标 `<proxy_pass>`，状态（运行中/已停止）。
- **变更**：`<创建了反代项目 / 新增了 /api 转发规则 / 修改了 proxy_pass / 启停了项目 / 设置了强制 HTTPS>`。
- **验证**：`nginx -t` 通过 / `ProxyProjectInfo` 复查 proxy_info 已同步 / 访问 `<域名>` 返回预期。
- **遗留**：`<若有：SSL 证书未部署需面板处理 / 后端服务未监听需确认>；否则无`。
