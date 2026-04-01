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

## 常用场景

### 场景一：创建新 PHP 网站

当用户需要创建新的 PHP 网站时：

```bash
# 创建基础 PHP 站点
python3 {baseDir}/scripts/site.py add -n example.com -p /www/wwwroot/example.com -v 82

# 创建站点并关联数据库
python3 {baseDir}/scripts/site.py add -n example.com -v 82 --create-db -d example_db -u example_user -P "SecurePass123"

# 创建站点并同时创建 FTP
python3 {baseDir}/scripts/site.py add -n example.com -v 82 --create-ftp -U ftpuser -P "FtpPass123"
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

### 场景十：完整部署 WordPress 网站

当用户需要从头部署一个完整的 WordPress 网站时，按以下步骤执行：

#### 步骤 1：环境检查

首先确认服务器已安装必要的软件：

```bash
# 查看已安装的 PHP 版本
python3 {baseDir}/scripts/php.py versions

# 查看 MySQL 服务状态（通过 btpanel 技能）
python3 ../btpanel/scripts/services.py -s SERVER_NAME list
```

**预期结果**：
- PHP 7.4 或更高版本已安装
- MySQL/MariaDB 服务运行正常

#### 步骤 2：创建站点并配置数据库

创建站点时**必须明确传递 sql 和 ftp 参数**：

```bash
# 创建站点 + 数据库（推荐同时创建 FTP 避免潜在问题）
python3 {baseDir}/scripts/site.py add -s SERVER_NAME \
    -n "example.com:8080" \
    -p "/www/wwwroot/wp-site" \
    -v 74 \
    --ps "WordPress 网站" \
    --create-db \
    --db-user "wp_db" \
    --db-password "WpPass123!" \
    --create-ftp \
    --ftp-user "wp_ftp" \
    --ftp-password "FtpPass123!"
```

**重要提示**：
- 宝塔 API 要求明确传递 `sql` 和 `ftp` 参数（`true` 或 `false`）
- 脚本已自动处理：默认传递 `false`，使用 `--create-db` 时改为 `true`
- 建议同时创建 FTP，避免潜在的 API 返回错误

**输出示例**：
```
✅ 站点创建成功：example.com:8080
   路径：/www/wwwroot/wp-site
   PHP 版本：74
   站点 ID: 15
   ✅ 数据库创建成功
      数据库名：wp_db
      用户名：wp_db
      密码：WpPass123!
   ✅ FTP 创建成功
      用户名：wp_ftp
      密码：FtpPass123!
```

#### 步骤 3：下载 WordPress 源码

使用文件管理技能下载 WordPress：

```bash
# 下载 WordPress 中文版（最新版本）
python3 ../btpanel_files/scripts/download.py -s SERVER_NAME \
    -u "https://cn.wordpress.org/latest-zh_CN.zip" \
    -p "/www/wwwroot/wp-site/wordpress.zip"

# 等待下载完成
python3 ../btpanel_files/scripts/download.py -s SERVER_NAME \
    -u "https://cn.wordpress.org/latest-zh_CN.zip" \
    -p "/www/wwwroot/wp-site/wordpress.zip" \
    --wait
```

**下载进度示例**：
```
📥 开始下载: https://cn.wordpress.org/latest-zh_CN.zip
   目标路径: /www/wwwroot/wp-site/wordpress.zip
⏳ 下载进行中... (34.2MB / 34.4MB)
✅ 下载完成: wordpress.zip (34.4MB)
```

#### 步骤 4：解压源码到站点目录

```bash
# 解压 WordPress 到站点目录
python3 ../btpanel_files/scripts/unzip.py -s SERVER_NAME \
    -s "/www/wwwroot/wp-site/wordpress.zip" \
    -d "/www/wwwroot/wp-site" \
    -t zip

# 查看解压结果
python3 ../btpanel_files/scripts/files.py -s SERVER_NAME ls -p "/www/wwwroot/wp-site"
```

**解压结果示例**：
```
📁 /www/wwwroot/wp-site

  目录:
    📁 wordpress                         4.0MB  755    -           2026-03-13 05:00:05

  文件:
    📄 wordpress.zip                     34.4MB  644    www         2026-04-01 16:30:00
```

#### 步骤 5：调整站点路径（如需要）

如果 WordPress 解压在子目录（如 `wordpress/`），需要修改站点路径：

```bash
# 修改站点路径指向 WordPress 目录
python3 {baseDir}/scripts/site.py -s SERVER_NAME set-path \
    -n "example.com:8080" \
    -p "/www/wwwroot/wp-site/wordpress"
```

#### 步骤 6：配置伪静态规则

WordPress 需要配置伪静态规则才能正常工作：

```bash
# 应用 WordPress 伪静态模板
python3 {baseDir}/scripts/rewrite.py -s SERVER_NAME set \
    -n "example.com:8080" \
    -t wordpress
```

**伪静态规则示例**：
```
location / {
    try_files $uri $uri/ /index.php?$query_string;
}
rewrite /wp-admin$ $scheme://$host$uri/ permanent;
```

#### 步骤 7：配置 SSL 证书（可选）

如果需要 HTTPS 访问：

```bash
# 申请 Let's Encrypt 免费证书
python3 {baseDir}/scripts/ssl_cert.py -s SERVER_NAME apply \
    -n "example.com:8080" \
    -d "example.com,www.example.com"

# 开启强制 HTTPS
python3 {baseDir}/scripts/ssl_cert.py -s SERVER_NAME https \
    -n "example.com:8080" \
    --enable
```

#### 步骤 8：访问安装向导

完成以上步骤后，向用户提供以下信息：

```
## 🎉 WordPress 部署完成！

### 站点信息
| 项目 | 值 |
|------|------|
| 访问地址 | http://example.com:8080 |
| 网站路径 | /www/wwwroot/wp-site/wordpress |
| PHP 版本 | 7.4 |

### 数据库信息（安装向导填写）
| 项目 | 值 |
|------|------|
| 数据库名 | wp_db |
| 用户名 | wp_db |
| 密码 | WpPass123! |
| 数据库主机 | localhost |
| 表前缀 | wp_（默认） |

### FTP 信息（文件上传用）
| 项目 | 值 |
|------|------|
| 用户名 | wp_ftp |
| 密码 | FtpPass123! |

### 下一步
访问 http://example.com:8080 开始 WordPress 安装向导，
填写以上数据库信息即可完成安装！
```

---

**完整部署流程总结**：

| 步骤 | 命令 | 说明 |
|------|------|------|
| 1 | `php.py versions` | 检查 PHP 版本 |
| 2 | `site.py add --create-db` | 创建站点和数据库 |
| 3 | `download.py --wait` | 下载 WordPress 源码 |
| 4 | `unzip.py` | 解压到站点目录 |
| 5 | `site.py set-path` | 调整站点路径 |
| 6 | `rewrite.py set -t wordpress` | 配置伪静态 |
| 7 | `ssl_cert.py apply` | 申请 SSL 证书（可选） |
| 8 | - | 提供安装信息给用户 |

**用户意图识别**：
- "帮我部署一个 WordPress 网站" → 按上述步骤依次执行
- "安装 WordPress" → 按上述步骤依次执行
- "新建一个博客网站" → 询问是否使用 WordPress，然后按步骤执行

**注意事项**：
1. 创建站点时必须明确传递 `sql` 和 `ftp` 参数
2. 下载大文件时使用 `--wait` 参数等待完成
3. WordPress 解压后通常在 `wordpress/` 子目录，需调整站点路径
4. 伪静态规则是 WordPress 正常工作的必要条件

---

## 注意事项

1. **删除操作谨慎**：删除站点、数据库等操作不可逆，操作前务必备份数据
2. **PHP 版本兼容**：切换 PHP 版本前，确认网站代码兼容新版本
3. **SSL 证书申请**：申请免费证书需要域名能正常解析且 80 端口开放
4. **数据库权限**：设置数据库访问权限时，`%` 表示允许远程连接，`127.0.0.1` 表示仅本地访问
5. **伪静态规则**：应用伪静态规则前，建议先查看当前规则并备份
6. **API 参数要求**：创建站点时宝塔 API 要求明确传递 `sql` 和 `ftp` 参数（脚本已自动处理）
