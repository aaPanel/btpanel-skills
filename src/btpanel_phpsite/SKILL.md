---
name: btpanel_phpsite
description: 宝塔面板 PHP 网站管理技能，提供站点创建、删除、启停、PHP 版本切换、域名管理、SSL 证书管理、伪静态管理、数据库管理等功能
user-invocable: true
disable-model-invocation: false
icon: icon/bt.png
metadata:
  openclaw:
    requires:
      bins:
        - python3
    keywords:
      - 宝塔面板
      - BT-Panel
      - PHP 网站
      - 站点管理
      - 域名管理
      - SSL 证书
      - 数据库管理
      - 伪静态
---

# 宝塔面板 PHP 网站管理

宝塔面板 PHP 网站管理技能，提供完整的 PHP 网站生命周期管理功能，包括站点创建、删除、启停、PHP 版本切换、域名管理、SSL 证书管理、伪静态规则配置、数据库管理等。

![宝塔面板](icon/bt-logo.svg)

## 图标资源

技能包提供以下图标文件，可在生成报告时引用：

| 文件 | 格式 | 用途 |
|------|------|------|
| `icon/bt-logo.svg` | SVG | 矢量图标，适合缩放 |

## AI 使用约束

本技能用于管理和修改服务器上的 PHP 网站，AI 应遵循以下原则：

1. **操作前确认**：删除、停用网站等操作前必须向用户确认
2. **执行前告知**：网站管理会影响线上服务，AI 应先向用户简述即将执行的操作步骤
3. **数据安全**：删除网站时提醒用户备份数据和数据库
4. **隐私保护**：不主动泄露敏感信息（如数据库密码、SSL 私钥等）
5. **影响评估**：修改 PHP 版本、SSL 证书等操作前，告知用户可能的影响

**执行流程示例**：
```
AI: 我将为您执行以下操作：
    1. 创建新站点 example.com
    2. 设置 PHP 版本为 8.2
    3. 创建关联数据库
    正在获取数据，请稍候...
    [执行命令]
    [展示结果和站点信息]
```

## 宝塔面板相关技能矩阵

当前宝塔面板技能包，共包含 3 个相互关联的技能：

| 技能名称                | 描述 | 依赖关系                              |
|---------------------|------|-----------------------------------|
| **btpanel**         | 运维监控技能 | ✅ 基础技能，主要用于资源监控、网站状态检查、服务状态检查等    |
| **btpanel-files**   | 文件管理技能 | ✅ 提供远程服务器文件辅助服务，可以读取文件列表和内容       |
| **btpanel-phpsite** | PHP 网站管理技能 | ✅ 提供远程服务器 PHP 网站管理功能，能够部署和管理php网站 |

### ⚠️ 常见问题

```

**问题 1: 配置文件不存在**
```
错误：未找到配置文件
解决：运行 python3 bt-config.py add 添加服务器配置
```

**问题 2: WordPress 部署失败**
```
错误：无法下载或解压文件
解决：确保 btpanel-files 技能已安装，提供文件操作能力
```

**问题 3: PYTHONPATH 未设置**
```bash
# 运行脚本前需要设置
export PYTHONPATH=/path/to/btpanel-skills/src:$PYTHONPATH
```

### 检查命令

```bash
# 检查 bt_common 模块
python3 -c "from bt_common.bt_client import BtClient; print('✅ 模块正常')"

# 检查配置文件
ls -la ~/.openclaw/bt-skills.yaml

# 测试站点管理
python3 {baseDir}/scripts/site.py list --server "你的服务器名"

# 测试文件管理（WordPress 部署需要）
python3 {baseDir}/../btpanel_files/scripts/download.py --help
```

### 完整安装验证

```bash
# 1. 检查所有技能目录
ls -la /path/to/btpanel-skills/src/
# 应包含：btpanel/ btpanel_files/ btpanel_phpsite/ bt_common/

# 2. 检查配置文件
cat ~/.openclaw/bt-skills.yaml

# 3. 测试完整流程（WordPress 部署）
python3 {baseDir}/scripts/site.py add -n "test.com:8080" --create-db --server "你的服务器名"
python3 {baseDir}/../btpanel_files/scripts/download.py --url "https://example.com/file.zip" --path "/tmp" --server "你的服务器名"
```

---

## 服务器配置管理

> **重要:** 没有服务器信息时需要先添加

本技能复用 `btpanel` 技能的配置系统，使用 `bt-config.py` 工具管理服务器：

```bash
# 查看帮助
python3 {baseDir}/scripts/bt-config.py -h

# 添加服务器
python3 {baseDir}/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN

# 列出服务器
python3 {baseDir}/scripts/bt-config.py list

# 删除服务器
python3 {baseDir}/scripts/bt-config.py remove prod-01
```

**获取 API Token 的方法**：
1. 登录宝塔面板
2. 进入「面板设置」->「API 接口」
3. 点击「获取 API Token」

**重要提示 - SSL 证书验证配置**：
添加服务器时，AI 应询问用户：
> "您的宝塔面板是否使用了受信任的 SSL 证书（如 Let's Encrypt、商业 CA 证书）？"

- ✅ **是**（受信任证书）→ 使用默认配置，无需额外参数
- ⚠️ **否**（自签名证书）→ 添加 `--verify-ssl false` 参数

**示例**：
```bash
# 自签名证书场景
python3 {baseDir}/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN --verify-ssl false

# 受信任证书场景（默认）
python3 {baseDir}/scripts/bt-config.py add -n prod-01 -H https://panel.example.com:8888 -t YOUR_TOKEN
```

## 常用场景

### 场景一：创建新 PHP 网站

当用户需要创建新的 PHP 网站时：

```bash
# 创建基础 PHP 站点
python3 {baseDir}/scripts/site.py add -n example.com -p /www/wwwroot/example.com -v 82

# 创建站点并关联数据库
python3 {baseDir}/scripts/site.py add -n example.com -v 82 --create-db --db-user example_user --db-password "SecurePass123"

# 创建站点并同时创建 FTP
python3 {baseDir}/scripts/site.py add -n example.com -v 82 --create-ftp --ftp-user ftpuser --ftp-password "FtpPass123"
```

**用户意图识别**：
- "帮我创建一个新网站" → 执行 `site.py add`
- "新建一个 PHP 站点" → 执行 `site.py add`
- "创建网站并配数据库" → 执行 `site.py add --create-db`

### 场景二：查看网站列表和状态

当用户需要查看网站列表或状态时：

```bash
# 查看所有站点
python3 {baseDir}/scripts/site.py list

# 查看站点详情
python3 {baseDir}/scripts/site.py info -n example.com

# 查看已安装的 PHP 版本
python3 {baseDir}/scripts/php.py versions

# 查看站点的 PHP 版本
python3 {baseDir}/scripts/php.py get -n example.com
```

**用户意图识别**：
- "看看有哪些网站" → 执行 `site.py list`
- "查看网站状态" → 执行 `site.py list` 或 `site.py info`
- "支持哪些 PHP 版本" → 执行 `php.py versions`

### 场景三：切换 PHP 版本

当用户需要修改站点的 PHP 版本时：

```bash
# 切换站点 PHP 版本
python3 {baseDir}/scripts/php.py set -n example.com -v 82

# 切换为纯静态站点
python3 {baseDir}/scripts/php.py set -n example.com --static
```

**用户意图识别**：
- "把这个站点的 PHP 版本升级到 8.2" → 执行 `php.py set -v 82`
- "切换到 PHP 7.4" → 执行 `php.py set -v 74`
- "改为静态站点" → 执行 `php.py set --static`

### 场景四：停用/启用网站

当用户需要临时停用或启用网站时：

```bash
# 停用网站
python3 {baseDir}/scripts/site.py stop -n example.com

# 启用网站
python3 {baseDir}/scripts/site.py start -n example.com
```

**用户意图识别**：
- "暂时关闭这个网站" → 执行 `site.py stop`
- "启用停用的站点" → 执行 `site.py start`
- "把这个站先停了" → 执行 `site.py stop`

### 场景五：删除网站

当用户需要删除网站时：

```bash
# 删除网站（保留文件和数据库）
python3 {baseDir}/scripts/site.py delete -n example.com

# 删除网站并删除文件目录
python3 {baseDir}/scripts/site.py delete -n example.com --delete-path

# 删除网站并删除关联数据库
python3 {baseDir}/scripts/site.py delete -n example.com --delete-db

# 完全删除（网站 + 文件 + 数据库+FTP）
python3 {baseDir}/scripts/site.py delete -n example.com --delete-path --delete-db --delete-ftp
```

**用户意图识别**：
- "删除这个网站" → 确认后执行 `site.py delete`
- "彻底删除网站和所有数据" → 确认后执行 `site.py delete --delete-path --delete-db`

**重要**：删除操作不可逆，必须先向用户确认并提醒备份。

### 场景六：管理域名绑定

当用户需要添加或删除绑定域名时：

```bash
# 查看站点域名列表
python3 {baseDir}/scripts/domain.py list -n example.com

# 添加域名
python3 {baseDir}/scripts/domain.py add -n example.com -d www.example.com

# 添加多个域名
python3 {baseDir}/scripts/domain.py add -n example.com -d test.example.com,www2.example.com

# 删除域名
python3 {baseDir}/scripts/domain.py delete -n example.com -d www.example.com
```

**用户意图识别**：
- "给这个站加个域名" → 执行 `domain.py add`
- "绑定新域名" → 执行 `domain.py add`
- "删除绑定的域名" → 执行 `domain.py delete`

### 场景七：管理 SSL 证书

当用户需要配置 SSL 证书时：

```bash
# 查看 SSL 证书信息
python3 {baseDir}/scripts/ssl_cert.py info -n example.com

# 上传 SSL 证书
python3 {baseDir}/scripts/ssl_cert.py upload -n example.com --key /path/to/key.pem --cert /path/to/cert.pem

# 申请免费证书
python3 {baseDir}/scripts/ssl_cert.py apply -n example.com -d example.com,www.example.com

# 开启强制 HTTPS
python3 {baseDir}/scripts/ssl_cert.py https -n example.com --enable

# 关闭强制 HTTPS
python3 {baseDir}/scripts/ssl_cert.py https -n example.com --disable

# 关闭 SSL
python3 {baseDir}/scripts/ssl_cert.py close -n example.com
```

**用户意图识别**：
- "查看证书状态" → 执行 `ssl_cert.py info`
- "上传 SSL 证书" → 执行 `ssl_cert.py upload`
- "申请免费证书" → 执行 `ssl_cert.py apply`
- "开启强制 HTTPS" → 执行 `ssl_cert.py https --enable`

---

### ⚠️ 申请免费 SSL 证书重要提示

**Let's Encrypt 免费证书申请条件：**

#### 1. 域名验证方式（二选一）

**方式 A: HTTP 文件验证（推荐）**
- ✅ 域名必须能正常解析到服务器 IP
- ✅ **80 端口必须开放**（未被防火墙阻止）
- ✅ 网站必须能正常通过 HTTP 访问
- ✅ 验证文件需要能被 Let's Encrypt 服务器访问
- ✅ 适合单个域名或不含通配符的多个域名

**方式 B: DNS 验证**
- ✅ 需要域名服务商支持 API 修改 DNS 记录
- ✅ 需要提供域名服务商的 API Key/Secret
- ✅ 适合通配符证书 (*.example.com)
- ✅ 不需要 80 端口开放
- ✅ **宝塔购买域名**：如果在宝塔面板购买了域名服务，使用其内置 DNS 能力，相当于已配置域名服务商 API
- ⚠️ **配置方法**：在宝塔面板 -> 网站 -> SSL -> DNS 验证 中配置 DNS 服务商 API 凭证

#### 2. 域名要求
- ❌ **不支持 IP 地址申请证书**（Let's Encrypt 仅支持域名）
- ❌ 不支持内网 IP（Let's Encrypt 无法访问验证）
- ✅ 域名必须已备案（中国大陆服务器）
- ✅ 一个证书最多包含 100 个域名

#### 3. 证书限制
- ⚠️ Let's Encrypt 证书有效期 **90 天**
- ⚠️ 每 3 个月需要续期一次（宝塔支持自动续期）
- ⚠️ 每周申请次数限制（约 50 次/周/域名）

#### 4. 常见错误场景

**错误 1: 使用 IP 地址申请**
```
❌ 错误：申请 IP 地址 192.168.69.172 的证书
✅ 正确：必须使用域名，如 example.com
```

**错误 2: 域名未解析到服务器**
```
❌ 错误：域名解析到其他服务器
✅ 正确：域名必须解析到当前服务器 IP
```

**错误 3: 80 端口被阻止**
```
❌ 错误：防火墙阻止 80 端口
✅ 正确：开放 80 端口用于 HTTP 验证
```

**错误 4: 内网域名申请**
```
❌ 错误：申请 inner.local 等内网域名
✅ 正确：使用公网可访问的域名
```

**错误 5: DNS 验证未配置**
```
❌ 错误：使用 DNS 验证但未配置 DNS 服务商 API
✅ 正确：先在面板中配置 DNS 服务商 API 凭证
```

#### 5. 申请前检查清单

```bash
# 1. 检查域名解析
ping example.com
# 应该解析到服务器 IP

# 2. 检查 80 端口
curl -I http://example.com
# 应该能正常访问

# 3. 绑定域名到站点
python3 {baseDir}/scripts/domain.py add -n example.com -d example.com

# 4. 验证网站访问
curl http://example.com
# 应该返回正常内容
```

#### 6. 推荐申请流程

```bash
# 步骤 1: 绑定域名
python3 {baseDir}/scripts/domain.py add -n example.com -d example.com,www.example.com

# 步骤 2: 申请证书（HTTP 验证）
python3 {baseDir}/scripts/ssl_cert.py apply -n example.com -d example.com,www.example.com

# 步骤 3: 开启强制 HTTPS
python3 {baseDir}/scripts/ssl_cert.py https -n example.com --enable

# 步骤 4: 验证证书
python3 {baseDir}/scripts/ssl_cert.py info -n example.com
```

**提示用户话术：**
> "申请免费 SSL 证书需要满足以下条件：
> 1. 使用域名（不能用 IP 地址）
> 2. 域名已解析到当前服务器
> 3. 80 端口开放（HTTP 验证方式）
> 4. 如果是通配符证书或在宝塔购买了域名，可以使用 DNS 验证方式
> 5. DNS 验证需要先在面板配置 DNS 服务商 API 凭证
> 
> 请问您的域名是否已解析到当前服务器？"

---

### 📄 证书申请日志

**日志路径：** `/www/server/panel/logs/letsencrypt.log`

**查看日志方法：**
```bash
# 手动查看
tail -50 /www/server/panel/logs/letsencrypt.log

# 或使用脚本（申请失败时自动查看）
python3 {baseDir}/scripts/ssl_cert.py apply -n example.com -d example.com
```

**申请失败时：**
- 脚本会自动读取日志最后 50 行
- 过滤出错误相关的日志
- 显示最近 10 条错误信息
- 提供解决方案建议

**常见日志错误：**
- `Connection refused` - 80 端口未开放或域名未解析
- `Invalid domain` - 域名格式错误
- `DNS verification failed` - DNS 验证失败（检查 API 配置）
- `Rate limit exceeded` - 达到申请频率限制（等待一段时间）

### 场景八：管理伪静态规则

当用户需要配置伪静态规则时：

```bash
# 查看伪静态模板列表
python3 {baseDir}/scripts/rewrite.py list -n example.com

# 查看当前伪静态规则
python3 {baseDir}/scripts/rewrite.py get -n example.com

# 应用 WordPress 伪静态规则
python3 {baseDir}/scripts/rewrite.py set -n example.com -t wordpress

# 应用 ThinkPHP 规则
python3 {baseDir}/scripts/rewrite.py set -n example.com -t thinkphp

# 自定义伪静态规则
python3 {baseDir}/scripts/rewrite.py set -n example.com --custom "location / { try_files $uri $uri/ /index.php?$query_string; }"
```

**用户意图识别**：
- "设置伪静态规则" → 执行 `rewrite.py set`
- "用 WordPress 的伪静态" → 执行 `rewrite.py set -t wordpress`
- "查看当前的伪静态" → 执行 `rewrite.py get`

### 场景九：管理数据库

当用户需要管理 MySQL 数据库时：

```bash
# 查看数据库列表
python3 {baseDir}/scripts/database.py list

# 查看数据库详情
python3 {baseDir}/scripts/database.py info -d example_db

# 创建数据库
python3 {baseDir}/scripts/database.py add -n example_db -u example_user -P "SecurePass123"

# 修改数据库密码
python3 {baseDir}/scripts/database.py password -d example_db -P "NewPass123"

# 设置数据库访问权限
python3 {baseDir}/scripts/database.py access -d example_db -a %

# 查看数据库表信息
python3 {baseDir}/scripts/database.py tables -d example_db

# 优化数据库表
python3 {baseDir}/scripts/database.py optimize -d example_db

# 修复数据库表
python3 {baseDir}/scripts/database.py repair -d example_db

# 删除数据库
python3 {baseDir}/scripts/database.py delete -d example_db
```

**用户意图识别**：
- "创建数据库" → 执行 `database.py add`
- "查看有哪些数据库" → 执行 `database.py list`
- "修改数据库密码" → 执行 `database.py password`
- "优化数据库" → 执行 `database.py optimize`

## 版本要求

- **宝塔面板**: >= 9.0.0
- **Python**: >= 3.10

## 用法

### 站点管理

```bash
# 查看站点列表
python3 {baseDir}/scripts/site.py list

# 创建站点
python3 {baseDir}/scripts/site.py add -n example.com -p /www/wwwroot/example.com -v 82

# 停用站点
python3 {baseDir}/scripts/site.py stop -n example.com

# 启用站点
python3 {baseDir}/scripts/site.py start -n example.com

# 删除站点
python3 {baseDir}/scripts/site.py delete -n example.com
```

### PHP 版本管理

```bash
# 查看 PHP 版本列表
python3 {baseDir}/scripts/php.py versions

# 查看站点 PHP 版本
python3 {baseDir}/scripts/php.py get -n example.com

# 设置 PHP 版本
python3 {baseDir}/scripts/php.py set -n example.com -v 82
```

### 域名管理

```bash
# 查看域名列表
python3 {baseDir}/scripts/domain.py list -n example.com

# 添加域名
python3 {baseDir}/scripts/domain.py add -n example.com -d www.example.com

# 删除域名
python3 {baseDir}/scripts/domain.py delete -n example.com -d www.example.com
```

### SSL 证书管理

```bash
# 查看 SSL 信息
python3 {baseDir}/scripts/ssl_cert.py info -n example.com

# 上传证书
python3 {baseDir}/scripts/ssl_cert.py upload -n example.com --key key.pem --cert cert.pem

# 申请免费证书
python3 {baseDir}/scripts/ssl_cert.py apply -n example.com -d example.com

# 开启/关闭强制 HTTPS
python3 {baseDir}/scripts/ssl_cert.py https -n example.com --enable
python3 {baseDir}/scripts/ssl_cert.py https -n example.com --disable

# 关闭 SSL
python3 {baseDir}/scripts/ssl_cert.py close -n example.com
```

### 伪静态管理

```bash
# 查看模板列表
python3 {baseDir}/scripts/rewrite.py list -n example.com

# 查看当前规则
python3 {baseDir}/scripts/rewrite.py get -n example.com

# 应用模板
python3 {baseDir}/scripts/rewrite.py set -n example.com -t wordpress
```

### 数据库管理

```bash
# 查看数据库列表
python3 {baseDir}/scripts/database.py list

# 创建数据库
python3 {baseDir}/scripts/database.py add -n testdb -u testuser -P "Password123"

# 修改密码
python3 {baseDir}/scripts/database.py password -d testdb -P "NewPass123"

# 删除数据库
python3 {baseDir}/scripts/database.py delete -d testdb
```

## 参数说明

### site.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `list` | 查看站点列表 | - |
| `add` | 创建站点 | - |
| `stop` | 停用站点 | - |
| `start` | 启用站点 | - |
| `delete` | 删除站点 | - |
| `info` | 查看站点详情 | - |
| `-n, --name` | 站点名称 | 必填 |
| `-p, --path` | 站点路径 | `/www/wwwroot/域名` |
| `-v, --version` | PHP 版本 | `82` |
| `--create-db` | 创建数据库 | 否 |
| `--create-ftp` | 创建 FTP | 否 |
| `--delete-path` | 删除站点目录 | 否 |
| `--delete-db` | 删除关联数据库 | 否 |
| `--delete-ftp` | 删除关联 FTP | 否 |

### php.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `versions` | 查看 PHP 版本列表 | - |
| `get` | 查看站点 PHP 版本 | - |
| `set` | 设置 PHP 版本 | - |
| `-n, --name` | 站点名称 | 必填 |
| `-v, --version` | PHP 版本号 | 必填 |
| `--static` | 设为纯静态 | - |

### domain.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `list` | 查看域名列表 | - |
| `add` | 添加域名 | - |
| `delete` | 删除域名 | - |
| `-n, --name` | 站点名称 | 必填 |
| `-d, --domain` | 域名（多个用逗号分隔） | 必填 |

### ssl_cert.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `info` | 查看 SSL 信息 | - |
| `upload` | 上传证书 | - |
| `apply` | 申请证书 | - |
| `https` | 设置强制 HTTPS | - |
| `close` | 关闭 SSL | - |
| `-n, --name` | 站点名称 | 必填 |
| `-d, --domain` | 域名列表 | - |
| `--key` | 私钥文件路径 | - |
| `--cert` | 证书文件路径 | - |

### rewrite.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `list` | 查看模板列表 | - |
| `get` | 查看当前规则 | - |
| `set` | 设置规则 | - |
| `-n, --name` | 站点名称 | 必填 |
| `-t, --template` | 模板名称 | - |
| `--custom` | 自定义规则 | - |

### database.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `list` | 查看数据库列表 | - |
| `add` | 创建数据库 | - |
| `info` | 查看数据库详情 | - |
| `password` | 修改密码 | - |
| `access` | 设置访问权限 | - |
| `tables` | 查看表信息 | - |
| `optimize` | 优化表 | - |
| `repair` | 修复表 | - |
| `delete` | 删除数据库 | - |
| `-n, --name` | 数据库名称 | 必填 |
| `-u, --user` | 数据库用户名 | 同数据库名 |
| `-P, --password` | 密码 | 随机生成 |
| `-d, --database` | 数据库名称 | 必填 |
| `-a, --access` | 访问权限 | `127.0.0.1` |

## 支持的 PHP 版本

| 版本 | 说明 |
|------|------|
| `52` | PHP 5.2 (已淘汰) |
| `53` | PHP 5.3 (已淘汰) |
| `54` | PHP 5.4 (已淘汰) |
| `55` | PHP 5.5 (已淘汰) |
| `56` | PHP 5.6 |
| `70` | PHP 7.0 |
| `71` | PHP 7.1 |
| `72` | PHP 7.2 |
| `73` | PHP 7.3 |
| `74` | PHP 7.4 |
| `80` | PHP 8.0 |
| `81` | PHP 8.1 |
| `82` | PHP 8.2 |
| `83` | PHP 8.3 |
| `84` | PHP 8.4 |
| `00` | 纯静态 |

## 支持的伪静态模板

常见伪静态模板：
- `wordpress` - WordPress
- `thinkphp` - ThinkPHP
- `laravel5` - Laravel 5
- `dedecms` - Dedecms
- `discuz` - Discuz
- `ecshop` - ECShop
- `typecho` - Typecho
- `zblog` - Z-Blog
- `drupal` - Drupal
- `phpcms` - PHPCMS
- `maccms` - 苹果 CMS
- `crmeb` - CRMEB
- `ShopWind` - 商派
- `EmpireCMS` - 帝国 CMS
- `EduSoho` - EduSoho

### 场景十：完整部署 WordPress 网站（实战示例）

> **实战更新日期:** 2026-04-02  
> **测试环境:** 内网 172 (192.168.69.172:8888)  
> **WordPress 版本:** 6.9.4 (最新中文版)

当用户需要从头部署一个完整的 WordPress 网站时，按以下步骤执行：

#### 步骤 1：环境检查

```bash
python3 {baseDir}/scripts/php.py versions
python3 {baseDir}/scripts/site.py list
```

#### 步骤 2：创建站点并配置数据库

```bash
python3 {baseDir}/scripts/site.py add -s "内网 172" \
    -n "192.168.69.172:19101" \
    -v 74 \
    --create-db \
    --db-user "wp_db_101"
```

**输出示例：**
```
✅ 站点创建成功：192.168.69.172:19101
   路径：/www/wwwroot/192.168.69.172_19101
   PHP 版本：74
   站点 ID: 24
   ✅ 数据库创建成功
      数据库名：wp_db_101
      用户名：wp_db_101
      密码：9q87Fbr8On41lzoT
```

#### 步骤 3：下载 WordPress 源码

```bash
python3 ../btpanel_files/scripts/download.py -s "内网 172" \
    download \
    --url "https://cn.wordpress.org/latest-zh_CN.zip" \
    --path "/www/wwwroot/192.168.69.172_19101" \
    --wait \
    --timeout 300
```

#### 步骤 4：解压到临时目录

```bash
python3 ../btpanel_files/scripts/unzip.py -s "内网 172" \
    unzip \
    --source "/www/wwwroot/192.168.69.172_19101/latest-zh_CN.zip" \
    --dest "/tmp/wp-extract"
```

#### 步骤 5：复制文件到站点根目录

```bash
PYTHONPATH=/mnt/c/Work/lpanel2/btpanel-skills/src python3 -c "
from bt_common.bt_client import BtClient
from bt_common.config import get_servers
servers = get_servers()
for s in servers:
    if s.name == '内网 172':
        client = BtClient(name=s.name, host=s.host, token=s.token, timeout=s.timeout)
        break
client.request('/files?action=CopyFile', {'sfile': '/tmp/wp-extract/wordpress', 'dfile': '/www/wwwroot/192.168.69.172_19101'})
"
```

#### 步骤 6：配置 wp-config.php

```bash
# 创建文件
python3 ../btpanel_files/scripts/files.py -s "内网 172" \
    touch "/www/wwwroot/192.168.69.172_19101/wp-config.php"

# 准备配置内容
python3 ../btpanel_files/scripts/files.py -s "内网 172" \
    cat "/www/wwwroot/192.168.69.172_19101/wp-config-sample.php" > /tmp/wp-config.txt

# 替换数据库配置
sed -i 's/database_name_here/wp_db_101/g; s/username_here/wp_db_101/g; s/password_here/9q87Fbr8On41lzoT/g; s/localhost/127.0.0.1/g' /tmp/wp-config.txt

# 写入配置
python3 ../btpanel_files/scripts/files.py -s "内网 172" \
    edit "/www/wwwroot/192.168.69.172_19101/wp-config.php" \
    -f /tmp/wp-config.txt
```

#### 步骤 7：应用伪静态规则

```bash
python3 {baseDir}/scripts/rewrite.py -s "内网 172" \
    set -n "192.168.69.172_19101" -t wordpress
```

#### 步骤 8：验证访问

```bash
curl -I http://192.168.69.172:19101
```

**预期输出：**
```
HTTP/1.1 302 Found
X-Redirect-By: WordPress
Location: http://192.168.69.172:19101/wp-admin/install.php
```

---

### 部署完成信息

```markdown
## 🎉 WordPress 部署完成！

| 项目 | 值 |
|------|------|
| 访问地址 | http://192.168.69.172:19101 |
| 数据库名 | wp_db_101 |
| 用户名 | wp_db_101 |
| 密码 | 9q87Fbr8On41lzoT |
| 数据库主机 | 127.0.0.1 |
```

### 关键注意事项

1. **数据库参数自动传递** - 脚本已自动处理 `sql=true` 参数
2. **下载大文件使用 --wait** - 确保下载完成
3. **解压到临时目录** - 避免子目录问题
4. **wp-config.php 配置** - 必须正确配置数据库连接
5. **伪静态规则必需** - WordPress 正常工作必要条件
6. **端口选择** - 建议使用 19000+ 避免冲突


## 注意事项

1. **删除操作谨慎**：删除站点、数据库等操作不可逆，操作前务必备份数据
2. **PHP 版本兼容**：切换 PHP 版本前，确认网站代码兼容新版本
3. **SSL 证书申请**：申请免费证书需要域名能正常解析且 80 端口开放
4. **数据库权限**：设置数据库访问权限时，`%` 表示允许远程连接，`127.0.0.1` 表示仅本地访问
5. **伪静态规则**：应用伪静态规则前，建议先查看当前规则并备份
6. **API 参数要求**：创建站点时宝塔 API 要求明确传递 `sql` 和 `ftp` 参数（脚本已自动处理）
